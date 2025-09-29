# AI Trade Matching System

> **Enterprise-grade trade confirmation matching powered by CrewAI on AWS EKS**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-0.80+-green.svg)
![AWS](https://img.shields.io/badge/AWS-Bedrock%20Claude-orange.svg)
![EKS](https://img.shields.io/badge/EKS-Kubernetes-blue.svg)
![DynamoDB](https://img.shields.io/badge/DynamoDB-MCP-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview

The AI Trade Matching System is an intelligent, cloud-native solution that automates the processing and matching of derivative trade confirmations using advanced AI capabilities. Built on AWS EKS with a multi-agent architecture powered by CrewAI, the system leverages AWS Bedrock Claude Sonnet for document analysis and implements sophisticated trade matching algorithms for financial operations teams.

**Key Problem Solved**: Manual trade confirmation matching is time-consuming, error-prone, and doesn't scale with trading volumes. This system automates the entire process from PDF ingestion to intelligent matching, reducing settlement risk and operational overhead.

**Technology Stack**:
- **AI/ML**: AWS Bedrock Claude Sonnet 4, CrewAI multi-agent framework
- **Infrastructure**: AWS EKS, Lambda, DynamoDB, S3
- **Backend**: FastAPI, Python 3.11+
- **Integration**: Model Context Protocol (MCP) for DynamoDB
- **Infrastructure as Code**: Terraform
- **Monitoring**: Prometheus, Grafana

## Features

- **🤖 AI-Powered Document Processing**: AWS Bedrock Claude Sonnet 4 with multimodal capabilities for accurate PDF text extraction
- **📄 Advanced PDF Pipeline**: High-quality PDF-to-image conversion (300 DPI) optimized for OCR processing
- **🎯 Multi-Agent Architecture**: 4 specialized agents handling document processing, OCR extraction, data analysis, and matching
- **☁️ Cloud-Native Deployment**: Enterprise-grade AWS EKS orchestration with auto-scaling and high availability
- **🗄️ Intelligent Data Storage**: DynamoDB integration via MCP with separate tables for bank and counterparty trades
- **🔍 Professional Trade Matching**: Sophisticated matching logic with tolerance handling and break analysis
- **📊 Event-Driven Processing**: S3 triggers, Lambda functions, and real-time processing workflows
- **🔐 Security-First Design**: IRSA (IAM Roles for Service Accounts) with least-privilege access
- **📈 Production Monitoring**: Comprehensive health checks, metrics, and observability
- **⚡ Auto-Scaling**: Horizontal Pod Autoscaler (HPA) for dynamic scaling based on workload

## Prerequisites

### Required AWS Setup

**AWS Account Requirements**:
- AWS CLI configured with appropriate permissions
- Access to AWS Bedrock (Claude Sonnet model)
- EKS cluster creation permissions
- DynamoDB, S3, Lambda, and IAM permissions

**AWS Services Used**:
```bash
# Core services
- Amazon EKS (Kubernetes orchestration)
- AWS Bedrock (Claude Sonnet AI model)
- Amazon DynamoDB (trade data storage)
- Amazon S3 (document storage)
- AWS Lambda (event processing)
- Amazon SNS (notifications)

# Supporting services
- IAM (security and permissions)
- CloudWatch (logging and monitoring)
- ECR (container registry)
```

### Development Environment

**Required Tools**:
```bash
# Container and orchestration
Docker >= 20.10
kubectl >= 1.28
helm >= 3.12 (optional)

# Infrastructure
Terraform >= 1.5
AWS CLI >= 2.13

# Development
Python >= 3.11
pip >= 23.0
```

**Python Dependencies**:
```bash
# Core framework
crewai>=0.80.0
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

# Web framework
fastapi
uvicorn
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌──────────┐    ┌─────────────────────────────┐ │
│  │   S3    │───▶│  Lambda  │───▶│         EKS Cluster         │ │
│  │ Bucket  │    │ Trigger  │    │  ┌─────────────────────────┐ │ │
│  └─────────┘    └──────────┘    │  │   Trade Matching Pod    │ │ │
│       │                         │  │                         │ │ │
│       │                         │  │  ┌─────────────────────┐│ │ │
│       ▼                         │  │  │  Document Processor ││ │ │
│  ┌─────────┐                    │  │  │  OCR Extractor     ││ │ │
│  │ Bedrock │◀───────────────────┼──┼──│  Data Analyst      ││ │ │
│  │ Claude  │                    │  │  │  Matching Analyst  ││ │ │
│  └─────────┘                    │  │  └─────────────────────┘│ │ │
│                                 │  └─────────────────────────┘ │ │
│                                 └─────────────────────────────┘ │
│                                              │                  │
│                                              ▼                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    DynamoDB                                 │ │
│  │  ┌─────────────────┐    ┌─────────────────────────────────┐│ │
│  │  │ BankTradeData   │    │ CounterpartyTradeData           ││ │
│  │  │ Table           │    │ Table                           ││ │
│  │  └─────────────────┘    └─────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow**:
1. **Document Upload**: Trade PDFs uploaded to S3 bucket with source classification (BANK/COUNTERPARTY)
2. **Event Trigger**: S3 event triggers Lambda function for processing initiation
3. **EKS Processing**: Lambda calls EKS API to start multi-agent workflow
4. **AI Processing**: CrewAI agents process documents using Bedrock Claude Sonnet
5. **Data Storage**: Structured trade data stored in appropriate DynamoDB tables
6. **Matching Analysis**: Intelligent matching between bank and counterparty trades
7. **Results**: Matching reports generated and stored in S3

## Project Components

### Core Application (`src/latest_trade_matching_agent/`)

**Multi-Agent System** (`crew_fixed.py`):
- **Document Processor**: Converts PDFs to high-resolution images for OCR
- **Trade Entity Extractor**: Uses Bedrock Claude for intelligent text extraction
- **Reporting Analyst**: Stores structured data in correct DynamoDB tables
- **Matching Analyst**: Performs sophisticated trade matching with tolerance handling

**Agent Configuration** (`config/`):
- `agents.yaml`: Defines agent roles, goals, and expertise
- `tasks.yaml`: Specifies workflow tasks and expected outputs

**Custom Tools** (`tools/`):
- `pdf_to_image.py`: High-quality PDF conversion with S3 integration
- `custom_tool.py`: Specialized tools for trade processing

### Infrastructure (`terraform/`)

**Core Infrastructure**:
- `eks.tf`: EKS cluster with VPC, node groups, and add-ons
- `dynamodb.tf`: Trade data tables with GSI for efficient querying
- `s3.tf`: Document storage buckets with lifecycle policies
- `lambda.tf`: S3 event processing functions

**Security & Networking**:
- IRSA configuration for secure AWS service access
- VPC with private/public subnets
- Security groups with least-privilege access

### Kubernetes Deployment (`k8s/`)

**Application Deployment**:
- `deployment.yaml`: Multi-replica deployment with resource limits
- `service.yaml`: Internal service for pod communication
- `hpa.yaml`: Horizontal Pod Autoscaler for dynamic scaling
- `service-account.yaml`: IRSA-enabled service account

### Serverless Components (`lambda/`)

**Event Processing**:
- `s3_event_processor.py`: Handles S3 events and triggers EKS processing
- Automatic source type detection (BANK/COUNTERPARTY)
- Error handling and dead letter queue integration

### Monitoring (`monitoring/`)

**Observability Stack**:
- Prometheus metrics collection
- Grafana dashboards for visualization
- Health check endpoints and automated monitoring

## Next Steps

### Potential Enhancements

**Advanced Features**:
- **Multi-Asset Class Support**: Extend beyond derivatives to equities, bonds, FX
- **Real-Time Streaming**: Implement Kinesis for real-time trade processing
- **Machine Learning**: Add ML models for anomaly detection and pattern recognition
- **Regulatory Reporting**: Automated compliance reporting and audit trails

**Performance Optimizations**:
- **Caching Layer**: Redis for frequently accessed trade data
- **Batch Processing**: Optimize for high-volume trade processing
- **Multi-Region**: Deploy across multiple AWS regions for global coverage

**Integration Enhancements**:
- **API Gateway**: Add rate limiting and authentication
- **Message Queues**: SQS/SNS for reliable message processing
- **Data Lake**: S3 + Athena for historical trade analysis

### Contributing

1. **Fork the Repository**: Create your own fork for development
2. **Feature Branches**: Use descriptive branch names (`feature/enhanced-matching`)
3. **Testing**: Add comprehensive tests for new functionality
4. **Documentation**: Update relevant documentation
5. **Pull Requests**: Submit PRs with detailed descriptions

**Development Workflow**:
```bash
# Set up development environment
git clone https://github.com/yourusername/ai-trade-matching-system.git
cd ai-trade-matching-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/

# Local development
python src/latest_trade_matching_agent/main.py
```

## Clean Up

### Resource Cleanup Commands

**Kubernetes Resources**:
```bash
# Remove application
kubectl delete -f k8s/

# Delete namespace
kubectl delete namespace trade-matching
```

**AWS Infrastructure**:
```bash
# Terraform cleanup
cd terraform/
terraform destroy -auto-approve

# Manual cleanup (if needed)
aws eks delete-cluster --name trade-matching-cluster
aws dynamodb delete-table --table-name BankTradeData
aws dynamodb delete-table --table-name CounterpartyTradeData
aws s3 rb s3://your-trade-documents-bucket --force
```

**Container Images**:
```bash
# Remove ECR repository
aws ecr delete-repository --repository-name trade-matching-system --force
```

**Cost Estimation**: Typical monthly costs range from $200-500 depending on processing volume and EKS node configuration.

## Troubleshooting

### Common Issues

**PDF Processing Errors**:
```bash
# Error: Poppler not found
# Solution: Install poppler-utils
brew install poppler  # macOS
apt-get install poppler-utils  # Ubuntu

# Error: Permission denied on /tmp/processing
# Solution: Check container security context and volume mounts
kubectl describe pod <pod-name> -n trade-matching
```

**AWS Authentication Issues**:
```bash
# Error: Unable to locate credentials
# Solution: Configure AWS credentials
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

**EKS Deployment Issues**:
```bash
# Error: ImagePullBackOff
# Solution: Check ECR permissions and image URI
kubectl describe pod <pod-name> -n trade-matching

# Error: CrashLoopBackOff
# Solution: Check application logs
kubectl logs <pod-name> -n trade-matching --previous
```

**DynamoDB Connection Issues**:
```bash
# Error: MCP server connection failed
# Solution: Verify IRSA configuration and DynamoDB permissions
kubectl get serviceaccount trade-matching-sa -n trade-matching -o yaml

# Check IAM role annotations
kubectl describe serviceaccount trade-matching-sa -n trade-matching
```

**Performance Issues**:
```bash
# High memory usage
# Solution: Adjust resource limits in deployment.yaml
kubectl top pods -n trade-matching

# Slow processing
# Solution: Scale up replicas or increase CPU limits
kubectl scale deployment trade-matching-system --replicas=5 -n trade-matching
```

### Debug Commands

```bash
# Check pod status
kubectl get pods -n trade-matching -o wide

# View application logs
kubectl logs -f deployment/trade-matching-system -n trade-matching

# Execute into pod for debugging
kubectl exec -it <pod-name> -n trade-matching -- /bin/bash

# Check resource usage
kubectl top nodes
kubectl top pods -n trade-matching

# View HPA status
kubectl get hpa -n trade-matching
kubectl describe hpa trade-matching-hpa -n trade-matching
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

For questions or support, please open an issue on GitHub or contact the development team.