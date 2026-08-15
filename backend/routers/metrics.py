"""
Metrics Router — GET /metrics.

WHY THIS PULLS FROM QueryLog INSTEAD OF RUNNING A FRESH BENCHMARK:
evaluation/benchmark.py needs hand-labeled ground truth (which chunks
SHOULD be relevant, what the answer SHOULD say) - that only exists for
your curated test cases, run manually/in CI. This endpoint reports on
REAL production query traffic instead: every question actually asked
by a real user, logged automatically in QueryLog by
backend/routers/query.py. Together they cover both angles: benchmark
results answer "is my system good on cases I've verified," this
endpoint answers "how is it actually performing on real usage."
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.session import get_db
from backend.database.models import QueryLog, Document
from evaluation.latency import compute_latency_stats

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(db: Session = Depends(get_db)):
    logs = db.query(QueryLog).all()
    latencies = [log.latency_ms for log in logs if log.latency_ms is not None]

    total_documents = db.query(func.count(Document.id)).scalar()
    by_status = dict(
        db.query(Document.processing_status, func.count(Document.id))
        .group_by(Document.processing_status)
        .all()
    )

    return {
        "total_documents_uploaded": total_documents,
        "documents_by_status": by_status,
        "total_queries": len(logs),
        "query_latency": compute_latency_stats(latencies),
    }
