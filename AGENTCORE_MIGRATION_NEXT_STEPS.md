# AgentCore Migration - Next Steps

## Current Status

Your AgentCore migration is well-advanced with most core functionality implemented. The remaining tasks focus on quality assurance, policy enforcement, and production readiness.

## Immediate Priorities

### 1. Complete Property-Based Testing (Task 32.x) ⚡ HIGH PRIORITY

**Status**: Started with Property 17 ✅  
**Files Created**: 
- `test_property_17_simple.py` ✅
- ~~`test_property_1_functional_parity.py`~~ ❌ **DEPRECATED - CrewAI removed**

**Note**: CrewAI functional parity tests are no longer applicable as CrewAI has been completely removed from the system. All legacy CrewAI code has been archived to `legacy/crewai/`.

**Next Steps**:
```bash
# Run existing property tests
python test_property_17_simple.py

# Install hypothesis for advanced property testing
pip install hypothesis

# Create remaining property tests
# - Property 37: Audit records immutability
# - Property 11: PDF DPI quality
# - Property 21: Fuzzy matching tolerances
```

### 2. Deploy AgentCore Evaluations (Task 33.x) 📊 HIGH PRIORITY

**Status**: Implementation ready ✅  
**Files Created**: `src/latest_trade_matching_agent/evaluations/custom_evaluators.py` ✅

**Next Steps**:
```bash
# Deploy evaluators to AgentCore Runtime
agentcore configure --name trade-extraction-evaluator
agentcore launch --agent-name trade-extraction-evaluator

# Set up CloudWatch metrics namespace
aws cloudwatch put-metric-data --namespace "AgentCore/Evaluations" --metric-data MetricName=QualityScore,Value=5

# Configure online evaluation (10% sampling)
# Create evaluation test harness
```

### 3. Deploy AgentCore Policy (Task 34.x) 🔐 HIGH PRIORITY

**Status**: Implementation ready ✅  
**Files Created**: `src/latest_trade_matching_agent/policy/trade_matching_policies.py` ✅

**Next Steps**:
```bash
# Create AgentCore Policy Engine
# Deploy Cedar policies for:
# - Trade amount limits ($100M threshold)
# - Role-based access control
# - Compliance controls
# - Emergency shutdown

# Test in LOG_ONLY mode first
# Switch to ENFORCE mode after validation
```

## Implementation Guide

### Step 1: Run Migration Completion Script

```bash
# Execute the comprehensive migration checker
python scripts/complete_agentcore_migration.py
```

This script will:
- ✅ Validate all property tests
- ✅ Check AgentCore Evaluations setup
- ✅ Verify Policy integration
- ✅ Validate error handling components
- ✅ Check HITL workflow implementation
- ✅ Verify audit trail completeness
- ✅ Validate SQS event architecture
- ✅ Check web portal features
- ✅ Run integration tests

### Step 2: AgentCore Evaluations Deployment

```python
# Use the custom evaluators
from src.latest_trade_matching_agent.evaluations.custom_evaluators import (
    TradeExtractionAccuracyEvaluator,
    MatchingQualityEvaluator,
    EvaluationOrchestrator
)

# Initialize evaluators
orchestrator = EvaluationOrchestrator()

# Evaluate agent interactions
results = orchestrator.evaluate_agent_interaction(
    agent_name="trade_extractor",
    interaction_data={
        "original_text": pdf_text,
        "extracted_trade": trade_model
    }
)
```

### Step 3: AgentCore Policy Deployment

```python
# Use the policy engine
from src.latest_trade_matching_agent.policy.trade_matching_policies import (
    PolicyEngine,
    create_test_scenarios
)

# Initialize policy engine
policy_engine = PolicyEngine()

# Create and deploy policies
policies = policy_engine.create_trade_matching_policies(
    policy_engine_id="your_policy_engine_id",
    gateway_arn="your_gateway_arn"
)

# Test policies
test_cases = create_test_scenarios()
results = policy_engine.test_policy_decisions(gateway_url, test_cases)
```

## Critical Business Rules Validation

Ensure these are properly enforced through policies:

### Trade Processing Rules
- ✅ **Source Classification**: BANK vs COUNTERPARTY validation
- ✅ **Table Routing**: Correct DynamoDB table assignment
- ✅ **Amount Limits**: $100M threshold for standard processing
- ✅ **Match Thresholds**: 85%+ auto-match, 70-84% review, <70% break

