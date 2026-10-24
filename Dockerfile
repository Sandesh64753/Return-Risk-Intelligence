# =========================================================================
# Product Return Risk Intelligence Platform - Unified Full-Stack Dockerfile
# Multi-stage build packaging both React Frontend & FastAPI Backend
# =========================================================================

# Stage 1: Build the React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Install dependencies using cached layers
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source and compile static production bundle
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend Runtime with Embedded React SPA
FROM python:3.11-slim AS runtime

# Set runtime environment configurations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    HOST=0.0.0.0 \
    SERVE_FRONTEND=true \
    FRONTEND_DIST_DIR=/app/frontend_dist

WORKDIR /app

# Install minimal OS dependencies for health check & networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python backend dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend codebase and artifacts
COPY backend/app /app/app
COPY backend/artifacts /app/artifacts
COPY backend/dataset /app/dataset
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/alembic.ini
COPY backend/.env.example /app/.env.example

# Copy compiled React frontend assets from Stage 1
COPY --from=frontend-builder /frontend/dist /app/frontend_dist

# Create unprivileged service user for runtime security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose standard application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# Launch uvicorn ASGI production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
