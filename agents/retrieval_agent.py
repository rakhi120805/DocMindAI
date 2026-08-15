"""
Retrieval Agent — the "R" in RAG.

JOB: Given a user's question, find the most relevant document chunks.
This agent does NOT generate answers — it only finds context. That
separation matters: it means retrieval quality (did we find the right
chunks?) can be measured independently of generation quality (did the
LLM phrase the answer well?) — see evaluation/metrics.py for exactly
this: "Context Precision" and "Recall" are retrieval metrics,
"Faithfulness" is a generation metric.
"""

from agents.base_agent import BaseAgent
from typing import Any, Dict


class RetrievalAgent(BaseAgent):
    name = "retrieval_agent"

    def __init__(self, embedder, vector_store, top_k: int = 5):
        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        question = input_data["question"]
        file_id = input_data["file_id"]

        question_vector = self.embedder.embed(question)
        matches = self.vector_store.search(
            vector=question_vector, top_k=self.top_k, filter_file_id=file_id
        )
        return {"chunks": matches}
