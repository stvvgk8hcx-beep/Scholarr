# Scholarr — Self-hosted academic file management
# Single-stage Python build (no Node.js needed, pure Python frontend)
FROM python:3.11-slim

LABEL maintainer="Calvin Pawluck"
LABEL description="Self-hosted academic file management system"
LABEL version="0.1.0"

WORKDIR /app

# System deps — mysql client libs and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml pyproject.toml
COPY scholarr scholarr
COPY alembic.ini alembic.ini

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[mysql]"

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/backups

# Non-root user for security
RUN useradd -m -u 1000 scholarr && \
    chown -R scholarr:scholarr /app

USER scholarr

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8787/health || exit 1

CMD ["uvicorn", "scholarr.app:app", "--host", "0.0.0.0", "--port", "8787"]
