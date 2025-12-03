"""
Exception Severity Scoring System

This module implements severity scoring for exceptions based on reason codes,
match scores, and historical patterns from RL.

Requirements: 8.1, 8.2
"""

from typing import Optional, Dict, Any
from ..models.exception import ExceptionRecord, SeverityLevel
from ..models.taxonomy import ReasonCodeTaxonomy


def compute_severity_score(
    exception: ExceptionRecord,
    rl_adjustment: Optional[float] = None
) -> float:
    """
    Compute severity score (0.0 to 1.0) for an exception.
    
    The severity score is computed based on:
    1. Base scores from reason codes
    2. Adjustment based on match score (if available)
    3. Historical patterns from RL (if available)
    
    Args:
        exception: ExceptionRecord to score
        rl_adjustment: Optional RL-based adjustment (-0.2 to +0.2)
    
    Returns:
        float: Severity score between 0.0 and 1.0
        
    Requirements:
        - 8.1: Use base scores for reason codes
        - 8.2: Adjust based on match scores
        - 8.2: Integrate historical patterns from RL
    
    Examples:
        >>> exc = ExceptionRecord(
        ...     exception_id="exc_123",
        ...     exception_type=ExceptionType.MATCHING_EXCEPTION,
        ...     event_type="MATCHING_EXCEPTION",
        ...     agent_id="trade_matching_agent",
        ...     reason_codes=["NOTIONAL_MISMATCH"],
        ...     error_message="Notional mismatch detected",
        ...     match_score=0.65
        ... )
        >>> score = compute_severity_score(exc)
        >>> 0.0 <= score <= 1.0
        True
    """
    
    # Step 1: Get base score from reason codes
    base_score = _compute_base_score(exception.reason_codes)
    
    # Step 2: Adjust based on match score (if available)
    score = _adjust_for_match_score(base_score, exception.match_score)
    
    # Step 3: Adjust based on retry count (more retries = higher severity)
    score = _adjust_for_retry_count(score, exception.retry_count)
    
    # Step 4: Apply RL adjustment (if available)
    if rl_adjustment is not None:
        score = _apply_rl_adjustment(score, rl_adjustment)
    
    # Ensure score is in valid range [0.0, 1.0]
    score = max(0.0, min(1.0, score))
    
    # Round to 2 decimal places
    return round(score, 2)


def _compute_base_score(reason_codes: list) -> float:
    """
    Compute base severity score from reason codes.
    
    Uses the maximum severity score among all reason codes.
    
    Args:
        reason_codes: List of reason codes
    
    Returns:
        float: Base severity score
    """
    if not reason_codes:
        return 0.5  # Default to medium severity
    
    # Get severity score for each reason code
    scores = [
        ReasonCodeTaxonomy.get_base_severity_score(code)
        for code in reason_codes
    ]
    
    # Use maximum severity (most severe issue determines overall severity)
    return max(scores) if scores else 0.5


def _adjust_for_match_score(base_score: float, match_score: Optional[float]) -> float:
    """
    Adjust severity score based on match score.
    
    Lower match scores indicate more severe issues.
    
    Args:
        base_score: Base severity score
        match_score: Match score (0.0 to 1.0), if available
    
    Returns:
        float: Adjusted severity score
    """
    if match_score is None:
        return base_score
    
    # Lower match score = higher severity
    # Formula: adjusted_score = base_score * (1 + (1 - match_score) * 0.3)
    # This increases severity by up to 30% for very low match scores
    
    match_factor = (1 - match_score) * 0.3
    adjusted_score = base_score * (1 + match_factor)
    
    return adjusted_score


def _adjust_for_retry_count(score: float, retry_count: int) -> float:
    """
    Adjust severity score based on retry count.
    
    More retries indicate persistent issues that are harder to resolve.
    
    Args:
        score: Current severity score
        retry_count: Number of retry attempts
    
    Returns:
        float: Adjusted severity score
    """
    if retry_count == 0:
        return score
    
    # Increase severity by 5% per retry, up to 20% total increase
    retry_factor = min(retry_count * 0.05, 0.20)
    adjusted_score = score * (1 + retry_factor)
    
    return adjusted_score


