# Multi-stage build for production-ready FastAPI server

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and constraints
COPY requirements.txt .
COPY constraints.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip==24.0 setuptools wheel && \
    pip install --no-cache-dir --constraint constraints.txt -r requirements.txt

# Verify critical packages are installed correctly
RUN python -c "import numpy; print(f'NumPy version: {numpy.__version__}')" && \
    python -c "import tensorflow; print(f'TensorFlow version: {tensorflow.__version__}')" && \
    python -c "import torch; print(f'PyTorch version: {torch.__version__}')" && \
    python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/quarantine /app/ml/models

# Create non-root user
RUN useradd -m -u 1000 dlpuser && \
    chown -R dlpuser:dlpuser /app

# Switch to non-root user
USER dlpuser

# Expose ports
EXPOSE 8000
EXPOSE 55000

# Set default port and workers
ENV PORT=${PORT:-55000}
ENV UVICORN_WORKERS=${UVICORN_WORKERS:-4}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers ${UVICORN_WORKERS}
