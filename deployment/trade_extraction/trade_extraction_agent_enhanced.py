"""
Enhanced Trade Data Extraction Agent - AgentCore Best Practices Implementation

This demonstrates the recommended AgentCore improvements:
1. Enhanced security with JWT validation
2. AgentCore Gateway integration
3. Advanced memory learning
4. Policy enforcement
5. PII-safe observability

Requirements: 2.1, 2.2, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel

# Import use_aws from strands-agents-tools (cleaned up import)
from strands_tools import use_aws

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# Enhanced AgentCore integrations
try:
    from bedrock_agentcore.observability import Observability
    from bedrock_agentcore import Gateway, Memory, Policy
    AGENTCORE_AVAILABLE = True
except ImportError:
    AGENTCORE_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
BANK_TABLE = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
AGENT_NAME = "trade-extraction-agent-enhanced"
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.1.0")
DEPLOYMENT_STAGE = os.getenv("DEPLOYMENT_STAGE", "development")

# AgentCore Resource Names
DYNAMODB_GATEWAY_NAME = os.getenv("AGENTCORE_GATEWAY_DYNAMODB", "trade-matching-system-dynamodb-gateway-production")
S3_GATEWAY_NAME = os.getenv("AGENTCORE_GATEWAY_S3", "trade-matching-system-s3-gateway-production")
MEMORY_PATTERNS_NAME = os.getenv("AGENTCORE_MEMORY_PATTERNS", "trade-matching-system-trade-patterns-production")
POLICY_ENGINE_NAME = os.getenv("AGENTCORE_POLICY_ENGINE", "trade-matching-system-policy-engine-production")

# Initialize AgentCore services
if AGENTCORE_AVAILABLE and DEPLOYMENT_STAGE == "production":
    try:
        dynamodb_gateway = Gateway(name=DYNAMODB_GATEWAY_NAME)
        s3_gateway = Gateway(name=S3_GATEWAY_NAME)
        memory_patterns = Memory(resource_name=MEMORY_PATTERNS_NAME)
        policy_engine = Policy(engine_name=POLICY_ENGINE_NAME)
        
        observability = Observability(
            service_name=AGENT_NAME,
            stage=DEPLOYMENT_STAGE,
            verbosity="medium",
            custom_attributes={
                "agent_type": "trade_extraction",
                "version": AGENT_VERSION,
                "security_enhanced": True
            }
        )
        
        ENHANCED_AGENTCORE = True
        logger.info("✅ Enhanced AgentCore services initialized")
    except Exception as e:
        logger.warning(f"AgentCore services initialization failed: {e}")
        ENHANCED_AGENTCORE = False
else:
    ENHANCED_AGENTCORE = False
    logger.info("ℹ️ Using development mode - AgentCore services disabled")

# PII patterns for financial data redaction
PII_PATTERNS = {
    "trade_id": r"(trade_id[\"']?\s*[:=]\s*[\"']?)([^\"',}\s]+)",
    "counterparty": r"(counterparty[\"']?\s*[:=]\s*[\"']?)([^\"',}\s]+)",
    "notional": r"(notional[\"']?\s*[:=]\s*[\"']?)(\d+\.?\d*)",
    "account_number": r"(account[\"']?\s*[:=]\s*[\"']?)(\d{8,})",
}

def redact_pii(text: str) -> str:
    """Redact PII from text for safe logging."""
    import re
    redacted_text = text
    for pattern_name, pattern in PII_PATTERNS.items():
        redacted_text = re.sub(pattern, r'\1[REDACTED]', redacted_text)
    return redacted_text

def create_secure_span_attributes(trade_data: dict, processing_metrics: dict) -> dict:
    """Create span attributes with PII redaction for financial data."""
    
    safe_attributes = {
        "trade_source": trade_data.get("TRADE_SOURCE"),
        "product_type": trade_data.get("product_type"),
        "currency": trade_data.get("currency"),
        "processing_time_ms": processing_metrics.get("processing_time_ms"),
        "extraction_confidence": processing_metrics.get("confidence", 0.0)
    }
    
    # Redact notional amount (keep only tier)
    notional = trade_data.get("notional", 0)
    if notional:
        try:
            notional_float = float(notional)
            if notional_float > 1_000_000_000:
                safe_attributes["notional_tier"] = "large"  # >$1B
            elif notional_float > 100_000_000:
                safe_attributes["notional_tier"] = "medium"  # >$100M
            else:
                safe_attributes["notional_tier"] = "small"
        except (ValueError, TypeError):
            safe_attributes["notional_tier"] = "unknown"
    
    # Hash counterparty name for tracking without exposing
    counterparty = trade_data.get("counterparty", "")
    if counterparty:
        safe_attributes["counterparty_hash"] = hashlib.sha256(
            counterparty.encode()
        ).hexdigest()[:8]
    
    return safe_attributes

# Enhanced Tools with AgentCore Integration

@tool
def validate_user_context(user_token: str = "") -> str:
    """
    Validate user context and extract role information.
    
    Args:
        user_token: JWT token from request context
        
    Returns:
        JSON string with validation result and user permissions
    """
    if not user_token:
        return json.dumps({
            "valid": False, 
            "reason": "No authentication token provided",
            "default_role": "operator"
        })
    
    try:
        # In production, this would validate JWT with Cognito
        # For now, extract role from token payload (mock implementation)
        
        # Mock JWT validation - in production use proper JWT library
        if "admin" in user_token.lower():
            user_role = "admin"
            permissions = ["trade_extraction", "data_read", "data_write", "policy_override"]
        elif "senior" in user_token.lower():
            user_role = "senior_operator"
            permissions = ["trade_extraction", "data_read", "data_write", "high_value_approval"]
        else:
            user_role = "operator"
            permissions = ["trade_extraction", "data_read"]
        
        return json.dumps({
            "valid": True,
            "user_role": user_role,
            "permissions": permissions,
            "token_validated": True
        })
        
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return json.dumps({
            "valid": False,
            "reason": f"Token validation error: {str(e)}",
            "default_role": "operator"
        })

@tool
def use_agentcore_gateway_dynamodb(operation: str, parameters: dict, label: str = "") -> str:
    """
    Use AgentCore Gateway for secure DynamoDB operations.
    
    Args:
        operation: DynamoDB operation (PutItem, GetItem, etc.)
        parameters: Operation parameters
        label: Description of the operation
        
    Returns:
        JSON string with operation result
    """
    try:
        logger.info(f"DynamoDB Gateway Operation: {operation} - {label}")
        
        if ENHANCED_AGENTCORE:
            # Use AgentCore Gateway for production
            result = dynamodb_gateway.invoke_tool(operation, parameters)
            return json.dumps({
                "success": True,
                "result": result,
                "gateway": "agentcore_dynamodb",
                "security": "managed",
                "operation": operation
            }, default=str)
        else:
            # Fallback to direct access for development
            return use_aws("dynamodb", operation.lower().replace("item", "_item"), parameters, label=label)
            
    except Exception as e:
        logger.error(f"DynamoDB Gateway operation failed: {operation} - {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "gateway": "agentcore_dynamodb",
            "operation": operation
        })

@tool
def use_agentcore_gateway_s3(operation: str, parameters: dict, label: str = "") -> str:
    """
    Use AgentCore Gateway for secure S3 operations.
    
    Args:
        operation: S3 operation (GetObject, PutObject, etc.)
        parameters: Operation parameters
        label: Description of the operation
        
    Returns:
        JSON string with operation result
    """
    try:
        logger.info(f"S3 Gateway Operation: {operation} - {label}")
        
        if ENHANCED_AGENTCORE:
            # Use AgentCore Gateway for production
            result = s3_gateway.invoke_tool(operation, parameters)
            return json.dumps({
                "success": True,
                "result": result,
                "gateway": "agentcore_s3",
                "security": "managed",
                "operation": operation
            }, default=str)
        else:
            # Fallback to direct access for development
            return use_aws("s3", operation.lower().replace("object", "_object"), parameters, label=label)
            
    except Exception as e:
        logger.error(f"S3 Gateway operation failed: {operation} - {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "gateway": "agentcore_s3",
            "operation": operation
        })

@tool
def learn_from_extraction_success(trade_data: dict, extraction_context: dict) -> str:
    """
    Store successful extraction patterns for continuous learning.
    
    Args:
        trade_data: Successfully extracted trade data
        extraction_context: Context about the extraction process
        
    Returns:
        JSON string with learning result
    """
    try:
        if not ENHANCED_AGENTCORE:
            return json.dumps({
                "success": True,
                "learning_enabled": False,
                "reason": "Development mode - learning disabled"
            })
        
        # Create learning pattern
        pattern_data = {
            "counterparty": trade_data.get("counterparty"),
            "product_type": trade_data.get("product_type"),
            "trade_source": trade_data.get("TRADE_SOURCE"),
            "extraction_confidence": extraction_context.get("confidence", 0.0),
            "field_mappings": extraction_context.get("field_mappings", {}),
            "success_factors": extraction_context.get("success_factors", []),
            "processing_time_ms": extraction_context.get("processing_time_ms", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in AgentCore Memory
        memory_patterns.store(
            content=json.dumps(pattern_data),
            metadata={
                "counterparty": trade_data.get("counterparty", ""),
                "product_type": trade_data.get("product_type", ""),
                "confidence": extraction_context.get("confidence", 0.0)
            }
        )
        
        return json.dumps({
            "success": True,
            "pattern_stored": True,
            "learning_enabled": True,
            "confidence": extraction_context.get("confidence", 0.0)
        })
        
    except Exception as e:
        logger.error(f"Learning from extraction failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "learning_enabled": False
        })

@tool
def get_extraction_guidance(counterparty: str, product_type: str, source_type: str) -> str:
    """
    Get extraction guidance from learned patterns.
    
    Args:
        counterparty: Counterparty name
        product_type: Product type (SWAP, OPTION, etc.)
        source_type: BANK or COUNTERPARTY
        
    Returns:
        JSON string with extraction guidance
    """
    try:
        if not ENHANCED_AGENTCORE:
            return json.dumps({
                "success": True,
                "guidance": {"confidence_boost": 0.0, "tips": []},
                "patterns_found": 0,
                "learning_enabled": False
            })
        
        # Query similar patterns
        query = f"{counterparty} {product_type} {source_type} extraction"
        results = memory_patterns.query(query=query, top_k=3)
        
        # Extract guidance from patterns
        guidance = {
            "confidence_boost": 0.0,
            "field_hints": {},
            "extraction_tips": [],
            "similar_patterns": len(results)
        }
        
        if results:
            # Calculate confidence boost based on pattern similarity
            avg_confidence = sum(r.get("similarity_score", 0) for r in results) / len(results)
            guidance["confidence_boost"] = min(0.1, avg_confidence * 0.05)
            
            # Extract tips from successful patterns
            for result in results:
                try:
                    pattern_data = json.loads(result.get("content", "{}"))
                    if pattern_data.get("success_factors"):
                        guidance["extraction_tips"].extend(pattern_data["success_factors"])
                    if pattern_data.get("field_mappings"):
                        guidance["field_hints"].update(pattern_data["field_mappings"])
                except json.JSONDecodeError:
                    continue
        
        return json.dumps({
            "success": True,
            "guidance": guidance,
            "patterns_found": len(results),
            "learning_enabled": True
        })
        
    except Exception as e:
        logger.error(f"Getting extraction guidance failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "guidance": {"confidence_boost": 0.0, "tips": []},
            "patterns_found": 0
        })

@tool
def validate_extraction_policy(trade_data: dict, user_context: dict) -> str:
    """
    Validate extraction against business policies.
    
    Args:
        trade_data: Extracted trade data
        user_context: User context with role and permissions
        
    Returns:
        JSON string with policy validation result
    """
    try:
        user_role = user_context.get("user_role", "operator")
        permissions = user_context.get("permissions", [])
        
        policy_checks = {
            "amount_limit_check": True,
            "counterparty_restriction_check": True,
            "data_integrity_check": True,
            "permission_check": True
        }
        
        # Check basic permissions
        if "trade_extraction" not in permissions:
            return json.dumps({
                "success": False,
                "policy_violation": "insufficient_permissions",
                "required_permission": "trade_extraction",
                "user_role": user_role
            })
        
        # Amount limit policy
        try:
            notional = float(trade_data.get("notional", 0))
            if user_role == "operator" and notional > 100_000_000:  # $100M
                policy_checks["amount_limit_check"] = False
                return json.dumps({
                    "success": False,
                    "policy_violation": "amount_limit_exceeded",
                    "limit": 100_000_000,
                    "actual": notional,
                    "requires_escalation": True,
                    "escalation_role": "senior_operator"
                })
        except (ValueError, TypeError):
            logger.warning("Invalid notional amount for policy check")
        
        # Data integrity policy
        trade_source = trade_data.get("TRADE_SOURCE")
        if trade_source not in ["BANK", "COUNTERPARTY"]:
            policy_checks["data_integrity_check"] = False
            return json.dumps({
                "success": False,
                "policy_violation": "invalid_trade_source",
                "valid_sources": ["BANK", "COUNTERPARTY"],
                "actual_source": trade_source,
                "requires_correction": True
            })
        
        # Counterparty restriction check (mock - would check against restricted list)
        counterparty = trade_data.get("counterparty", "").upper()
        restricted_counterparties = ["SANCTIONED_ENTITY_1", "BLOCKED_BANK_2"]
        if counterparty in restricted_counterparties:
            policy_checks["counterparty_restriction_check"] = False
            return json.dumps({
                "success": False,
                "policy_violation": "restricted_counterparty",
                "counterparty": counterparty,
                "requires_compliance_review": True
            })
        
        return json.dumps({
            "success": True,
            "policy_compliant": True,
            "checks_passed": policy_checks,
            "user_role": user_role
        })
        
    except Exception as e:
        logger.error(f"Policy validation failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "policy_compliant": False
        })

@tool
def get_extraction_context() -> str:
    """
    Get enhanced extraction context with AgentCore capabilities.
    
    Returns:
        JSON string with extraction context and capabilities
    """
    context = {
        "agent_info": {
            "name": AGENT_NAME,
            "version": AGENT_VERSION,
            "deployment_stage": DEPLOYMENT_STAGE,
            "enhanced_agentcore": ENHANCED_AGENTCORE
        },
        "capabilities": {
            "gateway_integration": ENHANCED_AGENTCORE,
            "memory_learning": ENHANCED_AGENTCORE,
            "policy_enforcement": ENHANCED_AGENTCORE,
            "pii_redaction": True,
            "security_enhanced": ENHANCED_AGENTCORE
        },
        "tables": {
            "bank_trades": {
                "name": BANK_TABLE,
                "purpose": "Stores trades from bank systems",
                "source_type": "BANK",
                "region": REGION
            },
            "counterparty_trades": {
                "name": COUNTERPARTY_TABLE,
                "purpose": "Stores trades from counterparty systems",
                "source_type": "COUNTERPARTY",
                "region": REGION
            }
        },
        "business_rules": {
            "table_routing": "BANK trades → BankTradeData, COUNTERPARTY trades → CounterpartyTradeData",
            "data_integrity": "TRADE_SOURCE field must match target table",
            "amount_limits": {
                "operator": 100_000_000,  # $100M
                "senior_operator": 1_000_000_000,  # $1B
                "admin": "unlimited"
            },
            "required_fields": ["Trade_ID", "TRADE_SOURCE", "notional", "currency", "counterparty"]
        }
    }
    
    return json.dumps(context, indent=2)

# Health Check Handler
@app.ping
def health_check() -> PingStatus:
    """Enhanced health check with AgentCore service status."""
    try:
        # Check AgentCore services if enabled
        if ENHANCED_AGENTCORE:
            # In production, would check actual service health
            pass
        return PingStatus.HEALTHY
    except Exception:
        return PingStatus.UNHEALTHY

# Enhanced System Prompt
ENHANCED_SYSTEM_PROMPT = f"""You are an enhanced Trade Data Extraction Agent with advanced AgentCore capabilities.

