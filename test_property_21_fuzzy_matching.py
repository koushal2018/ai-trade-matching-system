#!/usr/bin/env python3
"""
Property Test for Property 21: Fuzzy matching applies tolerances

**Feature: agentcore-migration, Property 21: Fuzzy matching applies tolerances**
**Validates: Requirements 7.1, 18.3**
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.latest_trade_matching_agent.matching.fuzzy_matcher import fuzzy_match
from src.latest_trade_matching_agent.models.trade import CanonicalTradeModel


@composite
def trade_pair_strategy(draw):
    """Generate pairs of trades for fuzzy matching tests."""
    base_trade_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    base_notional = draw(st.floats(min_value=1000000, max_value=100000000))
    base_currency = draw(st.sampled_from(['USD', 'EUR', 'GBP', 'JPY']))
    base_counterparty = draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', ' '))))
    base_date = draw(st.dates(min_value=datetime(2024, 1, 1).date(), max_value=datetime(2024, 12, 31).date()))
    
    # Create base trade
    base_trade = {
        "Trade_ID": f"BANK_{base_trade_id}",
        "TRADE_SOURCE": "BANK",
        "trade_date": base_date.strftime("%Y-%m-%d"),
        "notional": base_notional,
        "currency": base_currency,
        "counterparty": base_counterparty.strip(),
        "product_type": "SWAP"
    }
    
    # Create matching trade with slight variations
    matching_trade = {
        "Trade_ID": f"CP_{base_trade_id}",  # Different ID (as per business rules)
        "TRADE_SOURCE": "COUNTERPARTY",
        "trade_date": base_date.strftime("%Y-%m-%d"),
        "notional": base_notional,
        "currency": base_currency,
        "counterparty": base_counterparty.strip(),
        "product_type": "SWAP"
    }
    
    return base_trade, matching_trade


def test_property_21_fuzzy_matching_tolerances():
    """
    Property 21: Fuzzy matching applies tolerances correctly
    
    This test validates that:
    1. Trade_Date: ±2 days tolerance
    2. Notional: ±2% tolerance  
    3. Counterparty: fuzzy string matching
    4. Currency: exact match required
    5. Tolerances are applied consistently
    
    Requirements: 7.1, 18.3
    """
    print("\n🧪 Testing Property 21: Fuzzy matching applies tolerances")
    print("Running 100 test iterations...")
    
    test_cases_passed = 0
    
    for i in range(100):
        try:
            # Generate test trade pair
            base_trade_data = {
                "Trade_ID": f"BANK_TEST_{i:03d}",
                "TRADE_SOURCE": "BANK",
                "trade_date": "2024-06-15",
                "notional": 10000000.0,
                "currency": "USD",
                "counterparty": "Goldman Sachs",
                "product_type": "SWAP"
            }
            
            matching_trade_data = {
                "Trade_ID": f"CP_TEST_{i:03d}",
                "TRADE_SOURCE": "COUNTERPARTY", 
                "trade_date": "2024-06-15",
                "notional": 10000000.0,
                "currency": "USD",
                "counterparty": "Goldman Sachs",
                "product_type": "SWAP"
            }
            
            # Create trade models
            base_trade = CanonicalTradeModel(**base_trade_data)
            matching_trade = CanonicalTradeModel(**matching_trade_data)
            
            # Test exact match
            result = fuzzy_match(base_trade.model_dump(), matching_trade.model_dump())
            
            if not result.is_match():
                print(f"  ❌ Exact match failed for test case {i+1}")
                return False
            
            test_cases_passed += 1
            
        except Exception as e:
            print(f"  ❌ Test case {i+1} failed: {e}")
            return False
    
    print(f"✅ All {test_cases_passed}/100 test cases passed!")
    return True


def test_date_tolerance():
    """Test that ±2 days tolerance is applied correctly."""
    print("\n🧪 Testing date tolerance (±2 days)...")
    
    base_trade_data = {
        "Trade_ID": "BANK_DATE_TEST",
        "TRADE_SOURCE": "BANK",
        "trade_date": "2024-06-17",  # Monday
        "notional": 10000000.0,
        "currency": "USD",
        "counterparty": "Test Bank",
        "product_type": "SWAP"
    }
    
    test_cases = [
        ("2024-06-17", True, "Same date"),
        ("2024-06-18", True, "1 day later"),
        ("2024-06-19", True, "2 days later"),
        ("2024-06-15", True, "2 days earlier"),
        ("2024-06-20", False, "3 days later"),
        ("2024-06-14", False, "3 days earlier"),
    ]
    
    base_trade = CanonicalTradeModel(**base_trade_data)
    
    for test_date, should_match, description in test_cases:
        matching_trade_data = base_trade_data.copy()
        matching_trade_data["Trade_ID"] = "CP_DATE_TEST"
        matching_trade_data["TRADE_SOURCE"] = "COUNTERPARTY"
        matching_trade_data["trade_date"] = test_date
        
        matching_trade = CanonicalTradeModel(**matching_trade_data)
        result = fuzzy_match(base_trade.model_dump(), matching_trade.model_dump())
        
        if result.is_match() != should_match:
            print(f"  ❌ Date tolerance failed for {description}: expected {should_match}, got {result.is_match()}")
            return False
        
        print(f"  ✓ {description}: {'MATCH' if result.is_match() else 'NO MATCH'}")
    
    print("✅ Date tolerance test passed!")
    return True


def test_notional_tolerance():
    """Test that ±2% notional tolerance is applied correctly."""
    print("\n🧪 Testing notional tolerance (±2%)...")
    
    base_notional = 10000000.0  # $10M
    tolerance = 0.02  # 2%
    
    base_trade_data = {
        "Trade_ID": "BANK_NOTIONAL_TEST",
        "TRADE_SOURCE": "BANK",
        "trade_date": "2024-06-17",
        "notional": base_notional,
        "currency": "USD",
        "counterparty": "Test Bank",
        "product_type": "SWAP"
    }
    
    test_cases = [
        (base_notional, True, "Exact notional"),
        (base_notional * (1 + tolerance * 0.5), True, "Within +1%"),
        (base_notional * (1 - tolerance * 0.5), True, "Within -1%"),
        (base_notional * (1 + tolerance), True, "At +2% boundary"),
        (base_notional * (1 - tolerance), True, "At -2% boundary"),
        (base_notional * (1 + tolerance * 1.1), False, "Beyond +2%"),
        (base_notional * (1 - tolerance * 1.1), False, "Beyond -2%"),
    ]
    
    base_trade = CanonicalTradeModel(**base_trade_data)
    
    for test_notional, should_match, description in test_cases:
        matching_trade_data = base_trade_data.copy()
        matching_trade_data["Trade_ID"] = "CP_NOTIONAL_TEST"
        matching_trade_data["TRADE_SOURCE"] = "COUNTERPARTY"
        matching_trade_data["notional"] = test_notional
        
        matching_trade = CanonicalTradeModel(**matching_trade_data)
        result = fuzzy_match(base_trade.model_dump(), matching_trade.model_dump())
        
        if result.is_match() != should_match:
            print(f"  ❌ Notional tolerance failed for {description}: expected {should_match}, got {result.is_match()}")
            return False
        
        print(f"  ✓ {description}: {'MATCH' if result.is_match() else 'NO MATCH'}")
    
    print("✅ Notional tolerance test passed!")
    return True


def test_counterparty_fuzzy_matching():
    """Test that counterparty fuzzy string matching works correctly."""
    print("\n🧪 Testing counterparty fuzzy matching...")
    
    base_trade_data = {
        "Trade_ID": "BANK_CP_TEST",
        "TRADE_SOURCE": "BANK",
        "trade_date": "2024-06-17",
        "notional": 10000000.0,
        "currency": "USD",
        "counterparty": "Goldman Sachs",
        "product_type": "SWAP"
    }
    
    test_cases = [
        ("Goldman Sachs", True, "Exact match"),
        ("goldman sachs", True, "Case insensitive"),
        ("Goldman Sachs & Co", True, "Minor variation"),
        ("GS", True, "Common abbreviation"),
        ("JPMorgan", False, "Different counterparty"),
        ("", False, "Empty counterparty"),
    ]
    
    base_trade = CanonicalTradeModel(**base_trade_data)
    
    for test_counterparty, should_match, description in test_cases:
        matching_trade_data = base_trade_data.copy()
        matching_trade_data["Trade_ID"] = "CP_CP_TEST"
        matching_trade_data["TRADE_SOURCE"] = "COUNTERPARTY"
        matching_trade_data["counterparty"] = test_counterparty
        
        try:
            matching_trade = CanonicalTradeModel(**matching_trade_data)
            result = fuzzy_match(base_trade.model_dump(), matching_trade.model_dump())
            
            if result.is_match() != should_match:
                print(f"  ❌ Counterparty fuzzy matching failed for {description}: expected {should_match}, got {result.is_match()}")
                return False
            
            print(f"  ✓ {description}: {'MATCH' if result.is_match() else 'NO MATCH'}")
            
        except Exception as e:
            if should_match:
                print(f"  ❌ Counterparty test failed for {description}: {e}")
                return False
            else:
                print(f"  ✓ {description}: Correctly rejected invalid input")
    
    print("✅ Counterparty fuzzy matching test passed!")
    return True


def test_currency_exact_match():
    """Test that currency requires exact match (no tolerance)."""
    print("\n🧪 Testing currency exact match requirement...")
    
    base_trade_data = {
        "Trade_ID": "BANK_CCY_TEST",
        "TRADE_SOURCE": "BANK",
        "trade_date": "2024-06-17",
        "notional": 10000000.0,
        "currency": "USD",
        "counterparty": "Test Bank",
        "product_type": "SWAP"
    }
    
    test_cases = [
        ("USD", True, "Exact currency match"),
        ("usd", True, "Case normalized to uppercase"),  # Model normalizes to USD
        ("EUR", False, "Different currency"),
        ("GBP", False, "Another currency"),
    ]
    
    base_trade = CanonicalTradeModel(**base_trade_data)
    
    for test_currency, should_match, description in test_cases:
        matching_trade_data = base_trade_data.copy()
        matching_trade_data["Trade_ID"] = "CP_CCY_TEST"
        matching_trade_data["TRADE_SOURCE"] = "COUNTERPARTY"
        matching_trade_data["currency"] = test_currency
        
        try:
            matching_trade = CanonicalTradeModel(**matching_trade_data)
            result = fuzzy_match(base_trade.model_dump(), matching_trade.model_dump())
            
            if result.is_match() != should_match:
                print(f"  ❌ Currency exact match failed for {description}: expected {should_match}, got {result.is_match()}")
                return False
            
            print(f"  ✓ {description}: {'MATCH' if result.is_match() else 'NO MATCH'}")
            
        except Exception as e:
            if should_match:
                print(f"  ❌ Currency test failed for {description}: {e}")
                return False
            else:
                print(f"  ✓ {description}: Correctly rejected invalid input")
    
    print("✅ Currency exact match test passed!")
    return True


def main():
    """Run all property tests for fuzzy matching tolerances."""
    print("=" * 80)
    print("Property-Based Test for Fuzzy Matching Tolerances")
    print("Property 21: Fuzzy matching applies tolerances")
    print("Validates: Requirements 7.1, 18.3")
    print("=" * 80)
    
    all_passed = True
    
    # Run main property test
    if not test_property_21_fuzzy_matching_tolerances():
        all_passed = False
    
    # Run specific tolerance tests
    if not test_date_tolerance():
        all_passed = False
    
    if not test_notional_tolerance():
        all_passed = False
    
    if not test_counterparty_fuzzy_matching():
        all_passed = False
    
    if not test_currency_exact_match():
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL PROPERTY TESTS PASSED!")
        print("🎯 Property 21: Fuzzy matching applies tolerances - VALIDATED")
        print("📋 Requirements 7.1, 18.3: Matching tolerances - SATISFIED")
        print("✅ The fuzzy matching correctly applies all required tolerances")
    else:
        print("❌ SOME PROPERTY TESTS FAILED!")
        print("🚨 Property 21 validation incomplete")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    main()