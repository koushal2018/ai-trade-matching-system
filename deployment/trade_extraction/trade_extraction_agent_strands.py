"""
Trade Data Extraction Agent - Strands SDK Implementation

This agent uses Strands SDK with built-in tools for AWS operations.
It reads canonical adapter output from S3, extracts structured trade data using LLM reasoning,
and stores in DynamoDB - letting the agent decide which fields are relevant.

Requirements: 2.1, 2.2, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
# MUST be set before importing strands_tools
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_agents_tools import use_aws
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# AgentCore Observability with PII redaction
try:
    from bedrock_agentcore.observability import Observability
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

# PII patterns to redact from observability logs
PII_PATTERNS = {
    "trade_id": r"(trade_id[\"']?\s*[:=]\s*[\"']?)([^\"',}\s]+)",
    "counterparty": r"(counterparty[\"']?\s*[:=]\s*[\"']?)([^\"',}\s]+)",
    "notional": r"(notional[\"']?\s*[:=]\s*[\"']?)(\d+\.?\d*)",
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
BANK_TABLE = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_ALIAS = os.getenv("AGENT_ALIAS", "default")
OBSERVABILITY_STAGE = os.getenv("OBSERVABILITY_STAGE", "development")

# Agent identification constants
AGENT_NAME = "trade-extraction-agent"

# Initialize Observability with data redaction
observability = None
if OBSERVABILITY_AVAILABLE:
    try:
        observability = Observability(
            service_name=AGENT_NAME,
            stage=OBSERVABILITY_STAGE,
            verbosity="high" if OBSERVABILITY_STAGE == "development" else "low",
            # Configure filters to redact sensitive financial data
            # Note: Actual filter configuration depends on AgentCore Observability API
        )
        logger.info(f"Observability initialized for {AGENT_NAME} with PII redaction")
    except Exception as e:
        logger.warning(f"Failed to initialize observability: {e}")

# Note: This agent uses Strands' use_aws tool for AWS operations.
# Additional helper tools are provided for common patterns, but the LLM decides which to use.

# IAM Role Requirements (for AgentCore Runtime deployment):
# - s3:GetObject on {S3_BUCKET}/extracted/*
# - dynamodb:PutItem on {BANK_TABLE} and {COUNTERPARTY_TABLE}
# - bedrock:InvokeModel on {BEDROCK_MODEL_ID}
# - logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents for CloudWatch


# ============================================================================
# Helper Tools (High-Level - Agent decides strategy)
# ============================================================================

@tool
def get_extraction_context() -> str:
    """
    Get context about the extraction environment and business rules.
    
    Use this to understand:
    - Available DynamoDB tables and their purposes
    - Required data format and validation rules
    - Business constraints and data integrity requirements
    
    Returns:
        JSON string with extraction context and guidelines
    """
    context = {
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
        "data_format": {
            "storage": "DynamoDB typed format",
            "examples": {
                "string": {"S": "value"},
                "number": {"N": "123.45"},
                "boolean": {"BOOL": True}
            }
        },
        "required_fields": [
            "trade_id (partition key)",
            "internal_reference (sort key)",
            "TRADE_SOURCE (must match table: BANK or COUNTERPARTY)"
        ],
        "validation_rules": {
            "trade_id": "Must be unique and non-empty",
            "TRADE_SOURCE": "Must be exactly 'BANK' or 'COUNTERPARTY'",
            "dates": "Recommended format: YYYY-MM-DD",
            "numbers": "Must use DynamoDB N type with string representation"
        },
        "common_fields": [
            "trade_date", "effective_date", "maturity_date",
            "notional", "currency", "counterparty",
            "product_type", "fixed_rate", "floating_rate_index",
            "spread", "quantity", "settlement_type",
            "payment_frequency", "commodity_type", "delivery_point",
            "uti", "lei", "usi"
        ]
    }
    
    return json.dumps(context, indent=2)


# ============================================================================
# Health Check Handler
# ============================================================================

@app.ping
def health_check() -> PingStatus:
    """Custom health check for AgentCore Runtime."""
    # Simple health check - agent uses use_aws tool which handles its own connectivity
    return PingStatus.HEALTHY


# ============================================================================
# Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = f"""You are an expert Trade Data Extraction Agent for OTC derivative trade confirmations.

