"""
Exception Triage System

This module implements triage logic for exceptions, determining severity,
routing, priority, and SLA based on severity scores and RL policies.

Requirements: 8.2, 8.3
"""

from datetime import datetime
from typing import Optional, Dict, Any
from ..models.exception import (
    ExceptionRecord,
    TriageResult,
    TriageClassification,
    SeverityLevel,
    RoutingDestination
)
from ..models.taxonomy import ReasonCodeTaxonomy
from .classifier import classify_exception
from .scorer import compute_severity_score, get_severity_level


def triage_exception(
    exception: ExceptionRecord,
    severity_score: Optional[float] = None,
    rl_policy: Optional[Any] = None
) -> TriageResult:
    """
    Triage an exception to determine severity, routing, priority, and SLA.
    
    This function performs comprehensive triage analysis including:
    1. Classification of the exception type
    2. Severity scoring
    3. Routing determination (with optional RL policy)
    4. Priority assignment
    5. SLA calculation
    
    Args:
        exception: ExceptionRecord to triage
        severity_score: Pre-computed severity score (optional)
        rl_policy: Optional RL policy for routing decisions
    
    Returns:
        TriageResult: Complete triage result with routing and SLA
        
    Requirements:
        - 8.2: Determine severity (LOW, MEDIUM, HIGH, CRITICAL)
        - 8.2: Determine routing (AUTO_RESOLVE, OPS_DESK, SENIOR_OPS, COMPLIANCE, ENGINEERING)
        - 8.2: Set priority and SLA hours
        - 8.3: Integrate RL policy for routing decisions
    
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
        >>> result = triage_exception(exc)
        >>> result.severity in [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        True
    """
    
    # Step 1: Classify the exception
    classification = classify_exception(exception)
    
    # Step 2: Compute severity score if not provided
    if severity_score is None:
        severity_score = compute_severity_score(exception)
    
    # Step 3: Determine severity level
    severity = get_severity_level(severity_score)
    
    # Step 4: Determine routing (with optional RL policy)
    routing = _determine_routing(
        exception=exception,
        severity_score=severity_score,
        severity=severity,
        classification=classification,
        rl_policy=rl_policy
    )
    
    # Step 5: Determine priority based on severity
    priority = _determine_priority(severity, classification)
    
    # Step 6: Determine SLA hours based on severity and routing
    sla_hours = _determine_sla_hours(severity, routing)
    
    # Step 7: Generate recommended action
    recommended_action = _generate_recommended_action(
        exception, classification, severity, routing
    )
    
    # Step 8: Determine assignment (if applicable)
    assigned_to = _determine_assignment(routing, classification)
    
    # Create triage result
    return TriageResult(
        exception_id=exception.exception_id,
        severity=severity,
        severity_score=severity_score,
        routing=routing,
        priority=priority,
        sla_hours=sla_hours,
        classification=classification,
        recommended_action=recommended_action,
        assigned_to=assigned_to,
        triage_timestamp=datetime.utcnow()
    )


