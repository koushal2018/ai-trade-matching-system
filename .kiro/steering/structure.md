---
inclusion: always
---

# Project Structure

## Directory Organization

```
ai-trade-matching-system/
├── src/latest_trade_matching_agent/    # Main application code
│   ├── config/                         # Agent and task configurations
│   ├── tools/                          # Custom CrewAI tools
│   ├── crew_fixed.py                   # Main crew definition
│   ├── main.py                         # Entry point
│   └── eks_main.py                     # FastAPI server for EKS
├── terraform/                          # Infrastructure as Code
├── lambda/                             # Lambda function code
├── config/                             # Application configuration
├── data/                               # Sample trade PDFs
├── docs/                               # Documentation
├── storage/                            # Local storage directory
└── .kiro/                              # Kiro AI assistant configuration
```

## Key Files

### AgentCore Deployment (Production)

- **`deployment/pdf_adapter/pdf_adapter_agent_strands.py`**: PDF Adapter using Strands SDK
- **`deployment/trade_extraction/trade_extraction_agent_strands.py`**: Trade Extraction using Strands SDK
- **`deployment/trade_matching/trade_matching_agent_strands.py`**: Trade Matching using Strands SDK
- **`deployment/exception_management/exception_management_agent_strands.py`**: Exception Management with RL
- **`deployment/orchestrator/orchestrator_agent_strands.py`**: Orchestrator for SLA monitoring
- **`deployment/deploy_all.sh`**: Master deployment script for all agents

### Supporting Modules (Used by Deployment)

- **`src/latest_trade_matching_agent/matching/`**: Fuzzy matching, scoring, classification logic
- **`src/latest_trade_matching_agent/exception_handling/`**: Exception classification, triage, RL handler
- **`src/latest_trade_matching_agent/orchestrator/`**: SLA monitoring, compliance checking, control commands
- **`src/latest_trade_matching_agent/models/`**: Pydantic models for trade, events, registry, taxonomy

### Legacy Code (Not Used in Production)

- **`src/latest_trade_matching_agent/crew_fixed.py`**: Old CrewAI implementation (reference only)
- **`src/latest_trade_matching_agent/config/agents.yaml`**: Old agent configs (reference only)
- **`src/latest_trade_matching_agent/config/tasks.yaml`**: Old task configs (reference only)

### Infrastructure

- **`terraform/main.tf`**: Main Terraform configuration
- **`terraform/dynamodb.tf`**: DynamoDB table definitions
- **`terraform/s3.tf`**: S3 bucket configuration
- **`terraform/lambda.tf`**: Lambda function setup
- **`terraform/variables.tf`**: Terraform variables

### Documentation

- **`README.md`**: Comprehensive project documentation
- **`ARCHITECTURE.md`**: Detailed system architecture
- **`docs/architecture-simplified.mmd`**: Mermaid diagram of architecture

## Agent Architecture

The system uses a **Strands Swarm** with 4 specialized agents that autonomously hand off tasks:

1. **PDF Adapter Agent** (`pdf_adapter`)
   - Downloads PDFs from S3
   - Extracts text directly from PDF using Bedrock multimodal
   - Saves canonical output to S3 (extracted text + metadata)
   - Hands off to trade_extractor after successful extraction

2. **Trade Extraction Agent** (`trade_extractor`)
   - Reads canonical output from S3 using use_aws tool
   - LLM decides which trade fields to extract (context-aware)
   - Stores in DynamoDB (BANK or COUNTERPARTY table)
   - Hands off to trade_matcher after storing trade data

3. **Trade Matching Agent** (`trade_matcher`)
   - Scans both DynamoDB tables for trades
   - Matches by attributes (NOT Trade_ID - trades have different IDs across systems)
   - Calculates confidence scores and classifies results
   - Generates matching reports and saves to S3
   - Hands off to exception_handler if REVIEW_REQUIRED or BREAK

4. **Exception Handler Agent** (`exception_handler`)
   - Analyzes exceptions and determines severity (CRITICAL, HIGH, MEDIUM, LOW)
   - Calculates SLA deadlines based on business impact
   - Stores exception records in DynamoDB ExceptionsTable
   - Reports findings (no further handoff)

## Data Storage Patterns

### S3 Folder Structure

