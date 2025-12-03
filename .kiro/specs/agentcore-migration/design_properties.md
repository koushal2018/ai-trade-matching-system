### Correctness Properties (Continued from design.md)

Property 1: Functional parity with CrewAI implementation
*For any* trade confirmation PDF, processing through the new Strands SDK system should produce equivalent structured trade data and matching results as the original CrewAI system
**Validates: Requirements 1.5**

Property 2: Orchestrator routes requests correctly
*For any* incoming request, the Orchestrator Agent should route it to the appropriate specialized agent based on the request type
**Validates: Requirements 3.1**

Property 3: PDF Adapter independence
*For any* PDF document, the PDF Adapter Agent should be able to process it without requiring coordination with other agents
**Validates: Requirements 3.2**

Property 4: Trade Extraction independence
*For any* OCR text input, the Trade Data Extraction Agent should be able to parse trade entities without dependencies on other agents
**Validates: Requirements 3.3**

Property 5: Trade Matching independence
*For any* set of stored trades in DynamoDB, the Trade Matching Agent should be able to perform matching analysis independently
**Validates: Requirements 3.4**

Property 6: Exception handling independence
*For any* error condition from any agent, the Exception Management Agent should be able to handle it independently
**Validates: Requirements 3.5**

Property 7: Orchestrator detects and recovers from failures
*For any* agent failure scenario, the Orchestrator Agent should detect the failure and trigger appropriate recovery procedures
**Validates: Requirements 4.2**

Property 8: Orchestrator provides real-time status
*For any* status request, the Orchestrator Agent should return current status of all registered agents
**Validates: Requirements 4.3**

Property 9: Orchestrator coordinates handoffs
*For any* task completion by an agent, the Orchestrator should coordinate the handoff to the next appropriate agent in the workflow
**Validates: Requirements 4.4**

Property 10: Orchestrator aggregates metrics
*For any* metrics request, the Orchestrator should aggregate and return metrics from all agents
**Validates: Requirements 4.5**

Property 11: PDF conversion maintains 300 DPI
*For any* PDF document, the PDF Adapter Agent should produce JPEG images with exactly 300 DPI resolution
**Validates: Requirements 5.1, 18.1**

Property 12: OCR extraction completeness
*For any* set of images from a PDF, the PDF Adapter Agent should perform OCR on all images and combine the results
**Validates: Requirements 5.2**

Property 13: OCR results saved to S3
*For any* OCR extraction output, the PDF Adapter Agent should save the text to S3 and the text should be retrievable
**Validates: Requirements 5.3**

Property 14: PDF processing errors reported
*For any* processing failure in the PDF Adapter Agent, an error should be reported to the Exception Management Agent with full context
**Validates: Requirements 5.4**

Property 15: Successful processing triggers notification
*For any* successful PDF processing, the PDF Adapter Agent should notify the Trade Data Extraction Agent
**Validates: Requirements 5.5**

Property 16: All trade fields extracted
*For any* OCR text containing trade information, the Trade Data Extraction Agent should extract all required fields (Trade_ID, dates, notional, counterparty, etc.)
**Validates: Requirements 6.1**

Property 17: Trade source classification validity
*For any* parsed trade document, the TRADE_SOURCE field should be classified as either "BANK" or "COUNTERPARTY"
**Validates: Requirements 6.2**

Property 18: Structured data saved to S3
*For any* structured trade data, it should be saved as JSON to S3 and be retrievable
**Validates: Requirements 6.3**

Property 19: Trade routing to correct DynamoDB table
*For any* trade with TRADE_SOURCE="BANK", it should be stored in BankTradeData table; for TRADE_SOURCE="COUNTERPARTY", it should be stored in CounterpartyTradeData table
**Validates: Requirements 6.4**

Property 20: Extraction errors include context
*For any* extraction failure, the error report should include the OCR text, attempted parsing, and failure reason
**Validates: Requirements 6.5**

Property 21: Fuzzy matching applies tolerances
*For any* pair of trades being matched, the Trade Matching Agent should apply the specified tolerances: Trade_Date ±1 day, Notional ±0.01%, Counterparty fuzzy match
**Validates: Requirements 7.1, 18.3**

