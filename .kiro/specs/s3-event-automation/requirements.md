# Requirements Document

## Introduction

This feature implements automated agent invocation when trade confirmation PDF files are uploaded to S3. Currently, the system requires manual triggering of the trade processing pipeline. This feature will create an event-driven architecture where uploading a PDF to `s3://trade-matching-system-agentcore-production/BANK/` or `s3://trade-matching-system-agentcore-production/COUNTERPARTY/` automatically triggers the HTTP Orchestrator AgentCore Runtime, which coordinates the full trade processing pipeline. No changes will be made to the existing production agents.

## Glossary

- **S3_Event_Processor**: An AWS Lambda function that receives S3 event notifications and invokes the HTTP Orchestrator AgentCore Runtime
- **HTTP_Orchestrator**: The AgentCore Runtime that coordinates all trade processing agents via HTTP calls (ARN: `arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_swarm_agentcore_http-PJeubFHvY3`)
- **Trade_Confirmation_PDF**: A PDF document containing OTC derivative trade details from either a bank or counterparty
- **Source_Type**: Classification of the trade document origin, either "BANK" or "COUNTERPARTY"
- **Correlation_ID**: A unique identifier used to trace a document through the entire processing pipeline
- **Event_Payload**: The structured JSON payload sent to the HTTP Orchestrator containing document metadata

## Requirements

### Requirement 1

**User Story:** As a trade operations user, I want PDF files uploaded to S3 to automatically trigger processing, so that I don't need to manually invoke agents for each document.

#### Acceptance Criteria

1. WHEN a PDF file is uploaded to `s3://trade-matching-system-agentcore-production/BANK/` THEN the S3_Event_Processor SHALL invoke the HTTP_Orchestrator with source_type set to "BANK"
2. WHEN a PDF file is uploaded to `s3://trade-matching-system-agentcore-production/COUNTERPARTY/` THEN the S3_Event_Processor SHALL invoke the HTTP_Orchestrator with source_type set to "COUNTERPARTY"
3. WHEN the S3_Event_Processor invokes the HTTP_Orchestrator THEN the Event_Payload SHALL include document_id, document_path, source_type, correlation_id, and upload_timestamp
4. WHEN a non-PDF file is uploaded to monitored folders THEN the S3_Event_Processor SHALL ignore the event and not invoke the HTTP_Orchestrator

### Requirement 2

**User Story:** As a system administrator, I want the S3 event processor to handle errors gracefully, so that failed processing attempts don't block subsequent uploads.

#### Acceptance Criteria

1. WHEN the S3_Event_Processor fails to invoke the HTTP_Orchestrator THEN the S3_Event_Processor SHALL log the error with full context including bucket, key, and error details
2. WHEN the S3_Event_Processor encounters an invalid S3 event format THEN the S3_Event_Processor SHALL log a warning and skip processing without raising an exception
3. WHEN the HTTP_Orchestrator is unavailable THEN the S3_Event_Processor SHALL retry up to 3 times with exponential backoff before failing
4. IF the S3_Event_Processor fails after all retries THEN the Lambda function SHALL return an error response to trigger Lambda's built-in retry mechanism

### Requirement 3

**User Story:** As a DevOps engineer, I want the Lambda function to be properly configured with appropriate permissions and resources, so that it can reliably process S3 events.

#### Acceptance Criteria

1. THE S3_Event_Processor Lambda function SHALL have IAM permissions to read from the S3 bucket and invoke the HTTP_Orchestrator AgentCore Runtime
2. THE S3_Event_Processor Lambda function SHALL have a timeout of 60 seconds to handle AgentCore invocation delays
3. THE S3_Event_Processor Lambda function SHALL have 256 MB of memory allocated for efficient execution
4. THE S3 bucket notification configuration SHALL filter events to only trigger on `.pdf` file uploads in `BANK/` and `COUNTERPARTY/` folders

### Requirement 4

**User Story:** As a compliance officer, I want all document processing events to be traceable, so that I can audit the complete processing history.

#### Acceptance Criteria

1. WHEN the S3_Event_Processor processes an event THEN the S3_Event_Processor SHALL generate a unique correlation_id in the format `corr_{12-character-hex}`
2. WHEN the S3_Event_Processor invokes the HTTP_Orchestrator THEN the S3_Event_Processor SHALL log the correlation_id, document_id, source_type, and runtime ARN
3. WHEN the S3_Event_Processor completes processing THEN the S3_Event_Processor SHALL emit CloudWatch metrics for successful and failed event processing

### Requirement 5

**User Story:** As a developer, I want the event payload to follow a standardized format, so that the HTTP Orchestrator can reliably parse the invocation.

#### Acceptance Criteria

1. THE Event_Payload SHALL include fields: document_id, document_path, source_type, correlation_id, file_size_bytes, and upload_timestamp
2. THE Event_Payload document_path field SHALL be the full S3 URI (e.g., `s3://trade-matching-system-agentcore-production/BANK/trade.pdf`)
3. THE Event_Payload source_type field SHALL be either "BANK" or "COUNTERPARTY" based on the S3 key prefix

### Requirement 6

**User Story:** As a developer, I want to serialize and deserialize the Event_Payload to and from JSON, so that I can validate message integrity.

#### Acceptance Criteria

1. WHEN an Event_Payload is serialized to JSON THEN deserializing the JSON SHALL produce an equivalent Event_Payload object
2. WHEN an Event_Payload is created THEN the S3_Event_Processor SHALL validate all required fields are present before invocation
