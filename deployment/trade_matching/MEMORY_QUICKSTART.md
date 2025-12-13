# AgentCore Memory Quick Start Guide

## Your Existing Memory Resource

✅ **Memory Already Created!**

- **Memory ID**: `trade_matching_decisions-Z3tG4b4Xsd`
- **ARN**: `arn:aws:bedrock-agentcore:us-east-1:401552979575:memory/trade_matching_decisions-Z3tG4b4Xsd`
- **Region**: `us-east-1`
- **Account**: `401552979575`

## Quick Setup (3 Steps)

### Step 1: Load Environment Configuration

```bash
cd deployment/trade_matching
source .env.memory
```

This sets:
- `AGENTCORE_MEMORY_ID=trade_matching_decisions-Z3tG4b4Xsd`
- AWS region and other configurations

### Step 2: Test Memory Connection

```bash
python test_memory_integration.py
```

Expected output:
```
✓ Memory session manager initialized successfully
✓ Test memory session created successfully
✓ Test decision stored in memory
✓ Retrieved 1 turn(s) from memory
✅ All memory integration tests passed!
```

### Step 3: Deploy Agent with Memory

The agent is already configured to use your memory resource. Just deploy:

```bash
# If using AgentCore Runtime
agentcore launch --config agentcore.yaml

# Or test locally
python trade_matching_agent_strands.py
```

## How It Works

### Automatic Memory Storage

Every time the agent completes a matching operation, it automatically stores:

```python
{
    "trade_id": "GCS382857",
    "classification": "MATCHED",
    "confidence": 0.92,
    "key_attributes": {
        "currency": "USD",
        "product_type": "SWAP",
        "counterparty": "Goldman Sachs",
        "notional": 1000000
    },
    "reasoning": "All critical attributes align...",
    "timestamp": "2025-01-15T10:30:00Z"
}
```

### Memory Retrieval (Optional)

To enable context retrieval from past decisions, set:

```bash
export MEMORY_RETRIEVE_CONTEXT="true"
```

Then the agent will query similar past matches before making new decisions.

## Verify Memory is Working

### Check Agent Logs

Look for these log messages:

```
INFO - AgentCore Memory initialized: trade_matching_decisions-Z3tG4b4Xsd
INFO - Stored matching decision in memory: trade_id=GCS382857, classification=MATCHED, confidence=92%
```

### Query Memory Directly

```python
from bedrock_agentcore.memory.session import MemorySessionManager

session_manager = MemorySessionManager(
    memory_id="trade_matching_decisions-Z3tG4b4Xsd",
    region_name="us-east-1"
)

session = session_manager.create_memory_session(
    actor_id="trade-matching-agent",
    session_id="query_session"
)

# Search for past decisions
results = session.search_long_term_memories(
    query="USD SWAP Goldman Sachs",
    namespace_prefix="/",
    top_k=5
)

for result in results:
    print(result['content'])
```

### Check CloudWatch Metrics

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name MemoryStorageUsed \
  --dimensions Name=MemoryId,Value=trade_matching_decisions-Z3tG4b4Xsd \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --region us-east-1
```

## What Gets Stored

### After Each Trade Match

1. **Trade Identification**
   - Trade ID
   - Source type (BANK/COUNTERPARTY)
   - Correlation ID

2. **Matching Decision**
   - Classification (MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, BREAK)
   - Confidence score (0-100%)
   - Reasoning (first 500 characters)

3. **Trade Attributes**
   - Currency
   - Product type
   - Counterparty name
   - Notional amount
   - Key dates

4. **Performance Metrics**
   - Processing time (ms)
   - Token usage (input/output)
   - Timestamp

## Benefits You'll See

### 1. Consistency
- Similar trades matched the same way
- Reduces variability in decisions
- Maintains standards over time

### 2. Learning
- Agent learns from every decision
- Patterns emerge from historical data
- Edge cases build knowledge

### 3. Context
- Past decisions inform current analysis
- Counterparty-specific patterns recognized
- Product-specific tolerances learned

### 4. Explainability
- Decisions reference similar past cases
- Reasoning includes historical context
- Audit trail of learning progression

## Monitoring

### View Recent Decisions

```bash
# Get memory details
aws bedrock-agentcore get-memory \
  --memory-id trade_matching_decisions-Z3tG4b4Xsd \
  --region us-east-1
```

### Track Memory Growth

```bash
# Check storage usage over time
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name MemoryRecordCount \
  --dimensions Name=MemoryId,Value=trade_matching_decisions-Z3tG4b4Xsd \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --region us-east-1
```

### Monitor Query Performance

```bash
# Check semantic search latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name MemoryQueryLatency \
  --dimensions Name=MemoryId,Value=trade_matching_decisions-Z3tG4b4Xsd \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --region us-east-1
```

## Troubleshooting

### Memory Not Initializing

**Error**: `Failed to initialize AgentCore Memory`

**Solutions**:
1. Verify memory exists:
   ```bash
   aws bedrock-agentcore get-memory \
     --memory-id trade_matching_decisions-Z3tG4b4Xsd \
     --region us-east-1
   ```

2. Check IAM permissions - agent needs:
   - `bedrock-agentcore:GetMemory`
   - `bedrock-agentcore:CreateMemorySession`
   - `bedrock-agentcore:AddMemoryTurns`
   - `bedrock-agentcore:SearchMemory`

3. Verify region matches: `us-east-1`

### Decisions Not Being Stored

**Symptom**: No log message "Stored matching decision in memory"

**Solutions**:
1. Check if memory is enabled:
   ```bash
   echo $AGENTCORE_MEMORY_ID
   ```

2. Verify classification is not "UNKNOWN"
   - Memory only stores valid classifications

3. Check agent logs for errors:
   ```bash
   grep "Failed to store matching decision" agent.log
   ```

### High Memory Costs

**Symptom**: Unexpected AWS charges

**Solutions**:
1. Review retention policy
2. Implement selective storage (only REVIEW_REQUIRED cases)
3. Archive old decisions to S3

## Advanced Usage

### Custom Memory Queries

```python
from memory_integration import TradeMatchingMemory

memory = TradeMatchingMemory(
    memory_id="trade_matching_decisions-Z3tG4b4Xsd",
    region_name="us-east-1"
)

# Find all USD SWAP matches
results = memory.retrieve_similar_matches(
    trade_attributes={
        "currency": "USD",
        "product_type": "SWAP"
    },
    top_k=10
)
```

### Inject Memory Context into Prompts

```python
# Get context for current trade
memory_context = memory.get_memory_context_for_prompt(
    trade_attributes={
        "currency": "EUR",
        "product_type": "OPTION",
        "counterparty": "JP Morgan"
    },
    max_examples=3
)

# Include in agent prompt
prompt = f"""Match this trade...

{memory_context}

## Current Trade
...
"""
```

## Next Steps

1. ✅ Memory resource exists
2. ✅ Agent configured to use it
3. ✅ Test connection works
4. 🔄 Deploy and start matching trades
5. 📊 Monitor memory growth and performance
6. 🎯 Measure accuracy improvements over time

## Support

- **Documentation**: See `MEMORY_INTEGRATION_GUIDE.md` for detailed info
- **Code Examples**: See `INTEGRATION_EXAMPLE.py` for integration patterns
- **Memory Module**: See `memory_integration.py` for implementation details

Your Trade Matching Agent is now memory-enabled and ready to learn! 🚀