Property 22: Match classification validity
*For any* matching result, the classification should be one of: MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, BREAK, or DATA_ERROR
**Validates: Requirements 7.2**

Property 23: Matching reports are complete
*For any* matching operation, the generated markdown report should include summary statistics, matched trades list, breaks list, and data errors
**Validates: Requirements 7.3, 18.4**

Property 24: Reports saved to S3
*For any* generated matching report, it should be saved to S3 and be retrievable
**Validates: Requirements 7.4**

Property 25: Misplaced trades flagged as DATA_ERROR
*For any* trade with TRADE_SOURCE="BANK" found in CounterpartyTradeData table or TRADE_SOURCE="COUNTERPARTY" found in BankTradeData table, it should be flagged as DATA_ERROR
**Validates: Requirements 7.5**

Property 26: All errors logged with context
*For any* error reported by any agent, the Exception Management Agent should create a log entry with timestamp, agent ID, error type, and full context
**Validates: Requirements 8.1**

Property 27: Exponential backoff for transient errors
*For any* transient error, retry delays should follow exponential backoff pattern: delay_n = base_delay * (2 ^ n) where n is the retry attempt number
**Validates: Requirements 8.2**

Property 28: Permanent errors escalated to HITL
*For any* error classified as permanent (after max retries), it should be escalated to human operators via the Web Portal
**Validates: Requirements 8.3**

Property 29: Error resolution updates audit trail
*For any* error that is resolved (either automatically or via HITL), an audit trail entry should be created recording the resolution
**Validates: Requirements 8.4**

Property 30: Error pattern detection triggers alerts
*For any* detected pattern of similar errors (3+ occurrences within 1 hour), an administrator alert should be sent
**Validates: Requirements 8.5**

Property 31: Web Portal shows live progress
*For any* trade being processed, the Web Portal should display real-time progress updates via WebSocket
**Validates: Requirements 9.2**

Property 32: Web Portal displays error alerts
*For any* error that occurs, the Web Portal should display an alert with error details and HITL intervention options
**Validates: Requirements 9.3**

Property 33: Audit trail displays complete history
*For any* audit trail query, the Web Portal should display all matching records with complete operation history
**Validates: Requirements 9.4**

Property 34: All agent actions recorded in audit trail
*For any* action performed by any agent, an audit record should be created with timestamp, agent ID, action type, resource ID, and outcome
**Validates: Requirements 10.1**

Property 35: Audit records contain required fields
*For any* audit record, it should contain: timestamp, agent_id, action_type, resource_id, outcome, and immutable_hash
**Validates: Requirements 10.2**

Property 36: Audit trail filtering works correctly
*For any* audit trail query with filters (date range, agent ID, action type), only records matching all specified filters should be returned
**Validates: Requirements 10.3**

Property 37: Audit records are immutable
*For any* audit record, its immutable_hash should be SHA-256(timestamp + agent_id + action_type + resource_id + outcome + details), and any modification should be detectable by hash mismatch
**Validates: Requirements 10.4**

Property 38: Audit trail export format validity
*For any* audit trail export request, the output should be in a valid standard format (JSON, CSV, or XML) with all required fields
**Validates: Requirements 10.5**

Property 39: Trade patterns stored in memory
*For any* trade processing operation, relevant patterns (trade type, counterparty, notional range) should be stored in AgentCore Memory
**Validates: Requirements 11.1**

Property 40: Historical context retrieved for similar trades
*For any* trade that matches stored patterns (same counterparty + similar notional), relevant historical context should be retrieved from AgentCore Memory
**Validates: Requirements 11.2**

Property 41: Matching decisions recorded in semantic memory
*For any* matching decision (including classification and rationale), it should be stored in AgentCore Memory's semantic strategy
**Validates: Requirements 11.3**

Property 42: Error patterns stored for prevention
*For any* error occurrence, the error pattern (error type, agent, context) should be stored in AgentCore Memory
**Validates: Requirements 11.4**

