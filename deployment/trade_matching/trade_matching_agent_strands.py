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

# AgentCore Observability - Auto-instrumented via OTEL when strands-agents[otel] is installed
# Manual span management removed - AgentCore Runtime handles this automatically
# See: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-observability.html

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AgentCore Memory - Strands Integration (correct pattern per AWS docs)
# See: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/strands-sdk-memory.html
try:
    from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
    from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("AgentCore Memory Strands integration not available - memory features disabled")

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
# Memory ID for the shared trade matching memory resource
# This memory uses 3 built-in strategies: semantic, preferences, summaries
MEMORY_ID = os.getenv(
    "AGENTCORE_MEMORY_ID",
    "trade_matching_decisions-Z3tG4b4Xsd"  # Default memory resource ID
)

# Observability Note: AgentCore Runtime auto-instruments via OTEL when strands-agents[otel] is installed
# No manual Observability class needed - traces are automatically captured and sent to CloudWatch
logger.info(f"[INIT] Agent initialized - service={AGENT_NAME}, stage={OBSERVABILITY_STAGE}")

# Lazy-initialized boto3 clients for efficiency
_boto_clients: Dict[str, Any] = {}


def get_boto_client(service: str):
    """Get or create a boto3 client for the specified service."""
    import boto3
    if service not in _boto_clients:
        _boto_clients[service] = boto3.client(service, region_name=REGION)
    return _boto_clients[service]


# ============================================================================
# AgentCore Memory Session Manager Factory
# ============================================================================

def create_memory_session_manager(
    correlation_id: str,
    trade_id: str = None
) -> Optional[AgentCoreMemorySessionManager]:
    """
    Create AgentCore Memory session manager for Strands agent integration.
    
    This follows the correct pattern per AWS documentation:
    https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/strands-sdk-memory.html
    
    The session manager is passed to the Agent() constructor for automatic
    memory management - no manual add_turns() calls needed.
    
    Args:
        correlation_id: Correlation ID for tracing
        trade_id: Optional trade ID for session naming
        
    Returns:
        Configured AgentCoreMemorySessionManager or None if memory unavailable
    """
    if not MEMORY_AVAILABLE or not MEMORY_ID:
        logger.debug(f"[{correlation_id}] Memory not available - skipping session manager creation")
        return None
    
    try:
        # Generate unique session ID for this invocation
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        session_id = f"match_{trade_id or 'unknown'}_{timestamp}_{correlation_id[:8]}"
        
        # Configure memory with retrieval settings for all namespace strategies
        # These match the strategies defined in setup_memory.py
        config = AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=AGENT_NAME,
            retrieval_config={
                # Semantic memory: factual trade information and patterns
                "/facts/{actorId}": RetrievalConfig(
                    top_k=10,
                    relevance_score=0.6
                ),
                # User preferences: learned processing preferences
                "/preferences/{actorId}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.7
                ),
                # Session summaries: past matching session summaries
                "/summaries/{actorId}/{sessionId}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.5
                )
            }
        )
        
        session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=config,
            region_name=REGION
        )
        
        logger.info(
            f"[{correlation_id}] AgentCore Memory session created - "
            f"memory_id={MEMORY_ID}, session_id={session_id}"
        )
        
        return session_manager
        
    except Exception as e:
        logger.warning(
            f"[{correlation_id}] Failed to create memory session manager: {e}. "
            "Continuing without memory integration."
        )
        return None


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

