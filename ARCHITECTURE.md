# AI Trade Matching System - Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AI TRADE MATCHING SYSTEM                                 │
│          Amazon Bedrock AgentCore Runtime (us-east-1)                        │
└─────────────────────────────────────────────────────────────────────────────┘


╔═════════════════════════════════════════════════════════════════════════════╗
║  INPUT LAYER                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════╝

   📄 Trade Confirmation PDFs
         │
         │  Classification:
         │  • BANK (from bank systems)
         │  • COUNTERPARTY (from counterparties)
         │
         ▼
   ┌──────────────────────┐
   │   Amazon S3 Bucket   │
   │ trade-matching-system│
   │  -agentcore-prod     │
   └──────────┬───────────┘
              │
              │  S3 Folder Structure:
              │  ├─ BANK/                    (Bank trade PDFs - input)
              │  ├─ COUNTERPARTY/            (Counterparty PDFs - input)
              │  ├─ extracted/               (Canonical outputs + trade JSON)
              │  │  ├─ BANK/
              │  │  └─ COUNTERPARTY/
              │  └─ reports/                 (Matching reports)
              │
              ▼


╔═════════════════════════════════════════════════════════════════════════════╗
║  PROCESSING LAYER - Amazon Bedrock AgentCore Runtime                         ║
║  Event-Driven Architecture with Strands SDK                                  ║
╚═════════════════════════════════════════════════════════════════════════════╝

   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 1: PDF Adapter Agent                                      │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Framework: Strands SDK + Amazon Bedrock AgentCore                  │
   │  Model: Claude Sonnet 4 (us.anthropic.claude-sonnet-4-20250514)    │
   │  Temperature: 0.1 (deterministic)                                   │
   │                                                                      │
   │  Workflow (LLM-Driven):                                             │
   │  1. Download PDF from S3 using custom tool                          │
   │  2. Extract text directly from PDF using Bedrock multimodal         │
   │     (No image conversion - direct PDF processing)                   │
   │  3. Create canonical output with extracted text + metadata          │
   │  4. Save canonical output to S3: extracted/{source}/{id}.json       │
   │                                                                      │
   │  Tools:                                                              │
   │  • download_pdf_from_s3(bucket, key, document_id)                   │
   │  • extract_text_with_bedrock(pdf_base64, document_id)               │
   │  • save_canonical_output(document_id, source_type, text, ...)       │
   │  • use_aws (Strands built-in AWS tool)                              │
   │                                                                      │
   │  Input: SQS event from document-upload-events queue                 │
   │  Output: Canonical output saved to S3 + PDF_PROCESSED event         │
   └─────────────────────────┬───────────────────────────────────────────┘
                             │
                             │ SQS: extraction-events
                             │ Event: PDF_PROCESSED
                             ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 2: Trade Extraction Agent                                 │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Framework: Strands SDK + Amazon Bedrock AgentCore                  │
   │  Model: Claude Sonnet 4                                             │
   │  Temperature: 0.1 (deterministic)                                   │
   │                                                                      │
   │  Workflow (LLM-Driven):                                             │
   │  1. Read canonical output from S3 using use_aws tool                │
   │  2. Analyze extracted_text field                                    │
   │  3. LLM decides which trade fields to extract (context-aware)       │
   │  4. Store in DynamoDB using use_aws tool:                           │
   │     • BANK trades → BankTradeData table                             │
   │     • COUNTERPARTY trades → CounterpartyTradeData table             │
   │                                                                      │
   │  Tools:                                                              │
   │  • use_aws (S3 get_object, DynamoDB put_item)                       │
   │                                                                      │
   │  Key Features:                                                       │
   │  • LLM decides relevant fields (not hardcoded)                      │
   │  • DynamoDB typed format: {"S": "value"}, {"N": "123"}              │
   │  • Composite key: trade_id + internal_reference                     │
   │                                                                      │
   │  Input: SQS event from extraction-events queue                      │
   │  Output: Trade stored in DynamoDB + TRADE_EXTRACTED event           │
   └─────────────────────────┬───────────────────────────────────────────┘
                             │
                             │ SQS: matching-events
                             │ Event: TRADE_EXTRACTED
                             ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 3: Trade Matching Agent                                   │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Framework: Strands SDK + Amazon Bedrock AgentCore                  │
   │  Model: Claude Sonnet 4                                             │
   │                                                                      │
   │  Workflow:                                                           │
   │  1. Retrieve trades from both DynamoDB tables                       │
   │  2. Perform fuzzy matching with tolerances:                         │
   │     • Trade_ID: Exact match                                         │
   │     • Trade_Date: ±1 business day                                   │
   │     • Notional: ±0.01%                                              │
   │     • Counterparty: Fuzzy string match (≥80% similarity)            │
   │  3. Compute match score (0.0 to 1.0)                                │
   │  4. Classify result:                                                │
   │     • Score ≥0.85: MATCHED → AUTO_MATCH                             │
   │     • Score 0.70-0.84: PROBABLE_MATCH → ESCALATE (HITL)             │
   │     • Score 0.50-0.69: REVIEW_REQUIRED → EXCEPTION                  │
   │     • Score <0.50: BREAK → EXCEPTION                                │
   │  5. Generate detailed matching report                               │
   │  6. Save report to S3: reports/matching_report_{id}.md              │
   │  7. Publish appropriate event based on classification               │
   │                                                                      │
   │  Modules Used:                                                       │
   │  • src/latest_trade_matching_agent/matching/fuzzy_matcher.py        │
   │  • src/latest_trade_matching_agent/matching/scorer.py               │
   │  • src/latest_trade_matching_agent/matching/classifier.py           │
   │  • src/latest_trade_matching_agent/matching/report_generator.py     │
   │                                                                      │
   │  Input: SQS event from matching-events queue                        │
   │  Output: Report to S3 + event to hitl-review or exception queue     │
   └─────────────────────────┬───────────────────────────────────────────┘
                             │
                             │ SQS: exception-events (if needed)
                             │ Event: MATCHING_EXCEPTION
                             ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 4: Exception Management Agent                             │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Framework: Strands SDK + Amazon Bedrock AgentCore                  │
   │  Model: Claude Sonnet 4                                             │
   │                                                                      │
   │  Workflow:                                                           │
   │  1. Classify exception into triage category:                        │
   │     • AUTO_RESOLVABLE                                               │
   │     • OPERATIONAL_ISSUE                                             │
   │     • DATA_QUALITY_ISSUE                                            │
   │     • SYSTEM_ISSUE                                                  │
   │     • COMPLIANCE_ISSUE                                              │
   │  2. Compute severity score (0.0 to 1.0) with RL adjustments         │
   │  3. Determine routing destination:                                  │
   │     • AUTO_RESOLVE                                                  │
   │     • OPS_DESK                                                      │
   │     • SENIOR_OPS                                                    │
   │     • COMPLIANCE                                                    │
   │     • ENGINEERING                                                   │
   │  4. Assign priority (1=highest to 5=lowest)                         │
   │  5. Calculate SLA hours (2-24 hours based on severity)              │
   │  6. Delegate to appropriate queue                                   │
   │  7. Create tracking record in DynamoDB ExceptionsTable              │
   │  8. Update RL model with resolution outcomes                        │
   │                                                                      │
   │  Modules Used:                                                       │
   │  • src/latest_trade_matching_agent/exception_handling/classifier.py │
   │  • src/latest_trade_matching_agent/exception_handling/scorer.py     │
   │  • src/latest_trade_matching_agent/exception_handling/triage.py     │
   │  • src/latest_trade_matching_agent/exception_handling/delegation.py │
   │  • src/latest_trade_matching_agent/exception_handling/rl_handler.py │
   │                                                                      │
   │  Key Features:                                                       │
   │  • Q-learning algorithm for optimal routing                         │
   │  • Supervised learning from human decisions                         │
   │  • Experience replay buffer (1000 episodes)                         │
   │  • Model persistence (save/load)                                    │
   │                                                                      │
   │  Input: SQS event from exception-events queue                       │
   │  Output: Delegated to ops/compliance/engineering queue              │
   └─────────────────────────┬───────────────────────────────────────────┘
                             │
                             │ Monitoring all queues
                             ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 5: Orchestrator Agent                                     │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Framework: Strands SDK + Amazon Bedrock AgentCore                  │
   │  Model: Claude Sonnet 4                                             │
   │                                                                      │
   │  Workflow:                                                           │
   │  1. Monitor SLA compliance:                                         │
   │     • Processing time per agent                                     │
   │     • Throughput (trades/hour)                                      │
   │     • Error rates                                                   │
   │     • Latency metrics                                               │
   │  2. Check compliance:                                               │
   │     • Data integrity (TRADE_SOURCE routing)                         │
   │     • Required fields validation                                    │
   │     • Regulatory requirements                                       │
   │  3. Issue control commands:                                         │
   │     • PAUSE_PROCESSING                                              │
   │     • RESUME_PROCESSING                                             │
   │     • ADJUST_PRIORITY                                               │
   │     • TRIGGER_ESCALATION                                            │
   │     • SCALE_UP / SCALE_DOWN                                         │
   │  4. Aggregate metrics and emit to CloudWatch                        │
   │                                                                      │
   │  Modules Used:                                                       │
   │  • src/latest_trade_matching_agent/orchestrator/sla_monitor.py      │
   │  • src/latest_trade_matching_agent/orchestrator/compliance_checker.py│
   │  • src/latest_trade_matching_agent/orchestrator/control_command.py  │
   │                                                                      │
   │  Key Features:                                                       │
   │  • Lightweight governance (no direct agent invocation)              │
   │  • Event-driven monitoring (fanout from all queues)                 │
   │  • Reactive control (commands based on violations)                  │
   │  • Independent scaling                                              │
   │                                                                      │
   │  Input: SQS event from orchestrator-monitoring-queue                │
   │  Output: Control commands + CloudWatch metrics                      │
   └─────────────────────────────────────────────────────────────────────┘


   ╔════════════════════════════════════════════════════════════════════╗
   ║  All agents powered by:                                            ║
   ║                                                                    ║
   ║  🧠 AWS Bedrock - Claude Sonnet 4                                 ║
   ║  ─────────────────────────────────────────────────────────────────║
   ║  Model: us.anthropic.claude-sonnet-4-20250514-v1:0                ║
   ║  Region: us-east-1 (US East)                                      ║
   ║  Temperature: 0.1 (deterministic extraction)                      ║
   ║  Max Tokens: 4096                                                  ║
   ║  Framework: Strands SDK with use_aws tool                         ║
   ║  Runtime: Amazon Bedrock AgentCore                                ║
   ╚════════════════════════════════════════════════════════════════════╝


