# syntax=docker/dockerfile:1
# ----------------------------------------------------------------------------
# Knowledge Tracing ML pipeline — reproducible container image.
# Slim CPU base keeps the image small; deps are installed in a cached layer
# before the source is copied so code changes don't re-trigger pip installs.
# ----------------------------------------------------------------------------
FROM python:3.11-slim

# - PYTHONDONTWRITEBYTECODE: no .pyc clutter
# - PYTHONUNBUFFERED: stream logs straight to docker logs
# - PIP_NO_CACHE_DIR: smaller image (no pip wheel cache)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg \
    MLFLOW_ALLOW_FILE_STORE=true

WORKDIR /app

# System libs required by lightgbm (libgomp) and matplotlib; cleaned up after.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only torch separately (no CUDA payload) to keep the image lean.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    || pip install --no-cache-dir torch

# Dependency layer (cached unless requirements.txt changes).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code + committed sample dataset.
COPY . .

# Run as a non-root user (security: limits blast radius if the container is compromised).
RUN useradd --create-home --uid 1000 mluser \
    && chown -R mluser:mluser /app
USER mluser

# Default: run the pipeline on the committed sample (fully offline, reproducible).
# Override CMD to run on the full dataset:  docker run kt-pipeline ... --data-source full
ENTRYPOINT ["python", "-m", "src.pipeline"]
CMD ["--data-source", "sample"]
