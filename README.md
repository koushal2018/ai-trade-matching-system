# AI Trade Matching System

> **Enterprise-grade trade confirmation matching powered by CrewAI on AWS Bedrock**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-0.175+-green.svg)
![AWS](https://img.shields.io/badge/AWS-Bedrock%20Claude%20Sonnet%204-orange.svg)
![DynamoDB](https://img.shields.io/badge/DynamoDB-boto3%20%2B%20MCP-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview

The AI Trade Matching System is an intelligent, cloud-native solution that automates the processing and matching of derivative trade confirmations using advanced AI capabilities. Built on AWS native services with a multi-agent architecture powered by CrewAI, the system leverages **AWS Bedrock Claude Sonnet 4** for document analysis and implements sophisticated trade matching algorithms for financial operations teams.

**Key Problem Solved**: Manual trade confirmation matching is time-consuming, error-prone, and doesn't scale with trading volumes. This system automates the entire process from PDF ingestion to intelligent matching, reducing settlement risk and operational overhead.

**Technology Stack**:
- **AI/ML**: AWS Bedrock Claude Sonnet 4 (APAC region), CrewAI 0.175+ multi-agent framework
- **Data Storage**: Amazon DynamoDB with custom boto3 tools + AWS API MCP Server
- **Document Storage**: Amazon S3 with lifecycle management
- **Backend**: Python 3.11+ with FastAPI
- **Integration**: Model Context Protocol (MCP) for AWS operations
- **Document Processing**: Poppler, pdf2image, PIL for 300 DPI conversion

## Features

- **🤖 AI-Powered Document Processing**: AWS Bedrock Claude Sonnet 4 with multimodal capabilities for accurate PDF text extraction
- **📄 Advanced PDF Pipeline**: High-quality PDF-to-image conversion (300 DPI) optimized for OCR processing
- **🎯 Multi-Agent Architecture**: 5 specialized agents handling document processing, OCR extraction, entity parsing, data storage, and matching
- **☁️ Dual DynamoDB Integration**: Custom boto3 tool + AWS API MCP Server for maximum reliability
- **🗄️ Intelligent Data Storage**: DynamoDB with separate tables for bank and counterparty trades
- **🔍 Professional Trade Matching**: Sophisticated matching logic with fuzzy matching, tolerance handling, and break analysis
- **📊 Token-Optimized Design**: 85% token reduction through scratchpad pattern and aggressive optimization
- **🔐 Security-First Design**: IAM roles with least-privilege access, credential management via environment variables
- **📈 Production Ready**: Comprehensive error handling, logging, and monitoring capabilities

## Prerequisites

### Required AWS Setup

**AWS Account Requirements**:
- AWS CLI configured with appropriate permissions
- Access to AWS Bedrock (Claude Sonnet 4 model in APAC region: `apac.anthropic.claude-sonnet-4-20250514-v1:0`)
- DynamoDB, S3, and IAM permissions
- AWS region: `me-central-1` (Middle East - UAE)

**AWS Services Used**:
```bash
# Core services
- AWS Bedrock (Claude Sonnet 4 AI model)
- Amazon DynamoDB (trade data storage)
- Amazon S3 (document and image storage)
- IAM (security and permissions)

# Supporting tools
- MCP (Model Context Protocol) for AWS operations
- boto3 for direct DynamoDB access
```

### Development Environment

**Required Tools**:
```bash
# System dependencies
Python >= 3.11
poppler-utils (for PDF processing)

# Package managers
pip >= 23.0 or uv (recommended)
```

**Python Dependencies**:
```bash
# Core framework
crewai>=0.175.0
crewai-tools>=0.14.0

# AI/ML
anthropic>=0.39.0
litellm>=1.0.0

# AWS integration
boto3>=1.34.0
mcp[cli]

# Document processing
pdf2image>=1.17.0
Pillow>=10.0.0

# Utilities
python-dotenv
pydantic>=2.0.0
```

## Architecture

### High-Level System Architecture

```mermaid
graph TB
    subgraph "Input Layer"
        PDF[📄 Trade Confirmation PDFs<br/>BANK / COUNTERPARTY]
        S3[(Amazon S3<br/>otc-menat-2025)]
        PDF --> S3
    end

    subgraph "AWS Bedrock"
        Bedrock[🧠 Claude Sonnet 4<br/>apac.anthropic.claude-sonnet-4-20250514-v1:0<br/>Temperature: 0.7 | Max Tokens: 4096]
    end

    subgraph "Processing Layer - CrewAI Multi-Agent System"
        A1[🤖 Agent 1: Document Processor<br/>PDF → JPEG 300 DPI<br/>max_iter: 5]
        A2[🤖 Agent 2: OCR Processor<br/>Extract Text from Images<br/>max_iter: 10]
        A3[🤖 Agent 3: Trade Entity Extractor<br/>Parse JSON from Text<br/>max_iter: 5]
        A4[🤖 Agent 4: Reporting Analyst<br/>Store to DynamoDB<br/>max_iter: 8]
        A5[🤖 Agent 5: Matching Analyst<br/>Trade Matching & Reports<br/>max_iter: 10]

        A1 --> A2
        A2 --> A3
        A3 --> A4
        A4 --> A5
    end

    subgraph "Data Layer"
        DDB1[(DynamoDB<br/>BankTradeData<br/>PK: Trade_ID)]
        DDB2[(DynamoDB<br/>CounterpartyTradeData<br/>PK: Trade_ID)]
    end

    subgraph "Integration Layer"
        MCP[🔗 Model Context Protocol<br/>AWS API MCP Server<br/>awslabs.aws-api-mcp-server@latest]
        DDB_TOOL[⚙️ Custom DynamoDB Tool<br/>boto3 direct access]
    end

    subgraph "Output Layer"
        Reports[📊 Matching Reports<br/>S3: reports/]
        Images[🖼️ PDF Images<br/>S3: PDFIMAGES/]
        JSON[📋 Trade JSON<br/>S3: extracted/]
    end

    %% Connections
    S3 --> A1
    A1 --> Images
    A1 --> Bedrock
    A2 --> Bedrock
    A3 --> Bedrock
    A3 --> JSON
    A4 --> MCP
    A4 --> DDB_TOOL
    A5 --> MCP
    A5 --> DDB_TOOL

    DDB_TOOL --> DDB1
    DDB_TOOL --> DDB2
    MCP --> DDB1
    MCP --> DDB2

    A5 --> Reports

    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef agent fill:#00A4BD,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef bedrock fill:#527FFF,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef data fill:#3F8624,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef tool fill:#DD344C,stroke:#232F3E,stroke-width:2px,color:#fff

    class S3,Images,JSON,Reports aws
    class A1,A2,A3,A4,A5 agent
    class Bedrock bedrock
    class DDB1,DDB2 data
    class MCP,DDB_TOOL tool
```

> **Note**: GitHub automatically renders Mermaid diagrams. For the complete detailed architecture with all layers, see [ARCHITECTURE.md](ARCHITECTURE.md).

### Architecture Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Input** | Amazon S3 | Trade PDF storage (BANK/COUNTERPARTY folders) |
| **AI Engine** | AWS Bedrock Claude Sonnet 4 | Document processing, OCR, entity extraction |
| **Orchestration** | CrewAI 0.175+ | Multi-agent workflow management |
| **Data Storage** | DynamoDB (2 tables) | Trade data persistence with typed attributes |
| **Integration** | MCP + boto3 | Dual approach for DynamoDB operations |
| **Output** | S3 (reports/) | Matching analysis and reconciliation reports |

### Data Flow

1. **Document Upload**: Trade PDFs uploaded to S3 bucket with source classification (BANK/COUNTERPARTY)
2. **PDF Processing**: Document Processor agent converts PDF to high-resolution JPEG images (300 DPI)
3. **OCR Extraction**: OCR Processor agent extracts text from all pages using AWS Bedrock multimodal
4. **Entity Extraction**: Trade Entity Extractor parses OCR text into structured JSON and saves to S3
5. **Data Storage**: Reporting Analyst reads JSON from S3 and stores in appropriate DynamoDB table
6. **Matching Analysis**: Matching Analyst scans both tables, performs intelligent matching, generates reports
7. **Results**: Matching reports stored in S3 with detailed analysis and classifications

### Token Optimization Strategy

The system implements **85% token reduction** through:

1. **Scratchpad Pattern**: Agents save detailed data to S3, pass only summaries/paths between tasks
2. **Concise Configurations**: `agents.yaml` and `tasks.yaml` use minimal backstories
3. **Reduced Iterations**:
   - Document Processor: `max_iter=5`
   - OCR Processor: `max_iter=10`
   - Trade Entity Extractor: `max_iter=5`
   - Reporting Analyst: `max_iter=8`
   - Matching Analyst: `max_iter=10`
4. **Rate Limiting**: `max_rpm=2` (conservative to avoid AWS throttling)
5. **Task Delays**: 15-second pause between tasks
6. **Verbose Disabled**: `verbose=False` on all agents to reduce logging overhead

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-trade-matching-system.git
cd ai-trade-matching-system

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Alternative: Using uv (faster)
uv pip install -e .
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your AWS credentials
nano .env
```

Required environment variables:
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=me-central-1
AWS_PROFILE=default

# S3 Configuration
S3_BUCKET_NAME=otc-menat-2025

# DynamoDB Tables
DYNAMODB_BANK_TABLE=BankTradeData
DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData

# Bedrock Configuration
BEDROCK_MODEL=apac.anthropic.claude-sonnet-4-20250514-v1:0

# Dummy OpenAI key (required by CrewAI, not used)
OPENAI_API_KEY=sk-dummy-key-not-used
```

### 3. Run the System

```bash
# Run the crew with default inputs
python src/latest_trade_matching_agent/main.py

# Or using CrewAI CLI
crewai run

# Or using uv
uv run latest_trade_matching_agent
```

### 4. Input Format

The system expects this input structure (see `main.py`):

```python
inputs = {
    'document_path': 's3://bucket/SOURCE_TYPE/filename.pdf',  # S3 URI or local path
    'unique_identifier': 'TRADE_ID',                          # Used for folder naming
    'source_type': 'BANK' or 'COUNTERPARTY',                  # CRITICAL for routing
    's3_bucket': 'bucket-name',
    's3_key': 'SOURCE_TYPE/filename',
    'dynamodb_bank_table': 'BankTradeData',
    'dynamodb_counterparty_table': 'CounterpartyTradeData',
    'timestamp': 'YYYYMMDD_HHMMSS'
}
```

## Project Structure

```
ai-trade-matching-system/
├── src/
│   └── latest_trade_matching_agent/
│       ├── crew_fixed.py              # Main crew definition with 5 agents
│       ├── main.py                    # Entry point
│       ├── config/
│       │   ├── agents.yaml            # Agent configurations
│       │   └── tasks.yaml             # Task definitions
│       └── tools/
│           ├── pdf_to_image.py        # PDF conversion tool
│           └── dynamodb_tool.py       # Custom DynamoDB operations
├── .env.example                       # Environment template
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project metadata
├── CLAUDE.md                          # Development guidelines
└── README.md                          # This file
```

## AWS Operations

### DynamoDB Management

```bash
# List DynamoDB tables
aws dynamodb list-tables --region me-central-1

# Scan bank trades
aws dynamodb scan --table-name BankTradeData --region me-central-1

# Scan counterparty trades
aws dynamodb scan --table-name CounterpartyTradeData --region me-central-1

# Check table details
aws dynamodb describe-table --table-name BankTradeData --region me-central-1

# Delete all items (for testing)
aws dynamodb scan --table-name CounterpartyTradeData --region me-central-1 \
  --attributes-to-get Trade_ID | jq -r '.Items[].Trade_ID.S' | \
  xargs -I {} aws dynamodb delete-item \
  --table-name CounterpartyTradeData \
  --key '{"Trade_ID":{"S":"{}"}}'
```

### S3 Management

```bash
# List S3 bucket contents
aws s3 ls s3://otc-menat-2025 --recursive

# List extracted trade JSONs
aws s3 ls s3://otc-menat-2025/extracted/COUNTERPARTY/

# Download a specific file
aws s3 cp s3://otc-menat-2025/extracted/COUNTERPARTY/trade_GCS382857_20251012.json .

# Upload a test PDF
aws s3 cp test_trade.pdf s3://otc-menat-2025/COUNTERPARTY/
```

## Key Implementation Details

### DynamoDB Integration

The system uses a **dual approach** for maximum reliability:

1. **Custom DynamoDB Tool** ([tools/dynamodb_tool.py](src/latest_trade_matching_agent/tools/dynamodb_tool.py)):
   - Direct boto3 implementation
   - Supports `put_item` and `scan` operations
   - Handles DynamoDB typed format (e.g., `{"S": "value"}`)
   - No external dependencies

2. **AWS API MCP Server**:
   - Package: `awslabs.aws-api-mcp-server@latest`
   - Provides comprehensive AWS CLI commands as MCP tools
   - Supports all AWS services
   - Auto-managed lifecycle

**Important Note**: The `awslabs.dynamodb-mcp-server` package (v2.0.0+) only provides data modeling guidance, NOT operational tools. Use `awslabs.aws-api-mcp-server` for actual DynamoDB operations.

### DynamoDB Item Format

When using DynamoDB operations, ALL attributes must be typed:

```python
{
    "Trade_ID": {"S": "GCS382857"},           # String type
    "TRADE_SOURCE": {"S": "COUNTERPARTY"},    # Must be BANK or COUNTERPARTY
    "Notional": {"N": "11160"},               # Number type
    "s3_source": {"S": "s3://..."},           # S3 path to source JSON
    "processing_timestamp": {"S": "2025-..."}  # ISO8601 timestamp
}
```

### S3 Folder Structure

```
s3://otc-menat-2025/
├── BANK/                              # Bank trade PDFs
├── COUNTERPARTY/                      # Counterparty trade PDFs
├── PDFIMAGES/                         # Converted images
│   ├── BANK/{trade_id}/
│   └── COUNTERPARTY/{trade_id}/
├── extracted/                         # Structured JSON data
│   ├── BANK/
│   └── COUNTERPARTY/
└── reports/                           # Matching analysis reports
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

## Troubleshooting

### Common Issues

**PDF Processing Errors**:
```bash
# Error: Poppler not found
# Solution: Install poppler-utils
brew install poppler  # macOS
apt-get install poppler-utils  # Ubuntu/Debian
yum install poppler-utils  # RHEL/CentOS
```

**AWS Authentication Issues**:
```bash
# Error: Unable to locate credentials
# Solution: Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=me-central-1
```

**DynamoDB Connection Issues**:
```bash
# Error: Table not found
# Solution: Create DynamoDB tables
aws dynamodb create-table \
  --table-name BankTradeData \
  --attribute-definitions AttributeName=Trade_ID,AttributeType=S \
  --key-schema AttributeName=Trade_ID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region me-central-1

aws dynamodb create-table \
  --table-name CounterpartyTradeData \
  --attribute-definitions AttributeName=Trade_ID,AttributeType=S \
  --key-schema AttributeName=Trade_ID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region me-central-1
```

**MCP Server Issues**:
```bash
# Error: MCP server not found
# Solution: Install the MCP package
pip install mcp[cli]
# Or using uv
uv pip install mcp[cli]

# Test MCP server
uvx awslabs.aws-api-mcp-server@latest
```

**Rate Limiting**:
```bash
# Error: Rate limit exceeded
# Solution: The system is configured for 2 RPM to AWS Bedrock
# Increase delays in crew_fixed.py if needed:
# - Line 209: Task delay (currently 15 seconds)
# - Line 96: max_rpm=2 (can be increased if your limits allow)
```

## Performance Optimization

### Token Usage Monitoring

```bash
# The system logs token usage after each run
# Example output:
# Usage metrics: total_tokens=122273 prompt_tokens=110872 completion_tokens=11401
```

### Processing Time

Typical processing times per trade confirmation:
- PDF to Images: ~5 seconds
- OCR Extraction (5 pages): ~30-45 seconds
- Entity Extraction: ~10-15 seconds
- DynamoDB Storage: ~2-5 seconds
- Matching Analysis: ~10-20 seconds

**Total: ~60-90 seconds per trade confirmation**

## Development

### Adding New Features

1. **New Agent**: Add to `config/agents.yaml` and implement in `crew_fixed.py`
2. **New Task**: Define in `config/tasks.yaml` and link to agent
3. **New Tool**: Create in `tools/` directory and register in `__init__.py`

### Testing

```bash
# Run with test data
python src/latest_trade_matching_agent/main.py

# Check DynamoDB for results
aws dynamodb scan --table-name CounterpartyTradeData --region me-central-1

# View S3 outputs
aws s3 ls s3://otc-menat-2025/reports/ --recursive
```

### Debugging

Enable verbose mode in `crew_fixed.py`:
```python
# Change verbose=False to verbose=True for debugging
verbose=True
```

View detailed logs:
```bash
# The system logs all operations to console
# Check for INFO, WARNING, and ERROR messages
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License Summary**:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty

---

**Built with ❤️ for derivatives operations teams worldwide**

For questions or support, please open an issue on GitHub.
