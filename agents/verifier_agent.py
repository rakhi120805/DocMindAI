"""
Verification Agent.

JOB: Catch problems in the extracted document data — missing fields,
malformed IDs, suspicious values.

IMPORTANT DESIGN DECISION (say this explicitly in interviews):
This agent is DELIBERATELY NOT pure-LLM. Format checks (is this a
valid PAN? is this date real?) are exact, deterministic problems —
regex and rule-based validation is faster, cheaper, and 100%
reliable for these, whereas an LLM might hallucinate a "looks fine"
on a malformed ID. We only call the LLM for the fuzzy checks that
rules genuinely can't do, like "does this address look inconsistent
with the invoice's claimed company location?"

This mirrors a real fraud/compliance pipeline: deterministic checks
first (cheap, fast, exact), LLM reasoning second (for nuance).
"""

import re
from agents.base_agent import BaseAgent
from typing import Any, Dict, List

PAN_REGEX = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
AADHAAR_REGEX = r"^\d{4}\s?\d{4}\s?\d{4}$"


class VerifierAgent(BaseAgent):
    name = "verifier_agent"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        metadata = input_data.get("extracted_metadata", {})
        issues: List[str] = []

        issues += self._check_required_fields(metadata, input_data.get("document_type"))
        issues += self._check_pan(metadata)
        issues += self._check_aadhaar(metadata)
        issues += self._check_amount(metadata)

        status = "OK" if not issues else "Warning"
        return {"status": status, "issues": issues}

    def _check_required_fields(self, metadata: dict, doc_type: str) -> List[str]:
        required_by_type = {
            "Invoice": ["invoice_number", "amount", "date"],
            "Passport": ["passport_number", "name", "date_of_birth"],
        }
        required = required_by_type.get(doc_type, [])
        return [f"Missing required field: {f}" for f in required if not metadata.get(f)]

    def _check_pan(self, metadata: dict) -> List[str]:
        pan = metadata.get("pan")
        if pan and not re.match(PAN_REGEX, pan):
            return [f"Invalid PAN format: {pan}"]
        return []

    def _check_aadhaar(self, metadata: dict) -> List[str]:
        aadhaar = metadata.get("aadhaar")
        if aadhaar and not re.match(AADHAAR_REGEX, aadhaar):
            return [f"Invalid Aadhaar format: {aadhaar}"]
        return []

    def _check_amount(self, metadata: dict) -> List[str]:
        amount = metadata.get("amount")
        if amount is not None and amount < 0:
            return [f"Negative invoice amount: {amount}"]
        return []
