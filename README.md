<div align="center">

# AI Trade Matching System

### Enterprise-Grade Trade Confirmation Matching Powered by AWS Bedrock

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Amazon Nova Pro](https://img.shields.io/badge/Amazon-Nova%20Pro-FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![Strands SDK](https://img.shields.io/badge/Strands-SDK-00A4BD.svg?style=for-the-badge)](https://strandsagents.com)
[![AgentCore](https://img.shields.io/badge/Amazon-AgentCore-232F3E.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/agentcore/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<br/>

**Automate trade confirmation matching with AI agents that understand financial documents**

[Getting Started](#-quick-start) | [Architecture](#-architecture) | [Documentation](#-documentation) | [Contributing](#-contributing)

<br/>

<img src="generated-diagrams/ai-trade-matching-hero.png" alt="Architecture" width="900"/>

</div>

---

## Overview

The **AI Trade Matching System** is an intelligent, cloud-native solution that automates the processing and matching of derivative trade confirmations using advanced AI capabilities. Built on AWS native services with a **multi-agent swarm architecture** powered by Strands SDK, the system leverages **Amazon Nova Pro** for document analysis and implements sophisticated trade matching algorithms for financial operations teams.

### The Problem

Manual trade confirmation matching is:
- **Time-consuming**: Hours spent comparing PDF confirmations
- **Error-prone**: Human mistakes lead to settlement failures
- **Doesn't scale**: Growing trade volumes overwhelm operations teams

### The Solution

An AI-powered system that:
- **Extracts** trade data from PDF confirmations using multimodal AI
- **Matches** trades across counterparties using fuzzy matching algorithms
- **Handles exceptions** intelligently with ML-based triage
- **Scales automatically** on AWS Bedrock AgentCore Runtime

---

## Key Features

<table>
<tr>
<td width="50%">

### AI-Powered Processing
- **Amazon Nova Pro** multimodal extraction
- Intelligent document understanding
- 95%+ accuracy on trade field extraction

### Multi-Agent Architecture
- **4 specialized agents** working autonomously
- Emergent collaboration via handoffs
- Self-healing error recovery

</td>
<td width="50%">

### Enterprise Ready
- **DynamoDB** for scalable data storage
- **S3** for document management
- CloudWatch monitoring & alerts

### Production Deployment
- **AgentCore Runtime** for serverless scaling
- Terraform infrastructure as code
- React dashboard for operations

</td>
</tr>
</table>

---

## Architecture

The system uses a **swarm architecture** where specialized agents collaborate autonomously:

```
                                    +------------------+
                                    |   AWS Bedrock    |
                                    |  Amazon Nova Pro |
                                    +--------+---------+
                                             |
    +----------------+              +--------v---------+
    |   S3 Bucket    |              |                  |
    | BANK/          +------------->+   PDF Adapter    +----+
    | COUNTERPARTY/  |              |     Agent        |    |
    +----------------+              +--------+---------+    |
                                             |              |
                                    +--------v---------+    |
                                    |                  |    |
                                    | Trade Extractor  |    |
                                    |     Agent        |    |
                                    +--------+---------+    |
                                             |              |
         +-------------------+      +--------v---------+    |
         |    DynamoDB       |<-----+                  |    |
         | BankTradeData     |      |  Trade Matcher   |    |
         | CounterpartyData  |<-----+     Agent        |    |
         +-------------------+      +--------+---------+    |
                                             |              |
                                    +--------v---------+    |
                                    |                  |<---+
                                    |Exception Handler |
                                    |     Agent        |
                                    +------------------+
```

### Agent Responsibilities

| Agent | Purpose | Key Operations |
|-------|---------|----------------|
| **PDF Adapter** | Document ingestion | Download PDF, extract text via Bedrock multimodal, save canonical output |
| **Trade Extractor** | Data extraction | Parse trade fields, validate data, store in DynamoDB |
| **Trade Matcher** | Reconciliation | Match trades by attributes, calculate confidence scores, generate reports |
| **Exception Handler** | Issue management | Triage breaks, assign severity, track SLA deadlines |

### Data Flow

```mermaid
graph LR
    A[PDF Upload] --> B[S3 Bucket]
    B --> C[PDF Adapter]
    C --> D[Bedrock AI]
    D --> E[Trade Extractor]
    E --> F[(DynamoDB)]
    F --> G[Trade Matcher]
    G --> H{Match?}
    H -->|Yes| I[Report]
    H -->|No| J[Exception Handler]
    J --> K[(Exceptions Table)]
```

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **AWS Account** with Bedrock access (us-east-1)
- **AWS CLI** configured with appropriate permissions

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/ai-trade-matching-system.git
cd ai-trade-matching-system

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

Required variables:
```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

### 3. Deploy Infrastructure

```bash
cd terraform/agentcore
terraform init
terraform apply
```

### 4. Deploy Agents to AgentCore Runtime

```bash
# Install AgentCore CLI
pip install bedrock-agentcore-starter-toolkit

# Deploy PDF Adapter Agent
cd deployment/pdf_adapter
agentcore configure --entrypoint pdf_adapter_agent_strands.py --non-interactive
agentcore launch

# Deploy Trade Extraction Agent
cd ../trade_extraction
agentcore configure --entrypoint trade_extraction_agent_strands.py --non-interactive
agentcore launch

# Deploy Trade Matching Agent
cd ../trade_matching
agentcore configure --entrypoint trade_matching_agent_strands.py --non-interactive
agentcore launch

# Deploy Exception Management Agent
cd ../exception_management
agentcore configure --entrypoint exception_management_agent_strands.py --non-interactive
agentcore launch
```

### 5. Run the System

**Local Development (Strands Swarm):**
```bash
# Process a bank trade confirmation
python deployment/swarm/trade_matching_swarm.py \
  data/BANK/FAB_26933659.pdf \
  --source-type BANK \
  --verbose

# Process a counterparty trade
python deployment/swarm/trade_matching_swarm.py \
  s3://your-bucket/COUNTERPARTY/GCS381315_V1.pdf \
  --source-type COUNTERPARTY
```

**Production (AgentCore Runtime):**
```bash
# Invoke the orchestrator agent with a trade document
agentcore invoke '{
  "document_path": "s3://your-bucket/BANK/FAB_26933659.pdf",
  "source_type": "BANK",
  "document_id": "FAB_26933659"
}' --agent orchestrator_agent

# Check agent status
agentcore status --agent pdf_adapter_agent
agentcore status --agent trade_extraction_agent
```

---

## Project Structure

```
ai-trade-matching-system/
├── deployment/                    # Agent deployment packages
│   ├── swarm/                     # Main swarm implementation
│   ├── pdf_adapter/               # PDF processing agent
│   ├── trade_extraction/          # Data extraction agent
│   ├── trade_matching/            # Matching agent
│   ├── exception_management/      # Exception handling agent
│   └── orchestrator/              # Orchestration agent

├── terraform/                     # Infrastructure as Code
│   └── agentcore/                 # AgentCore deployment
├── web-portal/                    # React dashboard
├── web-portal-api/                # FastAPI backend
├── tests/                         # Test suites
├── config/                        # Configuration files
└── data/                          # Sample trade PDFs
```

---

## Web Dashboard

The system includes a **React-based dashboard** for operations teams:

- **Real-time agent monitoring** - Track agent health and performance
- **Trade matching results** - View matched/unmatched trades
- **Exception management** - Handle breaks and discrepancies
- **Processing metrics** - Monitor throughput and latency

### Running the Dashboard

```bash
# Start the API backend
cd web-portal-api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Start the frontend (in another terminal)
cd web-portal
npm install
npm run dev
```

---

## AWS Services

| Service | Purpose |
|---------|---------|
| **Bedrock** | Amazon Nova Pro for document analysis |
| **AgentCore** | Serverless agent runtime |
| **DynamoDB** | Trade data & exceptions storage |
| **S3** | Document & report storage |
| **CloudWatch** | Monitoring & logging |
| **IAM** | Security & access control |

---

## Performance

| Metric | Value |
|--------|-------|
| PDF Processing | ~5 seconds |
| OCR Extraction (5 pages) | ~30-45 seconds |
| Trade Matching | ~10-20 seconds |
| **Total per Trade** | **~60-90 seconds** |

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Detailed system architecture |
| [HOW_TO_RUN_TESTS.md](HOW_TO_RUN_TESTS.md) | Testing guide |
| [terraform/agentcore/README.md](terraform/agentcore/README.md) | Infrastructure deployment |
| [deployment/README.md](deployment/README.md) | Agent deployment guide |

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run property-based tests
pytest tests/property_based/ -v

# Run end-to-end tests
pytest tests/e2e/ -v
```

### Adding a New Agent

1. Create agent factory function in `deployment/swarm/`
2. Define tools with `@tool` decorator
3. Update swarm configuration with handoff conditions

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built for derivatives operations teams worldwide**

[Report Bug](../../issues) | [Request Feature](../../issues) | [Documentation](docs/)

</div>