╔═════════════════════════════════════════════════════════════════════════════╗
║  DATA LAYER                                                                  ║
╚═════════════════════════════════════════════════════════════════════════════╝

   ┌─────────────────────────────────────────────────────────────────────┐
   │  🗄️  Amazon DynamoDB (us-east-1)                                   │
   │  ─────────────────────────────────────────────────────────────────  │
   │                                                                      │
   │  ┌──────────────────────────┐    ┌──────────────────────────┐      │
   │  │  BankTradeData           │    │  CounterpartyTradeData   │      │
   │  │  ──────────────────────  │    │  ──────────────────────  │      │
   │  │  PK: trade_id (String)   │    │  PK: trade_id (String)   │      │
   │  │  SK: internal_reference  │    │  SK: internal_reference  │      │
   │  │  Billing: PAY_PER_REQUEST│    │  Billing: PAY_PER_REQUEST│      │
   │  │                          │    │                          │      │
   │  │  Required Attributes:    │    │  Required Attributes:    │      │
   │  │  • Trade_ID              │    │  • Trade_ID              │      │
   │  │  • TRADE_SOURCE: "BANK"  │    │  • TRADE_SOURCE:         │      │
   │  │                          │    │    "COUNTERPARTY"        │      │
   │  │  Trade Details:          │    │                          │      │
   │  │  • trade_date            │    │  Trade Details:          │      │
   │  │  • notional              │    │  • trade_date            │      │
   │  │  • currency              │    │  • notional              │      │
   │  │  • counterparty          │    │  • currency              │      │
   │  │  • product_type          │    │  • counterparty          │      │
   │  │  • ... (30+ fields)      │    │  • product_type          │      │
   │  │                          │    │  • ... (30+ fields)      │      │
   │  │  Format: DynamoDB typed  │    │  Format: DynamoDB typed  │      │
   │  │  {"S": "value"}          │    │  {"S": "value"}          │      │
   │  │  {"N": "123"}            │    │  {"N": "123"}            │      │
   │  └──────────────────────────┘    └──────────────────────────┘      │
   │                                                                      │
   │  ┌──────────────────────────┐    ┌──────────────────────────┐      │
   │  │  ExceptionsTable         │    │  AgentRegistry           │      │
   │  │  ──────────────────────  │    │  ──────────────────────  │      │
   │  │  PK: exception_id        │    │  PK: agent_id            │      │
   │  │  Tracks exception        │    │  Tracks agent status,    │      │
   │  │  lifecycle and routing   │    │  metrics, and SLA targets│      │
   │  └──────────────────────────┘    └──────────────────────────┘      │
   │                                                                      │
   │  Access Methods:                                                     │
   │  ├─ Strands use_aws tool (primary)                                  │
   │  │  • Service: dynamodb                                             │
   │  │  • Operations: put_item, get_item, scan, query                   │
   │  │                                                                   │
   │  └─ boto3 direct access (matching & exception modules)              │
   │     • For complex queries and batch operations                      │
   └─────────────────────────────────────────────────────────────────────┘


