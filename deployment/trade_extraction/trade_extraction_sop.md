# Trade Extraction Agent Standard Operating Procedure (SOP)

## Overview

This Standard Operating Procedure defines the workflow for the Trade Extraction Agent using RFC 2119 keywords to ensure reliable and consistent trade data extraction from PDF documents.

## Workflow Steps

### 1. Request Validation

The agent **MUST** validate all incoming requests before processing:

- The agent **MUST** verify that `document_path` is a valid S3 URI
- The agent **MUST** verify that `source_type` is either "BANK" or "COUNTERPARTY"
- The agent **MUST** verify that `correlation_id` follows the format `corr_[a-f0-9]{12}`
- The agent **SHOULD** log validation results with correlation_id for tracing
- If validation fails, the agent **MUST** return an error response and **MUST NOT** proceed

### 2. Document Retrieval

The agent **MUST** retrieve the PDF document from S3:

- The agent **MUST** use the provided S3 URI to download the document
- The agent **SHOULD** verify document accessibility before processing
- The agent **MUST** handle S3 access errors gracefully
- The agent **SHOULD** log document retrieval status with correlation_id

### 3. Trade Data Extraction

The agent **MUST** extract structured trade data using LLM processing:

- The agent **MUST** use Amazon Nova Pro model for document processing
- The agent **MUST** extract all required trade fields (trade_id, counterparty, notional_amount, currency, trade_date, product_type)
- The agent **MAY** extract optional fields (maturity_date) when available
- The agent **MUST** handle extraction failures and provide meaningful error messages
- The agent **SHOULD** log extraction progress with correlation_id

### 4. Data Validation and Normalization

The agent **MUST** validate and normalize extracted data:

- The agent **MUST** validate that all required fields are present
- The agent **MUST** normalize currency codes to ISO 4217 standard
- The agent **MUST** convert dates to ISO 8601 format
- The agent **MUST** validate notional amounts are positive numbers
- The agent **SHOULD** log validation results with correlation_id
- If validation fails, the agent **MUST** return an error response

### 5. Table Routing

The agent **MUST** route data to the correct DynamoDB table:

- The agent **MUST** use the TableRouter component for routing decisions
- The agent **MUST** route BANK source_type to BankTradeData table
- The agent **MUST** route COUNTERPARTY source_type to CounterpartyTradeData table
- The agent **MUST** handle routing errors gracefully
- The agent **SHOULD** log routing decisions with correlation_id

### 6. Data Storage

The agent **MUST** store validated trade data in DynamoDB:

- The agent **MUST** use the table determined by the routing step
- The agent **MUST** include correlation_id in stored data for tracing
- The agent **MUST** handle database errors gracefully
- The agent **SHOULD** log storage operations with correlation_id

### 7. Audit Trail Creation

The agent **MUST** create comprehensive audit trails:

- The agent **MUST** log all workflow steps with timestamps
- The agent **MUST** link source documents to extracted data
- The agent **MUST** record processing history queryable by correlation_id
- The agent **SHOULD** emit CloudWatch events for successful extractions

### 8. Response Generation

The agent **MUST** generate standardized responses:

- The agent **MUST** include success status in all responses
- The agent **MUST** include correlation_id in all responses
- The agent **MUST** include processing time metrics
- The agent **SHOULD** include extracted data in successful responses
- The agent **MUST** include error messages in failed responses

## Error Handling Requirements

- The agent **MUST** handle all exceptions gracefully without crashing
- The agent **MUST** provide descriptive error messages for all failure modes
- The agent **SHOULD** implement retry logic with exponential backoff for transient failures
- The agent **MUST** log all errors with correlation_id for debugging

## Observability Requirements

- The agent **MUST** emit CloudWatch metrics for successful/failed extractions
- The agent **MUST** emit CloudWatch metrics for processing time
- The agent **SHOULD** emit custom metrics for data quality indicators
- The agent **MUST** log all operations with structured logging including correlation_id

## Compliance Requirements

- The agent **MUST** follow all data privacy and security requirements
- The agent **SHOULD** implement appropriate access controls for sensitive data
- The agent **MUST** ensure audit trails are tamper-evident
- The agent **SHOULD** implement data retention policies as required

## Performance Requirements

- The agent **SHOULD** complete processing within 30 seconds for typical documents
- The agent **MUST** handle concurrent requests efficiently
- The agent **SHOULD** optimize memory usage for large documents
- The agent **MAY** implement caching for frequently accessed data

## Version Control

- **SOP Version**: 1.0.0
- **Last Updated**: 2024-12-20
- **Next Review**: 2025-03-20
- **Approved By**: System Architecture Team