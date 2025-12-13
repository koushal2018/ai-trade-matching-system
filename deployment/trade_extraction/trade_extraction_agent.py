"""
Trade Data Extraction Agent - AgentCore Runtime Entry Point (Standalone)

This is a self-contained entry point for the Trade Data Extraction Agent deployed to AgentCore Runtime.
It extracts structured trade data from canonical adapter output and stores it in DynamoDB.

Requirements: 2.1, 2.2, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional, List
import logging
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

# REQUIRED: Import BedrockAgentCoreApp
from bedrock_agentcore import BedrockAgentCoreApp

# Memory integration (optional - graceful fallback if not available)
try:
    import sys
    sys.path.insert(0, '/opt/agent/src')
    from latest_trade_matching_agent.memory import store_trade_pattern, retrieve_similar_trades
    MEMORY_ENABLED = True
except ImportError:
    MEMORY_ENABLED = False
    async def store_trade_pattern(*args, **kwargs):
        return {}
    async def retrieve_similar_trades(*args, **kwargs):
        return []

# Observability integration
try:
    from latest_trade_matching_agent.observability import create_span, record_latency, record_throughput, record_error
    OBSERVABILITY_ENABLED = True
except ImportError:
    OBSERVABILITY_ENABLED = False
    from contextlib import contextmanager
    @contextmanager
    def create_span(*args, **kwargs):
        yield None
    def record_latency(*args, **kwargs): pass
    def record_throughput(*args, **kwargs): pass
    def record_error(*args, **kwargs): pass

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

BEDROCK_MODEL_ID = "amazon.nova-pro-v1:0"
MATCHING_QUEUE_NAME = "trade-matching-system-matching-events-production"
EXCEPTION_QUEUE_NAME = "trade-matching-system-exception-events-production"


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


class CanonicalTradeModel(BaseModel):
    """Canonical trade model with mandatory and optional fields."""
    # Mandatory fields
    Trade_ID: str
    TRADE_SOURCE: Literal["BANK", "COUNTERPARTY"]
    trade_date: str
    notional: float
    currency: str
    counterparty: str
    product_type: str
    
    # Optional fields
    effective_date: Optional[str] = None
    maturity_date: Optional[str] = None
    commodity_type: Optional[str] = None
    strike_price: Optional[float] = None
    settlement_type: Optional[str] = None
    payment_frequency: Optional[str] = None
    day_count_convention: Optional[str] = None
    business_day_convention: Optional[str] = None
    fixed_rate: Optional[float] = None
    floating_rate_index: Optional[str] = None
    spread: Optional[float] = None
    notional_currency: Optional[str] = None
    settlement_currency: Optional[str] = None
    delivery_point: Optional[str] = None
    quantity: Optional[float] = None
    quantity_unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    total_value: Optional[float] = None
    buyer: Optional[str] = None
    seller: Optional[str] = None
    broker: Optional[str] = None
    clearing_house: Optional[str] = None
    uti: Optional[str] = None
    usi: Optional[str] = None
    lei: Optional[str] = None
    
    def to_dynamodb_format(self) -> Dict[str, Any]:
        """Convert to DynamoDB typed format."""
        item = {}
        for field_name, value in self.model_dump(exclude_none=True).items():
            if value is None:
                continue
            if isinstance(value, str):
                item[field_name] = {"S": value}
            elif isinstance(value, (int, float)):
                item[field_name] = {"N": str(value)}
            elif isinstance(value, bool):
                item[field_name] = {"BOOL": value}
            elif isinstance(value, list):
                item[field_name] = {"L": [{"S": str(v)} for v in value]}
            elif isinstance(value, dict):
                item[field_name] = {"M": {k: {"S": str(v)} for k, v in value.items()}}
        
        # Add trade_id and internal_reference as primary keys (DynamoDB schema)
        if "Trade_ID" in item:
            item["trade_id"] = item["Trade_ID"]
            # Use Trade_ID as internal_reference if not present
            if "internal_reference" not in item:
                item["internal_reference"] = item["Trade_ID"]
        
        return item


# ============================================================================
# LLM Extraction Functions
# ============================================================================

def extract_trade_fields_with_llm(
    bedrock_client,
    extracted_text: str,
    source_type: str,
    document_id: str
) -> Dict[str, Any]:
    """
    Extract trade fields from text using Bedrock Claude.
    
    Args:
        bedrock_client: Boto3 Bedrock Runtime client
        extracted_text: OCR extracted text from trade confirmation
        source_type: BANK or COUNTERPARTY
        document_id: Document identifier
        
    Returns:
        dict: Extraction result with canonical_trade and confidence
    """
    logger.info(f"Extracting trade fields using LLM for document: {document_id}")
    
    extraction_prompt = f"""Extract all trade information from the following trade confirmation text.
