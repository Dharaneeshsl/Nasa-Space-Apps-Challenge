# ==============================================================================
# CombustionLens: Multi-Stage Dockerfile for Hugging Face Spaces (Docker SDK)
#
# NOTE ON HARDWARE SPECS:
# Hugging Face Space hardware specs (e.g., CPU Basic: 2 vCPU, 16 GB RAM or Free tier)
# are NOT stated as fixed facts; they must be re-verified before the event.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React 18 + TypeScript + Vite Frontend
# ------------------------------------------------------------------------------
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Install package dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build static artifacts
COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Serve Static Assets + REST API with Python FastAPI & Uvicorn
# ------------------------------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    HF_HOME=/home/user/.cache/huggingface

WORKDIR /app

# Install system dependencies needed for C-extensions / DuckDB / PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs as user with UID 1000
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Pre-install CPU-only PyTorch to avoid 2-3 GB of unnecessary GPU CUDA packages
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache embedding and cross-encoder models into container image (avoids runtime download lag)
RUN mkdir -p /home/user/.cache/huggingface && \
    python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('all-MiniLM-L6-v2'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Copy application configuration and codebase
COPY config.yaml .
COPY api/ ./api/
COPY core/ ./core/
COPY data/ ./data/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY eval/ ./eval/

# Initialize DuckDB schema and verify directory structures
RUN python scripts/collect_nasa_data.py && \
    python scripts/prepare_nasa_tables.py && \
    python scripts/load_experiments.py && \
    python scripts/build_index.py

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder --chown=user:user /app/frontend/dist ./frontend/dist

# Ensure non-root user owns the application directory and cache
RUN chown -R user:user /app /home/user

# Switch to non-root user
USER user

# Hugging Face Spaces standard listening port
EXPOSE 7860

# Launch Uvicorn ASGI server serving FastAPI and mounted static React SPA
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
