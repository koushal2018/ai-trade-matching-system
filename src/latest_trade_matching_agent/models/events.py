"""
Event Message Schemas

This module defines standardized event message schemas for SQS-based
event-driven architecture with distributed tracing support.

Requirements: 3.1, 12.4
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class EventTaxonomy:
    """
    Standardized event types and their schemas.
    
    This taxonomy ensures consistent event naming across all agents
    and enables proper event routing and monitoring.
    
    Requirements:
        - 3.1: Define hierarchical workflow structure
        - 12.4: Support distributed tracing
    """
    
    # ========== Document Processing Events ==========
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    PDF_PROCESSED = "PDF_PROCESSED"
    OCR_COMPLETED = "OCR_COMPLETED"
    
    # ========== Extraction Events ==========
    EXTRACTION_STARTED = "EXTRACTION_STARTED"
    TRADE_EXTRACTED = "TRADE_EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    
    # ========== Matching Events ==========
    MATCHING_STARTED = "MATCHING_STARTED"
    MATCH_COMPLETED = "MATCH_COMPLETED"
    MATCHING_EXCEPTION = "MATCHING_EXCEPTION"
    
    # ========== Exception Events ==========
    EXCEPTION_RAISED = "EXCEPTION_RAISED"
    EXCEPTION_TRIAGED = "EXCEPTION_TRIAGED"
    EXCEPTION_DELEGATED = "EXCEPTION_DELEGATED"
    EXCEPTION_RESOLVED = "EXCEPTION_RESOLVED"
    
    # ========== HITL Events ==========
    HITL_REQUIRED = "HITL_REQUIRED"
    HITL_DECISION_MADE = "HITL_DECISION_MADE"
    
    # ========== Orchestration Events ==========
    SLA_VIOLATED = "SLA_VIOLATED"
    COMPLIANCE_CHECK_FAILED = "COMPLIANCE_CHECK_FAILED"
    CONTROL_COMMAND_ISSUED = "CONTROL_COMMAND_ISSUED"
    AGENT_HEALTH_CHANGED = "AGENT_HEALTH_CHANGED"
    
    # ========== System Events ==========
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_STOPPED = "AGENT_STOPPED"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"
    
    @classmethod
    def all_events(cls) -> list:
        """Get list of all event types."""
        return [
            value for name, value in vars(cls).items()
            if not name.startswith('_') and isinstance(value, str)
        ]
    
    @classmethod
    def is_valid_event(cls, event_type: str) -> bool:
        """Check if an event type is valid."""
        return event_type in cls.all_events()


class StandardEventMessage(BaseModel):
    """
    Standard schema for all SQS events.
    
    This schema ensures consistency across all event messages and enables
    distributed tracing via correlation_id.
    
    Requirements:
        - 3.1: Standardized event structure
        - 12.4: Distributed tracing with correlation_id
    
    Attributes:
        event_id: Unique identifier for this event
        event_type: Type of event (from EventTaxonomy)
        timestamp: When the event occurred (ISO 8601 format)
        source_agent: Agent that published the event
        correlation_id: Correlation ID for distributed tracing
        payload: Event-specific data
        metadata: Additional context
    """
    
    event_id: str = Field(
        ...,
        description="Unique identifier for this event",
        min_length=1
    )
    
    event_type: str = Field(
        ...,
        description="Type of event (from EventTaxonomy)"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the event occurred"
    )
    
    source_agent: str = Field(
        ...,
        description="Agent that published the event",
        min_length=1
    )
    
    correlation_id: str = Field(
        ...,
        description="Correlation ID for distributed tracing across agents",
        min_length=1
    )
    
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (e.g., user_id, file_size, confidence)"
    )
    
    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate that event_type is from EventTaxonomy."""
        if not EventTaxonomy.is_valid_event(v):
            raise ValueError(
                f"Invalid event_type: {v}. Must be from EventTaxonomy. "
                f"Valid types: {EventTaxonomy.all_events()}"
            )
        return v
    
    def to_sqs_message(self) -> str:
        """
        Serialize event to SQS message body (JSON string).
        
        Returns:
            JSON string suitable for SQS MessageBody
        """
        return self.model_dump_json()
    
    @classmethod
    def from_sqs_message(cls, message_body: str) -> "StandardEventMessage":
        """
        Deserialize event from SQS message body.
        
        Args:
            message_body: JSON string from SQS message
        
        Returns:
            StandardEventMessage instance
        """
        data = json.loads(message_body)
        return cls(**data)
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "event_id": "evt_123",
                    "event_type": "DOCUMENT_UPLOADED",
                    "timestamp": "2025-01-15T10:30:00Z",
                    "source_agent": "upload_service",
                    "correlation_id": "corr_abc",
                    "payload": {
                        "document_id": "doc_456",
                        "document_path": "s3://bucket/COUNTERPARTY/trade.pdf",
                        "source_type": "COUNTERPARTY"
                    },
                    "metadata": {
                        "user_id": "user_789",
                        "file_size_bytes": 245678
                    }
                },
                {
                    "event_id": "evt_124",
                    "event_type": "PDF_PROCESSED",
                    "timestamp": "2025-01-15T10:31:30Z",
                    "source_agent": "pdf_adapter_agent",
                    "correlation_id": "corr_abc",
                    "payload": {
                        "document_id": "doc_456",
                        "canonical_output_location": "s3://bucket/extracted/COUNTERPARTY/doc_456.json",
                        "page_count": 5,
                        "processing_time_ms": 8500
                    },
                    "metadata": {
                        "dpi": 300,
                        "ocr_confidence": 0.95
                    }
                },
                {
                    "event_id": "evt_125",
                    "event_type": "TRADE_EXTRACTED",
                    "timestamp": "2025-01-15T10:33:00Z",
                    "source_agent": "trade_extraction_agent",
                    "correlation_id": "corr_abc",
                    "payload": {
                        "trade_id": "GCS382857",
                        "source_type": "COUNTERPARTY",
                        "table_name": "CounterpartyTradeData"
                    },
                    "metadata": {
                        "extraction_confidence": 0.92,
                        "fields_extracted": 28
                    }
                }
            ]
        }