Property 43: Traces emitted for all agent executions
*For any* agent execution, distributed traces should be emitted to AgentCore Observability with span information
**Validates: Requirements 12.1**

Property 44: Performance metrics tracked
*For any* operation, latency, throughput, and error rate metrics should be tracked and sent to AgentCore Observability
**Validates: Requirements 12.2**

Property 45: Anomaly detection triggers alerts
*For any* detected anomaly (latency > 2x baseline, error rate > 5%), an alert should be triggered via AgentCore Observability
**Validates: Requirements 12.3**

Property 46: Distributed tracing spans all agents
*For any* request that involves multiple agents, the trace should include spans from all involved agents with proper parent-child relationships
**Validates: Requirements 12.4**

Property 47: DynamoDB operations use AgentCore Gateway
*For any* DynamoDB operation (put_item, scan, query), it should be executed through MCP tools exposed by AgentCore Gateway
**Validates: Requirements 13.2**

Property 48: S3 operations use AgentCore Gateway
*For any* S3 operation (get_object, put_object, list_objects), it should be executed through MCP tools exposed by AgentCore Gateway
**Validates: Requirements 13.3**

Property 49: Tool invocations logged in audit trail
*For any* tool invocation by any agent, an audit trail entry should be created with tool name, parameters, and outcome
**Validates: Requirements 13.5**

Property 50: Low-confidence matches trigger HITL
*For any* matching result with confidence_score < 0.7, the system should pause processing and request human review via the Web Portal
**Validates: Requirements 16.1**

Property 51: HITL decisions recorded in memory
*For any* human decision made via the Web Portal, it should be recorded in AgentCore Memory with the decision, rationale, and trade details
**Validates: Requirements 16.3**

Property 52: Processing resumes after HITL decision
*For any* HITL decision recorded, agent processing should automatically resume with the human-provided decision
**Validates: Requirements 16.4**

Property 53: Similar cases suggest past decisions
*For any* trade matching scenario similar to a past HITL case (same counterparty + similar differences), the system should suggest the previous human decision
**Validates: Requirements 16.5**

Property 54: JWT tokens validated for API calls
*For any* API call to the system, the JWT token should be validated against AgentCore Identity before processing the request
**Validates: Requirements 17.3**

Property 55: RBAC enforced for permissions
*For any* permission check, role-based access control should be enforced based on the user's roles from AgentCore Identity
**Validates: Requirements 17.4**

Property 56: Audit logs include user identity
*For any* audit log entry created for a user-initiated action, it should include the authenticated user's identity from AgentCore Identity
**Validates: Requirements 17.5**

Property 57: OCR accuracy maintained
*For any* OCR operation, the text extraction accuracy should be equivalent to or better than the baseline CrewAI implementation (measured by character error rate)
**Validates: Requirements 18.2**

## Error Handling

### Error Classification

The system classifies errors into three categories:

1. **Transient Errors**: Temporary failures that may succeed on retry
   - AWS service throttling
   - Network timeouts
   - Temporary resource unavailability
   - **Handling**: Exponential backoff retry (max 3 attempts)

2. **Permanent Errors**: Failures that won't succeed on retry
   - Invalid PDF format
   - Missing required trade fields
   - Authentication failures
   - **Handling**: Immediate escalation to HITL

3. **System Errors**: Infrastructure or configuration issues
   - AgentCore Runtime failures
   - Memory service unavailable
   - Gateway connection errors
   - **Handling**: Alert administrators, attempt failover

### Retry Strategy

```python
def exponential_backoff_retry(func, max_retries=3, base_delay=1.0):
    """
    Retry function with exponential backoff.
    delay_n = base_delay * (2 ^ n)
    """
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise PermanentError(f"Max retries exceeded: {e}")
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
            logger.info(f"Retry attempt {attempt + 1} after {delay}s delay")
```

### Error Context

All errors include:
- Timestamp
- Agent ID
- Error type and message
- Stack trace
- Input parameters
- System state at time of error

## Testing Strategy

### Unit Testing

**Framework**: pytest with pytest-asyncio for async tests

**Coverage Requirements**:
- Minimum 80% code coverage
- 100% coverage for critical paths (trade routing, matching logic)

