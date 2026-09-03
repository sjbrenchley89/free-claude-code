# Free Claude Code Server - Docker Image
FROM python:3.13-slim

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

# Install all dependencies from pyproject.toml
RUN pip install --no-cache-dir \
    'fastapi[standard]>=0.141.1' \
    'uvicorn>=0.52.1' \
    'httpx[socks]>=0.28.1' \
    'httpx2[socks]>=2.7.0,<3' \
    'markdown-it-py>=4.2.0' \
    'pydantic>=2.13.4' \
    'python-dotenv>=1.2.2' \
    'tiktoken>=0.13.0' \
    'python-telegram-bot>=22.8' \
    'discord.py>=2.7.1' \
    'openai>=3.2.0' \
    'anthropic>=0.40.0' \
    'loguru>=0.7.0' \
    'aiohttp>=3.14.3' \
    'jsonschema>=4.25.0' \
    'google-auth[requests]>=2.56.3' \
    'requests[socks]>=2.34.2'

# Set PYTHONPATH so the src directory is in the Python path
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Adjust permissions for the app directory
RUN chown -R fcc:fcc /app

# Switch to non-root user
USER fcc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Expose port
EXPOSE 8000

# Run the server - import and call the serve function
CMD ["python", "-c", "from free_claude_code.cli.commands import serve; serve()"]
