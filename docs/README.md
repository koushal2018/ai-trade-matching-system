# AI Trade Matching System - Documentation

This directory contains comprehensive documentation for the AI Trade Matching System, a multi-agent trade processing platform built on AWS Bedrock AgentCore.

## 🏗️ Architecture Overview

The system implements a **multi-agent architecture** using AWS Bedrock AgentCore Runtime with specialized agents for different aspects of trade processing:

- **PDF Adapter Agent** - Document processing and text extraction
- **Trade Extraction Agent** - Structured data extraction from trade confirmations  
- **Trade Matching Agent** - Fuzzy matching and reconciliation logic
- **Exception Management Agent** - Exception triage and SLA tracking
- **Orchestrator Agent** - Workflow coordination and handoff management

### Architecture Diagrams

#### `architecture-simplified.mmd`
Mermaid diagram source file showing the simplified system architecture and data flow.

**To render this diagram:**
1. Copy the content to [Mermaid Live Editor](https://mermaid.live/)
2. Or use any Mermaid-compatible renderer
3. Or view it in GitHub (supports Mermaid rendering)

## 📚 Documentation Structure

### Core Documentation

Located in the root directory:

- **[README.md](../README.md)** - Complete project overview, installation, and usage
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - Detailed system architecture and design decisions
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines and development workflow
- **[SECURITY.md](../SECURITY.md)** - Security policy, vulnerability reporting, and best practices
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history, release notes, and migration guides

### Agent Development & Deployment

Following AWS Bedrock AgentCore best practices:

#### Agent-Specific Documentation
- **[deployment/README.md](../deployment/README.md)** - Multi-agent deployment guide
- **[deployment/SETUP_GUIDE.md](../deployment/SETUP_GUIDE.md)** - Step-by-step AgentCore setup
- **[deployment/QUICK_START.md](../deployment/QUICK_START.md)** - Fast deployment for development
- **[deployment/AGENTCORE_BEST_PRACTICES.md](../deployment/AGENTCORE_BEST_PRACTICES.md)** - AgentCore optimization patterns

#### Individual Agent Documentation
- **[deployment/pdf_adapter/](../deployment/pdf_adapter/)** - PDF processing agent implementation
- **[deployment/trade_extraction/](../deployment/trade_extraction/)** - Data extraction agent with Strands SDK
- **[deployment/trade_matching/](../deployment/trade_matching/)** - Matching algorithm and fuzzy logic
- **[deployment/exception_management/](../deployment/exception_management/)** - Exception handling and SLA management
- **[deployment/orchestrator/](../deployment/orchestrator/)** - Agent coordination and workflow management

### Infrastructure & Operations

#### Infrastructure as Code
- **[terraform/README.md](../terraform/README.md)** - Infrastructure deployment with Terraform
- **[terraform/agentcore/README.md](../terraform/agentcore/README.md)** - AgentCore-specific infrastructure
- **[terraform/agentcore/QUICK_START.md](../terraform/agentcore/QUICK_START.md)** - Fast infrastructure setup
- **[terraform/agentcore/COST_SUMMARY.md](../terraform/agentcore/COST_SUMMARY.md)** - Cost optimization guide

#### Web Portal & API
- **[web-portal-api/README.md](../web-portal-api/README.md)** - FastAPI backend documentation
- **[web-portal/README.md](../web-portal/README.md)** - React frontend development guide

## 🚀 Quick Start Guides

### For Developers
1. **[Agent Development](../deployment/AGENTCORE_BEST_PRACTICES.md)** - Best practices for building agents
2. **[Local Testing](../deployment/QUICK_START.md)** - Test agents locally before deployment
3. **[Strands SDK Integration](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/index.md)** - Framework integration patterns

### For Operations
1. **[Infrastructure Setup](../terraform/agentcore/QUICK_START.md)** - Deploy infrastructure
2. **[Agent Deployment](../deployment/SETUP_GUIDE.md)** - Deploy agents to AgentCore Runtime
3. **[Monitoring Setup](../deployment/AGENTCORE_BEST_PRACTICES.md#monitoring)** - Observability and alerting

### For Contributors
1. **[Contributing Guide](../CONTRIBUTING.md)** - Development workflow and standards
2. **[Security Guidelines](../SECURITY.md)** - Security requirements and best practices
3. **[Testing Guide](../HOW_TO_RUN_TESTS.md)** - Test execution and coverage

## 🔧 Agent Development Patterns

This system follows **AWS Bedrock AgentCore best practices** for multi-agent systems:

### Agent Communication Patterns
- **Agent-to-Agent (A2A)** communication using `bedrock-agentcore:InvokeAgentRuntime`
- **Orchestrator Pattern** for workflow coordination
- **Specialist Pattern** for domain-specific processing
- **Pipeline Pattern** for sequential processing stages

### Code Patterns
```python
# AgentCore Runtime Integration
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()

@app.entrypoint
def handler(event):
    agent = Agent(tools=[...])
    return agent(event["prompt"])

if __name__ == "__main__":
    app.run()
```

### Deployment Patterns
- **Individual Agent Deployment** - Each agent as separate runtime
- **Multi-Agent Coordination** - Orchestrator manages handoffs
- **Resource Isolation** - Separate IAM roles and permissions
- **Scalable Architecture** - Auto-scaling based on demand

## 📖 External Resources

### AWS Bedrock AgentCore
- **[AgentCore Documentation](https://aws.github.io/bedrock-agentcore-starter-toolkit/)** - Official AgentCore guide
- **[Runtime Deployment](https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/runtime/quickstart.html)** - Agent deployment patterns
- **[Multi-Agent Examples](https://aws.github.io/bedrock-agentcore-starter-toolkit/examples/infrastructure-as-code/cloudformation/multi-agent-runtime/)** - Reference architectures

### Strands SDK
- **[Strands Documentation](https://strandsagents.com)** - Agent framework documentation
- **[Amazon Bedrock Integration](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/amazon-bedrock/index.md)** - Bedrock model integration
- **[AgentCore Deployment](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/index.md)** - Deployment to AgentCore

### AWS Services
- **[Amazon Bedrock](https://docs.aws.amazon.com/bedrock/)** - Foundation model service
- **[Amazon DynamoDB](https://docs.aws.amazon.com/dynamodb/)** - NoSQL database service
- **[Amazon S3](https://docs.aws.amazon.com/s3/)** - Object storage service
- **[AWS CloudWatch](https://docs.aws.amazon.com/cloudwatch/)** - Monitoring and observability

### Frontend Development
- **[React Documentation](https://react.dev/)** - Frontend framework
- **[Material-UI](https://mui.com/)** - React component library
- **[TypeScript](https://www.typescriptlang.org/)** - Type-safe JavaScript

## 🎯 Use Case Specific Guides

### Trade Processing Workflow
1. **[PDF Processing](../deployment/pdf_adapter/)** - Document ingestion and text extraction
2. **[Data Extraction](../deployment/trade_extraction/)** - Structured field extraction
3. **[Trade Matching](../deployment/trade_matching/)** - Cross-system reconciliation
4. **[Exception Handling](../deployment/exception_management/)** - Break management and SLA tracking

### Financial Services Compliance
- **[Security Implementation](../SECURITY.md)** - Financial data protection
- **[Audit Trail](../web-portal-api/README.md#audit-endpoints)** - Compliance tracking
- **[Data Retention](../terraform/agentcore/README.md#data-lifecycle)** - Regulatory compliance

### Performance Optimization
- **[Agent Tuning](../deployment/AGENTCORE_BEST_PRACTICES.md#performance)** - Latency and throughput optimization
- **[Cost Management](../terraform/agentcore/COST_SUMMARY.md)** - Resource cost optimization
- **[Monitoring](../deployment/AGENTCORE_BEST_PRACTICES.md#observability)** - Performance tracking

## 🤝 Community & Support

- **[GitHub Issues](https://github.com/your-org/ai-trade-matching-system/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/your-org/ai-trade-matching-system/discussions)** - Community discussions
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute to the project

---

**Note**: This system is built following AWS Bedrock AgentCore best practices for production-ready multi-agent systems. For the latest AgentCore patterns and updates, refer to the [official AgentCore documentation](https://aws.github.io/bedrock-agentcore-starter-toolkit/).