**Test Categories**:

1. **Agent Tests**: Test each agent's core functionality in isolation
2. **Tool Tests**: Test MCP tools and custom tools
3. **Model Tests**: Test Pydantic models and validation
4. **Utility Tests**: Test helper functions and utilities

**Example Unit Test**:
```python
def test_trade_source_classification():
    """Test that trade source is correctly classified."""
    bank_text = "Internal Trade ID: 12345\nTrader: John Doe\nP&L: $1000"
    result = classify_trade_source(bank_text)
    assert result == "BANK"
    
    cp_text = "Counterparty: ABC Corp\nSignature: _______"
    result = classify_trade_source(cp_text)
    assert result == "COUNTERPARTY"
```

### Property-Based Testing

**Framework**: Hypothesis for Python

**Configuration**: Minimum 100 iterations per property test

**Property Test Categories**:

1. **Functional Parity Properties**: Verify equivalence with CrewAI system
2. **Data Integrity Properties**: Verify correct table routing and data consistency
3. **Matching Properties**: Verify fuzzy matching tolerances and classifications
4. **Audit Trail Properties**: Verify immutability and completeness

**Example Property Test**:
```python
from hypothesis import given, strategies as st

@given(
    trade_source=st.sampled_from(["BANK", "COUNTERPARTY"]),
    trade_id=st.text(min_size=5, max_size=20)
)
def test_property_trade_routing(trade_source, trade_id):
    """
    Property 19: Trade routing to correct DynamoDB table
    Feature: agentcore-migration, Property 19
    
    For any trade with a given TRADE_SOURCE, it should be stored
    in the correct DynamoDB table.
    """
    trade_data = generate_trade_data(trade_id, trade_source)
    
    # Store the trade
    store_trade(trade_data)
    
    # Verify it's in the correct table
    if trade_source == "BANK":
        assert trade_exists_in_table("BankTradeData", trade_id)
        assert not trade_exists_in_table("CounterpartyTradeData", trade_id)
    else:
        assert trade_exists_in_table("CounterpartyTradeData", trade_id)
        assert not trade_exists_in_table("BankTradeData", trade_id)
```

### Integration Testing

**Scope**: Test agent interactions and end-to-end workflows

**Test Scenarios**:
1. Complete trade processing workflow (PDF → Matching → Report)
2. Error handling and recovery flows
3. HITL interaction flows
4. AgentCore service integrations (Memory, Observability, Gateway)

**Example Integration Test**:
```python
@pytest.mark.integration
async def test_end_to_end_trade_processing():
    """Test complete workflow from PDF upload to matching report."""
    # Upload test PDF
    pdf_path = upload_test_pdf("test_trade.pdf", "COUNTERPARTY")
    
    # Trigger orchestrator
    result = await orchestrator.process_trade(pdf_path)
    
    # Verify all stages completed
    assert result["pdf_processed"] is True
    assert result["data_extracted"] is True
    assert result["trade_stored"] is True
    assert result["matching_complete"] is True
    
    # Verify outputs exist
    assert s3_object_exists(result["ocr_text_path"])
    assert s3_object_exists(result["trade_json_path"])
    assert s3_object_exists(result["report_path"])
    
    # Verify DynamoDB entry
    trade = get_trade_from_dynamodb("CounterpartyTradeData", result["trade_id"])
    assert trade is not None
    assert trade["TRADE_SOURCE"] == "COUNTERPARTY"
```

### Frontend Testing

**Framework**: Jest + React Testing Library

**Test Categories**:
1. Component unit tests
2. Integration tests with mocked APIs
3. E2E tests with Playwright

**Example Frontend Test**:
```typescript
describe('Dashboard Component', () => {
  it('displays agent health status correctly', () => {
    const agents = [
      { agent_id: '1', agent_name: 'PDF Adapter', health: 'healthy' },
      { agent_id: '2', agent_name: 'Trade Matching', health: 'degraded' }
    ];
    
    render(<Dashboard agents={agents} metrics={mockMetrics} />);
    
    expect(screen.getByText('PDF Adapter')).toBeInTheDocument();
    expect(screen.getByText('healthy')).toHaveClass('status-healthy');
    expect(screen.getByText('degraded')).toHaveClass('status-degraded');
  });
});
```

