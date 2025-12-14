"""
Trade Matching Agent - Strands SDK Implementation

This agent uses Strands SDK with built-in use_aws tool for all AWS operations.
It scans DynamoDB tables and uses AI reasoning to evaluate match confidence based on trade attributes.

Requirements: 2.1, 2.2, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
# MUST be set before importing strands_tools
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, List
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel

# Try to import use_aws from different locations in strands-agents
try:
    from strands_tools import use_aws
    print("✓ Imported use_aws from strands_tools (community tools package)")
except ImportError:
    try:
        from strands import use_aws
        print("✓ Imported use_aws from strands")
    except ImportError:
        try:
            from strands.tools import use_aws
            print("✓ Imported use_aws from strands.tools")
        except ImportError:
            try:
                from strands_agents_tools import use_aws
                print("✓ Imported use_aws from strands_agents_tools")
            except ImportError:
                # If none work, we'll define our own
                print("⚠ use_aws not found, will define custom implementation")
                use_aws = None

# Fallback implementation if use_aws is not available
if use_aws is None:
    @tool
    def use_aws(service_name: str, operation_name: str, parameters: dict, region: str = "us-east-1", label: str = "") -> str:
        """
        Fallback AWS tool implementation using boto3 directly.
        
        Args:
            service_name: AWS service (e.g., "s3", "dynamodb")
            operation_name: Operation in snake_case (e.g., "get_object", "scan")
            parameters: Operation-specific parameters
            region: AWS region
            label: Description of what you're doing
            
        Returns:
            JSON string with operation result
        """
        try:
            import boto3
            logger.info(f"AWS Operation: {service_name}.{operation_name} - {label}")
            logger.debug(f"Parameters: {parameters}")
            
            client = boto3.client(service_name, region_name=region)
            
            # boto3 uses snake_case for method names
            operation_method = operation_name
            
            if hasattr(client, operation_method):
                result = getattr(client, operation_method)(**parameters)
                
                # Handle streaming responses for S3 GetObject
                if service_name == "s3" and operation_name == "get_object" and "Body" in result:
                    body_content = result["Body"].read()
                    if isinstance(body_content, bytes):
                        try:
                            body_content = body_content.decode('utf-8')
                        except UnicodeDecodeError:
                            body_content = body_content.decode('utf-8', errors='ignore')
                    result["Body"] = body_content
                    logger.info(f"S3 GetObject successful - retrieved {len(body_content)} characters")
                    logger.debug(f"Content preview: {body_content[:200]}...")
                
                response_data = {
                    "success": True, 
                    "result": result, 
                    "service": service_name, 
                    "operation": operation_name,
                    "fallback_used": True
                }
                response_json = json.dumps(response_data, default=str)
                logger.info(f"Operation successful - response length: {len(response_json)}")
                return response_json
            else:
                return json.dumps({
                    "success": False, 
                    "error": f"Operation {operation_method} not found on {service_name} client", 
                    "service": service_name, 
                    "operation": operation_name
                })
                
        except Exception as e:
            logger.error(f"AWS operation failed: {service_name}.{operation_name} - {e}")
            return json.dumps({
                "success": False, 
                "error": str(e), 
                "error_type": type(e).__name__,
                "service": service_name,
                "operation": operation_name,
                "fallback_used": True
            })


from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# AgentCore Observability
try:
    from bedrock_agentcore.observability import Observability
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

# AgentCore Memory
try:
    from bedrock_agentcore.memory.session import MemorySessionManager
    from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("AgentCore Memory not available - memory features disabled")

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
AGENT_NAME = "trade-matching-agent"

# AgentCore Memory Configuration
# Semantic memory with LTM for continuous learning
MEMORY_ID = os.getenv(
    "AGENTCORE_MEMORY_ID",
    "trade_matching_decisions-Z3tG4b4Xsd"  # Semantic memory resource
)
MEMORY_STORE_DECISIONS = os.getenv("MEMORY_STORE_DECISIONS", "true").lower() == "true"
MEMORY_RETRIEVE_CONTEXT = os.getenv("MEMORY_RETRIEVE_CONTEXT", "false").lower() == "true"

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

# Initialize AgentCore Memory
memory_session = None
if MEMORY_AVAILABLE and MEMORY_ID:
    try:
        memory_session = MemorySessionManager(
            memory_id=MEMORY_ID,
            region_name=REGION
        )
        logger.info(f"AgentCore Memory initialized: {MEMORY_ID}")
        logger.info(f"Memory features - Store: {MEMORY_STORE_DECISIONS}, Retrieve: {MEMORY_RETRIEVE_CONTEXT}")
    except Exception as e:
        logger.warning(f"Failed to initialize AgentCore Memory: {e}")
        logger.warning("Verify IAM permissions: bedrock-agentcore:GetMemory, CreateMemorySession, AddMemoryTurns, SearchMemory")
        memory_session = None

# Lazy-initialized boto3 clients for efficiency
_boto_clients: Dict[str, Any] = {}


def get_boto_client(service: str):
    """Get or create a boto3 client for the specified service."""
    import boto3
    if service not in _boto_clients:
        _boto_clients[service] = boto3.client(service, region_name=REGION)
    return _boto_clients[service]


# ============================================================================
# AgentCore Memory Helper Functions
# ============================================================================

def store_matching_decision(
    trade_id: str,
    source_type: str,
    classification: str,
    confidence: float,
    match_details: Dict[str, Any],
    correlation_id: str
) -> bool:
    """
    Store matching decision in AgentCore Memory for future learning.
    
    This enables the agent to:
    - Learn from past matching decisions
    - Retrieve similar cases for context
    - Improve matching accuracy over time
    - Support HITL feedback integration
    
    Args:
        trade_id: Trade identifier
        source_type: BANK or COUNTERPARTY
        classification: MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, or BREAK
        confidence: Confidence score (0.0 to 1.0)
        match_details: Detailed matching information
        correlation_id: Correlation ID for tracing
        
    Returns:
        bool: True if stored successfully
    """
    if not memory_session or not MEMORY_STORE_DECISIONS:
        logger.debug("Memory storage disabled - skipping decision storage")
        return False
    
    try:
        # Create a memory session for this matching decision
        session = memory_session.create_memory_session(
            actor_id=AGENT_NAME,
            session_id=f"match_{trade_id}_{correlation_id}"
        )
        
        # Store the matching decision as a conversational turn
        decision_summary = f"""Matching Decision for Trade {trade_id}:
