# ─── Base Image ───────────────────────────────────────────────
FROM python:3.13-slim

# ─── Environment Variables ────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ─── System Dependencies ──────────────────────────────────────
# Required for numpy, torch, sentence-transformers, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ─── Working Directory ────────────────────────────────────────
WORKDIR /app

# ─── Dependency Layer (IMPORTANT for caching) ─────────────────
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ─── Copy Application Code ────────────────────────────────────
COPY ./app ./app

# ─── Expose Port ──────────────────────────────────────────────
EXPOSE 8000

# ─── Default Command (override in docker-compose if needed) ───
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
