"""
Property-based tests for TableRouter component.

These tests validate the table routing correctness and source type validation
using Hypothesis for comprehensive property testing.
"""

import pytest
from hypothesis import given, strategies as st, assume
import os
import sys
import logging

# Set up logging for property tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the deployment directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'deployment', 'trade_extraction'))

from table_router import TableRouter


class TestTableRoutingProperties:
    """Property-based tests for table routing functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Set test environment variables
        os.environ['DYNAMODB_BANK_TABLE'] = 'TestBankTradeData'
        os.environ['DYNAMODB_COUNTERPARTY_TABLE'] = 'TestCounterpartyTradeData'
        self.router = TableRouter()
    
    @given(st.text())
    def test_property_1_table_routing_correctness(self, source_type: str):
        """
        Property 1: Table Routing Correctness
        
        For any valid source_type, the router must:
        1. Return success=True
        2. Return the correct table name
        3. Return no error message
        
        For invalid source_types, the router must:
        1. Return success=False
        2. Return None for table name
        3. Return a descriptive error message
        """
        success, table_name, error_message = self.router.get_target_table(source_type)
        
        # Normalize for comparison
        normalized_source_type = source_type.upper().strip() if source_type else ""
        
        if normalized_source_type in {'BANK', 'COUNTERPARTY'}:
            # Valid source types should succeed
            assert success is True, f"Expected success for valid source_type '{source_type}'"
            assert table_name is not None, f"Expected table_name for valid source_type '{source_type}'"
            assert error_message is None, f"Expected no error for valid source_type '{source_type}'"
            
            # Verify correct table mapping
            if normalized_source_type == 'BANK':
                assert table_name == 'TestBankTradeData'
            elif normalized_source_type == 'COUNTERPARTY':
                assert table_name == 'TestCounterpartyTradeData'
        else:
            # Invalid source types should fail
            assert success is False, f"Expected failure for invalid source_type '{source_type}'"
            assert table_name is None, f"Expected no table_name for invalid source_type '{source_type}'"
            assert error_message is not None, f"Expected error message for invalid source_type '{source_type}'"
            assert len(error_message) > 0, "Error message should not be empty"
    
    @given(st.one_of(
        st.just('BANK'),
        st.just('COUNTERPARTY'),
        st.just('bank'),
        st.just('counterparty'),
        st.just(' BANK '),
        st.just(' COUNTERPARTY ')
    ))
    def test_property_1_valid_source_types_always_succeed(self, source_type: str):
        """
        Property 1 Extension: Valid source types (with variations) always succeed.
        
        Tests case insensitivity and whitespace handling.
        """
        success, table_name, error_message = self.router.get_target_table(source_type)
        
        assert success is True
        assert table_name is not None
        assert error_message is None
        
        # Verify correct mapping regardless of case/whitespace
        normalized = source_type.upper().strip()
        if normalized == 'BANK':
            assert table_name == 'TestBankTradeData'
        elif normalized == 'COUNTERPARTY':
            assert table_name == 'TestCounterpartyTradeData'
    
    @given(st.text().filter(lambda x: x.upper().strip() not in {'BANK', 'COUNTERPARTY'}))
    def test_property_2_source_type_validation(self, invalid_source_type: str):
        """
        Property 2: Source Type Validation
        
        For any invalid source_type, validation must:
        1. Return is_valid=False
        2. Return non-empty error messages list
        3. Error messages must be descriptive strings
        """
        is_valid, error_messages = self.router.validate_source_type(invalid_source_type)
        
        assert is_valid is False, f"Expected validation failure for '{invalid_source_type}'"
        assert isinstance(error_messages, list), "Error messages must be a list"
        assert len(error_messages) > 0, "Must have at least one error message"
        
        # All error messages must be non-empty strings
        for error_msg in error_messages:
            assert isinstance(error_msg, str), "Error messages must be strings"
            assert len(error_msg) > 0, "Error messages must not be empty"
    
    @given(st.one_of(
        st.just('BANK'),
        st.just('COUNTERPARTY'),
        st.just('bank'),
        st.just('counterparty'),
        st.just(' BANK '),
        st.just(' COUNTERPARTY ')
    ))
    def test_property_2_valid_source_types_pass_validation(self, valid_source_type: str):
        """
        Property 2 Extension: Valid source types always pass validation.
        """
        is_valid, error_messages = self.router.validate_source_type(valid_source_type)
        
        assert is_valid is True, f"Expected validation success for '{valid_source_type}'"
        assert isinstance(error_messages, list), "Error messages must be a list"
        assert len(error_messages) == 0, "Valid source types should have no error messages"
    
    @given(st.one_of(st.just(None), st.just(""), st.just("   ")))
    def test_property_2_empty_source_types_fail_validation(self, empty_source_type):
        """
        Property 2 Extension: Empty/None source types always fail validation.
        """
        is_valid, error_messages = self.router.validate_source_type(empty_source_type)
        
        assert is_valid is False
        assert len(error_messages) > 0
        assert any("required" in msg.lower() for msg in error_messages)
    
    def test_table_mapping_consistency(self):
        """
        Property: Table mapping must be consistent across method calls.
        """
        mapping1 = self.router.get_table_mapping()
        mapping2 = self.router.get_table_mapping()
        
        assert mapping1 == mapping2, "Table mapping should be consistent"
        assert 'BANK' in mapping1, "Mapping must include BANK"
        assert 'COUNTERPARTY' in mapping1, "Mapping must include COUNTERPARTY"
        assert mapping1['BANK'] == 'TestBankTradeData'
        assert mapping1['COUNTERPARTY'] == 'TestCounterpartyTradeData'
    
    def test_valid_source_types_consistency(self):
        """
        Property: Valid source types list must be consistent and complete.
        """
        valid_types1 = self.router.get_valid_source_types()
        valid_types2 = self.router.get_valid_source_types()
        
        assert valid_types1 == valid_types2, "Valid source types should be consistent"
        assert 'BANK' in valid_types1, "Must include BANK"
        assert 'COUNTERPARTY' in valid_types1, "Must include COUNTERPARTY"
        assert len(valid_types1) == 2, "Should have exactly 2 valid source types"
    
    @given(st.integers())
    def test_property_non_string_source_types_fail(self, non_string_input):
        """
        Property: Non-string inputs should fail validation gracefully.
        """
        is_valid, error_messages = self.router.validate_source_type(non_string_input)
        
        assert is_valid is False
        assert len(error_messages) > 0
        assert any("string" in msg.lower() for msg in error_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])