# ========== Specific Event Schemas ==========

class DocumentUploadedEvent(StandardEventMessage):
    """
    Event published when a document is uploaded to S3.
    
    Payload fields:
        - document_id: Unique document identifier
        - document_path: S3 URI of the uploaded document
        - source_type: BANK or COUNTERPARTY
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.DOCUMENT_UPLOADED
        super().__init__(**data)


class PDFProcessedEvent(StandardEventMessage):
    """
    Event published when PDF processing completes.
    
    Payload fields:
        - document_id: Unique document identifier
        - canonical_output_location: S3 URI of canonical output
        - page_count: Number of pages processed
        - processing_time_ms: Processing time in milliseconds
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.PDF_PROCESSED
        super().__init__(**data)


class TradeExtractedEvent(StandardEventMessage):
    """
    Event published when trade extraction completes.
    
    Payload fields:
        - trade_id: Unique trade identifier
        - source_type: BANK or COUNTERPARTY
        - table_name: DynamoDB table where trade was stored
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.TRADE_EXTRACTED
        super().__init__(**data)


class MatchCompletedEvent(StandardEventMessage):
    """
    Event published when trade matching completes.
    
    Payload fields:
        - trade_id: Unique trade identifier
        - classification: Match classification
        - match_score: Computed match score
        - decision_status: AUTO_MATCH, ESCALATE, or EXCEPTION
        - report_path: S3 URI of matching report
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.MATCH_COMPLETED
        super().__init__(**data)


class ExceptionRaisedEvent(StandardEventMessage):
    """
    Event published when an exception occurs.
    
    Payload fields:
        - exception_id: Unique exception identifier
        - exception_type: Type of exception
        - trade_id: Associated trade ID (if applicable)
        - error_message: Human-readable error message
        - reason_codes: List of reason codes
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.EXCEPTION_RAISED
        super().__init__(**data)


class HITLRequiredEvent(StandardEventMessage):
    """
    Event published when human review is required.
    
    Payload fields:
        - trade_id: Unique trade identifier
        - match_score: Computed match score
        - report_path: S3 URI of matching report
        - review_deadline: ISO timestamp for review deadline
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.HITL_REQUIRED
        super().__init__(**data)


class MatchingExceptionEvent(StandardEventMessage):
    """
    Event published when a matching exception occurs.
    
    Payload fields:
        - exception_id: Unique exception identifier
        - trade_id: Unique trade identifier
        - match_score: Computed match score
        - reason_codes: List of reason codes
        - report_path: S3 URI of matching report
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.MATCHING_EXCEPTION
        super().__init__(**data)


class HITLDecisionMadeEvent(StandardEventMessage):
    """
    Event published when a human makes a HITL decision.
    
    Payload fields:
        - trade_id: Unique trade identifier
        - review_id: Unique review identifier
        - decision: APPROVE or REJECT
        - user_id: User who made the decision
        - review_time_seconds: Time taken to review
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.HITL_DECISION_MADE
        super().__init__(**data)


