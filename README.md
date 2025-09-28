# 🏦 AI Trade Matching System

> **Enterprise-grade trade confirmation matching powered by CrewAI on AWS EKS**

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-0.80+-green.svg)
![AWS](https://img.shields.io/badge/AWS-Bedrock%20Claude-orange.svg)
![EKS](https://img.shields.io/badge/EKS-Kubernetes-blue.svg)
![DynamoDB](https://img.shields.io/badge/DynamoDB-MCP-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

An intelligent system that automatically processes derivative trade confirmations using AWS Bedrock Claude Sonnet for PDF extraction and multi-agent workflows for sophisticated trade matching, deployed on AWS EKS with MCP DynamoDB integration.

## ⚠️ Disclaimer

**This is a personal educational project and has no affiliation, endorsement, or connection with any financial institutions, banks, or companies mentioned in the documentation or sample data. All bank names, trade references, and financial data used are purely fictional and for demonstration purposes only. This project is intended for learning and research purposes.**

## ✨ Key Features

- **📄 AI-Powered PDF Processing** - AWS Bedrock Claude Sonnet 4 with multimodal capabilities for document analysis
- **🖼️ PDF-to-Image Pipeline** - High-quality image conversion for optimal OCR processing
- **🤖 Multi-Agent Architecture** - 4 specialized agents: Document Processor, OCR Extractor, Data Analyst, Matching Analyst
- **☁️ AWS EKS Deployment** - Enterprise-grade Kubernetes orchestration with auto-scaling
- **🗄️ DynamoDB Integration** - MCP (Model Context Protocol) for seamless database operations
- **🔍 Intelligent Matching** - Professional-grade matching logic with tolerance handling
- **📊 Event-Driven Architecture** - S3 triggers, SNS notifications, and real-time processing
- **🔐 IRSA Security** - IAM Roles for Service Accounts with least-privilege access
- **📈 Monitoring & Observability** - Prometheus metrics, health checks, and comprehensive logging

## 🚀 Quick Start

### Prerequisites

- **AWS Account** with appropriate permissions
- **kubectl** configured for EKS cluster access
- **Docker** for building container images
- **Terraform** (optional, for infrastructure deployment)
- **AWS CLI** configured
- **Python 3.12+** (for local development)

### Quick Start (AWS EKS Deployment)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ai-trade-matching-system.git
cd ai-trade-matching-system

# 2. Deploy to existing EKS cluster
kubectl apply -f k8s/

# 3. Check deployment status
kubectl get pods -n trade-matching

# 4. Upload trade documents to S3
aws s3 cp your-trade-document.pdf s3://your-bucket/BANK/

# 5. Monitor processing
kubectl logs -f deployment/trade-matching-system -n trade-matching
```

### Local Development Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# 3. Run locally
python src/latest_trade_matching_agent/eks_main.py
```

## 📁 Project Structure

```
ai-trade-matching-system/
├── src/
│   └── latest_trade_matching_agent/
│       ├── config/
│       │   ├── agents.yaml          # AI agent definitions
│       │   └── tasks.yaml           # Task workflows
│       ├── tools/
│       │   ├── pdf_to_image.py      # PDF conversion tool
│       │   ├── ocr_tool.py          # OCR extraction
│       │   └── custom_tool.py       # Custom CrewAI tools
│       ├── crew_fixed.py            # Main orchestration
│       └── eks_main.py              # EKS FastAPI entry point
├── k8s/
│   ├── deployment.yaml              # Kubernetes deployment
│   ├── service.yaml                 # Service definition
│   ├── configmap.yaml               # Configuration
│   └── rbac.yaml                    # RBAC permissions
├── terraform/
│   ├── eks.tf                       # EKS cluster configuration
│   ├── iam.tf                       # IAM roles and policies
│   └── dynamodb.tf                  # DynamoDB tables
├── lambda/
│   └── s3_trigger/                  # S3 event trigger function
├── monitoring/
│   └── prometheus/                  # Monitoring configs
├── Dockerfile                       # Container image
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🔄 How It Works

### Event-Driven Processing Architecture

```
📁 S3 Upload:
   └── trade-document.pdf uploaded to s3://bucket/BANK/

📡 S3 Event Trigger:
   └── Lambda function invokes EKS processing endpoint

🚀 EKS Processing:
   ├── 1. Document Processor → PDF to high-quality images (300 DPI)
   ├── 2. OCR Extractor → Bedrock Claude extracts trade details
   ├── 3. Data Analyst → Stores structured data in DynamoDB (via MCP)
   └── 4. Matching Analyst → Intelligent matching with professional logic

📊 Results:
   ├── DynamoDB records updated
   ├── SNS notifications sent
   └── Processing logs available via kubectl
```

### AWS Architecture

- **EKS Cluster** - Kubernetes orchestration with auto-scaling
- **IRSA** - IAM Roles for Service Accounts for secure AWS access
- **DynamoDB** - Trade data storage with MCP integration
- **S3** - Document storage and processed images
- **Bedrock** - Claude Sonnet 4 for AI processing
- **SNS** - Event notifications
- **CloudWatch** - Logging and monitoring

## 🎯 Usage Examples

### Upload and Process Documents
```bash
# Upload via AWS CLI
aws s3 cp trade-confirmation.pdf s3://your-bucket/BANK/

# Or via API
curl -X POST http://your-eks-cluster/process \
  -H "Content-Type: application/json" \
  -d '{
    "s3_bucket": "your-bucket",
    "s3_key": "BANK/trade-confirmation.pdf",
    "source_type": "BANK",
    "event_time": "2025-01-28T10:30:00Z",
    "unique_identifier": "trade-001"
  }'
```

### Monitor Processing
```bash
# View real-time logs
kubectl logs -f deployment/trade-matching-system -n trade-matching

# Check processing status
curl http://your-eks-cluster/status/trade-001

# View health status
curl http://your-eks-cluster/health
```

### Scale the System
```bash
# Scale replicas
kubectl scale deployment/trade-matching-system --replicas=5 -n trade-matching

# Check HPA status
kubectl get hpa -n trade-matching
```

## 🛠️ Configuration

### Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: trade-matching-config
data:
  AWS_REGION: "us-east-1"
  LOG_LEVEL: "INFO"
  PROCESSING_TIMEOUT: "600"
  MAX_RETRIES: "3"
```

### IRSA Configuration
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: trade-matching-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/trade-matching-irsa-role
```

### Environment Variables (Local Development)
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=your-profile

# MCP Configuration
DDB_MCP_READONLY=false
```

### Agent Roles

| Agent | Role | Tools |
|-------|------|-------|
| **Document Processor** | Converts PDFs to images | PDFToImageTool, FileWriterTool |
| **Researcher** | Extracts trade data using OCR | OCRTool, FileReadTool, FileWriterTool |
| **Reporting Analyst** | Stores data in TinyDB | FileReadTool, FileWriterTool |
| **Matching Analyst** | Performs intelligent matching | FileReadTool, FileWriterTool |

## 📊 Sample Processing Logs

```
INFO:src.latest_trade_matching_agent.eks_main:{"processing_id": "fab-test_1759053194", "event": "Processing initiated"}
INFO:src.latest_trade_matching_agent.eks_main:{"processing_id": "fab-test_1759053194", "event": "Document downloaded from S3"}
INFO:src.latest_trade_matching_agent.eks_main:{"tool_count": 30, "event": "Connected to DynamoDB MCP server"}

🚀 Crew: crew
├── 📋 Task: document_processing_task
│   Status: Executing Task...
└── 🤖 Agent Started: Document Processing Specialist

✅ PDF Conversion Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Source: /tmp/processing/fab-test_1759053194/data/BANK/FAB_26933659.pdf
📊 Total Pages: 4
🎯 DPI: 300
📸 Format: JPEG
☁️  S3 Location: s3://bucket/PDFIMAGES/BANK/fab-test/
💾 Local Files: 4 files in /tmp/processing/fab-test/pdf_images/fab-test
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Images ready for OCR processing

INFO:LiteLLM: LiteLLM completion() model= global.anthropic.claude-sonnet-4
INFO:httpx: HTTP Request: POST https://bedrock-runtime.us-east-1.amazonaws.com/model/...

🔧 Used PDF to Image Converter (1)
🔧 Used Optical Character Recognition Tool (4)
🔧 Used DynamoDB Storage Tool (1)

✅ Processing Complete!
Status: SUCCESS
Trade Reference: FAB-26933659
Counterparty: MERRILL LYNCH INTERNATIONAL
Match Status: PENDING_COUNTERPARTY_CONFIRMATION
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Test basic functionality
pytest tests/test_basic.py

# Run with coverage
pytest --cov=src tests/
```

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Poppler not found** | Install: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux) |
| **AWS credentials error** | Configure AWS CLI or set environment variables in .env |
| **PDF conversion fails** | Ensure PDF is not password-protected and poppler is installed |
| **Import errors** | Run `pip install -r requirements.txt` |
| **Rate limiting** | Built-in rate limiting (2 RPM) - increase if needed in crew_fixed.py |

## 🎨 Customization

### Modify Document Path
```python
# In src/latest_trade_matching_agent/main.py
def run():
    document_path = './data/BANK/your_custom_file.pdf'  # Change this
    # ... rest of the function
```

### Adjust Rate Limits
```python
# In src/latest_trade_matching_agent/crew_fixed.py
@agent
def researcher(self) -> Agent:
    return Agent(
        # ...
        max_rpm=5,  # Increase from 2 if needed
        max_execution_time=900,  # Adjust timeout
        # ...
    )
```

## 📈 Performance & Scaling

- ⚡ PDF conversion: ~2-3 seconds per page at 300 DPI
- 🤖 OCR extraction: 30-90 seconds per document (Bedrock Claude)
- 💾 DynamoDB storage: <1 second per trade via MCP
- 🔍 Matching analysis: 10-30 seconds depending on complexity
- 🎯 HPA scaling: 2-6 replicas based on CPU/memory
- 📊 Throughput: ~100 documents/hour per replica
- 🔐 Cold start: ~10 seconds for new pods

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## 🙏 Acknowledgments

- [CrewAI](https://www.crewai.com/) - Multi-agent framework
- [AWS Bedrock](https://aws.amazon.com/bedrock/) - Claude Sonnet 4 model API
- [AWS EKS](https://aws.amazon.com/eks/) - Kubernetes orchestration
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol for DynamoDB
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [pdf2image](https://github.com/Belval/pdf2image) - PDF to image conversion

## 📧 Contact

koushaldutt@gmail.com

---

**Built with ❤️ for derivatives operations teams worldwide**