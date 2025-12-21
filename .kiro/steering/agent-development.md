---
inclusion: fileMatch
fileMatchPattern: "**/deployment/**/*.py"
---

# Agent Development Guidelines

## Agent Structure
Each agent lives in `deployment/<agent_name>/` with:
- `<agent_name>_strands.py` - Main agent implementation
- `agentcore.yaml` - AgentCore Runtime configuration
- `deploy.sh` - Deployment script
- `requirements.txt` - Agent-specific dependencies

## AgentCore Runtime Pattern
```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

app = BedrockAgentCoreApp()

@app.ping
def health_check() -> PingStatus:
    """Health check for AgentCore Runtime."""
    return PingStatus.HEALTHY

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """Main agent entrypoint."""
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    # ... agent logic
    return {"success": True, "correlation_id": correlation_id}
```

## Observability Integration
```python
from bedrock_agentcore.observability import Observability

observability = Observability(
    service_name="agent-name",
    stage="development",  # or "production"
    verbosity="high"
)

with observability.start_span("operation_name") as span:
    span.set_attribute("correlation_id", correlation_id)
    span.set_attribute("trade_id", trade_id)
    # ... operation
    span.set_attribute("success", True)
```

## AgentCore Memory (Optional)
```python
from bedrock_agentcore.memory.session import MemorySessionManager
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole

memory_session = MemorySessionManager(
    memory_id="memory-resource-id",
    region_name="us-east-1"
)
```

## Standard Response Format
```python
return {
    "success": True,
    "correlation_id": correlation_id,
    "agent_name": AGENT_NAME,
    "agent_version": AGENT_VERSION,
    "processing_time_ms": processing_time_ms,
    "token_usage": {
        "input_tokens": N,
        "output_tokens": N,
        "total_tokens": N
    },
    # ... agent-specific fields
}
```

## Environment Variables
- `AWS_REGION` - AWS region (default: us-east-1)
- `S3_BUCKET_NAME` - S3 bucket for documents
- `DYNAMODB_BANK_TABLE` - Bank trades table
- `DYNAMODB_COUNTERPARTY_TABLE` - Counterparty trades table
- `BEDROCK_MODEL_ID` - Model ID for agent
- `BYPASS_TOOL_CONSENT=true` - Required for AgentCore Runtime
