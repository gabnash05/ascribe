# ─── Base Image ───────────────────────────────────────────────
FROM python:3.12-slim

ARG EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
ARG EMBEDDING_CACHE_DIR=/app/model_cache

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=${EMBEDDING_CACHE_DIR} \
    SENTENCE_TRANSFORMERS_HOME=${EMBEDDING_CACHE_DIR}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
