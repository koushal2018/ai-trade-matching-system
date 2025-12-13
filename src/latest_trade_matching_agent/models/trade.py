"""
Canonical Trade Model

This module defines the standardized trade data model with mandatory and
optional attributes. All trade data extracted from various sources must
conform to this canonical model.

Requirements: 6.1, 6.2, 6.3, 6.4
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class CanonicalTradeModel(BaseModel):
    """
    Canonical trade data model with mandatory and optional fields.
    
    This model represents the standardized structure for all trade data
    regardless of source. It supports 30+ trade fields covering various
    derivative product types.
    
    Mandatory Fields:
        Trade_ID: Unique trade identifier
        TRADE_SOURCE: Classification (BANK or COUNTERPARTY)
        trade_date: Date the trade was executed
        notional: Trade notional amount
        currency: Currency of the notional
        counterparty: Name of the counterparty
        product_type: Type of derivative product
    
    Optional Fields:
        30+ additional fields for comprehensive trade representation
    
    Requirements:
        - 6.1: Extract all trade fields
        - 6.2: Classify trade source
        - 6.3: Save JSON to S3
        - 6.4: Store in appropriate DynamoDB table
    """
    
    # ========== MANDATORY FIELDS ==========
    
    Trade_ID: str = Field(
        ...,
        description="Unique trade identifier",
        min_length=1
    )
    
    TRADE_SOURCE: str = Field(
        ...,
        description="Classification of the trade source"
    )
    
    trade_date: str = Field(
        ...,
        description="Date the trade was executed (YYYY-MM-DD format)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    
    notional: float = Field(
        ...,
        description="Trade notional amount",
        gt=0
    )
    
    currency: str = Field(
        ...,
        description="Currency of the notional (ISO 4217 code)",
        min_length=3,
        max_length=3
    )
    
    counterparty: str = Field(
        ...,
        description="Name of the counterparty",
        min_length=1
    )
    
    product_type: str = Field(
        ...,
        description="Type of derivative product (e.g., SWAP, OPTION, FORWARD)",
        min_length=1
    )
    
    # ========== OPTIONAL FIELDS ==========
    
    effective_date: Optional[str] = Field(
        None,
        description="Effective date of the trade (YYYY-MM-DD format)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    
    maturity_date: Optional[str] = Field(
        None,
        description="Maturity date of the trade (YYYY-MM-DD format)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    
    commodity_type: Optional[str] = Field(
        None,
        description="Type of commodity (for commodity derivatives)"
    )
    
    strike_price: Optional[float] = Field(
        None,
        description="Strike price (for options)",
        gt=0
    )
    
    settlement_type: Optional[str] = Field(
        None,
        description="Settlement type (CASH, PHYSICAL)"
    )
    
    payment_frequency: Optional[str] = Field(
        None,
        description="Payment frequency (MONTHLY, QUARTERLY, ANNUALLY)"
    )
    
    fixed_rate: Optional[float] = Field(
        None,
        description="Fixed rate (for swaps)"
    )
    
    floating_rate_index: Optional[str] = Field(
        None,
        description="Floating rate index (e.g., LIBOR, SOFR)"
    )
    
    day_count_convention: Optional[str] = Field(
        None,
        description="Day count convention (e.g., ACT/360, 30/360)"
    )
    
    business_day_convention: Optional[str] = Field(
        None,
        description="Business day convention (FOLLOWING, MODIFIED_FOLLOWING)"
    )
    
    option_type: Optional[str] = Field(
        None,
        description="Option type (CALL, PUT)"
    )
    
    option_style: Optional[str] = Field(
        None,
        description="Option style (EUROPEAN, AMERICAN, ASIAN)"
    )
    
    exercise_date: Optional[str] = Field(
        None,
        description="Exercise date for options (YYYY-MM-DD format)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    
    delivery_point: Optional[str] = Field(
        None,
        description="Delivery point (for physical settlement)"
    )
    
    quantity: Optional[float] = Field(
        None,
        description="Quantity (for commodity trades)",
        gt=0
    )
    
    unit_of_measure: Optional[str] = Field(
        None,
        description="Unit of measure (BBL, MT, MWh)"
    )
    
    price_per_unit: Optional[float] = Field(
        None,
        description="Price per unit",
        gt=0
    )
    
    premium: Optional[float] = Field(
        None,
        description="Premium amount (for options)",
        ge=0
    )
    
    premium_currency: Optional[str] = Field(
        None,
        description="Currency of the premium (ISO 4217 code)",
        min_length=3,
        max_length=3
    )
    
    broker: Optional[str] = Field(
        None,
        description="Broker name"
    )
    
    trader_name: Optional[str] = Field(
        None,
        description="Name of the trader"
    )
    
    trader_email: Optional[str] = Field(
        None,
        description="Email of the trader"
    )
    
    confirmation_method: Optional[str] = Field(
        None,
        description="Method of confirmation (EMAIL, PLATFORM, PHONE)"
    )
    
    clearing_house: Optional[str] = Field(
        None,
        description="Clearing house name"
    )
    
    collateral_required: Optional[bool] = Field(
        None,
        description="Whether collateral is required"
    )
    
    collateral_amount: Optional[float] = Field(
        None,
        description="Amount of collateral",
        ge=0
    )
    
    collateral_currency: Optional[str] = Field(
        None,
        description="Currency of collateral (ISO 4217 code)",
        min_length=3,
        max_length=3
    )
    
    netting_agreement: Optional[str] = Field(
        None,
        description="Netting agreement reference"
    )
    
    master_agreement: Optional[str] = Field(
        None,
        description="Master agreement type (ISDA, EFET)"
    )
    
    credit_support_annex: Optional[str] = Field(
        None,
        description="Credit Support Annex reference"
    )
    
    # ========== METADATA FIELDS ==========
    
    s3_source: Optional[str] = Field(
        None,
        description="S3 URI of the source document"
    )
    
    processing_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this trade was processed"
    )
    
    extraction_confidence: Optional[float] = Field(
        None,
        description="Confidence score of the extraction (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    @field_validator("currency", "premium_currency", "collateral_currency")
    @classmethod
    def validate_currency_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency codes are uppercase."""
        if v is not None:
            return v.upper()
        return v
    
    @field_validator("TRADE_SOURCE")
    @classmethod
    def validate_trade_source(cls, v: str) -> str:
        """Ensure TRADE_SOURCE is uppercase and valid."""
        normalized = v.upper()
        if normalized not in ["BANK", "COUNTERPARTY"]:
            raise ValueError(f"TRADE_SOURCE must be 'BANK' or 'COUNTERPARTY', got '{v}'")
        return normalized
    
    def to_dynamodb_format(self) -> Dict[str, Any]:
        """
        Convert the trade model to DynamoDB typed format.
        
        DynamoDB requires type markers for all attributes:
        - S: String
        - N: Number (stored as string)
        - BOOL: Boolean
        - NULL: Null value
        
        Returns:
            Dictionary with DynamoDB type markers
        
        Example:
            {
                "Trade_ID": {"S": "GCS382857"},
                "notional": {"N": "1000000.00"},
                "collateral_required": {"BOOL": True}
            }
        """
        dynamodb_item = {}
        
        for field_name, field_value in self.model_dump(exclude_none=True).items():
            if field_value is None:
                continue
            
            # Handle different types
            if isinstance(field_value, bool):
                dynamodb_item[field_name] = {"BOOL": field_value}
            elif isinstance(field_value, (int, float)):
                # DynamoDB stores numbers as strings
                dynamodb_item[field_name] = {"N": str(field_value)}
            elif isinstance(field_value, datetime):
                # Convert datetime to ISO format string
                dynamodb_item[field_name] = {"S": field_value.isoformat()}
            elif isinstance(field_value, str):
                dynamodb_item[field_name] = {"S": field_value}
            else:
                # Fallback to string representation
                dynamodb_item[field_name] = {"S": str(field_value)}
        
        return dynamodb_item
    
    @classmethod
    def from_dynamodb_format(cls, dynamodb_item: Dict[str, Any]) -> "CanonicalTradeModel":
        """
        Create a CanonicalTradeModel from DynamoDB typed format.
        
        Args:
            dynamodb_item: Dictionary with DynamoDB type markers
        
        Returns:
            CanonicalTradeModel instance
        """
        python_dict = {}
        
        for field_name, typed_value in dynamodb_item.items():
            if "S" in typed_value:
                python_dict[field_name] = typed_value["S"]
            elif "N" in typed_value:
                # Try to convert to float, fallback to string
                try:
                    python_dict[field_name] = float(typed_value["N"])
                except ValueError:
                    python_dict[field_name] = typed_value["N"]
            elif "BOOL" in typed_value:
                python_dict[field_name] = typed_value["BOOL"]
            elif "NULL" in typed_value:
                python_dict[field_name] = None
        
        return cls(**python_dict)
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "Trade_ID": "GCS382857",
                    "TRADE_SOURCE": "COUNTERPARTY",
                    "trade_date": "2024-10-15",
                    "notional": 1000000.00,
                    "currency": "USD",
                    "counterparty": "Goldman Sachs",
                    "product_type": "SWAP",
                    "effective_date": "2024-10-17",
                    "maturity_date": "2025-10-17",
                    "commodity_type": "CRUDE_OIL",
                    "settlement_type": "CASH",
                    "payment_frequency": "MONTHLY",
                    "fixed_rate": 3.5,
                    "floating_rate_index": "BRENT",
                    "s3_source": "s3://bucket/COUNTERPARTY/GCS382857.pdf",
                    "extraction_confidence": 0.92
                }
            ]
        }
