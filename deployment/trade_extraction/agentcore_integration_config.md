# AgentCore Integration Configuration for Trade Extraction Agent

## Required AgentCore Resources

### 1. AgentCore Gateway
```bash
# Deploy DynamoDB Gateway
agentcore gateway create --config terraform/agentcore/configs/agentcore_gateway_config.json

# Verify gateway deployment
aws bedrock-agent list-gateways --region us-east-1
```

### 2. AgentCore Memory Resources
```bash
# Deploy memory resources
agentcore memory create --config terraform/agentcore/configs/agentcore_memory_config.json

# Required memory resources for trade extraction:
# - trade-matching-system-trade-patterns-production (semantic)
# - trade-matching-system-processing-history-production (event)
```

### 3. AgentCore Identity (Optional but Recommended)
```bash
# Already configured via Cognito
# User Pool: us-east-1_uQ2lN39dT
# Required for secure API access and RBAC
```

## Agent Configuration Updates

### Environment Variables
Add to `.env`:
```bash
# AgentCore Gateway
AGENTCORE_DYNAMODB_GATEWAY_NAME=trade-matching-system-dynamodb-gateway-production
AGENTCORE_S3_GATEWAY_NAME=trade-matching-system-s3-gateway-production

# AgentCore Memory
AGENTCORE_TRADE_PATTERNS_MEMORY=trade-matching-system-trade-patterns-production
AGENTCORE_PROCESSING_HISTORY_MEMORY=trade-matching-system-processing-history-production

# AgentCore Identity
AGENTCORE_USER_POOL_ID=us-east-1_uQ2lN39dT
AGENTCORE_CLIENT_ID=78daptta2m4lb6k5jm3n2hd8oc
```

### IAM Permissions
The agent needs these additional permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agent:InvokeGateway",
                "bedrock-agent:QueryMemory",
                "bedrock-agent:StoreMemory",
                "bedrock-agent:AddEvent"
            ],
            "Resource": [
                "arn:aws:bedrock-agent:us-east-1:*:gateway/trade-matching-system-*",
                "arn:aws:bedrock-agent:us-east-1:*:memory-resource/trade-matching-system-*"
            ]
        }
    ]
}
```

## Production Deployment Steps

### Step 1: Enable AgentCore Gateway Integration
```python
# In trade_extraction_agent_strands.py, uncomment:
from bedrock_agentcore import Gateway

dynamodb_gateway = Gateway(name="trade-matching-system-dynamodb-gateway-production")
s3_gateway = Gateway(name="trade-matching-system-s3-gateway-production")
```

### Step 2: Enable AgentCore Memory Integration
```python
# In trade_extraction_agent_strands.py, uncomment:
from bedrock_agentcore import Memory

trade_patterns_memory = Memory(resource_name="trade-matching-system-trade-patterns-production")
processing_history_memory = Memory(resource_name="trade-matching-system-processing-history-production")
```

### Step 3: Update Agent Prompt
The agent will now:
1. Query memory for similar trade patterns before extraction
2. Use gateway tools for secure AWS operations
3. Store successful extraction patterns for future use
4. Track processing events for audit and optimization

## Benefits of AgentCore Integration

### Security & Compliance
- **Managed Authentication**: Gateway handles IAM roles and permissions
- **Audit Trail**: All operations logged through AgentCore
- **RBAC**: Role-based access control via Cognito integration

### Performance & Reliability
- **Connection Pooling**: Gateway manages AWS connections efficiently
- **Retry Logic**: Built-in retry and error handling
- **Rate Limiting**: Automatic throttling protection

### Intelligence & Learning
- **Pattern Recognition**: Memory stores successful extraction patterns
- **Continuous Learning**: Agent improves over time with historical data
- **Context Awareness**: Similar trade patterns inform extraction strategy

### Monitoring & Observability
- **Centralized Metrics**: All operations tracked in CloudWatch
- **Performance Analytics**: Gateway provides detailed usage metrics
- **Error Analysis**: Memory stores error patterns for improvement

## Migration Path

### Phase 1: Parallel Operation (Current)
- Keep direct boto3 tools as fallback
- Add AgentCore tools alongside existing tools
- Agent can choose which tools to use

### Phase 2: AgentCore Primary (Recommended)
- Make AgentCore tools primary choice
- Use direct tools only for fallback
- Monitor performance and reliability

### Phase 3: AgentCore Only (Future)
- Remove direct boto3 tools
- Full AgentCore integration
- Maximum security and observability

## Testing AgentCore Integration

```bash
# Test with sample trade
python deployment/swarm/trade_matching_swarm.py \
  data/BANK/FAB_26933659.pdf \
  --source-type BANK \
  --use-agentcore \
  --verbose

