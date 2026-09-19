"""
App entrypoint.

Run with:  uvicorn backend.main:app --reload
Then visit http://127.0.0.1:8000/docs for the auto-generated,
interactive API docs (FastAPI's built-in Swagger UI) — genuinely
useful to demo live in an interview.
"""

import os
# MUST happen before ANYTHING imports torch or paddle (even indirectly).
#
# On Windows, PaddlePaddle and PyTorch each bundle their own copy of
# native runtime DLLs, and loading both into one process can conflict
# depending on WHICH ONE LOADS FIRST - confirmed by direct testing:
# `import paddleocr` then `import torch` crashes with WinError 127 on
# torch's shm.dll, but `import torch` then `import paddleocr` works
# fine. In this app, OCRAgent (paddle) always runs before the Indexer
# (torch, via sentence-transformers) in the normal pipeline order -
# exactly the bad order. Forcing torch to import here, at startup,
# guarantees the safe order regardless of which agent runs first.
# Strict low-memory flags for PaddlePaddle and CPU threads
os.environ["FLAGS_allocator_strategy"] = "naive_best_fit"
os.environ["FLAGS_fraction_of_cpu_memory_to_use"] = "0.05"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")  # extra safety net
import torch  # noqa: F401 - imported for its side effect (DLL load order), not used directly here
torch.set_num_threads(1)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.session import init_db, SessionLocal
from backend.database.models import Document
from backend.routers import upload, query, documents, metrics
from backend.config.settings import settings

app = FastAPI(title=settings.app_name)

# Allows the (future) React frontend, running on a different port,
# to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your real frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(query.router)
app.include_router(documents.router)
app.include_router(metrics.router)


@app.on_event("startup")
def on_startup():
    init_db()
    # If the container crashed or restarted while a background task was running,
    # clean up stranded "processing" documents so the frontend doesn't poll forever.
    db = SessionLocal()
    try:
        stranded = db.query(Document).filter(Document.processing_status.in_(["processing", "queued"])).all()
        for d in stranded:
            d.processing_status = "failed"
            d.verification_notes = {"error": "Server restarted while processing was in flight. Please re-upload this file."}
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    print(f"[DocMind AI] LLM provider: {settings.llm_provider} | model: {settings.llm_model_name}")


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}