## Deployment Strategy

### Phase 1: Infrastructure Setup (Week 1-2)

1. Provision AWS resources in us-east-1
2. Create AgentCore Memory resources
3. Set up AgentCore Gateway with MCP targets
4. Configure AgentCore Observability
5. Set up AgentCore Identity with Cognito

### Phase 2: Agent Migration (Week 3-5)

1. Implement Orchestrator Agent
2. Migrate PDF Adapter Agent
3. Migrate Trade Data Extraction Agent
4. Migrate Trade Matching Agent
5. Implement Exception Management Agent
6. Deploy all agents to AgentCore Runtime

### Phase 3: Frontend Development (Week 4-6)

1. Set up React project with TypeScript
2. Implement Dashboard component
3. Implement HITL Panel component
4. Implement Audit Trail component
5. Set up WebSocket and REST API integration

### Phase 4: Integration & Testing (Week 7-8)

1. Integration testing of all agents
2. End-to-end workflow testing
3. Performance testing and optimization
4. Security testing and penetration testing

### Phase 5: Data Migration (Week 9)

1. Export data from me-central-1
2. Transform data for us-east-1
3. Import data to new DynamoDB tables
4. Verify data integrity

### Phase 6: Production Deployment (Week 10)

1. Blue-green deployment to production
2. Monitor metrics and logs
3. Gradual traffic shift from old to new system
4. Decommission old CrewAI system

## Monitoring and Observability

### Key Metrics

1. **Agent Health Metrics**:
   - Agent uptime percentage
   - Average response time per agent
   - Error rate per agent
   - Active task count

2. **Processing Metrics**:
   - Trades processed per hour
   - Average processing time per trade
   - OCR accuracy rate
   - Matching success rate

3. **System Metrics**:
   - API latency (p50, p95, p99)
   - WebSocket connection count
   - Memory usage per agent
   - AgentCore Runtime scaling events

### Alerting Rules

1. **Critical Alerts** (PagerDuty):
   - Any agent health = UNHEALTHY
   - Error rate > 10% for 5 minutes
   - API latency p95 > 5 seconds
   - AgentCore Runtime failures

2. **Warning Alerts** (Email):
   - Agent health = DEGRADED
   - Error rate > 5% for 10 minutes
   - Processing time > 120 seconds
   - Memory usage > 80%

### Dashboards

1. **Operations Dashboard**:
   - Real-time agent status
   - Processing metrics
   - Error rates and types
   - System health overview

2. **Business Dashboard**:
   - Trades processed today/week/month
   - Match rate trends
   - Break analysis
   - HITL intervention rate

3. **Technical Dashboard**:
   - API performance metrics
   - Database query performance
   - AgentCore service health
   - Cost tracking

## Security Considerations

### Authentication & Authorization

- All API endpoints protected by AgentCore Identity JWT tokens
- Role-based access control (RBAC) for different user types:
  - **Admin**: Full system access
  - **Operator**: View and HITL decisions
  - **Auditor**: Read-only audit trail access
- MFA required for admin users

### Data Protection

- All data encrypted at rest (S3, DynamoDB)
- All data encrypted in transit (TLS 1.3)
- Sensitive fields (counterparty names, notionals) masked in logs
- PII handling compliant with regulations

### Network Security

- AgentCore Runtime deployed in VPC
- Private subnets for agents
- Security groups restrict traffic
- VPC endpoints for AWS services

### Audit & Compliance

- Immutable audit trail with tamper-evidence
- All actions logged with user identity
- Compliance reports exportable
- Regular security audits

## Cost Optimization

### AgentCore Runtime

- Use direct_code_deploy for faster deployments
- Configure idle timeout (900s) to reduce costs
- Set max lifetime (28800s) appropriately
- Monitor and adjust based on usage patterns

### AWS Services

- Use S3 Intelligent-Tiering for storage
- DynamoDB on-demand billing for variable load
- Bedrock Claude 4 with request batching
- CloudWatch Logs with retention policies

