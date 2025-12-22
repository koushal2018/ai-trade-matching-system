"""
Trade Data Extraction Agent - LLM-Centric Strands SDK Implementation

This agent follows LLM-centric design principles:
1. LLM drives all decision-making
2. Tools handle external operations
3. Minimal hardcoded logic
4. Agent autonomously chooses tools based on context

Requirements: 2.1, 2.2, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
import re
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Tuple
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel

# Import use_aws from strands_tools
try:
    from strands_tools import use_aws
    print("✓ Imported use_aws from strands_tools")
    USE_STRANDS_TOOLS_AWS = True
except ImportError:
    print("⚠ strands_tools.use_aws not found, will define custom implementation")
    use_aws = None
    USE_STRANDS_TOOLS_AWS = False

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
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
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-20250514-v1:0")
AGENT_NAME = "trade-extraction-agent"
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
DEPLOYMENT_STAGE = os.getenv("DEPLOYMENT_STAGE", "development")

# AgentCore Memory Configuration
# Memory ID for the shared trade matching memory resource
# This memory uses 3 built-in strategies: semantic, preferences, summaries
MEMORY_ID = os.getenv(
    "AGENTCORE_MEMORY_ID",
    "trade_matching_decisions-Z3tG4b4Xsd"  # Default memory resource ID - shared across all agents
)

# Fallback use_aws implementation if strands_tools not available
if not USE_STRANDS_TOOLS_AWS:
    @tool
    def use_aws(service_name: str, operation_name: str, parameters: dict, region: str = REGION, label: str = "") -> str:
        """
        AWS operations tool using boto3.
        
        Args:
            service_name: AWS service (e.g., "s3", "dynamodb")
            operation_name: Operation in snake_case (e.g., "get_object", "put_item")
            parameters: Operation-specific parameters
            region: AWS region
            label: Description of what you're doing
            
        Returns:
            JSON string with operation result
        """
        operation_start = datetime.now(timezone.utc)
        
        # LOG: AWS operation start
        logger.info(f"AWS_OPERATION_START - {service_name}.{operation_name}", extra={
            'service_name': service_name,
            'operation_name': operation_name,
            'region': region,
            'label': label,
            'parameter_keys': list(parameters.keys()) if parameters else [],
            'timestamp': operation_start.isoformat()
        })
        
        try:
            import boto3
            
            client = boto3.client(service_name, region_name=region)
            
            # Convert snake_case to camelCase for boto3
            parts = operation_name.split('_')
            operation_method = parts[0] + ''.join(word.capitalize() for word in parts[1:])
            
            if hasattr(client, operation_method):
                # LOG: Before AWS API call
                logger.debug(f"AWS_API_CALL - Executing {operation_method}", extra={
                    'service_name': service_name,
                    'operation_method': operation_method,
                    'parameters': {k: str(v)[:100] for k, v in parameters.items()} if parameters else {}
                })
                
                result = getattr(client, operation_method)(**parameters)
                
                # Handle streaming responses for S3 GetObject
                if service_name == "s3" and operation_name == "get_object" and "Body" in result:
                    body_content = result["Body"].read()
                    content_size = len(body_content)
                    
                    if isinstance(body_content, bytes):
                        try:
                            body_content = body_content.decode('utf-8')
                        except UnicodeDecodeError:
                            body_content = body_content.decode('utf-8', errors='ignore')
                    result["Body"] = body_content
                    
                    # LOG: S3 content processing
                    logger.info(f"AWS_S3_CONTENT - Processed S3 object content", extra={
                        'service_name': service_name,
                        'operation_name': operation_name,
                        'content_size_bytes': content_size,
                        'content_type': result.get('ContentType', 'unknown')
                    })
                
                operation_time_ms = (datetime.now(timezone.utc) - operation_start).total_seconds() * 1000
                
                # LOG: Successful AWS operation
                logger.info(f"AWS_OPERATION_SUCCESS - {service_name}.{operation_name} completed", extra={
                    'service_name': service_name,
                    'operation_name': operation_name,
                    'operation_time_ms': operation_time_ms,
                    'label': label,
                    'result_keys': list(result.keys()) if isinstance(result, dict) else [],
                    'success': True
                })
                
                return json.dumps({
                    "success": True, 
                    "result": result, 
                    "service": service_name, 
                    "operation": operation_name,
                    "operation_time_ms": operation_time_ms
                }, default=str)
            else:
                error_msg = f"Operation {operation_method} not found on {service_name} client"
                
                # LOG: Operation not found error
                logger.error(f"AWS_OPERATION_ERROR - {error_msg}", extra={
                    'service_name': service_name,
                    'operation_name': operation_name,
                    'operation_method': operation_method,
                    'available_methods': [m for m in dir(client) if not m.startswith('_')][:10],
                    'error_type': 'method_not_found'
                })
                
                return json.dumps({
                    "success": False, 
                    "error": error_msg,
                    "error_type": "method_not_found"
                })
                
        except Exception as e:
            operation_time_ms = (datetime.now(timezone.utc) - operation_start).total_seconds() * 1000
            
            # LOG: AWS operation failure with context
            logger.error(f"AWS_OPERATION_FAILED - {service_name}.{operation_name} failed", extra={
                'service_name': service_name,
                'operation_name': operation_name,
                'operation_time_ms': operation_time_ms,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'label': label,
                'parameters': {k: str(v)[:50] for k, v in parameters.items()} if parameters else {}
            }, exc_info=True)
            
            return json.dumps({
                "success": False, 
                "error": str(e), 
                "error_type": type(e).__name__,
                "operation_time_ms": operation_time_ms
            })

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
            "trade_id (partition key - lowercase)",
            "internal_reference (sort key - required for composite key)",
            "TRADE_SOURCE (must match table: BANK or COUNTERPARTY)"
        ],
        "validation_rules": {
            "trade_id": "Must be unique and non-empty (use lowercase 'trade_id' not 'Trade_ID')",
            "internal_reference": "Required sort key - use document_id or generate unique reference",
            "TRADE_SOURCE": "Must be exactly 'BANK' or 'COUNTERPARTY'",
            "dates": "Recommended format: YYYY-MM-DD",
            "numbers": "Must use DynamoDB N type with string representation"
        },
        "business_rules": {
            "table_routing": "BANK trades → BankTradeData, COUNTERPARTY trades → CounterpartyTradeData",
            "data_integrity": "TRADE_SOURCE field must match target table",
            "critical_fields": ["trade_id", "internal_reference", "notional", "currency", "trade_date", "counterparty"]
        }
    }
    
    return json.dumps(context, indent=2)

@tool
def validate_extraction_result(trade_data: dict, target_table: str) -> str:
    """
    Validate extracted trade data against business rules.
    
    Args:
        trade_data: Extracted trade data
        target_table: Target DynamoDB table name
        
    Returns:
        JSON string with validation results
    """
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }

    # Check required fields (using lowercase trade_id to match actual DynamoDB schema)
    required_fields = ["trade_id", "internal_reference", "TRADE_SOURCE"]
    for field in required_fields:
        if not trade_data.get(field):
            validation_results["valid"] = False
            validation_results["errors"].append(f"Missing required field: {field}")
    
    # Check TRADE_SOURCE matches table
    trade_source = trade_data.get("TRADE_SOURCE", "")
    if target_table == BANK_TABLE and trade_source != "BANK":
        logger.warning(f"TRADE_SOURCE '{trade_source}' doesn't exactly match table '{target_table}' - allowing for flexibility")
    elif target_table == COUNTERPARTY_TABLE and trade_source != "COUNTERPARTY":
        logger.warning(f"TRADE_SOURCE '{trade_source}' doesn't exactly match table '{target_table}' - allowing for flexibility")
    
    # Check data types for DynamoDB
    for key, value in trade_data.items():
        if value is not None and not isinstance(value, (str, int, float, bool)):
            validation_results["warnings"].append(f"Field '{key}' may need type conversion for DynamoDB")
    
    return json.dumps(validation_results)

@tool
def send_metrics(metric_name: str, value: float, dimensions: dict = None, unit: str = "Count") -> str:
    """
    Send custom metrics to CloudWatch.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        dimensions: Optional dimensions for the metric
        unit: Metric unit (Count, Milliseconds, etc.)
        
    Returns:
        JSON string with operation result
    """
    try:
        # LOG: Metrics operation start
        logger.info(f"METRICS_SEND - Sending metric to CloudWatch", extra={
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'dimensions': dimensions,
            'deployment_stage': DEPLOYMENT_STAGE
        })
        
        if DEPLOYMENT_STAGE != "production":
            logger.info(f"METRICS_SKIP - Metrics disabled in non-production environment", extra={
                'deployment_stage': DEPLOYMENT_STAGE,
                'metric_name': metric_name,
                'value': value
            })
            return json.dumps({"success": True, "message": "Metrics disabled in non-production"})
        
        import boto3
        cloudwatch = boto3.client('cloudwatch', region_name=REGION)
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.now(timezone.utc)
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': str(v)} for k, v in dimensions.items()
            ]
        
        cloudwatch.put_metric_data(
            Namespace='TradeMatching/Agents',
            MetricData=[metric_data]
        )
        
        # LOG: Successful metrics send
        logger.info(f"METRICS_SUCCESS - Metric sent successfully", extra={
            'metric_name': metric_name,
            'namespace': 'TradeMatching/Agents',
            'value': value,
            'unit': unit
        })
        
        return json.dumps({"success": True, "metric_sent": metric_name})
        
    except Exception as e:
        # LOG: Metrics send failure
        logger.error(f"METRICS_ERROR - Failed to send metric", extra={
            'metric_name': metric_name,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'value': value,
            'unit': unit
        }, exc_info=True)
        
        return json.dumps({"success": False, "error": str(e)})

@tool
def log_processing_event(event_type: str, details: dict) -> str:
    """
    Log processing events for audit and monitoring.
    
    Args:
        event_type: Type of event (extraction_started, extraction_completed, error_occurred)
        details: Event details
        
    Returns:
        JSON string with logging result
    """
    try:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "event_type": event_type,
            "details": details,
            "deployment_stage": DEPLOYMENT_STAGE,
            "region": REGION
        }
        
        # LOG: Processing event with structured data
        logger.info(f"PROCESSING_EVENT - {event_type}", extra={
            'event_type': event_type,
            'agent_name': AGENT_NAME,
            'agent_version': AGENT_VERSION,
            'details': details,
            'deployment_stage': DEPLOYMENT_STAGE,
            'correlation_id': details.get('correlation_id') if isinstance(details, dict) else None
        })
        
        # Also log as JSON for easy parsing
        logger.info(f"PROCESSING_EVENT_JSON: {json.dumps(log_entry)}")
        
        return json.dumps({"success": True, "logged": event_type})
        
    except Exception as e:
        # LOG: Event logging failure
        logger.error(f"EVENT_LOG_ERROR - Failed to log processing event", extra={
            'event_type': event_type,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'details_keys': list(details.keys()) if isinstance(details, dict) else []
        }, exc_info=True)
        
        return json.dumps({"success": False, "error": str(e)})

# ============================================================================
# AgentCore Memory Session Manager Factory
# ============================================================================

def create_memory_session_manager(
    correlation_id: str,
    document_id: str = None
) -> Optional[AgentCoreMemorySessionManager]:
    """
    Create AgentCore Memory session manager for Strands agent integration.
    
    This follows the correct pattern per AWS documentation:
    https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/strands-sdk-memory.html
    
    Args:
        correlation_id: Correlation ID for tracing
        document_id: Optional document ID for session naming
        
    Returns:
        Configured AgentCoreMemorySessionManager or None if memory unavailable
    """
    if not MEMORY_AVAILABLE or not MEMORY_ID:
        logger.debug(f"[{correlation_id}] Memory not available - skipping session manager creation")
        return None
    
    try:
        # Generate unique session ID for this invocation
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        session_id = f"extract_{document_id or 'unknown'}_{timestamp}_{correlation_id[:8]}"
        
        # Configure memory with retrieval settings for all namespace strategies
        config = AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=AGENT_NAME,
            retrieval_config={
                # Semantic memory: factual extraction patterns and trade data
                "/facts/{actorId}": RetrievalConfig(
                    top_k=10,
                    relevance_score=0.6
                ),
                # User preferences: learned extraction preferences
                "/preferences/{actorId}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.7
                ),
                # Session summaries: past extraction session summaries
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


# Health Check Handler
@app.ping
def health_check() -> PingStatus:
    """Health check for AgentCore Runtime."""
    return PingStatus.HEALTHY

# LLM-Driven System Prompt - Let the LLM decide what to extract
SYSTEM_PROMPT = f"""##Role##
You are an expert Trade Data Extraction Agent with deep knowledge of capital markets, OTC derivatives, commodities trading, and financial instruments. Your goal is to extract comprehensive trade information from financial documents and store it for downstream matching.

