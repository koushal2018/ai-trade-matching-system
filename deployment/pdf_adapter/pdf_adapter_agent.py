"""
PDF Adapter Agent - AgentCore Runtime Entry Point (Standalone)

This is a self-contained entry point for the PDF Adapter Agent deployed to AgentCore Runtime.
It processes PDF trade confirmations and produces standardized canonical output.

Requirements: 3.2, 5.1, 5.2, 5.3, 5.4, 5.5
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Literal
import logging
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

# REQUIRED: Import BedrockAgentCoreApp
from bedrock_agentcore import BedrockAgentCoreApp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# REQUIRED: Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# ============================================================================
# Constants
# ============================================================================

BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
EXTRACTION_QUEUE_NAME = "trade-matching-system-extraction-events-production"
EXCEPTION_QUEUE_NAME = "trade-matching-system-exception-events-production"
DEFAULT_DPI = 300


# ============================================================================
# Data Models (inline to avoid external dependencies)
# ============================================================================

class CanonicalAdapterOutput(BaseModel):
    """Canonical output schema for all adapter agents."""
    adapter_type: Literal["PDF", "CHAT", "EMAIL", "VOICE"]
    document_id: str
    source_type: Literal["BANK", "COUNTERPARTY"]
    extracted_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    s3_location: str
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str = ""


# ============================================================================
# PDF Processing Functions
# ============================================================================

def extract_text_from_pdf(
    s3_client,
    bedrock_client,
    pdf_path: str,
    s3_bucket: str,
    document_id: str
) -> str:
    """
    Extract text from a PDF using Bedrock's multimodal capabilities.
    
    Downloads the PDF from S3 and uses Claude to extract all text content
    from the trade confirmation document.
    
    Args:
        s3_client: Boto3 S3 client
        bedrock_client: Boto3 Bedrock Runtime client
        pdf_path: S3 path to the PDF (s3://bucket/key or just key)
        s3_bucket: Default S3 bucket name
        document_id: Unique document identifier
        
    Returns:
        str: Extracted text from the PDF
        
    Raises:
        ClientError: If S3 or Bedrock operations fail
    """
    logger.info(f"Processing PDF: {pdf_path}")
    
    # Parse S3 path
    if pdf_path.startswith("s3://"):
        parts = pdf_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]
    else:
        bucket = s3_bucket
        key = pdf_path
    
    # Download PDF from S3
    local_pdf_path = f"/tmp/{document_id}.pdf"
    s3_client.download_file(bucket, key, local_pdf_path)
    logger.info(f"Downloaded PDF to {local_pdf_path}")
    
    # Read PDF bytes
    with open(local_pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    # Use Bedrock Claude to extract text from PDF
    logger.info("Extracting text using Bedrock Claude...")
    
    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "document": {
                            "format": "pdf",
                            "name": f"{document_id}.pdf",
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
    logger.info(f"Extracted {len(extracted_text)} characters of text")
    
    return extracted_text


def _validate_payload(payload: Dict[str, Any]) -> tuple:
    """
    Validate the incoming payload and extract required fields.
    
    Args:
        payload: Event payload dictionary
        
    Returns:
        tuple: (document_id, document_path, source_type, correlation_id)
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    document_id = payload.get("document_id")
    document_path = payload.get("document_path")
    source_type = payload.get("source_type")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    if not document_id or not document_path or not source_type:
        raise ValueError("Missing required fields: document_id, document_path, or source_type")
    
    if source_type not in ["BANK", "COUNTERPARTY"]:
        raise ValueError(f"Invalid source_type: {source_type}. Must be BANK or COUNTERPARTY")
    
    return document_id, document_path, source_type, correlation_id


def _publish_success_event(
    sqs_client,
    document_id: str,
    canonical_output_location: str,
    correlation_id: str,
    source_type: str,
    processing_time_ms: float
) -> None:
    """
    Publish PDF_PROCESSED event to the extraction-events queue.
    
    Args:
        sqs_client: Boto3 SQS client
        document_id: Document identifier
        canonical_output_location: S3 location of canonical output
        correlation_id: Correlation ID for tracing
        source_type: BANK or COUNTERPARTY
        processing_time_ms: Processing time in milliseconds
    """
    try:
        queue_url = sqs_client.get_queue_url(QueueName=EXTRACTION_QUEUE_NAME)['QueueUrl']
        
        event_message = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "PDF_PROCESSED",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": "pdf_adapter_agent",
            "correlation_id": correlation_id,
            "payload": {
                "document_id": document_id,
                "canonical_output_location": canonical_output_location,
                "page_count": 1,
                "processing_time_ms": processing_time_ms
            },
            "metadata": {
                "dpi": DEFAULT_DPI,
                "source_type": source_type,
                "adapter_type": "PDF"
            }
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event_message, default=str)
        )
        logger.info("Published PDF_PROCESSED event to extraction-events queue")
    except ClientError as e:
        logger.warning(f"Could not publish to SQS (queue may not exist): {e}")


