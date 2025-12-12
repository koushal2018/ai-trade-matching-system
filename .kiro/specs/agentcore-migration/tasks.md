# Implementation Plan

## Overview

This implementation plan breaks down the AgentCore migration into discrete, manageable tasks. Each task builds incrementally on previous work, with checkpoints to ensure quality and correctness.

## Task List

- [x] 1. Set up AWS infrastructure in us-east-1
- [x] 1.1 Create S3 bucket for trade documents and outputs
  - Create bucket with encryption and versioning enabled
  - Set up folder structure: BANK/, COUNTERPARTY/, extracted/, reports/
  - Configure lifecycle policies for cost optimization
  - _Requirements: 14.1, 14.4_

- [x] 1.2 Create DynamoDB tables in us-east-1
  - Create BankTradeData table with Trade_ID as primary key
  - Create CounterpartyTradeData table with Trade_ID as primary key
  - Create ExceptionsTable for exception tracking
  - Create AgentRegistry table for agent registration
  - Configure on-demand billing mode
  - _Requirements: 14.1, 14.3_

- [x] 1.3 Set up SQS queues for event-driven architecture
  - Create document-upload-events queue (FIFO)
  - Create extraction-events queue (Standard)
  - Create matching-events queue (Standard)
  - Create exception-events queue (Standard)
  - Create hitl-review-queue (FIFO)
  - Create ops-desk-queue, senior-ops-queue, compliance-queue, engineering-queue
  - Create orchestrator-monitoring-queue (fanout from all queues)
  - Configure dead letter queues for all queues
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 1.4 Configure IAM roles and policies
  - Create AgentCore Runtime execution role
  - Create AgentCore Gateway role
  - Create Lambda execution roles for agents
  - Configure least-privilege policies for each agent
  - Set up cross-service permissions (S3, DynamoDB, SQS, Bedrock)
  - _Requirements: 17.1, 17.2_

- [x] 1.5 Set up AgentCore Memory resources
  - Create memory resource with semantic strategy for trade patterns
  - Create memory resource with event strategy for processing history
  - Create memory resource for exception patterns and RL policies
  - Configure 90-day event retention
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 1.6 Set up AgentCore Gateway with MCP targets
  - Create MCP Gateway for DynamoDB operations
  - Create MCP Gateway for S3 operations
  - Add Lambda target for custom operations
  - Configure authentication with AgentCore Identity
  - _Requirements: 13.1, 13.2, 13.3_

- [x] 1.7 Configure AgentCore Observability
  - Enable distributed tracing for all agents
  - Set up metrics collection (latency, throughput, error rates)
  - Configure anomaly detection rules
  - Create alerting rules for critical events
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [x] 1.8 Set up AgentCore Identity with Cognito
  - Create Cognito User Pool
  - Configure OAuth2 client credentials flow
  - Set up user roles (Admin, Operator, Auditor)
  - Configure MFA for admin users
  - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [x] 2. Implement core data models and schemas
- [x] 2.1 Create canonical adapter output schema
  - Define CanonicalAdapterOutput Pydantic model
  - Support adapter_type: PDF, CHAT, EMAIL, VOICE
  - Include metadata fields for extensibility
  - Write validation logic
  - _Requirements: 3.2, 5.1, 5.2, 5.3_

- [x] 2.2 Create canonical trade model
  - Define CanonicalTradeModel with mandatory and optional fields
  - Implement to_dynamodb_format() method
  - Add field validation rules
  - Support 30+ trade fields
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 2.3 Create matching result models
  - Define MatchingResult model with classification enum
  - Define MatchClassification enum (MATCHED, PROBABLE_MATCH, etc.)
  - Add match_score field (0.0 to 1.0)
  - Include reason_codes list
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 2.4 Create exception and triage models
  - Define ExceptionRecord model
  - Define TriageResult model with severity and routing
  - Define TriageClassification enum
  - Add severity_score field
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2.5 Create audit trail models
  - Define AuditRecord model with immutable_hash
  - Implement SHA-256 hash computation
  - Add tamper-evidence verification
  - Support standard export formats (JSON, CSV, XML)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 2.6 Create event message schemas
  - Define StandardEventMessage base model
  - Create event schemas for all event types in EventTaxonomy
  - Add correlation_id for distributed tracing
  - Implement event serialization/deserialization
  - _Requirements: 3.1, 12.4_

- [x] 2.7 Write property test for canonical models
  - **Property 17: Trade source classification validity**
  - **Validates: Requirements 6.2**

- [ ] 2.8 Write property test for audit trail immutability
  - **Property 37: Audit records are immutable**
  - **Validates: Requirements 10.4**

