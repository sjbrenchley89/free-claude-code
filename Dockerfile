# Multi-stage build for Free Claude Code server
# Stage 1: Build environment
FROM python:3.14-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set uv in PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
WORKDIR /build
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

# Build the package
RUN uv build --wheel

# Stage 2: Runtime environment
FROM python:3.14-slim

# Set environment variables for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Install runtime dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 fcc

# Set working directory
WORKDIR /app

# Copy built wheel from builder
COPY --from=builder /build/dist/*.whl .

# Install the package
RUN pip install --no-cache-dir *.whl && rm *.whl

# Change ownership to fcc user
RUN chown -R fcc:fcc /app

# Switch to non-root user
USER fcc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Expose port
EXPOSE 8000

# Run the server
CMD ["fcc-server"]
