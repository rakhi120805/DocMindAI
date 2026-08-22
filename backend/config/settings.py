"""
Central configuration for DocMind AI.

WHY THIS FILE EXISTS:
Instead of scattering `os.getenv("SOME_VAR")` calls across the codebase,
every setting lives here, in one typed, validated place. Pydantic's
BaseSettings automatically reads from environment variables (and a .env
file), and will raise a clear error at startup if something required is
missing — instead of failing halfway through processing a document.

INTERVIEW TALKING POINT:
"I centralized configuration using Pydantic Settings so the app fails
fast at startup if misconfigured, rather than failing midway through
a user's request."
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "DocMind AI"
    environment: str = "development"  # development | production

    # --- Storage paths ---
    # Consolidated under one data/ directory so a single Docker volume
    # mount covers everything that needs to survive a restart:
    # uploaded files, the FAISS index, and (implicitly, via
    # database_url below) the SQLite file.
    upload_dir: Path = Path("data/uploads")
    vector_store_dir: Path = Path("data/vector_store")

    # --- Database ---
    database_url: str = "sqlite:///./data/docmind.db"

    # --- LLM provider ---
    # We keep this provider-agnostic on purpose: swapping between
    # Ollama (local dev), Groq (fast + free tier, great for a live
    # demo), OpenAI, or Anthropic should mean changing THIS value, not
    # rewriting every agent.
    llm_provider: str = "ollama"  # e.g. "openai", "groq", "anthropic", "ollama"
    llm_model_name: str = "qwen2.5:7b-instruct"  # matches architecture doc's suggested model
    llm_api_key: str = ""  # unused for ollama - it's local, no key needed
    ollama_base_url: str = "http://localhost:11434"

    # --- OCR ---
    ocr_engine: str = "paddleocr"

    # --- CORS ---
    # "*" is fine for local dev (any origin can call the API), but in
    # production this should be your actual deployed frontend URL -
    # otherwise ANY website could make authenticated-looking requests
    # to your API from a user's browser. Comma-separated for multiple
    # origins (e.g. a Vercel preview URL + your custom domain).
    cors_origins: str = "*"

    # --- Chunking ---
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 128

    # --- Retrieval ---
    top_k_chunks: int = 5

    # NOTE: this MUST be `model_config = SettingsConfigDict(...)`, not the
    # older `class Config: env_file = ".env"` syntax. That older style is
    # a pydantic v1 pattern - with pydantic-settings v2 it can silently
    # fail to load the .env file at all (no error, it just falls back to
    # every field's hardcoded default). This was a real bug caught while
    # debugging why LLM_MODEL_NAME in .env wasn't taking effect - the
    # server kept using the default "qwen2.5:7b-instruct" no matter what
    # .env said, because .env was never actually being read.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()