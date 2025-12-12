"""
Exception Classification Logic

This module implements exception classification based on reason codes,
exception types, and context.

Requirements: 8.1
"""

from typing import Dict, Any
from ..models.exception import (
    ExceptionRecord,
    ExceptionType,
    TriageClassification,
    ReasonCodeTaxonomy
)
from ..models.taxonomy import ReasonCodeTaxonomy as TaxonomyReasonCodes


def classify_exception(exception: ExceptionRecord) -> TriageClassification:
    """
    Classify an exception based on its type, reason codes, and context.
    
    This function analyzes the exception and determines its triage classification,
    which will be used for routing and prioritization decisions.
    
    Args:
        exception: ExceptionRecord to classify
    
    Returns:
        TriageClassification: Classification result
        
    Requirements:
        - 8.1: Use reason codes for classification
        - 8.1: Support all exception types
    
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
        >>> classification = classify_exception(exc)
        >>> classification
        <TriageClassification.OPERATIONAL_ISSUE: 'OPERATIONAL_ISSUE'>
    """
    
    # Get reason code analysis
    reason_codes = exception.reason_codes
    exception_type = exception.exception_type
    
    # Classify based on reason codes and exception type
    if not reason_codes:
        # No reason codes - classify by exception type
        return _classify_by_exception_type(exception_type)
    
    # Analyze reason codes
    primary_category = _get_primary_reason_category(reason_codes)
    
    # Determine triage classification
    if primary_category == "MATCHING":
        return TriageClassification.OPERATIONAL_ISSUE
    
    elif primary_category == "DATA_ERROR":
        # Check for specific data integrity issues
        if any(code in reason_codes for code in [
            TaxonomyReasonCodes.MISPLACED_TRADE,
            TaxonomyReasonCodes.DUPLICATE_TRADE_ID
        ]):
            return TriageClassification.DATA_QUALITY_ISSUE
        return TriageClassification.DATA_QUALITY_ISSUE
    
    elif primary_category == "PROCESSING":
        return TriageClassification.SYSTEM_ISSUE
    
    elif primary_category == "SYSTEM":
        # Check for authentication/authorization issues (compliance)
        if any(code in reason_codes for code in [
            TaxonomyReasonCodes.AUTHENTICATION_FAILED,
            TaxonomyReasonCodes.AUTHORIZATION_FAILED
        ]):
            return TriageClassification.COMPLIANCE_ISSUE
        return TriageClassification.SYSTEM_ISSUE
    
    elif primary_category == "BUSINESS_LOGIC":
        # Check if it's auto-resolvable
        if _is_auto_resolvable(reason_codes, exception):
            return TriageClassification.AUTO_RESOLVABLE
        return TriageClassification.OPERATIONAL_ISSUE
    
    else:
        # Unknown category - default to operational issue
        return TriageClassification.OPERATIONAL_ISSUE


def _classify_by_exception_type(exception_type: ExceptionType) -> TriageClassification:
    """
    Classify exception when no reason codes are available.
    
    Args:
        exception_type: Type of exception
    
    Returns:
        TriageClassification: Classification based on exception type
    """
    classification_map = {
        ExceptionType.PROCESSING_ERROR: TriageClassification.SYSTEM_ISSUE,
        ExceptionType.EXTRACTION_ERROR: TriageClassification.SYSTEM_ISSUE,
        ExceptionType.MATCHING_EXCEPTION: TriageClassification.OPERATIONAL_ISSUE,
        ExceptionType.DATA_INTEGRITY_ERROR: TriageClassification.DATA_QUALITY_ISSUE,
        ExceptionType.SERVICE_ERROR: TriageClassification.SYSTEM_ISSUE,
        ExceptionType.VALIDATION_ERROR: TriageClassification.DATA_QUALITY_ISSUE,
    }
    
    return classification_map.get(exception_type, TriageClassification.OPERATIONAL_ISSUE)


def _get_primary_reason_category(reason_codes: list) -> str:
    """
    Get the primary category for a list of reason codes.
    
    Args:
        reason_codes: List of reason codes
    
    Returns:
        str: Primary category (MATCHING, DATA_ERROR, PROCESSING, SYSTEM, BUSINESS_LOGIC)
    """
    if not reason_codes:
        return "UNKNOWN"
    
    # Count codes by category
    category_counts: Dict[str, int] = {}
    
    for code in reason_codes:
        category = TaxonomyReasonCodes.get_reason_code_category(code)
        category_counts[category] = category_counts.get(category, 0) + 1
    
    # Return category with most codes
    if not category_counts:
        return "UNKNOWN"
    
    return max(category_counts.items(), key=lambda x: x[1])[0]


def _is_auto_resolvable(reason_codes: list, exception: ExceptionRecord) -> bool:
    """
    Determine if an exception is auto-resolvable based on reason codes and context.
    
    Args:
        reason_codes: List of reason codes
        exception: Exception record
    
    Returns:
        bool: True if auto-resolvable, False otherwise
    """
    # Auto-resolvable conditions:
    # 1. Low severity transient errors (rate limits, timeouts)
    # 2. Low confidence matches that can be retried
    # 3. Minor field mismatches with high match scores
    
    auto_resolvable_codes = [
        TaxonomyReasonCodes.RATE_LIMIT_EXCEEDED,
        TaxonomyReasonCodes.TIMEOUT,
        TaxonomyReasonCodes.NETWORK_ERROR,
        TaxonomyReasonCodes.CONFIDENCE_TOO_LOW,
    ]
    
    # Check if all reason codes are auto-resolvable
    if all(code in auto_resolvable_codes for code in reason_codes):
        return True
    
    # Check if match score is high enough for auto-resolution
    if exception.match_score is not None and exception.match_score >= 0.80:
        # High match score with minor mismatches can be auto-resolved
        minor_mismatch_codes = [
            TaxonomyReasonCodes.COMMODITY_TYPE_MISMATCH,
            TaxonomyReasonCodes.SETTLEMENT_TYPE_MISMATCH,
        ]
        if all(code in minor_mismatch_codes for code in reason_codes):
            return True
    
    # Check retry count - if already retried multiple times, not auto-resolvable
    if exception.retry_count >= 3:
        return False
    
    return False


def get_classification_description(classification: TriageClassification) -> str:
    """
    Get human-readable description for a triage classification.
    
    Args:
        classification: Triage classification
    
    Returns:
        str: Description of the classification
    """
    descriptions = {
        TriageClassification.AUTO_RESOLVABLE: (
            "Exception can be automatically resolved by the system through retry or "
            "automated correction mechanisms."
        ),
        TriageClassification.OPERATIONAL_ISSUE: (
            "Exception requires operational review and manual intervention to resolve "
            "trade matching or processing issues."
        ),
        TriageClassification.DATA_QUALITY_ISSUE: (
            "Exception is caused by data quality problems such as missing fields, "
            "invalid formats, or data integrity violations."
        ),
        TriageClassification.SYSTEM_ISSUE: (
            "Exception is caused by system-level problems such as service failures, "
            "processing errors, or infrastructure issues."
        ),
        TriageClassification.COMPLIANCE_ISSUE: (
            "Exception involves compliance, security, or authorization concerns that "
            "require immediate attention from compliance team."
        ),
    }
    
    return descriptions.get(
        classification,
        f"Unknown classification: {classification}"
    )
