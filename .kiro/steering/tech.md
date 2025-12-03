---
inclusion: always
---

# Technology Stack

## Core Framework

- **Python**: 3.11+ (required)
- **CrewAI**: 0.175+ multi-agent orchestration framework
- **AI Model**: AWS Bedrock Claude Sonnet 4 (`apac.anthropic.claude-sonnet-4-20250514-v1:0`)
- **Region**: me-central-1 (Middle East - UAE)

## AWS Services

- **AWS Bedrock**: Claude Sonnet 4 for document processing, OCR, entity extraction
- **Amazon S3**: Document and image storage (bucket: `otc-menat-2025`)
- **Amazon DynamoDB**: Trade data persistence (2 tables: BankTradeData, CounterpartyTradeData)
- **IAM**: Security and permissions management

## Key Libraries

- `crewai>=0.201.0` - Multi-agent framework
- `crewai-tools[mcp]>=0.14.0` - CrewAI tools with MCP support
- `anthropic>=0.69.0` - Anthropic API client
- `litellm>=1.74.9` - LLM provider abstraction
- `boto3>=1.40.0` - AWS SDK for Python
- `pdf2image>=1.17.0` - PDF to image conversion
- `Pillow>=11.3.0` - Image processing
- `fastapi>=0.118.0` - Web framework (for EKS deployment)
- `uvicorn>=0.37.0` - ASGI server
- `mcp>=1.16.0` - Model Context Protocol for AWS operations
- `python-dotenv>=1.1.0` - Environment variable management
- `pydantic>=2.11.0` - Data validation

## System Dependencies

- **poppler-utils**: Required for PDF processing (install via `brew install poppler` on macOS)
- **uv** or **pip**: Package manager (uv recommended for faster installs)

## Infrastructure as Code

- **Terraform**: >= 1.0 for AWS infrastructure provisioning
- **Backend**: S3 bucket for state storage with DynamoDB locking

## Common Commands

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Alternative: Using uv (faster)
uv pip install -e .
```

### Running the System

```bash
# Run with main.py
python src/latest_trade_matching_agent/main.py

# Run with CrewAI CLI
crewai run

# Run with uv
uv run latest_trade_matching_agent
```

### AWS Operations

```bash
# List DynamoDB tables
aws dynamodb list-tables --region me-central-1

# Scan bank trades
aws dynamodb scan --table-name BankTradeData --region me-central-1

# Scan counterparty trades
aws dynamodb scan --table-name CounterpartyTradeData --region me-central-1

# List S3 bucket contents
aws s3 ls s3://otc-menat-2025 --recursive

# Upload test PDF
aws s3 cp test_trade.pdf s3://otc-menat-2025/COUNTERPARTY/
```

### Terraform

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan infrastructure changes
terraform plan

# Apply infrastructure
terraform apply

# Destroy infrastructure
terraform destroy
```

## Configuration

### Environment Variables

Required in `.env` file:

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

### LLM Configuration

- **Model**: bedrock/apac.anthropic.claude-sonnet-4-20250514-v1:0
- **Temperature**: 0.7
- **Max Tokens**: 4096
- **Rate Limit**: 2 RPM (requests per minute)
- **Max Retry**: 1
- **Multimodal**: Enabled

## MCP Integration

- **Server**: awslabs.aws-api-mcp-server@latest
- **Command**: uvx (requires uv installation)
- **Purpose**: AWS CLI commands as MCP tools for DynamoDB and other AWS operations
- **Lifecycle**: Auto-managed by @CrewBase decorator

**Important**: Use `awslabs.aws-api-mcp-server` for actual DynamoDB operations, NOT `awslabs.dynamodb-mcp-server` (v2.0.0+ only provides data modeling guidance).

## Performance Characteristics

- **PDF Processing**: ~5 seconds
- **OCR Extraction (5 pages)**: ~30-45 seconds
- **Entity Extraction**: ~10-15 seconds
- **DynamoDB Storage**: ~2-5 seconds
- **Matching Analysis**: ~10-20 seconds
- **Total**: ~60-90 seconds per trade confirmation
- **Token Usage**: ~120K tokens per complete workflow (85% reduction achieved)
