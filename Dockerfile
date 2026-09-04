# Production Dockerfile for free-claude-code proxy server
# Supports Python 3.14.7 with uv package manager

FROM python:3.14.7-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.cargo/bin:$PATH" && \
    uv --version

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY scripts ./scripts

# Install dependencies with uv
ENV PATH="/root/.cargo/bin:$PATH"
RUN uv sync --frozen

# Create config directory
RUN mkdir -p /etc/fcc

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "import httpx; httpx.get('http://localhost:8082/health', timeout=5)" || exit 1

# Run the server
CMD ["uv", "run", "fcc-server"]
