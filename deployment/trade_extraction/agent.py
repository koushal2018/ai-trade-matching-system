"""
Trade Data Extraction Agent - CDM-Aligned Implementation
Based on FINOS/ISDA Common Domain Model (CDM) for OTC Derivatives

This agent extracts trade attributes following CDM standards to ensure
consistent matching across bank and counterparty systems.

CDM Reference: https://cdm.finos.org/docs/product-model/
"""

import os
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
import re
import boto3
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from decimal import Decimal
import logging

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
BANK_TABLE = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-opus-4-5-20251101-v1:0")
AGENT_NAME = "trade-extraction-agent-cdm"
AGENT_VERSION = "2.0.0"


# =============================================================================
# Custom JSON Encoder for DynamoDB/Decimal types
# =============================================================================
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


# =============================================================================
# CDM-Aligned Field Schema
# =============================================================================
CDM_TRADE_SCHEMA = {
    "core_identification": {
        "trade_id": "Unique trade identifier (partition key)",
        "internal_reference": "Internal reference/document ID (sort key)",
        "usi": "Unique Swap Identifier (if available)",
        "uti": "Unique Transaction Identifier (if available)",
        "product_qualifier": "ISDA Product Taxonomy (e.g., InterestRate_IRSwap_FixedFloat)"
    },
    "product_classification": {
        "asset_class": "Primary asset class (INTEREST_RATE, CREDIT, EQUITY, FX, COMMODITY)",
        "product_type": "Product type (SWAP, OPTION, FORWARD, CAP, FLOOR, SWAPTION)",
        "sub_product_type": "Sub-product (FIXED_FLOAT, BASIS, XCCY, etc.)"
    },
    "economic_terms": {
        "effective_date": "Trade effective/start date (YYYY-MM-DD)",
        "termination_date": "Maturity/end date (YYYY-MM-DD)",
        "trade_date": "Execution date (YYYY-MM-DD)",
        "settlement_date": "Settlement date (YYYY-MM-DD)"
    },
    "quantity_price": {
        "notional_amount": "Notional/principal amount (number)",
        "currency": "Notional currency (ISO 4217 code)",
        "notional_amount_2": "Second notional for cross-currency (number)",
        "currency_2": "Second currency for cross-currency (ISO 4217 code)"
    },
    "counterparty_info": {
        "party_a_name": "Party A / Bank name",
        "party_a_lei": "Party A Legal Entity Identifier",
        "party_b_name": "Party B / Counterparty name",
        "party_b_lei": "Party B Legal Entity Identifier",
        "executing_broker": "Executing broker (if applicable)"
    },
    "interest_rate_terms": {
        "fixed_rate": "Fixed rate (decimal, e.g., 0.025 for 2.5%)",
        "fixed_rate_payer": "Who pays fixed (PARTY_A or PARTY_B)",
        "floating_rate_index": "Floating rate index (SOFR, EURIBOR, LIBOR, etc.)",
        "floating_rate_spread": "Spread over index (decimal)",
        "floating_rate_payer": "Who pays floating (PARTY_A or PARTY_B)",
        "day_count_fraction": "Day count convention (ACT/360, 30/360, ACT/365, ACT/ACT)",
        "day_count_fraction_2": "Day count for leg 2 (if different)",
        "payment_frequency": "Payment frequency (MONTHLY, QUARTERLY, SEMI_ANNUAL, ANNUAL)",
        "payment_frequency_2": "Payment frequency for leg 2 (if different)",
        "business_day_convention": "Business day convention (FOLLOWING, MODIFIED_FOLLOWING, PRECEDING)",
        "reset_frequency": "Reset frequency for floating leg",
        "compounding_method": "Compounding method (NONE, FLAT, STRAIGHT)"
    },
    "fx_terms": {
        "fx_rate": "FX rate (for cross-currency)",
        "fx_rate_source": "FX rate source (e.g., WMR, ECB)",
        "settlement_currency": "Settlement currency"
    },
    "credit_terms": {
        "reference_entity": "Reference entity for CDS",
        "reference_obligation": "Reference obligation",
        "credit_spread": "Credit spread (bps)"
    },
    "option_terms": {
        "option_type": "Option type (CALL, PUT)",
        "option_style": "Exercise style (EUROPEAN, AMERICAN, BERMUDAN)",
        "strike_price": "Strike price",
        "premium_amount": "Premium amount",
        "premium_currency": "Premium currency",
        "expiry_date": "Option expiry date"
    },
    "settlement_terms": {
        "settlement_type": "Settlement type (CASH, PHYSICAL)",
        "delivery_method": "Delivery method (DVP, PVP, FREE)"
    },
    "metadata": {
        "TRADE_SOURCE": "Source system (BANK or COUNTERPARTY)",
        "document_type": "Document type (CONFIRMATION, TERM_SHEET, etc.)",
        "extraction_timestamp": "When data was extracted (ISO 8601)",
        "extraction_confidence": "Extraction confidence score (0-100)"
    }
}