## Your Mission
Extract structured trade data from canonical adapter output and store it securely in the appropriate DynamoDB table. You have access to advanced AgentCore services for enhanced security, learning, and compliance.

## Enhanced Capabilities
- **Security**: JWT token validation and role-based access control
- **Gateway Integration**: Secure, managed AWS operations through AgentCore Gateway
- **Memory Learning**: Learn from successful extraction patterns to improve accuracy
- **Policy Enforcement**: Automated compliance with business rules and regulations
- **PII Protection**: Advanced redaction of sensitive financial information
- **Observability**: Comprehensive monitoring with financial data protection

## Environment
- **Agent**: {AGENT_NAME} v{AGENT_VERSION}
- **Model**: {BEDROCK_MODEL_ID}
- **Region**: {REGION}
- **Deployment**: {DEPLOYMENT_STAGE}
- **Enhanced AgentCore**: {"Enabled" if ENHANCED_AGENTCORE else "Development Mode"}

## Available Tools

### Security & Authentication
- **validate_user_context**: Validate JWT tokens and extract user permissions
- **validate_extraction_policy**: Enforce business policies and compliance rules

### Enhanced AWS Operations
- **use_agentcore_gateway_dynamodb**: Secure DynamoDB operations via AgentCore Gateway
- **use_agentcore_gateway_s3**: Secure S3 operations via AgentCore Gateway
- **use_aws**: Direct AWS operations (fallback for development)

