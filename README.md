# DocMind AI

**Multi-Agent Document Intelligence & Verification Platform**

Upload a document (PDF, scanned image) and DocMind AI reads it (OCR),
figures out what it is (classification), pulls out structured facts
(metadata extraction), checks those facts for problems (verification),
scores it for risk, and lets you ask natural-language questions about
it (RAG-based Q&A) — all coordinated by a LangGraph-style Supervisor
across 8 specialized agents.

Everything runs **locally** — Ollama for the LLM, PaddleOCR for OCR,
FAISS + Sentence Transformers for retrieval. No paid API keys required.

---

## Architecture

```
Upload (PDF/image)
      │
      ▼
 OCR Agent  ──────────►  PyMuPDF (PDF→image) → Pillow (enhance) → PaddleOCR (read text)
      │
      ▼
 Classification Agent  ─►  LLM decides document type (Invoice, Passport, ...)
      │
      ▼
 Metadata Extraction Agent  ─►  LLM pulls type-specific fields (amount, PAN, dates...)
      │
      ▼
 Verification Agent  ─►  Regex/rule-based checks (valid PAN? negative amount?)
      │
      ▼
 Risk Agent  ─►  Combines verification issues into a 0-100 risk score
      │
      ▼
 Indexer  ─►  Chunk text → embed (Sentence Transformers) → store (FAISS)
```

At query time, a separate flow runs:

```
Question ─► Retrieval Agent (FAISS similarity search) ─► QA Agent (LLM answers from retrieved context)
```

All of this is coordinated by `agents/supervisor.py`, which passes a
shared state dict between agents — each agent's output becomes the
next agent's input.

---

## Project structure

```
DocMindAI/
├── backend/
│   ├── main.py              # FastAPI app entrypoint
│   ├── config/settings.py   # Central, typed configuration
│   ├── database/            # SQLAlchemy models + session handling
│   ├── models/schemas.py    # Pydantic request/response schemas
│   ├── routers/             # /upload, /query, /documents, /metrics
│   └── services/            # LLM client, pipeline orchestration
├── agents/                  # One file per agent + the Supervisor
├── ocr/                     # PDF/image preprocessing, OCR engine, text cleaning
├── rag/                     # Chunking, embedding, vector store, indexing
├── evaluation/              # Precision/recall, faithfulness, latency, benchmarking
├── tests/                   # Automated tests + fake-service test doubles
├── requirements.txt
└── .env.example
```

---

## Setup

```bash
cd DocMindAI
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**LLM (Ollama)** — install from [ollama.com](https://ollama.com), then:
```bash
ollama pull qwen2.5:7b-instruct   # or qwen2.5:3b-instruct on lower-RAM machines
ollama serve                      # usually auto-starts after install
```

**Environment**
```bash
cp .env.example .env
# make sure .env has: LLM_PROVIDER=ollama
```

**Run the server**
```bash
uvicorn backend.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for the interactive API (Swagger UI).

> First-run note: PaddleOCR and Sentence Transformers both download
> model weights the first time they're actually used (a few hundred MB
> each), then cache them locally. The very first document you process
> will be noticeably slower than subsequent ones.

---

## API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/upload` | POST | Upload a file. Returns instantly with a `file_id`; processing runs in the background. |
| `/documents/{file_id}/status` | GET | Poll processing progress. Returns `error` detail if `processing_status` is `"failed"`. |
| `/documents` | GET | List all uploaded documents. |
| `/query` | POST | Ask a question about a processed document. Returns an answer + a `confidence` (faithfulness) score. |
| `/metrics` | GET | Real usage stats: document counts by status, query volume, latency percentiles. |

---

## Running tests

```bash
pytest tests/test_evaluation.py -v
```

These test the evaluation metrics (precision/recall, faithfulness,
latency percentiles, character error rate) directly — no Ollama or
PaddleOCR required, so they're a good first check that your Python
environment itself is set up correctly.

---

## Troubleshooting

**`processing_status` stuck on `"failed"`, `document_type` is `null`**
The pipeline broke before Classification finished. Check the `error`
field from `GET /documents/{file_id}/status` — it'll point to one of:
- **OCR step failed** → PyMuPDF/PaddleOCR not installed correctly, or an unsupported file extension (`ocr/preprocess.py`'s `SUPPORTED_IMAGE_EXTS`)
- **Classification step failed** → almost always Ollama isn't running, or the model in `.env` (`LLM_MODEL_NAME`) doesn't match what you actually pulled (`ollama list` to check)

**`/query` returns 409 Conflict**
The document is still processing — keep polling `/documents/{file_id}/status` until `"done"`.

**Ollama connection errors**
`backend/services/llm_client.py` raises a specific `ConnectionError`
telling you to check `ollama serve` is running and the model is
pulled — read that message, it's meant to be actionable, not generic.

---

## Design decisions worth knowing for interviews

| Question | Where the answer lives |
|---|---|
| Why multiple agents instead of one prompt? | Each `agents/*.py` file — single responsibility, independently testable |
| How do agents talk to each other? | `agents/supervisor.py` — shared state dict passed between agent calls |
| Why background processing for uploads? | `backend/routers/upload.py` docstring |
| Why separate DB models from API schemas? | `backend/models/schemas.py` docstring |
| How would you swap LLM providers? | `backend/services/llm_client.py` — one file, one interface |
| Why regex checks instead of LLM for verification? | `agents/verifier_agent.py` docstring |
| How does retrieval actually find relevant text? | `rag/embedder.py` + `rag/vector_store.py` docstrings |
| Tell me about a bug you caught and fixed | `rag/vector_store.py` docstring — a per-request VectorStore instance would've silently dropped all embeddings between upload and query |
| How do you evaluate quality? | `evaluation/` — precision/recall, faithfulness, latency percentiles, `run_benchmark()` |
| Why percentiles and not just average latency? | `evaluation/latency.py` docstring — a single slow outlier hides in an average but not in p95 |
| How do you detect hallucination without another expensive LLM call? | `evaluation/hallucination.py` docstring — word-grounding heuristic as a cheap first pass, LLM-as-judge as the documented next step |

---

## What's stubbed / not yet built

- Report generation beyond Markdown (PDF/CSV formats)
- FAISS index persistence to disk (currently in-memory only — restarting the server loses the vector index; the `DocumentChunk` SQLite table still keeps chunk text/page data safe)
- Frontend (React)

## Next steps

1. Persist the FAISS index to disk so embeddings survive a server restart
2. Build the React frontend
3. Optional: swap the faithfulness heuristic for LLM-as-judge for higher-fidelity hallucination detection
