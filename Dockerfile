# syntax=docker/dockerfile:1
# Multi-stage, non-root, minimal attack surface.
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 UV_SYSTEM_PYTHON=1
WORKDIR /app

# deps layer (cached)
FROM base AS deps
RUN pip install --no-cache-dir uv
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system -e .

# runtime
FROM base AS runtime
RUN useradd --create-home --uid 10001 antar
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY src ./src
COPY knowledge ./knowledge
USER antar
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')" || exit 1
# Webapp (FastAPI/uvicorn). For the MCP server: override CMD with `python -m antar.mcp_server`.
CMD ["python", "-m", "uvicorn", "antar.webapp:app", "--host", "0.0.0.0", "--port", "8000"]
