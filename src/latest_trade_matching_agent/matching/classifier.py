"""
Match Classification Logic

This module implements classification logic for match results based on
scores and reason codes.

Requirements:
    - 7.2: Classify results based on score thresholds
    - 7.3: Generate reason codes and determine decision status

Classification Thresholds:
    - Score >= 0.85: AUTO_MATCH (MATCHED classification)
    - Score 0.70-0.84: ESCALATE (PROBABLE_MATCH classification)
    - Score < 0.70: EXCEPTION (REVIEW_REQUIRED or BREAK classification)
"""

from typing import List, Optional, Tuple
from ..models.matching import (
    MatchClassification,
    DecisionStatus,
    MatchingResult,
    FieldDifference
)
from .fuzzy_matcher import MatchResult


# Reason code taxonomy
class ReasonCodes:
    """Standard reason codes for matching results."""
    
    # Matching reason codes
    NOTIONAL_MISMATCH = "NOTIONAL_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    COUNTERPARTY_MISMATCH = "COUNTERPARTY_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    PRODUCT_TYPE_MISMATCH = "PRODUCT_TYPE_MISMATCH"
    TRADE_ID_MISMATCH = "TRADE_ID_MISMATCH"
    
    # Data quality reason codes
    MISSING_BANK_TRADE = "MISSING_BANK_TRADE"
    MISSING_COUNTERPARTY_TRADE = "MISSING_COUNTERPARTY_TRADE"
    DATA_ERROR = "DATA_ERROR"
    
    # Tolerance reason codes
    WITHIN_DATE_TOLERANCE = "WITHIN_DATE_TOLERANCE"
    WITHIN_NOTIONAL_TOLERANCE = "WITHIN_NOTIONAL_TOLERANCE"
    FUZZY_COUNTERPARTY_MATCH = "FUZZY_COUNTERPARTY_MATCH"


def classify_match(
    match_score: float,
    match_result: MatchResult,
    trade_id: str,
    bank_trade: dict = None,
    counterparty_trade: dict = None
) -> Tuple[MatchClassification, DecisionStatus, List[str]]:
    """
    Classify match result based on score and generate reason codes.
    
    Classification Logic:
        - Score >= 0.85: MATCHED (AUTO_MATCH)
        - Score 0.70-0.84: PROBABLE_MATCH (ESCALATE)
        - Score 0.50-0.69: REVIEW_REQUIRED (EXCEPTION)
        - Score < 0.50: BREAK (EXCEPTION)
    
    Decision Status:
        - AUTO_MATCH: Score >= 0.85
        - ESCALATE: Score 0.70-0.84 (requires HITL)
        - EXCEPTION: Score < 0.70 (requires exception handling)
    
    Args:
        match_score: Computed match score (0.0 to 1.0)
        match_result: Result from fuzzy_match()
        trade_id: Trade identifier
        bank_trade: Bank trade data (optional, for data error detection)
        counterparty_trade: Counterparty trade data (optional, for data error detection)
    
    Returns:
        Tuple of (classification, decision_status, reason_codes)
    
    Requirements:
        - 7.2: Use score thresholds for classification
        - 7.3: Generate reason codes and decision status
    
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
        >>> classification, decision, codes = classify_match(0.95, result, "ABC123")
        >>> classification == MatchClassification.MATCHED
        True
        >>> decision == DecisionStatus.AUTO_MATCH
        True
    """
    reason_codes = []
    
    # Check for data errors first
    if bank_trade is None:
        reason_codes.append(ReasonCodes.MISSING_BANK_TRADE)
        return MatchClassification.DATA_ERROR, DecisionStatus.EXCEPTION, reason_codes
    
    if counterparty_trade is None:
        reason_codes.append(ReasonCodes.MISSING_COUNTERPARTY_TRADE)
        return MatchClassification.DATA_ERROR, DecisionStatus.EXCEPTION, reason_codes
    
    # Check for Trade_ID mismatch (critical error)
    if not match_result.trade_id_match:
        reason_codes.append(ReasonCodes.TRADE_ID_MISMATCH)
        return MatchClassification.DATA_ERROR, DecisionStatus.EXCEPTION, reason_codes
    
    # Generate reason codes based on differences
    reason_codes.extend(_generate_reason_codes(match_result))
    
    # Classify based on score
    if match_score >= 0.85:
        classification = MatchClassification.MATCHED
        decision_status = DecisionStatus.AUTO_MATCH
    elif match_score >= 0.70:
        classification = MatchClassification.PROBABLE_MATCH
        decision_status = DecisionStatus.ESCALATE
    elif match_score >= 0.50:
        classification = MatchClassification.REVIEW_REQUIRED
        decision_status = DecisionStatus.EXCEPTION
    else:
        classification = MatchClassification.BREAK
        decision_status = DecisionStatus.EXCEPTION
    
    return classification, decision_status, reason_codes


