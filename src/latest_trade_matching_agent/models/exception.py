"""
Exception and Triage Models

This module defines models for exception handling, triage classification,
and routing decisions with severity scoring.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ExceptionType(str, Enum):
    """Types of exceptions that can occur in the system."""
    PROCESSING_ERROR = "PROCESSING_ERROR"
    EXTRACTION_ERROR = "EXTRACTION_ERROR"
    MATCHING_EXCEPTION = "MATCHING_EXCEPTION"
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"
    SERVICE_ERROR = "SERVICE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class SeverityLevel(str, Enum):
    """
    Severity levels for exceptions.
    
    Requirements:
        - 8.2: Rank exceptions by severity
    """
    LOW = "LOW"  # Severity score < 0.3
    MEDIUM = "MEDIUM"  # Severity score 0.3-0.6
    HIGH = "HIGH"  # Severity score 0.6-0.8
    CRITICAL = "CRITICAL"  # Severity score > 0.8


class RoutingDestination(str, Enum):
    """
    Routing destinations for exception delegation.
    
    Requirements:
        - 8.3: Delegate to appropriate handlers
    """
    AUTO_RESOLVE = "AUTO_RESOLVE"  # System can auto-resolve
    OPS_DESK = "OPS_DESK"  # Operations desk
    SENIOR_OPS = "SENIOR_OPS"  # Senior operations team
    COMPLIANCE = "COMPLIANCE"  # Compliance team
    ENGINEERING = "ENGINEERING"  # Engineering team


class ResolutionStatus(str, Enum):
    """Status of exception resolution."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    FAILED = "FAILED"


class ReasonCodeTaxonomy:
    """
    Standardized reason codes for exceptions and mismatches.
    
    Requirements:
        - 7.2: Use reason codes for classification
        - 8.1: Log errors with context
    """
    # Matching Reason Codes
    NOTIONAL_MISMATCH = "NOTIONAL_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    COUNTERPARTY_MISMATCH = "COUNTERPARTY_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    PRODUCT_TYPE_MISMATCH = "PRODUCT_TYPE_MISMATCH"
    
    # Extraction Reason Codes
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_FORMAT = "INVALID_FIELD_FORMAT"
    AMBIGUOUS_FIELD_VALUE = "AMBIGUOUS_FIELD_VALUE"
    
    # Processing Reason Codes
    OCR_QUALITY_LOW = "OCR_QUALITY_LOW"
    PDF_CORRUPTED = "PDF_CORRUPTED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    
    # System Reason Codes
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Data Integrity Reason Codes
    MISPLACED_TRADE = "MISPLACED_TRADE"
    DUPLICATE_TRADE_ID = "DUPLICATE_TRADE_ID"
    INVALID_TRADE_SOURCE = "INVALID_TRADE_SOURCE"


class ExceptionRecord(BaseModel):
    """
    Record of an exception that occurred in the system.
    
    Requirements:
        - 8.1: Log all errors with full context
        - 8.4: Update audit trail when resolved
    
    Attributes:
        exception_id: Unique identifier for the exception
        timestamp: When the exception occurred
        exception_type: Type of exception
        event_type: Event type that triggered the exception
        trade_id: Associated trade ID (if applicable)
        agent_id: Agent that reported the exception
        match_score: Match score (if from matching)
        reason_codes: List of reason codes
        context: Full context of the exception
        error_message: Human-readable error message
        stack_trace: Stack trace (if available)
        retry_count: Number of retry attempts
        correlation_id: Correlation ID for distributed tracing
    """
    
    exception_id: str = Field(
        ...,
        description="Unique identifier for the exception",
        min_length=1
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the exception occurred"
    )
    
    exception_type: ExceptionType = Field(
        ...,
        description="Type of exception"
    )
    
    event_type: str = Field(
        ...,
        description="Event type that triggered the exception"
    )
    
    trade_id: Optional[str] = Field(
        None,
        description="Associated trade ID (if applicable)"
    )
    
    agent_id: str = Field(
        ...,
        description="Agent that reported the exception"
    )
    
    match_score: Optional[float] = Field(
        None,
        description="Match score (if from matching)",
        ge=0.0,
        le=1.0
    )
    
    reason_codes: List[str] = Field(
        default_factory=list,
        description="List of reason codes explaining the exception"
    )
    
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full context of the exception"
    )
    
    error_message: str = Field(
        ...,
        description="Human-readable error message"
    )
    
    stack_trace: Optional[str] = Field(
        None,
        description="Stack trace (if available)"
    )
    
    retry_count: int = Field(
        default=0,
        description="Number of retry attempts",
        ge=0
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for distributed tracing"
    )
    
    def to_state_vector(self) -> Dict[str, Any]:
        """
        Convert exception to state vector for RL model.
        
        Returns:
            Dictionary representing the state for RL
        """
        return {
            "exception_type": self.exception_type.value,
            "reason_codes": self.reason_codes,
            "match_score": self.match_score or 0.0,
            "retry_count": self.retry_count,
            "has_trade_id": self.trade_id is not None,
        }


class TriageClassification(str, Enum):
    """
    Classification for triage decisions.
    
    Requirements:
        - 8.2: Classify exceptions for triage
    """
    AUTO_RESOLVABLE = "AUTO_RESOLVABLE"
    OPERATIONAL_ISSUE = "OPERATIONAL_ISSUE"
    DATA_QUALITY_ISSUE = "DATA_QUALITY_ISSUE"
    SYSTEM_ISSUE = "SYSTEM_ISSUE"
    COMPLIANCE_ISSUE = "COMPLIANCE_ISSUE"