# =============================================================================
# Tools
# =============================================================================

@tool
def get_s3_document(bucket: str, key: str) -> str:
    """
    Retrieve document content from S3.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        JSON string with document content or error
    """
    try:
        s3_client = boto3.client('s3', region_name=REGION)
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        
        # Try to decode as text
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            text_content = content.decode('utf-8', errors='ignore')
        
        logger.info(f"Retrieved document from s3://{bucket}/{key}, size: {len(content)} bytes")
        
        return json.dumps({
            "success": True,
            "content": text_content,
            "content_type": response.get('ContentType', 'unknown'),
            "size_bytes": len(content)
        })
    except Exception as e:
        logger.error(f"Failed to retrieve S3 document: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def get_cdm_extraction_schema() -> str:
    """
    Get the CDM-aligned field extraction schema.
    
    Returns the complete list of fields to extract from trade documents,
    organized by category according to ISDA/FINOS CDM standards.
    
    Returns:
        JSON string with field schema and descriptions
    """
    return json.dumps({
        "schema": CDM_TRADE_SCHEMA,
        "instructions": {
            "required_fields": [
                "trade_id",
                "internal_reference", 
                "TRADE_SOURCE",
                "effective_date",
                "termination_date",
                "notional_amount",
                "currency"
            ],
            "critical_for_matching": [
                "currency",
                "notional_amount",
                "effective_date",
                "termination_date",
                "trade_date",
                "product_type",
                "fixed_rate",
                "floating_rate_index",
                "day_count_fraction",
                "payment_frequency",
                "party_b_name",
                "party_b_lei"
            ],
            "date_format": "YYYY-MM-DD",
            "rate_format": "Decimal (0.025 for 2.5%)",
            "amount_format": "Number without commas"
        }
    }, indent=2)


@tool
def store_trade_data(trade_data: dict, source_type: str) -> str:
    """
    Store extracted trade data in DynamoDB.
    
    Args:
        trade_data: Dictionary of extracted trade fields
        source_type: Either 'BANK' or 'COUNTERPARTY'
        
    Returns:
        JSON string with storage result
    """
    try:
        # Select target table
        table_name = BANK_TABLE if source_type.upper() == 'BANK' else COUNTERPARTY_TABLE
        
        # Validate required keys
        if 'trade_id' not in trade_data:
            return json.dumps({"success": False, "error": "Missing required field: trade_id"})
        if 'internal_reference' not in trade_data:
            return json.dumps({"success": False, "error": "Missing required field: internal_reference"})
        
        # Convert to DynamoDB format
        dynamodb_item = {}
        for key, value in trade_data.items():
            if value is None or value == '':
                continue
            elif isinstance(value, (int, float, Decimal)):
                dynamodb_item[key] = {'N': str(value)}
            elif isinstance(value, bool):
                dynamodb_item[key] = {'BOOL': value}
            else:
                dynamodb_item[key] = {'S': str(value)}
        
        # Ensure TRADE_SOURCE is set
        dynamodb_item['TRADE_SOURCE'] = {'S': source_type.upper()}
        
        # Add extraction metadata
        dynamodb_item['extraction_timestamp'] = {'S': datetime.now(timezone.utc).isoformat()}
        dynamodb_item['extraction_agent_version'] = {'S': AGENT_VERSION}
        
        # Store in DynamoDB
        dynamodb_client = boto3.client('dynamodb', region_name=REGION)
        response = dynamodb_client.put_item(
            TableName=table_name,
            Item=dynamodb_item
        )
        
        logger.info(f"Stored trade {trade_data.get('trade_id')} in {table_name}")
        
        return json.dumps({
            "success": True,
            "table": table_name,
            "trade_id": trade_data.get('trade_id'),
            "fields_stored": len(dynamodb_item),
            "http_status": response.get('ResponseMetadata', {}).get('HTTPStatusCode')
        }, cls=DecimalEncoder)
        
    except Exception as e:
        logger.error(f"Failed to store trade data: {e}")
        return json.dumps({"success": False, "error": str(e)})


@tool
def validate_cdm_extraction(trade_data: dict) -> str:
    """
    Validate extracted data against CDM requirements.
    
    Args:
        trade_data: Dictionary of extracted trade fields
        
    Returns:
        JSON string with validation results and quality score
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "field_coverage": {},
        "quality_score": 0
    }
    
    # Required fields check
    required_fields = ["trade_id", "internal_reference", "TRADE_SOURCE", 
                       "effective_date", "termination_date", "notional_amount", "currency"]
    
    for field in required_fields:
        if field not in trade_data or not trade_data[field]:
            results["valid"] = False
            results["errors"].append(f"Missing required field: {field}")
    
    # Critical matching fields check
    critical_fields = ["currency", "notional_amount", "effective_date", "termination_date",
                       "trade_date", "product_type", "party_b_name"]
    
    critical_present = 0
    for field in critical_fields:
        if field in trade_data and trade_data[field]:
            critical_present += 1
        else:
            results["warnings"].append(f"Missing critical matching field: {field}")
    
    results["field_coverage"]["critical"] = f"{critical_present}/{len(critical_fields)}"
    
    # Interest rate specific fields
    ir_fields = ["fixed_rate", "floating_rate_index", "day_count_fraction", "payment_frequency"]
    ir_present = sum(1 for f in ir_fields if f in trade_data and trade_data[f])
    results["field_coverage"]["interest_rate"] = f"{ir_present}/{len(ir_fields)}"
    
    # Counterparty fields
    cpty_fields = ["party_a_name", "party_b_name", "party_a_lei", "party_b_lei"]
    cpty_present = sum(1 for f in cpty_fields if f in trade_data and trade_data[f])
    results["field_coverage"]["counterparty"] = f"{cpty_present}/{len(cpty_fields)}"
    
    # Date format validation
    date_fields = ["effective_date", "termination_date", "trade_date", "settlement_date"]
    for field in date_fields:
        if field in trade_data and trade_data[field]:
            # Check if it looks like a valid date
            value = str(trade_data[field])
            if not re.match(r'\d{4}-\d{2}-\d{2}', value):
                results["warnings"].append(f"Date field {field} may not be in YYYY-MM-DD format: {value}")
    
    # Calculate quality score
    total_fields = len(trade_data)
    critical_score = (critical_present / len(critical_fields)) * 50
    coverage_score = min(total_fields / 20, 1) * 30  # Cap at 20 fields for full score
    error_penalty = len(results["errors"]) * 10
    
    results["quality_score"] = max(0, min(100, critical_score + coverage_score + 20 - error_penalty))
    
    return json.dumps(results, indent=2)


# =============================================================================
# CDM-Aligned System Prompt
# =============================================================================

SYSTEM_PROMPT = f"""##Role##
You are an expert Trade Data Extraction Agent trained on the FINOS/ISDA Common Domain Model (CDM) for OTC derivatives. Your expertise covers interest rate swaps, cross-currency swaps, FX forwards, credit default swaps, commodity derivatives, and equity derivatives.

##Mission##
Extract comprehensive trade attributes from financial documents following CDM standards to enable accurate downstream trade matching. The quality of matching depends entirely on the completeness and accuracy of your extraction.

##CDM Field Categories##

1. **Core Identification**
   - trade_id: Unique trade identifier (REQUIRED - use as partition key)
   - internal_reference: Document reference (REQUIRED - use as sort key)
   - usi/uti: Unique Swap/Transaction Identifier
   - product_qualifier: ISDA taxonomy (e.g., InterestRate_IRSwap_FixedFloat)

2. **Product Classification**
   - asset_class: INTEREST_RATE, CREDIT, EQUITY, FX, COMMODITY
   - product_type: SWAP, OPTION, FORWARD, CAP, FLOOR, SWAPTION
   - sub_product_type: FIXED_FLOAT, BASIS, XCCY, etc.

3. **Economic Terms (CRITICAL FOR MATCHING)**
   - effective_date: Start date (YYYY-MM-DD format)
   - termination_date: Maturity date (YYYY-MM-DD format)
   - trade_date: Execution date (YYYY-MM-DD format)
   - settlement_date: Settlement date (YYYY-MM-DD format)

4. **Quantity & Price (CRITICAL FOR MATCHING)**
   - notional_amount: Principal amount (NUMBER, no commas)
   - currency: ISO 4217 code (USD, EUR, GBP, AED, etc.)
   - notional_amount_2: For cross-currency
   - currency_2: Second currency for cross-currency

5. **Counterparty Information (CRITICAL FOR MATCHING)**
   - party_a_name: Bank/Party A name
   - party_a_lei: 20-character Legal Entity Identifier
   - party_b_name: Counterparty name
   - party_b_lei: Counterparty LEI

6. **Interest Rate Terms (CRITICAL FOR IR PRODUCTS)**
   - fixed_rate: As decimal (0.025 = 2.5%)
   - fixed_rate_payer: PARTY_A or PARTY_B
   - floating_rate_index: SOFR, EURIBOR, LIBOR, ESTR, SONIA, etc.
   - floating_rate_spread: Spread in decimal
   - floating_rate_payer: PARTY_A or PARTY_B
   - day_count_fraction: ACT/360, 30/360, ACT/365, ACT/ACT
   - payment_frequency: MONTHLY, QUARTERLY, SEMI_ANNUAL, ANNUAL
   - business_day_convention: FOLLOWING, MODIFIED_FOLLOWING, PRECEDING
   - reset_frequency: DAILY, MONTHLY, QUARTERLY
   - compounding_method: NONE, FLAT, STRAIGHT

7. **FX Terms (For FX/XCCY products)**
   - fx_rate: Exchange rate
   - fx_rate_source: WMR, ECB, etc.
   - settlement_currency

8. **Credit Terms (For CDS)**
   - reference_entity
   - credit_spread (in basis points)

9. **Option Terms (For options/swaptions)**
   - option_type: CALL, PUT
   - option_style: EUROPEAN, AMERICAN, BERMUDAN
   - strike_price
   - premium_amount/currency
   - expiry_date

10. **Settlement Terms**
    - settlement_type: CASH, PHYSICAL
    - delivery_method: DVP, PVP, FREE

##Environment##
- Region: {REGION}
- Bank trades table: {BANK_TABLE}
- Counterparty trades table: {COUNTERPARTY_TABLE}

##Workflow##
1. Call get_cdm_extraction_schema() to review the complete field schema
2. Call get_s3_document() to retrieve the trade document
3. Extract ALL fields you can identify, following CDM naming conventions
4. Call validate_cdm_extraction() to check extraction quality
5. Call store_trade_data() to persist to DynamoDB

##Critical Requirements##
- Extract EVERY field present in the document - completeness is essential
- Use EXACT CDM field names (lowercase with underscores)
- Dates MUST be YYYY-MM-DD format
- Rates MUST be decimals (2.5% = 0.025)
- Amounts MUST be numbers without commas
- Identify the correct product_type based on document content
- Pay special attention to day_count_fraction and payment_frequency - these are critical for matching

##TRADE_SOURCE Routing##
- BANK → {BANK_TABLE}
- COUNTERPARTY → {COUNTERPARTY_TABLE}

##Output##
After extraction and storage, provide a summary:
{{
    "extraction_status": "SUCCESS" or "PARTIAL" or "FAILED",
    "trade_id": "extracted trade ID",
    "product_type": "identified product type",
    "fields_extracted": <count>,
    "quality_score": <0-100>,
    "missing_critical_fields": ["list of missing critical fields"],
    "dynamodb_result": "storage confirmation"
}}
"""


# =============================================================================
# Agent Factory
# =============================================================================

def create_extraction_agent() -> Agent:
    """Create the CDM-aligned extraction agent."""
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0,
        max_tokens=8192,
    )
    
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_s3_document,
            get_cdm_extraction_schema,
            store_trade_data,
            validate_cdm_extraction
        ]
    )


# =============================================================================
# AgentCore Runtime Handlers
# =============================================================================

@app.ping
def health_check() -> PingStatus:
    """Health check for AgentCore Runtime."""
    return PingStatus.HEALTHY


def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """AgentCore Runtime entrypoint."""
    start_time = datetime.now(timezone.utc)
    
    document_id = payload.get("document_id")
    canonical_output_location = payload.get("canonical_output_location")
    source_type = payload.get("source_type", "BANK")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    logger.info(f"[{correlation_id}] Starting CDM extraction for document: {document_id}")
    
    if not document_id or not canonical_output_location:
        return {
            "success": False,
            "error": "Missing required fields: document_id or canonical_output_location",
            "correlation_id": correlation_id
        }
    
    try:
        # Parse S3 location
        s3_path = canonical_output_location.replace("s3://", "")
        bucket = s3_path.split("/")[0]
        key = "/".join(s3_path.split("/")[1:])
        
        # Create agent
        agent = create_extraction_agent()
        
        # Build prompt
        prompt = f"""Extract trade data from document using CDM standards.

Document ID: {document_id}
S3 Location: s3://{bucket}/{key}
Source Type: {source_type}
Correlation ID: {correlation_id}

Use internal_reference = "{document_id}" as the sort key.

Follow the workflow:
1. Get the CDM schema
2. Retrieve the document from S3
3. Extract all CDM-aligned fields
4. Validate the extraction
5. Store in DynamoDB

Focus on extracting ALL matching-critical fields:
- Currency, Notional, Dates (effective, termination, trade)
- Product type, Fixed rate, Floating index
- Day count fraction, Payment frequency
- Counterparty name and LEI
"""
        
        # Invoke agent
        result = agent(prompt)
        
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # Extract response
        if hasattr(result, 'message') and result.message:
            if hasattr(result.message, 'content') and result.message.content:
                content = result.message.content
                if isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', str(content[0])) if isinstance(content[0], dict) else str(content[0])
                else:
                    response_text = str(content)
            else:
                response_text = str(result.message)
        else:
            response_text = str(result)
        
        logger.info(f"[{correlation_id}] CDM extraction completed in {processing_time_ms:.0f}ms")
        
        return {
            "success": True,
            "document_id": document_id,
            "source_type": source_type,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.error(f"[{correlation_id}] CDM extraction failed: {e}", exc_info=True)
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "document_id": document_id,
            "correlation_id": correlation_id,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


app.entrypoint(invoke)


def main():
    """CLI entry point."""
    print(f"🚀 Starting CDM-Aligned Trade Extraction Agent v{AGENT_VERSION}")
    app.run()


if __name__ == "__main__":
    main()
