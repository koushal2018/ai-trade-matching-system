"""
Basic tests for trade matching functionality.

This module contains simple tests to verify the matching logic works correctly.
"""

import pytest
from .fuzzy_matcher import fuzzy_match, MatchResult
from .scorer import compute_match_score, compute_match_score_with_confidence
from .classifier import classify_match, create_matching_result
from ..models.matching import MatchClassification, DecisionStatus


def test_fuzzy_match_perfect_match():
    """Test fuzzy matching with perfect match."""
    bank_trade = {
        "Trade_ID": {"S": "ABC123"},
        "trade_date": {"S": "2024-10-15"},
        "notional": {"N": "1000000.00"},
        "counterparty": {"S": "Goldman Sachs"},
        "currency": {"S": "USD"}
    }
    
    cp_trade = {
        "Trade_ID": {"S": "ABC123"},
        "trade_date": {"S": "2024-10-15"},
        "notional": {"N": "1000000.00"},
        "counterparty": {"S": "Goldman Sachs"},
        "currency": {"S": "USD"}
    }
    
    result = fuzzy_match(bank_trade, cp_trade)
    
    assert result.trade_id_match is True
    assert result.date_diff_days == 0
    assert result.notional_diff_pct == 0.0
    assert result.counterparty_similarity == 1.0
    assert result.currency_match is True
    assert len(result.differences) == 0


def test_fuzzy_match_with_tolerances():
    """Test fuzzy matching with values within tolerance."""
    bank_trade = {
        "Trade_ID": {"S": "ABC123"},
        "trade_date": {"S": "2024-10-15"},
        "notional": {"N": "1000000.00"},
        "counterparty": {"S": "Goldman Sachs"},
        "currency": {"S": "USD"}
    }
    
    cp_trade = {
        "Trade_ID": {"S": "ABC123"},
        "trade_date": {"S": "2024-10-16"},  # 1 day difference
        "notional": {"N": "1000050.00"},  # 0.005% difference
        "counterparty": {"S": "Goldman Sachs"},
        "currency": {"S": "USD"}
    }
    
    result = fuzzy_match(bank_trade, cp_trade)
    
    assert result.trade_id_match is True
    assert result.date_diff_days == 1
    assert result.notional_diff_pct == pytest.approx(0.005, abs=0.001)
    assert result.counterparty_similarity == 1.0
    assert result.currency_match is True


def test_compute_match_score_perfect():
    """Test match scoring with perfect match."""
    result = MatchResult(
        trade_id_match=True,
        date_diff_days=0,
        notional_diff_pct=0.0,
        counterparty_similarity=1.0,
        currency_match=True,
        exact_matches={},
        differences=[]
    )
    
    score = compute_match_score(result)
    assert score == 1.0


def test_compute_match_score_with_differences():
    """Test match scoring with some differences."""
    result = MatchResult(
        trade_id_match=True,
        date_diff_days=1,  # Within tolerance
        notional_diff_pct=0.005,  # Within tolerance
        counterparty_similarity=0.95,
        currency_match=True,
        exact_matches={},
        differences=[]
    )
    
    score = compute_match_score(result)
    assert 0.85 <= score <= 1.0  # Should be high score


def test_classify_match_auto_match():
    """Test classification for AUTO_MATCH."""
    result = MatchResult(
        trade_id_match=True,
        date_diff_days=0,
        notional_diff_pct=0.0,
        counterparty_similarity=1.0,
        currency_match=True,
        exact_matches={},
        differences=[]
    )
    
    classification, decision, codes = classify_match(
        match_score=0.95,
        match_result=result,
        trade_id="ABC123",
        bank_trade={"Trade_ID": {"S": "ABC123"}},
        counterparty_trade={"Trade_ID": {"S": "ABC123"}}
    )
    
    assert classification == MatchClassification.MATCHED
    assert decision == DecisionStatus.AUTO_MATCH


