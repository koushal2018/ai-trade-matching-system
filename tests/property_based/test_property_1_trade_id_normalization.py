"""
Property-based test for trade ID normalization consistency.
Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency
Validates: Requirements 5.1, 5.2, 5.3, 5.4

Property 1: Trade ID Normalization Consistency
For any trade ID string and optional source type, calling normalize_trade_id should produce:
1. A consistent output regardless of input format variations
2. When source is provided, the output should start with the appropriate prefix
3. The portion after the prefix should contain only numeric characters
"""
import re
from typing import Optional

import pytest
from hypothesis import given, strategies as st, settings, assume, example

# Import the normalize_trade_id function
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "deployment" / "trade_matching"))

from trade_matching_agent_strands import normalize_trade_id


# Hypothesis strategies for generating test data
@st.composite
def trade_id_strategy(draw):
    """Generate realistic trade IDs with various formats."""
    # Generate a numeric ID
    numeric_id = draw(st.integers(min_value=1, max_value=99999999))
    numeric_str = str(numeric_id)
    
    # Choose a format variation
    format_type = draw(st.sampled_from([
        'plain',           # Just the number
        'fab_lower',       # fab_12345
        'fab_upper',       # FAB_12345
        'cpty_lower',      # cpty_12345
        'cpty_upper',      # CPTY_12345
        'bank_lower',      # bank_12345
        'bank_upper',      # BANK_12345
        'mixed_alpha',     # ABC12345
    ]))
    
    if format_type == 'plain':
        return numeric_str
    elif format_type == 'fab_lower':
        return f"fab_{numeric_str}"
    elif format_type == 'fab_upper':
        return f"FAB_{numeric_str}"
    elif format_type == 'cpty_lower':
        return f"cpty_{numeric_str}"
    elif format_type == 'cpty_upper':
        return f"CPTY_{numeric_str}"
    elif format_type == 'bank_lower':
        return f"bank_{numeric_str}"
    elif format_type == 'bank_upper':
        return f"BANK_{numeric_str}"
    elif format_type == 'mixed_alpha':
        prefix = draw(st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu',))))
        return f"{prefix}{numeric_str}"
    
    return numeric_str


@st.composite
def source_type_strategy(draw):
    """Generate source type values."""
    return draw(st.sampled_from([None, "BANK", "COUNTERPARTY", "bank", "counterparty"]))


def extract_numeric_portion(trade_id: str) -> str:
    """Extract the numeric portion from a trade ID."""
    match = re.search(r'(\d+)', trade_id)
    if match:
        return match.group(1)
    return ""


def test_property_normalization_consistency_basic():
    """
    Property 1: Trade ID Normalization Consistency (Basic Test)
    
    For any trade ID with various prefix formats, normalization should produce
    consistent output with the numeric portion extracted.
    
    **Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency**
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    """
    # Test various formats of the same trade ID
    test_cases = [
        ("27254314", None, "27254314"),
        ("fab_27254314", None, "27254314"),
        ("FAB_27254314", None, "27254314"),
        ("cpty_27254314", None, "27254314"),
        ("CPTY_27254314", None, "27254314"),
        ("bank_27254314", None, "27254314"),
        ("BANK_27254314", None, "27254314"),
    ]
    
    for raw_id, source, expected in test_cases:
        result = normalize_trade_id(raw_id, source)
        assert result == expected, f"normalize_trade_id({raw_id}, {source}) = {result}, expected {expected}"


def test_property_normalization_with_source_bank():
    """
    Property 1: Trade ID Normalization with BANK Source
    
    When source is BANK, the normalized ID should have the bank_ prefix.
    
    **Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency**
    **Validates: Requirements 5.2**
    """
    test_cases = [
        "27254314",
        "fab_27254314",
        "FAB_27254314",
        "cpty_27254314",
        "CPTY_27254314",
    ]
    
    for raw_id in test_cases:
        result = normalize_trade_id(raw_id, "BANK")
        assert result.startswith("bank_"), f"normalize_trade_id({raw_id}, 'BANK') should start with 'bank_', got {result}"
        
        # Extract numeric portion
        numeric = result[5:]  # Skip "bank_"
        assert numeric.isdigit(), f"Numeric portion should be digits only, got {numeric}"


def test_property_normalization_with_source_counterparty():
    """
    Property 1: Trade ID Normalization with COUNTERPARTY Source
    
    When source is COUNTERPARTY, the normalized ID should have the cpty_ prefix.
    
    **Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency**
    **Validates: Requirements 5.2**
    """
    test_cases = [
        "27254314",
        "fab_27254314",
        "FAB_27254314",
        "bank_27254314",
        "BANK_27254314",
    ]
    
    for raw_id in test_cases:
        result = normalize_trade_id(raw_id, "COUNTERPARTY")
        assert result.startswith("cpty_"), f"normalize_trade_id({raw_id}, 'COUNTERPARTY') should start with 'cpty_', got {result}"
        
        # Extract numeric portion
        numeric = result[5:]  # Skip "cpty_"
        assert numeric.isdigit(), f"Numeric portion should be digits only, got {numeric}"


@given(
    trade_id=trade_id_strategy()
)
@settings(max_examples=100, deadline=None)
@example(trade_id="27254314")
@example(trade_id="fab_27254314")
@example(trade_id="FAB_27254314")
@example(trade_id="cpty_12345")
@example(trade_id="BANK_99999")
def test_property_normalization_extracts_numeric(trade_id):
    """
    Property 1: Trade ID Normalization Extracts Numeric Portion
    
    For any trade ID, normalization without source should extract the numeric portion.
    
    **Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency**
    **Validates: Requirements 5.3**
    """
    # Skip empty trade IDs
    assume(trade_id and len(trade_id) > 0)
    
    result = normalize_trade_id(trade_id, None)
    
    # Result should be numeric (when no source is provided)
    assert result.isdigit(), f"normalize_trade_id({trade_id}, None) should return numeric ID, got {result}"
    
    # The numeric portion should match what we extract manually
    expected_numeric = extract_numeric_portion(trade_id)
    assert result == expected_numeric, f"Expected {expected_numeric}, got {result}"


@given(
    trade_id=trade_id_strategy(),
    source=source_type_strategy()
)
@settings(max_examples=100, deadline=None)
@example(trade_id="27254314", source="BANK")
@example(trade_id="fab_27254314", source="COUNTERPARTY")
@example(trade_id="CPTY_12345", source="bank")
def test_property_normalization_consistency(trade_id, source):
    """
    Property 1: Trade ID Normalization Consistency (Property-Based Test)
    
    For any trade ID and source type, normalization should:
    1. Extract the numeric portion consistently
    2. Apply the correct prefix based on source
    3. Produce output with only numeric characters after the prefix
    
    **Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency**
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    """
    # Skip empty trade IDs
    assume(trade_id and len(trade_id) > 0)
    
    result = normalize_trade_id(trade_id, source)
    
    # Extract the expected numeric portion
    expected_numeric = extract_numeric_portion(trade_id)
    assume(expected_numeric)  # Skip if no numeric portion found
    
    if source:
        source_lower = source.lower()
        if source_lower == "bank":
            # Should have bank_ prefix
            assert result.startswith("bank_"), f"Expected 'bank_' prefix for source={source}, got {result}"
            numeric_part = result[5:]
            assert numeric_part == expected_numeric, f"Expected numeric part {expected_numeric}, got {numeric_part}"
        elif source_lower == "counterparty":
            # Should have cpty_ prefix
            assert result.startswith("cpty_"), f"Expected 'cpty_' prefix for source={source}, got {result}"
            numeric_part = result[5:]
            assert numeric_part == expected_numeric, f"Expected numeric part {expected_numeric}, got {numeric_part}"
    else:
        # No source - should return just the numeric portion
        assert result == expected_numeric, f"Expected {expected_numeric}, got {result}"


@given(
    trade_id1=trade_id_strategy(),
    trade_id2=trade_id_strategy()
)
@settings(max_examples=100, deadline=None)
def test_property_normalization_idempotence(trade_id1, trade_id2):
    """
    Property 1: Trade ID Normalization Idempotence
    
    For any two trade IDs with the same numeric portion, normalization should
    produce the same result (regardless of prefix variations).
    
    **Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency**
    **Validates: Requirements 5.1, 5.4**
    """
    # Skip empty trade IDs
    assume(trade_id1 and trade_id2)
    
    # Extract numeric portions
    numeric1 = extract_numeric_portion(trade_id1)
    numeric2 = extract_numeric_portion(trade_id2)
    
    # Only test if both have numeric portions and they match
    assume(numeric1 and numeric2 and numeric1 == numeric2)
    
    # Normalize both
    result1 = normalize_trade_id(trade_id1, None)
    result2 = normalize_trade_id(trade_id2, None)
    
    # Should produce the same result
    assert result1 == result2, f"normalize_trade_id({trade_id1}) = {result1}, normalize_trade_id({trade_id2}) = {result2}, expected same result"


def test_property_normalization_empty_input():
    """
    Property 1: Trade ID Normalization Empty Input Handling
    
    Empty or None trade IDs should be handled gracefully.
    
    **Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency**
    **Validates: Requirements 5.1**
    """
    # Empty string
    result = normalize_trade_id("", None)
    assert result == "", "Empty string should return empty string"
    
    # None
    result = normalize_trade_id(None, None)
    assert result is None, "None should return None"


def test_property_normalization_case_insensitive():
    """
    Property 1: Trade ID Normalization Case Insensitivity
    
    Prefix matching should be case-insensitive.
    
    **Feature: agent-issues-fix, Property 1: Trade ID Normalization Consistency**
    **Validates: Requirements 5.1, 5.4**
    """
    test_cases = [
        ("fab_12345", "FAB_12345"),
        ("cpty_12345", "CPTY_12345"),
        ("bank_12345", "BANK_12345"),
    ]
    
    for lower_case, upper_case in test_cases:
        result_lower = normalize_trade_id(lower_case, None)
        result_upper = normalize_trade_id(upper_case, None)
        assert result_lower == result_upper, f"Case-insensitive normalization failed: {lower_case} vs {upper_case}"


if __name__ == '__main__':
    print("="*80)
    print("Property 1: Trade ID Normalization Consistency")
    print("Feature: agent-issues-fix")
    print("Validates: Requirements 5.1, 5.2, 5.3, 5.4")
    print("="*80)
    print()
    
    # Run basic tests
    print("Running basic consistency test...")
    try:
        test_property_normalization_consistency_basic()
        print("✅ PASSED: Basic consistency test")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    print("\nRunning BANK source test...")
    try:
        test_property_normalization_with_source_bank()
        print("✅ PASSED: BANK source test")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    print("\nRunning COUNTERPARTY source test...")
    try:
        test_property_normalization_with_source_counterparty()
        print("✅ PASSED: COUNTERPARTY source test")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    print("\nRunning empty input test...")
    try:
        test_property_normalization_empty_input()
        print("✅ PASSED: Empty input test")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    print("\nRunning case insensitivity test...")
    try:
        test_property_normalization_case_insensitive()
        print("✅ PASSED: Case insensitivity test")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        exit(1)
    
    print("\n" + "="*80)
    print("✅ ALL BASIC TESTS PASSED")
    print("="*80)
    print("\nTo run property-based tests with Hypothesis:")
    print("  pytest tests/property_based/test_property_1_trade_id_normalization.py -v")
