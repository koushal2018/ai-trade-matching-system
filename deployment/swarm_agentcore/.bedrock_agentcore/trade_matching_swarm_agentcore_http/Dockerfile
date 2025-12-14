FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=us-east-1 \
    AWS_DEFAULT_REGION=us-east-1 \
    DEPLOYMENT_STAGE=production \
    AGENT_VERSION=1.0.0 \
    PDF_ADAPTER_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ \
    TRADE_EXTRACTION_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_extraction_agent-KnAx4O4ezw \
    TRADE_MATCHING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_agent-3aAvK64dQz \
    EXCEPTION_MANAGEMENT_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/exception_manager-uliBS5DsX3 \
    AGENT_TIMEOUT_SECONDS=600 \
    MAX_RETRIES=3



COPY requirements.txt requirements.txt
# Install from requirements file
RUN uv pip install -r requirements.txt




RUN uv pip install aws-opentelemetry-distro==0.12.2


# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Copy entire project (respecting .dockerignore)
COPY . .

# Use the full module path

CMD ["opentelemetry-instrument", "python", "-m", "trade_matching_swarm_agentcore_http"]