### Estimated Monthly Costs (us-east-1)

- AgentCore Runtime: $500-1000 (based on usage)
- Bedrock Claude 4: $300-600 (based on tokens)
- DynamoDB: $100-200 (on-demand)
- S3: $50-100 (with Intelligent-Tiering)
- Other AWS services: $100-200
- **Total**: $1050-2100/month

## Migration Risks & Mitigation

### Risk 1: Functional Parity Issues

**Risk**: New system doesn't match CrewAI behavior exactly
**Mitigation**: 
- Comprehensive property-based testing
- Parallel run period with comparison
- Gradual traffic shift

### Risk 2: Performance Degradation

**Risk**: New system slower than CrewAI
**Mitigation**:
- Performance testing before migration
- AgentCore Runtime auto-scaling
- Caching strategies

### Risk 3: Data Migration Errors

**Risk**: Data loss or corruption during migration
**Mitigation**:
- Dry-run migrations with validation
- Backup all data before migration
- Rollback plan ready

### Risk 4: Learning Curve

**Risk**: Team unfamiliar with Strands SDK and AgentCore
**Mitigation**:
- Training sessions for team
- Comprehensive documentation
- Gradual rollout with support

## Success Criteria

1. **Functional**: All 57 correctness properties pass
2. **Performance**: 90-second processing time maintained
3. **Reliability**: 99.9% uptime for agents
4. **Usability**: Web Portal accessible and responsive
5. **Cost**: Within estimated budget
6. **Security**: Pass security audit
7. **Compliance**: Audit trail meets regulatory requirements


## AgentCore Evaluations Properties

Property 58: Trade extraction quality evaluated
*For any* trade extraction operation, the system should evaluate extraction accuracy using the TradeExtractionAccuracy evaluator and record scores
**Validates: Requirements 19.1**

Property 59: Matching quality evaluated
*For any* matching decision, the system should assess matching quality using the MatchingQuality evaluator with LLM-as-Judge
**Validates: Requirements 19.2**

Property 60: Online evaluation samples traffic
*For any* configured online evaluation, the system should sample approximately 10% of live agent traffic for quality assessment
**Validates: Requirements 19.3**

Property 61: Low quality scores trigger alarms
*For any* evaluation score that drops below the configured threshold (3.5 for extraction, 4.0 for matching), the system should trigger a CloudWatch alarm
**Validates: Requirements 19.4**

Property 62: On-demand evaluation supported
*For any* batch of agent traces, the system should support on-demand evaluation using specified evaluators
**Validates: Requirements 19.5**

## AgentCore Policy Properties

Property 63: High-value trades require authorization
*For any* trade with notional amount exceeding $100M, the system should require elevated authorization via Cedar policy enforcement
**Validates: Requirements 20.1**

Property 64: Role-based approval thresholds enforced
*For any* HITL approval request, senior operators should be permitted to approve matches with score ≥0.70, while regular operators should only approve matches with score ≥0.85
**Validates: Requirements 20.2**

Property 65: Restricted counterparties blocked
*For any* trade involving a counterparty on the restricted list, the system should block processing via compliance policy
**Validates: Requirements 20.3**

Property 66: Emergency shutdown effective
*For any* emergency shutdown policy activation, the system should immediately block all trade processing operations
**Validates: Requirements 20.4**

Property 67: Policy decisions logged
*For any* policy evaluation (allow or deny), the system should log the decision to CloudWatch with full context including principal, action, resource, and decision reason
**Validates: Requirements 20.5**

## Updated Success Criteria

1. **Functional**: All 67 correctness properties pass (updated from 57)
2. **Performance**: 90-second processing time maintained
3. **Reliability**: 99.9% uptime for agents
4. **Usability**: Web Portal accessible and responsive
5. **Cost**: Within estimated budget
6. **Security**: Pass security audit with Policy enforcement
7. **Compliance**: Audit trail meets regulatory requirements
8. **Quality**: Evaluation scores maintain average ≥4.0
9. **Authorization**: Policy enforcement active in production
