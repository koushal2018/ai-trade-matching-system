# AI Trade Matching System - Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AI TRADE MATCHING SYSTEM                                 │
│                   AWS Cloud Architecture (me-central-1)                      │
└─────────────────────────────────────────────────────────────────────────────┘


╔═════════════════════════════════════════════════════════════════════════════╗
║  INPUT LAYER                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════╝

   📄 Trade Confirmation PDFs
         │
         │  Classification:
         │  • BANK (from bank)
         │  • COUNTERPARTY (from counterparty)
         │
         ▼
   ┌──────────────────────┐
   │   Amazon S3 Bucket   │
   │   otc-menat-2025     │
   └──────────┬───────────┘
              │
              │  S3 Folder Structure:
              │  ├─ BANK/                    (Bank trade PDFs)
              │  ├─ COUNTERPARTY/            (Counterparty PDFs)
              │  ├─ PDFIMAGES/               (Converted images)
              │  │  ├─ BANK/{trade_id}/
              │  │  └─ COUNTERPARTY/{trade_id}/
              │  ├─ extracted/               (Structured JSON)
              │  │  ├─ BANK/
              │  │  └─ COUNTERPARTY/
              │  └─ reports/                 (Matching reports)
              │
              ▼


╔═════════════════════════════════════════════════════════════════════════════╗
║  PROCESSING LAYER - CrewAI Multi-Agent System                                ║
╚═════════════════════════════════════════════════════════════════════════════╝

   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 1: Document Processor                                     │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Role: PDF to Image Converter                                       │
   │  Max Iterations: 5                                                  │
   │                                                                      │
   │  Tasks:                                                              │
   │  1. Download PDF from S3                                            │
   │  2. Convert PDF → JPEG images (300 DPI)                             │
   │  3. Save images to S3: PDFIMAGES/{source}/{id}/                     │
   │  4. Save locally: /tmp/processing/{id}/pdf_images/                  │
   │                                                                      │
   │  Tools: PDFToImageTool (poppler + boto3)                            │
   │  Output: "Images ready for OCR processing"                          │
   └─────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 2: OCR Processor                                          │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Role: Text Extraction Specialist                                   │
   │  Max Iterations: 10                                                 │
   │                                                                      │
   │  Tasks:                                                              │
   │  1. List all image files in directory                               │
   │  2. Process each page (1-5) with OCR                                │
   │  3. Extract text using AWS Bedrock multimodal                       │
   │  4. Combine text from all pages                                     │
   │  5. Save combined text: /tmp/processing/{id}/ocr_text.txt          │
   │                                                                      │
   │  Tools: OCRTool, FileWriterTool, DirectoryReadTool                  │
   │  Output: "OCR complete. Pages processed: 5"                         │
   └─────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 3: Trade Entity Extractor                                 │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Role: JSON Parser & Data Structurer                                │
   │  Max Iterations: 5                                                  │
   │                                                                      │
   │  Tasks:                                                              │
   │  1. Read OCR text from file                                         │
   │  2. Parse trade fields into structured JSON:                        │
   │     • Trade_ID (required)                                           │
   │     • TRADE_SOURCE (BANK/COUNTERPARTY)                              │
   │     • trade_date, effective_date, maturity_date                     │
   │     • notional, currency, commodity_type                            │
   │     • counterparty, product_type                                    │
   │     • ... (30+ fields)                                              │
   │  3. Save JSON to S3: extracted/{source}/trade_{id}_{ts}.json        │
   │  4. Return S3 path only (scratchpad pattern)                        │
   │                                                                      │
   │  Tools: FileReadTool, S3WriterTool                                  │
   │  Output: "S3_PATH: s3://.../extracted/COUNTERPARTY/trade_XXX.json" │
   └─────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 4: Reporting Analyst                                      │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Role: DynamoDB Data Storage Manager                                │
   │  Max Iterations: 8                                                  │
   │                                                                      │
   │  Tasks:                                                              │
   │  1. Extract S3 path from previous agent's output                    │
   │  2. Read trade JSON from S3                                         │
   │  3. Determine target table based on TRADE_SOURCE:                   │
   │     • BANK → BankTradeData                                          │
   │     • COUNTERPARTY → CounterpartyTradeData                          │
   │  4. Format data in DynamoDB typed format:                           │
   │     {"Trade_ID": {"S": "value"}, "notional": {"N": "123"}}         │
   │  5. Upsert to DynamoDB using Trade_ID as primary key                │
   │  6. Verify write success                                            │
   │                                                                      │
   │  Tools: S3ReaderTool, DynamoDBTool, AWS API MCP Server              │
   │  Output: "Trade data stored successfully in DynamoDB"               │
   └─────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  🤖 Agent 5: Matching Analyst                                       │
   │  ─────────────────────────────────────────────────────────────────  │
   │  Role: Trade Matching & Reconciliation Expert                       │
   │  Max Iterations: 10                                                 │
   │                                                                      │
   │  Tasks:                                                              │
   │  1. Data Integrity Check:                                           │
   │     • Scan BankTradeData - verify TRADE_SOURCE = "BANK"            │
   │     • Scan CounterpartyTradeData - verify "COUNTERPARTY"           │
   │  2. Perform Fuzzy Matching:                                         │
   │     • Trade_ID: exact match required                                │
   │     • Trade_Date: ±1 day tolerance                                  │
   │     • Notional: ±0.01% tolerance                                    │
   │     • Counterparty: fuzzy string match                              │
   │  3. Classify Results:                                               │
   │     • MATCHED - All criteria match                                  │
   │     • PROBABLE_MATCH - Trade_ID + 2/3 fields match                  │
   │     • REVIEW_REQUIRED - Differences within tolerance                │
   │     • BREAK - No matching Trade_ID found                            │
   │     • DATA_ERROR - Wrong TRADE_SOURCE in wrong table                │
   │  4. Generate markdown report                                        │
   │  5. Save to S3: reports/matching_report_{id}_{ts}.md               │
   │                                                                      │
   │  Tools: DynamoDBTool, S3WriterTool, FileWriterTool                  │
   │  Output: "Matching analysis complete. Report saved to S3"           │
   └─────────────────────────────────────────────────────────────────────┘


   ╔════════════════════════════════════════════════════════════════════╗
   ║  All agents powered by:                                            ║
   ║                                                                    ║
   ║  🧠 AWS Bedrock - Claude Sonnet 4                                 ║
   ║  ─────────────────────────────────────────────────────────────────║
   ║  Model: apac.anthropic.claude-sonnet-4-20250514-v1:0              ║
   ║  Region: me-central-1 (Middle East - UAE)                         ║
   ║  Temperature: 0.7                                                  ║
   ║  Max Tokens: 4096                                                  ║
   ║  Rate Limit: 2 RPM (requests per minute)                          ║
   ║  Max Retry: 1                                                      ║
   ║  Multimodal: Enabled (for OCR)                                    ║
   ╚════════════════════════════════════════════════════════════════════╝


