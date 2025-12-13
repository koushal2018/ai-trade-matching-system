# AgentCore Memory Integration for Trade Matching Agent

## Overview

This guide documents the AgentCore Memory integration for the Trade Matching Agent, enabling continuous learning from past matching decisions and HITL feedback.

## What We've Added

### 1. Memory Integration Module (`memory_integration.py`)

A dedicated module that provides:

- **`TradeMatchingMemory` class**: Main memory manager
- **`store_matching_decision()`**: Store matching decisions for learning
- **`retrieve_similar_matches()`**: Query past decisions for context
- **`get_memory_context_for_prompt()`**: Inject memory context into agent prompts

### 2. Enhanced Agent Implementation

Updated `trade_matching_agent_strands.py` with:

- AgentCore Memory SDK imports
- Memory session initialization
- Memory helper functions integrated into the agent
- Enhanced system prompt mentioning memory capabilities
- Automatic storage of matching decisions after each match

## How It Works

### Memory Storage Flow

```
1. Agent completes trade matching analysis
2. Extracts classification (MATCHED, PROBABLE_MATCH, etc.)
3. Extracts confidence score from response
4. Calls store_matching_decision() with:
   - Trade ID
   - Source type (BANK/COUNTERPARTY)
   - Classification
   - Confidence score
   - Match details (attributes, reasoning, metrics)
   - Correlation ID
5. Memory stored in AgentCore Memory (semantic strategy)
6. Available for future similarity searches
```

### Memory Retrieval Flow

```
1. Agent receives new trade to match
2. Extracts key attributes (currency, product_type, counterparty)
3. Calls retrieve_similar_matches() with attributes
4. AgentCore Memory performs semantic search
5. Returns top-k similar past decisions
6. Agent uses context to inform current matching
```

## Configuration

### Environment Variables

Add to your agent's environment:

```bash
# AgentCore Memory Resource ID
AGENTCORE_MEMORY_ID=trade_matching_decisions-Z3tG4b4Xsd

# AWS Configuration
AWS_REGION=us-east-1
```

### Memory Resource

Your existing memory resource:

- **Memory ID**: `trade_matching_decisions-Z3tG4b4Xsd`
- **ARN**: `arn:aws:bedrock-agentcore:us-east-1:401552979575:memory/trade_matching_decisions-Z3tG4b4Xsd`
- **Strategy**: Semantic
- **Purpose**: Store matching decisions, HITL feedback, and trade patterns
- **Retention**: Indefinite (for continuous learning)
- **Region**: us-east-1

## Deployment Steps

### Step 1: Verify Memory Resource

Your memory resource already exists. Verify it's active:

```bash
# Check memory status
aws bedrock-agentcore get-memory \
  --memory-id trade_matching_decisions-Z3tG4b4Xsd \
  --region us-east-1
```

### Step 2: Update Agent Configuration

Add memory configuration to `agentcore.yaml`:

```yaml
agent:
  name: trade-matching-agent
  runtime: PYTHON_3_11
  memory:
    - id: trade_matching_decisions-Z3tG4b4Xsd
      type: semantic
      enabled: true
```

### Step 3: Install Dependencies

Add to `requirements.txt`:

```
bedrock-agentcore>=0.1.0
bedrock-agentcore-memory>=0.1.0
```

### Step 4: Deploy Agent

```bash
cd deployment/trade_matching
agentcore launch --config agentcore.yaml
```

## Usage Examples

### Example 1: Basic Memory Storage

```python
from memory_integration import initialize_memory, get_memory

# Initialize during agent startup
memory = initialize_memory(
    memory_id="trade_matching_decisions-Z3tG4b4Xsd",
    region_name="us-east-1",
    agent_name="trade-matching-agent"
)

# Store a matching decision
memory.store_matching_decision(
    trade_id="GCS382857",
    source_type="COUNTERPARTY",
    classification="MATCHED",
    confidence=0.92,
    match_details={
        "key_attributes": {
            "currency": "USD",
            "product_type": "SWAP",
            "counterparty": "Goldman Sachs",
            "notional": 1000000
        },
        "reasoning": "All critical attributes align within tolerances...",
        "processing_time_ms": 15234,
        "token_usage": {"input": 1200, "output": 800}
    },
    correlation_id="corr_abc123"
)
```

### Example 2: Retrieve Similar Matches