- [x] 3. Implement registry and taxonomy system
- [x] 3.1 Create agent registry implementation
  - Implement AgentRegistryEntry model
  - Create register_agent() function
  - Create update_agent_status() function
  - Create get_agent_by_capability() function
  - Store in DynamoDB AgentRegistry table
  - _Requirements: 4.1, 4.3_

- [x] 3.2 Create workflow taxonomy configuration
  - Define hierarchical workflow structure
  - Create JSON configuration file
  - Store in S3 config/taxonomy.json
  - Implement taxonomy loader
  - _Requirements: 3.1_

- [x] 3.3 Create event taxonomy
  - Define EventTaxonomy class with all event types
  - Document event schemas for each type
  - Create event validation functions
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.4 Create reason code taxonomy
  - Define ReasonCodeTaxonomy class
  - Document all reason codes with descriptions
  - Create reason code classification logic
  - _Requirements: 7.2, 7.5, 8.1_

- [x] 4. Implement PDF Adapter Agent
- [x] 4.1 Create PDF to image conversion tool
  - Implement pdf_to_image_tool using poppler
  - Ensure 300 DPI output
  - Save images to S3 and local storage
  - Handle multi-page PDFs
  - _Requirements: 5.1, 18.1_

- [ ] 4.2 Write property test for PDF DPI
  - **Property 11: PDF conversion maintains 300 DPI**
  - **Validates: Requirements 5.1, 18.1**

- [x] 4.3 Create OCR extraction tool
  - Implement ocr_tool using AWS Bedrock Claude Sonnet 4
  - Process all pages from PDF
  - Combine text from multiple pages
  - Save extracted text to S3
  - _Requirements: 5.2, 5.3_

- [ ] 4.4 Write property test for OCR completeness
  - **Property 12: OCR extraction completeness**
  - **Validates: Requirements 5.2**

- [x] 4.5 Implement PDF Adapter Agent with event-driven architecture
  - Create BedrockAgentCoreApp wrapper
  - Subscribe to document-upload-events SQS queue
  - Implement canonical output schema generation
  - Publish PDF_PROCESSED events to extraction-events queue
  - Handle errors and publish to exception-events queue
  - Register agent in AgentRegistry
  - _Requirements: 3.2, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 4.6 Write property test for PDF processing errors
  - **Property 14: PDF processing errors reported**
  - **Validates: Requirements 5.4**

- [ ] 4.7 Write property test for canonical output schema
  - **Property 13: OCR results saved to S3**
  - **Validates: Requirements 5.3**

- [x] 5. Checkpoint - Ensure PDF Adapter tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Trade Data Extraction Agent
- [x] 6.1 Create LLM extraction tool
  - Implement llm_extraction_tool using AWS Bedrock
  - Extract all required trade fields
  - Handle optional fields gracefully
  - Validate extracted data against canonical trade model
  - _Requirements: 6.1, 6.2_

- [ ] 6.2 Write property test for field extraction
  - **Property 16: All trade fields extracted**
  - **Validates: Requirements 6.1**

- [x] 6.3 Create trade source classification logic
  - Implement classify_trade_source() function
  - Identify BANK vs COUNTERPARTY indicators
  - Use LLM for ambiguous cases
  - Validate classification result
  - _Requirements: 6.2_

- [ ] 6.4 Write property test for trade routing
  - **Property 19: Trade routing to correct DynamoDB table**
  - **Validates: Requirements 6.4**

- [x] 6.5 Implement Trade Data Extraction Agent with event-driven architecture
  - Create BedrockAgentCoreApp wrapper
  - Subscribe to extraction-events SQS queue
  - Read canonical adapter output from S3
  - Extract trade data using LLM
  - Store in appropriate DynamoDB table via boto3
  - Publish TRADE_EXTRACTED events to matching-events queue
  - Handle errors and publish to exception-events queue
  - Register agent in AgentRegistry
  - _Requirements: 3.3, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 6.6 Write property test for extraction errors
  - **Property 20: Extraction errors include context**
  - **Validates: Requirements 6.5**

- [x] 7. Checkpoint - Ensure Trade Extraction tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Trade Matching Agent with scoring
- [x] 8.1 Create fuzzy matching logic
  - Implement fuzzy_match() function with tolerances
  - Trade_Date: ±1 business day
  - Notional: ±0.01%
  - Counterparty: fuzzy string match
  - Return match result with differences
  - _Requirements: 7.1, 18.3_

- [ ] 8.2 Write property test for fuzzy matching tolerances
  - **Property 21: Fuzzy matching applies tolerances**
  - **Validates: Requirements 7.1, 18.3**

- [x] 8.3 Create match scoring system
  - Implement compute_match_score() function
  - Use weighted field comparisons
  - Return score 0.0 to 1.0
  - Include confidence metrics
  - _Requirements: 7.1, 7.2_