def _publish_exception_event(
    sqs_client,
    document_id: str,
    document_path: str,
    source_type: str,
    correlation_id: str,
    error: Exception
) -> None:
    """
    Publish EXCEPTION_RAISED event to the exception-events queue.
    
    Args:
        sqs_client: Boto3 SQS client
        document_id: Document identifier
        document_path: Original document path
        source_type: BANK or COUNTERPARTY
        correlation_id: Correlation ID for tracing
        error: The exception that occurred
    """
    try:
        queue_url = sqs_client.get_queue_url(QueueName=EXCEPTION_QUEUE_NAME)['QueueUrl']
        
        exception_event = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "EXCEPTION_RAISED",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": "pdf_adapter_agent",
            "correlation_id": correlation_id,
            "payload": {
                "exception_id": f"exc_{uuid.uuid4().hex[:12]}",
                "exception_type": "PDF_PROCESSING_ERROR",
                "trade_id": document_id or "unknown",
                "error_message": str(error),
                "reason_codes": ["PDF_PROCESSING_ERROR"]
            },
            "metadata": {
                "document_path": document_path or "unknown",
                "source_type": source_type or "unknown"
            }
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(exception_event, default=str)
        )
        logger.info("Published EXCEPTION_RAISED event to exception-events queue")
    except ClientError as e:
        logger.warning(f"Could not publish exception to SQS: {e}")


# ============================================================================
# Main Agent Logic
# ============================================================================

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for PDF Adapter Agent.
    
    This function is called by AgentCore Runtime when the agent is invoked.
    
    Args:
        payload: Event payload containing:
            - document_id: Unique identifier for the document
            - document_path: S3 path to the PDF
            - source_type: "BANK" or "COUNTERPARTY"
        context: AgentCore context (optional)
        
    Returns:
        dict: Processing result with canonical output location
        
    Validates: Requirements 2.1, 2.2, 3.2, 5.1, 5.2, 5.3, 5.4, 5.5
    """
    start_time = datetime.utcnow()
    logger.info("PDF Adapter Agent invoked via AgentCore Runtime")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    # Get configuration from environment
    region_name = os.getenv("AWS_REGION", "us-east-1")
    s3_bucket = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
    
    # Initialize AWS clients
    s3_client = boto3.client('s3', region_name=region_name)
    bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
    sqs_client = boto3.client('sqs', region_name=region_name)
    
    # Initialize variables for error handling scope
    document_id = None
    document_path = None
    source_type = None
    correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
    
    try:
        # Validate and extract payload fields
        document_id, document_path, source_type, correlation_id = _validate_payload(payload)
        
        logger.info(f"Processing document: {document_id} from {source_type}")
        
        # Step 1: Extract text from PDF using Bedrock
        logger.info("Step 1: Extracting text from PDF using Bedrock Claude")
        extracted_text = extract_text_from_pdf(
            s3_client=s3_client,
            bedrock_client=bedrock_client,
            pdf_path=document_path,
            s3_bucket=s3_bucket,
            document_id=document_id
        )
        
        # Step 2: Save extracted text to S3
        logger.info("Step 2: Saving extracted text to S3")
        ocr_output_key = f"extracted/{source_type}/{document_id}_ocr.txt"
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=ocr_output_key,
            Body=extracted_text.encode('utf-8'),
            ContentType='text/plain'
        )
        
        # Step 3: Create canonical output
        logger.info("Step 3: Creating canonical output")
        canonical_output = CanonicalAdapterOutput(
            adapter_type="PDF",
            document_id=document_id,
            source_type=source_type,
            extracted_text=extracted_text,
            metadata={
                "page_count": 1,  # Simplified - treating as single extraction
                "dpi": DEFAULT_DPI,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "ocr_model": BEDROCK_MODEL_ID
            },
            s3_location=f"s3://{s3_bucket}/extracted/{source_type}/{document_id}.json",
            processing_timestamp=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        # Step 4: Save canonical output to S3
        canonical_output_key = f"extracted/{source_type}/{document_id}.json"
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=canonical_output_key,
            Body=canonical_output.model_dump_json(indent=2),
            ContentType='application/json',
            Metadata={
                'document_id': document_id,
                'source_type': source_type,
                'adapter_type': 'PDF',
                'correlation_id': correlation_id
            }
        )
        
        logger.info(f"Canonical output saved to S3: {canonical_output.s3_location}")
        
        # Step 5: Publish PDF_PROCESSED event to extraction-events queue
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        _publish_success_event(
            sqs_client=sqs_client,
            document_id=document_id,
            canonical_output_location=canonical_output.s3_location,
            correlation_id=correlation_id,
            source_type=source_type,
            processing_time_ms=processing_time_ms
        )
        
        result = {
            "success": True,
            "document_id": document_id,
            "canonical_output_location": canonical_output.s3_location,
            "processing_time_ms": processing_time_ms,
            "extracted_text_length": len(extracted_text)
        }
        
        logger.info(f"Processing result: {json.dumps(result, default=str)}")
        return result
        
    except ValueError as e:
        # Validation errors - don't retry
        logger.error(f"Validation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "document_id": document_id or "unknown"
        }
        
    except ClientError as e:
        # AWS service errors
        logger.error(f"AWS service error: {e}", exc_info=True)
        _publish_exception_event(
            sqs_client=sqs_client,
            document_id=document_id,
            document_path=document_path,
            source_type=source_type,
            correlation_id=correlation_id,
            error=e
        )
        return {
            "success": False,
            "error": str(e),
            "document_id": document_id or "unknown"
        }
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error processing document: {e}", exc_info=True)
        _publish_exception_event(
            sqs_client=sqs_client,
            document_id=document_id,
            document_path=document_path,
            source_type=source_type,
            correlation_id=correlation_id,
            error=e
        )
        return {
            "success": False,
            "error": str(e),
            "document_id": document_id or "unknown"
        }


if __name__ == "__main__":
    """
    REQUIRED: Let AgentCore Runtime control the agent execution.
    """
    app.run()
