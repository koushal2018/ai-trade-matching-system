"""
Trade Data Validator for the Trade Extraction Agent.

This module implements comprehensive validation and normalization
of extracted trade data, ensuring data quality and consistency.
"""

import re
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

# from data_models import CanonicalTradeData  # Import not needed for validator

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of trade data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    normalized_data: Optional[Dict[str, Any]] = None


class TradeDataValidator:
    """
    Validates and normalizes extracted trade data.
    
    This class implements comprehensive validation including required field checking,
    currency code normalization to ISO 4217 standard, and date format conversion
    to ISO 8601.
    """
    
    # ISO 4217 currency codes (major currencies)
    VALID_CURRENCY_CODES = {
        'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
        'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RUB', 'CNY',
        'HKD', 'SGD', 'KRW', 'INR', 'BRL', 'MXN', 'ZAR', 'TRY'
    }
    
    # Common currency code mappings for normalization
    CURRENCY_MAPPINGS = {
        'DOLLAR': 'USD',
        'DOLLARS': 'USD',
        'US DOLLAR': 'USD',
        'US DOLLARS': 'USD',
        'EURO': 'EUR',
        'EUROS': 'EUR',
        'POUND': 'GBP',
        'POUNDS': 'GBP',
        'STERLING': 'GBP',
        'YEN': 'JPY',
        'SWISS FRANC': 'CHF',
        'CANADIAN DOLLAR': 'CAD',
        'AUSTRALIAN DOLLAR': 'AUD'
    }
    
    # Required fields for trade data
    REQUIRED_FIELDS = {
        'trade_id', 'counterparty', 'notional_amount', 'currency',
        'trade_date', 'product_type', 'correlation_id', 'source_document'
    }
    
    def __init__(self):
        """Initialize the TradeDataValidator."""
        logger.info("TradeDataValidator initialized")
    
    def validate_and_normalize(
        self,
        extracted_data: Dict[str, Any],
        correlation_id: str,
        source_document: str
    ) -> ValidationResult:
        """
        Validate and normalize extracted trade data.
        
        Args:
            extracted_data: Raw extracted trade data
            correlation_id: Correlation ID for tracing
            source_document: S3 URI of source document
            
        Returns:
            ValidationResult containing validation status and normalized data
        """
        errors = []
        warnings = []
        normalized_data = extracted_data.copy()
        
        logger.info(f"Starting validation for correlation_id {correlation_id}")
        
        try:
            # 1. Validate required fields
            missing_fields = self._validate_required_fields(extracted_data)
            if missing_fields:
                errors.extend([f"Missing required field: {field}" for field in missing_fields])
            
            # 2. Normalize and validate currency
            if 'currency' in extracted_data:
                currency_result = self._normalize_currency(extracted_data['currency'])
                if currency_result[0]:
                    normalized_data['currency'] = currency_result[1]
                else:
                    errors.append(currency_result[2])
            
            # 3. Validate and normalize notional amount
            if 'notional_amount' in extracted_data:
                amount_result = self._validate_notional_amount(extracted_data['notional_amount'])
                if amount_result[0]:
                    normalized_data['notional_amount'] = amount_result[1]
                else:
                    errors.append(amount_result[2])
            
            # 4. Normalize trade date
            if 'trade_date' in extracted_data:
                date_result = self._normalize_date(extracted_data['trade_date'], 'trade_date')
                if date_result[0]:
                    normalized_data['trade_date'] = date_result[1]
                else:
                    errors.append(date_result[2])
            
            # 5. Normalize maturity date (optional)
            if 'maturity_date' in extracted_data and extracted_data['maturity_date']:
                date_result = self._normalize_date(extracted_data['maturity_date'], 'maturity_date')
                if date_result[0]:
                    normalized_data['maturity_date'] = date_result[1]
                else:
                    warnings.append(f"Invalid maturity_date format: {date_result[2]}")
                    normalized_data['maturity_date'] = None
            
            # 6. Validate trade_id format
            if 'trade_id' in extracted_data:
                if not self._validate_trade_id(extracted_data['trade_id']):
                    warnings.append("trade_id format may not be standard")
            
            # 7. Validate counterparty
            if 'counterparty' in extracted_data:
                counterparty_result = self._validate_counterparty(extracted_data['counterparty'])
                if counterparty_result[0]:
                    normalized_data['counterparty'] = counterparty_result[1]
                else:
                    errors.append(counterparty_result[2])
            
            # 8. Validate product type
            if 'product_type' in extracted_data:
                product_result = self._validate_product_type(extracted_data['product_type'])
                if product_result[0]:
                    normalized_data['product_type'] = product_result[1]
                else:
                    warnings.append(product_result[2])
            
            # 9. Add system fields
            normalized_data['correlation_id'] = correlation_id
            normalized_data['source_document'] = source_document
            normalized_data['extracted_at'] = datetime.now(timezone.utc).isoformat()
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info(f"Validation successful for correlation_id {correlation_id}")
            else:
                logger.error(f"Validation failed for correlation_id {correlation_id}: {errors}")
            
            if warnings:
                logger.warning(f"Validation warnings for correlation_id {correlation_id}: {warnings}")
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                normalized_data=normalized_data if is_valid else None
            )
            
        except Exception as e:
            error_msg = f"Unexpected error during validation: {str(e)}"
            logger.error(f"Validation error for correlation_id {correlation_id}: {error_msg}")
            return ValidationResult(
                is_valid=False,
                errors=[error_msg],
                warnings=warnings
            )
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> List[str]:
        """Validate that all required fields are present."""
        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            if field not in ['correlation_id', 'source_document']:  # These are added by system
                if field not in data or data[field] is None or str(data[field]).strip() == '':
                    missing_fields.append(field)
        return missing_fields
    
    def _normalize_currency(self, currency: Any) -> Tuple[bool, Optional[str], Optional[str]]:
        """Normalize currency code to ISO 4217 standard."""
        if not currency:
            return False, None, "Currency code is required"
        
        currency_str = str(currency).upper().strip()
        
        # Direct match with ISO 4217 codes
        if currency_str in self.VALID_CURRENCY_CODES:
            return True, currency_str, None
        
        # Try mapping from common names
        if currency_str in self.CURRENCY_MAPPINGS:
            return True, self.CURRENCY_MAPPINGS[currency_str], None
        
        # Check if it's a 3-letter code that might be valid but not in our list
        if re.match(r'^[A-Z]{3}$', currency_str):
            return True, currency_str, None
        
        return False, None, f"Invalid currency code: {currency}"
    
    def _validate_notional_amount(self, amount: Any) -> Tuple[bool, Optional[Decimal], Optional[str]]:
        """Validate and convert notional amount to Decimal."""
        if amount is None:
            return False, None, "Notional amount is required"
        
        try:
            # Handle string amounts with currency symbols or commas
            if isinstance(amount, str):
                # Remove common currency symbols and formatting
                cleaned_amount = re.sub(r'[,$€£¥]', '', amount.strip())
                decimal_amount = Decimal(cleaned_amount)
            else:
                decimal_amount = Decimal(str(amount))
            
            if decimal_amount <= 0:
                return False, None, "Notional amount must be positive"
            
            return True, decimal_amount, None
            
        except (InvalidOperation, ValueError) as e:
            return False, None, f"Invalid notional amount format: {amount}"
    
    def _normalize_date(self, date_value: Any, field_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Normalize date to ISO 8601 format."""
        if not date_value:
            return False, None, f"{field_name} is required"
        
        date_str = str(date_value).strip()
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',           # ISO format
            '%Y-%m-%dT%H:%M:%S',  # ISO with time
            '%Y-%m-%dT%H:%M:%SZ', # ISO with time and Z
            '%m/%d/%Y',           # US format
            '%d/%m/%Y',           # European format
            '%m-%d-%Y',           # US with dashes
            '%d-%m-%Y',           # European with dashes
            '%Y/%m/%d',           # ISO with slashes
            '%B %d, %Y',          # Month name format
            '%d %B %Y',           # European month name
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return True, parsed_date.date().isoformat(), None
            except ValueError:
                continue
        
        # Try parsing with dateutil if available
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            return True, parsed_date.date().isoformat(), None
        except (ImportError, ValueError):
            pass
        
        return False, None, f"Unable to parse {field_name}: {date_value}"
    
    def _validate_trade_id(self, trade_id: Any) -> bool:
        """Validate trade ID format."""
        if not trade_id:
            return False
        
        trade_id_str = str(trade_id).strip()
        
        # Basic validation - should be non-empty and reasonable length
        if len(trade_id_str) < 3 or len(trade_id_str) > 50:
            return False
        
        # Should contain alphanumeric characters
        if not re.match(r'^[A-Za-z0-9\-_]+$', trade_id_str):
            return False
        
        return True
    
    def _validate_counterparty(self, counterparty: Any) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate and normalize counterparty name."""
        if not counterparty:
            return False, None, "Counterparty is required"
        
        counterparty_str = str(counterparty).strip()
        
        if len(counterparty_str) < 2:
            return False, None, "Counterparty name too short"
        
        if len(counterparty_str) > 100:
            return False, None, "Counterparty name too long"
        
        # Normalize whitespace
        normalized_counterparty = ' '.join(counterparty_str.split())
        
        return True, normalized_counterparty, None
    
    def _validate_product_type(self, product_type: Any) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate and normalize product type."""
        if not product_type:
            return False, None, "Product type is required"
        
        product_str = str(product_type).strip().upper()
        
        # Common product type normalizations
        product_mappings = {
            'INTEREST RATE SWAP': 'IRS',
            'IR SWAP': 'IRS',
            'SWAP': 'IRS',
            'CREDIT DEFAULT SWAP': 'CDS',
            'FX FORWARD': 'FX_FORWARD',
            'FOREIGN EXCHANGE FORWARD': 'FX_FORWARD',
            'CURRENCY FORWARD': 'FX_FORWARD',
            'FX OPTION': 'FX_OPTION',
            'CURRENCY OPTION': 'FX_OPTION'
        }
        
        if product_str in product_mappings:
            return True, product_mappings[product_str], None
        
        # If not in mappings, return as-is but normalized
        normalized_product = '_'.join(product_str.split())
        return True, normalized_product, None