- [ ] 8.4 Write property test for match scoring
  - **Property 22: Match classification validity**
  - **Validates: Requirements 7.2**

- [x] 8.5 Create classification logic
  - Implement classify_match() function
  - Use score thresholds: ≥0.85 AUTO_MATCH, 0.70-0.84 ESCALATE, <0.70 EXCEPTION
  - Generate reason codes
  - Determine decision status
  - _Requirements: 7.2, 7.3_

- [x] 8.6 Create report generation
  - Implement generate_report() function
  - Include summary statistics, matched trades, breaks, data errors
  - Generate markdown format
  - Save to S3
  - _Requirements: 7.3, 7.4, 18.4_

- [ ] 8.7 Write property test for report completeness
  - **Property 23: Matching reports are complete**
  - **Validates: Requirements 7.3, 18.4**

- [x] 8.8 Implement Trade Matching Agent with event-driven architecture
  - Create BedrockAgentCoreApp wrapper
  - Subscribe to matching-events SQS queue
  - Retrieve trades from both DynamoDB tables via boto3
  - Perform fuzzy matching and compute scores
  - Classify results and determine decision status
  - Generate and save reports to S3
  - Publish results to hitl-review-queue or exception-events queue based on decision
  - Register agent in AgentRegistry
  - _Requirements: 3.4, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 8.9 Write property test for misplaced trades
  - **Property 25: Misplaced trades flagged as DATA_ERROR**
  - **Validates: Requirements 7.5**

- [x] 9. Checkpoint - Ensure Trade Matching tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Exception Management Agent with RL
- [x] 10.1 Create exception classification logic
  - Implement classify_exception() function
  - Use reason codes for classification
  - Support all exception types
  - _Requirements: 8.1_

- [ ] 10.2 Write property test for error logging
  - **Property 26: All errors logged with context**
  - **Validates: Requirements 8.1**

- [x] 10.3 Create severity scoring system
  - Implement compute_severity_score() function
  - Use base scores for reason codes
  - Adjust based on match scores
  - Integrate historical patterns from RL
  - Return score 0.0 to 1.0
  - _Requirements: 8.1, 8.2_

- [x] 10.4 Create triage system
  - Implement triage_exception() function
  - Determine severity (LOW, MEDIUM, HIGH, CRITICAL)
  - Determine routing (AUTO_RESOLVE, OPS_DESK, SENIOR_OPS, COMPLIANCE, ENGINEERING)
  - Set priority and SLA hours
  - Integrate RL policy for routing decisions
  - _Requirements: 8.2, 8.3_

- [x] 10.5 Create delegation system
  - Implement delegate_exception() function
  - Assign to appropriate handler based on routing
  - Create tracking record with SLA deadline
  - Send notifications
  - _Requirements: 8.3, 8.4_

- [x] 10.6 Implement RL exception handler
  - Create RLExceptionHandler class
  - Implement record_episode() for state-action pairs
  - Implement update_with_resolution() for reward assignment
  - Implement compute_reward() function
  - Integrate supervised learning from human decisions
  - Store RL model in AgentCore Memory
  - _Requirements: 8.2, 8.3, 8.4, 8.5_

- [ ] 10.7 Write property test for exponential backoff
  - **Property 27: Exponential backoff for transient errors**
  - **Validates: Requirements 8.2**

- [x] 10.8 Implement Exception Management Agent with event-driven architecture
  - Create BedrockAgentCoreApp wrapper
  - Subscribe to exception-events SQS queue
  - Classify and score exceptions
  - Triage and delegate to appropriate queues
  - Track exception lifecycle in ExceptionsTable
  - Update RL model with resolution outcomes
  - Register agent in AgentRegistry
  - _Requirements: 3.5, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 10.9 Write property test for error pattern detection
  - **Property 30: Error pattern detection triggers alerts**
  - **Validates: Requirements 8.5**

- [x] 11. Checkpoint - Ensure Exception Management tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement Orchestrator Agent
- [x] 12.1 Create SLA monitoring tools
  - Implement sla_monitor_tool
  - Track processing time, throughput, error rates
  - Compare against SLA targets from AgentRegistry
  - Detect SLA violations
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 12.2 Create compliance checking tools
  - Implement compliance_checker_tool
  - Validate data integrity (TRADE_SOURCE in correct tables)
  - Check regulatory requirements
  - Detect compliance violations
  - _Requirements: 4.1, 4.2_

- [x] 12.3 Create control command tools
  - Implement control_command_tool
  - Support pause/resume processing
  - Support priority adjustment
  - Support escalation triggers
  - _Requirements: 4.1, 4.2_

