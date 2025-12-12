---
inclusion: always
---

# Technology Stack

## Core Framework

- **Python**: 3.11+ (required)
- **Strands SDK**: Multi-agent swarm framework with autonomous handoffs
- **AI Model**: AWS Bedrock Claude Sonnet 4 (`us.anthropic.claude-sonnet-4-20250514-v1:0`)
- **Region**: us-east-1 (US East - N. Virginia)

## AWS Services

- **AWS Bedrock**: Claude Sonnet 4 for document processing, text extraction, reasoning
- **Amazon S3**: Document and canonical output storage (bucket: `trade-matching-system-agentcore-production`)
- **Amazon DynamoDB**: Trade data persistence (3 tables: BankTradeData, CounterpartyTradeData, ExceptionsTable)
- **IAM**: Security and permissions management

## Key Libraries

- `strands>=0.1.0` - Multi-agent swarm framework
- `strands-tools>=0.1.0` - Strands AWS tools (use_aws)
- `boto3>=1.34.0` - AWS SDK for Python (direct DynamoDB access)
- `fastapi>=0.118.0` - Web framework (for web portal API)
- `uvicorn>=0.37.0` - ASGI server
- `python-dotenv>=1.1.0` - Environment variable management
- `pydantic>=2.0.0` - Data validation

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
# Run the Strands Swarm
python deployment/swarm/trade_matching_swarm.py \
  data/BANK/FAB_26933659.pdf \
  --source-type BANK \
  --document-id FAB_26933659 \
  --verbose

# Process a counterparty trade
python deployment/swarm/trade_matching_swarm.py \
  s3://trade-matching-system-agentcore-production/COUNTERPARTY/GCS381315_V1.pdf \
  --source-type COUNTERPARTY
```

### AWS Operations

```bash
# List DynamoDB tables
aws dynamodb list-tables --region us-east-1

# Scan bank trades
aws dynamodb scan --table-name BankTradeData --region us-east-1

# Scan counterparty trades
aws dynamodb scan --table-name CounterpartyTradeData --region us-east-1

# List S3 bucket contents
aws s3 ls s3://trade-matching-system-agentcore-production --recursive

# Upload test PDF
aws s3 cp test_trade.pdf s3://trade-matching-system-agentcore-production/COUNTERPARTY/
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
AWS_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=trade-matching-system-agentcore-production

# DynamoDB Tables
DYNAMODB_BANK_TABLE=BankTradeData
DYNAMODB_COUNTERPARTY_TABLE=CounterpartyTradeData
DYNAMODB_EXCEPTIONS_TABLE=ExceptionsTable

# Bedrock Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

### LLM Configuration

- **Model**: us.anthropic.claude-sonnet-4-20250514-v1:0
- **Temperature**: 0.1 (deterministic for financial operations)
- **Max Tokens**: 4096
- **Region**: us-east-1
- **Multimodal**: Enabled (direct PDF processing)

## Strands Swarm Configuration

- **Entry Point**: PDF Adapter agent
- **Max Handoffs**: 10 (prevents infinite loops)
- **Max Iterations**: 20 (total across all agents)
- **Execution Timeout**: 600 seconds (10 minutes)
- **Node Timeout**: 180 seconds (3 minutes per agent)
- **Repetitive Handoff Detection**: 6-window with 2 minimum unique agents

## Performance Characteristics

- **PDF Download**: ~2-5 seconds
- **Text Extraction (direct PDF)**: ~10-20 seconds
- **Trade Extraction**: ~10-15 seconds
- **DynamoDB Storage**: ~2-5 seconds
- **Matching Analysis**: ~10-20 seconds
- **Total**: ~40-70 seconds per trade confirmation
- **Token Usage**: Varies by document complexity (tracked per agent)
