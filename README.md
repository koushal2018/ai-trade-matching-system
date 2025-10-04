# AI Trade Matching System

> **Enterprise-grade trade confirmation matching powered by CrewAI on AWS**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-0.80+-green.svg)
![AWS](https://img.shields.io/badge/AWS-Bedrock%20Claude-orange.svg)
![DynamoDB](https://img.shields.io/badge/DynamoDB-MCP-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview

The AI Trade Matching System is an intelligent, cloud-native solution that automates the processing and matching of derivative trade confirmations using advanced AI capabilities. Built on AWS native services with a multi-agent architecture powered by CrewAI, the system leverages AWS Bedrock Claude Sonnet for document analysis and implements sophisticated trade matching algorithms for financial operations teams.

**Key Problem Solved**: Manual trade confirmation matching is time-consuming, error-prone, and doesn't scale with trading volumes. This system automates the entire process from PDF ingestion to intelligent matching, reducing settlement risk and operational overhead.

**Technology Stack**:
- **AI/ML**: AWS Bedrock Claude Sonnet 4, CrewAI multi-agent framework
- **Infrastructure**: AWS Lambda, DynamoDB, S3, Step Functions
- **Backend**: FastAPI, Python 3.11+
- **Integration**: Model Context Protocol (MCP) for DynamoDB
- **Infrastructure as Code**: Terraform
- **Monitoring**: CloudWatch, CloudWatch Logs

## Features

- **🤖 AI-Powered Document Processing**: AWS Bedrock Claude Sonnet 4 with multimodal capabilities for accurate PDF text extraction
- **📄 Advanced PDF Pipeline**: High-quality PDF-to-image conversion (300 DPI) optimized for OCR processing
- **🎯 Multi-Agent Architecture**: 4 specialized agents handling document processing, OCR extraction, data analysis, and matching
- **☁️ Cloud-Native Deployment**: Serverless AWS architecture with Lambda functions and Step Functions orchestration
- **🗄️ Intelligent Data Storage**: DynamoDB integration via MCP with separate tables for bank and counterparty trades
- **🔍 Professional Trade Matching**: Sophisticated matching logic with tolerance handling and break analysis
- **📊 Event-Driven Processing**: S3 triggers, Lambda functions, and Step Functions workflows
- **🔐 Security-First Design**: IAM roles with least-privilege access
- **📈 Production Monitoring**: CloudWatch metrics, logs, and alarms
- **⚡ Auto-Scaling**: Lambda concurrency and DynamoDB auto-scaling based on workload

## Prerequisites

### Required AWS Setup

**AWS Account Requirements**:
- AWS CLI configured with appropriate permissions
- Access to AWS Bedrock (Claude Sonnet model)
- DynamoDB, S3, Lambda, and IAM permissions
- Step Functions access

**AWS Services Used**:
```bash
# Core services
- AWS Bedrock (Claude Sonnet AI model)
- Amazon DynamoDB (trade data storage)
- Amazon S3 (document storage)
- AWS Lambda (serverless compute)
- AWS Step Functions (workflow orchestration)
- Amazon SNS (notifications)

# Supporting services
- IAM (security and permissions)
- CloudWatch (logging and monitoring)
```

### Development Environment

**Required Tools**:
```bash
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
│  │   S3    │───▶│  Lambda  │───▶│     Step Functions          │ │
│  │ Bucket  │    │ Trigger  │    │  ┌─────────────────────────┐ │ │
│  └─────────┘    └──────────┘    │  │   Processing Workflow   │ │ │
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
3. **Workflow Orchestration**: Step Functions orchestrates multi-agent workflow
4. **AI Processing**: CrewAI agents process documents using Bedrock Claude Sonnet via Lambda
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
- `dynamodb.tf`: Trade data tables with GSI for efficient querying
- `s3.tf`: Document storage buckets with lifecycle policies
- `lambda.tf`: Lambda functions for document processing
- `step_functions.tf`: Workflow orchestration state machines
- `iam.tf`: IAM roles and policies with least-privilege access

### Serverless Components (`lambda/`)

**Event Processing**:
- `s3_event_processor.py`: Handles S3 events and triggers workflow processing
- Automatic source type detection (BANK/COUNTERPARTY)
- Error handling and dead letter queue integration

### Monitoring (`monitoring/`)

**Observability Stack**:
- CloudWatch metrics and alarms
- CloudWatch Logs for centralized logging
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

**AWS Infrastructure**:
```bash
# Terraform cleanup
cd terraform/
terraform destroy -auto-approve

# Manual cleanup (if needed)
aws dynamodb delete-table --table-name BankTradeData
aws dynamodb delete-table --table-name CounterpartyTradeData
aws s3 rb s3://your-trade-documents-bucket --force
aws logs delete-log-group --log-group-name /aws/lambda/trade-matching
```

**Cost Estimation**: Typical monthly costs range from $50-150 depending on processing volume and Lambda invocations.

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

**Lambda Execution Issues**:
```bash
# Error: Lambda timeout
# Solution: Increase timeout in lambda configuration
aws lambda update-function-configuration \
  --function-name trade-matching-processor \
  --timeout 900

# Error: Out of memory
# Solution: Increase memory allocation
aws lambda update-function-configuration \
  --function-name trade-matching-processor \
  --memory-size 3008
```

**DynamoDB Connection Issues**:
```bash
# Error: MCP server connection failed
# Solution: Verify IAM role and DynamoDB permissions
aws iam get-role --role-name lambda-trade-matching-role

# Check Lambda execution role
aws lambda get-function-configuration \
  --function-name trade-matching-processor
```

**Performance Issues**:
```bash
# Slow processing
# Solution: Increase Lambda concurrency
aws lambda put-function-concurrency \
  --function-name trade-matching-processor \
  --reserved-concurrent-executions 10

# Check Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=trade-matching-processor \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

### Debug Commands

```bash
# Check Lambda function status
aws lambda get-function --function-name trade-matching-processor

# View Lambda logs
aws logs tail /aws/lambda/trade-matching-processor --follow

# Check recent invocations
aws lambda get-function-event-invoke-config \
  --function-name trade-matching-processor

# View Step Functions execution
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:region:account:stateMachine:trade-matching

# Check DynamoDB table status
aws dynamodb describe-table --table-name BankTradeData
aws dynamodb describe-table --table-name CounterpartyTradeData
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