# Free Claude Code Server - Production Docker Image
FROM python:3.14-slim

# Set environment variables for Python and system
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 fcc

# Set working directory
WORKDIR /app

# Copy project files
COPY --chown=fcc:fcc pyproject.toml uv.lock README.md LICENSE ./
COPY --chown=fcc:fcc src ./src

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Install dependencies and package using uv
# Use uv to sync all dependencies and install the package
RUN uv pip compile pyproject.toml -o requirements.txt && \
    pip install --no-cache-dir --compile -r requirements.txt && \
    pip install --no-cache-dir --compile -e .

# Switch to non-root user
USER fcc

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5).read()" || exit 1

# Expose port
EXPOSE 8000

# Run the server
CMD ["fcc-server"]