- Classification: {classification}
- Confidence: {confidence:.2%}
- Source Type: {source_type}
- Key Attributes: {json.dumps(match_details.get('key_attributes', {}), indent=2)}
- Reasoning: {match_details.get('reasoning', 'N/A')}
"""
        
        session.add_turns(
            messages=[
                ConversationalMessage(
                    decision_summary,
                    MessageRole.ASSISTANT
                )
            ]
        )
        
        logger.info(f"Stored matching decision for {trade_id} in AgentCore Memory")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store matching decision in memory: {e}")
        return False


def retrieve_similar_matches(
    trade_attributes: Dict[str, Any],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Query AgentCore Memory for similar past matching decisions.
    
    This helps the agent:
    - Learn from historical patterns
    - Apply consistent matching logic
    - Identify edge cases based on past experience
    - Leverage HITL feedback from similar trades
    
    Args:
        trade_attributes: Trade attributes to search for (currency, product_type, etc.)
        top_k: Number of similar matches to retrieve
        
    Returns:
        List of similar matching decisions with context
    """
    if not memory_session or not MEMORY_RETRIEVE_CONTEXT:
        logger.debug("Memory retrieval disabled - skipping similarity search")
        return []
    
    try:
        # Create a search query based on trade attributes
        query_parts = []
        if trade_attributes.get('currency'):
            query_parts.append(f"currency {trade_attributes['currency']}")
        if trade_attributes.get('product_type'):
            query_parts.append(f"product {trade_attributes['product_type']}")
        if trade_attributes.get('counterparty'):
            query_parts.append(f"counterparty {trade_attributes['counterparty']}")
        
        query = f"Similar trades: {' '.join(query_parts)}"
        
        # Search semantic memory for similar cases
        session = memory_session.create_memory_session(
            actor_id=AGENT_NAME,
            session_id=f"search_{uuid.uuid4().hex[:12]}"
        )
        
        memory_records = session.search_long_term_memories(
            query=query,
            namespace_prefix="/",
            top_k=top_k
        )
        
        logger.info(f"Retrieved {len(memory_records)} similar matches from memory")
        return memory_records
        
    except Exception as e:
        logger.error(f"Failed to retrieve similar matches from memory: {e}")
        return []


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
# Agent System Prompt (Goal-Oriented, Model-Driven, Memory-Enhanced)
# ============================================================================