class SLAViolatedEvent(StandardEventMessage):
    """
    Event published when an SLA is violated.
    
    Payload fields:
        - agent_id: Agent that violated SLA
        - sla_type: Type of SLA (processing_time, throughput, error_rate)
        - target_value: Target SLA value
        - actual_value: Actual measured value
        - violation_severity: LOW, MEDIUM, HIGH, CRITICAL
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.SLA_VIOLATED
        super().__init__(**data)


class ControlCommandIssuedEvent(StandardEventMessage):
    """
    Event published when orchestrator issues a control command.
    
    Payload fields:
        - command_type: Type of command (PAUSE, RESUME, ESCALATE, ADJUST_PRIORITY)
        - target_agent: Agent receiving the command
        - reason: Reason for the command
        - parameters: Command-specific parameters
    """
    
    def __init__(self, **data):
        if 'event_type' not in data:
            data['event_type'] = EventTaxonomy.CONTROL_COMMAND_ISSUED
        super().__init__(**data)


# ========== Event Factory ==========

class EventFactory:
    """
    Factory for creating event instances from event type.
    """
    
    _event_classes = {
        EventTaxonomy.DOCUMENT_UPLOADED: DocumentUploadedEvent,
        EventTaxonomy.PDF_PROCESSED: PDFProcessedEvent,
        EventTaxonomy.TRADE_EXTRACTED: TradeExtractedEvent,
        EventTaxonomy.MATCH_COMPLETED: MatchCompletedEvent,
        EventTaxonomy.MATCHING_EXCEPTION: MatchingExceptionEvent,
        EventTaxonomy.EXCEPTION_RAISED: ExceptionRaisedEvent,
        EventTaxonomy.HITL_REQUIRED: HITLRequiredEvent,
        EventTaxonomy.HITL_DECISION_MADE: HITLDecisionMadeEvent,
        EventTaxonomy.SLA_VIOLATED: SLAViolatedEvent,
        EventTaxonomy.CONTROL_COMMAND_ISSUED: ControlCommandIssuedEvent,
    }
    
    @classmethod
    def create_event(cls, event_type: str, **kwargs) -> StandardEventMessage:
        """
        Create an event instance based on event type.
        
        Args:
            event_type: Type of event from EventTaxonomy
            **kwargs: Event data
        
        Returns:
            Specific event instance or StandardEventMessage
        """
        event_class = cls._event_classes.get(event_type, StandardEventMessage)
        return event_class(event_type=event_type, **kwargs)
    
    @classmethod
    def from_sqs_message(cls, message_body: str) -> StandardEventMessage:
        """
        Create an event instance from SQS message body.
        
        Args:
            message_body: JSON string from SQS message
        
        Returns:
            Specific event instance or StandardEventMessage
        """
        data = json.loads(message_body)
        event_type = data.get('event_type')
        return cls.create_event(**data)


# ========== Event Validation Functions ==========

def validate_event_schema(event: StandardEventMessage) -> dict:
    """
    Validate that an event conforms to the standard schema.
    
    Args:
        event: Event to validate
    
    Returns:
        dict: Validation result with success status and any errors
        
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """
    errors = []
    
    # Check required fields
    if not event.event_id:
        errors.append("event_id is required")
    
    if not event.event_type:
        errors.append("event_type is required")
    elif not EventTaxonomy.is_valid_event(event.event_type):
        errors.append(f"Invalid event_type: {event.event_type}")
    
    if not event.source_agent:
        errors.append("source_agent is required")
    
    if not event.correlation_id:
        errors.append("correlation_id is required")
    
    # Check timestamp
    if not event.timestamp:
        errors.append("timestamp is required")
    
    # Check payload is a dict
    if not isinstance(event.payload, dict):
        errors.append("payload must be a dictionary")
    
    # Check metadata is a dict
    if not isinstance(event.metadata, dict):
        errors.append("metadata must be a dictionary")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def validate_event_payload(event: StandardEventMessage, required_fields: list) -> dict:
    """
    Validate that an event payload contains required fields.
    
    Args:
        event: Event to validate
        required_fields: List of required field names in payload
    
    Returns:
        dict: Validation result with success status and any errors
        
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """
    errors = []
    
    for field in required_fields:
        if field not in event.payload:
            errors.append(f"Required payload field missing: {field}")
        elif event.payload[field] is None:
            errors.append(f"Required payload field is None: {field}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def validate_document_uploaded_event(event: StandardEventMessage) -> dict:
    """
    Validate a DOCUMENT_UPLOADED event.
    
    Args:
        event: Event to validate
    
    Returns:
        dict: Validation result
        
    Validates: Requirements 3.2
    """
    # Check event type
    if event.event_type != EventTaxonomy.DOCUMENT_UPLOADED:
        return {
            "valid": False,
            "errors": [f"Expected event_type DOCUMENT_UPLOADED, got {event.event_type}"]
        }
    
    # Check required payload fields
    required_fields = ["document_id", "document_path", "source_type"]
    payload_validation = validate_event_payload(event, required_fields)
    
    if not payload_validation["valid"]:
        return payload_validation
    
    # Validate source_type
    source_type = event.payload.get("source_type")
    if source_type not in ["BANK", "COUNTERPARTY"]:
        return {
            "valid": False,
            "errors": [f"Invalid source_type: {source_type}. Must be BANK or COUNTERPARTY"]
        }
    
    return {"valid": True, "errors": []}


def validate_trade_extracted_event(event: StandardEventMessage) -> dict:
    """
    Validate a TRADE_EXTRACTED event.
    
    Args:
        event: Event to validate
    
    Returns:
        dict: Validation result
        
    Validates: Requirements 3.3
    """
    # Check event type
    if event.event_type != EventTaxonomy.TRADE_EXTRACTED:
        return {
            "valid": False,
            "errors": [f"Expected event_type TRADE_EXTRACTED, got {event.event_type}"]
        }
    
    # Check required payload fields
    required_fields = ["trade_id", "source_type", "table_name"]
    payload_validation = validate_event_payload(event, required_fields)
    
    if not payload_validation["valid"]:
        return payload_validation
    
    # Validate source_type
    source_type = event.payload.get("source_type")
    if source_type not in ["BANK", "COUNTERPARTY"]:
        return {
            "valid": False,
            "errors": [f"Invalid source_type: {source_type}. Must be BANK or COUNTERPARTY"]
        }
    
    # Validate table_name matches source_type
    table_name = event.payload.get("table_name")
    expected_table = "BankTradeData" if source_type == "BANK" else "CounterpartyTradeData"
    if table_name != expected_table:
        return {
            "valid": False,
            "errors": [f"Table name {table_name} does not match source_type {source_type}"]
        }
    
    return {"valid": True, "errors": []}


def validate_match_completed_event(event: StandardEventMessage) -> dict:
    """
    Validate a MATCH_COMPLETED event.
    
    Args:
        event: Event to validate
    
    Returns:
        dict: Validation result
        
    Validates: Requirements 3.4
    """
    # Check event type
    if event.event_type != EventTaxonomy.MATCH_COMPLETED:
        return {
            "valid": False,
            "errors": [f"Expected event_type MATCH_COMPLETED, got {event.event_type}"]
        }
    
    # Check required payload fields
    required_fields = ["trade_id", "classification", "match_score", "decision_status"]
    payload_validation = validate_event_payload(event, required_fields)
    
    if not payload_validation["valid"]:
        return payload_validation
    
    # Validate match_score range
    match_score = event.payload.get("match_score")
    if not isinstance(match_score, (int, float)) or not (0.0 <= match_score <= 1.0):
        return {
            "valid": False,
            "errors": [f"match_score must be between 0.0 and 1.0, got {match_score}"]
        }
    
    # Validate decision_status
    decision_status = event.payload.get("decision_status")
    if decision_status not in ["AUTO_MATCH", "ESCALATE", "EXCEPTION"]:
        return {
            "valid": False,
            "errors": [f"Invalid decision_status: {decision_status}"]
        }
    
    return {"valid": True, "errors": []}


def validate_exception_raised_event(event: StandardEventMessage) -> dict:
    """
    Validate an EXCEPTION_RAISED event.
    
    Args:
        event: Event to validate
    
    Returns:
        dict: Validation result
        
    Validates: Requirements 3.5
    """
    # Check event type
    if event.event_type != EventTaxonomy.EXCEPTION_RAISED:
        return {
            "valid": False,
            "errors": [f"Expected event_type EXCEPTION_RAISED, got {event.event_type}"]
        }
    
    # Check required payload fields
    required_fields = ["exception_id", "exception_type", "error_message"]
    payload_validation = validate_event_payload(event, required_fields)
    
    if not payload_validation["valid"]:
        return payload_validation
    
    # Check reason_codes is a list if present
    reason_codes = event.payload.get("reason_codes")
    if reason_codes is not None and not isinstance(reason_codes, list):
        return {
            "valid": False,
            "errors": ["reason_codes must be a list"]
        }
    
    return {"valid": True, "errors": []}
