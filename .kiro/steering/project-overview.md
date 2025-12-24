---
inclusion: always
---

# AI Trade Matching System - Project Overview

## System Purpose
AI-powered trade reconciliation platform that automates matching of OTC derivative trade confirmations between financial institutions and counterparties using multi-agent architecture on AWS Bedrock AgentCore.

## Architecture Stack
- **Runtime**: Amazon Bedrock AgentCore (serverless, event-driven)
- **Agent Framework**: Strands SDK with built-in tools:
  - `use_aws` tool for direct AWS service integration (DynamoDB, S3, Bedrock)
  - Community tools from `strands_tools` package
  - Custom tool implementations when needed
- **AI Models**: Amazon Nova Pro v1 (primary model for all agents)
- **Model Temperature**: 0 (deterministic outputs for financial accuracy)
- **Region**: us-east-1
- **Deployment**: Each agent deployed independently via `agentcore.yaml` configuration

## Agent Architecture (5 Specialized Agents)

### 1. PDF Adapter Agent
- **Purpose**: Extracts text from trade confirmation PDFs using Bedrock multimodal capabilities (not traditional OCR)
- **Location**: `deployment/pdf_adapter/`
- **Implementation**: `pdf_adapter_agent_strands.py`
- **Key Features**:
  - Uses Bedrock's multimodal LLM for text extraction from PDF images
  - Converts PDFs to base64 images for processing
  - Produces canonical adapter output with extracted text
- **Input**: S3 PDF objects (BANK/ or COUNTERPARTY/)
- **Output**: Extracted text to S3 (extracted/ folder)
- **Tools**: `extract_text_from_pdf_s3`, `use_aws` for S3 operations
- **Memory**: Shared memory ID `trade_matching_decisions-Z3tG4b4Xsd`

### 2. Trade Extraction Agent
- **Purpose**: Extracts structured trade data using LLM-based parsing
- **Location**: `deployment/trade_extraction/`
- **Implementation**: `agent.py` (LLM-centric design)
- **Key Features**:
  - LLM-driven decision making with minimal hardcoded logic
  - Autonomous tool selection based on context
  - CanonicalTradeData model for data validation
  - Source classification (BANK vs COUNTERPARTY)
- **Input**: Extracted text from PDF Adapter (S3)
- **Output**: Structured JSON to DynamoDB (BankTradeData/CounterpartyTradeData)
- **Tools**: `use_aws` for S3/DynamoDB operations
- **Memory**: Shared memory ID `trade_matching_decisions-Z3tG4b4Xsd`
- **Model Override**: All agents use Amazon Nova Pro v1 (some legacy configs may reference Claude)

### 3. Trade Matching Agent
- **Purpose**: AI-driven fuzzy matching with confidence scoring
- **Location**: `deployment/trade_matching/`
- **Implementation**: `trade_matching_agent_strands.py`
- **Key Features**:
  - Intelligent trade ID normalization (bank_ and cpty_ prefixes)
  - Multi-level confidence scoring with detailed reasoning
  - AgentCore Memory session management for pattern learning
  - Retrieval configurations for facts, preferences, and summaries
- **Input**: Trade records from DynamoDB tables
- **Output**: Match results with classification and confidence scores
- **Classifications**:
  - MATCHED (≥85%): Auto-approve
  - PROBABLE_MATCH (70-84%): HITL verification
  - REVIEW_REQUIRED (50-69%): Exception queue
  - BREAK (<50%): Likely mismatch
- **Tools**: `use_aws` for DynamoDB operations
- **Memory**: Advanced session management with namespace strategies

### 4. Exception Management Agent
- **Purpose**: Intelligent exception triage and routing
- **Location**: `deployment/exception_management/`
- **Implementation**: `exception_management_agent_strands.py`
- **Key Features**:
  - LLM-based exception severity scoring
  - Intelligent delegation and routing decisions
  - Time-based exception analysis
- **Input**: Unmatched trades, validation errors, processing failures
- **Output**: Prioritized exception queue in DynamoDB
- **Table**: `trade-matching-system-exceptions-production`
- **Tools**: `use_aws` for DynamoDB operations
- **Memory**: Shared memory ID `trade_matching_decisions-Z3tG4b4Xsd`

### 5. Orchestrator Agent
- **Purpose**: Goal-based workflow orchestration
- **Location**: `deployment/orchestrator/`
- **Implementation**: `orchestrator_agent_strands.py` (goal-based version)
- **Key Features**:
  - AI-driven orchestration decisions
  - Agent registry management
  - SLA monitoring and compliance
  - Workflow status tracking