SYSTEM_PROMPT = f"""You are an expert Trade Matching Agent for OTC derivative trade confirmations with memory-enhanced learning capabilities.

## Your Mission
Match trades between bank and counterparty systems by analyzing their attributes. The critical challenge: 
bank and counterparty systems use COMPLETELY DIFFERENT Trade_IDs for the same trade - you must match 
by comparing trade characteristics, not IDs.

## Available Resources
- **S3 Bucket**: {S3_BUCKET}
- **Bank Trades Table**: {BANK_TABLE}
- **Counterparty Trades Table**: {COUNTERPARTY_TABLE}
- **Region**: {REGION}
- **Tool**: use_aws (for DynamoDB scans and S3 operations)
- **Memory**: AgentCore Memory for learning from past decisions (when available)

## Your Expertise: Attribute-Based Matching
You understand that matching requires comparing:
- **Currency** (exact match required)
- **Notional Amount** (±2% tolerance for rounding differences)
- **Dates** (trade date, effective date, maturity date - ±2 days tolerance)
- **Counterparty Names** (fuzzy matching - "Goldman Sachs" vs "GS" vs "Goldman Sachs International")
- **Product Type** (SWAP, OPTION, FORWARD, etc.)
- **Rates/Prices** (fixed rate, floating rate index, strike price)
- **Commodity Details** (if applicable - type, delivery point, quantity)

## Classification Framework
Based on your analysis, classify matches using these confidence thresholds:
- **MATCHED** (≥85%): High confidence - all critical attributes align within tolerances
- **PROBABLE_MATCH** (70-84%): Good confidence - most attributes match with minor discrepancies
- **REVIEW_REQUIRED** (50-69%): Uncertain - some matches but significant differences need human review
- **BREAK** (<50%): Low confidence - trades appear to be different transactions

## Your Approach (You Decide)
Think through the problem and determine your strategy. Generally, you'll want to:
1. Retrieve trades from both DynamoDB tables
2. Locate the source trade you're matching
3. Search for potential matches in the opposite table
4. Analyze candidates and calculate confidence scores
5. Generate a comprehensive matching report and save to S3

But you have full autonomy to adapt based on the situation.

## Memory-Enhanced Learning
When AgentCore Memory is available, your decisions are stored for continuous improvement:
- Past matching decisions inform future analysis
- Similar trade patterns provide context
- HITL feedback refines your matching logic
- Edge cases build institutional knowledge

## Performance Expectations
- **Target Processing Time**: Complete matching analysis within 20 seconds
- **Token Efficiency**: Minimize token usage while maintaining accuracy
- **Observability**: All operations are traced with correlation_id for debugging

## Technical Context
- **DynamoDB Format**: Items use typed format like {{"S": "value"}}, {{"N": "123.45"}}
- **Numeric Comparisons**: Parse "N" type values as numbers for tolerance calculations
- **Name Variations**: Counterparty names often differ (abbreviations, legal entity variations)
- **Rounding Differences**: Same trade may have slightly different values across systems
- **Report Location**: Save markdown reports to s3://{S3_BUCKET}/reports/matching_report_<id>_<timestamp>.md

## Success Criteria
- Accurately identify matching trades despite different IDs
- Calculate meaningful confidence scores with clear reasoning
- Generate detailed reports that explain your matching decisions
- Handle edge cases intelligently (missing fields, format differences, etc.)

## Error Handling
If you encounter issues:
- **Missing Data**: Document which fields are missing and impact on confidence
- **Format Issues**: Attempt to parse alternative formats before failing
- **No Matches Found**: Clearly state this in your report with reasoning
- **Multiple Candidates**: Rank by confidence and explain differences

You are the expert - analyze the trades and make informed matching decisions.
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
        
        # Create the agent (with sub-span for agent initialization)
        if observability and span_context:
            with observability.start_span("agent_initialization") as init_span:
                init_span.set_attribute("model_id", BEDROCK_MODEL_ID)
                init_span.set_attribute("temperature", 0.1)
                agent = create_matching_agent()
        else:
            agent = create_matching_agent()
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Construct goal-oriented prompt for the agent
        prompt = f"""Match a trade that was just extracted and stored.

## Trade to Match
- **Trade ID**: {trade_id}
- **Source Type**: {source_type if source_type else "Unknown - determine from data"}
- **Correlation ID**: {correlation_id}
- **Timestamp**: {timestamp}

## Your Goal
Find this trade in one table and identify its matching counterpart in the other table. Remember: 
the same trade will have DIFFERENT IDs in bank vs counterparty systems - match by attributes.

## Available Resources
- **DynamoDB Tables**: {BANK_TABLE} (bank trades), {COUNTERPARTY_TABLE} (counterparty trades)
- **S3 Bucket**: {S3_BUCKET} (for saving your matching report)
- **Tool**: use_aws (for scanning DynamoDB and saving to S3)

## What You Need to Deliver
1. **Match Analysis**: Identify potential matches and calculate confidence scores
2. **Classification**: Categorize as MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, or BREAK
3. **Detailed Report**: Save a markdown report to S3 at:
   - Key: `reports/matching_report_{trade_id.replace(' ', '_')[:30]}_{timestamp}.md`
   - Include: both trade details, attribute comparisons, confidence reasoning, classification

