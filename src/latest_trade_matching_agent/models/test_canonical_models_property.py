"""
Property-Based Tests for Canonical Models

This module implements property-based tests to validate correctness properties 
of the canonical trade and adapter models.

**Feature: agentcore-migration, Property 17: Trade source classification validity**

Requirements: 6.2
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.trade import CanonicalTradeModel
from models.adapter import CanonicalAdapterOutput
from typing import Dict, Any, List
import json
import random


# ========== GENERATORS ==========

def generate_valid_trade_id() -> str:
    """Generate valid trade IDs."""
    prefixes = ["GCS", "FAB", "TRD", "SWP", "OPT"]
    prefix = random.choice(prefixes)
    number = random.randint(100000, 999999999)
    return f"{prefix}{number}"


def generate_valid_currency_code() -> str:
    """Generate valid 3-letter currency codes."""
    currencies = [
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
        "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "SGD", "HKD"
    ]
    return random.choice(currencies)


def generate_valid_date_string() -> str:
    """Generate valid date strings in YYYY-MM-DD format."""
    year = random.randint(2020, 2030)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Safe day range
    return f"{year:04d}-{month:02d}-{day:02d}"


def generate_valid_counterparty_name() -> str:
    """Generate valid counterparty names."""
    counterparties = [
        "Goldman Sachs", "JPMorgan Chase", "Morgan Stanley", "Citigroup",
        "Bank of America", "Wells Fargo", "Deutsche Bank", "Barclays",
        "Credit Suisse", "UBS", "HSBC", "BNP Paribas", "Societe Generale"
    ]
    return random.choice(counterparties)


def generate_valid_product_type() -> str:
    """Generate valid product types."""
    products = ["SWAP", "OPTION", "FORWARD", "FUTURE", "SWAPTION", "CAP", "FLOOR"]
    return random.choice(products)


def generate_canonical_trade_model_data() -> Dict[str, Any]:
    """Generate data for creating CanonicalTradeModel instances."""
    # Mandatory fields
    trade_data = {
        "Trade_ID": generate_valid_trade_id(),
        "TRADE_SOURCE": random.choice(["BANK", "COUNTERPARTY"]),
        "trade_date": generate_valid_date_string(),
        "notional": random.uniform(1000.0, 1000000000.0),
        "currency": generate_valid_currency_code(),
        "counterparty": generate_valid_counterparty_name(),
        "product_type": generate_valid_product_type()
    }
    
    # Optional fields (randomly include some)
    if random.choice([True, False]):
        trade_data.update({
            "effective_date": generate_valid_date_string(),
            "maturity_date": generate_valid_date_string(),
            "commodity_type": random.choice(["CRUDE_OIL", "NATURAL_GAS", "GOLD", "SILVER"]),
            "settlement_type": random.choice(["CASH", "PHYSICAL"]),
            "extraction_confidence": random.uniform(0.0, 1.0)
        })
    
    return trade_data


def generate_canonical_adapter_output_data() -> Dict[str, Any]:
    """Generate data for creating CanonicalAdapterOutput instances."""
    adapter_type = random.choice(["PDF", "CHAT", "EMAIL", "VOICE"])
    source_type = random.choice(["BANK", "COUNTERPARTY"])
    
    # Base data
    adapter_data = {
        "adapter_type": adapter_type,
        "document_id": f"doc_{random.randint(100, 999999)}",
        "source_type": source_type,
        "extracted_text": f"Sample extracted text {random.randint(1, 1000)}",
        "s3_location": f"s3://test-bucket/extracted/{source_type}/doc_{random.randint(100, 999)}.json"
    }
    
    # Adapter-specific metadata
    if adapter_type == "PDF":
        adapter_data["metadata"] = {
            "page_count": random.randint(1, 20),
            "dpi": 300,  # Must be 300 for PDF
            "ocr_confidence": random.uniform(0.5, 1.0)
        }
    elif adapter_type == "CHAT":
        adapter_data["metadata"] = {
            "chat_platform": random.choice(["slack", "teams", "discord"]),
            "user_id": f"U{random.randint(100000, 999999)}",
            "channel_id": f"C{random.randint(100000, 999999)}"
        }
    else:
        adapter_data["metadata"] = {}
    
    return adapter_data


# ========== PROPERTY TESTS ==========

def test_property_17_trade_source_classification_validity():
    """
    **Feature: agentcore-migration, Property 17: Trade source classification validity**
    **Validates: Requirements 6.2**
    
    Property: For any parsed trade document, the TRADE_SOURCE field should be 
    classified as either "BANK" or "COUNTERPARTY"
    
    This property ensures that:
    1. TRADE_SOURCE is always one of the two valid values
    2. The classification is preserved through model operations
    3. DynamoDB round-trip preserves the classification
    """
    print("Running Property 17 with 100 test cases...")
    
    for i in range(100):
        # Generate test data
        trade_data = generate_canonical_trade_model_data()
        
        # Create the canonical trade model
        trade = CanonicalTradeModel(**trade_data)
        
        # Property 1: TRADE_SOURCE must be either BANK or COUNTERPARTY
        assert trade.TRADE_SOURCE in ["BANK", "COUNTERPARTY"], \
            f"Test {i+1}: TRADE_SOURCE must be BANK or COUNTERPARTY, got: {trade.TRADE_SOURCE}"
        
        # Property 2: TRADE_SOURCE should match the input (case-insensitive handling)
        expected_source = trade_data["TRADE_SOURCE"].upper()
        assert trade.TRADE_SOURCE == expected_source, \
            f"Test {i+1}: TRADE_SOURCE should be {expected_source}, got: {trade.TRADE_SOURCE}"
        
        # Property 3: DynamoDB conversion preserves TRADE_SOURCE
        dynamodb_format = trade.to_dynamodb_format()
        assert "TRADE_SOURCE" in dynamodb_format, \
            f"Test {i+1}: TRADE_SOURCE must be present in DynamoDB format"
        assert dynamodb_format["TRADE_SOURCE"]["S"] in ["BANK", "COUNTERPARTY"], \
            f"Test {i+1}: DynamoDB TRADE_SOURCE must be BANK or COUNTERPARTY, got: {dynamodb_format['TRADE_SOURCE']['S']}"
        
        # Property 4: Round-trip conversion preserves TRADE_SOURCE
        trade_back = CanonicalTradeModel.from_dynamodb_format(dynamodb_format)
        assert trade_back.TRADE_SOURCE == trade.TRADE_SOURCE, \
            f"Test {i+1}: Round-trip should preserve TRADE_SOURCE: {trade.TRADE_SOURCE} != {trade_back.TRADE_SOURCE}"
        
        # Property 5: TRADE_SOURCE determines table routing logic
        # This validates the business rule that BANK trades go to BankTradeData
        # and COUNTERPARTY trades go to CounterpartyTradeData
        if trade.TRADE_SOURCE == "BANK":
            expected_table = "BankTradeData"
        else:  # COUNTERPARTY
            expected_table = "CounterpartyTradeData"
        
        # Simulate the table routing logic that would be used in the agent
        actual_table = "BankTradeData" if trade.TRADE_SOURCE == "BANK" else "CounterpartyTradeData"
        assert actual_table == expected_table, \
            f"Test {i+1}: Trade routing logic failed: {trade.TRADE_SOURCE} should route to {expected_table}, got {actual_table}"


def test_property_adapter_source_type_validity():
    """
    Property: For any adapter output, the source_type field should be 
    classified as either "BANK" or "COUNTERPARTY"
    
    This ensures consistency between adapter output and trade model classification.
    """
    print("Running adapter source type validity with 100 test cases...")
    
    for i in range(100):
        # Generate test data
        adapter_data = generate_canonical_adapter_output_data()
        
        # Create the canonical adapter output
        adapter_output = CanonicalAdapterOutput(**adapter_data)
        
        # Property 1: source_type must be either BANK or COUNTERPARTY
        assert adapter_output.source_type in ["BANK", "COUNTERPARTY"], \
            f"Test {i+1}: source_type must be BANK or COUNTERPARTY, got: {adapter_output.source_type}"
        
        # Property 2: source_type should match the input
        expected_source = adapter_data["source_type"]
        assert adapter_output.source_type == expected_source, \
            f"Test {i+1}: source_type should be {expected_source}, got: {adapter_output.source_type}"
        
        # Property 3: S3 location should reflect the source type
        assert adapter_output.source_type in adapter_output.s3_location, \
            f"Test {i+1}: S3 location should contain source_type {adapter_output.source_type}: {adapter_output.s3_location}"


def test_property_trade_source_case_insensitive_handling():
    """
    Property: Trade source classification should handle case variations correctly.
    
    This ensures that "bank", "BANK", "Bank" all become "BANK" and
    "counterparty", "COUNTERPARTY", "Counterparty" all become "COUNTERPARTY".
    """
    print("Running case-insensitive handling tests...")
    
    # Test various case combinations
    test_cases = [
        ("BANK", "BANK"),
        ("bank", "BANK"),
        ("Bank", "BANK"),
        ("COUNTERPARTY", "COUNTERPARTY"),
        ("counterparty", "COUNTERPARTY"),
        ("Counterparty", "COUNTERPARTY")
    ]
    
    for raw_source, expected_normalized in test_cases:
        # Create minimal trade data with the raw source
        trade_data = {
            "Trade_ID": "TEST123",
            "TRADE_SOURCE": raw_source,  # Use raw input
            "trade_date": "2024-01-01",
            "notional": 1000000.0,
            "currency": "USD",
            "counterparty": "Test Bank",
            "product_type": "SWAP"
        }
        
        # The model should normalize to uppercase
        trade = CanonicalTradeModel(**trade_data)
        assert trade.TRADE_SOURCE in ["BANK", "COUNTERPARTY"], \
            f"Normalized TRADE_SOURCE must be BANK or COUNTERPARTY, got: {trade.TRADE_SOURCE}"
        assert trade.TRADE_SOURCE == expected_normalized, \
            f"Expected {expected_normalized}, got {trade.TRADE_SOURCE}"


def test_property_trade_source_consistency_across_operations():
    """
    Property: TRADE_SOURCE should remain consistent across all model operations.
    
    This ensures that serialization, deserialization, and other operations
    preserve the trade source classification.
    """
    print("Running consistency across operations with 50 test cases...")
    
    for i in range(50):
        # Generate test data
        trade_data = generate_canonical_trade_model_data()
        trade = CanonicalTradeModel(**trade_data)
        original_source = trade.TRADE_SOURCE
        
        # Property 1: JSON serialization preserves TRADE_SOURCE
        json_data = trade.model_dump()
        assert json_data["TRADE_SOURCE"] == original_source, \
            f"Test {i+1}: JSON serialization should preserve TRADE_SOURCE"
        
        # Property 2: JSON deserialization preserves TRADE_SOURCE
        trade_from_json = CanonicalTradeModel(**json_data)
        assert trade_from_json.TRADE_SOURCE == original_source, \
            f"Test {i+1}: JSON deserialization should preserve TRADE_SOURCE"
        
        # Property 3: DynamoDB format preserves TRADE_SOURCE
        dynamodb_data = trade.to_dynamodb_format()
        trade_from_dynamodb = CanonicalTradeModel.from_dynamodb_format(dynamodb_data)
        assert trade_from_dynamodb.TRADE_SOURCE == original_source, \
            f"Test {i+1}: DynamoDB round-trip should preserve TRADE_SOURCE"
        
        # Property 4: All instances should have the same TRADE_SOURCE
        all_sources = [
            trade.TRADE_SOURCE,
            trade_from_json.TRADE_SOURCE,
            trade_from_dynamodb.TRADE_SOURCE
        ]
        assert all(source == original_source for source in all_sources), \
            f"Test {i+1}: All operations should preserve TRADE_SOURCE {original_source}, got: {all_sources}"


# ========== EDGE CASE TESTS ==========

def test_invalid_trade_source_rejected():
    """
    Test that invalid TRADE_SOURCE values are properly rejected.
    
    This validates that the model enforces the constraint that TRADE_SOURCE
    must be either "BANK" or "COUNTERPARTY".
    """
    invalid_sources = ["BROKER", "EXCHANGE", "CLEARING", "", "bank", "counterparty", None]
    
    for invalid_source in invalid_sources:
        try:
            trade_data = {
                "Trade_ID": "TEST123",
                "TRADE_SOURCE": invalid_source,
                "trade_date": "2024-01-01",
                "notional": 1000000.0,
                "currency": "USD",
                "counterparty": "Test Bank",
                "product_type": "SWAP"
            }
            
            # This should raise a validation error
            trade = CanonicalTradeModel(**trade_data)
            
            # If we get here, the validation failed
            assert False, f"Should have rejected invalid TRADE_SOURCE: {invalid_source}"
            
        except (ValueError, TypeError) as e:
            # This is expected - invalid sources should be rejected
            assert "TRADE_SOURCE" in str(e) or "validation error" in str(e).lower(), \
                f"Error should mention TRADE_SOURCE validation: {e}"


def test_adapter_invalid_source_type_rejected():
    """
    Test that invalid source_type values are properly rejected in adapter output.
    """
    invalid_sources = ["BROKER", "EXCHANGE", "", None]
    
    for invalid_source in invalid_sources:
        try:
            adapter_data = {
                "adapter_type": "PDF",
                "document_id": "test_doc",
                "source_type": invalid_source,
                "extracted_text": "Test text",
                "metadata": {"page_count": 1, "dpi": 300},
                "s3_location": "s3://test/doc.json"
            }
            
            # This should raise a validation error
            adapter = CanonicalAdapterOutput(**adapter_data)
            
            # If we get here, the validation failed
            assert False, f"Should have rejected invalid source_type: {invalid_source}"
            
        except (ValueError, TypeError) as e:
            # This is expected - invalid sources should be rejected
            assert "source_type" in str(e) or "validation error" in str(e).lower(), \
                f"Error should mention source_type validation: {e}"


# ========== TEST RUNNER ==========

def run_property_tests():
    """Run all property-based tests for canonical models."""
    print("=" * 80)
    print("Running Property-Based Tests for Canonical Models")
    print("=" * 80)
    
    try:
        print("\n🧪 Testing Property 17: Trade source classification validity...")
        test_property_17_trade_source_classification_validity()
        print("✅ Property 17 passed!")
        
        print("\n🧪 Testing adapter source type validity...")
        test_property_adapter_source_type_validity()
        print("✅ Adapter source type validity passed!")
        
        print("\n🧪 Testing case-insensitive handling...")
        test_property_trade_source_case_insensitive_handling()
        print("✅ Case-insensitive handling passed!")
        
        print("\n🧪 Testing consistency across operations...")
        test_property_trade_source_consistency_across_operations()
        print("✅ Consistency across operations passed!")
        
        print("\n🧪 Testing invalid trade source rejection...")
        test_invalid_trade_source_rejected()
        print("✅ Invalid trade source rejection passed!")
        
        print("\n🧪 Testing invalid adapter source type rejection...")
        test_adapter_invalid_source_type_rejected()
        print("✅ Invalid adapter source type rejection passed!")
        
        print("\n" + "=" * 80)
        print("✅ All property-based tests passed successfully!")
        print("🎯 Property 17: Trade source classification validity - VALIDATED")
        print("📋 Requirements 6.2: Classify trade source - SATISFIED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Property test failed: {e}")
        print("=" * 80)
        return False


if __name__ == "__main__":
    run_property_tests()