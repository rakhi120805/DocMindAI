"""
Risk Agent.

JOB: Combine signals from Classification, Verification, and metadata
to produce a single 0-100 risk score, e.g. for invoice fraud or
identity mismatch. This agent intentionally reads the OUTPUT of other
agents rather than raw text — it's a good example, in interviews, of
agents being composable: the Supervisor runs Classification and
Verification first, then feeds their combined output into this one.
"""

from agents.base_agent import BaseAgent
from typing import Any, Dict, List


class RiskAgent(BaseAgent):
    name = "risk_agent"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        verification_issues = input_data.get("verification_issues", [])
        metadata = input_data.get("extracted_metadata", {})

        score = 0
        reasons: List[str] = []

        # Simple deterministic scoring rules to start with.
        # A more advanced version could have the LLM weigh in on
        # ambiguous cases (e.g. "does this look like a template forgery?").
        if verification_issues:
            score += 20 * len(verification_issues)
            reasons.append(f"{len(verification_issues)} verification issue(s) found")

        if not metadata:
            score += 15
            reasons.append("No metadata could be extracted")

        score = min(score, 100)
        return {"risk_score": score, "reasons": reasons}
