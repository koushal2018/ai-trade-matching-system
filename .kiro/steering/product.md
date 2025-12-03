---
inclusion: always
---

# Product Overview

AI Trade Matching System - An enterprise-grade trade confirmation matching solution that automates the processing and matching of derivative trade confirmations using AWS Bedrock Claude Sonnet 4 and CrewAI multi-agent framework.

## Core Problem

Manual trade confirmation matching is time-consuming, error-prone, and doesn't scale with trading volumes. This system automates the entire process from PDF ingestion to intelligent matching, reducing settlement risk and operational overhead.

## Key Capabilities

- AI-powered document processing using AWS Bedrock Claude Sonnet 4 (multimodal)
- High-quality PDF-to-image conversion (300 DPI) optimized for OCR
- Multi-agent architecture with 5 specialized agents handling document processing, OCR extraction, entity parsing, data storage, and matching
- Dual DynamoDB integration (custom boto3 tool + AWS API MCP Server)
- Intelligent data storage with separate tables for bank and counterparty trades
- Professional trade matching with fuzzy matching, tolerance handling, and break analysis
- Token-optimized design (85% reduction through scratchpad pattern)

## Data Flow

1. Trade PDFs uploaded to S3 (BANK or COUNTERPARTY folders)
2. PDF converted to high-resolution JPEG images (300 DPI)
3. OCR extraction using AWS Bedrock multimodal capabilities
4. Entity extraction into structured JSON saved to S3
5. Data stored in appropriate DynamoDB table based on source
6. Matching analysis across both tables with detailed reporting

## Critical Business Rules

- **Source Classification**: All trades must be classified as either BANK or COUNTERPARTY
- **Table Routing**: BANK trades → BankTradeData, COUNTERPARTY trades → CounterpartyTradeData
- **Data Integrity**: System verifies TRADE_SOURCE field matches table location
- **Primary Key**: Trade_ID is the primary key for all DynamoDB operations
- **Matching Criteria**: Trade_ID (exact), Trade_Date (±1 day), Notional (±0.01%), Counterparty (fuzzy)
