"""
Documents Router — status polling and history.

This is what the frontend polls after upload to show a progress
indicator ("Processing... Classifying... Verifying... Done").
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Document
from backend.models.schemas import DocumentStatusResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{file_id}/status", response_model=DocumentStatusResponse)
async def get_status(file_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.file_id == file_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentStatusResponse(
        file_id=doc.file_id,
        filename=doc.filename,
        document_type=doc.document_type,
        classification_confidence=doc.classification_confidence,
        processing_status=doc.processing_status,
        verification_status=doc.verification_status,
        risk_score=doc.risk_score,
        # pipeline_service.py stores {"error": "..."} in verification_notes
        # when processing fails - surface it here so failures are actually
        # debuggable through the API, not just visible in the DB directly.
        error=doc.verification_notes.get("error") if (
            doc.processing_status == "failed" and doc.verification_notes
        ) else None,
        extracted_metadata=doc.extracted_metadata,
        # verification_notes holds a LIST of issue strings on success
        # (see agents/verifier_agent.py's output), but a DICT with an
        # "error" key on failure (see pipeline_service.py's except
        # block) - same column, two different shapes depending on
        # outcome. Only treat it as the issues list when it's actually
        # a list, so a failed run doesn't get misread as "0 issues."
        verification_issues=doc.verification_notes if (
            doc.processing_status != "failed" and isinstance(doc.verification_notes, list)
        ) else None,
    )


@router.get("")
async def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [
        {
            "file_id": d.file_id,
            "filename": d.filename,
            "document_type": d.document_type,
            "processing_status": d.processing_status,
            # These two were missing here originally - caught via a real
            # end-to-end test hitting this endpoint directly, then
            # comparing the response against what frontend/Sidebar.jsx
            # actually reads. Without them, every "done" document's
            # stamp badge in the sidebar list silently fell back to
            # "pending" (gray), since Sidebar.jsx colors the badge from
            # verification_status + risk_score, and both were always
            # undefined coming from this endpoint - a real bug that
            # pure UI mocking wouldn't have surfaced, since the mock
            # would have just been given whatever shape I assumed.
            "verification_status": d.verification_status,
            "risk_score": d.risk_score,
            "uploaded_at": d.uploaded_at,
        }
        for d in docs
    ]