"""
Trade Matching Swarm - Strands SDK Multi-Agent Implementation

This swarm orchestrates multiple specialized agents that autonomously collaborate
to process trade confirmations from PDF ingestion through matching.

Agents hand off to each other based on their expertise:
- PDF Adapter → Trade Extraction → Trade Matching → Exception Management

The swarm enables emergent collaboration where agents decide when to hand off
based on task context, not hardcoded workflow steps.
"""

import os
import json
import uuid
import base64
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands.multiagent import Swarm

# Try to import use_aws from strands-tools
try:
    from strands_tools.aws import use_aws
except ImportError:
    use_aws = None

# AgentCore Memory imports
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)

# Memory error handling imports
from memory_error_handling import (
    MemoryFallbackHandler,
    get_fallback_handler,
    create_session_manager_safe,
    retrieve_with_timeout,
    store_pattern_safe
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import shared AWS resources
from aws_resources import get_aws_client, get_config

# Get shared configuration
_config = get_config()
REGION = _config["region"]
S3_BUCKET = _config["s3_bucket"]
BANK_TABLE = _config["bank_table"]
COUNTERPARTY_TABLE = _config["counterparty_table"]
EXCEPTIONS_TABLE = _config["exceptions_table"]
BEDROCK_MODEL_ID = _config["bedrock_model_id"]  # Use configured model (amazon.nova-pro-v1:0)



# ============================================================================
# PDF Adapter Tools
# ============================================================================

@tool
def download_pdf_from_s3(bucket: str, key: str, document_id: str) -> str:
    """
    Download a PDF file from S3 and return its base64-encoded content.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key (path to the PDF)
        document_id: Unique identifier for the document
        
    Returns:
        JSON string with success status, base64 PDF content, and file size
    """
    try:
        s3_client = get_aws_client('s3')
        local_path = f"/tmp/{document_id}.pdf"
        
        s3_client.download_file(bucket, key, local_path)
        
        with open(local_path, 'rb') as f:
            pdf_bytes = f.read()
        
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return json.dumps({
            "success": True,
            "pdf_base64": pdf_base64,
            "file_size_bytes": len(pdf_bytes),
            "local_path": local_path
        })
    except Exception as e:
        logger.error(f"Failed to download PDF from S3: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def extract_text_with_bedrock(pdf_base64: str, document_id: str) -> str:
    """
    Extract text from a PDF using AWS Bedrock's multimodal capabilities.
    
    Args:
        pdf_base64: Base64-encoded PDF content
        document_id: Unique identifier for the document
        
    Returns:
        JSON string with success status and extracted text
    """
    try:
        bedrock_client = get_aws_client('bedrock-runtime')
        pdf_bytes = base64.b64decode(pdf_base64)
        
        sanitized_name = re.sub(r'[^a-zA-Z0-9\-\(\)\[\]\s]', '-', document_id)
        sanitized_name = re.sub(r'\s+', ' ', sanitized_name).strip()
        
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[{
                "role": "user",
                "content": [
                    {"document": {"format": "pdf", "name": sanitized_name, "source": {"bytes": pdf_bytes}}},
                    {"text": """Extract ALL text from this trade confirmation PDF document.
Include every piece of text visible in the document, maintaining the structure.
Extract all trade details including:
- Trade ID / Reference numbers
- Dates (trade date, effective date, maturity date, etc.)
- Counterparty information
- Notional amounts and currencies
- Product type and commodity details
- Settlement information
- Any other relevant trade terms

Return the complete extracted text."""}
                ]
            }]
        )
        
        extracted_text = response['output']['message']['content'][0]['text']
        return json.dumps({
            "success": True,
            "extracted_text": extracted_text,
            "text_length": len(extracted_text)
        })
    except Exception as e:
        logger.error(f"Failed to extract text with Bedrock: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def save_canonical_output(
    document_id: str,
    source_type: str,
    extracted_text: str,
    correlation_id: str
) -> str:
    """
    Save the canonical adapter output to S3 in the standardized format.
    
    Args:
        document_id: Unique identifier for the document
        source_type: BANK or COUNTERPARTY
        extracted_text: The extracted text from the PDF
        correlation_id: Correlation ID for tracing
        
    Returns:
        JSON string with success status and S3 location
    """
    try:
        s3_client = get_aws_client('s3')
        
        canonical_output = {
            "adapter_type": "PDF",
            "document_id": document_id,
            "source_type": source_type,
            "extracted_text": extracted_text,
            "metadata": {
                "processing_timestamp": datetime.utcnow().isoformat(),
                "ocr_model": BEDROCK_MODEL_ID
            },
            "s3_location": f"s3://{S3_BUCKET}/extracted/{source_type}/{document_id}.json",
            "correlation_id": correlation_id
        }
        
        canonical_output_key = f"extracted/{source_type}/{document_id}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=canonical_output_key,
            Body=json.dumps(canonical_output, indent=2),
            ContentType='application/json'
        )
        
        return json.dumps({
            "success": True,
            "canonical_output_location": f"s3://{S3_BUCKET}/{canonical_output_key}",
            "document_id": document_id,
            "source_type": source_type
        })
    except Exception as e:
        logger.error(f"Failed to save canonical output: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================================================================
# Trade Extraction Tools
# ============================================================================

@tool
def read_canonical_output(document_id: str, source_type: str) -> str:
    """
    Read canonical output from S3.
    
    Args:
        document_id: Unique identifier for the document
        source_type: BANK or COUNTERPARTY
        
    Returns:
        JSON string with canonical output data
    """
    try:
        s3_client = get_aws_client('s3')
        canonical_output_key = f"extracted/{source_type}/{document_id}.json"
        
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=canonical_output_key)
        canonical_data = json.loads(response['Body'].read().decode('utf-8'))
        
        return json.dumps({
            "success": True,
            "canonical_output": canonical_data
        })
    except Exception as e:
        logger.error(f"Failed to read canonical output: {e}")
        return json.dumps({"success": False, "error": str(e)})