def _determine_routing(
    exception: ExceptionRecord,
    severity_score: float,
    severity: SeverityLevel,
    classification: TriageClassification,
    rl_policy: Optional[Any] = None
) -> RoutingDestination:
    """
    Determine routing destination for an exception.
    
    Uses business rules and optional RL policy for optimal routing.
    
    Args:
        exception: Exception record
        severity_score: Computed severity score
        severity: Severity level
        classification: Triage classification
        rl_policy: Optional RL policy
    
    Returns:
        RoutingDestination: Where to route the exception
    """
    
    # Rule 1: Auto-resolvable exceptions
    if classification == TriageClassification.AUTO_RESOLVABLE:
        return RoutingDestination.AUTO_RESOLVE
    
    # Rule 2: Critical severity or compliance issues -> SENIOR_OPS
    if severity == SeverityLevel.CRITICAL or classification == TriageClassification.COMPLIANCE_ISSUE:
        return RoutingDestination.SENIOR_OPS
    
    # Rule 3: Authentication/Authorization failures -> COMPLIANCE
    if any(code in exception.reason_codes for code in [
        ReasonCodeTaxonomy.AUTHENTICATION_FAILED,
        ReasonCodeTaxonomy.AUTHORIZATION_FAILED
    ]):
        return RoutingDestination.COMPLIANCE
    
    # Rule 4: High severity matching issues -> OPS_DESK
    if severity == SeverityLevel.HIGH and classification == TriageClassification.OPERATIONAL_ISSUE:
        return RoutingDestination.OPS_DESK
    
    # Rule 5: Data quality issues -> OPS_DESK
    if classification == TriageClassification.DATA_QUALITY_ISSUE:
        return RoutingDestination.OPS_DESK
    
    # Rule 6: System issues -> ENGINEERING
    if classification == TriageClassification.SYSTEM_ISSUE:
        return RoutingDestination.ENGINEERING
    
    # Rule 7: Use RL policy if available
    if rl_policy is not None:
        rl_routing = _get_rl_routing(exception, rl_policy)
        if rl_routing is not None:
            return rl_routing
    
    # Rule 8: Medium severity -> OPS_DESK
    if severity == SeverityLevel.MEDIUM:
        return RoutingDestination.OPS_DESK
    
    # Rule 9: Low severity -> AUTO_RESOLVE
    if severity == SeverityLevel.LOW:
        return RoutingDestination.AUTO_RESOLVE
    
    # Default: OPS_DESK
    return RoutingDestination.OPS_DESK


def _get_rl_routing(exception: ExceptionRecord, rl_policy: Any) -> Optional[RoutingDestination]:
    """
    Get routing recommendation from RL policy.
    
    Args:
        exception: Exception record
        rl_policy: RL policy object
    
    Returns:
        Optional[RoutingDestination]: RL-recommended routing, or None if not available
    """
    try:
        # Convert exception to state vector
        state = exception.to_state_vector()
        
        # Get prediction from RL policy
        if hasattr(rl_policy, 'predict'):
            prediction = rl_policy.predict(state)
            
            # Convert prediction to RoutingDestination
            routing_map = {
                "AUTO_RESOLVE": RoutingDestination.AUTO_RESOLVE,
                "OPS_DESK": RoutingDestination.OPS_DESK,
                "SENIOR_OPS": RoutingDestination.SENIOR_OPS,
                "COMPLIANCE": RoutingDestination.COMPLIANCE,
                "ENGINEERING": RoutingDestination.ENGINEERING,
            }
            
            return routing_map.get(prediction)
    except Exception:
        # If RL policy fails, return None to fall back to business rules
        return None
    
    return None


def _determine_priority(severity: SeverityLevel, classification: TriageClassification) -> int:
    """
    Determine priority level (1=highest, 5=lowest) based on severity and classification.
    
    Args:
        severity: Severity level
        classification: Triage classification
    
    Returns:
        int: Priority level (1-5)
    """
    # Priority mapping based on severity
    priority_map = {
        SeverityLevel.CRITICAL: 1,
        SeverityLevel.HIGH: 2,
        SeverityLevel.MEDIUM: 3,
        SeverityLevel.LOW: 4,
    }
    
    base_priority = priority_map.get(severity, 3)
    
    # Adjust priority for compliance issues (always priority 1)
    if classification == TriageClassification.COMPLIANCE_ISSUE:
        return 1
    
    # Adjust priority for auto-resolvable (always priority 5)
    if classification == TriageClassification.AUTO_RESOLVABLE:
        return 5
    
    return base_priority


def _determine_sla_hours(severity: SeverityLevel, routing: RoutingDestination) -> int:
    """
    Determine SLA hours based on severity and routing.
    
    Args:
        severity: Severity level
        routing: Routing destination
    
    Returns:
        int: SLA in hours
    """
    # Base SLA by severity
    sla_map = {
        SeverityLevel.CRITICAL: 2,   # 2 hours
        SeverityLevel.HIGH: 4,       # 4 hours
        SeverityLevel.MEDIUM: 8,     # 8 hours
        SeverityLevel.LOW: 24,       # 24 hours
    }
    
    base_sla = sla_map.get(severity, 8)
    
    # Adjust SLA for auto-resolve (shorter SLA)
    if routing == RoutingDestination.AUTO_RESOLVE:
        return min(base_sla, 1)  # Max 1 hour for auto-resolve
    
    # Adjust SLA for compliance (always 2 hours)
    if routing == RoutingDestination.COMPLIANCE:
        return 2
    
    # Adjust SLA for engineering (longer SLA for system issues)
    if routing == RoutingDestination.ENGINEERING:
        return base_sla * 2  # Double the SLA for engineering issues
    
    return base_sla


