# AgentCore Best Practices - Trade Extraction Agent

## ✅ Current Implementation Status

### Security & Authentication
- [x] IAM role requirements documented in code comments
- [x] Environment-based configuration (no hardcoded credentials)
- [ ] **TODO**: Implement Cognito integration for user authentication
- [ ] **TODO**: Add API Gateway authentication for external access
- [ ] **TODO**: Implement request signing for agent-to-agent communication

**Recommendation**: For production deployment, configure IAM roles with least-privilege access:
```python
# Required IAM permissions (add to deployment/trade_extraction/iam_policy.json)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::trade-matching-system-agentcore-production/extracted/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:PutItem"],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/BankTradeData",
        "arn:aws:dynamodb:us-east-1:*:table/CounterpartyTradeData"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
    }
  ]
}
```

### Modular Services Integration

#### AgentCore Memory
- [ ] **TODO**: Integrate AgentCore Memory for conversation persistence
- [ ] **TODO**: Store extraction patterns and field mappings
- [ ] **TODO**: Enable semantic search for similar trade structures

**Implementation Guide**:
```python
# Add to trade_extraction_agent_strands.py
from bedrock_agentcore.memory import MemoryClient

# Initialize memory client
memory_client = MemoryClient(
    memory_id=os.getenv("AGENTCORE_MEMORY_ID"),
    region_name=REGION
)

# Store extraction patterns
memory_client.store_event({
    "trade_id": trade_id,
    "extraction_pattern": extracted_fields,
    "document_type": source_type,
    "timestamp": datetime.utcnow().isoformat()
})

# Query for similar extractions
similar_trades = memory_client.search_semantic(
    query=f"trades similar to {trade_id}",
    max_results=5
)
```

#### AgentCore Gateway
- [ ] **TODO**: Deploy Gateway for API management
- [ ] **TODO**: Configure rate limiting (e.g., 100 requests/minute)
- [ ] **TODO**: Add request/response transformation

**Configuration**:
```bash
# Deploy Gateway (run from deployment/trade_extraction/)
bedrock-agentcore gateway create \
  --name trade-extraction-gateway \
  --target-type agent \
  --target-arn <agent-arn> \
  --rate-limit 100 \
  --burst-limit 200
```

### Observability

#### Current Implementation
- [x] AgentCore Observability integrated
- [x] Token usage tracking with cost estimation
- [x] Error categorization (database, storage, model)
- [x] Processing time metrics
- [x] Correlation ID tracking

#### Improvements Needed
- [x] **DONE**: PII redaction patterns defined
- [ ] **TODO**: Implement actual PII filtering in observability spans
- [ ] **TODO**: Configure CloudWatch Logs Insights queries
- [ ] **TODO**: Set up alarms for error rates and latency

**PII Redaction Implementation**:
```python
def redact_sensitive_data(data: str) -> str:
    """Redact PII from observability data."""
    import re
    for pattern_name, pattern in PII_PATTERNS.items():
        data = re.sub(pattern, r"\1[REDACTED]", data)
    return data

# Use in observability spans
if span_context:
    safe_response = redact_sensitive_data(response_text)
    span_context.set_attribute("agent_response_preview", safe_response[:200])
```

**CloudWatch Alarms**:
```bash
# Create alarm for high error rate
aws cloudwatch put-metric-alarm \
  --alarm-name trade-extraction-high-error-rate \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name ErrorRate \
  --namespace AgentCore/TradeExtraction \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### Built-in Tools

#### Current Usage
- [x] `use_aws` tool for S3 and DynamoDB operations
- [x] **IMPLEMENTED**: Tool resource reuse via `aws_resources.py` module
- [ ] **Consider**: AgentCore Browser for web-based trade confirmations
- [ ] **Consider**: AgentCore Code Interpreter for complex calculations

**Tool Resource Reuse Pattern** (✅ Implemented):
The system uses a shared `AWSResourceManager` class that maintains singleton AWS client instances:

```python
# aws_resources.py - Reusable resource manager
class AWSResourceManager:
    def __init__(self):
        self._clients: Dict[str, Any] = {}  # Cached clients
        
    def get_client(self, service: str):
        if service not in self._clients:
            # Create once with proper config (timeouts, retries)
            self._clients[service] = self.session.client(service, config=config)
        return self._clients[service]  # Reuse existing

# In agent tools
def download_pdf_from_s3(...):
    s3_client = get_aws_client('s3')  # Gets shared client
```

**Benefits**:
- Connection pooling across multiple tool calls
- Reduced overhead from client initialization
- Consistent configuration (timeouts, retries) across all operations
- Better performance for high-volume processing

**When to use Browser**:
- Processing HTML-based trade confirmations
- Scraping counterparty portals for trade data
- Validating trade details against external systems

**When to use Code Interpreter**:
- Complex notional calculations with multiple currencies
- Statistical analysis of matching patterns
- Custom validation logic for exotic derivatives

### Versioning & Aliases

#### Current Implementation
- [x] Agent version tracking (`AGENT_VERSION` env var)
- [x] Agent alias support (`AGENT_ALIAS` env var)
- [ ] **TODO**: Implement A/B testing framework
- [ ] **TODO**: Create deployment pipeline with gradual rollout

**A/B Testing Strategy**:
```python
# Route 10% of traffic to new version for testing
if random.random() < 0.1:
    agent_version = "2.0.0"  # New version with improved extraction
else:
    agent_version = "1.0.0"  # Stable version

