"""
Pydantic schemas = the API's request/response contract.

WHY THESE ARE SEPARATE FROM database/models.py:
database/models.py describes DB TABLES (SQLAlchemy).
This file describes API SHAPES (Pydantic) — what JSON goes in and out
of your endpoints. They often look similar but serve different jobs:
you never want to accidentally expose an internal DB column (like a
file's server-side path) to the frontend just because it's in the
table. Keeping them separate is a deliberate security/design boundary.
"""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    processing_status: str


class DocumentStatusResponse(BaseModel):
    file_id: str
    filename: str
    document_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    processing_status: str
    verification_status: Optional[str] = None
    risk_score: Optional[int] = None
    error: Optional[Any] = None


class QueryRequest(BaseModel):
    file_id: str
    question: str


class QueryResponse(BaseModel):
    answer: str
    confidence: Optional[float] = None
    source_chunks: list[dict] = []
    latency_ms: Optional[int] = None


class VerificationResult(BaseModel):
    status: str  # "OK" | "Warning" | "Failed"
    issues: list[str] = []


class RiskResult(BaseModel):
    risk_score: int
    reasons: list[str] = []


class SummaryResponse(BaseModel):
    executive_summary: str
    key_findings: list[str] = []
    important_dates: list[str] = []
    action_items: list[str] = []
