---
inclusion: fileMatch
fileMatchPattern: ['**/deployment/**/*.py', '**/deployment/**/agentcore.yaml', '**/deployment/**/deploy.sh']
---

# Agent Development Guidelines

## Agent File Structure
Each agent in `deployment/<agent_name>/` requires:
- `<agent_name>_strands.py` - Main agent implementation using Strands SDK
- `agentcore.yaml` - AgentCore Runtime configuration
- `deploy.sh` - Deployment script
- `requirements.txt` - Python dependencies

## AgentCore Runtime Pattern
All agents must use the BedrockAgentCoreApp pattern with ping health check and entrypoint:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus
import uuid

app = BedrockAgentCoreApp()

@app.ping
def health_check() -> PingStatus:
    return PingStatus.HEALTHY

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    # Agent logic here
    return {"success": True, "correlation_id": correlation_id}
```

## Observability - CRITICAL RULES

**DO NOT use manual `Observability` class** - causes 202 warnings and breaks monitoring.

AgentCore Runtime auto-instruments via OpenTelemetry. Use structured logging only:

```python
import logging
logger = logging.getLogger(__name__)

# OTEL captures these logs automatically with correlation_id
logger.info(f"[{correlation_id}] Operation completed - trade_id={trade_id}, time={processing_time_ms:.0f}ms")
```

Required dependencies in `requirements.txt`:
```
strands-agents[otel]>=0.1.0
aws-opentelemetry-distro>=0.2.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-exporter-otlp>=1.20.0
```

## AgentCore Memory Integration

**CRITICAL**: Use Strands-specific memory classes, NOT generic `MemorySessionManager`.

```python
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID", "trade_matching_decisions-Z3tG4b4Xsd")

def create_memory_session_manager(correlation_id: str) -> Optional[AgentCoreMemorySessionManager]:
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

# Pass to Strands Agent constructor
agent = Agent(
    model=bedrock_model,
    system_prompt=SYSTEM_PROMPT,
    tools=[...],
    session_manager=session_manager
)
```

## Standard Response Format
All agents must return consistent response structure:

```python
return {
    "success": bool,
    "correlation_id": str,
    "agent_name": str,
    "agent_version": str,
    "processing_time_ms": float,
    "token_usage": {
        "input_tokens": int,
        "output_tokens": int,
        "total_tokens": int
    }
    # Agent-specific fields below
}
```

## Required Environment Variables
- `AWS_REGION` - AWS region (default: us-east-1)
- `S3_BUCKET_NAME` - S3 bucket for documents
- `DYNAMODB_BANK_TABLE` - Bank trades table name
- `DYNAMODB_COUNTERPARTY_TABLE` - Counterparty trades table name
- `BEDROCK_MODEL_ID` - Bedrock model ID (e.g., anthropic.claude-sonnet-4-20250514-v1:0)
- `BYPASS_TOOL_CONSENT=true` - Required for AgentCore Runtime tool execution
- `AGENTCORE_MEMORY_ID` - Shared memory ID across agents

## Deployment

### CodeBuild Structure
Each agent's `.bedrock_agentcore/<agent_name>/` folder must contain:
- `Dockerfile` - Container build instructions
- `requirements.txt` - Python dependencies (MUST be in this folder, not parent)
- `<agent_name>.py` - Agent code (MUST be in this folder, not parent)

### Common Deployment Failures

**source.zip too small / missing files**
- Check `.dockerignore` - do NOT exclude `.bedrock_agentcore/`
- AgentCore CLI uses dockerignore patterns to filter source.zip

**CodeBuild role not found**
- Role format: `AmazonBedrockAgentCoreSDKCodeBuild-us-east-1-<hash>`
- Must have trust policy for `codebuild.amazonaws.com`
- Required policies: ECR, CloudWatch Logs, S3, BedrockAgentCore

### Deployment Commands
```bash
# Standard deployment (CodeBuild - recommended)
cd deployment/<agent_name>
agentcore launch --auto-update-on-conflict

# Local build fallback if CodeBuild fails
agentcore deploy --local-build

# View build logs
aws logs tail /aws/codebuild/bedrock-agentcore-<agent>-builder --follow
```

## Error Handling Pattern
All agents must implement structured error handling with correlation tracking:

```python
try:
    # Agent logic
    result = process_trade(payload)
    return {"success": True, "correlation_id": correlation_id, "result": result}
except Exception as e:
    logger.error(f"[{correlation_id}] Agent failed: {str(e)}", exc_info=True)
    return {
        "success": False,
        "correlation_id": correlation_id,
        "error": str(e),
        "error_type": type(e).__name__
    }
```
