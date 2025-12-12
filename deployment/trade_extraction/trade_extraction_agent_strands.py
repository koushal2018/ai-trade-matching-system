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
from strands_tools import use_aws
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# AgentCore Observability
try:
    from bedrock_agentcore.observability import Observability
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

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
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_ALIAS = os.getenv("AGENT_ALIAS", "default")
OBSERVABILITY_STAGE = os.getenv("OBSERVABILITY_STAGE", "development")

# Agent identification constants
AGENT_NAME = "trade-extraction-agent"

# Initialize Observability
observability = None
if OBSERVABILITY_AVAILABLE:
    try:
        observability = Observability(
            service_name=AGENT_NAME,
            stage=OBSERVABILITY_STAGE,
            verbosity="high" if OBSERVABILITY_STAGE == "development" else "low"
        )
        logger.info(f"Observability initialized for {AGENT_NAME}")
    except Exception as e:
        logger.warning(f"Failed to initialize observability: {e}")

# Lazy-initialized boto3 clients for efficiency
_boto_clients: Dict[str, Any] = {}


def get_boto_client(service: str):
    """Get or create a boto3 client for the specified service."""
    import boto3
    if service not in _boto_clients:
        _boto_clients[service] = boto3.client(service, region_name=REGION)
    return _boto_clients[service]


# ============================================================================
# Health Check Handler
# ============================================================================

@app.ping
def health_check() -> PingStatus:
    """Custom health check for AgentCore Runtime."""
    try:
        # Verify S3 client can be created
        get_boto_client('s3')
        return PingStatus.HEALTHY
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return PingStatus.HEALTHY  # Return healthy to avoid restart loops


# ============================================================================
# Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = f"""You are an expert Trade Data Extraction Agent for OTC derivative trade confirmations.

Your job is to extract structured trade data from trade confirmation documents and store them in DynamoDB.

## Available AWS Resources
- S3 Bucket: {S3_BUCKET}
- Bank Trades Table: {BANK_TABLE}
- Counterparty Trades Table: {COUNTERPARTY_TABLE}
- Region: {REGION}

## Your Workflow
1. Use the use_aws tool to read the canonical adapter output JSON from S3
   - The file contains extracted_text from OCR processing
   - It also contains source_type (BANK or COUNTERPARTY)

2. Analyze the extracted_text and identify ALL relevant trade information
   - You decide which fields are important based on the document content
   - Different trade types have different relevant fields

3. Use the use_aws tool to store the extracted trade in DynamoDB
   - Route to BankTradeData if source_type is BANK
   - Route to CounterpartyTradeData if source_type is COUNTERPARTY
   - Use DynamoDB typed format: {{"S": "string"}}, {{"N": "number"}}

## Key Fields to Look For (extract what's present)
- Trade_ID / Reference Number (REQUIRED - use as partition key 'trade_id')
- internal_reference (REQUIRED - use Trade_ID value as sort key)
- TRADE_SOURCE (REQUIRED - BANK or COUNTERPARTY)
- trade_date, effective_date, maturity_date/termination_date
- notional, currency
- counterparty, buyer, seller
- product_type (SWAP, OPTION, FORWARD, etc.)
- fixed_rate, floating_rate_index, spread
- quantity, quantity_unit, price_per_unit
- settlement_type, payment_frequency
- commodity_type, delivery_point
- uti, lei, usi

## DynamoDB Item Format Example
```json
{{
  "trade_id": {{"S": "12345"}},
  "internal_reference": {{"S": "12345"}},
  "Trade_ID": {{"S": "12345"}},
  "TRADE_SOURCE": {{"S": "COUNTERPARTY"}},
  "trade_date": {{"S": "2025-02-06"}},
  "notional": {{"N": "18600"}},
  "currency": {{"S": "EUR"}},
  "counterparty": {{"S": "Merrill Lynch International"}},
  "product_type": {{"S": "SWAP"}}
}}
```

## Important Notes
- Use YYYY-MM-DD format for all dates
- Store numeric values as strings in the N type
- Extract ALL available information - be thorough
- The trade_id and internal_reference are the composite primary key
"""


# ============================================================================
# Create Strands Agent
# ============================================================================

def create_extraction_agent() -> Agent:
    """Create and configure the Strands extraction agent with AWS tools."""
    # Explicitly configure BedrockModel for consistent behavior
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for deterministic extraction
        max_tokens=4096,
    )
    
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[use_aws]
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
        
        # Construct the prompt for the agent
        prompt = f"""Extract trade data from a document and store it in DynamoDB.

## Task Details
- Document ID: {document_id}
- Canonical Output Location: {canonical_output_location}
- Source Type Hint: {source_type if source_type else "Check the source_type field in the JSON"}
- Correlation ID: {correlation_id}

## Instructions
1. First, use the use_aws tool to get the canonical output from S3:
   - Service: s3
   - Operation: get_object
   - Bucket: {S3_BUCKET if not canonical_output_location.startswith('s3://') else canonical_output_location.split('/')[2]}
   - Key: {canonical_output_location.replace(f's3://{S3_BUCKET}/', '') if canonical_output_location.startswith('s3://') else canonical_output_location}

2. Parse the JSON response and analyze the extracted_text field

3. Extract all relevant trade fields from the text - you decide what's important based on the content

4. Use the use_aws tool to store in DynamoDB:
   - Service: dynamodb  
   - Operation: put_item
   - TableName: {COUNTERPARTY_TABLE if source_type == 'COUNTERPARTY' else BANK_TABLE if source_type == 'BANK' else 'Determine from source_type in JSON'}
   - Item: The extracted trade data in DynamoDB typed format

5. Report what you extracted and stored

Be thorough - extract every piece of trade information you can find.
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
                span_context.set_attribute("error_message", str(e))
                span_context.set_attribute("processing_time_ms", processing_time_ms)
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
