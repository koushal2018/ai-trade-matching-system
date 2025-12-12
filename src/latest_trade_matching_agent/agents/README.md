# AgentCore Agents

This directory contains the AgentCore-compatible agents for the AI Trade Matching System migration.

## PDF Adapter Agent

The PDF Adapter Agent is the first agent in the event-driven pipeline. It processes PDF trade confirmations and produces standardized canonical output for downstream agents.

### Features

- **Event-Driven Architecture**: Subscribes to `document-upload-events` SQS queue
- **300 DPI Image Conversion**: Converts PDFs to high-quality JPEG images (requirement 5.1, 18.1)
- **OCR Extraction**: Uses AWS Bedrock Claude Sonnet 4 for multimodal text extraction
- **Canonical Output**: Produces standardized output conforming to `CanonicalAdapterOutput` schema
- **Error Handling**: Publishes exceptions to `exception-events` queue
- **Agent Registry**: Self-registers in AgentRegistry with capabilities and SLA targets
- **Distributed Tracing**: Supports correlation IDs for end-to-end tracing

### Requirements Validated

- **3.2**: Event-driven architecture with SQS
- **5.1**: PDF to 300 DPI image conversion
- **5.2**: OCR extraction using AWS Bedrock
- **5.3**: Save extracted text to S3
- **5.4**: Error reporting to exception queue
- **5.5**: Notify Trade Data Extraction Agent

### Usage

#### Local Testing

```bash
# Run tests
python src/latest_trade_matching_agent/agents/test_pdf_adapter.py

# Register agent only
python src/latest_trade_matching_agent/agents/pdf_adapter_agent.py register

# Test with sample document
python src/latest_trade_matching_agent/agents/pdf_adapter_agent.py test

# Run continuously (poll SQS queue)
python src/latest_trade_matching_agent/agents/pdf_adapter_agent.py
```

#### AgentCore Runtime Deployment

```bash
# Configure agent
agentcore configure \
  --agent-name pdf-adapter-agent \
  --runtime PYTHON_3_11 \
  --entrypoint src.latest_trade_matching_agent.agents.pdf_adapter_agent:invoke

# Launch agent
agentcore launch --agent-name pdf-adapter-agent

# Test invocation
agentcore invoke --agent-name pdf-adapter-agent \
  --payload '{
    "document_id": "test_001",
    "document_path": "s3://bucket/COUNTERPARTY/trade.pdf",
    "source_type": "COUNTERPARTY"
  }'
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PDF Adapter Agent                         │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ PDF to Image │───▶│  OCR Tool    │───▶│  Canonical   │  │
│  │  (300 DPI)   │    │ (Bedrock)    │    │   Output     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         ▲                                          │
         │                                          ▼
  document-upload-events                  extraction-events
      (SQS Queue)                            (SQS Queue)
                                                   │
                                                   ▼
                                        Trade Data Extraction Agent
```

### Event Flow

1. **Input Event** (`DOCUMENT_UPLOADED`):
   ```json
   {
     "event_id": "evt_123",
     "event_type": "DOCUMENT_UPLOADED",
     "source_agent": "upload_service",
     "correlation_id": "corr_abc",
     "payload": {
       "document_id": "doc_456",
       "document_path": "s3://bucket/COUNTERPARTY/trade.pdf",
       "source_type": "COUNTERPARTY"
     }
   }
   ```

2. **Processing Steps**:
   - Convert PDF to 300 DPI JPEG images
   - Perform OCR extraction on all pages
   - Combine text from multiple pages
   - Create canonical output with metadata
   - Save to S3

3. **Output Event** (`PDF_PROCESSED`):
   ```json
   {
     "event_id": "evt_124",
     "event_type": "PDF_PROCESSED",
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
       "source_type": "COUNTERPARTY"
     }
   }
   ```

### Canonical Output Schema

```json
{
  "adapter_type": "PDF",
  "document_id": "doc_456",
  "source_type": "COUNTERPARTY",
  "extracted_text": "Trade Confirmation\nTrade ID: GCS382857\n...",
  "metadata": {
    "page_count": 5,
    "dpi": 300,
    "processing_timestamp": "2025-01-15T10:31:30Z",
    "ocr_model": "us.anthropic.claude-sonnet-4-20250514-v1:0"
  },
  "s3_location": "s3://bucket/extracted/COUNTERPARTY/doc_456.json",
  "processing_timestamp": "2025-01-15T10:31:30Z",
  "correlation_id": "corr_abc"
}
```

### Error Handling

When errors occur, the agent publishes an `EXCEPTION_RAISED` event:

```json
{
  "event_id": "evt_125",
  "event_type": "EXCEPTION_RAISED",
  "source_agent": "pdf_adapter_agent",
  "correlation_id": "corr_abc",
  "payload": {
    "exception_id": "exc_789",
    "exception_type": "PDF_PROCESSING_ERROR",
    "trade_id": "doc_456",
    "error_message": "PDF conversion failed: corrupted file",
    "reason_codes": ["PDF_PROCESSING_ERROR"]
  }
}
```

### SLA Targets

- **Processing Time**: 30 seconds per PDF
- **Throughput**: 120 PDFs per hour
- **Error Rate**: < 5%

### Scaling Configuration

- **Min Instances**: 1
- **Max Instances**: 10
- **Target Queue Depth**: 50 messages
- **Scale Up Threshold**: 80% of target
- **Scale Down Threshold**: 20% of target

### Dependencies

- `boto3`: AWS SDK for S3, SQS, Bedrock
- `pdf2image`: PDF to image conversion
- `poppler-utils`: Required system dependency for pdf2image
- `pydantic`: Data validation
- `strands-agents`: Agent framework (for future integration)

### Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET_NAME=trade-matching-bucket

# Queue Names
DOCUMENT_UPLOAD_QUEUE=document-upload-events
EXTRACTION_EVENTS_QUEUE=extraction-events
EXCEPTION_EVENTS_QUEUE=exception-events

# Bedrock Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

### Monitoring

The agent updates its metrics in the AgentRegistry:

- `last_processing_time_ms`: Time taken for last document
- `total_processed`: Total documents processed
- `last_heartbeat`: Last activity timestamp

### Future Enhancements

- Support for additional adapter types (Chat, Email, Voice)
- Batch processing for multiple documents
- Advanced error recovery with exponential backoff
- Integration with AgentCore Memory for processing patterns
- Real-time metrics streaming to AgentCore Observability
