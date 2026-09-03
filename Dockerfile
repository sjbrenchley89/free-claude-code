# Free Claude Code Server - Docker Image
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
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 fcc

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir \
    fastapi[standard]>=0.141.1 \
    uvicorn>=0.52.1 \
    httpx[socks]>=0.28.1 \
    httpx2[socks]>=2.7.0 \
    markdown-it-py>=4.2.0 \
    pydantic>=2.13.4 \
    python-dotenv>=1.2.2 \
    tiktoken>=0.13.0 \
    python-telegram-bot>=22.8

# Create startup script that runs the server using python -m
RUN echo '#!/usr/bin/env python\nfrom free_claude_code.cli.commands import serve\nif __name__ == "__main__":\n    serve()' > /app/run_server.py && \
    chmod +x /app/run_server.py

# Set PYTHONPATH so the src directory is in the Python path
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Switch to non-root user
USER fcc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Expose port
EXPOSE 8000

# Run the server using the startup script
CMD ["python", "/app/run_server.py"]
