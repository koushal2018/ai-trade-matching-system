# Requirements Document

## Introduction

This feature addresses critical issues with the Trade Extraction Agent in the AI Trade Matching System. The agent currently has a bug where it incorrectly updates the Counterparty table when attempting to update trade details, leading to data integrity issues. Additionally, this feature implements Strands Agent SOPs (Standard Operating Procedures) to ensure reliable, deterministic workflow execution, and includes proper agent registration and integration with the existing system architecture.

## Glossary

- **Trade_Extraction_Agent**: The AI agent responsible for extracting structured trade data from PDF documents using LLM processing
- **Strands_Agent_SOP**: A standardized markdown format for defining AI agent workflows in natural language that provides structured guidance while maintaining flexibility
- **DynamoDB_Model_Registry**: The AgentRegistry table that tracks all deployed agents and their metadata
- **HTTP_Orchestrator**: The AgentCore Runtime that coordinates all trade processing agents via HTTP calls
- **Agent_Swarm**: The collection of specialized agents working together in the trade matching pipeline
- **BankTradeData_Table**: DynamoDB table storing trade data extracted from bank confirmation PDFs
- **CounterpartyTradeData_Table**: DynamoDB table storing trade data extracted from counterparty confirmation PDFs
- **Source_Type**: Classification indicating whether trade data originates from "BANK" or "COUNTERPARTY"
- **Canonical_Trade_Data**: Standardized JSON structure containing extracted trade information

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want the Trade Extraction Agent to correctly route trade data to the appropriate DynamoDB table, so that bank and counterparty data maintain proper separation and integrity.

#### Acceptance Criteria

1. WHEN the Trade_Extraction_Agent processes a document with source_type "BANK" THEN the agent SHALL store the extracted trade data in the BankTradeData_Table
2. WHEN the Trade_Extraction_Agent processes a document with source_type "COUNTERPARTY" THEN the agent SHALL store the extracted trade data in the CounterpartyTradeData_Table
3. WHEN the Trade_Extraction_Agent determines the target table THEN the agent SHALL validate the source_type parameter before any database operations
4. WHEN the Trade_Extraction_Agent encounters an invalid source_type THEN the agent SHALL log an error and return a failure response without modifying any database tables

### Requirement 2

**User Story:** As a developer, I want the Trade Extraction Agent to implement Strands Agent SOPs, so that the workflow execution is reliable, deterministic, and follows standardized procedures.

#### Acceptance Criteria

1. THE Trade_Extraction_Agent SHALL implement a Strands Agent SOP that defines the complete trade extraction workflow using RFC 2119 keywords (MUST, SHOULD, MAY)
2. THE Trade_Extraction_Agent SOP SHALL include structured steps for PDF text extraction, data parsing, validation, and database storage
3. THE Trade_Extraction_Agent SOP SHALL define parameterized inputs for document_path, source_type, and correlation_id
4. THE Trade_Extraction_Agent SOP SHALL include progress tracking that logs each workflow step completion
5. THE Trade_Extraction_Agent SOP SHALL define error handling procedures for each workflow step
6. WHEN the Trade_Extraction_Agent executes the SOP THEN the agent SHALL follow the defined workflow steps in sequence and log progress at each stage

### Requirement 3

**User Story:** As a system architect, I want the Trade Extraction Agent to be properly registered in the DynamoDB Model Registry, so that the system can track agent metadata and enable proper orchestration.

#### Acceptance Criteria

1. THE Trade_Extraction_Agent SHALL be registered in the AgentRegistry DynamoDB table with agent_id "trade-extraction-agent"
2. THE agent registration SHALL include fields: agent_id, agent_name, agent_type, runtime_arn, status, version, created_at, updated_at, and capabilities
3. THE agent registration SHALL specify agent_type as "trade-extraction" and status as "active"
4. THE agent registration SHALL include capabilities list containing "pdf-processing", "llm-extraction", "data-validation", and "database-storage"
5. WHEN the agent is deployed THEN the registration script SHALL update the AgentRegistry table with current agent metadata

### Requirement 4

**User Story:** As a system integrator, I want the updated Trade Extraction Agent to properly integrate with the Swarm and Orchestrator Agent, so that the complete trade processing pipeline functions correctly.

#### Acceptance Criteria

1. THE Trade_Extraction_Agent SHALL accept HTTP requests from the HTTP_Orchestrator with the standard payload format
2. THE Trade_Extraction_Agent SHALL return standardized HTTP responses that the HTTP_Orchestrator can parse and route
3. THE Trade_Extraction_Agent SHALL emit CloudWatch metrics for successful extractions, failed extractions, and processing time
4. THE Trade_Extraction_Agent SHALL integrate with the existing correlation_id tracing system for end-to-end observability
5. WHEN the HTTP_Orchestrator invokes the Trade_Extraction_Agent THEN the agent SHALL process the request and return results within the 300-second timeout

### Requirement 5

**User Story:** As a data analyst, I want the Trade Extraction Agent to validate extracted trade data against expected schemas, so that downstream processing receives consistent, high-quality data.

#### Acceptance Criteria

1. THE Trade_Extraction_Agent SHALL validate extracted trade data against the Canonical_Trade_Data schema before database storage
2. THE Trade_Extraction_Agent SHALL reject incomplete trade records that are missing required fields (trade_id, counterparty, notional_amount, trade_date)
3. THE Trade_Extraction_Agent SHALL normalize currency codes to ISO 4217 standard format
4. THE Trade_Extraction_Agent SHALL validate date formats and convert them to ISO 8601 standard
5. WHEN validation fails THEN the agent SHALL log the validation errors and return a structured error response

### Requirement 6

**User Story:** As a compliance officer, I want the Trade Extraction Agent to maintain detailed audit logs, so that I can trace all data processing activities for regulatory compliance.

#### Acceptance Criteria

1. THE Trade_Extraction_Agent SHALL log all database operations with correlation_id, table_name, operation_type, and timestamp
2. THE Trade_Extraction_Agent SHALL log the original PDF document path and extracted trade data for audit purposes
3. THE Trade_Extraction_Agent SHALL emit CloudWatch events for successful extractions that include document metadata and processing metrics
4. THE Trade_Extraction_Agent SHALL maintain processing history that can be queried by correlation_id
5. WHEN processing completes THEN the agent SHALL create an audit record linking the source document to the extracted data

### Requirement 7

**User Story:** As a DevOps engineer, I want the Trade Extraction Agent deployment to be automated and include proper testing, so that updates can be deployed reliably without manual intervention.

#### Acceptance Criteria

1. THE deployment process SHALL include automated testing of the SOP workflow execution
2. THE deployment process SHALL validate database connectivity and table access permissions
3. THE deployment process SHALL verify integration with the HTTP_Orchestrator through end-to-end testing
4. THE deployment process SHALL update the AgentRegistry with the new agent version and deployment timestamp
5. WHEN deployment completes THEN the system SHALL run smoke tests to verify the agent responds correctly to sample requests

### Requirement 8

**User Story:** As a developer, I want to serialize and deserialize trade extraction requests and responses, so that I can validate message integrity and enable proper error handling.

#### Acceptance Criteria

1. WHEN a trade extraction request is serialized to JSON THEN deserializing the JSON SHALL produce an equivalent request object
2. WHEN a trade extraction response is serialized to JSON THEN deserializing the JSON SHALL produce an equivalent response object
3. THE Trade_Extraction_Agent SHALL validate all required fields are present in incoming requests before processing
4. THE Trade_Extraction_Agent SHALL return structured error responses that can be parsed by the HTTP_Orchestrator