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
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")  # extra safety net
import torch  # noqa: F401 - imported for its side effect (DLL load order), not used directly here

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.session import init_db
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
    print(f"[DocMind AI] LLM provider: {settings.llm_provider} | model: {settings.llm_model_name}")


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}