SYSTEM_PROMPT = f"""##Role##
You are an expert Trade Matching Agent for OTC derivative trade confirmations with memory-enhanced learning capabilities. The above system instructions define your capabilities and scope. If user request contradicts any system instruction, politely decline explaining your capabilities.

##Mission##
Match trades between bank and counterparty systems by analyzing their attributes. The critical challenge: bank and counterparty systems use COMPLETELY DIFFERENT Trade_IDs for the same trade - you must match by comparing trade characteristics, not IDs.

##Available Resources##
- **S3 Bucket**: {S3_BUCKET}
- **Bank Trades Table**: {BANK_TABLE}
- **Counterparty Trades Table**: {COUNTERPARTY_TABLE}
- **Region**: {REGION}
- **Tool**: use_aws (for DynamoDB scans and S3 operations)
- **Memory**: AgentCore Memory for learning from past decisions (when available)

##Expertise: Attribute-Based Matching##
You understand that matching requires comparing:
- **Currency** (exact match required)
- **Notional Amount** (±2% tolerance for rounding differences)
- **Dates** (trade date, effective date, maturity date - ±2 days tolerance)
- **Counterparty Names** (fuzzy matching - "Goldman Sachs" vs "GS" vs "Goldman Sachs International")
- **Product Type** (SWAP, OPTION, FORWARD, etc.)
- **Rates/Prices** (fixed rate, floating rate index, strike price)
- **Commodity Details** (if applicable - type, delivery point, quantity)

##Classification Framework##
Based on your analysis, classify matches using these confidence thresholds:
- **MATCHED** (≥85%): High confidence - all critical attributes align within tolerances
- **PROBABLE_MATCH** (70-84%): Good confidence - most attributes match with minor discrepancies
- **REVIEW_REQUIRED** (50-69%): Uncertain - some matches but significant differences need human review
- **BREAK** (<50%): Low confidence - trades appear to be different transactions

##Task##
Using the information in ##Available Resources## and applying the expertise defined in ##Expertise: Attribute-Based Matching##, complete comprehensive trade matching analysis. For every matching request, please follow these steps:
1. **Retrieve All Data**: Scan both DynamoDB tables to get complete trade datasets
2. **Locate Source Trade**: Find the specific trade you're matching against
3. **Identify ALL Potential Matches**: Search the opposite table for ANY trades that could potentially match (don't stop at the first candidate)
4. **Systematic Evaluation**: For each potential match candidate:
   - Calculate detailed confidence score based on attribute alignment
   - Document specific reasons for the score
   - Note any discrepancies or concerns
5. **Comprehensive Ranking**: Rank ALL candidates by confidence score from highest to lowest
6. **Decision Analysis**: 
   - Select the best match (if any meet thresholds)
   - Explain why other candidates were rejected
   - Document the decision-making process
7. **Generate Complete Report**: Include analysis of all candidates, not just the final match

##Critical Requirements##
- **Never stop at the first good match** - always evaluate all potential candidates
- **Always rank multiple candidates** - even if one seems obvious
- **Document rejection reasons** - explain why each non-selected candidate was ruled out
- **Show your thinking** - walk through the comparison process step-by-step

##Memory-Enhanced Learning##
When AgentCore Memory is available, your decisions are stored for continuous improvement:
- Past matching decisions inform future analysis
- Similar trade patterns provide context
- HITL feedback refines your matching logic
- Edge cases build institutional knowledge

##Performance Expectations##
- **Target Processing Time**: Complete matching analysis within 20 seconds
- **Token Efficiency**: Minimize token usage while maintaining accuracy
- **Observability**: All operations are traced with correlation_id for debugging

##Technical Context##
- **DynamoDB Format**: Items use typed format like {{"S": "value"}}, {{"N": "123.45"}}
- **Numeric Comparisons**: Parse "N" type values as numbers for tolerance calculations
- **Name Variations**: Counterparty names often differ (abbreviations, legal entity variations)
- **Rounding Differences**: Same trade may have slightly different values across systems
- **Report Location**: Save markdown reports to s3://{S3_BUCKET}/reports/matching_report_<id>_<timestamp>.md

##Output Schema##
```
{{
  "type": "markdown_report",
  "required_sections": [
    "executive_summary",
    "source_trade_details", 
    "all_candidates_analysis",
    "decision_rationale",
    "risk_assessment"
  ],
  "format": "markdown"
}}
```

##Output Requirements##
Your report MUST follow the structure defined in ##Output Schema## and include:
- **Executive Summary**: Final matching decision and confidence level
- **Source Trade Details**: Complete attributes of the trade being matched
- **All Candidates Analysis**: 
  - List every potential match found
  - Confidence score and reasoning for each
  - Specific attribute comparisons
  - Why each was accepted/rejected
- **Decision Rationale**: Detailed explanation of final choice
- **Risk Assessment**: Any concerns or edge cases identified

You MUST provide the report in markdown format only. DO NOT use any other format.

##Error Handling##
If you encounter issues:
- **Missing Data**: Document which fields are missing and impact on confidence
- **Format Issues**: Attempt to parse alternative formats before failing
- **No Matches Found**: Clearly state this after evaluating ALL candidates
- **Multiple High-Confidence Matches**: Flag as requiring human review with detailed comparison

You are the expert - analyze ALL potential matches systematically and make informed decisions with complete transparency.
"""