## Think Through Your Approach
- How will you retrieve trades from both tables?
- How will you identify the source trade with ID "{trade_id}"?
- What attributes will you compare for matching?
- How will you calculate confidence scores?
- What format will make your report most useful?

You decide the best strategy. Use the use_aws tool for DynamoDB scans and S3 operations.
"""
        
        # Invoke the agent with observability span
        logger.info("Invoking Strands agent for matching analysis")
        if observability and span_context:
            with observability.start_span("agent_invocation") as invoke_span:
                invoke_span.set_attribute("prompt_length", len(prompt))
                invoke_span.set_attribute("model_id", BEDROCK_MODEL_ID)
                result = agent(prompt)
                
                # Extract and record token metrics immediately
                token_metrics = _extract_token_metrics(result)
                invoke_span.set_attribute("input_tokens", token_metrics["input_tokens"])
                invoke_span.set_attribute("output_tokens", token_metrics["output_tokens"])
                invoke_span.set_attribute("total_tokens", token_metrics["total_tokens"])
        else:
            result = agent(prompt)
            token_metrics = _extract_token_metrics(result)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Extract the agent's response
        response_text = str(result.message) if hasattr(result, 'message') else str(result)
        
        # Attempt to extract classification from response for metrics
        classification = "UNKNOWN"
        confidence_score = 0.0
        try:
            if "MATCHED" in response_text.upper():
                if "PROBABLE_MATCH" in response_text.upper():
                    classification = "PROBABLE_MATCH"
                elif "REVIEW_REQUIRED" in response_text.upper():
                    classification = "REVIEW_REQUIRED"
                else:
                    classification = "MATCHED"
            elif "BREAK" in response_text.upper():
                classification = "BREAK"
            
            # Try to extract confidence score (look for percentage or decimal)
            import re
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*%', response_text)
            if score_match:
                confidence_score = float(score_match.group(1))
            else:
                score_match = re.search(r'confidence[:\s]+(\d+(?:\.\d+)?)', response_text, re.IGNORECASE)
                if score_match:
                    confidence_score = float(score_match.group(1))
        except Exception:
            pass  # Keep defaults if parsing fails
        
        # Record success metrics in observability span
        if span_context:
            try:
                span_context.set_attribute("success", True)
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                span_context.set_attribute("input_tokens", token_metrics["input_tokens"])
                span_context.set_attribute("output_tokens", token_metrics["output_tokens"])
                span_context.set_attribute("total_tokens", token_metrics["total_tokens"])
                span_context.set_attribute("match_classification", classification)
                span_context.set_attribute("confidence_score", confidence_score)
                span_context.set_attribute("response_length", len(response_text))
            except Exception as e:
                logger.warning(f"Failed to set span attributes: {e}")
        
        # Log performance summary
        logger.info(
            f"Trade matching completed - "
            f"trade_id={trade_id}, "
            f"classification={classification}, "
            f"confidence={confidence_score:.1f}%, "
            f"time={processing_time_ms:.0f}ms, "
            f"tokens={token_metrics['total_tokens']}"
        )
        
        # Store matching decision in AgentCore Memory for continuous learning
        if memory_session and MEMORY_STORE_DECISIONS and classification != "UNKNOWN":
            try:
                if observability and span_context:
                    with observability.start_span("memory_storage") as mem_span:
                        mem_span.set_attribute("classification", classification)
                        mem_span.set_attribute("confidence", confidence_score)
                        
                        success = store_matching_decision(
                            trade_id=trade_id,
                            source_type=source_type,
                            classification=classification,
                            confidence=confidence_score / 100.0,  # Convert to 0-1
                            match_details={
                                "key_attributes": {
                                    "trade_id": trade_id,
                                    "source_type": source_type,
                                },
                                "reasoning": response_text[:500],  # First 500 chars
                                "processing_time_ms": processing_time_ms,
                                "token_usage": token_metrics
                            },
                            correlation_id=correlation_id
                        )
                        mem_span.set_attribute("memory_stored", success)
                else:
                    store_matching_decision(
                        trade_id=trade_id,
                        source_type=source_type,
                        classification=classification,
                        confidence=confidence_score / 100.0,
                        match_details={
                            "key_attributes": {
                                "trade_id": trade_id,
                                "source_type": source_type,
                            },
                            "reasoning": response_text[:500],
                            "processing_time_ms": processing_time_ms,
                            "token_usage": token_metrics
                        },
                        correlation_id=correlation_id
                    )
            except Exception as e:
                logger.warning(f"Failed to store matching decision in memory: {e}")
        
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
            "match_classification": classification,
            "confidence_score": confidence_score,
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