```python
# Query for similar past decisions
similar_matches = memory.retrieve_similar_matches(
    trade_attributes={
        "currency": "USD",
        "product_type": "SWAP",
        "counterparty": "Goldman Sachs"
    },
    top_k=5
)

# Use in agent prompt
for match in similar_matches:
    print(f"Past decision: {match['content'][:200]}...")
```

### Example 3: Enhanced Agent Prompt

```python
# Get memory context for current trade
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

## Current Trade to Match
- Trade ID: {trade_id}
- Currency: EUR
- Product: OPTION
...
"""
```

## Benefits

### 1. Continuous Learning
- Agent learns from every matching decision
- Patterns emerge from historical data
- Edge cases build institutional knowledge

### 2. Consistency
- Similar trades matched consistently
- Reduces variability in decisions
- Maintains matching standards over time

### 3. HITL Integration
- Human feedback stored in memory
- Agent learns from corrections
- Improves accuracy on ambiguous cases

### 4. Context-Aware Matching
- Past decisions inform current analysis
- Counterparty-specific patterns recognized
- Product-specific tolerances learned

### 5. Explainability
- Decisions reference similar past cases
- Reasoning includes historical context
- Audit trail of learning progression

## Monitoring

### Memory Usage Metrics

```bash
# Check memory storage usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name MemoryStorageUsed \
  --dimensions Name=MemoryId,Value=trade_matching_decisions-Z3tG4b4Xsd \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 3600 \
  --statistics Average \
  --region us-east-1
```

### Query Performance

```bash
# Check semantic search latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name MemoryQueryLatency \
  --dimensions Name=MemoryId,Value=trade_matching_decisions-Z3tG4b4Xsd \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum \
  --region us-east-1
```

## Troubleshooting

### Memory Not Available

**Symptom**: Logs show "Memory not available - skipping decision storage"

**Solutions**:
1. Verify memory resource exists: `agentcore memory list`
2. Check memory status: `agentcore memory status <memory-id>`
3. Ensure memory is ACTIVE (not CREATING or FAILED)
4. Verify IAM permissions for agent to access memory

### Semantic Search Returns No Results

**Symptom**: `retrieve_similar_matches()` returns empty list

**Solutions**:
1. Verify decisions are being stored (check logs)
2. Wait for indexing (semantic embeddings take time)
3. Broaden search query (fewer specific attributes)
4. Check memory retention policy (events may have expired)

### High Memory Costs

**Symptom**: Unexpected costs from memory storage

**Solutions**:
1. Review retention policy (90 days vs indefinite)
2. Implement selective storage (only store REVIEW_REQUIRED cases)
3. Archive old decisions to S3
4. Use event memory for short-term data

## Next Steps

### Task 20.6 Completion

This implementation completes task 20.6 from your migration plan:

- [x] 20.6 Integrate memory with Trade Matching Agent
  - Store matching decisions in semantic memory ✓
  - Retrieve HITL feedback for similar cases ✓
  - Enable continuous learning ✓

### Future Enhancements

1. **HITL Feedback Loop**
   - Update stored decisions when humans override
   - Track accuracy improvements over time
   - Generate confidence calibration reports

2. **Advanced Pattern Recognition**
   - Identify counterparty-specific matching patterns
   - Learn product-specific tolerances
   - Detect systematic data quality issues

3. **Memory-Driven Thresholds**
   - Dynamically adjust confidence thresholds
   - Learn optimal classification boundaries
   - Adapt to changing trade characteristics

4. **Cross-Agent Memory Sharing**
   - Share patterns with Trade Extraction Agent
   - Inform Exception Handler with matching patterns
   - Build unified knowledge base

## References

- [AgentCore Memory Documentation](https://aws.github.io/bedrock-agentcore-starter-toolkit/examples/semantic_search.md)
- [Memory CLI Guide](https://aws.github.io/bedrock-agentcore-starter-toolkit/mcp/agentcore_memory.md)
- [Terraform Memory Configuration](../../terraform/agentcore/agentcore_memory.tf)
- [Memory Config README](../../terraform/agentcore/configs/AGENTCORE_MEMORY_README.md)

## Support

For issues or questions:
1. Check AgentCore Memory logs in CloudWatch
2. Review agent execution logs
3. Consult AgentCore documentation
4. Contact AWS Support for memory resource issues