```
s3://trade-matching-system-agentcore-production/
├── BANK/                              # Bank trade PDFs (input)
├── COUNTERPARTY/                      # Counterparty trade PDFs (input)
├── extracted/                         # Canonical adapter output
│   ├── BANK/{document_id}.json
│   └── COUNTERPARTY/{document_id}.json
└── reports/                           # Matching analysis reports
    └── matching_report_{trade_id}_{timestamp}.md
```

### Local Processing Directory

```
/tmp/
└── {document_id}.pdf                  # Temporary PDF download
```

### DynamoDB Tables

- **BankTradeData**: Stores trades from bank systems (TRADE_SOURCE="BANK")
- **CounterpartyTradeData**: Stores trades from counterparties (TRADE_SOURCE="COUNTERPARTY")
- **Primary Key**: Trade_ID (String)
- **Format**: DynamoDB typed format (e.g., `{"S": "value"}`, `{"N": "123"}`)

## Code Conventions

### Agent Configuration

- All agents use AWS Bedrock Claude Sonnet 4 (`us.anthropic.claude-sonnet-4-20250514-v1:0`)
- Strands Swarm framework with autonomous handoffs
- `temperature=0.1` for deterministic processing
- `max_tokens=4096` for response generation
- LLM-driven decision making (agents decide when to hand off)
- Direct boto3 access for DynamoDB operations

### Task Flow

- Swarm-based architecture (agents hand off to each other autonomously)
- Canonical output pattern: standardized adapter output for downstream processing
- Agents decide when to hand off based on task context
- No hardcoded workflow steps - emergent collaboration

### Tool Usage

- **Strands AWS Tool**: `use_aws` - Built-in tool for S3 and Bedrock operations
- **Custom Tools**: 
  - `download_pdf_from_s3`: Get PDF from S3
  - `extract_text_with_bedrock`: OCR with Bedrock multimodal
  - `save_canonical_output`: Save standardized output to S3
  - `store_trade_in_dynamodb`: Save extracted trade data
  - `scan_trades_table`: Retrieve trades from DynamoDB
  - `save_matching_report`: Save analysis to S3
  - `get_severity_guidelines`: Get exception classification rules
  - `store_exception_record`: Track exceptions with SLA deadlines
- **boto3 Direct Access**: All custom tools use boto3 for AWS operations

### Error Handling

- All tools return JSON strings with success/error status
- Agents verify operations before proceeding
- Data integrity checks before matching

### LLM Optimization

- Low temperature (0.1) for deterministic extraction
- Goal-oriented prompts (LLM decides the approach)
- Canonical output pattern (standardized format)
- AgentCore observability for token tracking
- Strands SDK handles tool orchestration efficiently

## Input Format

The swarm's `process_trade_confirmation()` function expects:

```python
result = process_trade_confirmation(
    document_path="s3://bucket/key or just key",  # S3 path to PDF
    source_type="BANK" or "COUNTERPARTY",         # CRITICAL for routing
    document_id="optional_doc_id",                # Auto-generated if not provided
    correlation_id="optional_corr_id"             # For tracing
)
```

CLI usage:
```bash
python deployment/swarm/trade_matching_swarm.py \
  data/BANK/FAB_26933659.pdf \
  --source-type BANK \
  --document-id FAB_26933659 \
  --verbose
```

## Deployment Patterns

### Strands Swarm (Current Implementation)

Run the swarm locally:
```bash
python deployment/swarm/trade_matching_swarm.py \
  document_path \
  --source-type BANK \
  --verbose
```

### Web Portal

React frontend with FastAPI backend:
```bash
cd web-portal
npm run dev

cd web-portal-api
uvicorn app.main:app --reload
```

### Legacy AgentCore Deployment (Reference Only)

The `deployment/*/` folders contain legacy AgentCore deployment packages that are not used in the current Strands Swarm implementation.

## Important Notes

- Always classify trades as BANK or COUNTERPARTY before processing
- trade_id is the primary key for all DynamoDB operations
- Use DynamoDB typed format for all attributes: `{"S": "value"}`, `{"N": "123"}`
- Verify TRADE_SOURCE matches table location (data integrity check)
- Strands Swarm manages agent handoffs autonomously
- Agents decide when to hand off based on task context (no hardcoded workflows)
- All agents use Bedrock Claude Sonnet 4 in us-east-1 region
- Trades have DIFFERENT IDs across systems - match by attributes, not Trade_ID