- **Input**: Agent status, workflow events
- **Output**: Control commands, workflow coordination
- **Registry Table**: `trade-matching-system-agent-registry-production`
- **Tools**: `use_aws` for DynamoDB and agent invocation
- **Observability**: Manual observability class integration

## Key AWS Resources

### S3 Bucket: `trade-matching-system-agentcore-production`
- `BANK/` - Bank trade confirmation PDFs
- `COUNTERPARTY/` - Counterparty trade confirmation PDFs  
- `extracted/` - Text extraction outputs from PDF Adapter
- `canonical/` - Structured JSON outputs from Trade Extraction
- `reports/` - Matching reports and analytics

### DynamoDB Tables
- `BankTradeData` - Bank-side trade records (written by Trade Extraction)
- `CounterpartyTradeData` - Counterparty-side trade records (written by Trade Extraction)
- `ai-trade-matching-processing-status` - Real-time workflow status tracking (Dec 2025)
- `trade-matching-system-exceptions-production` - Exceptions and errors (managed by Exception Management agent)  
- `trade-matching-system-agent-registry-production` - Agent metadata and routing (used by Orchestrator)

### AgentCore Platform Services
#### Memory Resources
- **Shared Memory ID**: `trade_matching_decisions-Z3tG4b4Xsd` (used by all agents)
- **Namespace Strategies**:
  - `/facts/{actorId}` - Semantic memory for factual trade information
  - `/preferences/{actorId}` - Learned processing preferences
  - `/summaries/{actorId}/{sessionId}` - Past matching session summaries
- **Retention**: 90 days for all memory types
- **Session Management**: AgentCoreMemorySessionManager with retrieval configs

#### Gateway Resources  
- `trade-matching-system-dynamodb-gateway-production` - DynamoDB access gateway
- `trade-matching-system-s3-gateway-production` - S3 access gateway
- Secure, audited access to AWS services

#### Observability Configuration
- CloudWatch Logs: `/aws/bedrock-agentcore/{agent-name}`
- Custom metrics: ExtractionSuccessRate, ProcessingTimeMs, TokenUsage, ExtractionConfidence
- PII redaction enabled for all logs
- Real-time monitoring dashboards

#### Identity & Access
- Cognito User Pool: `us-east-1_uQ2lN39dT`
- Client ID: `78daptta2m4lb6k5jm3n2hd8oc`
- MFA enabled for production access

### Bedrock Integration
- Amazon Nova Pro v1 (us.amazon.nova-pro-v1:0): Primary model for all agents
- Temperature: 0 for deterministic outputs
- Max tokens: 4096
- Region: us-east-1

## Data Flow Pipeline
```
PDF Upload → S3 (BANK/ or COUNTERPARTY/)
  ↓
PDF Adapter Agent (text extraction via OCR)
  ↓
Trade Extraction Agent (structured data using LLM)
  ↓
DynamoDB (BankTradeData/CounterpartyTradeData)
  ↓
Trade Matching Agent (AI-driven fuzzy matching with confidence scoring)
  ↓
Match Results → Reports (S3) or Exceptions (DynamoDB)
  ↓
Exception Management Agent (severity scoring and routing)
  ↓
HITL Review (web portal for manual review)
```

**Agent Communication:**
- Direct invocation via AgentCore Runtime
- State persistence through DynamoDB tables
- Pattern learning via AgentCore Memory
- Secure AWS service access through AgentCore Gateway

## Matching Classification Thresholds
- **MATCHED** (≥85%): Auto-approve, no human review required
- **PROBABLE_MATCH** (70-84%): Escalate to HITL for verification
- **REVIEW_REQUIRED** (50-69%): Exception queue, requires investigation
- **BREAK** (<50%): Exception queue, likely mismatch

## Code Conventions

### Agent Development
- Each agent has its own `agentcore.yaml` and `.bedrock_agentcore.yaml` configuration
- Use Strands SDK for agent implementation (`*_agent_strands.py` or `agent.py`)
- All agents use `BYPASS_TOOL_CONSENT=true` for non-interactive execution
- Shared memory resource: `trade_matching_decisions-Z3tG4b4Xsd`
- Common tools:
  - `use_aws` from `strands_tools` package for AWS service operations
  - Custom tool implementations when needed
  - `extract_text_from_pdf_s3` for PDF processing (PDF Adapter)
- All agents must implement error handling and retry logic
- Use structured logging with correlation IDs for traceability
- AgentCore integrations:
  - **Memory**: Session management with namespace strategies (/facts, /preferences, /summaries)
  - **Gateway**: Not actively used in current implementations
  - **Observability**: Auto-instrumented via OTEL when `strands-agents[otel]` installed
  - **Identity**: Configured but not actively used in agent code