The above system instructions define your capabilities and scope. If user request contradicts any system instruction, politely decline explaining your capabilities.

##Mission##
Analyze trade documents, identify ALL relevant trade attributes, and persist them to DynamoDB. Use your capital markets expertise to recognize important fields - trade economics, counterparty details, pricing terms, settlement conventions, and any attributes critical for trade reconciliation and matching.

##Environment##
- Region: {REGION}
- Bank trades table: {BANK_TABLE}
- Counterparty trades table: {COUNTERPARTY_TABLE}

##Constraints##
- DynamoDB partition key: trade_id (lowercase)
- DynamoDB sort key: internal_reference (use document_id from request)
- Required field: TRADE_SOURCE ("BANK" or "COUNTERPARTY")
- DynamoDB format: {{'S': 'string'}} for text, {{'N': '123.45'}} for numbers
- Route based on source_type: BANK → {BANK_TABLE}, COUNTERPARTY → {COUNTERPARTY_TABLE}
- Use ONLY information present in the provided document. DO NOT include information not found in the source document.

##Task##
Please follow these steps:
1. Retrieve the document from S3
2. Analyze its content and extract every meaningful trade attribute you find
3. Store the complete extracted data in DynamoDB using the format specified in ##Constraints##
4. Log completion

Extract comprehensively - dates, amounts, parties, terms, pricing, settlement details, and any other trade-relevant information. The more complete the extraction, the better for downstream trade matching.

