---
inclusion: always
---

# Project Structure

## Directory Organization

```
ai-trade-matching-system/
├── src/latest_trade_matching_agent/    # Main application code
│   ├── config/                         # Agent and task configurations
│   ├── tools/                          # Custom CrewAI tools
│   ├── crew_fixed.py                   # Main crew definition
│   ├── main.py                         # Entry point
│   └── eks_main.py                     # FastAPI server for EKS
├── terraform/                          # Infrastructure as Code
├── lambda/                             # Lambda function code
├── config/                             # Application configuration
├── data/                               # Sample trade PDFs
├── docs/                               # Documentation
├── storage/                            # Local storage directory
└── .kiro/                              # Kiro AI assistant configuration
```

## Key Files

### Application Core

- **`src/latest_trade_matching_agent/crew_fixed.py`**: Main crew definition with 5 agents and MCP integration
- **`src/latest_trade_matching_agent/main.py`**: Entry point for running the crew
- **`src/latest_trade_matching_agent/eks_main.py`**: FastAPI server for EKS deployment

### Configuration Files

- **`src/latest_trade_matching_agent/config/agents.yaml`**: Agent definitions (roles, goals, backstories)
- **`src/latest_trade_matching_agent/config/tasks.yaml`**: Task definitions for each agent
- **`.env`**: Environment variables (AWS credentials, S3 bucket, DynamoDB tables)
- **`llm_config.json`**: LLM configuration for AWS Bedrock

### Custom Tools

- **`src/latest_trade_matching_agent/tools/pdf_to_image.py`**: PDF to image conversion tool
- **`src/latest_trade_matching_agent/tools/dynamodb_tool.py`**: Custom DynamoDB operations (put_item, scan)
- **`src/latest_trade_matching_agent/tools/custom_tool.py`**: Additional custom tools

### Infrastructure

- **`terraform/main.tf`**: Main Terraform configuration
- **`terraform/dynamodb.tf`**: DynamoDB table definitions
- **`terraform/s3.tf`**: S3 bucket configuration
- **`terraform/lambda.tf`**: Lambda function setup
- **`terraform/variables.tf`**: Terraform variables

### Documentation

- **`README.md`**: Comprehensive project documentation
- **`ARCHITECTURE.md`**: Detailed system architecture
- **`docs/architecture-simplified.mmd`**: Mermaid diagram of architecture

## Agent Architecture

The system uses 5 specialized agents in sequential order:

1. **Document Processor** (`document_processor`)
   - Converts PDF to JPEG images (300 DPI)
   - Saves to S3 and local storage
   - Max iterations: 5

2. **OCR Processor** (`ocr_processor`)
   - Extracts text from images using AWS Bedrock
   - Combines text from all pages
   - Max iterations: 10

3. **Trade Entity Extractor** (`trade_entity_extractor`)
   - Parses OCR text into structured JSON
   - Saves to S3 (scratchpad pattern)
   - Max iterations: 5

4. **Reporting Analyst** (`reporting_analyst`)
   - Reads JSON from S3
   - Stores in appropriate DynamoDB table
   - Max iterations: 8

5. **Matching Analyst** (`matching_analyst`)
   - Scans both DynamoDB tables
   - Performs fuzzy matching
   - Generates reports
   - Max iterations: 10

## Data Storage Patterns

### S3 Folder Structure

```
s3://otc-menat-2025/
├── BANK/                              # Bank trade PDFs (input)
├── COUNTERPARTY/                      # Counterparty trade PDFs (input)
├── PDFIMAGES/                         # Converted images
│   ├── BANK/{trade_id}/
│   └── COUNTERPARTY/{trade_id}/
├── extracted/                         # Structured JSON data
│   ├── BANK/trade_{id}_{timestamp}.json
│   └── COUNTERPARTY/trade_{id}_{timestamp}.json
└── reports/                           # Matching analysis reports
    └── matching_report_{id}_{timestamp}.md
```

### Local Processing Directory

```
/tmp/processing/{unique_identifier}/
├── pdf_images/
│   └── {unique_identifier}/
│       ├── {filename}_page_001.jpg
│       ├── {filename}_page_002.jpg
│       └── ...
└── ocr_text.txt
```

### DynamoDB Tables

- **BankTradeData**: Stores trades from bank systems (TRADE_SOURCE="BANK")
- **CounterpartyTradeData**: Stores trades from counterparties (TRADE_SOURCE="COUNTERPARTY")
- **Primary Key**: Trade_ID (String)
- **Format**: DynamoDB typed format (e.g., `{"S": "value"}`, `{"N": "123"}`)

## Code Conventions

### Agent Configuration

- All agents use AWS Bedrock Claude Sonnet 4
- `verbose=False` to reduce token overhead
- `max_rpm=2` for rate limiting
- `max_retry_limit=1` for efficiency
- `multimodal=True` for image processing
- `respect_context_window=True`

### Task Flow

- Sequential process (Process.sequential)
- 15-second delay between tasks to avoid AWS throttling
- Scratchpad pattern: agents save data to S3, pass only paths/summaries
- Memory disabled (ChromaDB has credential handling issues with AWS Bedrock)

### Tool Usage

- **Standard CrewAI Tools**: FileReadTool, FileWriterTool, DirectoryReadTool, S3ReaderTool, S3WriterTool, OCRTool
- **Custom Tools**: PDFToImageTool, DynamoDBTool
- **MCP Tools**: AWS API MCP Server for DynamoDB and other AWS operations

### Error Handling

- All tools return JSON strings with success/error status
- Agents verify operations before proceeding
- Data integrity checks before matching

### Token Optimization

- Concise backstories in agents.yaml
- Minimal task descriptions
- Scratchpad pattern (save to S3, pass paths only)
- Reduced max_iter values
- Verbose mode disabled

## Input Format

The crew expects this input structure:

```python
inputs = {
    'document_path': 's3://bucket/SOURCE_TYPE/filename.pdf',  # S3 URI or local path
    'unique_identifier': 'TRADE_ID',                          # For folder naming
    'source_type': 'BANK' or 'COUNTERPARTY',                  # CRITICAL for routing
    's3_bucket': 'bucket-name',
    's3_key': 'SOURCE_TYPE/filename',
    'dynamodb_bank_table': 'BankTradeData',
    'dynamodb_counterparty_table': 'CounterpartyTradeData',
    'timestamp': 'YYYYMMDD_HHMMSS'
}
```

## Deployment Patterns

### Local Development

Run directly with Python:
```bash
python src/latest_trade_matching_agent/main.py
```

### EKS Deployment

FastAPI server with REST API:
```bash
uvicorn src.latest_trade_matching_agent.eks_main:app --host 0.0.0.0 --port 8000
```

### Lambda Deployment

Event-driven processing via S3 triggers (see `lambda/s3_event_processor.py`)

## Important Notes

- Always classify trades as BANK or COUNTERPARTY before processing
- Trade_ID is the primary key for all DynamoDB operations
- Use DynamoDB typed format for all attributes
- Verify TRADE_SOURCE matches table location (data integrity check)
- MCP server lifecycle is auto-managed by @CrewBase decorator
