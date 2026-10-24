# =========================================================================
# Product Return Risk Intelligence Platform - FastAPI Backend Dockerfile
# =========================================================================
FROM python:3.11-slim as base

# Set environment configurations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install minimal OS dependencies for health check & networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application codebase and artifacts
COPY app /app/app
COPY artifacts /app/artifacts
COPY dataset /app/dataset
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY .env.example /app/.env.example

# Create unprivileged service user for runtime security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose standard FastAPI application port
EXPOSE 8000

# Automated healthcheck monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Launch uvicorn ASGI production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
