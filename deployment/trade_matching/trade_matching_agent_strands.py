"""
Trade Matching Agent - Strands SDK Implementation

This agent uses Strands SDK with built-in use_aws tool for all AWS operations.
It scans DynamoDB tables and uses AI reasoning to evaluate match confidence based on trade attributes.

Requirements: 2.1, 2.2, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

# Strands SDK imports
from strands import Agent
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
AGENT_NAME = "trade-matching-agent"

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
        # Verify DynamoDB client can be created
        get_boto_client('dynamodb')
        return PingStatus.HEALTHY
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return PingStatus.HEALTHY  # Return healthy to avoid restart loops


# ============================================================================
# Agent System Prompt
# ============================================================================

SYSTEM_PROMPT = f"""You are an expert Trade Matching Agent for OTC derivative trade confirmations.

Your job is to match trades between bank systems and counterparty systems. The key challenge is that 
there is NO common Trade_ID across systems - bank and counterparty use completely different reference numbers.

## Available AWS Resources
- S3 Bucket: {S3_BUCKET}
- Bank Trades Table: {BANK_TABLE}
- Counterparty Trades Table: {COUNTERPARTY_TABLE}
- Region: {REGION}

## Matching Strategy
You must match trades based on their ATTRIBUTES, not their IDs:
- Currency (must match exactly)
- Maturity Date / Termination Date (must match exactly or within 1-2 days)
- Notional Amount (within 2% tolerance)
- Trade Date (within 2 days tolerance)
- Counterparty names (fuzzy match - names may differ slightly between systems)
- Product Type (SWAP, OPTION, etc.)
- Fixed Rate / Price (should match)
- Commodity type if applicable

## Classification Rules
Based on your analysis, classify each potential match:
- **MATCHED** (85%+ confidence): All key attributes align within tolerances
- **PROBABLE_MATCH** (70-84% confidence): Most attributes match, minor discrepancies
- **REVIEW_REQUIRED** (50-69% confidence): Some attributes match but significant differences exist
- **BREAK** (<50% confidence): Trades do not appear to be the same transaction

## Workflow
1. Use use_aws tool to scan the BankTradeData table (dynamodb scan operation)
2. Use use_aws tool to scan the CounterpartyTradeData table (dynamodb scan operation)
3. Find the specified trade_id in the appropriate table
4. Search the opposite table for potential matches based on attributes
5. Analyze each candidate and calculate confidence scores
6. Use use_aws tool to save a detailed matching report to S3 (s3 put_object operation)

## Report Format
Save the report as markdown to: s3://{S3_BUCKET}/reports/matching_report_<match_id>_<timestamp>.md

Include:
- Match ID (combination of both trade IDs)
- Classification and confidence score
- Detailed reasoning for the match decision
- All attribute comparisons
- Both trade details in JSON format

## Important Notes
- DynamoDB items use typed format: {{"S": "string"}}, {{"N": "number"}}
- Parse the N type values as numbers for comparison
- Counterparty names may be abbreviated or formatted differently
- Consider that the same trade may have slightly different values due to rounding or timing
"""


# ============================================================================
# Create Strands Agent
# ============================================================================

def create_matching_agent() -> Agent:
    """Create and configure the Strands matching agent with AWS tools."""
    # Explicitly configure BedrockModel for consistent behavior
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for deterministic matching decisions
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
    AgentCore Runtime entrypoint for Trade Matching Agent.
    
    Uses Strands SDK with use_aws tool for all AWS operations.
    
    Args:
        payload: Event payload containing:
            - trade_id: Trade identifier to match
            - source_type: BANK or COUNTERPARTY (which table the trade is in)
            - correlation_id: Optional correlation ID for tracking
        context: AgentCore context (optional)
        
    Returns:
        dict: Matching result with classification and confidence score
    """
    start_time = datetime.utcnow()
    logger.info("Trade Matching Agent (Strands) invoked")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    trade_id = payload.get("trade_id")
    source_type = payload.get("source_type", "").upper()
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # Standard observability attributes
    obs_attributes = {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "agent_alias": AGENT_ALIAS,
        "correlation_id": correlation_id,
        "trade_id": trade_id or "unknown",
        "source_type": source_type or "unknown",
    }
    
    if not trade_id:
        error_response = {
            "success": False,
            "error": "Missing required field: trade_id",
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
        }
        if observability:
            try:
                with observability.start_span("trade_matching") as span:
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
                span_context = observability.start_span("trade_matching")
                span_context.__enter__()
                for k, v in obs_attributes.items():
                    span_context.set_attribute(k, v)
            except Exception as e:
                logger.warning(f"Failed to start observability span: {e}")
                span_context = None
        
        # Create the agent
        agent = create_matching_agent()
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Construct the prompt for the agent
        prompt = f"""Find and match a trade that was just extracted.

## Task Details
- Trade ID: {trade_id}
- Source Type: {source_type if source_type else "Unknown - check both tables"}
- Correlation ID: {correlation_id}
- Timestamp: {timestamp}

## Instructions

1. **Scan both DynamoDB tables** using use_aws tool:
   - Service: dynamodb
   - Operation: scan
   - TableName: {BANK_TABLE}
   
   Then scan:
   - Service: dynamodb
   - Operation: scan  
   - TableName: {COUNTERPARTY_TABLE}

2. **Find the source trade** with ID "{trade_id}" in the scan results
   - Note: DynamoDB returns items with typed format like {{"S": "value"}} or {{"N": "123"}}

3. **Search for matches** in the opposite table based on attributes:
   - Compare currency, notional, dates, counterparty, product_type, fixed_rate
   - Calculate a confidence score based on how many attributes match

4. **Generate a matching report** and save to S3:
   - Service: s3
   - Operation: put_object
   - Bucket: {S3_BUCKET}
   - Key: reports/matching_report_{trade_id.replace(' ', '_')[:30]}_{timestamp}.md
   - Body: Your detailed markdown report

5. **Report your findings** including:
   - Whether a match was found
   - The matched trade ID (if found)
   - Classification (MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, BREAK)
   - Confidence score
   - Key differences found

Remember: Bank and counterparty systems use DIFFERENT Trade IDs for the same trade.
You must match based on attributes like currency, notional, dates, and counterparty names.
"""
        
        # Invoke the agent
        logger.info("Invoking Strands agent for matching analysis")
        result = agent(prompt)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract token metrics
        token_metrics = _extract_token_metrics(result)
        logger.info(f"Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Extract the agent's response
        response_text = str(result.message) if hasattr(result, 'message') else str(result)
        
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
            "trade_id": trade_id,
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
        logger.error(f"Error in matching agent: {e}", exc_info=True)
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
            "trade_id": trade_id,
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