### Security & Compliance
- ✅ **Role-Based Access**: Operator vs Senior Operator permissions
- ✅ **Restricted Counterparties**: Block sanctioned entities
- ✅ **Data Integrity**: Verify TRADE_SOURCE matches table
- ✅ **Audit Trail**: Immutable logging with SHA-256 hashes

## Testing Strategy

### 1. Property-Based Tests
```bash
# Test trade source classification
python test_property_17_simple.py

# Note: CrewAI functional parity tests have been removed
# as CrewAI is no longer part of the system

# Add more property tests for:
# - Audit immutability
# - PDF processing quality
# - Matching tolerances
```

### 2. Policy Tests
```bash
# Test policy decisions
python -c "
from src.latest_trade_matching_agent.policy.trade_matching_policies import *
engine = PolicyEngine()
scenarios = create_test_scenarios()
results = engine.test_policy_decisions('gateway_url', scenarios)
print(f'Passed: {sum(1 for r in results if r[\"passed\"])}/{len(results)}')
"
```

### 3. End-to-End Tests
```bash
# Run complete workflow test
python tests/e2e/test_complete_workflow.py

# Test with sample PDFs
python deployment/swarm/trade_matching_swarm.py \
  data/BANK/FAB_26933659.pdf \
  --source-type BANK \
  --verbose
```

## Production Deployment Checklist

### Pre-Deployment
- [ ] All property tests pass
- [ ] Policy engine configured and tested
- [ ] Evaluations deployed and monitoring
- [ ] Error handling validated
- [ ] HITL workflow tested
- [ ] Audit trail verified
- [ ] Performance meets 90-second requirement

### Deployment
- [ ] Deploy agents to AgentCore Runtime
- [ ] Configure AgentCore Memory resources
- [ ] Set up AgentCore Gateway with policies
- [ ] Enable AgentCore Observability
- [ ] Deploy web portal and API

### Post-Deployment
- [ ] Monitor agent health and metrics
- [ ] Validate policy enforcement
- [ ] Test HITL workflow end-to-end
- [ ] Verify audit trail completeness
- [ ] Conduct user training
- [ ] Plan CrewAI system decommission

## Key Files Created

### Property Testing
- ✅ `test_property_17_simple.py` - Trade source classification
- ✅ `test_property_1_functional_parity.py` - CrewAI parity validation

### AgentCore Evaluations
- ✅ `src/latest_trade_matching_agent/evaluations/custom_evaluators.py`
  - TradeExtractionAccuracyEvaluator (LLM-as-Judge)
  - MatchingQualityEvaluator
  - OCRQualityEvaluator
  - ExceptionHandlingQualityEvaluator
  - EvaluationOrchestrator

### AgentCore Policy
- ✅ `src/latest_trade_matching_agent/policy/trade_matching_policies.py`
  - Cedar policies for trade amount limits
  - Role-based access control
  - Compliance controls
  - Emergency shutdown capabilities
  - Data integrity validation

### Migration Management
- ✅ `scripts/complete_agentcore_migration.py` - Comprehensive task validator

## Success Metrics

### Quality Metrics (via Evaluations)
- Trade extraction accuracy: >95%
- Matching quality score: >4.0/5.0
- OCR quality: >90% completeness
- Exception handling: <2% false positives

### Performance Metrics
- End-to-end processing: <90 seconds
- Agent response time: <30 seconds
- Error rate: <1%
- Throughput: 100+ trades/hour

### Security Metrics (via Policy)
- Policy compliance: 100%
- Unauthorized access attempts: 0
- Data integrity violations: 0
- Audit trail completeness: 100%

## Support Resources

### AgentCore Documentation
- [AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html)
- [AgentCore Evaluations](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations-overview.html)
- [AgentCore Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-overview.html)

### Implementation Examples
- Policy Integration: Check `src/latest_trade_matching_agent/policy/`
- Evaluations: Check `src/latest_trade_matching_agent/evaluations/`
- Property Tests: Check `test_property_*.py` files

## Next Actions

1. **Run the migration completion script**: `python scripts/complete_agentcore_migration.py`
2. **Execute property tests**: Validate all business logic
3. **Deploy evaluations**: Set up quality monitoring
4. **Configure policies**: Implement security controls
5. **Test end-to-end**: Validate complete workflow
6. **Deploy to production**: Follow deployment checklist

Your AgentCore migration is in excellent shape! The core functionality is implemented and you have comprehensive tools for validation and deployment. Focus on the testing and policy deployment to complete the migration successfully.