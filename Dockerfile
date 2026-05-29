# syntax=docker/dockerfile:1
# Multi-stage build: builder installs deps, slim runtime runs the server.

# ── stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tooling; remove cache in the same layer.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/

# Install the project + runtime deps into an isolated prefix so we can copy
# only the installed files into the final stage.
RUN pip install --no-cache-dir --prefix=/install -e .


# ── stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user (uid/gid 10001, no home directory shell).
RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --no-create-home --shell /sbin/nologin appuser

# Copy installed packages from builder.
COPY --from=builder /install /usr/local

# Copy application source (read-only at runtime).
COPY --chown=appuser:appgroup src/ /app/src/

WORKDIR /app

ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Bind to all interfaces so the container is reachable; the code-layer
    # NeighborJack warning is suppressed when RENDER or CONTAINER=1 is set.
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    # SCALE-001: select transport via env var instead of --http CLI flag.
    MCP_TRANSPORT=streamable-http

# Drop to non-root before any network activity.
USER appuser

EXPOSE 8000

# Lightweight health-check: the /health path returns 200 on the MCP HTTP
# transport; adjust if you add a dedicated /healthz endpoint.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

ENTRYPOINT ["python", "-m", "openlex_mcp.server"]
# Transport, host, and port are set via ENV above — no CLI flags needed.
# Override with e.g. docker run --env MCP_TRANSPORT=stdio for stdio mode.