- [x] 12.4 Implement Orchestrator Agent with event-driven architecture
  - Create BedrockAgentCoreApp wrapper
  - Subscribe to orchestrator-monitoring-queue (fanout from all queues)
  - Monitor SLAs for all agents
  - Enforce compliance checkpoints
  - Issue control commands when needed
  - Aggregate metrics from all agents
  - Register agent in AgentRegistry
  - _Requirements: 3.1, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 12.5 Write property test for orchestrator coordination
  - **Property 9: Orchestrator coordinates handoffs**
  - **Validates: Requirements 4.4**

- [ ] 12.6 Write property test for metrics aggregation
  - **Property 10: Orchestrator aggregates metrics**
  - **Validates: Requirements 4.5**

- [x] 13. Checkpoint - Ensure Orchestrator tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Deploy agents to AgentCore Runtime
- [x] 14.1 Prepare agent deployment packages
  - Create requirements.txt for each agent
  - Include bedrock-agentcore, strands-agents, strands-agents-tools
  - Ensure all dependencies are specified
  - Create agentcore.yaml configuration files
  - Create deploy.sh scripts for each agent
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 14.2 Deploy PDF Adapter Agent
  - Run agentcore configure for PDF Adapter
  - Set runtime to PYTHON_3_11
  - Configure memory integration
  - Run agentcore launch
  - Test with agentcore invoke
  - _Requirements: 2.1, 2.2, 3.2_

- [x] 14.3 Deploy Trade Data Extraction Agent
  - Run agentcore configure for Trade Extraction
  - Configure memory integration
  - Run agentcore launch
  - Test with agentcore invoke
  - _Requirements: 2.1, 2.2, 3.3_

- [x] 14.4 Deploy Trade Matching Agent
  - Run agentcore configure for Trade Matching
  - Configure memory integration
  - Run agentcore launch
  - Test with agentcore invoke
  - _Requirements: 2.1, 2.2, 3.4_

- [x] 14.5 Deploy Exception Management Agent
  - Run agentcore configure for Exception Management
  - Configure memory integration
  - Run agentcore launch
  - Test with agentcore invoke
  - _Requirements: 2.1, 2.2, 3.5_

- [x] 14.6 Deploy Orchestrator Agent
  - Run agentcore configure for Orchestrator
  - Configure memory integration
  - Run agentcore launch
  - Test with agentcore invoke
  - _Requirements: 2.1, 2.2, 3.1_

- [x] 15. Checkpoint - Verify all agents deployed
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement React Web Portal
- [x] 16.1 Set up React project with TypeScript
  - Initialize React project with Create React App or Vite
  - Configure TypeScript
  - Install Material-UI or Ant Design
  - Set up React Query for data fetching
  - Install Recharts for visualizations
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 16.2 Create Dashboard component
  - Implement AgentHealthPanel showing agent status
  - Implement ProcessingMetrics showing real-time metrics
  - Implement MatchingResults showing match rates and breaks
  - Add color-coded health indicators
  - _Requirements: 9.1, 15.1, 15.2, 15.3_

- [ ] 16.3 Write unit tests for Dashboard component
  - Test agent health status display
  - Test metrics rendering
  - Test color-coded indicators

- [x] 16.4 Create HITL Panel component
  - Implement TradeComparisonCard for side-by-side trade display
  - Add approve/reject buttons
  - Implement decision submission logic
  - Show pending reviews list
  - _Requirements: 9.3, 16.1, 16.2, 16.3, 16.4_

- [ ] 16.5 Write unit tests for HITL Panel component
  - Test trade comparison display
  - Test decision submission
  - Test pending reviews list

- [x] 16.6 Create Audit Trail component
  - Implement DataGrid for audit records
  - Add filtering by date, agent, action type
  - Implement pagination
  - Add export functionality
  - _Requirements: 9.4, 10.1, 10.2, 10.3, 10.5_

- [ ] 16.7 Write unit tests for Audit Trail component
  - Test filtering logic
  - Test pagination
  - Test export functionality

- [x] 16.8 Implement WebSocket integration
  - Create WebSocket connection to backend
  - Handle AGENT_STATUS updates
  - Handle TRADE_PROCESSED updates
  - Handle HITL_REQUIRED updates
  - Implement reconnection logic
  - _Requirements: 9.2, 9.3, 15.2_

- [ ] 16.9 Write property test for WebSocket updates
  - **Property 31: Web Portal shows live progress**
  - **Validates: Requirements 9.2**

- [x] 16.10 Implement REST API integration
  - Create API client for HITL decisions
  - Create API client for audit trail queries
  - Implement JWT token handling
  - Add error handling and retries
  - _Requirements: 9.3, 9.4, 17.3_

- [ ] 16.11 Write property test for API authentication
  - **Property 54: JWT tokens validated for API calls**
  - **Validates: Requirements 17.3**

