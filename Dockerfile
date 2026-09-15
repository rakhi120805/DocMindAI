# DocMind AI backend — production image
FROM python:3.11-slim

WORKDIR /app

# System dependencies needed by our Python packages:
# - libgl1/libglib2.0-0: required by PaddleOCR/OpenCV under the hood,
#   even in a headless server with no display.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Where uploaded files, the SQLite DB, and the persisted FAISS index
# all live. Mount this as a volume in production (/app/data).
RUN mkdir -p data/uploads data/vector_store

EXPOSE 8000

# Uses PORT if provided by Railway/Render/Cloud provider, otherwise defaults to 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
