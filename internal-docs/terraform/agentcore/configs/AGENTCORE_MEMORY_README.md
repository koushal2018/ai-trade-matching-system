# AgentCore Memory Setup

This directory contains configuration for AgentCore Memory resources.

## Memory Resources

### 1. Trade Patterns Memory (Semantic)
- **Name**: trade-matching-system-trade-patterns-production
- **Strategy**: Semantic
- **Purpose**: Store trade patterns, counterparty information, and historical context
- **Retention**: Indefinite (no expiration)
- **Embedding Model**: amazon.titan-embed-text-v2:0

### 2. Processing History Memory (Event)
- **Name**: trade-matching-system-processing-history-production
- **Strategy**: Event
- **Purpose**: Track agent operations, processing steps, and workflow history
- **Retention**: 90 days
- **Ordering**: Timestamp-based

### 3. Exception Patterns Memory (Semantic)
- **Name**: trade-matching-system-exception-patterns-production
- **Strategy**: Semantic
- **Purpose**: Store error patterns, RL policies, and exception resolution strategies
- **Retention**: Indefinite (for continuous learning)
- **Embedding Model**: amazon.titan-embed-text-v2:0

### 4. Matching Decisions Memory (Semantic)
- **Name**: trade-matching-system-matching-decisions-production
- **Strategy**: Semantic
- **Purpose**: Store matching decisions, HITL feedback, and scoring patterns
- **Retention**: Indefinite (for continuous learning)
- **Embedding Model**: amazon.titan-embed-text-v2:0

## Deployment

### Using AWS CLI (Manual)

Run the deployment script:
```bash
cd ./scripts
./deploy_agentcore_memory.sh
```

### Using AgentCore CLI (Recommended)

Once AgentCore CLI is available, use:
```bash
agentcore memory create --config ./configs/agentcore_memory_config.json
```

## Verification

List all memory resources:
```bash
aws bedrock-agent list-memory-resources --region us-east-1
```

Get details of a specific memory resource:
```bash
aws bedrock-agent describe-memory-resource \
  --memory-resource-id <resource-id> \
  --region us-east-1
```

## Integration with Agents

Each agent should be configured to use the appropriate memory resources:

- **PDF Adapter Agent**: processing-history
- **Trade Extraction Agent**: trade-patterns, processing-history
- **Trade Matching Agent**: trade-patterns, matching-decisions
- **Exception Management Agent**: exception-patterns, processing-history
- **Orchestrator Agent**: processing-history

## Memory Operations

### Store Data
```python
from bedrock_agentcore import Memory

memory = Memory(resource_name="trade-matching-system-trade-patterns-production")
memory.store({
    "trade_id": "GCS382857",
    "counterparty": "ABC Corp",
    "notional": 1000000,
    "pattern": "commodity_swap"
})
```

### Retrieve Data
```python
results = memory.query("commodity swap with ABC Corp", top_k=5)
```

### Event Memory
```python
event_memory = Memory(resource_name="trade-matching-system-processing-history-production")
event_memory.add_event({
    "timestamp": "2025-01-15T10:30:00Z",
    "agent": "pdf_adapter",
    "action": "pdf_processed",
    "trade_id": "GCS382857"
})
```

## Monitoring

Monitor memory usage and performance:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name MemoryStorageUsed \
  --dimensions Name=MemoryResourceName,Value=trade-matching-system-trade-patterns-production \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 3600 \
  --statistics Average \
  --region us-east-1
```

## Cleanup

To delete memory resources:
```bash
aws bedrock-agent delete-memory-resource \
  --memory-resource-id <resource-id> \
  --region us-east-1
```
