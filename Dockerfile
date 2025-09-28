# Multi-stage build for optimized image size and security
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements files
COPY requirements.txt .
COPY requirements-eks.txt .

# Combine requirements files
RUN cat requirements-eks.txt >> requirements.txt

# Install Python dependencies to a specific location
RUN pip install --no-cache-dir -r requirements.txt --target /app/deps

# Production stage
FROM python:3.11-slim

# Install runtime dependencies and build tools needed for MCP
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    curl \
    gcc \
    g++ \
    build-essential \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install pip packages globally including MCP server
RUN pip install --no-cache-dir \
    awslabs.dynamodb-mcp-server \
    && rm -rf /root/.cache/pip

# Copy Python packages from builder
COPY --from=builder /app/deps /app/deps

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY *.py ./
COPY pyproject.toml ./

# Create necessary directories
RUN mkdir -p /tmp/processing /app/logs /app/data

# Create non-root user for security
RUN useradd -m -u 1000 trader && \
    chown -R trader:trader /app /tmp/processing

# Switch to non-root user
USER trader

# Add deps to Python path
ENV PYTHONPATH=/app/deps:$PYTHONPATH

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FASTMCP_LOG_LEVEL=ERROR \
    LITELLM_LOG=ERROR \
    XDG_DATA_HOME=/tmp/processing \
    XDG_CONFIG_HOME=/tmp/processing \
    PATH=/app/deps/bin:$PATH

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["python", "-m", "uvicorn", "src.latest_trade_matching_agent.eks_main:app", "--host", "0.0.0.0", "--port", "8080"]