╔═════════════════════════════════════════════════════════════════════════════╗
║  DATA LAYER                                                                  ║
╚═════════════════════════════════════════════════════════════════════════════╝

   ┌─────────────────────────────────────────────────────────────────────┐
   │  🗄️  Amazon DynamoDB (me-central-1)                                │
   │  ─────────────────────────────────────────────────────────────────  │
   │                                                                      │
   │  ┌──────────────────────────┐    ┌──────────────────────────┐      │
   │  │  BankTradeData           │    │  CounterpartyTradeData   │      │
   │  │  ──────────────────────  │    │  ──────────────────────  │      │
   │  │  PK: Trade_ID (String)   │    │  PK: Trade_ID (String)   │      │
   │  │  Billing: PAY_PER_REQUEST│    │  Billing: PAY_PER_REQUEST│      │
   │  │                          │    │                          │      │
   │  │  Required Attributes:    │    │  Required Attributes:    │      │
   │  │  • Trade_ID              │    │  • Trade_ID              │      │
   │  │  • TRADE_SOURCE: "BANK"  │    │  • TRADE_SOURCE:         │      │
   │  │                          │    │    "COUNTERPARTY"        │      │
   │  │  Trade Details:          │    │                          │      │
   │  │  • trade_date            │    │  Trade Details:          │      │
   │  │  • effective_date        │    │  • trade_date            │      │
   │  │  • maturity_date         │    │  • effective_date        │      │
   │  │  • notional              │    │  • maturity_date         │      │
   │  │  • currency              │    │  • notional              │      │
   │  │  • commodity_type        │    │  • currency              │      │
   │  │  • product_type          │    │  • commodity_type        │      │
   │  │  • counterparty          │    │  • product_type          │      │
   │  │                          │    │  • counterparty          │      │
   │  │  Metadata:               │    │                          │      │
   │  │  • s3_source             │    │  Metadata:               │      │
   │  │  • processing_timestamp  │    │  • s3_source             │      │
   │  │  • global_uti            │    │  • processing_timestamp  │      │
   │  │  • document_version      │    │  • global_uti            │      │
   │  │                          │    │  • document_version      │      │
   │  │  Total: 30+ fields       │    │  Total: 30+ fields       │      │
   │  └──────────────────────────┘    └──────────────────────────┘      │
   │                                                                      │
   │  Access Methods:                                                     │
   │  ├─ Custom DynamoDBTool (boto3 direct API)                          │
   │  │  • put_item(table_name, item)                                    │
   │  │  • scan(table_name)                                              │
   │  │  • Typed format: {"attr": {"S": "value"}, {"N": "123"}}         │
   │  │                                                                   │
   │  └─ AWS API MCP Server (uvx awslabs.aws-api-mcp-server@latest)     │
   │     • Full AWS CLI command support                                  │
   │     • Auto-starts on first get_mcp_tools() call                     │
   │     • Auto-cleanup after crew execution                             │
   └─────────────────────────────────────────────────────────────────────┘