- [x] 17. Checkpoint - Ensure Web Portal tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Implement backend API for Web Portal
- [x] 18.1 Create FastAPI application
  - Set up FastAPI project structure
  - Configure CORS for React frontend
  - Set up JWT authentication middleware
  - Add request logging
  - _Requirements: 9.1, 17.2, 17.3_

- [x] 18.2 Implement WebSocket endpoint
  - Create WebSocket endpoint for real-time updates
  - Implement connection management
  - Broadcast agent status updates
  - Broadcast trade processing updates
  - Broadcast HITL requests
  - _Requirements: 9.2, 9.3_

- [x] 18.3 Implement HITL decision endpoint
  - Create POST /api/hitl/{review_id}/decision endpoint
  - Validate JWT token
  - Record decision in AgentCore Memory
  - Publish decision to SQS for agent processing
  - Update audit trail
  - _Requirements: 16.3, 16.4, 17.3_

- [x] 18.4 Implement audit trail query endpoint
  - Create GET /api/audit endpoint
  - Support filtering by date, agent, action type
  - Implement pagination
  - Support export formats (JSON, CSV, XML)
  - Validate JWT token and enforce RBAC
  - _Requirements: 10.3, 10.5, 17.4_

- [ ] 18.5 Write property test for RBAC enforcement
  - **Property 55: RBAC enforced for permissions**
  - **Validates: Requirements 17.4**

- [x] 18.6 Implement agent status endpoint
  - Create GET /api/agents/status endpoint
  - Query AgentRegistry for all agents
  - Return health status, metrics, and active tasks
  - _Requirements: 4.3, 9.1_

- [x] 19. Checkpoint - Ensure backend API tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 20. Implement AgentCore Memory integration
- [x] 20.1 Create memory storage utilities
  - Implement store_trade_pattern() function
  - Implement retrieve_similar_trades() function
  - Implement store_matching_decision() function
  - Implement store_error_pattern() function
  - Use AgentCore Memory semantic strategy
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ] 20.2 Write property test for memory storage
  - **Property 39: Trade patterns stored in memory**
  - **Validates: Requirements 11.1**

- [ ] 20.3 Write property test for memory retrieval
  - **Property 40: Historical context retrieved for similar trades**
  - **Validates: Requirements 11.2**

- [x] 20.4 Integrate memory with PDF Adapter Agent
  - Store processing history in event memory
  - Track PDF processing patterns
  - _Requirements: 11.1_

- [x] 20.5 Integrate memory with Trade Extraction Agent
  - Store extraction patterns in semantic memory
  - Retrieve similar trade patterns for context
  - _Requirements: 11.1, 11.2_

- [x] 20.6 Integrate memory with Trade Matching Agent
  - Store matching decisions in semantic memory
  - Retrieve HITL feedback for similar cases
  - _Requirements: 11.2, 11.3, 16.5_

- [ ] 20.7 Write property test for HITL decision suggestions
  - **Property 53: Similar cases suggest past decisions**
  - **Validates: Requirements 16.5**

- [x] 20.8 Integrate memory with Exception Management Agent
  - Store error patterns in event memory
  - Store RL policies in semantic memory
  - Retrieve historical error patterns
  - _Requirements: 11.4_

- [x] 21. Checkpoint - Ensure memory integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 22. Implement AgentCore Observability integration
- [x] 22.1 Add distributed tracing to all agents
  - Instrument PDF Adapter Agent with traces
  - Instrument Trade Extraction Agent with traces
  - Instrument Trade Matching Agent with traces
  - Instrument Exception Management Agent with traces
  - Instrument Orchestrator Agent with traces
  - Use correlation_id for trace propagation
  - _Requirements: 12.1, 12.4_

- [ ] 22.2 Write property test for distributed tracing
  - **Property 46: Distributed tracing spans all agents**
  - **Validates: Requirements 12.4**

- [x] 22.3 Add metrics collection to all agents
  - Track latency for each agent operation
  - Track throughput (trades processed per hour)
  - Track error rates
  - Emit metrics to AgentCore Observability
  - _Requirements: 12.2_

- [ ] 22.4 Write property test for metrics tracking
  - **Property 44: Performance metrics tracked**
  - **Validates: Requirements 12.2**

- [x] 22.5 Configure anomaly detection
  - Set up anomaly detection rules (latency > 2x baseline, error rate > 5%)
  - Configure alerts for anomalies
  - Test anomaly detection with synthetic data
  - _Requirements: 12.3_

- [x] 23. Checkpoint - Ensure observability integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 23.5. Implement AgentCore Evaluations integration
- [x] 23.5.1 Create custom evaluators for trade matching
  - Create TradeExtractionAccuracy evaluator
  - Create MatchingQuality evaluator
  - Create OCRQuality evaluator
  - Create ExceptionHandlingQuality evaluator
  - Define evaluation criteria and scoring schemas
  - _Requirements: 12.2, 18.5, 19.1, 19.2_