def test_classify_match_escalate():
    """Test classification for ESCALATE."""
    result = MatchResult(
        trade_id_match=True,
        date_diff_days=1,
        notional_diff_pct=0.005,
        counterparty_similarity=0.85,
        currency_match=True,
        exact_matches={},
        differences=[
            {
                "field_name": "trade_date",
                "bank_value": "2024-10-15",
                "counterparty_value": "2024-10-16",
                "difference_type": "WITHIN_TOLERANCE",
                "tolerance_applied": True,
                "within_tolerance": True
            }
        ]
    )
    
    classification, decision, codes = classify_match(
        match_score=0.75,
        match_result=result,
        trade_id="ABC123",
        bank_trade={"Trade_ID": {"S": "ABC123"}},
        counterparty_trade={"Trade_ID": {"S": "ABC123"}}
    )
    
    assert classification == MatchClassification.PROBABLE_MATCH
    assert decision == DecisionStatus.ESCALATE


def test_classify_match_exception():
    """Test classification for EXCEPTION."""
    result = MatchResult(
        trade_id_match=True,
        date_diff_days=5,
        notional_diff_pct=2.0,
        counterparty_similarity=0.5,
        currency_match=False,
        exact_matches={},
        differences=[
            {
                "field_name": "notional",
                "bank_value": 1000000.0,
                "counterparty_value": 1020000.0,
                "difference_type": "TOLERANCE_EXCEEDED",
                "tolerance_applied": True,
                "within_tolerance": False,
                "percentage_difference": 2.0
            }
        ]
    )
    
    classification, decision, codes = classify_match(
        match_score=0.45,
        match_result=result,
        trade_id="ABC123",
        bank_trade={"Trade_ID": {"S": "ABC123"}},
        counterparty_trade={"Trade_ID": {"S": "ABC123"}}
    )
    
    assert classification == MatchClassification.BREAK
    assert decision == DecisionStatus.EXCEPTION


def test_create_matching_result():
    """Test creating a complete matching result."""
    result = MatchResult(
        trade_id_match=True,
        date_diff_days=0,
        notional_diff_pct=0.0,
        counterparty_similarity=1.0,
        currency_match=True,
        exact_matches={},
        differences=[]
    )
    
    matching_result = create_matching_result(
        trade_id="ABC123",
        match_score=0.95,
        match_result=result,
        bank_trade={"Trade_ID": {"S": "ABC123"}},
        counterparty_trade={"Trade_ID": {"S": "ABC123"}},
        matching_timestamp="2025-01-15T10:00:00Z"
    )
    
    assert matching_result.trade_id == "ABC123"
    assert matching_result.match_score == 0.95
    assert matching_result.classification == MatchClassification.MATCHED
    assert matching_result.decision_status == DecisionStatus.AUTO_MATCH
    assert matching_result.requires_hitl is False


def test_compute_match_score_with_confidence():
    """Test match scoring with confidence metric."""
    result = MatchResult(
        trade_id_match=True,
        date_diff_days=0,
        notional_diff_pct=0.0,
        counterparty_similarity=1.0,
        currency_match=True,
        exact_matches={},
        differences=[]
    )
    
    score, confidence = compute_match_score_with_confidence(result)
    
    assert score == 1.0
    assert confidence >= 0.95


if __name__ == "__main__":
    # Run tests
    test_fuzzy_match_perfect_match()
    print("✓ test_fuzzy_match_perfect_match passed")
    
    test_fuzzy_match_with_tolerances()
    print("✓ test_fuzzy_match_with_tolerances passed")
    
    test_compute_match_score_perfect()
    print("✓ test_compute_match_score_perfect passed")
    
    test_compute_match_score_with_differences()
    print("✓ test_compute_match_score_with_differences passed")
    
    test_classify_match_auto_match()
    print("✓ test_classify_match_auto_match passed")
    
    test_classify_match_escalate()
    print("✓ test_classify_match_escalate passed")
    
    test_classify_match_exception()
    print("✓ test_classify_match_exception passed")
    
    test_create_matching_result()
    print("✓ test_create_matching_result passed")
    
    test_compute_match_score_with_confidence()
    print("✓ test_compute_match_score_with_confidence passed")
    
    print("\nAll tests passed! ✓")
