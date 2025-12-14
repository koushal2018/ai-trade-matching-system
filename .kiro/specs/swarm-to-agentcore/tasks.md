# Implementation Plan

- [x] 1. Set up AgentCore Memory resource
  - Create memory resource with 3 built-in strategies (semantic, user preference, summary)
  - Configure standard namespace patterns
  - Export memory ID for agent configuration
  - _Requirements: 2.1, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 1.1 Create memory resource setup script
  - Write `create_trade_matching_memory()` function
  - Configure semanticMemoryStrategy with /facts/{actorId} namespace
  - Configure userPreferenceMemoryStrategy with /preferences/{actorId} namespace
  - Configure summaryMemoryStrategy with /summaries/{actorId}/{sessionId} namespace
  - Use `create_memory_and_wait()` to ensure availability
  - _Requirements: 2.1, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 1.2 Write property test for memory resource configuration
  - **Property 5: Configuration correctness**
  - **Validates: Requirements 11.1**

- [x] 2. Implement session manager factory
  - Create per-agent session manager with unique session IDs
  - Configure retrieval for all 3 namespaces
  - Handle missing environment variables gracefully
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 2.1 Create `create_agent_session_manager()` function
  - Accept agent_name, document_id, memory_id, actor_id, region_name parameters
  - Generate unique session ID: trade_{document_id}_{agent_name}_{timestamp}
  - Configure AgentCoreMemoryConfig with retrieval settings
  - Return AgentCoreMemorySessionManager instance
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 2.2 Configure retrieval for all namespaces
  - /facts/{actorId}: top_k=10, relevance_score=0.6
  - /preferences/{actorId}: top_k=5, relevance_score=0.7
  - /summaries/{actorId}/{sessionId}: top_k=5, relevance_score=0.5
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 2.3 Write property test for session ID format
  - **Property 3: Session ID format compliance**
  - **Validates: Requirements 10.1, 10.2**

- [x] 3. Update agent factory functions
  - Modify agent creation to use per-agent session managers
  - Update system prompts with memory access guidance
  - Maintain all existing tool implementations
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 3.1 Update `create_pdf_adapter_agent()` function
  - Accept document_id and memory_id parameters
  - Create dedicated session manager for pdf_adapter
  - Update system prompt with memory access instructions
  - Maintain existing tools (download_pdf_from_s3, extract_text_with_bedrock, save_canonical_output)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 13.2_

- [x] 3.2 Update `create_trade_extractor_agent()` function
  - Accept document_id and memory_id parameters
  - Create dedicated session manager for trade_extractor
  - Update system prompt with memory access instructions
  - Maintain existing tools (store_trade_in_dynamodb, use_aws)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 13.3_

- [x] 3.3 Update `create_trade_matcher_agent()` function
  - Accept document_id and memory_id parameters
  - Create dedicated session manager for trade_matcher
  - Update system prompt with memory access instructions
  - Maintain existing tools (scan_trades_table, save_matching_report, use_aws)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 13.4_

- [x] 3.4 Update `create_exception_handler_agent()` function
  - Accept document_id and memory_id parameters
  - Create dedicated session manager for exception_handler
  - Update system prompt with memory access instructions
  - Maintain existing tools (get_severity_guidelines, store_exception_record, use_aws)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 13.5_

- [x] 3.5 Write property test for functional parity
  - **Property 4: Functional parity preservation**
  - **Validates: Requirements 8.1, 8.2, 16.1**

- [x] 4. Update swarm creation function
  - Modify to create agents with individual session managers
  - Maintain swarm configuration (max_handoffs, max_iterations, timeouts)
  - Preserve autonomous handoff patterns
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 4.1 Update `create_trade_matching_swarm_with_memory()` function
  - Accept document_id and memory_id parameters
  - Create all 4 agents with individual session managers
  - Maintain swarm configuration unchanged
  - Return configured Swarm instance
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 5. Implement error handling
  - Add memory service failure handling with circuit breaker
  - Add session manager initialization error handling
  - Add memory retrieval timeout handling
  - Add memory storage failure handling
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 5.1 Create `MemoryFallbackHandler` class
  - Implement retry logic with exponential backoff
  - Implement circuit breaker pattern
  - Implement fallback to operation without memory
  - Log all memory failures for monitoring
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 5.2 Create `create_session_manager_safe()` function
  - Wrap session manager creation with try-catch
  - Return None on failure instead of raising
  - Log errors with context
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 5.3 Create `retrieve_with_timeout()` async function
  - Implement timeout for memory retrieval
  - Return None on timeout
  - Log timeout events
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 5.4 Create `store_pattern_safe()` function
  - Wrap memory storage with try-catch
  - Return success boolean
  - Continue processing on failure
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 6. Create AgentCore Runtime deployment package
  - Create deployment directory structure
  - Create AgentCore entrypoint function
  - Create agentcore.yaml configuration
  - Add dependencies to requirements.txt
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 6.1 Create deployment directory
  - Create deployment/swarm_agentcore/ directory
  - Copy trade_matching_swarm.py with memory integration
  - Copy aws_resources.py for shared AWS clients
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 6.2 Create AgentCore entrypoint
  - Create trade_matching_swarm_agentcore.py
  - Implement `invoke()` function with BedrockAgentCoreApp
  - Extract parameters from payload
  - Create swarm with memory
  - Execute swarm and return results
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 20.1, 20.2, 20.3, 20.4, 20.5_

