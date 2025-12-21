# Implementation Plan: Trade Extraction Agent Fix and SOP Implementation

## Overview

This implementation plan addresses the critical table routing bug in the Trade Extraction Agent and implements Strands Agent SOPs for reliable workflow execution. The plan includes fixing the source_type routing logic, implementing comprehensive validation, adding agent registry integration, and enhancing observability.

## Tasks

- [x] 1. Set up project structure and core interfaces
  - Create directory structure for trade extraction components
  - Define core data classes and interfaces (TradeExtractionRequest, TradeExtractionResponse, CanonicalTradeData)
  - Set up testing framework with Hypothesis for property-based testing
  - _Requirements: 8.1, 8.2_

- [x] 2. Implement table routing fix
  - [x] 2.1 Create TableRouter component with explicit source_type validation
    - Write TableRouter class with get_target_table() method
    - Implement proper error handling for invalid source_type values
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 Write property test for table routing correctness
    - **Property 1: Table Routing Correctness**
    - **Validates: Requirements 1.1, 1.2**

  - [x] 2.3 Write property test for source type validation
    - **Property 2: Source Type Validation**
    - **Validates: Requirements 1.3, 1.4**

- [x] 3. Implement Strands Agent SOP integration
  - [x] 3.1 Create SOP definition document
    - Write trade_extraction_sop.md with RFC 2119 keywords
    - Define workflow steps for request validation, extraction, validation, routing, and audit
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

  - [x] 3.2 Implement SOP workflow engine integration
    - Integrate Strands Agent SOP execution engine
    - Implement progress tracking and logging for each workflow step
    - _Requirements: 2.4, 2.6_

  - [x] 3.3 Write property test for workflow step logging
    - **Property 3: Workflow Step Logging**
    - **Validates: Requirements 2.4, 2.6**

- [x] 4. Implement data validation and normalization
  - [x] 4.1 Create TradeDataValidator component
    - Implement validate_and_normalize() method with required field checking
    - Add currency code normalization to ISO 4217 standard
    - Add date format validation and conversion to ISO 8601
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 4.2 Write property tests for data validation
    - **Property 8: Data Schema Validation**
    - **Property 9: Required Field Validation**
    - **Property 10: Currency Code Normalization**
    - **Property 11: Date Format Normalization**
    - **Property 12: Validation Error Handling**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 5. Checkpoint - Ensure core components pass tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement agent registry integration
  - [x] 6.1 Create agent registration script
    - Write register_trade_extraction_agent() function
    - Implement DynamoDB AgentRegistry table integration
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 6.2 Write property test for agent registration completeness
    - **Property 4: Agent Registration Completeness**
    - **Validates: Requirements 3.2**

- [x] 7. Implement HTTP request/response handling
  - [x] 7.1 Create HTTP interface for trade_matching_swarm_agentcore_http integration
    - Implement request parsing and validation
    - Implement standardized response formatting
    - Add correlation_id propagation throughout the system
    - _Requirements: 4.1, 4.2, 4.4_

  - [x] 7.2 Write property tests for HTTP processing
    - **Property 5: HTTP Request Processing**
    - **Property 7: Correlation ID Propagation**
    - **Validates: Requirements 4.1, 4.2, 4.4**

- [x] 8. Implement observability and metrics
  - [x] 8.1 Add CloudWatch metrics emission
    - Implement metrics for successful/failed extractions and processing time
    - Add CloudWatch event emission for successful extractions
    - _Requirements: 4.3, 6.3_

  - [x] 8.2 Implement audit logging and processing history
    - Add database operation logging with correlation_id
    - Implement audit trail creation linking source documents to extracted data
    - Add processing history storage queryable by correlation_id
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [ ] 8.3 Write property tests for observability
    - **Property 6: Metrics Emission**
    - **Property 13: Database Operation Logging**
    - **Property 14: Audit Trail Creation**
    - **Property 15: CloudWatch Event Emission**
    - **Property 16: Processing History Storage**
    - **Validates: Requirements 4.3, 6.1, 6.2, 6.3, 6.4, 6.5**

- [x] 9. Implement serialization and validation
  - [x] 9.1 Add request/response serialization
    - Implement JSON serialization/deserialization for TradeExtractionRequest
    - Implement JSON serialization/deserialization for TradeExtractionResponse
    - Add request field validation before processing
    - Add structured error response formatting
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ] 9.2 Write property tests for serialization
    - **Property 17: Request Serialization Round-Trip**
    - **Property 18: Response Serialization Round-Trip**
    - **Property 19: Request Field Validation**
    - **Property 20: Structured Error Response Format**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [x] 10. Integration and wiring
  - [x] 10.1 Wire all components together in main agent
    - Integrate TableRouter, TradeDataValidator, and SOP workflow engine
    - Implement complete trade extraction pipeline with proper error handling
    - Add retry configuration and exponential backoff logic
    - _Requirements: All requirements integration_

  - [ ] 10.2 Write integration tests
    - Test end-to-end SOP workflow execution
    - Test HTTP request/response handling with mock trade_matching_swarm_agentcore_http
    - Test database connectivity and table access
    - _Requirements: All requirements integration_

- [x] 11. Deployment preparation
  - [x] 11.1 Create deployment scripts and configuration
    - Create simple AgentCore deployment script (deploy.sh)
    - AgentCore automatically handles IAM role creation
    - Create agent registration deployment script
    - _Requirements: 3.5, 7.4_

  - [x] 11.2 Write deployment validation tests
    - Test agent registration in DynamoDB
    - Test integration with existing HTTP orchestrator
    - Validate AgentCore runtime status and logging
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Most core components have been implemented and tested
- The main agent uses LLM-centric design with Strands SDK
- Property-based tests exist for table routing, data validation, SOP workflow, HTTP interface, and agent registry
- Remaining tasks focus on completing property tests for observability and serialization, integration tests, and deployment preparation
- The implementation maintains compatibility with existing trade_matching_swarm_agentcore_http orchestrator
- **Deployment simplified**: AgentCore automatically handles IAM role creation, so no CloudFormation template needed
- All AWS resources (S3, DynamoDB, etc.) already exist in the system