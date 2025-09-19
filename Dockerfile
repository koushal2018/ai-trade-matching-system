# Multi-stage build for production deployment
FROM python:3.12-slim as builder

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r trader && useradd -r -g trader trader

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY src/ ./src/
COPY .env.example ./.env.example

# Create necessary directories
RUN mkdir -p data/BANK data/COUNTERPARTY storage && \
    chown -R trader:trader /app

# Switch to non-root user
USER trader

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import sys; sys.path.append('./src'); from latest_trade_matching_agent.tools.trade_tools import TradeStorageTool; exit(0)"

# Default command
CMD ["python", "-m", "src.latest_trade_matching_agent.main"]

# Labels for metadata
LABEL maintainer="AI Trade Matching System" \
      version="1.0" \
      description="AI-powered trade matching system with multi-LLM support"