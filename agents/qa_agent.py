"""
Question Answering Agent.

JOB: Given a question + retrieved chunks (from RetrievalAgent), produce
a grounded answer. "Grounded" is the key word — the prompt explicitly
instructs the LLM to answer ONLY from the provided context and say
"I don't know" rather than guessing, which is the main defense against
hallucination in a RAG system.
"""

from agents.base_agent import BaseAgent
from typing import Any, Dict

QA_PROMPT = """Answer the question using ONLY the context below.
If the answer isn't in the context, say "I don't have enough
information in this document to answer that."

Context:
{context}

Question: {question}

Answer:"""


class QAAgent(BaseAgent):
    name = "qa_agent"

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        chunks = input_data["chunks"]
        question = input_data["question"]

        context = "\n---\n".join(c["text"] for c in chunks)
        prompt = QA_PROMPT.format(context=context, question=question)

        answer = self.llm_client.complete(prompt)
        return {"answer": answer.strip()}
