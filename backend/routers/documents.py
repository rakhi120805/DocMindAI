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
            "uploaded_at": d.uploaded_at,
        }
        for d in docs
    ]
