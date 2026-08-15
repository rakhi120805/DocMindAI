"""
Supervisor — the traffic controller of the whole agent system.

WHAT LANGGRAPH ACTUALLY GIVES YOU (important to understand, not just
namedrop in an interview):
LangGraph models your agent workflow as a GRAPH of nodes (each node =
one agent's `run()` call) and edges (the rules for what runs next).
Instead of writing a pile of if/else statements to decide "should I
call the QA agent or the Summary agent next?", you define:
  - Nodes: ocr, classify, extract, retrieve, qa, verify, risk, summarize, report
  - Edges: which node runs after which
  - Conditional edges: e.g. "if the user asked a question -> QA path,
    if they asked for a summary -> Summary path"
This also gives you built-in state passing between nodes (each node
reads/writes a shared state dict) and makes the flow visualizable and
debuggable — you can literally print the graph and see the pipeline.

TWO DISTINCT FLOWS THIS SUPERVISOR HANDLES:
1. INGESTION FLOW (runs once per uploaded document):
   OCR -> Classify -> Extract Metadata -> Verify -> Risk-score
   (Chunk -> Embed happens too, for the RAG layer - see rag/)
2. QUERY FLOW (runs every time a user asks a question):
   Retrieve -> QA

Below is a simplified version showing the ROUTING LOGIC clearly,
without requiring the langgraph package to be installed yet. Once
you're ready, this maps directly onto a langgraph.graph.StateGraph.
"""

from typing import Any, Dict, TypedDict, Optional


class PipelineState(TypedDict, total=False):
    file_id: str
    file_path: str
    pages: list
    document_type: Optional[str]
    classification_confidence: Optional[float]
    extracted_metadata: dict
    verification_status: Optional[str]
    verification_issues: list
    risk_score: Optional[int]
    question: Optional[str]
    chunks: list
    answer: Optional[str]


class Supervisor:
    """
    Plain-Python version of the routing logic. Swap this internals for
    a real langgraph.graph.StateGraph once dependencies are installed —
    the AGENT CLASSES themselves don't need to change, only how they're
    wired together.
    """

    def __init__(self, agents: Dict[str, Any]):
        # agents = {"ocr": OCRAgent(), "classify": ClassificationAgent(...), ...}
        self.agents = agents

    def run_ingestion(self, file_path: str, file_id: str) -> PipelineState:
        state: PipelineState = {"file_path": file_path, "file_id": file_id}

        ocr_out = self.agents["ocr"].run({"file_path": file_path})
        state["pages"] = ocr_out["pages"]

        classify_out = self.agents["classify"].run({"pages": state["pages"]})
        state["document_type"] = classify_out["type"]
        state["classification_confidence"] = classify_out["confidence"]

        extract_out = self.agents["extract"].run({
            "pages": state["pages"],
            "document_type": state["document_type"],
        })
        state["extracted_metadata"] = extract_out["extracted_metadata"]

        verify_out = self.agents["verify"].run({
            "extracted_metadata": state["extracted_metadata"],
            "document_type": state["document_type"],
        })
        state["verification_status"] = verify_out["status"]
        state["verification_issues"] = verify_out["issues"]

        risk_out = self.agents["risk"].run({
            "verification_issues": state["verification_issues"],
            "extracted_metadata": state["extracted_metadata"],
        })
        state["risk_score"] = risk_out["risk_score"]

        index_out = self.agents["index"].run({
            "pages": state["pages"],
            "file_id": file_id,
        })
        state["chunks"] = index_out["chunks"]

        return state

    def run_query(self, file_id: str, question: str) -> PipelineState:
        state: PipelineState = {"file_id": file_id, "question": question}

        retrieval_out = self.agents["retrieve"].run({
            "file_id": file_id, "question": question,
        })
        state["chunks"] = retrieval_out["chunks"]

        qa_out = self.agents["qa"].run({
            "chunks": state["chunks"], "question": question,
        })
        state["answer"] = qa_out["answer"]

        return state
