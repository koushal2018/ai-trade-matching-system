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

## Observability Integration (OTEL Auto-Instrumentation)
AgentCore Runtime automatically instruments agents via OpenTelemetry when `strands-agents[otel]` is installed.
**Do NOT use manual `Observability` class** - it causes 202 warnings and degraded monitoring.

```python
# requirements.txt - Include OTEL dependencies
# strands-agents[otel]>=0.1.0
# aws-opentelemetry-distro>=0.2.0
# opentelemetry-api>=1.20.0
# opentelemetry-sdk>=1.20.0
# opentelemetry-exporter-otlp>=1.20.0

# In your agent code - use structured logging instead of manual spans
import logging
logger = logging.getLogger(__name__)

# Log with correlation_id for tracing (OTEL captures these automatically)
logger.info(
    f"[{correlation_id}] Operation completed - "
    f"trade_id={trade_id}, time={processing_time_ms:.0f}ms"
)
```

See: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-observability.html

## AgentCore Memory - Strands Integration (Correct Pattern)

**IMPORTANT**: Use the Strands-specific memory integration, NOT the generic `MemorySessionManager`.

```python
# Correct imports for Strands agents
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# Shared memory ID across all agents
MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID", "trade_matching_decisions-Z3tG4b4Xsd")

def create_memory_session_manager(correlation_id: str) -> Optional[AgentCoreMemorySessionManager]:
    """Create memory session manager for Strands agent."""
    config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=f"session_{correlation_id[:8]}",
        actor_id=AGENT_NAME,
        retrieval_config={
            "/facts/{actorId}": RetrievalConfig(top_k=10, relevance_score=0.6),
            "/preferences/{actorId}": RetrievalConfig(top_k=5, relevance_score=0.7),
            "/summaries/{actorId}/{sessionId}": RetrievalConfig(top_k=5, relevance_score=0.5)
        }
    )
    return AgentCoreMemorySessionManager(agentcore_memory_config=config, region_name=REGION)

# Pass to agent creation
agent = Agent(
    model=bedrock_model,
    system_prompt=SYSTEM_PROMPT,
    tools=[...],
    session_manager=session_manager  # Memory integration
)
```

See: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/strands-sdk-memory.html

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


## CodeBuild Deployment Notes

### Build Folder Structure
Each agent has a `.bedrock_agentcore/<agent_name>/` folder containing:
- `Dockerfile` - Container build instructions
- `requirements.txt` - Python dependencies (MUST be in this folder)
- `<agent_name>.py` - Agent code (MUST be in this folder)

### Common Deployment Issues

**Issue: source.zip too small / files missing**
- Check `.dockerignore` in parent folder - do NOT exclude `.bedrock_agentcore/`
- The agentcore CLI uses dockerignore patterns to filter source.zip contents

**Issue: CodeBuild role not found**
- Role name format: `AmazonBedrockAgentCoreSDKCodeBuild-us-east-1-<hash>`
- Must have trust policy for `codebuild.amazonaws.com`
- Required policies: ECR, CloudWatch Logs, S3, BedrockAgentCore

### Deployment Commands
```bash
# Standard deployment (CodeBuild - recommended)
cd deployment/<agent_name> && agentcore launch --auto-update-on-conflict

# Local build workaround if CodeBuild fails
agentcore deploy --local-build

# Check build logs
aws logs get-log-events --log-group-name /aws/codebuild/bedrock-agentcore-<agent>-builder --log-stream-name <build-id>
```