class TriageResult(BaseModel):
    """
    Result of exception triage with severity and routing.
    
    Requirements:
        - 8.2: Rank by severity and determine routing
        - 8.3: Delegate to appropriate handlers
    
    Attributes:
        exception_id: Reference to the exception
        severity: Severity level
        severity_score: Computed severity score (0.0 to 1.0)
        routing: Routing destination
        priority: Priority level (1=highest, 5=lowest)
        sla_hours: SLA for resolution in hours
        classification: Triage classification
        recommended_action: Recommended action to resolve
        assigned_to: User/team assigned to (if applicable)
        triage_timestamp: When triage was performed
    """
    
    exception_id: str = Field(
        ...,
        description="Reference to the exception",
        min_length=1
    )
    
    severity: SeverityLevel = Field(
        ...,
        description="Severity level"
    )
    
    severity_score: float = Field(
        ...,
        description="Computed severity score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    routing: RoutingDestination = Field(
        ...,
        description="Routing destination"
    )
    
    priority: int = Field(
        ...,
        description="Priority level (1=highest, 5=lowest)",
        ge=1,
        le=5
    )
    
    sla_hours: int = Field(
        ...,
        description="SLA for resolution in hours",
        gt=0
    )
    
    classification: TriageClassification = Field(
        ...,
        description="Triage classification"
    )
    
    recommended_action: Optional[str] = Field(
        None,
        description="Recommended action to resolve the exception"
    )
    
    assigned_to: Optional[str] = Field(
        None,
        description="User or team assigned to handle this exception"
    )
    
    triage_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When triage was performed"
    )
    
    @model_validator(mode='after')
    def validate_severity_and_priority(self) -> 'TriageResult':
        """
        Validate that severity level aligns with severity score and priority.
        
        Requirements:
            - Score < 0.3: LOW
            - Score 0.3-0.6: MEDIUM
            - Score 0.6-0.8: HIGH
            - Score > 0.8: CRITICAL
        """
        score = self.severity_score
        severity = self.severity
        priority = self.priority
        
        # Validate severity matches score
        if score < 0.3 and severity != SeverityLevel.LOW:
            raise ValueError(f"Severity score {score} < 0.3 should be LOW")
        elif 0.3 <= score < 0.6 and severity != SeverityLevel.MEDIUM:
            raise ValueError(f"Severity score {score} in [0.3, 0.6) should be MEDIUM")
        elif 0.6 <= score < 0.8 and severity != SeverityLevel.HIGH:
            raise ValueError(f"Severity score {score} in [0.6, 0.8) should be HIGH")
        elif score >= 0.8 and severity != SeverityLevel.CRITICAL:
            raise ValueError(f"Severity score {score} >= 0.8 should be CRITICAL")
        
        # Validate priority matches severity
        if severity == SeverityLevel.CRITICAL and priority > 1:
            raise ValueError("CRITICAL severity should have priority 1")
        elif severity == SeverityLevel.HIGH and priority > 2:
            raise ValueError("HIGH severity should have priority 1 or 2")
        
        return self
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "exception_id": "exc_123",
                    "severity": "HIGH",
                    "severity_score": 0.75,
                    "routing": "OPS_DESK",
                    "priority": 2,
                    "sla_hours": 4,
                    "classification": "OPERATIONAL_ISSUE",
                    "recommended_action": "Review trade data and correct notional mismatch",
                    "assigned_to": "ops_team_alpha"
                },
                {
                    "exception_id": "exc_456",
                    "severity": "CRITICAL",
                    "severity_score": 0.90,
                    "routing": "SENIOR_OPS",
                    "priority": 1,
                    "sla_hours": 2,
                    "classification": "COMPLIANCE_ISSUE",
                    "recommended_action": "Escalate counterparty mismatch to senior operations",
                    "assigned_to": "senior_ops_lead"
                }
            ]
        }


class DelegationResult(BaseModel):
    """
    Result of exception delegation.
    
    Requirements:
        - 8.3: Delegate exceptions to appropriate handlers
        - 8.4: Track exception lifecycle
    """
    
    exception_id: str = Field(
        ...,
        description="Reference to the exception"
    )
    
    status: str = Field(
        ...,
        description="Delegation status (DELEGATED, FAILED)"
    )
    
    assigned_to: str = Field(
        ...,
        description="User or team assigned to"
    )
    
    tracking_id: str = Field(
        ...,
        description="Tracking ID for the delegation"
    )
    
    queue_name: Optional[str] = Field(
        None,
        description="SQS queue name where the exception was sent"
    )
    
    sla_deadline: datetime = Field(
        ...,
        description="SLA deadline for resolution"
    )
    
    notification_sent: bool = Field(
        default=False,
        description="Whether notification was sent to assignee"
    )


class ResolutionOutcome(BaseModel):
    """
    Outcome of exception resolution for RL learning.
    
    Requirements:
        - 8.5: Learn from resolution patterns
    """
    
    exception_id: str = Field(
        ...,
        description="Reference to the exception"
    )
    
    resolved_at: datetime = Field(
        ...,
        description="When the exception was resolved"
    )
    
    resolution_time_hours: float = Field(
        ...,
        description="Time taken to resolve in hours",
        gt=0
    )
    
    resolved_within_sla: bool = Field(
        ...,
        description="Whether resolved within SLA"
    )
    
    routing_was_correct: bool = Field(
        ...,
        description="Whether the routing decision was correct"
    )
    
    human_decision: Optional[str] = Field(
        None,
        description="Human decision made during resolution"
    )
    
    resolution_notes: Optional[str] = Field(
        None,
        description="Notes about the resolution"
    )