def _generate_recommended_action(
    exception: ExceptionRecord,
    classification: TriageClassification,
    severity: SeverityLevel,
    routing: RoutingDestination
) -> str:
    """
    Generate recommended action for resolving the exception.
    
    Args:
        exception: Exception record
        classification: Triage classification
        severity: Severity level
        routing: Routing destination
    
    Returns:
        str: Recommended action description
    """
    # Get primary reason code
    primary_reason = exception.reason_codes[0] if exception.reason_codes else None
    
    if not primary_reason:
        return f"Review exception and determine appropriate resolution for {classification.value}"
    
    # Get reason code description
    reason_description = ReasonCodeTaxonomy.get_reason_code_description(primary_reason)
    
    # Generate action based on classification and routing
    if classification == TriageClassification.AUTO_RESOLVABLE:
        return f"Automatically retry operation. Issue: {reason_description}"
    
    elif classification == TriageClassification.OPERATIONAL_ISSUE:
        if "MISMATCH" in primary_reason:
            return f"Review trade data and resolve mismatch. Issue: {reason_description}"
        return f"Review and correct operational issue. Issue: {reason_description}"
    
    elif classification == TriageClassification.DATA_QUALITY_ISSUE:
        return f"Investigate and correct data quality issue. Issue: {reason_description}"
    
    elif classification == TriageClassification.SYSTEM_ISSUE:
        return f"Investigate system issue and apply fix. Issue: {reason_description}"
    
    elif classification == TriageClassification.COMPLIANCE_ISSUE:
        return f"Escalate to compliance team immediately. Issue: {reason_description}"
    
    else:
        return f"Review exception and determine resolution. Issue: {reason_description}"


def _determine_assignment(
    routing: RoutingDestination,
    classification: TriageClassification
) -> Optional[str]:
    """
    Determine initial assignment for the exception.
    
    Args:
        routing: Routing destination
        classification: Triage classification
    
    Returns:
        Optional[str]: Team or user to assign to
    """
    assignment_map = {
        RoutingDestination.AUTO_RESOLVE: "system_auto_resolver",
        RoutingDestination.OPS_DESK: "ops_team",
        RoutingDestination.SENIOR_OPS: "senior_ops_team",
        RoutingDestination.COMPLIANCE: "compliance_team",
        RoutingDestination.ENGINEERING: "engineering_team",
    }
    
    return assignment_map.get(routing)


def get_triage_summary(triage_result: TriageResult) -> Dict[str, Any]:
    """
    Get human-readable summary of triage result.
    
    Args:
        triage_result: Triage result
    
    Returns:
        dict: Summary of triage decision
    """
    return {
        "exception_id": triage_result.exception_id,
        "severity": {
            "level": triage_result.severity.value,
            "score": triage_result.severity_score,
        },
        "routing": {
            "destination": triage_result.routing.value,
            "assigned_to": triage_result.assigned_to,
        },
        "priority": {
            "level": triage_result.priority,
            "description": _get_priority_description(triage_result.priority),
        },
        "sla": {
            "hours": triage_result.sla_hours,
            "deadline": _calculate_deadline(triage_result.triage_timestamp, triage_result.sla_hours),
        },
        "classification": triage_result.classification.value,
        "recommended_action": triage_result.recommended_action,
        "triage_timestamp": triage_result.triage_timestamp.isoformat(),
    }


def _get_priority_description(priority: int) -> str:
    """Get description for priority level."""
    descriptions = {
        1: "Critical - Immediate attention required",
        2: "High - Prompt attention required",
        3: "Medium - Normal attention required",
        4: "Low - Can be handled in due course",
        5: "Lowest - Automated handling",
    }
    return descriptions.get(priority, f"Priority {priority}")


def _calculate_deadline(triage_timestamp: datetime, sla_hours: int) -> str:
    """Calculate SLA deadline."""
    from datetime import timedelta
    deadline = triage_timestamp + timedelta(hours=sla_hours)
    return deadline.isoformat()