## Your Mission
Transform canonical adapter output from S3 into structured trade records in DynamoDB. You have complete autonomy over your approach - analyze the situation, reason about the data, and determine the optimal extraction strategy.

## Available Resources
- **S3 Bucket**: {S3_BUCKET} (contains canonical adapter outputs)
- **DynamoDB Tables**: {BANK_TABLE} (bank trades), {COUNTERPARTY_TABLE} (counterparty trades)
- **AWS Region**: {REGION}

## Your Tools

### use_aws
Interact with AWS services (S3, DynamoDB, etc.). You decide which operations to perform and in what order.

**Parameters**:
- service_name: AWS service (e.g., "s3", "dynamodb")
- operation_name: Operation in snake_case (e.g., "get_object", "put_item")
- parameters: Operation-specific parameters
- region: AWS region (use "{REGION}")
- label: Description of what you're doing

### get_extraction_context
Get information about the extraction environment, data format requirements, and business rules. Use this when you need to understand constraints or validation requirements.

## Decision-Making Framework

You are an intelligent agent. For each extraction task:

1. **Analyze**: What information is available? What's the source type? What fields are present?
2. **Reason**: Which fields are relevant for matching? How should values be normalized? What's the appropriate table?
3. **Validate**: Does the data meet business requirements? Are required fields present? Is the format correct?
4. **Execute**: Perform the necessary AWS operations to achieve your goal
5. **Verify**: Did the operation succeed? Should you take additional actions?

## Key Constraints

- BANK trades must go to {BANK_TABLE}
- COUNTERPARTY trades must go to {COUNTERPARTY_TABLE}
- Primary key structure: trade_id (partition key), internal_reference (sort key)
- TRADE_SOURCE field must match the table (data integrity requirement)
- DynamoDB requires typed format: {{"S": "string"}}, {{"N": "number"}}, {{"BOOL": true}}

## Your Autonomy

You decide:
- How to extract and structure the data
- Which fields to include based on relevance
- How to handle missing or ambiguous information
- Whether to normalize values (e.g., date formats, currency codes)
- What validation checks to perform
- The order of operations

