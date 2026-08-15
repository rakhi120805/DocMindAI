"""
Pipeline Service — the glue between HTTP routers and the agent system.

WHY ROUTERS DON'T CALL AGENTS DIRECTLY:
Keeps FastAPI route handlers thin (just HTTP concerns: parse request,
call service, return response) while this file owns the actual
business logic of "what happens when a document is uploaded" and
"what happens when a question is asked." This also makes the pipeline
testable without spinning up a web server.
"""

from sqlalchemy.orm import Session
from backend.database.session import SessionLocal
from backend.database.models import Document, DocumentChunk
from backend.services.llm_client import LLMClient

from agents.ocr_agent import OCRAgent
from agents.classification_agent import ClassificationAgent
from agents.metadata_extraction_agent import MetadataExtractionAgent
from agents.verifier_agent import VerifierAgent
from agents.risk_agent import RiskAgent
from agents.retrieval_agent import RetrievalAgent
from agents.qa_agent import QAAgent
from agents.supervisor import Supervisor

from rag.embedder import get_embedder
from rag.vector_store import get_vector_store
from rag.indexer import Indexer


def _build_supervisor() -> Supervisor:
    """
    Builds one Supervisor with all agents wired up. In a bigger app
    this would be a proper dependency-injection container; for this
    project size, one factory function is clear enough — and easy to
    explain in an interview without over-engineering.

    IMPORTANT: embedder and vector_store come from get_embedder() /
    get_vector_store() - shared singletons, NOT `Embedder()` /
    `VectorStore()` called fresh here. A fresh VectorStore() on every
    call would silently lose every embedding between requests (see
    rag/vector_store.py's docstring for why). LLMClient and the
    per-request agents ARE fine to build fresh each call - they hold
    no state that needs to persist.
    """
    llm_client = LLMClient()
    embedder = get_embedder()
    vector_store = get_vector_store()

    agents = {
        "ocr": OCRAgent(),
        "classify": ClassificationAgent(llm_client),
        "extract": MetadataExtractionAgent(llm_client),
        "verify": VerifierAgent(),
        "risk": RiskAgent(),
        "index": Indexer(embedder, vector_store),
        "retrieve": RetrievalAgent(embedder, vector_store),
        "qa": QAAgent(llm_client),
    }
    return Supervisor(agents)


def run_ingestion_pipeline(file_id: str, file_path: str) -> None:
    """
    Runs as a FastAPI BackgroundTask after /upload responds.
    Updates the Document row as each stage completes, so the frontend
    can poll GET /documents/{file_id}/status and show real progress.
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.file_id == file_id).first()
        doc.processing_status = "processing"
        db.commit()

        supervisor = _build_supervisor()
        state = supervisor.run_ingestion(file_path=file_path, file_id=file_id)

        doc.document_type = state.get("document_type")
        doc.classification_confidence = state.get("classification_confidence")
        doc.extracted_metadata = state.get("extracted_metadata")
        doc.verification_status = state.get("verification_status")
        doc.verification_notes = state.get("verification_issues")
        doc.risk_score = state.get("risk_score")

        # Persist chunk metadata to SQLite too, mirroring what's in
        # FAISS. FAISS only lives in memory (until we add index
        # save/load to disk) - SQLite's copy means chunk text/page
        # info survives a server restart even before that's added.
        for chunk in state.get("chunks", []):
            db.add(DocumentChunk(
                file_id=file_id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page"],
                text=chunk["text"],
            ))

        doc.processing_status = "done"
        db.commit()

    except Exception as e:
        doc.processing_status = "failed"
        doc.verification_notes = {"error": str(e)}
        db.commit()
    finally:
        db.close()


def run_query_pipeline(file_id: str, question: str) -> dict:
    supervisor = _build_supervisor()
    state = supervisor.run_query(file_id=file_id, question=question)
    return {"answer": state["answer"], "chunks": state["chunks"]}
