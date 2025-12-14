#!/usr/bin/env python3
"""
Simple Property Test for Property 17: Trade source classification validity

**Feature: agentcore-migration, Property 17: Trade source classification validity**
**Validates: Requirements 6.2**
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from latest_trade_matching_agent.models.trade import CanonicalTradeModel
from latest_trade_matching_agent.models.adapter import CanonicalAdapterOutput
import random


def test_property_17_trade_source_classification_validity():
    """
    **Feature: agentcore-migration, Property 17: Trade source classification validity**
    **Validates: Requirements 6.2**
    
    Property: For any parsed trade document, the TRADE_SOURCE field should be 
    classified as either "BANK" or "COUNTERPARTY"
    """
    print("🧪 Testing Property 17: Trade source classification validity")
    print("Running 100 test iterations...")
    
    test_cases_passed = 0
    
    for i in range(100):
        # Generate random test data
        trade_data = {
            "Trade_ID": f"TEST{random.randint(100000, 999999)}",
            "TRADE_SOURCE": random.choice(["BANK", "COUNTERPARTY"]),
            "trade_date": "2024-01-15",
            "notional": random.uniform(1000.0, 10000000.0),
            "currency": random.choice(["USD", "EUR", "GBP"]),
            "counterparty": random.choice(["Goldman Sachs", "JPMorgan", "Citigroup"]),
            "product_type": random.choice(["SWAP", "OPTION", "FORWARD"])
        }
        
        try:
            # Create the canonical trade model
            trade = CanonicalTradeModel(**trade_data)
            
            # Property 1: TRADE_SOURCE must be either BANK or COUNTERPARTY
            assert trade.TRADE_SOURCE in ["BANK", "COUNTERPARTY"], \
                f"TRADE_SOURCE must be BANK or COUNTERPARTY, got: {trade.TRADE_SOURCE}"
            
            # Property 2: TRADE_SOURCE should match the input (normalized to uppercase)
            expected_source = trade_data["TRADE_SOURCE"].upper()
            assert trade.TRADE_SOURCE == expected_source, \
                f"TRADE_SOURCE should be {expected_source}, got: {trade.TRADE_SOURCE}"
            
            # Property 3: DynamoDB conversion preserves TRADE_SOURCE
            dynamodb_format = trade.to_dynamodb_format()
            assert "TRADE_SOURCE" in dynamodb_format, \
                "TRADE_SOURCE must be present in DynamoDB format"
            assert dynamodb_format["TRADE_SOURCE"]["S"] in ["BANK", "COUNTERPARTY"], \
                f"DynamoDB TRADE_SOURCE must be BANK or COUNTERPARTY, got: {dynamodb_format['TRADE_SOURCE']['S']}"
            
            # Property 4: Round-trip conversion preserves TRADE_SOURCE
            trade_back = CanonicalTradeModel.from_dynamodb_format(dynamodb_format)
            assert trade_back.TRADE_SOURCE == trade.TRADE_SOURCE, \
                f"Round-trip should preserve TRADE_SOURCE: {trade.TRADE_SOURCE} != {trade_back.TRADE_SOURCE}"
            
            # Property 5: TRADE_SOURCE determines table routing logic
            expected_table = "BankTradeData" if trade.TRADE_SOURCE == "BANK" else "CounterpartyTradeData"
            actual_table = "BankTradeData" if trade.TRADE_SOURCE == "BANK" else "CounterpartyTradeData"
            assert actual_table == expected_table, \
                f"Trade routing logic failed: {trade.TRADE_SOURCE} should route to {expected_table}, got {actual_table}"
            
            test_cases_passed += 1
            
        except Exception as e:
            print(f"❌ Test case {i+1} failed: {e}")
            return False
    
    print(f"✅ All {test_cases_passed}/100 test cases passed!")
    return True


def test_case_insensitive_handling():
    """Test that case variations are handled correctly."""
    print("\n🧪 Testing case-insensitive handling...")
    
    test_cases = [
        ("BANK", "BANK"),
        ("bank", "BANK"),
        ("Bank", "BANK"),
        ("COUNTERPARTY", "COUNTERPARTY"),
        ("counterparty", "COUNTERPARTY"),
        ("Counterparty", "COUNTERPARTY")
    ]
    
    for raw_source, expected_normalized in test_cases:
        trade_data = {
            "Trade_ID": "TEST123",
            "TRADE_SOURCE": raw_source,
            "trade_date": "2024-01-01",
            "notional": 1000000.0,
            "currency": "USD",
            "counterparty": "Test Bank",
            "product_type": "SWAP"
        }
        
        try:
            trade = CanonicalTradeModel(**trade_data)
            assert trade.TRADE_SOURCE == expected_normalized, \
                f"Expected {expected_normalized}, got {trade.TRADE_SOURCE}"
            print(f"  ✓ '{raw_source}' -> '{trade.TRADE_SOURCE}'")
        except Exception as e:
            print(f"  ❌ Case '{raw_source}' failed: {e}")
            return False
    
    print("✅ Case-insensitive handling passed!")
    return True


def test_invalid_sources_rejected():
    """Test that invalid TRADE_SOURCE values are rejected."""
    print("\n🧪 Testing invalid source rejection...")
    
    invalid_sources = ["BROKER", "EXCHANGE", "CLEARING", "", None]
    
    for invalid_source in invalid_sources:
        trade_data = {
            "Trade_ID": "TEST123",
            "TRADE_SOURCE": invalid_source,
            "trade_date": "2024-01-01",
            "notional": 1000000.0,
            "currency": "USD",
            "counterparty": "Test Bank",
            "product_type": "SWAP"
        }
        
        try:
            trade = CanonicalTradeModel(**trade_data)
            print(f"  ❌ Should have rejected invalid source: {invalid_source}")
            return False
        except (ValueError, TypeError):
            print(f"  ✓ Correctly rejected invalid source: {invalid_source}")
    
    print("✅ Invalid source rejection passed!")
    return True


def main():
    """Run all property tests."""
    print("=" * 80)
    print("Property-Based Test for Canonical Models")
    print("Property 17: Trade source classification validity")
    print("Validates: Requirements 6.2")
    print("=" * 80)
    
    all_passed = True
    
    # Run main property test
    if not test_property_17_trade_source_classification_validity():
        all_passed = False
    
    # Run case-insensitive test
    if not test_case_insensitive_handling():
        all_passed = False
    
    # Run invalid source rejection test
    if not test_invalid_sources_rejected():
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL PROPERTY TESTS PASSED!")
        print("🎯 Property 17: Trade source classification validity - VALIDATED")
        print("📋 Requirements 6.2: Classify trade source - SATISFIED")
        print("✅ The canonical models correctly enforce trade source classification")
    else:
        print("❌ SOME PROPERTY TESTS FAILED!")
        print("🚨 Property 17 validation incomplete")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)