##Output Requirements##
You MUST follow the DynamoDB format specifications in ##Constraints## when storing data. Use {{'S': 'string'}} for text values and {{'N': '123.45'}} for numeric values. DO NOT deviate from the required format.

Output Schema:
{{
    "type": "object",
    "properties": {{
        "extraction_status": {{"type": "string", "description": "SUCCESS or FAILED"}},
        "trade_data": {{"type": "object", "description": "Extracted trade attributes in DynamoDB format"}},
        "dynamodb_response": {{"type": "object", "description": "DynamoDB operation result"}},
        "log_message": {{"type": "string", "description": "Completion log entry"}}
    }},
    "required": ["extraction_status", "trade_data", "log_message"]
}}
"""

def create_extraction_agent(
    session_manager: Optional[AgentCoreMemorySessionManager] = None
) -> Agent:
    """
    Create and configure the Strands extraction agent with memory.
    
    Args:
        session_manager: Optional AgentCore Memory session manager for automatic
                        memory management. When provided, the agent automatically
                        stores and retrieves conversation context.
    
    Returns:
        Configured Strands Agent with tools and optional memory
    """
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0,  # Greedy decoding for tool calling (Nova Pro requirement)
        max_tokens=4096,
    )
    
    # Create agent with optional memory integration
    if session_manager:
        return Agent(
            model=bedrock_model,
            system_prompt=SYSTEM_PROMPT,
            tools=[
                use_aws,
                get_extraction_context,
                validate_extraction_result,
                send_metrics,
                log_processing_event
            ],
            session_manager=session_manager
        )
    else:
        return Agent(
            model=bedrock_model,
            system_prompt=SYSTEM_PROMPT,
            tools=[
                use_aws,
                get_extraction_context,
                validate_extraction_result,
                send_metrics,
                log_processing_event
            ]
        )

def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    LLM-Centric AgentCore Runtime entrypoint.
    
    This function provides minimal scaffolding and lets the LLM agent
    drive all decision-making through tool usage.
    """
    start_time = datetime.now(timezone.utc)
    
    # Extract basic information
    document_id = payload.get("document_id")
    canonical_output_location = payload.get("canonical_output_location")
    source_type = payload.get("source_type", "")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # LOG: Request received with full payload details
    logger.info(f"[{correlation_id}] INVOKE_START - Agent invocation started", extra={
        'correlation_id': correlation_id,
        'document_id': document_id,
        'canonical_output_location': canonical_output_location,
        'source_type': source_type,
        'agent_name': AGENT_NAME,
        'agent_version': AGENT_VERSION,
        'payload_size_bytes': len(json.dumps(payload)),
        'timestamp': start_time.isoformat()
    })
    
    # LOG: Input validation
    logger.debug(f"[{correlation_id}] INPUT_VALIDATION - Validating input parameters", extra={
        'has_document_id': bool(document_id),
        'has_canonical_output': bool(canonical_output_location),
        'source_type_provided': bool(source_type),
        'payload_keys': list(payload.keys())
    })
    
    # Basic validation (minimal hardcoded logic)
    if not document_id or not canonical_output_location:
        error_msg = "Missing required fields: document_id or canonical_output_location"
        logger.error(f"[{correlation_id}] VALIDATION_ERROR - {error_msg}", extra={
            'correlation_id': correlation_id,
            'missing_document_id': not bool(document_id),
            'missing_canonical_output': not bool(canonical_output_location),
            'provided_fields': [k for k, v in payload.items() if v],
            'error_type': 'validation_error'
        })
        
        return {
            "success": False,
            "error": error_msg,
            "agent_name": AGENT_NAME,
            "correlation_id": correlation_id,
            "error_type": "validation_error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    try:
        # Create memory session manager for this invocation (if memory is enabled)
        session_manager = None
        if MEMORY_AVAILABLE and MEMORY_ID:
            session_manager = create_memory_session_manager(
                correlation_id=correlation_id,
                document_id=document_id
            )
        
        # LOG: Agent creation
        logger.info(f"[{correlation_id}] AGENT_CREATE - Creating LLM agent", extra={
            'correlation_id': correlation_id,
            'model_id': BEDROCK_MODEL_ID,
            'region': REGION,
            'temperature': 0.1,
            'max_tokens': 4096,
            'memory_enabled': session_manager is not None
        })
        
        # Create the agent with optional memory integration
        agent = create_extraction_agent(session_manager=session_manager)
        
        if session_manager:
            logger.info(f"[{correlation_id}] Agent created with AgentCore Memory integration")
        else:
            logger.info(f"[{correlation_id}] Agent created without memory (memory disabled or unavailable)")
        
        # Construct goal-oriented prompt - let LLM decide the approach
        prompt = f"""**Goal**: Extract and store trade data from canonical adapter output.

**Context**:
- Document: {document_id}  
- Canonical Output Location: {canonical_output_location}
- Source Type: {source_type if source_type else "Unknown - determine from data"}
- Correlation ID: {correlation_id}

**Instructions**:
1. First, read the trade data from the S3 location using use_aws
2. Extract relevant trade fields from the JSON data
3. Store the data directly in DynamoDB using use_aws (do NOT validate first - just store)
4. Log completion and send metrics

**Important**: Skip all validation steps - just read, extract, store, and complete. Focus on getting data into DynamoDB.
"""
        
        # LOG: LLM invocation start
        logger.info(f"[{correlation_id}] LLM_INVOKE_START - Starting LLM processing", extra={
            'correlation_id': correlation_id,
            'prompt_length': len(prompt),
            'tools_available': len(agent.tools) if hasattr(agent, 'tools') else 0
        })
        
        # Let the LLM agent drive the entire process
        logger.info("Invoking LLM-centric trade extraction agent")
        result = agent(prompt)
        
        # LOG: LLM invocation complete
        logger.info(f"[{correlation_id}] LLM_INVOKE_COMPLETE - LLM processing completed", extra={
            'correlation_id': correlation_id,
            'result_type': type(result).__name__,
            'has_message': hasattr(result, 'message'),
            'has_metrics': hasattr(result, 'metrics') or hasattr(result, 'usage')
        })
        
        # Calculate processing time
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # Extract response text
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
        
        # Extract token metrics if available
        # Per Strands SDK docs, use get_summary()["accumulated_usage"] with camelCase keys
        # Requirements: 10.1, 10.2, 10.4
        token_metrics = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        try:
            if hasattr(result, 'metrics') and result.metrics:
                summary = result.metrics.get_summary()
                usage = summary.get("accumulated_usage", {})
                # Note: Strands uses camelCase (inputTokens, outputTokens)
                token_metrics["input_tokens"] = usage.get("inputTokens", 0) or 0
                token_metrics["output_tokens"] = usage.get("outputTokens", 0) or 0
                token_metrics["total_tokens"] = usage.get("totalTokens", 0) or (token_metrics["input_tokens"] + token_metrics["output_tokens"])
                
                # Log warning if token counts are zero (potential instrumentation issue)
                if token_metrics["total_tokens"] == 0:
                    logger.warning(f"[{correlation_id}] Token counting returned zero - potential instrumentation issue")
        except Exception as e:
            logger.warning(f"[{correlation_id}] Failed to extract token metrics: {e}")
        
        # LOG: Successful completion with metrics
        logger.info(f"[{correlation_id}] INVOKE_SUCCESS - Agent execution completed successfully", extra={
            'correlation_id': correlation_id,
            'document_id': document_id,
            'source_type': source_type,
            'processing_time_ms': processing_time_ms,
            'token_usage': token_metrics,
            'response_length': len(response_text),
            'agent_name': AGENT_NAME,
            'agent_version': AGENT_VERSION,
            'model_id': BEDROCK_MODEL_ID,
            'deployment_stage': DEPLOYMENT_STAGE,
            'memory_enabled': session_manager is not None
        })
        
        # LOG: Performance metrics for monitoring
        if processing_time_ms > 30000:  # Log slow requests
            logger.warning(f"[{correlation_id}] PERFORMANCE_WARNING - Slow processing detected", extra={
                'correlation_id': correlation_id,
                'processing_time_ms': processing_time_ms,
                'threshold_ms': 30000,
                'document_id': document_id
            })
        
        return {
            "success": True,
            "document_id": document_id,
            "source_type": source_type,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "token_usage": token_metrics,
            "model_id": BEDROCK_MODEL_ID,
            "deployment_stage": DEPLOYMENT_STAGE,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # LOG: Detailed error information
        logger.error(f"[{correlation_id}] INVOKE_ERROR - Agent execution failed", extra={
            'correlation_id': correlation_id,
            'document_id': document_id,
            'source_type': source_type,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'processing_time_ms': processing_time_ms,
            'agent_name': AGENT_NAME,
            'agent_version': AGENT_VERSION,
            'model_id': BEDROCK_MODEL_ID,
            'canonical_output_location': canonical_output_location
        }, exc_info=True)
        
        # LOG: Additional context for debugging
        logger.debug(f"[{correlation_id}] ERROR_CONTEXT - Additional debugging information", extra={
            'correlation_id': correlation_id,
            'payload_keys': list(payload.keys()),
            'environment_vars': {
                'AWS_REGION': REGION,
                'S3_BUCKET_NAME': S3_BUCKET,
                'DEPLOYMENT_STAGE': DEPLOYMENT_STAGE
            },
            'stack_trace': str(e)
        })
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "document_id": document_id,
            "correlation_id": correlation_id,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "canonical_output_location": canonical_output_location,
            "source_type": source_type
        }

# Register with AgentCore Runtime
app.entrypoint(invoke)

def main():
    """CLI entry point for testing and AgentCore Runtime."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM-Centric Trade Data Extraction Agent")
    parser.add_argument("--mode", choices=["runtime", "test"], default="runtime")
    parser.add_argument("--document-id", help="Document ID for testing")
    parser.add_argument("--canonical-output-location", help="S3 location of canonical output")
    parser.add_argument("--source-type", choices=["BANK", "COUNTERPARTY"], help="Trade source type")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.mode == "test" and args.document_id and args.canonical_output_location:
        # CLI testing mode
        print(f"🧪 Testing LLM-Centric Trade Extraction Agent")
        print(f"Document ID: {args.document_id}")
        print(f"Canonical Output: {args.canonical_output_location}")
        print(f"Source Type: {args.source_type}")
        
        test_payload = {
            "document_id": args.document_id,
            "canonical_output_location": args.canonical_output_location,
            "source_type": args.source_type or "BANK",
            "correlation_id": f"cli_test_{uuid.uuid4().hex[:8]}"
        }
        
        result = invoke(test_payload)
        
        print(f"\n📊 Results:")
        print(f"Success: {result.get('success', False)}")
        if result.get('success'):
            print(f"Processing Time: {result.get('processing_time_ms', 0):.0f}ms")
            print(f"Token Usage: {result.get('token_usage', {})}")
            print(f"Agent Response: {result.get('agent_response', '')[:200]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return result.get('success', False)
    
    else:
        # AgentCore Runtime mode
        print(f"🚀 Starting LLM-Centric Trade Extraction Agent")
        app.run()

if __name__ == "__main__":
    main()