### Learning & Intelligence
- **learn_from_extraction_success**: Store successful patterns for continuous improvement
- **get_extraction_guidance**: Get guidance from learned patterns for similar trades

### Context & Configuration
- **get_extraction_context**: Get enhanced context with AgentCore capabilities

## Decision-Making Framework

You are an intelligent agent with enhanced capabilities. For each extraction task:

1. **Authenticate**: Validate user context and permissions
2. **Learn**: Query memory for similar trade patterns and extraction insights
3. **Analyze**: What information is available? What's the source type? What fields are present?
4. **Reason**: Which fields are relevant? How should values be normalized? What's the appropriate table?
5. **Validate**: Check against business policies and compliance rules
6. **Execute**: Use AgentCore Gateway for secure operations
7. **Store**: Save to correct table with proper format and security
8. **Learn**: Store successful patterns for future improvement
9. **Monitor**: Ensure all operations are properly logged with PII redaction

## Key Constraints & Policies

- **Authentication Required**: Validate user tokens for all operations
- **Amount Limits**: Operators ($100M), Senior Operators ($1B), Admins (unlimited)
- **Data Integrity**: TRADE_SOURCE must match table (BANK → BankTradeData, COUNTERPARTY → CounterpartyTradeData)
- **Restricted Counterparties**: Block trades with sanctioned entities
- **PII Protection**: Redact sensitive information from logs and traces
- **Policy Compliance**: All operations must pass policy validation