def create_matching_result(
    trade_id: str,
    match_score: float,
    match_result: Optional[MatchResult],
    bank_trade: dict = None,
    counterparty_trade: dict = None,
    report_path: str = None,
    matching_timestamp: str = None
) -> MatchingResult:
    """
    Create a complete MatchingResult from match score and fuzzy match result.
    
    This is a convenience function that combines classification, scoring,
    and result creation into a single operation.
    
    Args:
        trade_id: Trade identifier
        match_score: Computed match score
        match_result: Result from fuzzy_match() (optional, None if trades missing)
        bank_trade: Bank trade data (optional)
        counterparty_trade: Counterparty trade data (optional)
        report_path: S3 path to matching report (optional)
        matching_timestamp: ISO timestamp (optional)
    
    Returns:
        Complete MatchingResult object
    
    Requirements:
        - 7.2: Complete matching result with classification
        - 7.3: Include all required fields
    """
    # Create a dummy match_result if None
    if match_result is None:
        from .fuzzy_matcher import MatchResult
        match_result = MatchResult(
            trade_id_match=False,
            date_diff_days=None,
            notional_diff_pct=None,
            counterparty_similarity=None,
            currency_match=None,
            exact_matches={},
            differences=[]
        )
    
    # Classify the match
    classification, decision_status, reason_codes = classify_match(
        match_score,
        match_result,
        trade_id,
        bank_trade,
        counterparty_trade
    )
    
    # Convert match result differences to FieldDifference objects
    differences = [
        FieldDifference(
            field_name=diff["field_name"],
            bank_value=diff.get("bank_value"),
            counterparty_value=diff.get("counterparty_value"),
            difference_type=diff["difference_type"],
            tolerance_applied=diff.get("tolerance_applied", False),
            within_tolerance=diff.get("within_tolerance", False),
            percentage_difference=diff.get("percentage_difference")
        )
        for diff in match_result.differences
    ]
    
    # Determine if HITL is required
    requires_hitl = decision_status == DecisionStatus.ESCALATE
    
    # Compute confidence score (simplified)
    confidence_score = 1.0 if match_score >= 0.85 else 0.8 if match_score >= 0.70 else 0.6
    
    return MatchingResult(
        trade_id=trade_id,
        classification=classification,
        match_score=match_score,
        decision_status=decision_status,
        reason_codes=reason_codes,
        bank_trade=bank_trade,
        counterparty_trade=counterparty_trade,
        differences=differences,
        confidence_score=confidence_score,
        requires_hitl=requires_hitl,
        report_path=report_path,
        matching_timestamp=matching_timestamp
    )


def _generate_reason_codes(match_result: MatchResult) -> List[str]:
    """
    Generate reason codes based on match result differences.
    
    Args:
        match_result: Result from fuzzy_match()
    
    Returns:
        List of reason codes
    """
    codes = []
    
    # Check each field for mismatches
    for diff in match_result.differences:
        field_name = diff["field_name"]
        diff_type = diff["difference_type"]
        within_tolerance = diff.get("within_tolerance", False)
        
        if field_name == "trade_date":
            if within_tolerance:
                codes.append(ReasonCodes.WITHIN_DATE_TOLERANCE)
            else:
                codes.append(ReasonCodes.DATE_MISMATCH)
        
        elif field_name == "notional":
            if within_tolerance:
                codes.append(ReasonCodes.WITHIN_NOTIONAL_TOLERANCE)
            else:
                codes.append(ReasonCodes.NOTIONAL_MISMATCH)
        
        elif field_name == "counterparty":
            if diff_type == "FUZZY_MATCH":
                codes.append(ReasonCodes.FUZZY_COUNTERPARTY_MATCH)
            else:
                codes.append(ReasonCodes.COUNTERPARTY_MISMATCH)
        
        elif field_name == "currency":
            codes.append(ReasonCodes.CURRENCY_MISMATCH)
        
        elif field_name == "product_type":
            codes.append(ReasonCodes.PRODUCT_TYPE_MISMATCH)
        
        elif field_name == "Trade_ID":
            codes.append(ReasonCodes.TRADE_ID_MISMATCH)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_codes = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)
    
    return unique_codes


def check_data_integrity(bank_trade: dict, counterparty_trade: dict) -> Tuple[bool, List[str]]:
    """
    Check data integrity for misplaced trades.
    
    Verifies that:
    - Bank trade has TRADE_SOURCE="BANK"
    - Counterparty trade has TRADE_SOURCE="COUNTERPARTY"
    
    Args:
        bank_trade: Trade from BankTradeData table
        counterparty_trade: Trade from CounterpartyTradeData table
    
    Returns:
        Tuple of (is_valid, error_codes)
    
    Requirements:
        - 7.5: Flag misplaced trades as DATA_ERROR
    """
    errors = []
    
    # Extract TRADE_SOURCE from both trades
    bank_source = _extract_trade_source(bank_trade)
    cp_source = _extract_trade_source(counterparty_trade)
    
    # Check bank trade
    if bank_source and bank_source != "BANK":
        errors.append(f"MISPLACED_TRADE_IN_BANK_TABLE: TRADE_SOURCE={bank_source}")
    
    # Check counterparty trade
    if cp_source and cp_source != "COUNTERPARTY":
        errors.append(f"MISPLACED_TRADE_IN_CP_TABLE: TRADE_SOURCE={cp_source}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def _extract_trade_source(trade: dict) -> str:
    """
    Extract TRADE_SOURCE from trade dictionary.
    
    Handles both regular dict and DynamoDB typed format.
    
    Args:
        trade: Trade dictionary
    
    Returns:
        TRADE_SOURCE value or None
    """
    if not trade:
        return None
    
    if "TRADE_SOURCE" not in trade:
        return None
    
    value = trade["TRADE_SOURCE"]
    
    # Handle DynamoDB typed format
    if isinstance(value, dict) and "S" in value:
        return value["S"]
    
    return value