╔═════════════════════════════════════════════════════════════════════════════╗
║  INTEGRATION LAYER                                                           ║
╚═════════════════════════════════════════════════════════════════════════════╝

   ┌─────────────────────────────────────────────────────────────────────┐
   │  🔗 Model Context Protocol (MCP)                                    │
   │  ─────────────────────────────────────────────────────────────────  │
   │                                                                      │
   │  Configuration:                                                      │
   │  ├─ Server: awslabs.aws-api-mcp-server@latest                       │
   │  ├─ Command: uvx                                                     │
   │  ├─ Environment:                                                     │
   │  │  • AWS_REGION=me-central-1                                       │
   │  │  • AWS_PROFILE=default                                           │
   │  │  • Uses AWS credentials from environment                         │
   │  │                                                                   │
   │  └─ Capabilities:                                                    │
   │     • AWS CLI commands as MCP tools                                 │
   │     • Supports all AWS services (DynamoDB, S3, Lambda, etc.)        │
   │     • Lifecycle managed by CrewAI @CrewBase decorator               │
   │     • Connection timeout: 60 seconds                                │
   │                                                                      │
   │  Important Note:                                                     │
   │  ⚠️  awslabs.dynamodb-mcp-server v2.0.0+ provides ONLY data        │
   │     modeling guidance, NOT operational tools.                       │
   │     Use awslabs.aws-api-mcp-server for actual operations.          │
   └─────────────────────────────────────────────────────────────────────┘


╔═════════════════════════════════════════════════════════════════════════════╗
║  OPTIMIZATION STRATEGIES                                                     ║
╚═════════════════════════════════════════════════════════════════════════════╝

   Token Optimization (85% Reduction):
   ────────────────────────────────────────────────────────────────────
   1. Scratchpad Pattern
      • Agents save detailed data to S3
      • Pass only S3 paths between tasks
      • Reduces context size significantly

   2. Concise Configurations
      • Minimal backstories in agents.yaml
      • Focused task descriptions
      • Essential instructions only

   3. Reduced Iterations
      • Document Processor: max_iter=5
      • OCR Processor: max_iter=10
      • Trade Entity Extractor: max_iter=5
      • Reporting Analyst: max_iter=8
      • Matching Analyst: max_iter=10

   4. Rate Limiting
      • max_rpm=2 (conservative to avoid throttling)
      • 15-second delay between tasks

   5. Verbose Mode Disabled
      • verbose=False on all agents
      • Reduces logging overhead


