"""
Summary Agent.

JOB: Produce an executive summary, key findings, important dates, and
action items from the FULL document text (not just retrieved chunks —
summarization needs the whole picture, unlike Q&A which only needs
relevant pieces). For long documents this agent would use a
map-reduce strategy: summarize each chunk, then summarize the
summaries — worth mentioning if asked about scaling to long docs.
"""

from agents.base_agent import BaseAgent
from typing import Any, Dict

SUMMARY_PROMPT = """Summarize the following document. Respond as JSON:
{{
  "executive_summary": "...",
  "key_findings": ["..."],
  "important_dates": ["..."],
  "action_items": ["..."]
}}

Document:
{text}
"""


class SummaryAgent(BaseAgent):
    name = "summary_agent"

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        full_text = " ".join(p["text"] for p in input_data["pages"])
        prompt = SUMMARY_PROMPT.format(text=full_text[:8000])

        return self.llm_client.complete_json(prompt)
