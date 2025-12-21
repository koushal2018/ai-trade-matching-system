"""
Property-based tests for TradeDataValidator component.

These tests validate data validation and normalization functionality
using Hypothesis for comprehensive property testing.
"""

import pytest
from hypothesis import given, strategies as st, assume
from decimal import Decimal
import os
import sys
from datetime import datetime

# Add the deployment directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'deployment', 'trade_extraction'))

from trade_data_validator import TradeDataValidator, ValidationResult


class TestDataValidationProperties:
    """Property-based tests for trade data validation functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.validator = TradeDataValidator()
    
    @given(st.dictionaries(
        keys=st.sampled_from(['trade_id', 'counterparty', 'notional_amount', 'currency', 'trade_date', 'product_type']),
        values=st.one_of(st.text(), st.integers(), st.floats(), st.none()),
        min_size=0,
        max_size=6
    ))
    def test_property_8_data_schema_validation(self, trade_data: dict):
        """
        Property 8: Data Schema Validation
        
        For any input data dictionary, the validator must:
        1. Return a ValidationResult object
        2. Correctly identify missing required fields
        3. Handle invalid data types gracefully
        4. Not crash on any input
        """
        correlation_id = "test_corr_123"
        source_document = "s3://test-bucket/test.pdf"
        
        result = self.validator.validate_and_normalize(trade_data, correlation_id, source_document)
        
        # Must return ValidationResult
        assert isinstance(result, ValidationResult)
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        
        # All error messages must be strings
        for error in result.errors:
            assert isinstance(error, str)
            assert len(error) > 0
        
        # All warning messages must be strings
        for warning in result.warnings:
            assert isinstance(warning, str)
            assert len(warning) > 0
        
        # If valid, normalized_data must be provided
        if result.is_valid:
            assert result.normalized_data is not None
            assert isinstance(result.normalized_data, dict)
            # System fields must be added
            assert result.normalized_data['correlation_id'] == correlation_id
            assert result.normalized_data['source_document'] == source_document
            assert 'extracted_at' in result.normalized_data
    
    @given(st.lists(st.sampled_from([
        'trade_id', 'counterparty', 'notional_amount', 'currency', 'trade_date', 'product_type'
    ]), min_size=0, max_size=6, unique=True))
    def test_property_9_required_field_validation(self, present_fields: list):
        """
        Property 9: Required Field Validation
        
        For any combination of present/missing required fields:
        1. Missing required fields must be detected
        2. Error messages must be descriptive
        3. Validation must fail if any required field is missing
        """
        # Create test data with only the present fields
        trade_data = {}
        for field in present_fields:
            if field == 'trade_id':
                trade_data[field] = 'TEST123'
            elif field == 'counterparty':
                trade_data[field] = 'Test Bank'
            elif field == 'notional_amount':
                trade_data[field] = '1000000'
            elif field == 'currency':
                trade_data[field] = 'USD'
            elif field == 'trade_date':
                trade_data[field] = '2024-01-01'
            elif field == 'product_type':
                trade_data[field] = 'IRS'
        
        result = self.validator.validate_and_normalize(
            trade_data, "test_corr", "s3://test/doc.pdf"
        )
        
        # Required fields (excluding system-added ones)
        required_fields = {'trade_id', 'counterparty', 'notional_amount', 'currency', 'trade_date', 'product_type'}
        missing_fields = required_fields - set(present_fields)
        
        if missing_fields:
            # Should be invalid if required fields are missing
            assert result.is_valid is False
            # Should have error messages for missing fields
            error_text = ' '.join(result.errors).lower()
            for missing_field in missing_fields:
                assert missing_field in error_text or 'missing' in error_text
        else:
            # Should be valid if all required fields are present (with valid values)
            assert result.is_valid is True
            assert result.normalized_data is not None
    
    @given(st.one_of(
        st.just('USD'), st.just('EUR'), st.just('GBP'), st.just('JPY'),
        st.just('usd'), st.just('eur'), st.just('gbp'),
        st.just('DOLLAR'), st.just('EURO'), st.just('POUND'),
        st.just('US DOLLAR'), st.just('EUROS'),
        st.text(min_size=3, max_size=3, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    ))
    def test_property_10_currency_code_normalization(self, currency_input):
        """
        Property 10: Currency Code Normalization
        
        For any currency input, the validator must:
        1. Normalize valid currencies to ISO 4217 codes
        2. Handle case insensitivity
        3. Map common currency names to codes
        4. Accept 3-letter codes even if not in predefined list
        """
        trade_data = {
            'trade_id': 'TEST123',
            'counterparty': 'Test Bank',
            'notional_amount': '1000000',
            'currency': currency_input,
            'trade_date': '2024-01-01',
            'product_type': 'IRS'
        }
        
        result = self.validator.validate_and_normalize(
            trade_data, "test_corr", "s3://test/doc.pdf"
        )
        
        if result.is_valid:
            # Normalized currency should be uppercase
            normalized_currency = result.normalized_data['currency']
            assert isinstance(normalized_currency, str)
            assert normalized_currency.isupper()
            assert len(normalized_currency) == 3
            
            # Known mappings should be normalized correctly
            if currency_input.upper() in ['USD', 'DOLLAR', 'DOLLARS', 'US DOLLAR', 'US DOLLARS']:
                assert normalized_currency == 'USD'
            elif currency_input.upper() in ['EUR', 'EURO', 'EUROS']:
                assert normalized_currency == 'EUR'
            elif currency_input.upper() in ['GBP', 'POUND', 'POUNDS', 'STERLING']:
                assert normalized_currency == 'GBP'
    
    @given(st.one_of(
        st.just('2024-01-01'),
        st.just('01/01/2024'),
        st.just('01-01-2024'),
        st.just('2024/01/01'),
        st.just('January 1, 2024'),
        st.just('1 January 2024'),
        st.text(min_size=1, max_size=20)
    ))
    def test_property_11_date_format_normalization(self, date_input):
        """
        Property 11: Date Format Normalization
        
        For any date input, the validator must:
        1. Parse common date formats correctly
        2. Normalize to ISO 8601 format (YYYY-MM-DD)
        3. Handle invalid dates gracefully
        4. Provide meaningful error messages for unparseable dates
        """
        trade_data = {
            'trade_id': 'TEST123',
            'counterparty': 'Test Bank',
            'notional_amount': '1000000',
            'currency': 'USD',
            'trade_date': date_input,
            'product_type': 'IRS'
        }
        
        result = self.validator.validate_and_normalize(
            trade_data, "test_corr", "s3://test/doc.pdf"
        )
        
        if result.is_valid:
            # Normalized date should be ISO 8601 format
            normalized_date = result.normalized_data['trade_date']
            assert isinstance(normalized_date, str)
            # Should match YYYY-MM-DD pattern
            import re
            assert re.match(r'^\d{4}-\d{2}-\d{2}$', normalized_date)
            
            # Should be a valid date
            datetime.fromisoformat(normalized_date)
        else:
            # If invalid, should have meaningful error about date
            if any('date' in error.lower() for error in result.errors):
                error_text = ' '.join(result.errors).lower()
                assert 'parse' in error_text or 'format' in error_text or 'invalid' in error_text
    
    @given(st.one_of(
        st.integers(min_value=1, max_value=1000000000),
        st.floats(min_value=0.01, max_value=1000000000.0, allow_nan=False, allow_infinity=False),
        st.text(min_size=1, max_size=20),
        st.just('1,000,000'),
        st.just('$1000000'),
        st.just('€500000'),
        st.just('0'),
        st.just('-1000'),
        st.none()
    ))
    def test_property_12_validation_error_handling(self, notional_input):
        """
        Property 12: Validation Error Handling
        
        For any notional amount input, the validator must:
        1. Handle various numeric formats
        2. Reject negative or zero amounts
        3. Parse amounts with currency symbols and formatting
        4. Provide clear error messages for invalid amounts
        """
        trade_data = {
            'trade_id': 'TEST123',
            'counterparty': 'Test Bank',
            'notional_amount': notional_input,
            'currency': 'USD',
            'trade_date': '2024-01-01',
            'product_type': 'IRS'
        }
        
        result = self.validator.validate_and_normalize(
            trade_data, "test_corr", "s3://test/doc.pdf"
        )
        
        if result.is_valid:
            # Valid amounts should be converted to Decimal and be positive
            normalized_amount = result.normalized_data['notional_amount']
            assert isinstance(normalized_amount, Decimal)
            assert normalized_amount > 0
        else:
            # Invalid amounts should have descriptive errors
            if notional_input is None:
                assert any('required' in error.lower() for error in result.errors)
            elif str(notional_input) in ['0', '-1000']:
                assert any('positive' in error.lower() for error in result.errors)
    
    def test_property_validation_consistency(self):
        """
        Property: Validation results must be consistent for identical inputs.
        """
        trade_data = {
            'trade_id': 'TEST123',
            'counterparty': 'Test Bank',
            'notional_amount': '1000000',
            'currency': 'USD',
            'trade_date': '2024-01-01',
            'product_type': 'IRS'
        }
        
        result1 = self.validator.validate_and_normalize(
            trade_data, "test_corr", "s3://test/doc.pdf"
        )
        result2 = self.validator.validate_and_normalize(
            trade_data, "test_corr", "s3://test/doc.pdf"
        )
        
        # Results should be consistent (excluding timestamp fields)
        assert result1.is_valid == result2.is_valid
        assert result1.errors == result2.errors
        assert result1.warnings == result2.warnings
        
        if result1.is_valid and result2.is_valid:
            # Normalized data should be identical except for extracted_at timestamp
            for key, value in result1.normalized_data.items():
                if key != 'extracted_at':
                    assert result2.normalized_data[key] == value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])