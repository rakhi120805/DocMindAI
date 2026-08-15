"""
Database models (SQLite via SQLAlchemy).

WHY WE NEED BOTH SQLite AND FAISS (common interview question!):
- FAISS stores VECTORS (for "find text that means something similar").
- SQLite stores FACTS (for "what is the exact invoice amount",
  "who uploaded this", "when was it processed").
LLMs are bad at exact lookups from fuzzy similarity search — you don't
want a vector search to accidentally return the wrong invoice's amount.
So structured facts go in SQLite, and are pulled with exact SQL queries,
never guessed from embeddings.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Document(Base):
    """One row per uploaded file."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True)  # public-facing UUID
    filename = Column(String)
    file_path = Column(String)

    # Filled in by the Classification Agent (Step 3 of the pipeline)
    document_type = Column(String, nullable=True)       # "Invoice", "Passport", ...
    classification_confidence = Column(Float, nullable=True)

    # Filled in by Metadata Extraction (Step 4)
    extracted_metadata = Column(JSON, nullable=True)     # {"pan": "...", "amount": ...}

    # Filled in by the Verification Agent
    verification_status = Column(String, nullable=True)  # "OK" | "Warning" | "Failed"
    verification_notes = Column(JSON, nullable=True)

    # Filled in by the Risk Agent
    risk_score = Column(Integer, nullable=True)           # 0-100

    processing_status = Column(String, default="queued")  # queued|processing|done|failed
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    queries = relationship("QueryLog", back_populates="document")


class DocumentChunk(Base):
    """
    One row per text chunk. We store page_number + char offsets here
    so that later we can highlight citations (show which page an
    answer came from) without re-parsing the PDF.
    """
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, index=True)
    chunk_index = Column(Integer)
    page_number = Column(Integer, nullable=True)
    text = Column(Text)
    vector_id = Column(Integer, nullable=True)  # position in the FAISS index


class QueryLog(Base):
    """
    Every question a user asks gets logged here — this is what powers
    the Evaluation Layer (latency, confidence, retrieved context, etc).
    """
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    question = Column(Text)
    answer = Column(Text, nullable=True)
    retrieved_chunk_ids = Column(JSON, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="queries")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    format = Column(String)       # "markdown" | "pdf" | "json" | "csv"
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