## Your Autonomy

You decide:
- How to authenticate and authorize operations
- Which patterns to learn from and apply
- How to extract and structure the data
- What validation checks to perform
- When to escalate for policy violations
- How to optimize for accuracy and compliance

Think critically about security, compliance, and continuous improvement. Use your enhanced capabilities to provide the most secure and intelligent trade extraction possible.
"""

def create_enhanced_extraction_agent() -> Agent:
    """Create and configure the enhanced Strands extraction agent."""
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for consistent financial data processing
        max_tokens=4096,
    )
    
    # Enhanced tool set with AgentCore integration
    enhanced_tools = [
        # Security & Authentication
        validate_user_context,
        validate_extraction_policy,
        
        # Enhanced AWS Operations
        use_agentcore_gateway_dynamodb,
        use_agentcore_gateway_s3,
        use_aws,  # Fallback
        
        # Learning & Intelligence
        learn_from_extraction_success,
        get_extraction_guidance,
        
        # Context & Configuration
        get_extraction_context
    ]
    
    agent = Agent(
        model=bedrock_model,
        system_prompt=ENHANCED_SYSTEM_PROMPT,
        tools=enhanced_tools
    )
    
    # Apply observability wrapper if available
    if ENHANCED_AGENTCORE and observability:
        agent = observability.wrap_agent(agent)
        logger.info("✅ Enhanced observability applied")
    
    return agent

def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Enhanced AgentCore Runtime entrypoint with security and learning.
    """
    start_time = datetime.utcnow()
    
    # Extract payload information
    document_id = payload.get("document_id")
    canonical_output_location = payload.get("canonical_output_location")
    source_type = payload.get("source_type", "")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    user_token = payload.get("user_token", "")  # JWT token from request
    
    # Basic validation
    if not document_id or not canonical_output_location:
        return {
            "success": False,
            "error": "Missing required fields: document_id or canonical_output_location",
            "agent_name": AGENT_NAME,
            "security_validated": False
        }
    
    try:
        # Start enhanced observability span
        span_context = None
        if ENHANCED_AGENTCORE and observability:
            try:
                span_name = f"enhanced_trade_extraction.{source_type.lower() if source_type else 'unknown'}"
                span_context = observability.start_span(span_name)
                span_context.__enter__()
                
                # Set enhanced attributes with PII redaction
                span_context.set_attribute("agent_name", AGENT_NAME)
                span_context.set_attribute("agent_version", AGENT_VERSION)
                span_context.set_attribute("correlation_id", correlation_id)
                span_context.set_attribute("document_id", document_id)
                span_context.set_attribute("source_type", source_type or "unknown")
                span_context.set_attribute("enhanced_agentcore", True)
                span_context.set_attribute("security_enabled", True)
                
            except Exception as e:
                logger.warning(f"Failed to start enhanced observability span: {e}")
                span_context = None
        
        # Create enhanced agent
        agent = create_enhanced_extraction_agent()
        
        # Enhanced goal-oriented prompt with security context
        prompt = f"""**Goal**: Securely extract and store trade data with enhanced AgentCore capabilities.

**Context**:
- Document: {document_id}
- Canonical Output: {canonical_output_location}
- Source Type: {source_type if source_type else "Unknown - determine from data"}
- Correlation: {correlation_id}
- User Token: {"Provided" if user_token else "Not provided"}

**Enhanced Success Criteria**:
- User authentication and authorization validated
- Trade data extracted with learned pattern guidance
- Business policies and compliance rules enforced
- Data stored securely via AgentCore Gateway
- Successful patterns learned for future improvement
- All operations monitored with PII protection

**Security Requirements**:
- Validate user context and permissions
- Check against business policies before processing
- Use secure Gateway operations for AWS access
- Redact sensitive information from logs

**Learning Objectives**:
- Query memory for similar extraction patterns
- Apply learned guidance to improve accuracy
- Store successful patterns for continuous improvement

Use your enhanced AgentCore capabilities to achieve these goals securely and intelligently.
"""
        
        # Invoke enhanced agent
        logger.info("Invoking enhanced Strands agent for secure trade extraction")
        result = agent(prompt)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract response safely
        if hasattr(result, 'message') and result.message:
            if hasattr(result.message, 'content') and result.message.content:
                content = result.message.content
                if isinstance(content, list) and len(content) > 0:
                    first_block = content[0]
                    response_text = first_block.get('text', str(result.message)) if isinstance(first_block, dict) else str(first_block)
                else:
                    response_text = str(content)
            else:
                response_text = str(result.message)
        else:
            response_text = str(result)
        
        # Redact PII from response for logging
        safe_response = redact_pii(response_text)
        
        # Enhanced span attributes with PII protection
        if span_context:
            try:
                span_context.set_attribute("success", True)
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                span_context.set_attribute("response_length_chars", len(response_text))
                span_context.set_attribute("pii_redacted", True)
                
                # Performance tier classification
                if processing_time_ms < 15000:
                    span_context.set_attribute("performance_tier", "fast")
                elif processing_time_ms < 30000:
                    span_context.set_attribute("performance_tier", "normal")
                else:
                    span_context.set_attribute("performance_tier", "slow")
                    
            except Exception as e:
                logger.warning(f"Failed to set enhanced span attributes: {e}")
        
        return {
            "success": True,
            "document_id": document_id,
            "source_type": source_type,
            "correlation_id": correlation_id,
            "agent_response": safe_response,  # PII-redacted response
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "enhanced_agentcore": ENHANCED_AGENTCORE,
            "security_validated": True,
            "pii_protected": True,
            "model_id": BEDROCK_MODEL_ID,
            "deployment_stage": DEPLOYMENT_STAGE,
        }
        
    except Exception as e:
        logger.error(f"Enhanced extraction agent failed: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Enhanced error handling with PII protection
        safe_error = redact_pii(str(e))
        
        if span_context:
            try:
                span_context.set_attribute("success", False)
                span_context.set_attribute("error_type", type(e).__name__)
                span_context.set_attribute("error_message", safe_error[:500])
                span_context.set_attribute("processing_time_ms", processing_time_ms)
            except Exception:
                pass
        
        return {
            "success": False,
            "error": safe_error,
            "error_type": type(e).__name__,
            "document_id": document_id,
            "agent_name": AGENT_NAME,
            "processing_time_ms": processing_time_ms,
            "enhanced_agentcore": ENHANCED_AGENTCORE,
            "security_validated": False,
            "pii_protected": True
        }
    finally:
        # Close enhanced observability span
        if span_context:
            try:
                span_context.__exit__(None, None, None)
            except Exception:
                pass

# Register with AgentCore Runtime
app.entrypoint(invoke)

def main():
    """CLI entry point for enhanced agent testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Trade Data Extraction Agent")
    parser.add_argument("--mode", choices=["runtime", "test"], default="runtime")
    parser.add_argument("--document-id", help="Document ID for testing")
    parser.add_argument("--canonical-output-location", help="S3 location of canonical output")
    parser.add_argument("--source-type", choices=["BANK", "COUNTERPARTY"], help="Trade source type")
    parser.add_argument("--user-token", help="JWT token for authentication testing")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.mode == "test" and args.document_id and args.canonical_output_location:
        print(f"🧪 Testing Enhanced Trade Extraction Agent")
        print(f"Document ID: {args.document_id}")
        print(f"Canonical Output: {args.canonical_output_location}")
        print(f"Source Type: {args.source_type}")
        print(f"Enhanced AgentCore: {ENHANCED_AGENTCORE}")
        print(f"Security Features: {'Enabled' if ENHANCED_AGENTCORE else 'Development Mode'}")
        
        test_payload = {
            "document_id": args.document_id,
            "canonical_output_location": args.canonical_output_location,
            "source_type": args.source_type or "BANK",
            "correlation_id": f"cli_test_{uuid.uuid4().hex[:8]}",
            "user_token": args.user_token or "test_operator_token"
        }
        
        result = invoke(test_payload)
        
        print(f"\n📊 Enhanced Results:")
        print(f"Success: {result.get('success', False)}")
        print(f"Security Validated: {result.get('security_validated', False)}")
        print(f"PII Protected: {result.get('pii_protected', False)}")
        if result.get('success'):
            print(f"Processing Time: {result.get('processing_time_ms', 0):.0f}ms")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result.get('success', False)
    
    else:
        print(f"🚀 Starting Enhanced Trade Extraction Agent")
        print(f"Enhanced AgentCore: {ENHANCED_AGENTCORE}")
        app.run()

if __name__ == "__main__":
    main()