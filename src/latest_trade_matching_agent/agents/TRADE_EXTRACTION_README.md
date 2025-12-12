# Trade Data Extraction Agent

## Overview

The Trade Data Extraction Agent is responsible for extracting structured trade data from unstructured text (OCR output) and storing it in the appropriate DynamoDB table. It is part of the event-driven AgentCore architecture.

## Responsibilities

1. **Subscribe to extraction-events SQS queue** - Listens for PDF_PROCESSED events
2. **Read canonical adapter output from S3** - Retrieves the standardized output from PDF Adapter
3. **Extract trade data using LLM** - Uses AWS Bedrock Claude Sonnet 4 to parse unstructured text
4. **Classify trade source** - Determines if trade is from BANK or COUNTERPARTY
5. **Validate against canonical trade model** - Ensures all mandatory fields are present
6. **Store in appropriate DynamoDB table** - Routes to BankTradeData or CounterpartyTradeData
7. **Publish TRADE_EXTRACTED events** - Notifies downstream agents (Trade Matching Agent)
8. **Handle errors** - Publishes exception events for failed extractions
9. **Register in AgentRegistry** - Maintains agent metadata and health status

## Architecture

```
extraction-events (SQS)
    ↓
Trade Data Extraction Agent
    ├─→ Read canonical output from S3
    ├─→ Extract trade fields (LLM)
    ├─→ Classify trade source
    ├─→ Validate canonical model
    ├─→ Store in DynamoDB (BANK or COUNTERPARTY table)
    ├─→ Save JSON to S3 (audit trail)
    └─→ Publish TRADE_EXTRACTED event
        ↓
matching-events (SQS)
```

## Components

### 1. LLM Extraction Tool (`llm_extraction_tool.py`)

Extracts structured trade data from unstructured text using AWS Bedrock Claude Sonnet 4.

**Features:**
- Extracts 30+ trade fields (mandatory and optional)
- Validates against CanonicalTradeModel
- Handles optional fields gracefully
- Computes extraction confidence score
- Provides detailed error messages for validation failures

**Usage:**
```python
from src.latest_trade_matching_agent.tools.llm_extraction_tool import LLMExtractionTool

tool = LLMExtractionTool(region_name="us-east-1")
result = tool.extract_trade_fields(
    extracted_text="Trade Confirmation\nTrade ID: GCS382857\n...",
    source_type="COUNTERPARTY",
    document_id="doc_123"
)

if result["success"]:
    canonical_trade = result["canonical_trade"]
    confidence = result["extraction_confidence"]
```

### 2. Trade Source Classifier (`trade_source_classifier.py`)

Classifies trades as BANK or COUNTERPARTY using pattern matching and LLM.

**Features:**
- Pattern-based classification for clear cases
- LLM-based classification for ambiguous cases
- Uses document path as additional context
- Provides confidence scores and reasoning

**Usage:**
```python
from src.latest_trade_matching_agent.tools.trade_source_classifier import TradeSourceClassifier

classifier = TradeSourceClassifier(region_name="us-east-1")
result = classifier.classify_trade_source(
    extracted_text="Trade Confirmation from Goldman Sachs...",
    document_path="s3://bucket/COUNTERPARTY/trade.pdf"
)

if result["success"]:
    source_type = result["source_type"]  # "BANK" or "COUNTERPARTY"
    confidence = result["confidence"]
```

### 3. Trade Data Extraction Agent (`trade_extraction_agent.py`)

Main agent that orchestrates the extraction process.

**Features:**
- Event-driven architecture with SQS
- Automatic DynamoDB table routing
- Error handling and exception publishing
- Agent registry integration
- Metrics tracking

## Event Flow

### Input Event (PDF_PROCESSED)

```json
{
  "event_id": "evt_124",
  "event_type": "PDF_PROCESSED",
  "timestamp": "2025-01-15T10:31:30Z",
  "source_agent": "pdf_adapter_agent",
  "correlation_id": "corr_abc",
  "payload": {
    "document_id": "doc_456",
    "canonical_output_location": "s3://bucket/extracted/COUNTERPARTY/doc_456.json",
    "page_count": 5,
    "processing_time_ms": 8500
  },
  "metadata": {
    "dpi": 300,
    "ocr_confidence": 0.95
  }
}
```

### Output Event (TRADE_EXTRACTED)

```json
{
  "event_id": "evt_125",
  "event_type": "TRADE_EXTRACTED",
  "timestamp": "2025-01-15T10:33:00Z",
  "source_agent": "trade_extraction_agent",
  "correlation_id": "corr_abc",
  "payload": {
    "trade_id": "GCS382857",
    "source_type": "COUNTERPARTY",
    "table_name": "CounterpartyTradeData",
    "processing_time_ms": 12500
  },
  "metadata": {
    "extraction_confidence": 0.92,
    "fields_extracted": 28,
    "document_id": "doc_456"
  }
}
```

## Configuration

### Environment Variables

```bash
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=trade-matching-system-agentcore-production

# SQS Queues
EXTRACTION_EVENTS_QUEUE=trade-matching-system-extraction-events-production
MATCHING_EVENTS_QUEUE=trade-matching-system-matching-events-production
EXCEPTION_EVENTS_QUEUE=trade-matching-system-exception-events-production

# DynamoDB Tables
BANK_TABLE_NAME=BankTradeData
COUNTERPARTY_TABLE_NAME=CounterpartyTradeData
```

