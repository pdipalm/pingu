FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates iputils-ping \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app

ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then \
    pip install --no-cache-dir -e ".[dev]"; \
    else \
    pip install --no-cache-dir -e .; \
    fi

ARG INCLUDE_TESTS=false
RUN if [ "$INCLUDE_TESTS" = "true" ]; then mkdir -p /app/tests; fi
COPY tests ./tests
RUN if [ "$INCLUDE_TESTS" != "true" ]; then rm -rf /app/tests; fi

COPY alembic.ini ./
COPY alembic ./alembic
COPY targets.yaml ./