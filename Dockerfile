# --- Builder Stage ---
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies and playwright browsers
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# --- Production Stage ---
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app



COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Install system dependencies needed by Playwright (must be root)
RUN playwright install-deps

# Create appuser
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Install Playwright browser binary as appuser
RUN playwright install chromium

COPY --chown=appuser:appuser . .

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