@tool
def store_trade_in_dynamodb(trade_data_json: str, source_type: str) -> str:
    """
    Store extracted trade data in the appropriate DynamoDB table.
    
    Args:
        trade_data_json: JSON string containing trade fields (trade_id required)
        source_type: BANK or COUNTERPARTY - determines which table to use
        
    Returns:
        JSON string with success status and table name
    """
    try:
        dynamodb_client = get_aws_client('dynamodb')
        trade_data = json.loads(trade_data_json)
        
        table_name = BANK_TABLE if source_type == "BANK" else COUNTERPARTY_TABLE
        trade_id = trade_data.get("trade_id", trade_data.get("Trade_ID", f"unknown_{uuid.uuid4().hex[:8]}"))
        
        # Convert to DynamoDB typed format
        item = {
            "trade_id": {"S": str(trade_id)},
            "internal_reference": {"S": str(trade_id)},
            "TRADE_SOURCE": {"S": source_type}
        }
        
        # Add all other fields
        for key, value in trade_data.items():
            if key in ["trade_id", "Trade_ID", "internal_reference", "TRADE_SOURCE"]:
                continue
            if isinstance(value, (int, float)):
                item[key] = {"N": str(value)}
            elif value is not None:
                item[key] = {"S": str(value)}
        
        dynamodb_client.put_item(TableName=table_name, Item=item)
        
        return json.dumps({
            "success": True,
            "trade_id": trade_id,
            "table_name": table_name,
            "source_type": source_type
        })
    except Exception as e:
        logger.error(f"Failed to store trade in DynamoDB: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================================================================
# Trade Matching Tools
# ============================================================================

@tool
def scan_trades_table(source_type: str) -> str:
    """
    Scan a DynamoDB table to retrieve all trades.
    
    Args:
        source_type: BANK or COUNTERPARTY - determines which table to scan
        
    Returns:
        JSON string with list of trades from the table
    """
    try:
        dynamodb_client = get_aws_client('dynamodb')
        table_name = BANK_TABLE if source_type == "BANK" else COUNTERPARTY_TABLE
        
        response = dynamodb_client.scan(TableName=table_name)
        
        # Convert DynamoDB format to simple dict
        trades = []
        for item in response.get("Items", []):
            trade = {}
            for key, value in item.items():
                if "S" in value:
                    trade[key] = value["S"]
                elif "N" in value:
                    trade[key] = float(value["N"])
            trades.append(trade)
        
        return json.dumps({
            "success": True,
            "table_name": table_name,
            "trade_count": len(trades),
            "trades": trades
        })
    except Exception as e:
        logger.error(f"Failed to scan trades table: {e}")
        return json.dumps({"success": False, "error": str(e), "trades": []})


@tool
def save_matching_report(
    report_content: str,
    trade_id: str,
    match_classification: str,
    confidence_score: float
) -> str:
    """
    Save a matching analysis report to S3.
    
    Args:
        report_content: Markdown content of the matching report
        trade_id: Trade ID being matched
        match_classification: MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, or BREAK
        confidence_score: Confidence score (0.0 to 1.0)
        
    Returns:
        JSON string with S3 location of the report
    """
    try:
        s3_client = get_aws_client('s3')
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        report_key = f"reports/matching_report_{trade_id}_{timestamp}.md"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=report_key,
            Body=report_content.encode('utf-8'),
            ContentType='text/markdown',
            Metadata={
                'trade_id': trade_id,
                'classification': match_classification,
                'confidence_score': str(confidence_score)
            }
        )
        
        return json.dumps({
            "success": True,
            "report_location": f"s3://{S3_BUCKET}/{report_key}",
            "classification": match_classification,
            "confidence_score": confidence_score
        })
    except Exception as e:
        logger.error(f"Failed to save matching report: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================================================================
# Exception Management Tools
# ============================================================================

@tool
def get_severity_guidelines() -> str:
    """
    Get severity classification guidelines for exception analysis.
    
    Returns:
        JSON with severity level definitions and typical reason code impacts
    """
    guidelines = {
        "severity_levels": {
            "CRITICAL": "Immediate action required - trade cannot settle, regulatory risk, or counterparty mismatch",
            "HIGH": "Urgent attention needed - significant financial discrepancies (notional, currency)",
            "MEDIUM": "Review required - date mismatches, minor discrepancies that may auto-resolve",
            "LOW": "Informational - processing delays, missing non-critical fields"
        },
        "reason_code_impacts": {
            "COUNTERPARTY_MISMATCH": "Typically CRITICAL - wrong trading partner",
            "NOTIONAL_MISMATCH": "Typically HIGH - financial exposure difference",
            "CURRENCY_MISMATCH": "Typically HIGH - FX risk",
            "DATE_MISMATCH": "Typically MEDIUM - may affect settlement timing",
            "MISSING_FIELD": "Typically MEDIUM - depends on field importance",
            "PROCESSING_ERROR": "Typically LOW - technical issue, retry possible"
        },
        "sla_targets": {
            "CRITICAL": "2 hours",
            "HIGH": "4 hours",
            "MEDIUM": "8 hours",
            "LOW": "24 hours"
        }
    }
    
    return json.dumps(guidelines, indent=2)


@tool
def store_exception_record(
    exception_id: str,
    trade_id: str,
    event_type: str,
    severity: str,
    reason_codes: str,
    notes: str,
    sla_hours: int
) -> str:
    """
    Store an exception record in DynamoDB for tracking.
    
    Args:
        exception_id: Unique exception identifier
        trade_id: Associated trade ID
        event_type: Type of exception event
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        reason_codes: Comma-separated reason codes
        notes: Additional notes about the exception
        sla_hours: Number of hours until SLA deadline (agent determines based on severity)
        
    Returns:
        JSON with success status and calculated SLA deadline
    """
    try:
        dynamodb_client = get_aws_client('dynamodb')
        
        sla_deadline = (datetime.utcnow() + timedelta(hours=sla_hours)).isoformat()
        reason_code_list = [code.strip() for code in reason_codes.split(",") if code.strip()]
        
        item = {
            "exception_id": {"S": exception_id},
            "timestamp": {"S": datetime.utcnow().isoformat()},
            "trade_id": {"S": trade_id},
            "event_type": {"S": event_type},
            "severity": {"S": severity},
            "reason_codes": {"SS": reason_code_list if reason_code_list else ["NONE"]},
            "notes": {"S": notes},
            "sla_deadline": {"S": sla_deadline},
            "sla_hours": {"N": str(sla_hours)},
            "resolution_status": {"S": "PENDING"}
        }
        
        dynamodb_client.put_item(TableName=EXCEPTIONS_TABLE, Item=item)
        
        return json.dumps({
            "success": True,
            "exception_id": exception_id,
            "sla_deadline": sla_deadline,
            "sla_hours": sla_hours
        })
    except Exception as e:
        logger.error(f"Failed to store exception: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================================================================
# Fallback use_aws Tool (if not available from strands-tools)
# ============================================================================

if use_aws is None:
    @tool
    def use_aws(service_name: str, operation_name: str, parameters: dict, region: str = "us-east-1", label: str = "") -> str:
        """
        Fallback AWS tool implementation using boto3 directly.
        
        Args:
            service_name: AWS service (e.g., "s3", "dynamodb")
            operation_name: Operation in snake_case (e.g., "get_object", "put_item")
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
                            body_content = base64.b64encode(body_content).decode('utf-8')
                    result["Body"] = body_content
                
                # Remove non-serializable objects
                if "ResponseMetadata" in result:
                    del result["ResponseMetadata"]
                
                return json.dumps({"success": True, "result": result}, default=str)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Operation {operation_method} not found on {service_name} client"
                })
        except Exception as e:
            logger.error(f"AWS operation failed: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})


# ============================================================================
# AgentCore Memory Session Manager Factory
# ============================================================================

def create_agent_session_manager(
    agent_name: str,
    document_id: str,
    memory_id: str = None,
    actor_id: str = "trade_matching_system",
    region_name: str = "us-east-1"
) -> Optional[AgentCoreMemorySessionManager]:
    """
    Create session manager for a specific agent with retrieval configs.
    
    IMPORTANT: Per AgentCore Memory documentation, only one agent per session is supported.
    Each agent in the swarm gets its own session manager with a unique session ID.
    
    This function includes error handling with fallback to operation without memory.
    
    Args:
        agent_name: Name of the agent (pdf_adapter, trade_extractor, etc.)
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        actor_id: Actor identifier (default: trade_matching_system)
        region_name: AWS region (default: us-east-1)
        
    Returns:
        Configured session manager instance for this agent, or None if memory is disabled/fails
    """
    if memory_id is None:
        memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
        if not memory_id:
            logger.warning("AGENTCORE_MEMORY_ID not set - memory integration disabled")
            return None
    
    # Use fallback handler to create session manager with retry logic
    fallback_handler = get_fallback_handler()
    
    def _create_session_manager():
        # Generate unique session ID for this agent and trade
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        session_id = f"trade_{document_id}_{agent_name}_{timestamp}"
        
        # Configure retrieval for all namespaces using built-in strategies
        config = AgentCoreMemoryConfig(
            memory_id=memory_id,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config={
                # Semantic memory: factual trade information
                "/facts/{actorId}": RetrievalConfig(
                    top_k=10,
                    relevance_score=0.6
                ),
                # User preferences: learned processing preferences
                "/preferences/{actorId}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.7
                ),
                # Session summaries: trade processing summaries
                "/summaries/{actorId}/{sessionId}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.5
                )
            }
        )
        
        session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=config,
            region_name=region_name
        )
        
        logger.info(f"Created session manager for {agent_name} with session_id: {session_id}")
        
        return session_manager
    
    # Execute with fallback handling
    try:
        return fallback_handler.execute_with_fallback(
            _create_session_manager,
            operation_name=f"create_session_manager_{agent_name}"
        )
    except Exception as e:
        logger.error(
            f"Failed to create session manager for {agent_name}: {e}. "
            "Continuing without memory integration."
        )
        return None


# ============================================================================
# Bedrock Model Factory
# ============================================================================

def create_bedrock_model() -> BedrockModel:
    """Create a configured Bedrock model for all agents."""
    return BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,
        max_tokens=4096,
    )


# ============================================================================
# Agent System Prompts
# ============================================================================

def get_pdf_adapter_prompt() -> str:
    """Get the PDF Adapter system prompt with memory access guidance."""
    return f"""You are a PDF Adapter specialist for OTC trade confirmations.

## Your Expertise
- Download PDFs from S3
- Extract text using Bedrock's multimodal capabilities
- Save canonical output for downstream processing
- Learn from past extraction patterns stored in memory

## Memory Access
You have access to historical extraction patterns in semantic memory (/facts) and learned preferences (/preferences):
1. Check memory for similar document layouts and extraction techniques
2. Apply successful patterns from past processing
3. Record new extraction techniques that work well to /facts
4. Store OCR preferences and quality improvements to /preferences

## Resources
- S3 Bucket: {S3_BUCKET}
- Region: {REGION}

## Tools
- download_pdf_from_s3: Get PDF from S3
- extract_text_with_bedrock: OCR the PDF content
- save_canonical_output: Save standardized output to S3

## When to Hand Off
- After successfully extracting text and saving canonical output → hand off to trade_extractor
- If extraction fails → hand off to exception_handler with error details

## Output
Always report the canonical_output_location when successful so the next agent can find the data.
"""

def get_trade_extractor_prompt() -> str:
    """Get the Trade Extraction system prompt with memory access guidance."""
    return f"""You are a Trade Data Extraction specialist for OTC derivatives.

## Your Expertise
- Parse extracted text to identify trade fields
- Structure data for DynamoDB storage
- Route trades to correct table based on source type
- Learn from past field mapping patterns stored in memory

## Memory Access
You have access to historical field extraction patterns in semantic memory (/facts) and learned preferences (/preferences):
1. Check memory for similar field mapping scenarios
2. Apply successful extraction techniques from past trades
3. Record new field mappings that work well to /facts
4. Store extraction preferences and error corrections to /preferences

## Resources
- Bank Table: {BANK_TABLE}
- Counterparty Table: {COUNTERPARTY_TABLE}

## Key Fields to Extract
- trade_id / Trade_ID (REQUIRED)
- trade_date, effective_date, maturity_date
- notional, currency
- counterparty, buyer, seller
- product_type (SWAP, OPTION, FORWARD)
- fixed_rate, floating_rate_index

## Tools
- use_aws: Read canonical output from S3
- store_trade_in_dynamodb: Save extracted trade data

## When to Hand Off
- After storing trade successfully → hand off to trade_matcher
- If extraction fails or data is incomplete → hand off to exception_handler
"""

def get_trade_matcher_prompt() -> str:
    """Get the Trade Matching system prompt with memory access guidance."""
    return f"""You are a Trade Matching specialist for OTC derivatives.

## Your Expertise
- Match trades between bank and counterparty systems
- Trades have DIFFERENT IDs across systems - match by attributes
- Calculate confidence scores based on attribute alignment
- Learn from past matching decisions stored in memory

## Memory Access
You have access to historical matching decisions in semantic memory (/facts) and learned preferences (/preferences):
1. Check memory for similar trade matching scenarios
2. Apply consistent decision-making based on past cases
3. Record matching decisions with rationale to /facts
4. Store HITL feedback and threshold adjustments to /preferences

## Matching Strategy
Match by attributes, NOT by Trade_ID:
- Currency (exact match)
- Notional (within 2% tolerance)
- Maturity/Termination Date (within 2 days)
- Trade Date (within 2 days)
- Counterparty names (fuzzy match)
- Product Type

## Classification Guidelines
- MATCHED (85%+): All key attributes align
- PROBABLE_MATCH (70-84%): Most attributes match
- REVIEW_REQUIRED (50-69%): Some discrepancies
- BREAK (<50%): Not the same trade

## Tools
- scan_trades_table: Get trades from BANK or COUNTERPARTY table
- save_matching_report: Save analysis to S3

## Your Decision-Making
You decide how to approach the matching analysis. Consider:
- Which tables to scan and when
- How to calculate confidence scores
- What constitutes a significant discrepancy
- Whether issues warrant escalation to exception_handler

Hand off to exception_handler if you identify issues requiring attention (REVIEW_REQUIRED or BREAK classifications), but use your judgment about severity.
"""

def get_exception_handler_prompt() -> str:
    """Get the Exception Handler system prompt with memory access guidance."""
    return f"""You are an Exception Management specialist for trade processing.

## Your Expertise
- Analyze exceptions and determine appropriate severity levels
- Calculate SLA deadlines based on business impact
- Route exceptions to appropriate teams
- Track exceptions for resolution
- Learn from past exception resolutions stored in memory

## Memory Access
You have access to historical exception resolution patterns in semantic memory (/facts) and learned preferences (/preferences):
1. Check memory for similar exception scenarios
2. Apply consistent severity classification based on past cases
3. Record resolution strategies that worked well to /facts
4. Store severity classification adjustments to /preferences

## Your Approach
1. First, call get_severity_guidelines() to understand severity classification rules
2. Analyze the exception details (event type, reason codes, match score if available)
3. Check memory for similar past exceptions and their resolutions
4. Determine the appropriate severity level (CRITICAL, HIGH, MEDIUM, LOW) based on:
   - Business impact (counterparty mismatches are most critical)
   - Financial exposure (notional/currency mismatches)
   - Settlement risk (date mismatches)
   - Operational impact (processing errors)
   - Historical patterns from memory
5. Calculate appropriate SLA hours based on severity
6. Store the exception record with your determined severity and SLA

## Tools
- get_severity_guidelines: Get severity classification rules and SLA targets
- store_exception_record: Save exception to ExceptionsTable (you provide severity and sla_hours)

## When to Hand Off
- After recording exception → report findings (no handoff needed)
- If you need more context about the trade → hand off to trade_matcher

## Important
YOU decide the severity level and SLA hours based on the exception context. Use the guidelines as reference, but apply your judgment to the specific situation and learn from past resolutions.
"""


# ============================================================================
# Agent Factory Functions
# ============================================================================

def create_pdf_adapter_agent(document_id: str, memory_id: str = None) -> Agent:
    """
    Create PDF Adapter agent with its own session manager.
    
    Memory Usage:
    - Reads from /facts/{actorId} for extraction patterns and document layouts
    - Reads from /preferences/{actorId} for learned OCR preferences
    - Writes successful extraction techniques to /facts/{actorId}
    - Writes processing preferences to /preferences/{actorId}
    
    Args:
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        
    Returns:
        Configured Agent instance with memory integration
    """
    # Create dedicated session manager for this agent
    session_manager = create_agent_session_manager(
        agent_name="pdf_adapter",
        document_id=document_id,
        memory_id=memory_id
    )
    
    return Agent(
        name="pdf_adapter",
        model=create_bedrock_model(),
        system_prompt=get_pdf_adapter_prompt(),
        tools=[
            download_pdf_from_s3,
            extract_text_with_bedrock,
            save_canonical_output
        ],
        session_manager=session_manager
    )


def create_trade_extractor_agent(document_id: str, memory_id: str = None) -> Agent:
    """
    Create Trade Extraction agent with its own session manager.
    
    Memory Usage:
    - Reads from /facts/{actorId} for field mapping patterns
    - Reads from /preferences/{actorId} for extraction preferences
    - Writes successful field mappings to /facts/{actorId}
    - Writes extraction preferences to /preferences/{actorId}
    
    Args:
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        
    Returns:
        Configured Agent instance with memory integration
    """
    # Create dedicated session manager for this agent
    session_manager = create_agent_session_manager(
        agent_name="trade_extractor",
        document_id=document_id,
        memory_id=memory_id
    )
    
    return Agent(
        name="trade_extractor",
        model=create_bedrock_model(),
        system_prompt=get_trade_extractor_prompt(),
        tools=[
            store_trade_in_dynamodb,
            use_aws
        ],
        session_manager=session_manager
    )


def create_trade_matcher_agent(document_id: str, memory_id: str = None) -> Agent:
    """
    Create Trade Matching agent with its own session manager.
    
    Memory Usage:
    - Reads from /facts/{actorId} for matching decisions and patterns
    - Reads from /preferences/{actorId} for matching thresholds
    - Writes matching decisions and rationale to /facts/{actorId}
    - Writes HITL feedback and threshold adjustments to /preferences/{actorId}
    
    Args:
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        
    Returns:
        Configured Agent instance with memory integration
    """
    # Create dedicated session manager for this agent
    session_manager = create_agent_session_manager(
        agent_name="trade_matcher",
        document_id=document_id,
        memory_id=memory_id
    )
    
    return Agent(
        name="trade_matcher",
        model=create_bedrock_model(),
        system_prompt=get_trade_matcher_prompt(),
        tools=[
            scan_trades_table,
            save_matching_report,
            use_aws
        ],
        session_manager=session_manager
    )


def create_exception_handler_agent(document_id: str, memory_id: str = None) -> Agent:
    """
    Create Exception Handler agent with its own session manager.
    
    Memory Usage:
    - Reads from /facts/{actorId} for exception resolution patterns
    - Reads from /preferences/{actorId} for severity classification preferences
    - Writes resolution strategies to /facts/{actorId}
    - Writes severity classification adjustments to /preferences/{actorId}
    
    Args:
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        
    Returns:
        Configured Agent instance with memory integration
    """
    # Create dedicated session manager for this agent
    session_manager = create_agent_session_manager(
        agent_name="exception_handler",
        document_id=document_id,
        memory_id=memory_id
    )
    
    return Agent(
        name="exception_handler",
        model=create_bedrock_model(),
        system_prompt=get_exception_handler_prompt(),
        tools=[
            get_severity_guidelines,
            store_exception_record,
            use_aws
        ],
        session_manager=session_manager
    )


# ============================================================================
# Swarm Creation
# ============================================================================

def create_trade_matching_swarm_with_memory(
    document_id: str,
    memory_id: str = None
) -> Swarm:
    """
    Create the Trade Matching Swarm with AgentCore Memory integration.
    
    IMPORTANT: Each agent gets its own session manager to comply with AgentCore Memory's
    "one agent per session" limitation. All agents share the same memory resource and
    actor ID, enabling cross-agent learning while maintaining session isolation.
    
    The swarm enables autonomous collaboration:
    - pdf_adapter processes PDFs and hands off to trade_extractor
    - trade_extractor parses data and hands off to trade_matcher
    - trade_matcher analyzes matches and may hand off to exception_handler
    - exception_handler triages issues
    
    Args:
        document_id: Unique document identifier for this trade
        memory_id: AgentCore Memory ID (from environment if not provided)
        
    Returns:
        Configured Swarm instance with memory-enabled agents
    """
    # Create agents with individual session managers
    # Each agent gets a unique session ID but shares the same memory resource
    pdf_adapter = create_pdf_adapter_agent(document_id, memory_id)
    trade_extractor = create_trade_extractor_agent(document_id, memory_id)
    trade_matcher = create_trade_matcher_agent(document_id, memory_id)
    exception_handler = create_exception_handler_agent(document_id, memory_id)
    
    swarm = Swarm(
        [pdf_adapter, trade_extractor, trade_matcher, exception_handler],
        entry_point=pdf_adapter,
        max_handoffs=10,
        max_iterations=20,
        execution_timeout=600.0,  # 10 minutes total
        node_timeout=180.0,       # 3 minutes per agent
        repetitive_handoff_detection_window=6,
        repetitive_handoff_min_unique_agents=2
    )
    
    return swarm


def create_trade_matching_swarm() -> Swarm:
    """
    Create the Trade Matching Swarm without memory integration (backward compatibility).
    
    This function maintains backward compatibility for existing code that doesn't use memory.
    For new deployments with memory, use create_trade_matching_swarm_with_memory() instead.
    
    Returns:
        Configured Swarm instance without memory integration
    """
    # Generate a temporary document ID for backward compatibility
    temp_document_id = f"temp_{uuid.uuid4().hex[:12]}"
    
    # Create swarm with memory disabled (memory_id=None will skip session manager creation)
    return create_trade_matching_swarm_with_memory(
        document_id=temp_document_id,
        memory_id=None
    )


# ============================================================================
# Processing Functions
# ============================================================================

def process_trade_confirmation(
    document_path: str,
    source_type: str,
    document_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    memory_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a trade confirmation through the swarm with optional memory integration.
    
    Args:
        document_path: S3 path to the PDF (s3://bucket/key or just key)
        source_type: BANK or COUNTERPARTY
        document_id: Optional document ID (generated if not provided)
        correlation_id: Optional correlation ID for tracing
        memory_id: Optional AgentCore Memory ID (from environment if not provided)
        
    Returns:
        Swarm execution result with status and details
    """
    if document_id is None:
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
    if correlation_id is None:
        correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
    
    # Parse S3 path
    if document_path.startswith("s3://"):
        parts = document_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]
    else:
        bucket = S3_BUCKET
        key = document_path
    
    # Create the swarm with memory integration
    swarm = create_trade_matching_swarm_with_memory(
        document_id=document_id,
        memory_id=memory_id
    )
    
    # Build the task prompt
    memory_note = " All agents have access to historical patterns stored in memory to improve decision-making." if memory_id or os.environ.get("AGENTCORE_MEMORY_ID") else ""
    
    task = f"""Process this trade confirmation PDF and match it against existing trades.

## Document Details
- Document ID: {document_id}
- S3 Location: s3://{bucket}/{key}
- Source Type: {source_type}
- Correlation ID: {correlation_id}

## Goal
Extract trade data from the PDF, store it in DynamoDB, analyze matches against existing trades, and handle any exceptions that arise.

The swarm will coordinate the work - each agent will decide when to hand off based on their expertise and the task context.{memory_note}
"""
    
    logger.info(f"Starting swarm processing for {document_id}")
    start_time = datetime.utcnow()
    
    try:
        result = swarm(task)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "document_id": document_id,
            "correlation_id": correlation_id,
            "status": str(result.status),
            "node_history": [node.node_id for node in result.node_history],
            "execution_count": result.execution_count,
            "execution_time_ms": result.execution_time,
            "processing_time_ms": processing_time_ms,
            "accumulated_usage": result.accumulated_usage
        }
    except Exception as e:
        logger.error(f"Swarm execution failed: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "success": False,
            "document_id": document_id,
            "correlation_id": correlation_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "processing_time_ms": processing_time_ms
        }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI entrypoint for the Trade Matching Swarm."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Trade Matching Swarm - Process OTC trade confirmations"
    )
    parser.add_argument(
        "document_path",
        help="S3 path to the PDF document (s3://bucket/key or just key)"
    )
    parser.add_argument(
        "--source-type", "-s",
        choices=["BANK", "COUNTERPARTY"],
        required=True,
        help="Source type: BANK or COUNTERPARTY"
    )
    parser.add_argument(
        "--document-id", "-d",
        help="Optional document ID (auto-generated if not provided)"
    )
    parser.add_argument(
        "--correlation-id", "-c",
        help="Optional correlation ID for tracing"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    result = process_trade_confirmation(
        document_path=args.document_path,
        source_type=args.source_type,
        document_id=args.document_id,
        correlation_id=args.correlation_id
    )
    
    print(json.dumps(result, indent=2, default=str))
    
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    exit(main())
