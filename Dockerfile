# Free Claude Code Server - Production Docker Image
FROM python:3.14-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Install comprehensive system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    git \
    curl \
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 fcc

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

# Install with pip (upgraded for better dependency resolution)
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Clean up unnecessary build files to reduce image size
RUN find /usr/local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /usr/local/lib/python3.14/site-packages/*/tests /usr/local/lib/python3.14/site-packages/*/test

# Switch to non-root user
USER fcc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Expose port
EXPOSE 8000

# Run the server
CMD ["fcc-server"]
