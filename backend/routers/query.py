"""
Query Router — handles POST /query.

Unlike upload, this one IS synchronous (waits for the answer before
responding) because retrieval + a single LLM call is fast (typically
1-3 seconds), and the user is actively waiting for a chat-style
answer — there's no good UX for "your answer is queued."
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Document, QueryLog
from backend.models.schemas import QueryRequest, QueryResponse
from backend.services.pipeline_service import run_query_pipeline
from evaluation.hallucination import faithfulness_score

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_document(request: QueryRequest, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.file_id == request.file_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.processing_status == "failed":
        raise HTTPException(
            status_code=422,
            detail="Document processing failed. Check GET /documents/{file_id}/status "
                   "for the specific error.",
        )
    if doc.processing_status != "done":
        raise HTTPException(
            status_code=409,
            detail=f"Document still processing (status: {doc.processing_status})",
        )

    start = time.time()
    result = run_query_pipeline(request.file_id, request.question)
    latency_ms = int((time.time() - start) * 1000)

    # Faithfulness doubles as a live "confidence" signal returned to
    # the caller - a cheap, real-time hallucination check on every
    # single answer, not just something computed later in a batch
    # benchmark. See evaluation/hallucination.py for what this
    # actually measures and its known limitations.
    context_texts = [c["text"] for c in result["chunks"]]
    confidence = faithfulness_score(result["answer"], context_texts)

    # Log every query for the Evaluation Layer — this is what
    # evaluation/metrics.py and GET /metrics read from later.
    log = QueryLog(
        document_id=doc.id,
        question=request.question,
        answer=result["answer"],
        retrieved_chunk_ids=[c.get("chunk_index") for c in result["chunks"]],
        latency_ms=latency_ms,
        confidence=confidence,
    )
    db.add(log)
    db.commit()

    return QueryResponse(
        answer=result["answer"],
        confidence=confidence,
        source_chunks=result["chunks"],
        latency_ms=latency_ms,
    )
