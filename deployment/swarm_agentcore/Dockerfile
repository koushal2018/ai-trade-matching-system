# =============================================================================
# Secure Multi-stage Dockerfile for HTTP Agent Orchestrator
# Security: Non-root user, no secrets, minimal attack surface
# =============================================================================

# -----------------------------------------------------------------------------
# Build Stage - Install dependencies
# -----------------------------------------------------------------------------
FROM public.ecr.aws/docker/library/python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install globally
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Runtime Stage - Minimal production image
# -----------------------------------------------------------------------------
FROM public.ecr.aws/docker/library/python:3.11-slim

# Metadata labels
LABEL maintainer="trade-matching-team@example.com"
LABEL version="1.0.0"
LABEL description="HTTP Agent Orchestrator for Trade Matching System"
LABEL security.scan="enabled"

WORKDIR /app

# Copy Python packages from builder (global site-packages)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY http_agent_orchestrator.py .
COPY trade_matching_swarm_agentcore_http.py .
COPY idempotency.py .
COPY status_tracker.py .

# Create non-root user and group
RUN groupadd -r agentcore --gid 1000 && \
    useradd -r -g agentcore --uid 1000 --home-dir /app --shell /sbin/nologin agentcore && \
    chown -R agentcore:agentcore /app

# Environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER agentcore

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost', 8080); conn.request('GET', '/ping'); r = conn.getresponse(); exit(0 if r.status == 200 else 1)" || exit 1

# Run application
CMD ["python", "http_agent_orchestrator.py"]
