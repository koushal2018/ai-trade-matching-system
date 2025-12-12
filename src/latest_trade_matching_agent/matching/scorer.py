"""
Match Scoring System

This module implements the match scoring system that computes a weighted
score based on field comparisons.

Requirements:
    - 7.1: Use weighted field comparisons
    - 7.2: Return score 0.0 to 1.0 with confidence metrics

Scoring Weights:
    - Trade_ID: 0.30 (exact match required)
    - trade_date: 0.20 (±1 day tolerance)
    - notional: 0.25 (±0.01% tolerance)
    - counterparty: 0.15 (fuzzy match)
    - currency: 0.10 (exact match)
"""

from typing import Dict, Tuple
from .fuzzy_matcher import MatchResult


# Field weights for scoring
FIELD_WEIGHTS = {
    "Trade_ID": 0.30,
    "trade_date": 0.20,
    "notional": 0.25,
    "counterparty": 0.15,
    "currency": 0.10,
}


def compute_match_score(match_result: MatchResult) -> float:
    """
    Compute match score based on field comparisons.
    
    The score is a weighted average of individual field scores, where each
    field contributes based on its importance to trade matching.
    
    Scoring Logic:
        - Trade_ID: 1.0 if exact match, 0.0 otherwise
        - trade_date: Decreases linearly with day difference
        - notional: Decreases based on percentage difference
        - counterparty: Uses fuzzy similarity score
        - currency: 1.0 if exact match, 0.0 otherwise
    
    Args:
        match_result: Result from fuzzy_match() function
    
    Returns:
        Match score from 0.0 (no match) to 1.0 (perfect match)
    
    Requirements:
        - 7.1: Weighted field comparisons
        - 7.2: Score 0.0 to 1.0
    
    Example:
        >>> result = MatchResult(
        ...     trade_id_match=True,
        ...     date_diff_days=0,
        ...     notional_diff_pct=0.005,
        ...     counterparty_similarity=0.95,
        ...     currency_match=True,
        ...     exact_matches={},
        ...     differences=[]
        ... )
        >>> score = compute_match_score(result)
        >>> score >= 0.95
        True
    """
    field_scores = {}
    
    # 1. Trade_ID: Binary score (must match exactly)
    field_scores["Trade_ID"] = 1.0 if match_result.trade_id_match else 0.0
    
    # 2. trade_date: Score based on day difference
    if match_result.date_diff_days is not None:
        field_scores["trade_date"] = _compute_date_score(match_result.date_diff_days)
    else:
        # If date is missing, give neutral score
        field_scores["trade_date"] = 0.5
    
    # 3. notional: Score based on percentage difference
    if match_result.notional_diff_pct is not None:
        field_scores["notional"] = _compute_notional_score(match_result.notional_diff_pct)
    else:
        # If notional is missing, give neutral score
        field_scores["notional"] = 0.5
    
    # 4. counterparty: Use fuzzy similarity score directly
    if match_result.counterparty_similarity is not None:
        field_scores["counterparty"] = match_result.counterparty_similarity
    else:
        # If counterparty is missing, give neutral score
        field_scores["counterparty"] = 0.5
    
    # 5. currency: Binary score (must match exactly)
    if match_result.currency_match is not None:
        field_scores["currency"] = 1.0 if match_result.currency_match else 0.0
    else:
        # If currency is missing, give neutral score
        field_scores["currency"] = 0.5
    
    # Compute weighted average
    total_score = sum(
        field_scores[field] * FIELD_WEIGHTS[field]
        for field in FIELD_WEIGHTS
    )
    
    # Round to 2 decimal places
    return round(total_score, 2)