# Monitor AgentCore metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name GatewayInvocations \
  --dimensions Name=GatewayName,Value=trade-matching-system-dynamodb-gateway-production \
  --start-time 2025-01-15T00:00:00Z \
  --end-time 2025-01-15T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## Advanced Integration Features

### 1. Gateway Integration (High Priority)
Replace direct boto3 calls with AgentCore Gateway:
```python
# In trade_extraction_agent_strands.py, replace use_aws calls with:
from .agentcore_gateway_integration import AgentCoreGatewayIntegration

gateway = AgentCoreGatewayIntegration()
result = gateway.store_trade_data(table_name, trade_data)
```

### 2. Memory Integration (High Priority)
Enable learning from past extractions:
```python
# In trade_extraction_agent_strands.py, add memory-enhanced tools:
from .agentcore_memory_integration import use_agentcore_memory_enhanced

# Query for similar patterns before extraction
patterns = use_agentcore_memory_enhanced(
    operation="get_similar_patterns",
    data={"counterparty": "Goldman Sachs", "product_type": "SWAP", "source_type": "BANK"}
)

# Store successful patterns after extraction
use_agentcore_memory_enhanced(
    operation="store_pattern",
    data={"trade_data": extracted_data, "extraction_context": context}
)
```

### 3. Policy Integration (Medium Priority)
Enforce business rules and compliance:
```python
# In trade_extraction_agent_strands.py, add policy validation:
from .agentcore_policy_integration import validate_trade_extraction_with_policy

validation = validate_trade_extraction_with_policy(
    trade_data=extracted_trade,
    target_table="BankTradeData",
    user_role="operator"
)
```

### 4. Enhanced Observability (Medium Priority)
Advanced monitoring and PII redaction:
```python
# In trade_extraction_agent_strands.py, wrap your invoke function:
from .agentcore_observability_enhancement import create_enhanced_observability_wrapper

invoke = create_enhanced_observability_wrapper(invoke)
```

## Production Deployment Checklist

### Phase 1: Gateway & Memory (Immediate)
- [ ] Deploy AgentCore Gateway for DynamoDB and S3 operations
- [ ] Deploy AgentCore Memory resources for pattern learning
- [ ] Update agent to use gateway tools instead of direct boto3
- [ ] Enable memory pattern storage and retrieval

### Phase 2: Policy & Observability (Next Sprint)
- [ ] Deploy AgentCore Policy Engine with Cedar policies
- [ ] Integrate policy validation into extraction workflow
- [ ] Enable enhanced observability with PII redaction
- [ ] Set up custom CloudWatch metrics and alarms

### Phase 3: Advanced Features (Future)
- [ ] Implement A/B testing for extraction strategies
- [ ] Add real-time anomaly detection
- [ ] Enable automated model fine-tuning based on feedback
- [ ] Implement advanced compliance reporting

## Expected Benefits

### Security & Compliance
- **Managed Authentication**: Gateway handles IAM roles and permissions automatically
- **PII Protection**: Advanced redaction prevents sensitive data leakage
- **Policy Enforcement**: Automated compliance with business rules
- **Audit Trail**: Complete traceability of all operations

### Performance & Reliability
- **Connection Pooling**: Gateway manages AWS connections efficiently
- **Intelligent Caching**: Memory reduces redundant processing
- **Retry Logic**: Built-in error handling and recovery
- **Load Balancing**: Automatic scaling based on demand

### Intelligence & Learning
- **Pattern Recognition**: Memory learns from successful extractions
- **Continuous Improvement**: Agent gets smarter over time
- **Context Awareness**: Similar trade patterns inform extraction strategy
- **Quality Optimization**: Automatic detection and correction of extraction issues

### Monitoring & Operations
- **Real-time Metrics**: Advanced performance and quality tracking
- **Anomaly Detection**: Automatic identification of unusual patterns
- **Cost Optimization**: Token usage and cost tracking
- **Operational Insights**: Detailed analytics for process improvement

This comprehensive integration positions your trade extraction agent for enterprise-grade deployment with enhanced security, reliability, intelligence, and operational excellence.