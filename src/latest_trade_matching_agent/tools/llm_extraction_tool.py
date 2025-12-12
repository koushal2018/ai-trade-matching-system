"""
LLM Extraction Tool

This tool uses AWS Bedrock Claude Sonnet 4 to extract structured trade data
from unstructured text. It validates extracted data against the canonical
trade model and handles optional fields gracefully.

Requirements: 6.1, 6.2
"""

import json
import logging
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

from ..models.trade import CanonicalTradeModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMExtractionTool:
    """
    Tool for extracting structured trade data from unstructured text using LLM.
    
    This tool:
    1. Takes unstructured text as input
    2. Uses AWS Bedrock Claude Sonnet 4 to extract trade fields
    3. Validates extracted data against CanonicalTradeModel
    4. Handles optional fields gracefully
    5. Returns structured trade data or error information
    
    Validates: Requirements 6.1, 6.2
    """
    
    def __init__(
        self,
        model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name: str = "us-east-1",
        max_tokens: int = 4096,
        temperature: float = 0.0  # Use 0 for deterministic extraction
    ):
        """
        Initialize LLM Extraction Tool.
        
        Args:
            model_id: AWS Bedrock model ID
            region_name: AWS region
            max_tokens: Maximum tokens for response
            temperature: Temperature for LLM (0.0 for deterministic)
        """
        self.model_id = model_id
        self.region_name = region_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=region_name
        )
        
        logger.info(f"LLM Extraction Tool initialized with model: {model_id}")
    
    def _build_extraction_prompt(self, extracted_text: str, source_type: str) -> str:
        """
        Build the extraction prompt for the LLM.
        
        Args:
            extracted_text: Unstructured text from OCR or other source
            source_type: BANK or COUNTERPARTY
        
        Returns:
            str: Formatted prompt for LLM
        """
        prompt = f"""You are a trade data extraction specialist. Extract structured trade information from the following text.

SOURCE TYPE: {source_type}

TEXT TO ANALYZE:
{extracted_text}

EXTRACTION INSTRUCTIONS:
1. Extract ALL available trade fields from the text
2. Return ONLY valid JSON (no markdown, no explanations)
3. Use null for missing optional fields
4. Ensure all mandatory fields are present
5. Follow the exact field names specified below

MANDATORY FIELDS (must be present):
- Trade_ID: Unique trade identifier (string)
- trade_date: Trade execution date in YYYY-MM-DD format
- notional: Trade notional amount (number)
- currency: Currency code (3-letter ISO code, e.g., USD, EUR)
- counterparty: Counterparty name (string)
- product_type: Derivative product type (e.g., SWAP, OPTION, FORWARD)

OPTIONAL FIELDS (include if available):
- effective_date: Effective date (YYYY-MM-DD)
- maturity_date: Maturity date (YYYY-MM-DD)
- commodity_type: Commodity type (e.g., CRUDE_OIL, NATURAL_GAS)
- strike_price: Strike price for options (number)
- settlement_type: Settlement type (CASH or PHYSICAL)
- payment_frequency: Payment frequency (MONTHLY, QUARTERLY, ANNUALLY)
- fixed_rate: Fixed rate for swaps (number)
- floating_rate_index: Floating rate index (e.g., LIBOR, SOFR)
- day_count_convention: Day count convention (e.g., ACT/360, 30/360)
- business_day_convention: Business day convention (FOLLOWING, MODIFIED_FOLLOWING)
- option_type: Option type (CALL or PUT)
- option_style: Option style (EUROPEAN, AMERICAN, ASIAN)
- exercise_date: Exercise date for options (YYYY-MM-DD)
- delivery_point: Delivery point for physical settlement
- quantity: Quantity for commodity trades (number)
- unit_of_measure: Unit of measure (BBL, MT, MWh)
- price_per_unit: Price per unit (number)
- premium: Premium amount for options (number)
- premium_currency: Currency of premium (3-letter ISO code)
- broker: Broker name
- trader_name: Trader name
- trader_email: Trader email
- confirmation_method: Confirmation method (EMAIL, PLATFORM, PHONE)
- clearing_house: Clearing house name
- collateral_required: Whether collateral is required (boolean)
- collateral_amount: Collateral amount (number)
- collateral_currency: Collateral currency (3-letter ISO code)
- netting_agreement: Netting agreement reference
- master_agreement: Master agreement type (ISDA, EFET)
- credit_support_annex: Credit Support Annex reference

IMPORTANT NOTES:
- Trade_ID might be labeled as "Trade ID", "Confirmation Number", "Deal Number", "Reference", etc.
- Dates must be in YYYY-MM-DD format (convert if necessary)
- Currency codes must be 3-letter uppercase (e.g., USD, not $)
- Numbers should be numeric values without currency symbols or commas
- For boolean fields, use true or false (lowercase)
- If a field is not found in the text, use null

Return ONLY the JSON object with extracted fields. Do not include any explanations or markdown formatting.
"""
        return prompt
    
    def extract_trade_fields(
        self,
        extracted_text: str,
        source_type: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract trade fields from unstructured text using LLM.
        
        Args:
            extracted_text: Unstructured text from OCR or other source
            source_type: BANK or COUNTERPARTY
            document_id: Optional document ID for tracking
        
        Returns:
            dict: Extracted trade data or error information
            
        Validates: Requirements 6.1, 6.2
        """
        try:
            logger.info(f"Extracting trade fields from text (source: {source_type})")
            
            # Build extraction prompt
            prompt = self._build_extraction_prompt(extracted_text, source_type)
            
            # Prepare request body for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Invoke Bedrock model
            logger.info(f"Invoking Bedrock model: {self.model_id}")
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text from response
            if 'content' in response_body and len(response_body['content']) > 0:
                extracted_json_text = response_body['content'][0]['text']
            else:
                raise ValueError("No content in Bedrock response")
            
            logger.info("LLM extraction completed successfully")
            
            # Parse JSON from LLM response
            # Remove markdown code blocks if present
            extracted_json_text = extracted_json_text.strip()
            if extracted_json_text.startswith("```json"):
                extracted_json_text = extracted_json_text[7:]
            if extracted_json_text.startswith("```"):
                extracted_json_text = extracted_json_text[3:]
            if extracted_json_text.endswith("```"):
                extracted_json_text = extracted_json_text[:-3]
            extracted_json_text = extracted_json_text.strip()
            
            try:
                trade_data = json.loads(extracted_json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"LLM response: {extracted_json_text[:500]}")
                return {
                    "success": False,
                    "error": f"Failed to parse LLM response as JSON: {e}",
                    "raw_response": extracted_json_text[:500]
                }
            
            # Add TRADE_SOURCE field
            trade_data["TRADE_SOURCE"] = source_type
            
            # Add document_id if provided
            if document_id:
                trade_data["s3_source"] = f"document:{document_id}"
            
            # Validate against canonical trade model
            try:
                canonical_trade = CanonicalTradeModel(**trade_data)
                logger.info(f"Trade data validated successfully: {canonical_trade.Trade_ID}")
                
                return {
                    "success": True,
                    "trade_data": canonical_trade.model_dump(),
                    "canonical_trade": canonical_trade,
                    "extraction_confidence": self._compute_confidence(trade_data)
                }
            except Exception as validation_error:
                logger.error(f"Trade data validation failed: {validation_error}")
                return {
                    "success": False,
                    "error": f"Validation failed: {validation_error}",
                    "raw_trade_data": trade_data,
                    "missing_fields": self._identify_missing_fields(trade_data)
                }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock API error: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"Bedrock API error: {error_code}",
                "error_message": error_message
            }
        
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _compute_confidence(self, trade_data: Dict[str, Any]) -> float:
        """
        Compute extraction confidence based on field completeness.
        
        Args:
            trade_data: Extracted trade data
        
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        # Count mandatory fields present
        mandatory_fields = [
            "Trade_ID", "TRADE_SOURCE", "trade_date", "notional",
            "currency", "counterparty", "product_type"
        ]
        
        mandatory_present = sum(
            1 for field in mandatory_fields
            if field in trade_data and trade_data[field] is not None
        )
        
        # Count optional fields present
        optional_fields = [
            "effective_date", "maturity_date", "commodity_type", "strike_price",
            "settlement_type", "payment_frequency", "fixed_rate", "floating_rate_index",
            "day_count_convention", "business_day_convention", "option_type",
            "option_style", "exercise_date", "delivery_point", "quantity",
            "unit_of_measure", "price_per_unit", "premium", "premium_currency",
            "broker", "trader_name", "trader_email", "confirmation_method",
            "clearing_house", "collateral_required", "collateral_amount",
            "collateral_currency", "netting_agreement", "master_agreement",
            "credit_support_annex"
        ]
        
        optional_present = sum(
            1 for field in optional_fields
            if field in trade_data and trade_data[field] is not None
        )
        
        # Confidence = 70% mandatory + 30% optional
        mandatory_score = (mandatory_present / len(mandatory_fields)) * 0.7
        optional_score = (optional_present / len(optional_fields)) * 0.3
        
        confidence = mandatory_score + optional_score
        return round(confidence, 2)
    
    def _identify_missing_fields(self, trade_data: Dict[str, Any]) -> list:
        """
        Identify missing mandatory fields.
        
        Args:
            trade_data: Extracted trade data
        
        Returns:
            list: List of missing mandatory field names
        """
        mandatory_fields = [
            "Trade_ID", "trade_date", "notional",
            "currency", "counterparty", "product_type"
        ]
        
        missing = [
            field for field in mandatory_fields
            if field not in trade_data or trade_data[field] is None
        ]
        
        return missing
    
    def _run(
        self,
        extracted_text: str,
        source_type: str,
        document_id: Optional[str] = None
    ) -> str:
        """
        Run the tool (CrewAI-compatible interface).
        
        Args:
            extracted_text: Unstructured text from OCR or other source
            source_type: BANK or COUNTERPARTY
            document_id: Optional document ID for tracking
        
        Returns:
            str: JSON string with extraction result
        """
        result = self.extract_trade_fields(extracted_text, source_type, document_id)
        return json.dumps(result, indent=2, default=str)


# Convenience function for direct usage
def extract_trade_data(
    extracted_text: str,
    source_type: str,
    document_id: Optional[str] = None,
    model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name: str = "us-east-1"
) -> Dict[str, Any]:
    """
    Extract trade data from unstructured text.
    
    Args:
        extracted_text: Unstructured text from OCR or other source
        source_type: BANK or COUNTERPARTY
        document_id: Optional document ID for tracking
        model_id: AWS Bedrock model ID
        region_name: AWS region
    
    Returns:
        dict: Extraction result
    """
    tool = LLMExtractionTool(model_id=model_id, region_name=region_name)
    return tool.extract_trade_fields(extracted_text, source_type, document_id)