def compute_match_score_with_confidence(
    match_result: MatchResult
) -> Tuple[float, float]:
    """
    Compute match score with confidence metric.
    
    Confidence is based on:
    - Number of fields available for comparison
    - Quality of fuzzy matches
    - Presence of critical fields (Trade_ID, notional, date)
    
    Args:
        match_result: Result from fuzzy_match() function
    
    Returns:
        Tuple of (match_score, confidence_score)
        Both scores are in range [0.0, 1.0]
    
    Requirements:
        - 7.2: Include confidence metrics
    
    Example:
        >>> result = MatchResult(
        ...     trade_id_match=True,
        ...     date_diff_days=0,
        ...     notional_diff_pct=0.0,
        ...     counterparty_similarity=1.0,
        ...     currency_match=True,
        ...     exact_matches={},
        ...     differences=[]
        ... )
        >>> score, confidence = compute_match_score_with_confidence(result)
        >>> score == 1.0 and confidence >= 0.95
        True
    """
    match_score = compute_match_score(match_result)
    
    # Compute confidence based on data availability and quality
    confidence_factors = []
    
    # Critical fields presence
    if match_result.trade_id_match is not None:
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.0)
    
    if match_result.date_diff_days is not None:
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.5)
    
    if match_result.notional_diff_pct is not None:
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.5)
    
    if match_result.counterparty_similarity is not None:
        # High similarity = high confidence
        confidence_factors.append(match_result.counterparty_similarity)
    else:
        confidence_factors.append(0.5)
    
    if match_result.currency_match is not None:
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.5)
    
    # Average confidence
    confidence_score = sum(confidence_factors) / len(confidence_factors)
    
    return match_score, round(confidence_score, 2)


def _compute_date_score(days_diff: int) -> float:
    """
    Compute score for date field based on day difference.
    
    Scoring:
        - 0 days: 1.0
        - 1 day: 0.9 (within tolerance)
        - 2 days: 0.7
        - 3+ days: decreases linearly to 0.0 at 7+ days
    
    Args:
        days_diff: Absolute difference in days
    
    Returns:
        Score from 0.0 to 1.0
    """
    if days_diff == 0:
        return 1.0
    elif days_diff == 1:
        return 0.9  # Within tolerance
    elif days_diff == 2:
        return 0.7
    elif days_diff <= 7:
        # Linear decrease from 0.7 to 0.0
        return max(0.0, 0.7 - (days_diff - 2) * 0.14)
    else:
        return 0.0


def _compute_notional_score(pct_diff: float) -> float:
    """
    Compute score for notional field based on percentage difference.
    
    Scoring:
        - 0.00%: 1.0
        - 0.01%: 0.95 (at tolerance boundary)
        - 0.10%: 0.80
        - 1.00%: 0.50
        - 5.00%+: 0.0
    
    Args:
        pct_diff: Percentage difference (0.0 to 100.0)
    
    Returns:
        Score from 0.0 to 1.0
    """
    if pct_diff == 0.0:
        return 1.0
    elif pct_diff <= 0.01:
        # Within tolerance: 0.95 to 1.0
        return 0.95 + (0.01 - pct_diff) / 0.01 * 0.05
    elif pct_diff <= 0.10:
        # 0.01% to 0.10%: 0.80 to 0.95
        return 0.80 + (0.10 - pct_diff) / 0.09 * 0.15
    elif pct_diff <= 1.0:
        # 0.10% to 1.0%: 0.50 to 0.80
        return 0.50 + (1.0 - pct_diff) / 0.9 * 0.30
    elif pct_diff <= 5.0:
        # 1.0% to 5.0%: 0.0 to 0.50
        return max(0.0, 0.50 - (pct_diff - 1.0) / 4.0 * 0.50)
    else:
        return 0.0


def _compute_fuzzy_score(similarity: float) -> float:
    """
    Compute score for fuzzy-matched fields.
    
    For counterparty names, we use the similarity score directly
    but apply a threshold for acceptable matches.
    
    Args:
        similarity: Similarity score from 0.0 to 1.0
    
    Returns:
        Score from 0.0 to 1.0
    """
    # Similarity >= 0.8 is considered acceptable
    if similarity >= 0.8:
        return similarity
    else:
        # Below threshold, penalize more heavily
        return similarity * 0.5
