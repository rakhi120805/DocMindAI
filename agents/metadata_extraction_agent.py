"""
Metadata Extraction Agent — Step 4 of the pipeline.

JOB: Given OCR'd text AND its known document type (from Classification),
pull out the specific structured fields that document type actually
has, as JSON.

WHY THIS NEEDS THE DOCUMENT TYPE FIRST (dependency on Classification):
An Invoice and a Passport have completely different fields worth
extracting (GST number vs. date of birth). Rather than asking the LLM
one giant open-ended "extract everything" prompt, we look up a
per-type schema and ask ONLY for those fields. This is the same
"constrain the output space" principle from Classification — the
narrower the ask, the more reliable the extraction.

WHY THIS FEEDS DIRECTLY INTO VerifierAgent AND RiskAgent:
Look at agents/verifier_agent.py - it checks for a valid `pan`,
`aadhaar`, `amount` etc. Those checks are meaningless until this
agent actually populates those fields. This is a good example of
agent OUTPUT becoming another agent's INPUT, which is exactly what
the Supervisor wires together (see agents/supervisor.py).
"""

from agents.base_agent import BaseAgent
from typing import Any, Dict, List

# Per-document-type field schemas. Adding a new document type later
# means adding one line here — nothing else in this agent changes.
FIELD_SCHEMAS: Dict[str, List[str]] = {
    "Invoice": ["invoice_number", "date", "amount", "gst", "pan", "company", "email"],
    "Passport": ["passport_number", "name", "date_of_birth", "nationality", "expiry_date"],
    "Aadhaar": ["aadhaar", "name", "date_of_birth", "address"],
    "Bank Statement": ["account_number", "name", "statement_period", "closing_balance"],
    "Resume": ["name", "email", "phone", "years_experience"],
    "Tax Form": ["pan", "name", "assessment_year", "amount"],
    "Insurance": ["policy_number", "name", "amount", "date"],
}

EXTRACTION_PROMPT = """Extract the following fields from the document
text below. Respond ONLY as JSON with exactly these keys: {fields}
If a field isn't present in the text, use null for its value.

Document text:
---
{text}
---
"""


class MetadataExtractionAgent(BaseAgent):
    name = "metadata_extraction_agent"

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        document_type = input_data.get("document_type")
        full_text = " ".join(p["text"] for p in input_data["pages"])

        fields = FIELD_SCHEMAS.get(document_type)
        if not fields:
            # Unknown/unsupported type - nothing to reliably extract.
            # Returning an empty dict (not raising) keeps the pipeline
            # moving; Verification/Risk agents already handle empty
            # metadata gracefully (see agents/verifier_agent.py).
            return {"extracted_metadata": {}}

        prompt = EXTRACTION_PROMPT.format(
            fields=", ".join(fields),
            text=full_text[:6000],
        )

        raw_result = self.llm_client.complete_json(prompt)
        cleaned = self._coerce_types(raw_result, document_type)

        return {"extracted_metadata": cleaned}

    def _coerce_types(self, result: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """
        LLMs return amounts as strings sometimes ("1,200.00" or even
        "1200.00 INR"). VerifierAgent's negative-amount check does a
        numeric comparison (`amount < 0`), so we normalize numeric
        fields here rather than trusting the LLM's output type — one
        more example of not letting LLM unpredictability leak into
        strict downstream logic.
        """
        if "amount" in result and isinstance(result["amount"], str):
            digits_only = "".join(
                ch for ch in result["amount"] if ch.isdigit() or ch in ".-"
            )
            try:
                result["amount"] = float(digits_only) if digits_only else None
            except ValueError:
                result["amount"] = None
        return result
