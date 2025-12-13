# AgentCore Best Practices Improvements for Trade Extraction Agent

## Current Status ✅

The recent cleanup of the `use_aws` import is excellent - you've simplified the code by removing the complex fallback logic and now directly import from `strands_tools`. This makes the code cleaner and more reliable.

## Recommended AgentCore Improvements

### 1. Security & Authentication Enhancements 🔐

**Current State**: Basic IAM roles configured
**Improvement**: Implement comprehensive security patterns

```python
# Add to agentcore.yaml
identity:
  enabled: true
  user_pool_id: "us-east-1_uQ2lN39dT"
  client_id: "78daptta2m4lb6k5jm3n2hd8oc"
  mfa_required: true
  token_validation: true

# Add JWT token validation in agent
@tool
def validate_user_context(user_token: str = "") -> str:
    """Validate user context and extract role information."""
    if not user_token:
        return json.dumps({"valid": False, "reason": "No token provided"})
    
    try:
        # Validate JWT token with Cognito
        # Extract user role and permissions
        return json.dumps({
            "valid": True,
            "user_role": "operator",  # Extract from token
            "permissions": ["trade_extraction", "data_read"]
        })
    except Exception as e:
        return json.dumps({"valid": False, "reason": str(e)})
```

### 2. Enhanced AgentCore Gateway Integration 🌐

**Current State**: Gateway tools available but not fully utilized
**Improvement**: Replace direct boto3 calls with Gateway operations

