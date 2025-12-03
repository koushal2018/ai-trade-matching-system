# Quick Start: Trade Data Extraction Agent

## Prerequisites

1. AWS credentials configured
2. Python 3.11+ installed
3. Required packages installed:
   ```bash
   pip install boto3 pydantic anthropic
   ```

## Environment Setup

Create a `.env` file or set environment variables:

```bash
export AWS_DEFAULT_REGION=us-east-1
export S3_BUCKET_NAME=trade-matching-system-agentcore-production
export EXTRACTION_EVENTS_QUEUE=trade-matching-system-extraction-events-production
export MATCHING_EVENTS_QUEUE=trade-matching-system-matching-events-production
export EXCEPTION_EVENTS_QUEUE=trade-matching-system-exception-events-production
export BANK_TABLE_NAME=BankTradeData
export COUNTERPARTY_TABLE_NAME=CounterpartyTradeData
```

## Quick Test

### 1. Test LLM Extraction Tool

```python
from src.latest_trade_matching_agent.tools.llm_extraction_tool import extract_trade_data

sample_text = """
Trade Confirmation
Trade ID: GCS382857
Trade Date: 2024-10-15
Notional: 1,000,000 USD
Currency: USD
Counterparty: Goldman Sachs
Product Type: SWAP
"""

result = extract_trade_data(
    extracted_text=sample_text,
    source_type="COUNTERPARTY",
    document_id="test_doc_001"
)

print(f"Success: {result['success']}")
print(f"Trade ID: {result['trade_data']['Trade_ID']}")
print(f"Confidence: {result['extraction_confidence']}")
```

### 2. Test Trade Source Classifier

```python
from src.latest_trade_matching_agent.tools.trade_source_classifier import classify_trade_source

text = "Trade Confirmation from Goldman Sachs\nTheir Reference: GCS382857"

source_type = classify_trade_source(
    extracted_text=text,
    document_path="s3://bucket/COUNTERPARTY/trade.pdf"
)

print(f"Source Type: {source_type}")  # Should be "COUNTERPARTY"
```

### 3. Test Trade Data Extraction Agent

```python
from src.latest_trade_matching_agent.agents.trade_extraction_agent import TradeDataExtractionAgent
from src.latest_trade_matching_agent.models.events import StandardEventMessage, EventTaxonomy

# Initialize agent
agent = TradeDataExtractionAgent()

# Register agent
agent.register()

# Create test event
test_event = StandardEventMessage(
    event_id="evt_test_001",
    event_type=EventTaxonomy.PDF_PROCESSED,
    source_agent="pdf_adapter_agent",
    correlation_id="corr_test_001",
    payload={
        "document_id": "test_doc_001",
        "canonical_output_location": "s3://bucket/extracted/COUNTERPARTY/test_doc_001.json"
    }
)

# Extract trade
result = agent.extract_trade(test_event)

print(f"Success: {result['success']}")
if result['success']:
    print(f"Trade ID: {result['trade_id']}")
    print(f"Table: {result['table_name']}")
    print(f"Confidence: {result['extraction_confidence']}")
```

## Running the Agent

### Local Development

```bash
# Register agent only
python -m src.latest_trade_matching_agent.agents.trade_extraction_agent register

# Test with sample event
python -m src.latest_trade_matching_agent.agents.trade_extraction_agent test

# Run continuously (poll SQS)
python -m src.latest_trade_matching_agent.agents.trade_extraction_agent
```

### Integration Tests

```bash
# Run all integration tests
python test_trade_extraction_integration.py
```

### Unit Tests

```bash
# Run unit tests with pytest
pytest src/latest_trade_matching_agent/agents/test_trade_extraction.py -v
```

## AgentCore Deployment

### 1. Configure Agent

```bash
agentcore configure \
  --agent-name trade-extraction-agent \
  --runtime PYTHON_3_11 \
  --entrypoint src.latest_trade_matching_agent.agents.trade_extraction_agent:invoke \
  --memory-integration enabled \
  --region us-east-1
```

### 2. Deploy Agent

```bash
agentcore launch --agent-name trade-extraction-agent
```

### 3. Test Agent

```bash
agentcore invoke --agent-name trade-extraction-agent \
  --payload '{
    "document_id": "test_doc_001",
    "canonical_output_location": "s3://bucket/extracted/COUNTERPARTY/test_doc_001.json"
  }'
```

### 4. Monitor Agent

```bash
# Check agent status
agentcore status --agent-name trade-extraction-agent

# View logs
agentcore logs --agent-name trade-extraction-agent --tail 100

# View metrics
agentcore metrics --agent-name trade-extraction-agent
```

## Troubleshooting

### Issue: LLM extraction fails

**Solution:**
1. Check Bedrock model availability: `aws bedrock list-foundation-models --region us-east-1`
2. Verify IAM permissions for Bedrock
3. Check model ID is correct: `us.anthropic.claude-sonnet-4-20250514-v1:0`

### Issue: Classification mismatch

**Solution:**
1. Check document path contains correct source indicator (BANK or COUNTERPARTY)
2. Review text for clear indicators
3. Adjust confidence threshold if needed

### Issue: DynamoDB storage fails

**Solution:**
1. Verify tables exist: `aws dynamodb list-tables --region us-east-1`
2. Check IAM permissions for DynamoDB
3. Ensure Trade_ID is unique

### Issue: SQS message not processed

**Solution:**
1. Check queue exists: `aws sqs list-queues --region us-east-1`
2. Verify message format matches StandardEventMessage schema
3. Check dead letter queue for failed messages
4. Increase visibility timeout if processing takes longer

## Monitoring Metrics

The agent tracks the following metrics:

- `last_processing_time_ms` - Time to process last trade
- `total_processed` - Total trades processed
- `last_extraction_confidence` - Confidence of last extraction
- `last_heartbeat` - Last agent heartbeat timestamp

Query metrics from AgentRegistry:

```python
from src.latest_trade_matching_agent.models.registry import AgentRegistry

registry = AgentRegistry(region_name="us-east-1")
agent = registry.get_agent("trade_extraction_agent")

print(f"Status: {agent.deployment_status}")
print(f"Metrics: {agent.metrics}")
print(f"Last Heartbeat: {agent.last_heartbeat}")
```

## Next Steps

1. ✅ Verify AWS resources are created (S3 bucket, DynamoDB tables, SQS queues)
2. ✅ Test with real PDF_PROCESSED events from PDF Adapter Agent
3. ✅ Monitor extraction confidence and adjust prompts if needed
4. ✅ Deploy to AgentCore Runtime for production use
5. ✅ Set up CloudWatch alarms for SLA violations

## Support

For issues or questions:
1. Check the comprehensive README: `src/latest_trade_matching_agent/agents/TRADE_EXTRACTION_README.md`
2. Review the implementation summary: `TASK_6_IMPLEMENTATION_SUMMARY.md`
3. Check the design document: `.kiro/specs/agentcore-migration/design.md`
