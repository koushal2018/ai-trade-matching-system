# Backend Architecture

## Overview

The AI Trade Matching System backend is built on a modern, cloud-native architecture that combines multi-agent AI processing with enterprise-grade AWS services. The system is designed for high availability, scalability, and fault tolerance while maintaining strict security and compliance standards required for financial operations.

**Architecture Principles**:
- **Event-Driven**: Asynchronous processing triggered by S3 events
- **Microservices**: Containerized services deployed on Kubernetes
- **AI-First**: Multi-agent system powered by AWS Bedrock Claude Sonnet
- **Cloud-Native**: Fully managed AWS services with Infrastructure as Code

## Project Structure

```
src/latest_trade_matching_agent/
├── crew_fixed.py              # Main orchestration and agent definitions
├── main.py                    # Entry point and MCP integration
├── config/
│   ├── agents.yaml           # Agent roles and capabilities
│   └── tasks.yaml            # Workflow task definitions
└── tools/
    ├── pdf_to_image.py       # PDF conversion with S3 integration
    └── custom_tool.py        # Specialized trade processing tools

terraform/
├── eks.tf                    # EKS cluster and VPC configuration
├── dynamodb.tf              # Database tables and indexes
├── s3.tf                    # Storage buckets and policies
├── lambda.tf                # Serverless event processing
└── iam.tf                   # Security roles and policies

k8s/
├── deployment.yaml          # Application deployment configuration
├── service.yaml             # Internal service definitions
├── hpa.yaml                 # Auto-scaling configuration
└── service-account.yaml     # IRSA security configuration

lambda/
└── s3_event_processor.py    # S3 event handling and EKS integration
```

### Core Components

**Multi-Agent System** (`crew_fixed.py`):
```python
class LatestTradeMatchingAgent:
    """Enhanced multi-agent crew for trade processing"""
    
    def __init__(self, dynamodb_tools=None, request_context=None):
        self.dynamodb_tools = dynamodb_tools or []
        self.request_context = request_context or {}
        
    @agent
    def document_processor(self) -> Agent:
        """Converts PDFs to high-quality images"""
        
    @agent  
    def trade_entity_extractor(self) -> Agent:
        """Extracts trade data using Bedrock Claude"""
        
    @agent
    def reporting_analyst(self) -> Agent:
        """Stores data in correct DynamoDB tables"""
        
    @agent
    def matching_analyst(self) -> Agent:
        """Performs intelligent trade matching"""
```

**Configuration Management**:
- Environment-based configuration with dynamic overrides
- Request context injection for dynamic parameters
- Configurable rate limits and execution timeouts

## Data Flow

### End-to-End Processing Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐
│   S3 Event  │───▶│   Lambda    │───▶│        EKS Cluster          │
│  (PDF Upload)│    │  Processor  │    │                             │
└─────────────┘    └─────────────┘    │  ┌─────────────────────────┐│
                                      │  │    CrewAI Workflow      ││
                                      │  │                         ││
                                      │  │  1. Document Processor  ││
                                      │  │  2. OCR Extractor      ││
                                      │  │  3. Data Analyst       ││
                                      │  │  4. Matching Analyst   ││
                                      │  └─────────────────────────┘│
                                      └─────────────────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Storage                             │
│  ┌─────────────────┐              ┌─────────────────────────────┐│
│  │ BankTradeData   │              │ CounterpartyTradeData       ││
│  │ - Trade_ID (PK) │              │ - Trade_ID (PK)             ││
│  │ - Trade_Date    │              │ - Trade_Date                ││
│  │ - Counterparty  │              │ - Bank                      ││
│  │ - Notional      │              │ - Notional                  ││
│  │ - Product_Type  │              │ - Product_Type              ││
│  └─────────────────┘              └─────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Processing Steps

**1. Document Ingestion**:
```python
# S3 event structure
{
    "s3_bucket": "trade-documents",
    "s3_key": "BANK/GCS382857_V1.pdf",
    "source_type": "BANK",  # Auto-detected from path
    "unique_identifier": "GCS382857"
}
```

**2. PDF Processing**:
- High-resolution conversion (300 DPI) for optimal OCR
- Multi-page handling with sequential processing
- S3 storage for processed images
- Local caching for agent access

**3. AI-Powered Extraction**:
```python
# Bedrock Claude integration
llm = LLM(model="bedrock/global.anthropic.claude-sonnet-4-20250514-v1:0")

# OCR processing with context awareness
ocr_tool = OCRTool(llm)
extracted_data = ocr_tool.run(image_path)
```

**4. Data Classification and Storage**:
- Source type validation (BANK vs COUNTERPARTY)
- Table routing based on trade source
- Idempotent operations to prevent duplicates
- Audit trail maintenance

**5. Intelligent Matching**:
- Cross-table matching between bank and counterparty trades
- Tolerance-based field comparison
- Professional matching standards
- Break analysis and reporting