- [x] 6.3 Create agentcore.yaml configuration
  - Set name: trade-matching-swarm
  - Set runtime: python3.11
  - Configure environment variables (AGENTCORE_MEMORY_ID, ACTOR_ID, AWS_REGION, S3_BUCKET_NAME, DynamoDB tables)
  - Add dependencies (strands, bedrock-agentcore[strands-agents], boto3)
  - Set timeout: 600 seconds, memory: 2048 MB
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 6.4 Create requirements.txt
  - Add strands>=0.1.0
  - Add strands-tools>=0.1.0
  - Add bedrock-agentcore[strands-agents]>=0.1.0
  - Add boto3>=1.34.0
  - Add pydantic>=2.0.0
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 7. Create deployment scripts
  - Create memory resource creation script
  - Create AgentCore deployment script
  - Create local testing script
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 7.1 Create setup_memory.py script
  - Call create_trade_matching_memory()
  - Output memory ID
  - Provide export command for environment variable
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 7.2 Create deploy_agentcore.sh script
  - Run agentcore configure --name trade-matching-swarm
  - Run agentcore launch --agent-name trade-matching-swarm
  - Verify deployment status
  - Output agent endpoint URL
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 7.3 Create test_local.py script
  - Test swarm with memory locally
  - Use test actor and session IDs
  - Verify memory storage and retrieval
  - Clean up test memory data
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Write property tests
  - Property 1: Memory storage consistency
  - Property 2: Memory retrieval relevance
  - Property 3: Session ID format compliance (already written in 2.3)
  - Property 4: Functional parity preservation (already written in 3.5)
  - Property 5: Configuration correctness (already written in 1.2)
  - Property 6: AgentCore Runtime scaling
  - _Requirements: All requirements_

- [x] 9.1 Write property test for memory storage consistency
  - **Property 1: Memory storage consistency**
  - **Validates: Requirements 2.2, 2.4, 3.1**

- [x] 9.2 Write property test for memory retrieval relevance
  - **Property 2: Memory retrieval relevance**
  - **Validates: Requirements 2.3**

- [x] 9.3 Write property test for AgentCore Runtime scaling
  - **Property 6: AgentCore Runtime scaling**
  - **Validates: Requirements 1.2**

- [x] 10. Write unit tests
  - Test memory resource creation
  - Test session manager creation
  - Test agent creation with memory
  - Test error handling
  - _Requirements: All requirements_

- [x] 10.1 Write unit tests for memory resource creation
  - Test create_trade_matching_memory() returns valid memory ID
  - Test memory resource has semantic strategy
  - Test memory resource has user preference strategy
  - Test memory resource has summary strategy
  - _Requirements: 2.1, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 10.2 Write unit tests for session manager creation
  - Test create_agent_session_manager() returns valid session manager
  - Test session ID format is correct
  - Test retrieval configs are set correctly
  - Test error handling for missing memory ID
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 10.3 Write unit tests for agent creation
  - Test agents are created with session managers
  - Test each agent has unique session ID
  - Test all agents share same memory resource
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 10.4 Write unit tests for error handling
  - Test memory fallback on service failure
  - Test session manager safe creation
  - Test retrieval timeout handling
  - Test storage failure handling
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 11. Write integration tests
  - Test complete trade processing with memory
  - Test memory persistence across sessions
  - _Requirements: All requirements_

- [x] 11.1 Write integration test for trade processing
  - Process first trade and verify memory storage
  - Process similar trade and verify memory retrieval
  - Verify memory was used in second processing
  - _Requirements: 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 11.2 Write integration test for memory persistence
  - Create session 1 and store pattern
  - Create session 2 and retrieve pattern
  - Verify pattern persists across sessions
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 12. Write performance tests
  - Test memory retrieval latency
  - Test AgentCore Runtime scaling
  - _Requirements: 2.5, 1.2_

- [x] 12.1 Write performance test for memory retrieval
  - Measure retrieval latency
  - Verify latency < 500ms
  - _Requirements: 2.5_

- [x] 12.2 Write performance test for AgentCore scaling
  - Simulate increasing load
  - Verify response time doesn't degrade significantly
  - _Requirements: 1.2_

- [x] 13. Create documentation
  - Write deployment guide
  - Write memory configuration guide
  - Write troubleshooting guide
  - Write CLI command examples
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [x] 13.1 Write deployment guide
  - Document step-by-step deployment process
  - Include memory resource creation
  - Include AgentCore deployment
  - Include verification steps
  - _Requirements: 19.1, 19.2_

- [x] 13.2 Write memory configuration guide
  - Document memory strategies
  - Document namespace patterns
  - Document retrieval configuration
  - Include configuration examples
  - _Requirements: 19.3_

- [x] 13.3 Write troubleshooting guide
  - Document common issues
  - Document error messages
  - Document resolution steps
  - _Requirements: 19.4_

- [x] 13.4 Write CLI command examples
  - Document memory creation commands
  - Document deployment commands
  - Document testing commands
  - _Requirements: 19.5_

- [x] 14. Final Checkpoint - Make sure all tests are passing
  - Ensure all tests pass, ask the user if questions arise.