╔═════════════════════════════════════════════════════════════════════════════╗
║  DATA FLOW SUMMARY                                                           ║
╚═════════════════════════════════════════════════════════════════════════════╝

   Step 1: Document Upload
           Trade PDF → S3 (BANK/ or COUNTERPARTY/)

   Step 2: PDF Processing
           PDF → 5 JPEG images (300 DPI)
           → S3: PDFIMAGES/{source}/{id}/
           → Local: /tmp/processing/{id}/pdf_images/

   Step 3: OCR Extraction
           5 images → AWS Bedrock OCR
           → Combined text file: ocr_text.txt

   Step 4: Entity Extraction
           OCR text → Structured JSON (30+ fields)
           → S3: extracted/{source}/trade_{id}.json

   Step 5: Data Storage
           JSON → DynamoDB (BankTradeData or CounterpartyTradeData)
           → Typed format with Trade_ID as primary key

   Step 6: Matching Analysis
           Scan both DynamoDB tables
           → Fuzzy matching with tolerances
           → Classification (MATCHED/BREAK/etc.)
           → Report → S3: reports/matching_report_{id}.md

   Total Processing Time: ~60-90 seconds per trade confirmation
   Token Usage: ~120K tokens per complete workflow


╔═════════════════════════════════════════════════════════════════════════════╗
║  SECURITY & PERMISSIONS                                                      ║
╚═════════════════════════════════════════════════════════════════════════════╝

   AWS Credentials:
   ────────────────────────────────────────────────────────────────────
   • Managed via environment variables
   • AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
   • AWS_DEFAULT_REGION=me-central-1
   • AWS_PROFILE=default

   Required IAM Permissions:
   ────────────────────────────────────────────────────────────────────
   • S3: GetObject, PutObject, ListBucket
   • DynamoDB: PutItem, Scan, Query, DescribeTable
   • Bedrock: InvokeModel (Claude Sonnet 4)
   • CloudWatch: PutMetricData, CreateLogGroup, CreateLogStream (optional)

   Security Best Practices:
   ────────────────────────────────────────────────────────────────────
   • Use IAM roles instead of access keys where possible
   • Enable S3 bucket encryption at rest
   • Enable DynamoDB encryption at rest
   • Use VPC endpoints for private AWS service access
   • Enable CloudTrail for audit logging
   • Implement least-privilege access policies
```

## Component Details

### Agent Responsibilities

| Agent | Primary Function | Key Tools | Max Iterations |
|-------|-----------------|-----------|----------------|
| Document Processor | PDF → Images (300 DPI) | PDFToImageTool | 5 |
| OCR Processor | Image → Text | OCRTool, FileWriterTool | 10 |
| Trade Entity Extractor | Text → Structured JSON | FileReadTool, S3WriterTool | 5 |
| Reporting Analyst | JSON → DynamoDB | DynamoDBTool, MCP Server | 8 |
| Matching Analyst | Trade Matching & Reports | DynamoDBTool, S3WriterTool | 10 |

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| AI/ML | AWS Bedrock Claude Sonnet 4 | Document processing, OCR, entity extraction |
| Framework | CrewAI 0.175+ | Multi-agent orchestration |
| Data Storage | Amazon DynamoDB | Trade data persistence |
| Document Storage | Amazon S3 | PDFs, images, reports |
| Integration | Model Context Protocol (MCP) | AWS service integration |
| Processing | Python 3.11+, boto3 | Core application logic |

### Performance Metrics

| Metric | Value |
|--------|-------|
| PDF Processing | ~5 seconds |
| OCR Extraction (5 pages) | ~30-45 seconds |
| Entity Extraction | ~10-15 seconds |
| DynamoDB Storage | ~2-5 seconds |
| Matching Analysis | ~10-20 seconds |
| **Total Processing Time** | **~60-90 seconds** |
| **Token Usage** | **~120K tokens** |
| **Token Reduction** | **85%** |

### File Locations

| Component | Path |
|-----------|------|
| Main Crew | `src/latest_trade_matching_agent/crew_fixed.py` |
| Entry Point | `src/latest_trade_matching_agent/main.py` |
| Agent Config | `src/latest_trade_matching_agent/config/agents.yaml` |
| Task Config | `src/latest_trade_matching_agent/config/tasks.yaml` |
| PDF Tool | `src/latest_trade_matching_agent/tools/pdf_to_image.py` |
| DynamoDB Tool | `src/latest_trade_matching_agent/tools/dynamodb_tool.py` |
| Environment | `.env` |

---

**Last Updated**: October 2025
**System Version**: 1.0
**Architecture**: Multi-Agent AI System on AWS Bedrock