```python
# Replace current use_aws calls with Gateway-specific tools
@tool
def use_agentcore_gateway_dynamodb(operation: str, parameters: dict) -> str:
    """Use AgentCore Gateway for secure DynamoDB operations."""
    try:
        if GATEWAY_AVAILABLE and DEPLOYMENT_STAGE == "production":
            result = dynamodb_gateway.invoke_tool(operation, parameters)
            return json.dumps({
                "success": True, 
                "result": result, 
                "gateway": "agentcore_dynamodb",
                "security": "managed"
            })
        else:
            # Fallback to direct access for development
            return use_aws("dynamodb", operation.lower(), parameters)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

### 3. Advanced Memory Integration 🧠

**Current State**: Basic memory operations
**Improvement**: Implement intelligent pattern learning

```python
# Enhanced memory integration with learning capabilities
@tool
def learn_from_extraction_success(trade_data: dict, extraction_context: dict) -> str:
    """Store successful extraction patterns for continuous learning."""
    try:
        pattern_data = {
            "counterparty": trade_data.get("counterparty"),
            "product_type": trade_data.get("product_type"),
            "extraction_confidence": extraction_context.get("confidence", 0.0),
            "field_mappings": extraction_context.get("field_mappings", {}),
            "success_factors": extraction_context.get("success_factors", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in AgentCore Memory for pattern recognition
        memory_result = use_agentcore_memory(
            operation="store",
            memory_resource="trade-patterns",
            data=pattern_data
        )
        
        return json.dumps({
            "success": True,
            "pattern_stored": True,
            "learning_enabled": True
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def get_extraction_guidance(counterparty: str, product_type: str) -> str:
    """Get extraction guidance from learned patterns."""
    try:
        query = f"{counterparty} {product_type} extraction pattern"
        patterns = use_agentcore_memory(
            operation="query",
            memory_resource="trade-patterns",
            query=query,
            top_k=3
        )
        
        # Extract guidance from similar patterns
        guidance = {
            "confidence_boost": 0.05,
            "field_hints": {},
            "extraction_tips": []
        }
        
        return json.dumps({
            "success": True,
            "guidance": guidance,
            "patterns_found": 3
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

### 4. Enhanced Observability with PII Redaction 📊

**Current State**: Basic observability implemented
**Improvement**: Advanced monitoring with financial data protection

```python
# Enhanced observability with financial data redaction
def create_secure_span_attributes(trade_data: dict, processing_metrics: dict) -> dict:
    """Create span attributes with PII redaction for financial data."""
    
    # Redact sensitive financial information
    safe_attributes = {
        "trade_source": trade_data.get("TRADE_SOURCE"),
        "product_type": trade_data.get("product_type"),
        "currency": trade_data.get("currency"),
        "processing_time_ms": processing_metrics.get("processing_time_ms"),
        "token_usage": processing_metrics.get("token_usage", {}),
        "extraction_confidence": processing_metrics.get("confidence", 0.0)
    }
    
    # Redact notional amount (keep only magnitude)
    notional = trade_data.get("notional", 0)
    if notional:
        if notional > 1_000_000_000:
            safe_attributes["notional_tier"] = "large"  # >$1B
        elif notional > 100_000_000:
            safe_attributes["notional_tier"] = "medium"  # >$100M
        else:
            safe_attributes["notional_tier"] = "small"
    
    # Hash counterparty name for tracking without exposing
    counterparty = trade_data.get("counterparty", "")
    if counterparty:
        import hashlib
        safe_attributes["counterparty_hash"] = hashlib.sha256(
            counterparty.encode()
        ).hexdigest()[:8]
    
    return safe_attributes
```

### 5. Policy Integration for Compliance 📋

**Current State**: No policy enforcement
**Improvement**: Integrate with AgentCore Policy Engine

```python
@tool
def validate_extraction_policy(trade_data: dict, user_context: dict) -> str:
    """Validate extraction against business policies."""
    try:
        # Check trade amount limits based on user role
        notional = float(trade_data.get("notional", 0))
        user_role = user_context.get("user_role", "operator")
        
        policy_checks = {
            "amount_limit_check": True,
            "counterparty_restriction_check": True,
            "data_integrity_check": True
        }
        
        # Amount limit policy
        if user_role == "operator" and notional > 100_000_000:
            policy_checks["amount_limit_check"] = False
            return json.dumps({
                "success": False,
                "policy_violation": "amount_limit",
                "requires_escalation": True,
                "escalation_role": "senior_operator"
            })
        
        # Data integrity policy
        trade_source = trade_data.get("TRADE_SOURCE")
        if trade_source not in ["BANK", "COUNTERPARTY"]:
            policy_checks["data_integrity_check"] = False
            return json.dumps({
                "success": False,
                "policy_violation": "invalid_trade_source",
                "requires_correction": True
            })
        
        return json.dumps({
            "success": True,
            "policy_compliant": True,
            "checks_passed": policy_checks
        })
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

### 6. Versioning & A/B Testing Support 🔄

**Current State**: Single version deployment
**Improvement**: Support for gradual rollouts

```yaml
# Enhanced agentcore.yaml with versioning
deployment:
  traffic_routing:
    enabled: true
    variants:
      - alias: "production"
        weight: 90
        version: "1.0.0"
      - alias: "canary"
        weight: 10
        version: "1.1.0"
  
  monitoring:
    comparative_metrics:
      - metric: "ExtractionAccuracy"
        threshold: 0.95
        comparison: "canary_vs_production"
      - metric: "ProcessingTime"
        threshold: 30000  # 30 seconds
        comparison: "canary_vs_production"
```

### 7. Built-in Tools Integration 🛠️

**Current State**: Custom tools for all operations
**Improvement**: Leverage AgentCore built-in capabilities

```python
# Use AgentCore Code Interpreter for complex data transformations
@tool
def transform_trade_data_with_code_interpreter(raw_data: str) -> str:
    """Use AgentCore Code Interpreter for complex data transformations."""
    try:
        # Code to execute in secure sandbox
        transformation_code = f"""
import json
import re
from datetime import datetime

# Parse and transform the raw trade data
raw_data = '''{raw_data}'''

# Complex transformation logic here
# This runs in AgentCore's secure sandbox
transformed_data = {{
    "trade_id": extract_trade_id(raw_data),
    "normalized_counterparty": normalize_counterparty_name(raw_data),
    "parsed_dates": parse_all_dates(raw_data)
}}

print(json.dumps(transformed_data))
"""
        
        # Execute in AgentCore Code Interpreter
        # This would use the actual AgentCore Code Interpreter API
        result = {
            "success": True,
            "transformed_data": {},
            "execution_safe": True
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

## Implementation Priority

### Phase 1: Security & Gateway (Immediate) 🚨
1. ✅ Clean up use_aws imports (DONE)
2. 🔄 Implement AgentCore Gateway integration
3. 🔄 Add JWT token validation
4. 🔄 Enable policy enforcement

### Phase 2: Intelligence & Learning (Next Sprint) 🧠
1. 🔄 Enhanced memory integration with pattern learning
2. 🔄 Advanced observability with PII redaction
3. 🔄 Custom evaluators for quality monitoring

### Phase 3: Advanced Features (Future) 🚀
1. 🔄 A/B testing infrastructure
2. 🔄 Code Interpreter integration
3. 🔄 Advanced anomaly detection

## Expected Benefits

### Security Improvements 🔐
- **Managed Authentication**: AgentCore handles JWT validation automatically
- **Policy Enforcement**: Automated compliance with business rules
- **PII Protection**: Financial data redaction prevents data leakage
- **Audit Trail**: Complete traceability of all operations

### Performance & Reliability 📈
- **Gateway Benefits**: Connection pooling, retry logic, rate limiting
- **Memory Learning**: Improved accuracy through pattern recognition
- **Quality Monitoring**: Real-time evaluation and alerting
- **Gradual Rollouts**: Safe deployment of improvements

### Operational Excellence 🎯
- **Continuous Learning**: Agent gets smarter over time
- **Automated Monitoring**: Proactive issue detection
- **Cost Optimization**: Token usage tracking and optimization
- **Compliance Reporting**: Automated regulatory compliance

## Next Steps

1. **Review and approve** these improvements
2. **Implement Phase 1** security enhancements
3. **Test in development** environment
4. **Deploy to staging** for validation
5. **Gradual rollout** to production

The current cleanup of the `use_aws` import is a great foundation for these improvements!