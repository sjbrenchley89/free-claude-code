# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.14.7-slim-bookworm

# ==================== Builder ====================
FROM ${PYTHON_IMAGE} AS builder

# Pin the toolchain and package metadata for builds without Git history.
ARG UV_VERSION=0.12.13
ARG FCC_VERSION=6.5.11
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PIP_ROOT_USER_ACTION=ignore \
    SETUPTOOLS_SCM_PRETEND_VERSION=${FCC_VERSION}

RUN --mount=type=secret,id=fcc_ca,target=/run/secrets/fcc-ca.pem \
    if [ -f /run/secrets/fcc-ca.pem ]; then \
        export PIP_CERT=/run/secrets/fcc-ca.pem; \
    fi; \
    pip install --no-cache-dir "uv==${UV_VERSION}"

WORKDIR /app

# Resolve dependencies first so the layer caches independently of source edits.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=secret,id=fcc_ca,target=/run/secrets/fcc-ca.pem \
    if [ -f /run/secrets/fcc-ca.pem ]; then \
        export SSL_CERT_FILE=/run/secrets/fcc-ca.pem; \
    fi; \
    uv sync --locked --no-dev --no-install-project

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY scripts/update ./scripts/update

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=secret,id=fcc_ca,target=/run/secrets/fcc-ca.pem \
    if [ -f /run/secrets/fcc-ca.pem ]; then \
        export SSL_CERT_FILE=/run/secrets/fcc-ca.pem; \
    fi; \
    uv sync --locked --no-dev

# ==================== Runtime ====================
FROM ${PYTHON_IMAGE} AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app \
    && install -d -m 0700 -o app -g app /home/app/.fcc

ENV PATH="/app/.venv/bin:$PATH" \
    HOME="/home/app" \
    PYTHONUNBUFFERED=1 \
    FCC_OPEN_BROWSER=false \
    PROXY_AUTH_ENABLED=true \
    HOST=0.0.0.0 \
    PORT=8082

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src

USER app

EXPOSE 8082

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

CMD ["python", "-m", "free_claude_code.cli.cloud"]