def _apply_rl_adjustment(score: float, rl_adjustment: float) -> float:
    """
    Apply RL-based adjustment to severity score.
    
    RL adjustment is learned from historical resolution patterns.
    
    Args:
        score: Current severity score
        rl_adjustment: RL adjustment value (-0.2 to +0.2)
    
    Returns:
        float: Adjusted severity score
    """
    # Clamp RL adjustment to valid range
    rl_adjustment = max(-0.2, min(0.2, rl_adjustment))
    
    # Apply adjustment
    adjusted_score = score + rl_adjustment
    
    return adjusted_score


def get_severity_level(severity_score: float) -> SeverityLevel:
    """
    Convert severity score to severity level.
    
    Args:
        severity_score: Severity score (0.0 to 1.0)
    
    Returns:
        SeverityLevel: Severity level enum
        
    Mapping:
        - Score < 0.3: LOW
        - Score 0.3-0.6: MEDIUM
        - Score 0.6-0.8: HIGH
        - Score >= 0.8: CRITICAL
    """
    if severity_score < 0.3:
        return SeverityLevel.LOW
    elif severity_score < 0.6:
        return SeverityLevel.MEDIUM
    elif severity_score < 0.8:
        return SeverityLevel.HIGH
    else:
        return SeverityLevel.CRITICAL


def get_severity_description(severity_level: SeverityLevel) -> str:
    """
    Get human-readable description for a severity level.
    
    Args:
        severity_level: Severity level
    
    Returns:
        str: Description of the severity level
    """
    descriptions = {
        SeverityLevel.LOW: (
            "Low severity issue that can be handled with standard procedures. "
            "Minimal impact on operations."
        ),
        SeverityLevel.MEDIUM: (
            "Medium severity issue requiring attention within normal business hours. "
            "Moderate impact on operations."
        ),
        SeverityLevel.HIGH: (
            "High severity issue requiring prompt attention. "
            "Significant impact on operations or data quality."
        ),
        SeverityLevel.CRITICAL: (
            "Critical severity issue requiring immediate attention. "
            "Major impact on operations, compliance, or data integrity."
        ),
    }
    
    return descriptions.get(
        severity_level,
        f"Unknown severity level: {severity_level}"
    )


def compute_severity_breakdown(exception: ExceptionRecord) -> Dict[str, Any]:
    """
    Compute detailed severity breakdown for an exception.
    
    This provides transparency into how the severity score was calculated.
    
    Args:
        exception: ExceptionRecord to analyze
    
    Returns:
        dict: Detailed breakdown of severity calculation
    """
    # Compute base score
    base_score = _compute_base_score(exception.reason_codes)
    
    # Compute adjustments
    match_adjusted = _adjust_for_match_score(base_score, exception.match_score)
    match_adjustment = match_adjusted - base_score
    
    retry_adjusted = _adjust_for_retry_count(match_adjusted, exception.retry_count)
    retry_adjustment = retry_adjusted - match_adjusted
    
    # Final score
    final_score = round(retry_adjusted, 2)
    severity_level = get_severity_level(final_score)
    
    # Get reason code details
    reason_code_details = [
        {
            "code": code,
            "base_severity": ReasonCodeTaxonomy.get_base_severity_score(code),
            "category": ReasonCodeTaxonomy.get_reason_code_category(code),
            "description": ReasonCodeTaxonomy.get_reason_code_description(code)
        }
        for code in exception.reason_codes
    ]
    
    return {
        "exception_id": exception.exception_id,
        "final_score": final_score,
        "severity_level": severity_level.value,
        "breakdown": {
            "base_score": round(base_score, 2),
            "match_adjustment": round(match_adjustment, 2),
            "retry_adjustment": round(retry_adjustment, 2),
            "rl_adjustment": 0.0,  # Placeholder for RL adjustment
        },
        "factors": {
            "reason_codes": exception.reason_codes,
            "match_score": exception.match_score,
            "retry_count": exception.retry_count,
        },
        "reason_code_details": reason_code_details,
    }
