FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim
WORKDIR /app

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=us-east-1 \
    AWS_DEFAULT_REGION=us-east-1

# Copy entire project first (as root)
COPY . /app/

# Debug: List files to see what was copied
RUN ls -la /app/

# Install dependencies
RUN uv pip install -r /app/requirements.txt

# Install OTEL
RUN uv pip install aws-opentelemetry-distro==0.12.2

# Create non-root user and change ownership
RUN useradd -m -u 1000 bedrock_agentcore && \
    chown -R bedrock_agentcore:bedrock_agentcore /app

USER bedrock_agentcore

EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Use the full module path
CMD ["opentelemetry-instrument", "python", "-m", "exception_management_agent_strands"]
