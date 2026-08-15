"""
Upload Router — handles POST /upload.

DESIGN DECISION WORTH EXPLAINING IN AN INTERVIEW:
This endpoint returns IMMEDIATELY after saving the file and creating a
"queued" DB row — it does NOT wait for OCR/classification/etc to
finish before responding. Those slow steps run in a background task.
This matters because:
  1. A user uploading a 50-page scanned PDF shouldn't stare at a
     spinner for 30+ seconds with no feedback.
  2. If OCR takes longer than the HTTP timeout, the request would
     just fail even though processing was still happening.
The frontend instead polls (or listens via websocket) GET
/documents/{file_id}/status to see progress — a standard async job
pattern used in any real document-processing product.
"""

import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Document
from backend.models.schemas import UploadResponse
from backend.config.settings import settings
from backend.services.pipeline_service import run_ingestion_pipeline

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_id = str(uuid.uuid4())
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    dest_path = settings.upload_dir / f"{file_id}_{file.filename}"

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        file_id=file_id,
        filename=file.filename,
        file_path=str(dest_path),
        processing_status="queued",
    )
    db.add(doc)
    db.commit()

    # Runs AFTER the response is sent — this is what makes upload feel instant.
    background_tasks.add_task(run_ingestion_pipeline, file_id, str(dest_path))

    return UploadResponse(
        file_id=file_id, filename=file.filename, processing_status="queued"
    )
