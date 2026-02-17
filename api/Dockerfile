# ============================================================================
# TechCare Bot - API Dockerfile
# ============================================================================

FROM python:3.11-slim

LABEL maintainer="Carsten Eckhardt <carsten@eckhardt-marketing.de>"
LABEL version="1.0.0"
LABEL description="TechCare Bot API - FastAPI Backend"

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY api/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download Spacy German model (für PII Detection)
RUN python -m spacy download de_core_news_md

# Copy API code
COPY api/ /app/api/

# Copy TechCare core (für Tool-Logic)
COPY techcare/ /app/techcare/

# Create data directory
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