# Track performance by version in observability
span_context.set_attribute("agent_version", agent_version)
span_context.set_attribute("ab_test_group", "treatment" if agent_version == "2.0.0" else "control")
```

**Deployment Pipeline**:
```bash
# 1. Deploy new version as alias
bedrock-agentcore agent deploy \
  --agent-file trade_extraction_agent_strands.py \
  --version 2.0.0 \
  --alias canary

# 2. Route 10% traffic to canary
bedrock-agentcore agent update-routing \
  --agent-name trade-extraction-agent \
  --canary-weight 10

# 3. Monitor metrics for 24 hours
# 4. If successful, promote to production
bedrock-agentcore agent promote \
  --agent-name trade-extraction-agent \
  --from-alias canary \
  --to-alias production
```

## 🎯 Priority Recommendations

### High Priority (Implement Now)
1. **Security**: Create IAM policy JSON and document authentication flow
2. **PII Redaction**: Implement actual filtering in observability spans
3. **Error Handling**: Add retry logic with exponential backoff for transient failures

### Medium Priority (Next Sprint)
4. **Memory Integration**: Store extraction patterns for learning
5. **Gateway Deployment**: Add rate limiting and API management
6. **Monitoring**: Set up CloudWatch alarms and dashboards

### Low Priority (Future Enhancement)
7. **A/B Testing**: Implement version comparison framework
8. **Browser Tool**: Add support for HTML-based confirmations
9. **Advanced Analytics**: Track extraction accuracy over time

## 📊 Success Metrics

Track these KPIs to measure agent effectiveness:
- **Extraction Accuracy**: % of trades extracted without errors
- **Processing Time**: P50, P95, P99 latency
- **Cost per Trade**: Token usage × pricing
- **Error Rate**: % of failed extractions
- **SLA Compliance**: % of trades processed within target time

## 🔒 Security Checklist

Before production deployment:
- [ ] IAM roles configured with least-privilege access
- [ ] Secrets stored in AWS Secrets Manager (not environment variables)
- [ ] VPC endpoints configured for private AWS service access
- [ ] Encryption at rest enabled for DynamoDB tables
- [ ] Encryption in transit enforced (TLS 1.2+)
- [ ] CloudTrail logging enabled for audit trail
- [ ] PII redaction implemented in all logs
- [ ] Rate limiting configured to prevent abuse
- [ ] Input validation for all payload fields
- [ ] Output sanitization to prevent injection attacks

## 🤖 LLM-Centric Design Principles

### Current Implementation (✅ Fully Optimized)

The Trade Extraction Agent follows advanced LLM-centric design:

1. **LLM as Autonomous Decision Maker**
   - Purely goal-oriented prompts with minimal prescription
   - Agent analyzes, reasons, and determines its own approach
   - No workflow steps or examples that constrain thinking
   - Temperature set to 0.3 to enable reasoning while maintaining consistency

2. **High-Level Tool Architecture**
   - `use_aws`: Universal AWS operations tool (agent decides which operations)
   - `get_extraction_context`: Provides business rules and constraints on-demand
   - No prescriptive helper tools that force a specific workflow
   - Tools represent capabilities, not steps

3. **Emergent Strategy**
   - Agent discovers the optimal extraction approach through reasoning
   - Can adapt to different data structures and edge cases
   - Validates data based on understanding of business rules
   - Determines table routing through analysis, not hardcoded logic

4. **Minimal Prompt Design**
   - System prompt focuses on mission and autonomy
   - Task prompts provide only goal and context
   - No examples that prescribe the "right" approach
   - Agent has freedom to innovate and optimize

### Example: Evolution of Design

**❌ Prescriptive (Anti-Pattern)**:
```
Step 1: Read from S3 using get_object
Step 2: Extract these specific fields: [list]
Step 3: Validate using validate_trade_data tool
Step 4: Determine table using determine_target_table tool
Step 5: Store in DynamoDB using put_item
```

**⚠️ Semi-Prescriptive (Better, but still limiting)**:
```
Your Goal: Transform canonical output into structured trade record

Available Resources: [tools and tables]
Business Rules: [constraints]
Success Criteria: [what defines success]

Example approach:
1. Read canonical output from S3
2. Extract and validate fields
3. Store in appropriate table

Determine the optimal approach to achieve this goal.
```

**✅ Fully Autonomous (Current Implementation)**:
```
Goal: Extract and store trade data from canonical adapter output.

Context:
- Document: {document_id}
- Canonical Output: {canonical_output_location}
- Source Type: {source_type or "Unknown - determine from data"}

Success Criteria:
- Trade data extracted with all relevant fields
- Data stored in the correct DynamoDB table
- Data integrity maintained

Analyze the canonical output, reason about the data structure, 
and determine the best approach to achieve this goal.
```

### Key Improvements Made

1. **Removed Prescriptive Helper Tools**
   - Eliminated `validate_trade_data` (agent reasons about validation)
   - Eliminated `determine_target_table` (agent determines routing)
   - Replaced with `get_extraction_context` (provides info, not decisions)

2. **Simplified System Prompt**
   - Removed step-by-step examples
   - Removed prescriptive tool usage patterns
   - Added "Decision-Making Framework" that encourages reasoning
   - Emphasized autonomy and critical thinking

3. **Optimized Temperature**
   - Changed from 0.4 to 0.3
   - Balances reasoning ability with consistency for financial data
   - Enables the agent to think through edge cases

4. **Minimal Task Prompts**
   - Removed all workflow hints
   - Provides only goal, context, and success criteria
   - Agent discovers the approach through analysis

## 📚 Additional Resources

- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [AgentCore Memory Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-memory.html)
- [AgentCore Gateway Setup](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-gateway.html)
- [Observability Best Practices](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-observability.html)
- [Strands SDK Documentation](https://docs.strands.ai/)