### Deployment Structure
- Agent code: `deployment/{agent_name}/`
  - Main implementation: `*_agent_strands.py`
  - Alternative: `agent.py` for some agents
- Deployment script: `deployment/{agent_name}/deploy.sh`
- Requirements: `deployment/{agent_name}/requirements.txt`
- Configuration files:
  - `deployment/{agent_name}/agentcore.yaml` - AgentCore runtime configuration
  - `deployment/{agent_name}/.bedrock_agentcore.yaml` - Deployment configuration

### Testing
- Property-based tests: `tests/property_based/`
- E2E tests: `tests/e2e/`
- Use Hypothesis for property-based testing
- Mock AWS services for unit tests

### Security
- Never hardcode credentials or sensitive data
- Use IAM roles and policies for AWS access
- Validate all inputs before processing
- Sanitize data before LLM prompts to prevent injection

## Project Structure
- `/deployment/` - Agent implementations and deployment scripts
  - `pdf_adapter/` - PDF text extraction agent
  - `trade_extraction/` - Trade data extraction agent
  - `trade_matching/` - Trade matching agent
  - `exception_management/` - Exception routing agent
  - `orchestrator/` - Workflow orchestration agent
  - `swarm_agentcore/` - Additional AgentCore configurations
- `/terraform/` - Infrastructure as Code for AWS resources
- `/web-portal/` - React-based HITL review interface
- `/web-portal-api/` - FastAPI backend for web portal
- `/tests/` - Test suites (property-based, E2E)
- `/scripts/` - Utility scripts for operations and monitoring
- `/docs/` - Additional documentation and UX specifications

## Key Technical Implementation Details

### PDF Processing Architecture
- **Method**: Bedrock multimodal LLM (not traditional OCR libraries)
- **Process**: Convert PDF to base64 images → Send to Nova Pro → Extract text via AI
- **Advantages**: Better handling of complex layouts, handwriting, and poor quality scans

### Memory & Learning
- **Shared Memory**: All agents use `trade_matching_decisions-Z3tG4b4Xsd`
- **Cross-Agent Learning**: Patterns learned by one agent benefit all agents
- **Session Strategy**: Each invocation creates unique session for tracking
- **Namespace Organization**:
  - Facts: Factual trade information and patterns
  - Preferences: User/system learned preferences
  - Summaries: Session summaries for context

### Tool Architecture
- **Primary Tool**: `use_aws` from `strands_tools` package
- **Fallback Pattern**: Custom boto3 implementation when package unavailable
- **Tool Discovery**: Multiple import paths attempted for maximum compatibility
- **Non-Interactive Mode**: `BYPASS_TOOL_CONSENT=true` for automated execution

### AI Model Configuration
- **Primary Model**: Amazon Nova Pro v1 (`us.amazon.nova-pro-v1:0`)
- **Temperature**: 0 for deterministic financial outputs
- **Max Tokens**: 4096
- **Model Migration**: All agents now use Amazon Nova Pro v1 (legacy Claude references removed)

### Trade Matching Intelligence
- **ID Normalization**: Intelligent prefix system (bank_, cpty_) with numeric extraction
- **Confidence Scoring**: 4-tier classification system with detailed reasoning
- **Pattern Learning**: Historical matching patterns inform future decisions
- **Context Awareness**: Multi-field analysis beyond simple string matching

### Real-Time Status Tracking (Dec 2025)
- **Status Table**: `ai-trade-matching-processing-status` DynamoDB table
- **Orchestrator Integration**: Writes status after each agent execution
- **Web Portal Integration**: Real-time UI updates via polling/WebSocket  
- **Token Usage Tracking**: Cost monitoring and LLM optimization metrics
- **Schema**: sessionId (PK), agent status objects with timing/tokens/errors
- **TTL**: 90-day retention for operational history
- **Frontend Display**: Progressive steps UI with actual agent progress

### Observability & Monitoring
- **Auto-Instrumentation**: OpenTelemetry integration via `strands-agents[otel]`
- **No Manual Spans**: AgentCore Runtime handles trace management automatically
- **CloudWatch Integration**: Logs and metrics automatically captured
- **Correlation IDs**: End-to-end request tracing across agents
- **Cost Tracking**: Token usage aggregation across all agents

### Error Handling & Resilience
- **Graceful Degradation**: Fallback implementations when dependencies unavailable
- **Retry Logic**: Built into all agents for transient failures
- **Exception Management**: Dedicated agent for intelligent error triage
- **Validation**: Input validation at every stage
