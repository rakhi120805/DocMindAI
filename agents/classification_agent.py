"""
Classification Agent — Step 3 of the pipeline.

JOB: Given the OCR'd text, decide what TYPE of document this is
(Invoice, Passport, Bank Statement, Resume, etc.) with a confidence
score, so downstream agents know which extraction/verification rules
to apply. (You wouldn't check for a PAN number on a resume.)

WHY THIS MATTERS: it's the branch point of the whole pipeline —
everything downstream (which metadata fields to extract, which
verification rules apply) depends on getting this right first.

HOW IT WORKS: sends the OCR text to the LLM with a constrained prompt
("pick one of these classes") and asks for JSON back. This is a good
place to talk about PROMPT ENGINEERING in interviews: constraining the
output space (giving a fixed list of classes) makes the LLM's job much
more reliable than an open-ended "what is this document?" prompt.
"""

from agents.base_agent import BaseAgent
from typing import Any, Dict

DOCUMENT_CLASSES = [
    "Invoice", "Passport", "Aadhaar", "Bank Statement",
    "Resume", "Research Paper", "Insurance", "Tax Form", "Unknown",
]

CLASSIFICATION_PROMPT = """You are a document classification system.
Given the extracted text below, classify it into exactly one of these
classes: {classes}

Respond ONLY with JSON: {{"type": "<class>", "confidence": <0-1 float>}}

Document text:
---
{text}
---
"""


class ClassificationAgent(BaseAgent):
    name = "classification_agent"

    def __init__(self, llm_client):
        # The LLM client is injected (dependency injection), not hardcoded,
        # so we can swap OpenAI/Anthropic/local models without touching
        # this agent's logic.
        self.llm_client = llm_client

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        full_text = " ".join(p["text"] for p in input_data["pages"])

        prompt = CLASSIFICATION_PROMPT.format(
            classes=", ".join(DOCUMENT_CLASSES),
            text=full_text[:4000],  # cap prompt size for cost/latency
        )

        result = self.llm_client.complete_json(prompt)

        # Guard against the model inventing a class we didn't list.
        if result.get("type") not in DOCUMENT_CLASSES:
            result["type"] = "Unknown"

        return result