### Error Handling and Resilience

**Retry Mechanisms**:
- Exponential backoff for transient failures
- Dead letter queues for failed processing
- Circuit breaker patterns for external services

**Data Integrity**:
- Transaction-like operations across services
- Validation at each processing stage
- Comprehensive logging and audit trails

## Core Components

### Multi-Agent Architecture

**Agent Specialization**:

1. **Document Processing Specialist**:
   - **Role**: PDF conversion and image preparation
   - **Tools**: PDFToImageTool, S3WriterTool
   - **Expertise**: 10+ years in document processing
   - **Output**: High-quality images ready for OCR

2. **Senior Trade Document Analyst**:
   - **Role**: AI-powered text extraction and analysis
   - **Tools**: OCRTool (Bedrock Claude), FileReadTool
   - **Expertise**: 15+ years in trade document analysis
   - **Critical Skill**: Source type identification (BANK/COUNTERPARTY)

3. **DynamoDB Trade Data Manager**:
   - **Role**: Data storage and table routing
   - **Tools**: DynamoDB MCP tools, FileWriterTool
   - **Expertise**: 12+ years in database operations
   - **Critical Function**: Correct table selection based on source

4. **Trade Data Matching Manager**:
   - **Role**: Intelligent trade matching and analysis
   - **Tools**: DynamoDB MCP tools, matching algorithms
   - **Expertise**: 20+ years in trade confirmation matching
   - **Output**: Comprehensive matching reports

### Database Schema

**BankTradeData Table**:
```json
{
    "Trade_ID": "GCS382857",           // Primary Key
    "Trade_Date": "2024-01-15",
    "Counterparty": "MERRILL LYNCH INTERNATIONAL",
    "Product_Type": "Interest Rate Swap",
    "Notional_Amount": 10000000,
    "Currency": "USD",
    "Maturity_Date": "2029-01-15",
    "Fixed_Rate": 3.75,
    "TRADE_SOURCE": "BANK",           // Audit field
    "Processing_Timestamp": "2024-01-15T10:30:00Z",
    "S3_Source_Key": "BANK/GCS382857_V1.pdf"
}
```

**CounterpartyTradeData Table**:
```json
{
    "Trade_ID": "ML-REF-789456",      // Primary Key
    "Trade_Date": "2024-01-15", 
    "Bank": "FIRST ABU DHABI BANK",
    "Product_Type": "Interest Rate Swap",
    "Notional_Amount": 10000000,
    "Currency": "USD",
    "Maturity_Date": "2029-01-15",
    "Fixed_Rate": 3.75,
    "TRADE_SOURCE": "COUNTERPARTY",   // Audit field
    "Processing_Timestamp": "2024-01-15T10:35:00Z",
    "S3_Source_Key": "COUNTERPARTY/ML-REF-789456.pdf"
}
```

**Global Secondary Indexes**:
- **TradeDateIndex**: Efficient querying by trade date
- **CounterpartyIndex**: Fast counterparty-based lookups
- **BankIndex**: Quick bank-based searches

### Integration Layer

**Model Context Protocol (MCP)**:
```python
# DynamoDB MCP integration
dynamodb_params = StdioServerParameters(
    command="uvx",
    args=["awslabs.dynamodb-mcp-server@latest"],
    env={
        "DDB-MCP-READONLY": "false",
        "AWS_PROFILE": "default", 
        "AWS_REGION": "us-east-1"
    }
)

with MCPServerAdapter(dynamodb_params) as dynamodb_tools:
    crew_instance = LatestTradeMatchingAgent(dynamodb_tools=list(dynamodb_tools))
```

**AWS Service Integration**:
- **Bedrock**: AI model access via LiteLLM
- **S3**: Document storage and retrieval
- **DynamoDB**: Structured data persistence
- **Lambda**: Event-driven processing
- **SNS**: Notification and alerting

### Security Architecture

**IRSA (IAM Roles for Service Accounts)**:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: trade-matching-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/trade-matching-irsa-role
```

**Least Privilege Access**:
- Service-specific IAM roles
- Resource-level permissions
- Network security groups
- Container security contexts

**Data Protection**:
- Encryption at rest (DynamoDB, S3)
- Encryption in transit (TLS)
- Secure credential management
- Audit logging

### Performance Optimization

**Scaling Strategies**:
- Horizontal Pod Autoscaler (HPA) for dynamic scaling
- Resource requests and limits for optimal scheduling
- Node affinity for performance-critical workloads

**Caching and Optimization**:
- Local file caching for agent processing
- DynamoDB query optimization with GSI
- S3 transfer acceleration for large files

**Monitoring and Observability**:
- Prometheus metrics collection
- Custom application metrics
- Health check endpoints
- Distributed tracing capabilities

This backend architecture provides a robust, scalable foundation for enterprise-grade trade matching operations while maintaining the flexibility to adapt to changing business requirements.