- [x] 23.5.2 Configure online evaluation
  - Set up continuous monitoring for live agent traffic
  - Configure sampling rules (10% of traffic)
  - Define target agents for each evaluator
  - _Requirements: 12.2, 12.3, 19.3_

- [x] 23.5.3 Set up evaluation metrics and alerting
  - Configure CloudWatch metrics namespace
  - Create alarms for quality score drops
  - Set up SNS notifications for evaluation alerts
  - _Requirements: 12.3, 19.4_

- [x] 23.5.4 Implement on-demand evaluation for testing
  - Create evaluation test harness
  - Support batch evaluation of specific interactions
  - Enable pre-deployment quality gates
  - _Requirements: 18.5, 19.5_

- [x] 23.6. Implement AgentCore Policy integration
- [x] 23.6.1 Create policy engine for trade matching
  - Set up TradeMatchingPolicyEngine
  - Configure policy validation mode
  - _Requirements: 17.1, 17.4, 20.1_

- [x] 23.6.2 Implement trade amount limit policies
  - Create Cedar policy for notional amount limits
  - Configure $100M threshold for standard processing
  - _Requirements: 17.4, 20.1_

- [x] 23.6.3 Implement role-based access control policies
  - Create senior operator approval policy
  - Create regular operator approval policy
  - Define role-based match score thresholds
  - _Requirements: 17.4, 20.2_

- [x] 23.6.4 Implement compliance control policies
  - Create restricted counterparty blocking policy
  - Create emergency shutdown policy (disabled by default)
  - _Requirements: 17.1, 17.4, 20.3, 20.4_

- [x] 23.6.5 Attach policy engine to Gateway
  - Configure policy enforcement mode (LOG_ONLY for dev, ENFORCE for prod)
  - Set up policy decision logging
  - Create policy denial alerts
  - _Requirements: 17.1, 17.4, 20.5_

- [x] 23.7. Checkpoint - Ensure Evaluations and Policy tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 24. Implement end-to-end integration tests
- [x] 24.1 Create test data generator
  - Generate synthetic trade PDFs (BANK and COUNTERPARTY)
  - Generate trades with various matching scenarios
  - Generate trades with intentional mismatches
  - _Requirements: 18.1, 18.2, 18.3_

- [ ] 24.2 Write property test for functional parity
  - **Property 1: Functional parity with CrewAI implementation**
  - **Validates: Requirements 1.5**

- [x] 24.3 Test complete workflow (PDF to matching report)
  - Upload test PDF to S3
  - Verify PDF Adapter processes it
  - Verify Trade Extraction stores data
  - Verify Trade Matching generates report
  - Verify all events published correctly
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 24.4 Test error handling and recovery
  - Simulate PDF processing errors
  - Verify Exception Management handles errors
  - Verify retry logic works correctly
  - Verify escalation to HITL
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 24.5 Test HITL workflow
  - Generate low-confidence match
  - Verify HITL request sent to Web Portal
  - Submit human decision via API
  - Verify decision recorded in memory
  - Verify processing resumes
  - _Requirements: 16.1, 16.2, 16.3, 16.4_

- [ ] 24.6 Test audit trail completeness
  - Perform various operations
  - Query audit trail
  - Verify all operations logged
  - Verify immutable hashes
  - Test export functionality
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 25. Final Checkpoint - Ensure all integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 26. Data migration from me-central-1 to us-east-1
- [x] 26.1 Export data from me-central-1
  - Export BankTradeData table
  - Export CounterpartyTradeData table
  - Export all S3 objects
  - Verify data integrity
  - _Requirements: 14.3_

- [x] 26.2 Transform data for us-east-1
  - Update region references in data
  - Update S3 paths
  - Validate data against canonical models
  - _Requirements: 14.3_

- [x] 26.3 Import data to us-east-1
  - Import to BankTradeData table
  - Import to CounterpartyTradeData table
  - Upload S3 objects
  - Verify data integrity
  - _Requirements: 14.3_

- [x] 26.4 Validate migrated data
  - Compare record counts
  - Verify data integrity
  - Test queries on migrated data
  - _Requirements: 14.3_

- [x] 27. Performance testing and optimization
- [x] 27.1 Load testing
  - Test with 100 concurrent trade processing requests
  - Measure latency, throughput, error rates
  - Verify auto-scaling works correctly
  - _Requirements: 2.2, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 27.2 Optimize agent performance
  - Identify bottlenecks from load testing
  - Optimize LLM prompts for faster extraction
  - Optimize DynamoDB queries
  - Adjust AgentCore Runtime configurations
  - _Requirements: 18.5_

