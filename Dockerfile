# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.14-slim-bookworm

# ==================== Builder ====================
FROM ${PYTHON_IMAGE} AS builder

# uv is pinned to the floor required by pyproject.toml ([tool.uv] required-version).
ARG UV_VERSION=0.12.13
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PIP_ROOT_USER_ACTION=ignore

RUN pip install --no-cache-dir "uv==${UV_VERSION}"

WORKDIR /app

# Resolve dependencies first so the layer caches independently of source edits.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ==================== Runtime ====================
FROM ${PYTHON_IMAGE} AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app

ENV PATH="/app/.venv/bin:$PATH" \
    HOME="/home/app" \
    PYTHONUNBUFFERED=1 \
    FCC_OPEN_BROWSER=false \
    HOST=0.0.0.0 \
    PORT=8082

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src

USER app

EXPOSE 8082

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

CMD ["fcc-server"]