Think critically. Reason about edge cases. Optimize for downstream matching accuracy.
"""


# ============================================================================
# Create Strands Agent
# ============================================================================

def create_extraction_agent() -> Agent:
    """Create and configure the Strands extraction agent with AWS tools and helpers."""
    # Explicitly configure BedrockModel for consistent behavior
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.3,  # Enable reasoning while maintaining consistency for financial data
        max_tokens=4096,
    )
    
    # Provide high-level tools - agent decides strategy and approach
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[use_aws, get_extraction_context]
    )


# ============================================================================
# AgentCore Entrypoint
# ============================================================================

def _extract_token_metrics(result) -> Dict[str, int]:
    """Extract token usage metrics from Strands agent result."""
    metrics = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    try:
        if hasattr(result, 'metrics'):
            metrics["input_tokens"] = getattr(result.metrics, 'input_tokens', 0) or 0
            metrics["output_tokens"] = getattr(result.metrics, 'output_tokens', 0) or 0
        elif hasattr(result, 'usage'):
            metrics["input_tokens"] = getattr(result.usage, 'input_tokens', 0) or 0
            metrics["output_tokens"] = getattr(result.usage, 'output_tokens', 0) or 0
        metrics["total_tokens"] = metrics["input_tokens"] + metrics["output_tokens"]
    except Exception:
        pass
    return metrics


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Trade Data Extraction Agent.
    
    Uses Strands SDK with use_aws tool for all AWS operations.
    
    Args:
        payload: Event payload containing:
            - document_id: Unique identifier for the document
            - canonical_output_location: S3 path to canonical adapter output
            - source_type: Optional - BANK or COUNTERPARTY
        context: AgentCore context (optional)
        
    Returns:
        dict: Extraction result with trade_id and table_name
    """
    start_time = datetime.utcnow()
    logger.info("Trade Data Extraction Agent (Strands) invoked")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    document_id = payload.get("document_id")
    canonical_output_location = payload.get("canonical_output_location")
    source_type = payload.get("source_type", "")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # Standard observability attributes
    obs_attributes = {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "agent_alias": AGENT_ALIAS,
        "correlation_id": correlation_id,
        "document_id": document_id or "unknown",
        "source_type": source_type or "unknown",
        "model_id": BEDROCK_MODEL_ID,  # Track which model is being used
        "operation": "trade_extraction",  # Standardized operation name
    }
    
    if not document_id or not canonical_output_location:
        error_response = {
            "success": False,
            "error": "Missing required fields: document_id or canonical_output_location",
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
        }
        if observability:
            try:
                with observability.start_span("extract_trade_data") as span:
                    for k, v in obs_attributes.items():
                        span.set_attribute(k, v)
                    span.set_attribute("success", False)
                    span.set_attribute("error_type", "validation_error")
            except Exception as e:
                logger.warning(f"Observability span error: {e}")
        return error_response
    
    try:
        # Start observability span for the main operation
        span_context = None
        if observability:
            try:
                span_context = observability.start_span("extract_trade_data")
                span_context.__enter__()
                for k, v in obs_attributes.items():
                    span_context.set_attribute(k, v)
            except Exception as e:
                logger.warning(f"Failed to start observability span: {e}")
                span_context = None
        
        # Create the agent
        agent = create_extraction_agent()
        
        # Construct the prompt for the agent - purely goal-oriented
        prompt = f"""**Goal**: Extract and store trade data from canonical adapter output.

**Context**:
- Document: {document_id}
- Canonical Output: {canonical_output_location}
- Source Type: {source_type if source_type else "Unknown - determine from data"}
- Correlation: {correlation_id}

**Success Criteria**:
- Trade data extracted with all relevant fields
- Data stored in the correct DynamoDB table
- Data integrity maintained

Analyze the canonical output, reason about the data structure, and determine the best approach to achieve this goal.
"""
        
        # Invoke the agent
        logger.info("Invoking Strands agent for trade extraction")
        result = agent(prompt)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract token metrics
        token_metrics = _extract_token_metrics(result)
        logger.info(f"Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Extract the agent's response safely (consistent with other agents)
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
        
        # Record success metrics in observability span
        if span_context:
            try:
                span_context.set_attribute("success", True)
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                span_context.set_attribute("input_tokens", token_metrics["input_tokens"])
                span_context.set_attribute("output_tokens", token_metrics["output_tokens"])
                span_context.set_attribute("total_tokens", token_metrics["total_tokens"])
                # Add cost estimation (approximate - adjust based on actual pricing)
                # Nova Pro pricing: ~$0.0008/1K input tokens, ~$0.0032/1K output tokens
                estimated_cost = (token_metrics["input_tokens"] * 0.0008 / 1000) + \
                                (token_metrics["output_tokens"] * 0.0032 / 1000)
                span_context.set_attribute("estimated_cost_usd", round(estimated_cost, 6))
            except Exception as e:
                logger.warning(f"Failed to set span attributes: {e}")
        
        return {
            "success": True,
            "document_id": document_id,
            "source_type": source_type,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "agent_alias": AGENT_ALIAS,
            "token_usage": token_metrics,
        }
        
    except Exception as e:
        logger.error(f"Error in extraction agent: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record error in observability span
        if span_context:
            try:
                span_context.set_attribute("success", False)
                span_context.set_attribute("error_type", type(e).__name__)
                span_context.set_attribute("error_message", str(e)[:500])  # Truncate long errors
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                # Track error category for better analysis
                if "DynamoDB" in str(e) or "dynamodb" in str(e):
                    span_context.set_attribute("error_category", "database")
                elif "S3" in str(e) or "s3" in str(e):
                    span_context.set_attribute("error_category", "storage")
                elif "Bedrock" in str(e) or "bedrock" in str(e):
                    span_context.set_attribute("error_category", "model")
                else:
                    span_context.set_attribute("error_category", "unknown")
            except Exception:
                pass
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "document_id": document_id,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "processing_time_ms": processing_time_ms,
        }
    finally:
        # Close observability span
        if span_context:
            try:
                span_context.__exit__(None, None, None)
            except Exception:
                pass


if __name__ == "__main__":
    """Let AgentCore Runtime control the agent execution."""
    app.run()
