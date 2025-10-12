# AI Trade Matching System - Documentation

This directory contains comprehensive documentation for the AI Trade Matching System.

## 📚 Documentation Index

### 1. **Getting Started**
- [Main README](../README.md) - Complete overview, installation, and quick start guide
- [.env.example](../.env.example) - Environment configuration template

### 2. **Architecture Documentation**
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Detailed system architecture with ASCII diagrams
- [AWS Services Diagram](./aws-services-diagram.md) - Complete AWS infrastructure with Mermaid diagrams
- [Architecture Mermaid File](../aws-architecture.mmd) - High-level architecture diagram source
- [Simplified Architecture](./architecture-simplified.mmd) - Process flow diagram

### 3. **Development Guidelines**
- [CLAUDE.md](../CLAUDE.md) - Development instructions for Claude Code
- Project guidelines, coding standards, and AI agent best practices

### 4. **Code Documentation**
- [crew_fixed.py](../src/latest_trade_matching_agent/crew_fixed.py) - Main crew implementation
- [agents.yaml](../src/latest_trade_matching_agent/config/agents.yaml) - Agent configurations
- [tasks.yaml](../src/latest_trade_matching_agent/config/tasks.yaml) - Task definitions

## 🏗️ System Architecture Overview

The system consists of 5 main components:

### 1. Input Layer
- **Amazon S3** bucket (`otc-menat-2025`) for PDF storage
- Folders: BANK/, COUNTERPARTY/, PDFIMAGES/, extracted/, reports/

### 2. Processing Layer
Five specialized CrewAI agents:
1. **Document Processor** - PDF to Image conversion (300 DPI)
2. **OCR Processor** - Text extraction from images
3. **Trade Entity Extractor** - JSON parsing and structuring
4. **Reporting Analyst** - DynamoDB data storage
5. **Matching Analyst** - Trade matching and reconciliation

### 3. AI Engine
- **AWS Bedrock** Claude Sonnet 4 (APAC region)
- Model: `apac.anthropic.claude-sonnet-4-20250514-v1:0`
- Used for: OCR, entity extraction, document analysis

### 4. Data Layer
- **Amazon DynamoDB** with two tables:
  - `BankTradeData` - Bank trade confirmations
  - `CounterpartyTradeData` - Counterparty confirmations
- Primary Key: `Trade_ID` (String)
- Billing: PAY_PER_REQUEST

### 5. Integration Layer
- **AWS API MCP Server** - AWS operations via Model Context Protocol
- **Custom boto3 Tool** - Direct DynamoDB access
- Dual approach for maximum reliability

## 📊 Diagrams

### High-Level Architecture
See the main [README.md](../README.md#architecture) for the Mermaid diagram showing:
- All 5 agents
- AWS services integration
- Data flow between components

### Detailed Architecture
See [ARCHITECTURE.md](../ARCHITECTURE.md) for:
- Layer-by-layer breakdown
- Component specifications
- Performance metrics
- File locations

### AWS Services Architecture
See [aws-services-diagram.md](./aws-services-diagram.md) for:
- Complete AWS infrastructure
- Service configurations
- Cost estimation
- Security best practices
- Sequence diagram

## 🔧 Key Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Runtime environment |
| CrewAI | 0.175+ | Multi-agent orchestration |
| AWS Bedrock | Claude Sonnet 4 | AI/ML processing |
| Amazon DynamoDB | - | Data persistence |
| Amazon S3 | - | Document storage |
| boto3 | 1.34+ | AWS SDK for Python |
| MCP | latest | Model Context Protocol |
| pdf2image | 1.17+ | PDF conversion |
| poppler-utils | - | PDF processing (system) |

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| Processing Time per Trade | 60-90 seconds |
| Token Usage per Trade | ~120K tokens |
| Token Reduction | 85% (via optimization) |
| Agents | 5 specialized agents |
| Max Iterations per Agent | 5-10 (optimized) |
| AWS Bedrock Rate Limit | 2 RPM |

## 🔐 Security Considerations

### Authentication
- AWS credentials via environment variables
- IAM roles preferred over access keys
- No hardcoded credentials

### Authorization
- Least-privilege IAM policies
- Service-specific permissions
- No wildcard access

### Encryption
- S3: Server-side encryption (SSE-S3)
- DynamoDB: Encryption at rest
- TLS 1.2+ for all AWS API calls

### Audit & Compliance
- CloudTrail for audit logging (optional)
- CloudWatch for monitoring (optional)
- Structured logging throughout

## 💡 Key Design Decisions

### 1. Multi-Agent Architecture
- **Why**: Separation of concerns, easier to maintain and extend
- **How**: 5 specialized agents with distinct responsibilities
- **Benefit**: Each agent can be optimized independently

### 2. Scratchpad Pattern (85% Token Reduction)
- **Why**: Reduce token usage and costs
- **How**: Agents save data to S3, pass only S3 paths between tasks
- **Benefit**: Massive token savings while maintaining full context

### 3. Dual DynamoDB Integration
- **Why**: Maximum reliability and flexibility
- **How**: Custom boto3 tool + AWS API MCP Server
- **Benefit**: Fallback options, no single point of failure

### 4. Claude Sonnet 4 (Not Nova Pro)
- **Why**: Nova Pro outputs "zeros" for complex multi-step tasks
- **How**: Switched to Claude Sonnet 4 APAC region
- **Benefit**: Reliable, accurate processing

### 5. Sequential Processing
- **Why**: Each step depends on previous output
- **How**: Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5
- **Benefit**: Clear data flow, easier debugging

## 🚀 Getting Started

1. **Installation**
   ```bash
   git clone https://github.com/yourusername/ai-trade-matching-system.git
   cd ai-trade-matching-system
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

3. **Run**
   ```bash
   crewai run
   ```

See [README.md](../README.md#quick-start) for detailed instructions.

## 📝 Additional Resources

- [CrewAI Documentation](https://docs.crewai.com/) - Official CrewAI docs
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/) - AWS Bedrock reference
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/) - DynamoDB guide
- [Model Context Protocol](https://github.com/awslabs/mcp) - MCP specification

## 🤝 Contributing

See the main [README.md](../README.md#contributing) for contribution guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Last Updated**: October 2025
**Documentation Version**: 1.0
**System Version**: 1.0
