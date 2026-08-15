"""
Report Agent.

JOB: Take everything produced by the other agents (classification,
metadata, verification, risk, summary) and render it into a
downloadable report — Markdown, PDF, JSON, or CSV. This is the "last
mile" agent — it does no reasoning of its own, just formatting, which
is worth pointing out: not every agent needs to call an LLM.
"""

from agents.base_agent import BaseAgent
from typing import Any, Dict


class ReportAgent(BaseAgent):
    name = "report_agent"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        fmt = input_data.get("format", "markdown")
        if fmt == "markdown":
            content = self._to_markdown(input_data)
        else:
            raise NotImplementedError(f"Format '{fmt}' not implemented yet")

        return {"format": fmt, "content": content}

    def _to_markdown(self, data: Dict[str, Any]) -> str:
        return f"""# Document Report

**Type:** {data.get('document_type', 'Unknown')}
**Confidence:** {data.get('classification_confidence', 'N/A')}
**Verification status:** {data.get('verification_status', 'N/A')}
**Risk score:** {data.get('risk_score', 'N/A')}/100

## Summary
{data.get('executive_summary', 'No summary generated.')}

## Extracted Metadata
{data.get('extracted_metadata', {})}
"""
