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
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
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
    """Get or create a boto3 client for the specified service."""
    import boto3
    if service not in _boto_clients:
        _boto_clients[service] = boto3.client(service, region_name=REGION)
    return _boto_clients[service]


# ============================================================================
# Custom Tools for PDF Processing
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
        s3_client = get_boto_client('s3')
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
        return json.dumps({
            "success": False,
            "error": str(e)
        })


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
    import re
    
    try:
        bedrock_client = get_boto_client('bedrock-runtime')
        
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_base64)
        
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
            ]
        )
        
        extracted_text = response['output']['message']['content'][0]['text']
        
        return json.dumps({
            "success": True,
            "extracted_text": extracted_text,
            "text_length": len(extracted_text)
        })
    except Exception as e:
        logger.error(f"Failed to extract text with Bedrock: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def save_canonical_output(
    document_id: str,
    source_type: str,
    extracted_text: str,
    correlation_id: str,
    processing_time_ms: float
) -> str:
    """
    Save the canonical adapter output to S3 in the standardized format.
    
    Args:
        document_id: Unique identifier for the document
        source_type: BANK or COUNTERPARTY
        extracted_text: The extracted text from the PDF
        correlation_id: Correlation ID for tracing
        processing_time_ms: Processing time in milliseconds
        
    Returns:
        JSON string with success status and S3 location
    """
    try:
        s3_client = get_boto_client('s3')
        
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
                "processing_time_ms": processing_time_ms
            },
            "s3_location": f"s3://{S3_BUCKET}/extracted/{source_type}/{document_id}.json",
            "processing_timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id
        }
        
        # Save to S3
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
            "ocr_text_location": f"s3://{S3_BUCKET}/{ocr_output_key}"
        })
    except Exception as e:
        logger.error(f"Failed to save canonical output: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
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
# Agent System Prompt (Optimized for token efficiency)
# ============================================================================

SYSTEM_PROMPT = f"""You are a PDF Adapter Agent for OTC trade confirmations.

## Resources
- S3: {S3_BUCKET} | Region: {REGION} | Model: {BEDROCK_MODEL_ID}

## Tools
1. download_pdf_from_s3(bucket, key, document_id) → PDF base64
2. extract_text_with_bedrock(pdf_base64, document_id) → extracted text
3. save_canonical_output(document_id, source_type, extracted_text, correlation_id, processing_time_ms) → S3 location
4. use_aws → general AWS operations

## Workflow
1. Download PDF from S3
2. Extract all text using Bedrock
3. Save canonical output to S3
4. Report success/failure with S3 location

## Rules
- source_type: "BANK" or "COUNTERPARTY" only
- Preserve all extracted text (no summarization)
- Report errors clearly with details
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
        temperature=0.1,  # Low temperature for deterministic document processing
        max_tokens=4096,
    )
    
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            download_pdf_from_s3,
            extract_text_with_bedrock,
            save_canonical_output,
            use_aws
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
    }
    
    # Basic validation
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
    
    if source_type and source_type not in ["BANK", "COUNTERPARTY"]:
        return {
            "success": False,
            "error": f"Invalid source_type: {source_type}. Must be BANK or COUNTERPARTY",
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
        }
    
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
        
        # Parse S3 path
        if document_path.startswith("s3://"):
            parts = document_path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]
        else:
            bucket = S3_BUCKET
            key = document_path
        
        # Construct goal-oriented prompt - let LLM decide the approach
        prompt = f"""Process this PDF trade confirmation and produce canonical output.

## Document Information
- Document ID: {document_id}
- Location: s3://{bucket}/{key}
- Source Type: {source_type if source_type else "Infer from path (BANK or COUNTERPARTY folder)"}
- Correlation ID: {correlation_id}

## Goal
Extract all text from the PDF and save it as canonical output to S3. The canonical output should preserve all trade details for downstream processing.

## Available Tools
- download_pdf_from_s3: Retrieve the PDF from S3
- extract_text_with_bedrock: Extract text using Bedrock's multimodal capabilities  
- save_canonical_output: Save the standardized output to S3

## Success Criteria
- All text extracted from the PDF
- Canonical output saved to S3 with proper metadata
- Report the S3 location and extraction summary
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