- [x] 27.3 Verify 90-second processing time
  - Test end-to-end processing time
  - Ensure average time ≤ 90 seconds per trade
  - Identify and fix any performance issues
  - _Requirements: 18.5_

- [x] 28. Security testing
- [x] 28.1 Test authentication and authorization
  - Test JWT token validation
  - Test RBAC enforcement
  - Test MFA for admin users
  - Verify unauthorized access is blocked
  - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [x] 28.2 Test data encryption
  - Verify S3 encryption at rest
  - Verify DynamoDB encryption at rest
  - Verify TLS 1.3 for data in transit
  - _Requirements: 17.1_

- [x] 28.3 Test audit trail immutability
  - Attempt to modify audit records
  - Verify hash mismatch detection
  - Test tamper-evidence
  - _Requirements: 10.4_

- [x] 28.4 Penetration testing
  - Test for common vulnerabilities (OWASP Top 10)
  - Test API security
  - Test WebSocket security
  - Address any findings
  - _Requirements: 17.1, 17.2_

- [x] 29. Documentation and training
- [x] 29.1 Create user documentation
  - Write user guide for Web Portal
  - Document HITL workflow
  - Document audit trail usage
  - Create troubleshooting guide
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 29.2 Create operator documentation
  - Document agent monitoring procedures
  - Document exception handling procedures
  - Document escalation procedures
  - Create runbooks for common issues
  - _Requirements: 4.1, 4.2, 8.3_

- [x] 29.3 Create developer documentation
  - Document agent architecture
  - Document event schemas
  - Document API endpoints
  - Document deployment procedures
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 29.4 Conduct training sessions
  - Train operations team on Web Portal
  - Train operations team on exception handling
  - Train development team on agent architecture
  - Train development team on deployment procedures
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 30. Production deployment
- [x] 30.1 Prepare production environment
  - Create production AWS account/environment
  - Set up production AgentCore resources
  - Configure production monitoring and alerting
  - Set up production backups
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 30.2 Deploy to production (blue-green)
  - Deploy all agents to production AgentCore Runtime
  - Deploy Web Portal to production
  - Deploy backend API to production
  - Keep old CrewAI system running (green)
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 30.3 Gradual traffic shift
  - Route 10% of traffic to new system
  - Monitor metrics and errors
  - Route 25% of traffic to new system
  - Route 50% of traffic to new system
  - Route 100% of traffic to new system
  - _Requirements: 2.1, 2.2_

- [x] 30.4 Monitor production system
  - Monitor agent health and metrics
  - Monitor error rates and SLA compliance
  - Monitor cost and resource usage
  - Address any issues immediately
  - _Requirements: 4.1, 4.2, 4.3, 12.1, 12.2, 12.3_

- [x] 30.5 Decommission old CrewAI system
  - Verify new system is stable
  - Archive old system data
  - Shut down old system resources
  - Document lessons learned
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 32. Implement missing property-based tests
- [ ] 32.1 Set up property-based testing framework
  - Install hypothesis library for Python property testing
  - Create test generators for trade data, PDFs, and matching scenarios
  - Configure test runners with minimum 100 iterations per property
  - _Requirements: 18.5_

- [ ] 32.2 Implement core correctness properties
  - **Property 1: Functional parity with CrewAI implementation**
  - **Property 17: Trade source classification validity**
  - **Property 37: Audit records are immutable**
  - **Property 11: PDF conversion maintains 300 DPI**
  - **Property 21: Fuzzy matching applies tolerances**
  - **Validates: Requirements 1.5, 6.2, 10.4, 5.1, 7.1**

- [ ] 32.3 Implement memory and observability properties
  - **Property 39: Trade patterns stored in memory**
  - **Property 46: Distributed tracing spans all agents**
  - **Property 44: Performance metrics tracked**
  - **Validates: Requirements 11.1, 12.4, 12.2**

- [ ] 32.4 Implement security and HITL properties
  - **Property 54: JWT tokens validated for API calls**
  - **Property 53: Similar cases suggest past decisions**
  - **Property 31: Web Portal shows live progress**
  - **Validates: Requirements 17.3, 16.5, 9.2**

- [ ] 33. Complete AgentCore Evaluations integration
- [ ] 33.1 Implement custom evaluators for quality assessment
  - Create TradeExtractionAccuracy evaluator with LLM-as-Judge
  - Create MatchingQuality evaluator for decision assessment
  - Create OCRQuality evaluator for text extraction assessment
  - Configure evaluation criteria and scoring schemas (1-5 scale)
  - _Requirements: 19.1, 19.2_

