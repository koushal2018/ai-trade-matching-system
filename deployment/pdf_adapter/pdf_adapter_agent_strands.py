"""
PDF Adapter Agent - Strands SDK Implementation

This agent uses Strands SDK with built-in tools for AWS operations.
It processes PDF trade confirmations using LLM reasoning to extract text
and produce standardized canonical output - letting the agent decide the best approach.

Requirements: 3.2, 5.1, 5.2, 5.3, 5.4, 5.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
import base64
from datetime import datetime
from typing import Any, Dict, Optional
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_agents_tools import use_aws
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
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_ALIAS = os.getenv("AGENT_ALIAS", "default")
OBSERVABILITY_STAGE = os.getenv("OBSERVABILITY_STAGE", "development")

# Agent identification constants
AGENT_NAME = "pdf-adapter-agent"

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
    """
    Get or create a boto3 client for the specified service.
    
    Uses lazy initialization to avoid creating clients until needed.
    Clients are cached for reuse across tool invocations.
    
    Args:
        service: AWS service name (e.g., 's3', 'bedrock-runtime')
        
    Returns:
        Configured boto3 client for the service
    """
    import boto3
    from botocore.config import Config
    
    if service not in _boto_clients:
        # Configure timeout for Nova models (60 min inference timeout per AWS docs)
        config = Config(
            read_timeout=3600,  # 60 minutes for Nova document processing
            connect_timeout=10,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        _boto_clients[service] = boto3.client(service, region_name=REGION, config=config)
    return _boto_clients[service]


# ============================================================================
# Custom Tools for PDF Processing (Granular, LLM-driven)
# ============================================================================

@tool
def infer_source_type_from_path(document_path: str) -> str:
    """
    Infer the source type (BANK or COUNTERPARTY) from an S3 path.
    
    Analyzes the path structure to determine if this is a bank or counterparty trade.
    
    Args:
        document_path: S3 path (s3://bucket/key or just key)
        
    Returns:
        JSON string with inferred source_type or error
    """
    try:
        if "/BANK/" in document_path or document_path.startswith("BANK/"):
            return json.dumps({"success": True, "source_type": "BANK"})
        elif "/COUNTERPARTY/" in document_path or document_path.startswith("COUNTERPARTY/"):
            return json.dumps({"success": True, "source_type": "COUNTERPARTY"})
        else:
            return json.dumps({
                "success": False,
                "error": f"Cannot determine source_type from path '{document_path}'. Must contain /BANK/ or /COUNTERPARTY/"
            })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def extract_text_from_pdf_s3(
    document_path: str,
    document_id: str
) -> str:
    """
    Download a PDF from S3 and extract all text using Bedrock's multimodal capabilities.
    
    This tool handles the complete text extraction workflow:
    - Downloads PDF from S3
    - Extracts text using Amazon Nova Pro multimodal
    - Returns the complete extracted text
    
    Args:
        document_path: S3 path (s3://bucket/key or just key)
        document_id: Unique identifier for the document
        
    Returns:
        JSON string with extracted text and metadata
    """
    import re
    
    try:
        # Parse S3 path
        if document_path.startswith("s3://"):
            parts = document_path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]
        else:
            bucket = S3_BUCKET
            key = document_path
        
        # Download PDF
        s3_client = get_boto_client('s3')
        local_path = f"/tmp/{document_id}.pdf"
        s3_client.download_file(bucket, key, local_path)
        
        with open(local_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Extract text using Bedrock multimodal
        bedrock_client = get_boto_client('bedrock-runtime')
        
        # Sanitize document name for Bedrock
        sanitized_name = re.sub(r'[^a-zA-Z0-9\-\(\)\[\]\s]', '-', document_id)
        sanitized_name = re.sub(r'\s+', ' ', sanitized_name).strip()
        
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "document": {
                                "format": "pdf",
                                "name": sanitized_name,
                                "source": {
                                    "bytes": pdf_bytes
                                }
                            }
                        },
                        {
                            "text": """Extract ALL text from this trade confirmation PDF document.

Include every piece of text visible in the document, maintaining the structure as much as possible.
Extract all trade details including:
- Trade ID / Reference numbers
- Dates (trade date, effective date, maturity date, etc.)
- Counterparty information
- Notional amounts and currencies
- Product type and commodity details
- Settlement information
- Any other relevant trade terms

Return the complete extracted text."""
                        }
                    ]
                }
            ],
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.2,
                "topP": 0.9
            }
        )
        
        extracted_text = response['output']['message']['content'][0]['text']
        
        return json.dumps({
            "success": True,
            "extracted_text": extracted_text,
            "file_size_bytes": len(pdf_bytes),
            "text_length": len(extracted_text),
            "document_id": document_id
        })
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })


@tool
def save_canonical_output_to_s3(
    document_id: str,
    source_type: str,
    extracted_text: str,
    correlation_id: str,
    file_size_bytes: int
) -> str:
    """
    Save canonical adapter output to S3 in standardized format.
    
    Creates the canonical output structure with metadata and saves to S3.
    Also saves raw extracted text as a separate file.
    
    Args:
        document_id: Unique identifier for the document
        source_type: BANK or COUNTERPARTY
        extracted_text: Complete extracted text from PDF
        correlation_id: Correlation ID for tracing
        file_size_bytes: Original PDF file size
        
    Returns:
        JSON string with S3 locations and success status
    """
    try:
        # Create canonical output structure
        canonical_output = {
            "adapter_type": "PDF",
            "document_id": document_id,
            "source_type": source_type,
            "extracted_text": extracted_text,
            "metadata": {
                "page_count": 1,
                "dpi": 300,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "ocr_model": BEDROCK_MODEL_ID,
                "file_size_bytes": file_size_bytes,
                "text_length": len(extracted_text)
            },
            "s3_location": f"s3://{S3_BUCKET}/extracted/{source_type}/{document_id}.json",
            "processing_timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id
        }
        
        # Save canonical output to S3
        s3_client = get_boto_client('s3')
        canonical_output_key = f"extracted/{source_type}/{document_id}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=canonical_output_key,
            Body=json.dumps(canonical_output, indent=2),
            ContentType='application/json',
            Metadata={
                'document_id': document_id,
                'source_type': source_type,
                'adapter_type': 'PDF',
                'correlation_id': correlation_id
            }
        )
        
        # Also save raw extracted text
        ocr_output_key = f"extracted/{source_type}/{document_id}_ocr.txt"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=ocr_output_key,
            Body=extracted_text.encode('utf-8'),
            ContentType='text/plain'
        )
        
        return json.dumps({
            "success": True,
            "canonical_output_location": canonical_output["s3_location"],
            "ocr_text_location": f"s3://{S3_BUCKET}/{ocr_output_key}",
            "document_id": document_id,
            "source_type": source_type
        })
        
    except Exception as e:
        logger.error(f"Failed to save canonical output: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })





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
# Agent System Prompt (Goal-oriented, not prescriptive)
# ============================================================================

SYSTEM_PROMPT = f"""You are an intelligent PDF Adapter Agent for OTC derivative trade confirmations.

## Your Mission
Transform PDF trade confirmations into standardized canonical output that downstream agents can process.

## Available Resources
- S3 Bucket: {S3_BUCKET}
- AWS Region: {REGION}
- Bedrock Model: {BEDROCK_MODEL_ID}

## Available Tools
1. **infer_source_type_from_path**: Determine if a document is BANK or COUNTERPARTY based on S3 path
2. **extract_text_from_pdf_s3**: Download PDF from S3 and extract all text using Bedrock multimodal
3. **save_canonical_output_to_s3**: Save standardized canonical output with metadata
4. **use_aws**: General AWS operations if needed

## Your Workflow (You Decide the Order)
Think about the task and decide which tools to use and when. Generally you'll want to:
1. Validate or infer the source_type if not provided
2. Extract text from the PDF
3. Save the canonical output to S3

But you have full autonomy to adapt based on the situation.

## Success Criteria
- Extract ALL text from the PDF (no summarization)
- Determine the correct source_type (BANK or COUNTERPARTY)
- Save canonical output to S3 with proper metadata
- Handle errors intelligently

## Key Principles
- **Think First**: Analyze what needs to be done before acting
- **Use Tools Wisely**: Each tool has a specific purpose - use them appropriately
- **Be Complete**: Extract all text - downstream agents need every detail
- **Be Clear**: Explain your reasoning and what you accomplished

You are the LLM - you decide the approach.
"""


# ============================================================================
# Create Strands Agent
# ============================================================================

def create_pdf_adapter_agent() -> Agent:
    """Create and configure the Strands PDF adapter agent with tools."""
    # Explicitly configure BedrockModel for better control
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.3,  # Higher temperature for better reasoning and adaptability
        max_tokens=4096,
    )
    
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            infer_source_type_from_path,
            extract_text_from_pdf_s3,
            save_canonical_output_to_s3,
            use_aws  # Fallback for any additional AWS operations
        ]
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
    AgentCore Runtime entrypoint for PDF Adapter Agent.
    
    Uses Strands SDK with custom tools for PDF processing operations.
    The LLM decides how to orchestrate the tools based on the input.
    
    Args:
        payload: Event payload containing:
            - document_id: Unique identifier for the document
            - document_path: S3 path to the PDF (s3://bucket/key or just key)
            - source_type: "BANK" or "COUNTERPARTY"
            - correlation_id: Optional correlation ID for tracing
        context: AgentCore context (optional)
        
    Returns:
        dict: Processing result with canonical output location
    """
    start_time = datetime.utcnow()
    logger.info("PDF Adapter Agent (Strands) invoked")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    document_id = payload.get("document_id")
    document_path = payload.get("document_path")
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
        "operation": "pdf_processing",  # Standardized operation name
    }
    
    # Minimal validation - let the agent handle edge cases
    if not document_id or not document_path:
        error_response = {
            "success": False,
            "error": "Missing required fields: document_id or document_path",
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
        }
        if observability:
            try:
                with observability.start_span("pdf_processing") as span:
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
                span_context = observability.start_span("pdf_processing")
                span_context.__enter__()
                for k, v in obs_attributes.items():
                    span_context.set_attribute(k, v)
            except Exception as e:
                logger.warning(f"Failed to start observability span: {e}")
                span_context = None
        
        # Create the agent
        agent = create_pdf_adapter_agent()
        
        # Construct goal-oriented prompt - let the agent reason about the approach
        prompt = f"""Process this trade confirmation PDF and create canonical output.

**Document ID**: {document_id}
**S3 Path**: {document_path}
**Source Type**: {source_type if source_type else "Not specified - infer from path"}
**Correlation ID**: {correlation_id}

**Your Goal**: Extract all text from this PDF and save it as canonical output to S3.

**Think through your approach**:
1. Do you need to infer the source_type? (Use infer_source_type_from_path if needed)
2. Extract the text from the PDF (Use extract_text_from_pdf_s3)
3. Save the canonical output (Use save_canonical_output_to_s3)

You decide which tools to use and in what order. Be thorough and handle any issues intelligently.
"""
        
        # Invoke the agent
        logger.info("Invoking Strands agent for PDF processing")
        result = agent(prompt)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract token metrics
        token_metrics = _extract_token_metrics(result)
        logger.info(f"Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Extract the agent's response safely
        if hasattr(result, 'message') and result.message:
            if hasattr(result.message, 'content') and result.message.content:
                # Handle structured content
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
        logger.error(f"Error in PDF adapter agent: {e}", exc_info=True)
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
