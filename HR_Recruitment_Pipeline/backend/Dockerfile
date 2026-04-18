# ── Stage 1: Build dependencies ──────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production image ────────────────────────────────────────
FROM python:3.11-slim AS production

# Metadata
LABEL maintainer="Khushi Sorathia"
LABEL description="HR Recruitment Pipeline – FastAPI Backend"

# Security: run as non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy pre-built dependencies from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY ./app ./app

# Create directory for SQLite (when not using Postgres)
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Environment defaults (overridden by docker-compose / .env)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL="sqlite:///./data/hr_pipeline.db"

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
