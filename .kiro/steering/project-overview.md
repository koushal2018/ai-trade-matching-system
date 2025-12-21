---
inclusion: always
---

# AI Trade Matching System - Project Overview

## System Description
This is an AI-powered trade reconciliation platform built on AWS that automates matching of OTC derivative trade confirmations between financial institutions and counterparties.

## Architecture
- **Runtime**: Amazon Bedrock AgentCore (serverless)
- **Agent Framework**: Strands SDK with `use_aws` tool
- **AI Model**: Claude Sonnet 4 / Amazon Nova Pro (temperature: 0.1)
- **Region**: us-east-1

## Core Agents (5 specialized agents)
1. **PDF Adapter Agent** - Extracts text from trade confirmation PDFs
2. **Trade Extraction Agent** - Extracts structured trade data using LLM
3. **Trade Matching Agent** - Fuzzy matches trades with confidence scoring
4. **Exception Management Agent** - Routes exceptions with RL-based severity scoring
5. **Orchestrator Agent** - Monitors SLA compliance and issues control commands

## Key AWS Resources
- **S3**: `trade-matching-system-agentcore-production` (PDFs, canonical outputs, reports)
- **DynamoDB**: BankTradeData, CounterpartyTradeData, ExceptionsTable, AgentRegistry
- **SQS**: Event-driven communication between agents (FIFO queues)
- **Bedrock**: Claude Sonnet 4 for reasoning, Nova Pro for document processing

## Data Flow
```
PDF Upload → S3 (BANK/ or COUNTERPARTY/) → PDF Adapter → Trade Extraction 
→ DynamoDB → Trade Matching → Reports/Exceptions → HITL Review
```

## Matching Classification Thresholds
- **MATCHED** (≥85%): Auto-approve
- **PROBABLE_MATCH** (70-84%): Escalate to HITL
- **REVIEW_REQUIRED** (50-69%): Exception queue
- **BREAK** (<50%): Exception queue