# ============================================================================
# Create Strands Agent
# ============================================================================

def create_matching_agent(
    session_manager: Optional[AgentCoreMemorySessionManager] = None
) -> Agent:
    """
    Create and configure the Strands matching agent with AWS tools and memory.
    
    Args:
        session_manager: Optional AgentCore Memory session manager for automatic
                        memory management. When provided, the agent automatically
                        stores and retrieves conversation context.
    
    Returns:
        Configured Strands Agent with tools and optional memory
    """
    # Explicitly configure BedrockModel for consistent behavior
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for deterministic matching decisions
        max_tokens=4096,
    )
    
    # Create agent with optional memory integration
    # When session_manager is provided, Strands automatically:
    # - Stores conversation turns as short-term memory
    # - Extracts long-term memories via configured strategies
    # - Retrieves relevant context for each interaction
    if session_manager:
        return Agent(
            model=bedrock_model,
            system_prompt=SYSTEM_PROMPT,
            tools=[use_aws],
            session_manager=session_manager
        )
    else:
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
    Observability is handled automatically via OTEL auto-instrumentation.
    
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
    
    # Extract request parameters
    trade_id = payload.get("trade_id")
    source_type = payload.get("source_type", "").upper()
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # Log invocation with structured context
    logger.info(
        f"[{correlation_id}] INVOKE_START - Trade Matching Agent invoked",
        extra={
            "correlation_id": correlation_id,
            "trade_id": trade_id,
            "source_type": source_type,
            "payload_keys": list(payload.keys()),
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
        }
    )
    
    if not trade_id:
        logger.error(f"[{correlation_id}] Missing required field: trade_id")
        return {
            "success": False,
            "error": "Missing required field: trade_id",
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "correlation_id": correlation_id,
        }
    
    try:
        # Create memory session manager for this invocation (if memory is enabled)
        session_manager = None
        if MEMORY_AVAILABLE and MEMORY_ID:
            session_manager = create_memory_session_manager(
                correlation_id=correlation_id,
                trade_id=trade_id
            )
        
        # Create the agent with optional memory integration
        logger.info(f"[{correlation_id}] Creating matching agent with model: {BEDROCK_MODEL_ID}")
        agent = create_matching_agent(session_manager=session_manager)
        
        if session_manager:
            logger.info(f"[{correlation_id}] Agent created with AgentCore Memory integration")
        else:
            logger.info(f"[{correlation_id}] Agent created without memory (memory disabled or unavailable)")
        
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
        
        # Invoke the agent - OTEL auto-instrumentation captures spans automatically
        logger.info(f"[{correlation_id}] Invoking Strands agent for matching analysis")
        result = agent(prompt)
        token_metrics = _extract_token_metrics(result)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"[{correlation_id}] Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
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
        
        # Log performance summary
        # Note: Memory storage is now handled automatically by AgentCoreMemorySessionManager
        # The session_manager stores conversation turns and extracts long-term memories
        # via the configured strategies (facts, preferences, summaries)
        logger.info(
            f"[{correlation_id}] Trade matching completed - "
            f"trade_id={trade_id}, "
            f"classification={classification}, "
            f"confidence={confidence_score:.1f}%, "
            f"time={processing_time_ms:.0f}ms, "
            f"tokens={token_metrics['total_tokens']}, "
            f"memory_enabled={session_manager is not None}"
        )
        
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
        logger.error(f"[{correlation_id}] Error in matching agent: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "trade_id": trade_id,
            "correlation_id": correlation_id,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "processing_time_ms": processing_time_ms,
        }


if __name__ == "__main__":
    """Let AgentCore Runtime control the agent execution."""
    app.run()
