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

# Strict low-memory settings for PaddlePaddle and CPU threads
ENV FLAGS_allocator_strategy=naive_best_fit \
    FLAGS_fraction_of_cpu_memory_to_use=0.05 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models during Docker build so runtime uploads never spike memory or download over network
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='en', use_angle_cls=False, show_log=False)"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .

# Where uploaded files, the SQLite DB, and the persisted FAISS index
# all live. Mount this as a volume in production (/app/data).
RUN mkdir -p data/uploads data/vector_store

EXPOSE 8000

# Uses PORT if provided by Railway/Render/Cloud provider, otherwise defaults to 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