Return a JSON object with the following fields (use null for missing fields):

Required fields:
- Trade_ID: The unique trade identifier/reference number
- trade_date: The trade date in YYYY-MM-DD format
- notional: The notional amount as a number
- currency: The currency code (e.g., USD, EUR, GBP)
- counterparty: The counterparty name
- product_type: The type of derivative (e.g., SWAP, OPTION, FORWARD)

Optional fields (include if present):
- effective_date: Start date of the trade
- maturity_date: End date of the trade
- commodity_type: Type of commodity if applicable
- strike_price: Strike price for options
- settlement_type: Physical or Cash
- payment_frequency: Payment frequency (e.g., Monthly, Quarterly)
- fixed_rate: Fixed rate if applicable
- floating_rate_index: Floating rate index (e.g., LIBOR, SOFR)
- spread: Spread over floating rate
- quantity: Quantity for commodity trades
- quantity_unit: Unit of quantity (e.g., BBL, MT)
- price_per_unit: Price per unit
- buyer: Buyer name
- seller: Seller name
- broker: Broker name if applicable
- clearing_house: Clearing house if applicable
- uti: Unique Transaction Identifier
- lei: Legal Entity Identifier

Trade Confirmation Text:
{extracted_text}

Return ONLY a valid JSON object with the extracted fields. Do not include any explanation or markdown formatting."""

    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": extraction_prompt}]
            }
        ]
    )
    
    response_text = response['output']['message']['content'][0]['text']
    
    # Parse JSON response
    try:
        # Clean up response if it has markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        extracted_data = json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"LLM returned invalid JSON: {response_text[:200]}")
    
    # Add TRADE_SOURCE from canonical output
    extracted_data["TRADE_SOURCE"] = source_type
    
    # Validate and create canonical trade model
    canonical_trade = CanonicalTradeModel(**extracted_data)
    
    # Calculate extraction confidence based on filled fields
    total_fields = len(CanonicalTradeModel.model_fields)
    filled_fields = len([v for v in canonical_trade.model_dump(exclude_none=True).values() if v is not None])
    extraction_confidence = filled_fields / total_fields
    
    logger.info(f"Extracted {filled_fields}/{total_fields} fields (confidence: {extraction_confidence:.2f})")
    
    return {
        "success": True,
        "canonical_trade": canonical_trade,
        "extraction_confidence": extraction_confidence
    }


# ============================================================================
# Event Publishing Functions
# ============================================================================

def _publish_success_event(
    sqs_client,
    trade_id: str,
    source_type: str,
    table_name: str,
    correlation_id: str,
    processing_time_ms: float,
    extraction_confidence: float
) -> None:
    """Publish TRADE_EXTRACTED event to the matching-events queue."""
    try:
        queue_url = sqs_client.get_queue_url(QueueName=MATCHING_QUEUE_NAME)['QueueUrl']
        
        event_message = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "TRADE_EXTRACTED",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": "trade_extraction_agent",
            "correlation_id": correlation_id,
            "payload": {
                "trade_id": trade_id,
                "source_type": source_type,
                "table_name": table_name,
                "processing_time_ms": processing_time_ms
            },
            "metadata": {
                "extraction_confidence": extraction_confidence
            }
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event_message, default=str)
        )
        logger.info("Published TRADE_EXTRACTED event to matching-events queue")
    except ClientError as e:
        logger.warning(f"Could not publish to SQS (queue may not exist): {e}")


def _publish_exception_event(
    sqs_client,
    document_id: str,
    canonical_output_location: str,
    correlation_id: str,
    error: Exception
) -> None:
    """Publish EXCEPTION_RAISED event to the exception-events queue."""
    try:
        queue_url = sqs_client.get_queue_url(QueueName=EXCEPTION_QUEUE_NAME)['QueueUrl']
        
        exception_event = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": "EXCEPTION_RAISED",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": "trade_extraction_agent",
            "correlation_id": correlation_id,
            "payload": {
                "exception_id": f"exc_{uuid.uuid4().hex[:12]}",
                "exception_type": "EXTRACTION_FAILED",
                "trade_id": document_id or "unknown",
                "error_message": str(error),
                "reason_codes": ["EXTRACTION_FAILED"]
            },
            "metadata": {
                "canonical_output_location": canonical_output_location or "unknown"
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
    AgentCore Runtime entrypoint for Trade Data Extraction Agent.
    
    Args:
        payload: Event payload containing:
            - document_id: Unique identifier for the document
            - canonical_output_location: S3 path to canonical adapter output
        context: AgentCore context (optional)
        
    Returns:
        dict: Extraction result with trade_id and table_name
        
    Validates: Requirements 2.1, 2.2, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5
    """
    start_time = datetime.utcnow()
    logger.info("Trade Data Extraction Agent invoked via AgentCore Runtime")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    # Get configuration from environment
    region_name = os.getenv("AWS_REGION", "us-east-1")
    s3_bucket = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
    bank_table = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
    counterparty_table = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
    
    # Initialize AWS clients
    s3_client = boto3.client('s3', region_name=region_name)
    bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
    dynamodb_client = boto3.client('dynamodb', region_name=region_name)
    sqs_client = boto3.client('sqs', region_name=region_name)
    
    # Initialize variables for error handling scope
    document_id = None
    canonical_output_location = None
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    try:
        # Extract payload fields
        document_id = payload.get("document_id")
        canonical_output_location = payload.get("canonical_output_location")
        
        if not document_id or not canonical_output_location:
            raise ValueError("Missing required fields: document_id or canonical_output_location")
        
        logger.info(f"Processing document: {document_id}")
        
        # Step 1: Read canonical adapter output from S3
        logger.info(f"Step 1: Reading canonical output from S3: {canonical_output_location}")
        
        # Parse S3 URI
        if canonical_output_location.startswith("s3://"):
            s3_uri_parts = canonical_output_location[5:].split("/", 1)
            bucket = s3_uri_parts[0]
            key = s3_uri_parts[1]
        else:
            bucket = s3_bucket
            key = canonical_output_location
        
        # Read from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        canonical_output_json = response['Body'].read().decode('utf-8')
        canonical_output_data = json.loads(canonical_output_json)
        
        # Validate canonical output
        canonical_output = CanonicalAdapterOutput(**canonical_output_data)
        logger.info(f"Canonical output loaded: adapter_type={canonical_output.adapter_type}")
        
        # Step 2: Extract trade data using LLM
        logger.info("Step 2: Extracting trade fields using LLM")
        
        extraction_result = extract_trade_fields_with_llm(
            bedrock_client=bedrock_client,
            extracted_text=canonical_output.extracted_text,
            source_type=canonical_output.source_type,
            document_id=document_id
        )
        
        canonical_trade = extraction_result["canonical_trade"]
        extraction_confidence = extraction_result["extraction_confidence"]
        
        logger.info(f"Trade extracted: {canonical_trade.Trade_ID} (confidence: {extraction_confidence})")
        
        # Step 3: Determine target DynamoDB table
        if canonical_trade.TRADE_SOURCE == "BANK":
            table_name = bank_table
        else:
            table_name = counterparty_table
        
        logger.info(f"Step 3: Storing trade in DynamoDB table: {table_name}")
        
        # Step 4: Store in DynamoDB
        dynamodb_item = canonical_trade.to_dynamodb_format()
        
        dynamodb_client.put_item(
            TableName=table_name,
            Item=dynamodb_item
        )
        
        logger.info(f"Trade stored successfully: {canonical_trade.Trade_ID}")
        
        # Step 5: Publish TRADE_EXTRACTED event
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        _publish_success_event(
            sqs_client=sqs_client,
            trade_id=canonical_trade.Trade_ID,
            source_type=canonical_trade.TRADE_SOURCE,
            table_name=table_name,
            correlation_id=correlation_id,
            processing_time_ms=processing_time_ms,
            extraction_confidence=extraction_confidence
        )
        
        result = {
            "success": True,
            "trade_id": canonical_trade.Trade_ID,
            "source_type": canonical_trade.TRADE_SOURCE,
            "table_name": table_name,
            "extraction_confidence": extraction_confidence,
            "processing_time_ms": processing_time_ms
        }
        
        logger.info(f"Extraction result: {json.dumps(result, default=str)}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "document_id": document_id or "unknown"
        }
        
    except ClientError as e:
        logger.error(f"AWS service error: {e}", exc_info=True)
        _publish_exception_event(
            sqs_client=sqs_client,
            document_id=document_id,
            canonical_output_location=canonical_output_location,
            correlation_id=correlation_id,
            error=e
        )
        return {
            "success": False,
            "error": str(e),
            "document_id": document_id or "unknown"
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        _publish_exception_event(
            sqs_client=sqs_client,
            document_id=document_id,
            canonical_output_location=canonical_output_location,
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
