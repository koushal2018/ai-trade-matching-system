---
inclusion: always
---

# Product Overview

AI Trade Matching System - An enterprise-grade trade confirmation matching solution that automates the processing and matching of derivative trade confirmations using AWS Bedrock Claude Sonnet 4 and Strands Swarm framework.

## Core Problem

Manual trade confirmation matching is time-consuming, error-prone, and doesn't scale with trading volumes. This system automates the entire process from PDF ingestion to intelligent matching, reducing settlement risk and operational overhead.

## Key Capabilities

- AI-powered document processing using AWS Bedrock Claude Sonnet 4 (multimodal) for direct PDF text extraction
- Strands Swarm architecture with 4 specialized agents that autonomously hand off tasks
- Emergent collaboration where agents decide when to hand off based on task context
- DynamoDB integration with boto3 for direct database access
- Intelligent data storage with separate tables for bank and counterparty trades
- Professional trade matching by attributes (trades have different IDs across systems)
- Exception management with severity classification and SLA tracking
- Canonical output pattern for standardized adapter output

## Data Flow

1. Trade PDFs uploaded to S3 (BANK or COUNTERPARTY folders)
2. PDF Adapter Agent downloads PDF and extracts text using AWS Bedrock multimodal
3. Canonical output (extracted text + metadata) saved to S3
4. PDF Adapter hands off to Trade Extraction Agent
5. Trade Extraction Agent reads canonical output and extracts structured trade data
6. Trade data stored in appropriate DynamoDB table (BankTradeData or CounterpartyTradeData)
7. Trade Extraction hands off to Trade Matching Agent
8. Trade Matching Agent scans both tables and matches by attributes (NOT Trade_ID)
9. Matching report saved to S3 with classification (MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, BREAK)
10. If issues found, Trade Matching hands off to Exception Handler Agent
11. Exception Handler analyzes severity, calculates SLA deadlines, and stores exception record

## Critical Business Rules

- **Source Classification**: All trades must be classified as either BANK or COUNTERPARTY
- **Table Routing**: BANK trades → BankTradeData, COUNTERPARTY trades → CounterpartyTradeData
- **Data Integrity**: System verifies TRADE_SOURCE field matches table location
- **Primary Key**: trade_id is the primary key for all DynamoDB operations
- **Matching Strategy**: Match by attributes (currency, notional, dates, counterparty) - NOT by Trade_ID
- **Trades Have Different IDs**: Bank and counterparty systems use different Trade_IDs for the same trade
- **Matching Tolerances**: Currency (exact), Notional (±2%), Dates (±2 days), Counterparty (fuzzy)
- **Classification Thresholds**: MATCHED (85%+), PROBABLE_MATCH (70-84%), REVIEW_REQUIRED (50-69%), BREAK (<50%)
