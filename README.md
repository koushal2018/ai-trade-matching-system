# AI Trade Matching System

> **Enterprise-grade trade confirmation matching powered by Strands SDK on AWS Bedrock**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Strands](https://img.shields.io/badge/Strands-SDK-green.svg)
![AWS](https://img.shields.io/badge/AWS-Bedrock%20Claude%20Sonnet%204-orange.svg)
![DynamoDB](https://img.shields.io/badge/DynamoDB-boto3-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview

The AI Trade Matching System is an intelligent, cloud-native solution that automates the processing and matching of derivative trade confirmations using advanced AI capabilities. Built on AWS native services with a multi-agent swarm architecture powered by Strands SDK, the system leverages **AWS Bedrock Claude Sonnet 4** for document analysis and implements sophisticated trade matching algorithms for financial operations teams.

**Key Problem Solved**: Manual trade confirmation matching is time-consuming, error-prone, and doesn't scale with trading volumes. This system automates the entire process from PDF ingestion to intelligent matching, reducing settlement risk and operational overhead.

**Technology Stack**:
- **AI/ML**: AWS Bedrock Claude Sonnet 4 (US East region), Strands Agents Framework
- **Agent Framework**: Amazon Bedrock AgentCore Runtime with Strands SDK
- **Data Storage**: Amazon DynamoDB with boto3 direct access
- **Document Storage**: Amazon S3
- **Backend**: Python 3.11+ with FastAPI (for web portal)
- **Integration**: Strands AWS tools for S3, DynamoDB, and Bedrock operations
- **Document Processing**: AWS Bedrock multimodal for PDF text extraction

## Features

- **🤖 AI-Powered Document Processing**: AWS Bedrock Claude Sonnet 4 with multimodal capabilities for accurate PDF text extraction
- **� Swarm Adrchitecture**: 4 specialized agents (PDF Adapter, Trade Extractor, Trade Matcher, Exception Handler) that autonomously hand off tasks
- **🎯 Emergent Collaboration**: Agents decide when to hand off based on task context, not hardcoded workflows
- **☁️ Direct AWS Integration**: boto3 for DynamoDB operations, Strands AWS tools for S3 and Bedrock
- **🗄️ Intelligent Data Storage**: DynamoDB with separate tables for bank and counterparty trades
- **🔍 Professional Trade Matching**: Attribute-based matching (trades have different IDs across systems)
- **📊 Canonical Output Pattern**: Standardized adapter output format for downstream processing
- **🔐 Security-First Design**: IAM roles with least-privilege access, credential management via environment variables
- **📈 Production Ready**: Comprehensive error handling, logging, and monitoring capabilities

## Prerequisites

### Required AWS Setup

**AWS Account Requirements**:
- AWS CLI configured with appropriate permissions
- Access to AWS Bedrock (Amazon Nova Pro model in US East region: `amazon.nova-pro-v1:0`)
- DynamoDB, S3, and IAM permissions
- AWS region: `us-east-1` (US East - N. Virginia)

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
strands>=0.1.0
strands-tools>=0.1.0

# AWS integration
boto3>=1.34.0

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
        S3[(Amazon S3<br/>trade-matching-system-agentcore-production)]
        PDF --> S3
    end

    subgraph "AWS Bedrock"
        Bedrock[🧠 Amazon Nova Pro<br/>amazon.nova-pro-v1:0<br/>Temperature: 0.1 | Max Tokens: 4096]
    end

    subgraph "Processing Layer - Strands Swarm"
        A1[🤖 PDF Adapter<br/>Download & Extract Text<br/>Canonical Output]
        A2[🤖 Trade Extractor<br/>Parse & Store Trade Data]
        A3[🤖 Trade Matcher<br/>Match by Attributes<br/>Generate Reports]
        A4[🤖 Exception Handler<br/>Triage & Track Issues]

        A1 -->|Hand off| A2
        A2 -->|Hand off| A3
        A3 -->|If issues| A4
        A1 -->|If error| A4
        A2 -->|If error| A4
    end

    subgraph "Data Layer"
        DDB1[(DynamoDB<br/>BankTradeData<br/>PK: trade_id)]
        DDB2[(DynamoDB<br/>CounterpartyTradeData<br/>PK: trade_id)]
        DDB3[(DynamoDB<br/>ExceptionsTable<br/>PK: exception_id)]
    end

    subgraph "Output Layer"
        Reports[📊 Matching Reports<br/>S3: reports/]
        Canonical[📋 Canonical Output<br/>S3: extracted/]
        Exceptions[⚠️ Exception Records<br/>DynamoDB]
    end

    %% Connections
    S3 --> A1
    A1 --> Bedrock
    A1 --> Canonical
    A2 --> DDB1
    A2 --> DDB2
    A3 --> DDB1
    A3 --> DDB2
    A3 --> Reports
    A4 --> DDB3
    A4 --> Exceptions

    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef agent fill:#00A4BD,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef bedrock fill:#527FFF,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef data fill:#3F8624,stroke:#232F3E,stroke-width:2px,color:#fff

    class S3,Canonical,Reports,Exceptions aws
    class A1,A2,A3,A4 agent
    class Bedrock bedrock
    class DDB1,DDB2,DDB3 data
```

> **Note**: GitHub automatically renders Mermaid diagrams. For the complete detailed architecture with all layers, see [ARCHITECTURE.md](ARCHITECTURE.md).

### Architecture Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Input** | Amazon S3 | Trade PDF storage (BANK/COUNTERPARTY folders) |
| **AI Engine** | AWS Bedrock Claude Sonnet 4 | PDF text extraction via multimodal API |
| **Orchestration** | Strands Swarm | Autonomous agent collaboration with handoffs |
| **Data Storage** | DynamoDB (3 tables) | Trade data + exceptions with typed attributes |
| **Integration** | boto3 + Strands tools | Direct AWS SDK access for reliability |
| **Output** | S3 (reports/) | Matching analysis and reconciliation reports |

### Data Flow

1. **Document Upload**: Trade PDFs uploaded to S3 bucket with source classification (BANK/COUNTERPARTY)
2. **PDF Adapter**: Downloads PDF from S3, extracts text using Bedrock multimodal, saves canonical output
3. **Trade Extraction**: Parses extracted text, identifies trade fields, stores in appropriate DynamoDB table
4. **Trade Matching**: Scans both tables, matches by attributes (NOT Trade_ID), calculates confidence scores
5. **Exception Handling**: Analyzes breaks/mismatches, determines severity, tracks with SLA deadlines
6. **Results**: Matching reports and exception records stored for operations team review

### Swarm Configuration

The system uses **Strands Swarm** for autonomous collaboration:

1. **Entry Point**: PDF Adapter agent starts the workflow
2. **Max Handoffs**: 10 (prevents infinite loops)
3. **Max Iterations**: 20 (total across all agents)
4. **Execution Timeout**: 600 seconds (10 minutes)
5. **Node Timeout**: 180 seconds (3 minutes per agent)
6. **Repetitive Handoff Detection**: 6-window with 2 minimum unique agents
7. **Temperature**: 0.1 (deterministic behavior for financial operations)

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
AWS_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=trade-matching-system-agentcore-production

# DynamoDB Tables
DYNAMODB_BANK_TABLE=BankTradeData
DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData
DYNAMODB_EXCEPTIONS_TABLE=ExceptionsTable

# Bedrock Configuration
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
```

### 3. Run the System

```bash
# Run the swarm with CLI arguments
python deployment/swarm/trade_matching_swarm.py \
  data/BANK/FAB_26933659.pdf \
  --source-type BANK \
  --document-id FAB_26933659 \
  --verbose

# Or process a counterparty trade
python deployment/swarm/trade_matching_swarm.py \
  s3://trade-matching-system-agentcore-production/COUNTERPARTY/GCS381315_V1.pdf \
  --source-type COUNTERPARTY
```

### 4. Input Format

The `process_trade_confirmation()` function accepts:

```python
result = process_trade_confirmation(
    document_path="s3://bucket/key or just key",  # S3 path to PDF
    source_type="BANK" or "COUNTERPARTY",         # CRITICAL for routing
    document_id="optional_doc_id",                # Auto-generated if not provided
    correlation_id="optional_corr_id"             # For tracing
)
```

## Project Structure

```
ai-trade-matching-system/
├── deployment/swarm/                  # Strands Swarm implementation
│   ├── trade_matching_swarm.py        # Main swarm with 4 agents
│   └── requirements.txt               # Swarm dependencies
├── src/latest_trade_matching_agent/   # Supporting modules
│   ├── agents/                        # Agent implementations
│   ├── exception_handling/            # Exception management with RL
│   ├── matching/                      # Fuzzy matching, scoring, classification
│   ├── memory/                        # AgentCore memory integration
│   ├── models/                        # Pydantic models (trade, events, registry)
│   ├── observability/                 # Metrics and tracing
│   ├── orchestrator/                  # SLA monitoring, compliance, control
│   ├── policy/                        # Policy management
│   └── tools/                         # Custom tools (PDF, DynamoDB, LLM)
├── deployment/                        # AgentCore deployment packages
│   ├── pdf_adapter/                   # PDF Adapter Agent deployment
│   ├── trade_extraction/              # Trade Extraction Agent deployment
│   ├── trade_matching/                # Trade Matching Agent deployment
│   ├── exception_management/          # Exception Management Agent deployment
│   ├── orchestrator/                  # Orchestrator Agent deployment
│   └── deploy_all.sh                  # Master deployment script
├── legacy/                            # Archived legacy code
│   └── crewai/                        # Legacy CrewAI implementation (not used)
├── terraform/                         # Infrastructure as Code
│   ├── agentcore/                     # AgentCore infrastructure (SQS, DynamoDB, etc.)
│   └── *.tf                           # Core AWS resources
├── tests/                             # Test suites
│   └── e2e/                           # End-to-end tests
├── web-portal/                        # React frontend
├── web-portal-api/                    # FastAPI backend
├── config/                            # Application configuration
├── data/                              # Sample trade PDFs
├── docs/                              # Documentation
├── lambda/                            # Lambda functions
├── scripts/                           # Utility scripts
├── .env.example                       # Environment template
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project metadata
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

### Agent Handoff Pattern

The swarm uses **autonomous handoffs** where agents decide when to pass control:

1. **PDF Adapter** → **Trade Extractor**: After successful text extraction and canonical output saved
2. **Trade Extractor** → **Trade Matcher**: After storing trade data in DynamoDB
3. **Trade Matcher** → **Exception Handler**: If match classification is REVIEW_REQUIRED or BREAK
4. **Any Agent** → **Exception Handler**: On errors or processing failures

### DynamoDB Integration

The system uses **direct boto3 access** via Strands tools:

- **store_trade_in_dynamodb**: Stores extracted trade data with proper typing
- **scan_trades_table**: Retrieves all trades from BANK or COUNTERPARTY table
- **store_exception_record**: Tracks exceptions with SLA deadlines
- All operations use DynamoDB typed format (e.g., `{"S": "value"}`, `{"N": "123"}`)

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
s3://trade-matching-system-agentcore-production/
├── BANK/                              # Bank trade PDFs (input)
├── COUNTERPARTY/                      # Counterparty trade PDFs (input)
├── extracted/                         # Canonical adapter output
│   ├── BANK/{document_id}.json
│   └── COUNTERPARTY/{document_id}.json
└── reports/                           # Matching analysis reports
    └── matching_report_{trade_id}_{timestamp}.md
```

### Local Processing Directory

```
/tmp/
└── {document_id}.pdf                  # Temporary PDF download
```

## Troubleshooting

### Common Issues

**PDF Processing Errors**:
```bash
# Error: Failed to extract text with Bedrock
# Solution: Verify Bedrock model access
aws bedrock list-foundation-models --region us-east-1 | grep nova-pro

# Ensure you have access to the model
aws bedrock get-foundation-model \
  --model-identifier amazon.nova-pro-v1:0 \
  --region us-east-1
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
  --attribute-definitions AttributeName=trade_id,AttributeType=S \
  --key-schema AttributeName=trade_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

aws dynamodb create-table \
  --table-name CounterpartyTradeData \
  --attribute-definitions AttributeName=trade_id,AttributeType=S \
  --key-schema AttributeName=trade_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

aws dynamodb create-table \
  --table-name ExceptionsTable \
  --attribute-definitions AttributeName=exception_id,AttributeType=S \
  --key-schema AttributeName=exception_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Strands Installation Issues**:
```bash
# Error: strands module not found
# Solution: Install Strands SDK
pip install strands strands-tools

# Or using uv
uv pip install strands strands-tools
```

**Rate Limiting**:
```bash
# Error: Rate limit exceeded
# Solution: The swarm has built-in timeouts:
# - execution_timeout: 600 seconds (10 minutes total)
# - node_timeout: 180 seconds (3 minutes per agent)
# Adjust these in create_trade_matching_swarm() if needed
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

1. **New Agent**: Create agent factory function in `trade_matching_swarm.py`
2. **New Tool**: Define with `@tool` decorator and add to agent's tools list
3. **New Handoff**: Update agent system prompts with handoff conditions

### Testing

```bash
# Run with test data
python deployment/swarm/trade_matching_swarm.py \
  data/BANK/FAB_26933659.pdf \
  --source-type BANK \
  --verbose

# Check DynamoDB for results
aws dynamodb scan --table-name BankTradeData --region us-east-1

# View S3 outputs
aws s3 ls s3://trade-matching-system-agentcore-production/reports/ --recursive
```

### Debugging

Enable verbose logging:
```bash
python deployment/swarm/trade_matching_swarm.py \
  your_document.pdf \
  --source-type BANK \
  --verbose
```

View detailed logs:
```bash
# The system logs all operations to console
# Check for INFO, WARNING, and ERROR messages
# Swarm execution includes node_history showing agent handoffs
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