╔═════════════════════════════════════════════════════════════════════════════╗
║  INTEGRATION LAYER                                                           ║
╚═════════════════════════════════════════════════════════════════════════════╝

   ┌─────────────────────────────────────────────────────────────────────┐
   │  🔗 Amazon SQS - Event-Driven Communication                         │
   │  ─────────────────────────────────────────────────────────────────  │
   │                                                                      │
   │  Queues:                                                             │
   │  ├─ document-upload-events.fifo → PDF Adapter Agent                 │
   │  ├─ extraction-events → Trade Extraction Agent                      │
   │  ├─ matching-events → Trade Matching Agent                          │
   │  ├─ exception-events → Exception Management Agent                   │
   │  ├─ hitl-review-queue.fifo → Human-in-the-Loop review              │
   │  ├─ ops-desk-queue → Operations team                                │
   │  ├─ senior-ops-queue → Senior operations                            │
   │  ├─ compliance-queue → Compliance team                              │
   │  ├─ engineering-queue → Engineering team                            │
   │  └─ orchestrator-monitoring-queue → Orchestrator Agent              │
   │                                                                      │
   │  Event Format: StandardEventMessage                                 │
   │  {                                                                   │
   │    "event_id": "evt_abc123",                                        │
   │    "event_type": "PDF_PROCESSED",                                   │
   │    "source_agent": "pdf-adapter-agent",                             │
   │    "correlation_id": "corr_xyz789",                                 │
   │    "payload": { ... },                                              │
   │    "metadata": { ... }                                              │
   │  }                                                                   │
   └─────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────┐
   │  🧠 Strands SDK - LLM-Powered Agent Framework                       │
   │  ─────────────────────────────────────────────────────────────────  │
   │                                                                      │
   │  Key Features:                                                       │
   │  • Built-in use_aws tool for S3, DynamoDB, Bedrock operations       │
   │  • LLM-driven decision making (no hardcoded workflows)              │
   │  • Tool consent bypass for AgentCore Runtime                        │
   │  • Automatic tool orchestration                                     │
   │  • Token usage tracking                                             │
   │                                                                      │
   │  Configuration:                                                      │
   │  • Model: BedrockModel with Claude Sonnet 4                         │
   │  • Temperature: 0.1 (deterministic)                                 │
   │  • Max Tokens: 4096                                                 │
   │  • Region: us-east-1                                                │
   │  • Environment: BYPASS_TOOL_CONSENT=true                            │
   └─────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────┐
   │  📊 Amazon Bedrock AgentCore - Observability                        │
   │  ─────────────────────────────────────────────────────────────────  │
   │                                                                      │
   │  Features:                                                           │
   │  • Distributed tracing with correlation IDs                         │
   │  • Token usage metrics per agent invocation                         │
   │  • Processing time tracking                                         │
   │  • Success/failure rates                                            │
   │  • CloudWatch integration                                           │
   │  • Custom spans for detailed profiling                              │
   │                                                                      │
   │  Metrics Emitted:                                                    │
   │  • input_tokens, output_tokens, total_tokens                        │
   │  • processing_time_ms                                               │
   │  • success (boolean)                                                │
   │  • error_type, error_message (on failure)                           │
   └─────────────────────────────────────────────────────────────────────┘


