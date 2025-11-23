# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for spoon_agent using uv
# Optimized for fast builds and minimal image size

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM ghcr.io/astral-sh/uv:0.5.11-python3.12-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy link mode to avoid hard-link warnings
ENV UV_LINK_MODE=copy

# Install dependencies first (separate from code for better caching)
# This layer is cached and only rebuilt when dependencies change
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
# Use cache mount to speed up repeated builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Now install the project (fast since dependencies are already installed)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.12-slim-bookworm AS runtime

# Install runtime dependencies only (curl for healthchecks, ca-certificates for HTTPS)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --from=builder --chown=appuser:appuser /app /app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set Python path
ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

# Run the application
CMD ["python", "-m", "spoon_agent.main"]