### Agent Configuration

```python
agent = TradeDataExtractionAgent(
    agent_id="trade_extraction_agent",
    region_name="us-east-1",
    s3_bucket="trade-matching-system-agentcore-production",
    extraction_events_queue="trade-matching-system-extraction-events-production",
    matching_events_queue="trade-matching-system-matching-events-production",
    exception_events_queue="trade-matching-system-exception-events-production",
    bank_table_name="BankTradeData",
    counterparty_table_name="CounterpartyTradeData"
)
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

### AgentCore Runtime Deployment

```bash
# Configure agent
agentcore configure \
  --agent-name trade-extraction-agent \
  --runtime PYTHON_3_11 \
  --entrypoint src.latest_trade_matching_agent.agents.trade_extraction_agent:invoke

# Deploy agent
agentcore launch --agent-name trade-extraction-agent

# Test agent
agentcore invoke --agent-name trade-extraction-agent \
  --payload '{"document_id": "test_doc", "canonical_output_location": "s3://..."}'
```

## Data Models

### Canonical Trade Model

The agent validates all extracted data against the `CanonicalTradeModel`:

**Mandatory Fields:**
- Trade_ID
- TRADE_SOURCE (BANK or COUNTERPARTY)
- trade_date
- notional
- currency
- counterparty
- product_type

**Optional Fields (30+):**
- effective_date, maturity_date
- commodity_type, strike_price
- settlement_type, payment_frequency
- fixed_rate, floating_rate_index
- option_type, option_style
- broker, trader_name, trader_email
- collateral_required, collateral_amount
- master_agreement, credit_support_annex
- And more...

### DynamoDB Storage

Trades are stored in DynamoDB typed format:

```python
{
    "Trade_ID": {"S": "GCS382857"},
    "TRADE_SOURCE": {"S": "COUNTERPARTY"},
    "trade_date": {"S": "2024-10-15"},
    "notional": {"N": "1000000.0"},
    "currency": {"S": "USD"},
    "counterparty": {"S": "Goldman Sachs"},
    "product_type": {"S": "SWAP"},
    ...
}
```

## Error Handling

The agent handles various error scenarios:

1. **Missing canonical output** - S3 object not found
2. **Invalid canonical output** - Schema validation failure
3. **Extraction failure** - LLM unable to extract mandatory fields
4. **Validation failure** - Extracted data doesn't match canonical model
5. **DynamoDB errors** - Table not found, permission issues
6. **SQS errors** - Queue not found, message format issues

All errors result in:
- Exception event published to exception-events queue
- Error logged with full context
- Original message retained for retry or DLQ

## Monitoring

### Metrics Tracked

- `last_processing_time_ms` - Time to process last trade
- `total_processed` - Total trades processed
- `last_extraction_confidence` - Confidence of last extraction
- `last_heartbeat` - Last agent heartbeat timestamp

### SLA Targets

- Processing time: 15 seconds per trade
- Throughput: 240 trades per hour
- Error rate: < 5%

## Testing

### Unit Tests

```bash
# Run unit tests
pytest src/latest_trade_matching_agent/agents/test_trade_extraction.py -v
```

### Integration Tests

```bash
# Run integration tests
python test_trade_extraction_integration.py
```

## Requirements Validation

This agent validates the following requirements:

- **3.3**: Event-driven architecture with SQS
- **6.1**: Extract all trade fields using LLM
- **6.2**: Classify trade source (BANK or COUNTERPARTY)
- **6.3**: Save structured JSON to S3
- **6.4**: Store in appropriate DynamoDB table
- **6.5**: Report extraction errors with context

## Dependencies

- `boto3` - AWS SDK for Python
- `pydantic` - Data validation
- `anthropic` - AWS Bedrock Claude Sonnet 4

## Related Components

- **PDF Adapter Agent** - Upstream agent that produces canonical output
- **Trade Matching Agent** - Downstream agent that consumes TRADE_EXTRACTED events
- **Exception Management Agent** - Handles extraction failures
- **AgentRegistry** - Tracks agent health and metrics

## Troubleshooting

### Common Issues

1. **LLM extraction fails**
   - Check Bedrock model availability in region
   - Verify IAM permissions for Bedrock
   - Review extraction prompt for clarity

2. **Classification mismatch**
   - Check document path contains correct source indicator
   - Review text for clear BANK/COUNTERPARTY indicators
   - Adjust confidence threshold if needed

3. **DynamoDB storage fails**
   - Verify table exists in correct region
   - Check IAM permissions for DynamoDB
   - Ensure Trade_ID is unique

4. **SQS message not processed**
   - Check queue visibility timeout (should be > processing time)
   - Verify message format matches StandardEventMessage schema
   - Check dead letter queue for failed messages

## Future Enhancements

1. **Batch processing** - Process multiple trades in parallel
2. **Caching** - Cache LLM responses for similar trades
3. **Confidence thresholds** - Escalate low-confidence extractions to HITL
4. **Field-level confidence** - Track confidence per field
5. **Historical learning** - Learn from past extractions to improve accuracy
