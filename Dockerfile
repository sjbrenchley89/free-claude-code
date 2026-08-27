# Free Claude Code Server - Docker Image
# Python 3.14 slim base with optimized dependency installation
FROM python:3.14-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager for fast dependency resolution
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create non-root user for security
RUN useradd -m -u 1000 fcc

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

# Install the package and dependencies with uv
RUN uv pip install --system --compile-bytecode .

# Clean up build dependencies (optional, comment out to reduce layer count)
# RUN apt-get remove -y build-essential git curl && apt-get autoremove -y

# Change ownership to fcc user
RUN chown -R fcc:fcc /app

# Switch to non-root user
USER fcc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Expose port
EXPOSE 8000

# Run the server
CMD ["fcc-server"]
