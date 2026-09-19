# DocMind AI backend — production image
#
# WHY python:3.11-slim: full-size python images bundle a lot of build
# tools/docs we don't need at runtime, bloating the image and slowing
# every deploy. slim keeps the base small; we install exactly the
# system packages our dependencies actually need (below) rather than
# relying on the full image's kitchen sink.
FROM python:3.11-slim

WORKDIR /app

# System dependencies needed by our Python packages:
# - libgl1/libglib2.0-0: required by PaddleOCR/OpenCV under the hood,
#   even in a headless server with no display - these libraries expect
#   certain graphics libs to exist even if never used for rendering.
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
# all live (consolidated - see backend/config/settings.py). Mount
# this as a volume in production (see docker-compose.yml) so it all
# survives a container restart/redeploy - without a volume, this
# resets every time the container rebuilds, defeating the whole
# point of the FAISS disk-persistence code.
RUN mkdir -p data/uploads data/vector_store

EXPOSE 8000

# Uses PORT if provided by Railway/Render/Cloud provider, otherwise defaults to 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