╔═════════════════════════════════════════════════════════════════════════════╗
║  DEPLOYMENT ARCHITECTURE                                                     ║
╚═════════════════════════════════════════════════════════════════════════════╝

   Production Deployment:
   ────────────────────────────────────────────────────────────────────
   • Platform: Amazon Bedrock AgentCore Runtime
   • Region: us-east-1
   • Scaling: Auto-scaling (1-10 instances per agent)
   • Memory: 2-4GB per agent
   • Timeout: 3-15 minutes per agent
   • Deployment: Serverless (no infrastructure management)

   Deployment Process:
   ────────────────────────────────────────────────────────────────────
   1. Package agent code with requirements.txt
   2. Configure agent with agentcore.yaml
   3. Deploy using deployment scripts (deployment/*/deploy.sh)
   4. AgentCore Runtime manages lifecycle automatically

   Infrastructure:
   ────────────────────────────────────────────────────────────────────
   • Terraform: terraform/agentcore/ (SQS, DynamoDB, S3, IAM)
   • Web Portal: React + FastAPI (web-portal/, web-portal-api/)
   • Monitoring: CloudWatch + AgentCore Observability


╔═════════════════════════════════════════════════════════════════════════════╗
║  DATA FLOW SUMMARY                                                           ║
╚═════════════════════════════════════════════════════════════════════════════╝

   Step 1: Document Upload
           Trade PDF → S3 (BANK/ or COUNTERPARTY/)
           → Trigger: document-upload-events SQS message

   Step 2: PDF Processing (PDF Adapter Agent)
           Download PDF → Extract text with Bedrock multimodal
           → Save canonical output to S3: extracted/{source}/{id}.json
           → Publish: PDF_PROCESSED event to extraction-events

   Step 3: Trade Extraction (Trade Extraction Agent)
           Read canonical output from S3
           → LLM extracts relevant trade fields
           → Store in DynamoDB (BankTradeData or CounterpartyTradeData)
           → Publish: TRADE_EXTRACTED event to matching-events

   Step 4: Trade Matching (Trade Matching Agent)
           Retrieve trades from both DynamoDB tables
           → Fuzzy matching with scoring
           → Classify result (MATCHED/PROBABLE_MATCH/BREAK)
           → Generate report → S3: reports/matching_report_{id}.md
           → Publish: MATCH_COMPLETED or MATCHING_EXCEPTION event

   Step 5: Exception Handling (Exception Management Agent - if needed)
           Classify exception → Compute severity with RL
           → Determine routing destination
           → Delegate to appropriate team queue
           → Track in ExceptionsTable

   Step 6: Orchestration (Orchestrator Agent - continuous)
           Monitor SLA compliance across all agents
           → Check data integrity and compliance
           → Issue control commands if violations detected
           → Emit metrics to CloudWatch

   Total Processing Time: ~60-90 seconds per trade confirmation
   Token Usage: Varies by document complexity (tracked per agent)


╔═════════════════════════════════════════════════════════════════════════════╗
║  SECURITY & PERMISSIONS                                                      ║
╚═════════════════════════════════════════════════════════════════════════════╝

   AWS Credentials:
   ────────────────────────────────────────────────────────────────────
   • Managed via IAM roles (preferred)
   • Environment variables for local development
   • AWS_REGION=us-east-1

   Required IAM Permissions:
   ────────────────────────────────────────────────────────────────────
   • S3: GetObject, PutObject, ListBucket
   • DynamoDB: PutItem, GetItem, Scan, Query, DescribeTable
   • Bedrock: InvokeModel (Claude Sonnet 4)
   • SQS: SendMessage, ReceiveMessage, DeleteMessage
   • CloudWatch: PutMetricData, CreateLogGroup, CreateLogStream

   Security Best Practices:
   ────────────────────────────────────────────────────────────────────
   • Use IAM roles instead of access keys
   • Enable S3 bucket encryption at rest
   • Enable DynamoDB encryption at rest
   • Use VPC endpoints for private AWS service access
   • Enable CloudTrail for audit logging
   • Implement least-privilege access policies
   • Rotate credentials regularly
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Agent Framework** | Amazon Bedrock AgentCore Runtime | Serverless agent execution |
| **Agent SDK** | Strands SDK | LLM-powered agents with AWS tools |
| **AI Model** | AWS Bedrock Claude Sonnet 4 | Document processing, extraction, reasoning |
| **Data Storage** | Amazon DynamoDB | Trade data persistence |
| **Document Storage** | Amazon S3 | PDFs, canonical outputs, reports |
| **Event Bus** | Amazon SQS | Event-driven communication |
| **Observability** | AgentCore Observability + CloudWatch | Metrics, tracing, logging |
| **Infrastructure** | Terraform | Infrastructure as Code |
| **Web Portal** | React + FastAPI | User interface |

## Performance Metrics

| Metric | Value |
|--------|-------|
| PDF Processing | ~5-10 seconds |
| Text Extraction | ~10-20 seconds (direct PDF) |
| Trade Extraction | ~10-15 seconds |
| DynamoDB Storage | ~2-5 seconds |
| Matching Analysis | ~10-20 seconds |
| **Total Processing Time** | **~40-70 seconds** |
| **Agents** | 5 specialized agents |
| **Deployment** | Serverless (AgentCore) |

## File Locations

| Component | Path |
|-----------|------|
| **PDF Adapter** | `deployment/pdf_adapter/pdf_adapter_agent_strands.py` |
| **Trade Extraction** | `deployment/trade_extraction/trade_extraction_agent_strands.py` |
| **Trade Matching** | `deployment/trade_matching/trade_matching_agent_strands.py` |
| **Exception Management** | `deployment/exception_management/exception_management_agent_strands.py` |
| **Orchestrator** | `deployment/orchestrator/orchestrator_agent_strands.py` |
| **Matching Logic** | `src/latest_trade_matching_agent/matching/` |
| **Exception Logic** | `src/latest_trade_matching_agent/exception_handling/` |
| **Orchestrator Logic** | `src/latest_trade_matching_agent/orchestrator/` |
| **Models** | `src/latest_trade_matching_agent/models/` |
| **Infrastructure** | `terraform/agentcore/` |

---

**Last Updated**: December 4, 2024  
**System Version**: 2.0 (AgentCore + Strands)  
**Architecture**: Event-Driven Multi-Agent System on Amazon Bedrock AgentCore