- [ ] 33.2 Configure online evaluation monitoring
  - Set up continuous monitoring for 10% of live agent traffic
  - Configure sampling rules and target agent selection
  - Create CloudWatch metrics namespace for evaluation scores
  - Set up alarms for quality score drops below thresholds
  - _Requirements: 19.3, 19.4_

- [ ] 33.3 Implement on-demand evaluation capabilities
  - Create evaluation test harness for batch assessment
  - Support pre-deployment quality gates
  - Enable A/B testing of agent configurations
  - _Requirements: 19.5_

- [ ] 34. Complete AgentCore Policy integration
- [ ] 34.1 Implement Cedar policies for authorization
  - Create trade amount limit policy ($100M threshold)
  - Create role-based access control policies (senior vs regular operators)
  - Create compliance control policies (restricted counterparties)
  - Create emergency shutdown policy (disabled by default)
  - _Requirements: 20.1, 20.2, 20.3, 20.4_

- [ ] 34.2 Configure policy enforcement and monitoring
  - Attach policy engine to AgentCore Gateway
  - Configure enforcement mode (LOG_ONLY for dev, ENFORCE for prod)
  - Set up policy decision logging to CloudWatch
  - Create alerts for policy denials and violations
  - _Requirements: 20.5_

- [ ] 35. Implement comprehensive error handling and recovery
- [ ] 35.1 Enhance exception classification and triage
  - Implement severity scoring system with RL integration
  - Create delegation system for routing to appropriate teams
  - Implement exponential backoff for transient errors
  - Add error pattern detection and alerting
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 35.2 Complete reinforcement learning integration
  - Implement RLExceptionHandler with episode recording
  - Add reward computation based on resolution outcomes
  - Integrate supervised learning from human decisions
  - Store RL models in AgentCore Memory
  - _Requirements: 8.2, 8.3, 8.4, 8.5_

- [ ] 36. Complete HITL workflow implementation
- [ ] 36.1 Implement HITL decision endpoints
  - Create POST /api/hitl/{review_id}/decision endpoint
  - Implement decision validation and recording
  - Add decision publishing to SQS for agent processing
  - Update audit trail with HITL decisions
  - _Requirements: 16.3, 16.4_

- [ ] 36.2 Integrate HITL with AgentCore Memory
  - Store HITL decisions in semantic memory
  - Implement similar case suggestion based on past decisions
  - Add decision context retrieval for matching scenarios
  - _Requirements: 16.5_

- [ ] 37. Complete audit trail implementation
- [ ] 37.1 Implement immutable audit logging
  - Add SHA-256 hash computation for tamper-evidence
  - Implement audit record validation and verification
  - Create audit trail query endpoints with filtering
  - Add export functionality (JSON, CSV, XML formats)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 37.2 Integrate audit trail with all agents
  - Add audit logging to all agent operations
  - Include user identity in authenticated operations
  - Track agent handoffs and decision points
  - Record performance metrics and error events
  - _Requirements: 10.1, 10.2_

- [ ] 38. Implement SQS event-driven architecture
- [ ] 38.1 Create SQS queue infrastructure
  - Create document-upload-events queue (FIFO)
  - Create extraction-events, matching-events, exception-events queues
  - Create HITL review queue and delegation queues
  - Configure dead letter queues and retry policies
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 38.2 Implement event publishing and subscription
  - Add SQS event publishing to all agents
  - Implement event message schemas with correlation IDs
  - Add event subscription handlers for agent coordination
  - Implement orchestrator monitoring queue (fanout)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 39. Complete Web Portal real-time features
- [ ] 39.1 Implement WebSocket real-time updates
  - Create WebSocket connection management
  - Implement agent status update broadcasting
  - Add trade processing progress updates
  - Implement HITL request notifications
  - _Requirements: 9.2, 9.3_

- [ ] 39.2 Complete dashboard components
  - Implement AgentHealthPanel with color-coded indicators
  - Add ProcessingMetrics with real-time charts
  - Create MatchingResults panel with statistics
  - Add drill-down capabilities for detailed views
  - _Requirements: 15.1, 15.2, 15.3_

- [ ] 40. Final integration and validation
- [ ] 40.1 Complete system integration testing
  - Test complete workflow from PDF upload to matching report
  - Validate error handling and recovery scenarios
  - Test HITL workflow end-to-end
  - Verify audit trail completeness and immutability
  - _Requirements: 1.5, 8.1, 16.1, 10.4_

- [ ] 40.2 Performance and security validation
  - Verify 90-second processing time requirement
  - Test authentication and authorization (JWT, RBAC, MFA)
  - Validate data encryption (S3, DynamoDB, TLS 1.3)
  - Run penetration testing and address findings
  - _Requirements: 18.5, 17.1, 17.2, 17.3, 17.4_

- [ ] 41. Final Checkpoint - Complete migration validation
  - Ensure all tests pass, ask the user if questions arise.
