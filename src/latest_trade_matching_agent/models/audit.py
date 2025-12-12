"""
Audit Trail Models

This module defines models for audit trail records with immutable hashing
and tamper-evidence verification.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    """
    Types of actions that can be audited.
    
    Requirements:
        - 10.2: Include action type in audit records
    """
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    PDF_PROCESSED = "PDF_PROCESSED"
    TRADE_EXTRACTED = "TRADE_EXTRACTED"
    TRADE_MATCHED = "TRADE_MATCHED"
    EXCEPTION_RAISED = "EXCEPTION_RAISED"
    EXCEPTION_RESOLVED = "EXCEPTION_RESOLVED"
    HITL_DECISION = "HITL_DECISION"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_STOPPED = "AGENT_STOPPED"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    DATA_EXPORTED = "DATA_EXPORTED"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class ActionOutcome(str, Enum):
    """
    Outcome of an audited action.
    
    Requirements:
        - 10.2: Include outcome in audit records
    """
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    PENDING = "PENDING"


class ExportFormat(str, Enum):
    """
    Supported export formats for audit trails.
    
    Requirements:
        - 10.5: Export audit trails in standard formats
    """
    JSON = "JSON"
    CSV = "CSV"
    XML = "XML"


class AuditRecord(BaseModel):
    """
    Immutable audit record with tamper-evidence.
    
    Requirements:
        - 10.1: Record all system operations
        - 10.2: Include timestamp, agent ID, action type, and outcome
        - 10.3: Support filtering by date, agent, and action type
        - 10.4: Ensure immutability and tamper-evidence
        - 10.5: Export in standard formats
    
    Attributes:
        record_id: Unique identifier for the audit record
        timestamp: When the action occurred (ISO 8601 format)
        agent_id: ID of the agent that performed the action
        action_type: Type of action performed
        resource_id: ID of the resource affected (e.g., trade_id, document_id)
        outcome: Outcome of the action
        user_id: ID of the user (if human-initiated)
        details: Additional details about the action
        immutable_hash: SHA-256 hash for tamper-evidence
        previous_hash: Hash of the previous audit record (blockchain-style)
        correlation_id: Correlation ID for distributed tracing
    """
    
    record_id: str = Field(
        ...,
        description="Unique identifier for the audit record",
        min_length=1
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the action occurred"
    )
    
    agent_id: str = Field(
        ...,
        description="ID of the agent that performed the action",
        min_length=1
    )
    
    action_type: ActionType = Field(
        ...,
        description="Type of action performed"
    )
    
    resource_id: Optional[str] = Field(
        None,
        description="ID of the resource affected (e.g., trade_id, document_id)"
    )
    
    outcome: ActionOutcome = Field(
        ...,
        description="Outcome of the action"
    )
    
    user_id: Optional[str] = Field(
        None,
        description="ID of the user (if human-initiated)"
    )
    
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details about the action"
    )
    
    immutable_hash: str = Field(
        default="",
        description="SHA-256 hash for tamper-evidence"
    )
    
    previous_hash: Optional[str] = Field(
        None,
        description="Hash of the previous audit record (blockchain-style)"
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for distributed tracing"
    )
    
    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of the audit record for tamper-evidence.
        
        The hash is computed over all fields except immutable_hash itself.
        This ensures that any modification to the record will be detected.
        
        Requirements:
            - 10.4: Implement SHA-256 hash computation
        
        Returns:
            SHA-256 hash as hexadecimal string
        """
        # Create a dictionary of all fields except immutable_hash
        hash_data = {
            "record_id": self.record_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "action_type": self.action_type.value,
            "resource_id": self.resource_id,
            "outcome": self.outcome.value,
            "user_id": self.user_id,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "correlation_id": self.correlation_id,
        }
        
        # Convert to JSON string with sorted keys for consistency
        json_str = json.dumps(hash_data, sort_keys=True, default=str)
        
        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def verify_hash(self) -> bool:
        """
        Verify that the immutable_hash matches the computed hash.
        
        This detects any tampering with the audit record.
        
        Requirements:
            - 10.4: Add tamper-evidence verification
        
        Returns:
            True if hash is valid, False if tampered
        """
        if not self.immutable_hash:
            return False
        
        computed_hash = self.compute_hash()
        return computed_hash == self.immutable_hash
    
    def finalize(self) -> None:
        """
        Finalize the audit record by computing and setting the immutable hash.
        
        This should be called before storing the record to make it immutable.
        """
        self.immutable_hash = self.compute_hash()
    
    def to_json(self) -> str:
        """
        Export audit record as JSON.
        
        Requirements:
            - 10.5: Support JSON export format
        
        Returns:
            JSON string representation
        """
        return self.model_dump_json(indent=2)
    
    def to_csv_row(self) -> List[str]:
        """
        Export audit record as CSV row.
        
        Requirements:
            - 10.5: Support CSV export format
        
        Returns:
            List of string values for CSV row
        """
        return [
            self.record_id,
            self.timestamp.isoformat(),
            self.agent_id,
            self.action_type.value,
            self.resource_id or "",
            self.outcome.value,
            self.user_id or "",
            json.dumps(self.details),
            self.immutable_hash,
            self.previous_hash or "",
            self.correlation_id or "",
        ]
    
    def to_xml(self) -> str:
        """
        Export audit record as XML.
        
        Requirements:
            - 10.5: Support XML export format
        
        Returns:
            XML string representation
        """
        xml_parts = ['<AuditRecord>']
        xml_parts.append(f'  <RecordId>{self.record_id}</RecordId>')
        xml_parts.append(f'  <Timestamp>{self.timestamp.isoformat()}</Timestamp>')
        xml_parts.append(f'  <AgentId>{self.agent_id}</AgentId>')
        xml_parts.append(f'  <ActionType>{self.action_type.value}</ActionType>')
        
        if self.resource_id:
            xml_parts.append(f'  <ResourceId>{self.resource_id}</ResourceId>')
        
        xml_parts.append(f'  <Outcome>{self.outcome.value}</Outcome>')
        
        if self.user_id:
            xml_parts.append(f'  <UserId>{self.user_id}</UserId>')
        
        if self.details:
            xml_parts.append('  <Details>')
            for key, value in self.details.items():
                xml_parts.append(f'    <{key}>{value}</{key}>')
            xml_parts.append('  </Details>')
        
        xml_parts.append(f'  <ImmutableHash>{self.immutable_hash}</ImmutableHash>')
        
        if self.previous_hash:
            xml_parts.append(f'  <PreviousHash>{self.previous_hash}</PreviousHash>')
        
        if self.correlation_id:
            xml_parts.append(f'  <CorrelationId>{self.correlation_id}</CorrelationId>')
        
        xml_parts.append('</AuditRecord>')
        return '\n'.join(xml_parts)
    
    @classmethod
    def csv_header(cls) -> List[str]:
        """
        Get CSV header row.
        
        Returns:
            List of column names
        """
        return [
            "record_id",
            "timestamp",
            "agent_id",
            "action_type",
            "resource_id",
            "outcome",
            "user_id",
            "details",
            "immutable_hash",
            "previous_hash",
            "correlation_id",
        ]
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "record_id": "audit_001",
                    "timestamp": "2025-01-15T10:30:00Z",
                    "agent_id": "pdf_adapter_agent",
                    "action_type": "PDF_PROCESSED",
                    "resource_id": "doc_456",
                    "outcome": "SUCCESS",
                    "user_id": None,
                    "details": {
                        "page_count": 5,
                        "processing_time_ms": 8500,
                        "dpi": 300
                    },
                    "immutable_hash": "a1b2c3d4e5f6...",
                    "previous_hash": "f6e5d4c3b2a1...",
                    "correlation_id": "corr_abc"
                },
                {
                    "record_id": "audit_002",
                    "timestamp": "2025-01-15T11:00:00Z",
                    "agent_id": "web_portal",
                    "action_type": "HITL_DECISION",
                    "resource_id": "trade_GCS382857",
                    "outcome": "SUCCESS",
                    "user_id": "user_789",
                    "details": {
                        "decision": "APPROVE",
                        "review_time_seconds": 45,
                        "confidence": "HIGH"
                    },
                    "immutable_hash": "b2c3d4e5f6a1...",
                    "previous_hash": "a1b2c3d4e5f6...",
                    "correlation_id": "corr_def"
                }
            ]
        }


class AuditTrailQuery(BaseModel):
    """
    Query parameters for filtering audit trail.
    
    Requirements:
        - 10.3: Support filtering by date, agent, and action type
    """
    
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for filtering (inclusive)"
    )
    
    end_date: Optional[datetime] = Field(
        None,
        description="End date for filtering (inclusive)"
    )
    
    agent_id: Optional[str] = Field(
        None,
        description="Filter by agent ID"
    )
    
    action_type: Optional[ActionType] = Field(
        None,
        description="Filter by action type"
    )
    
    outcome: Optional[ActionOutcome] = Field(
        None,
        description="Filter by outcome"
    )
    
    user_id: Optional[str] = Field(
        None,
        description="Filter by user ID"
    )
    
    resource_id: Optional[str] = Field(
        None,
        description="Filter by resource ID"
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Filter by correlation ID"
    )
    
    limit: int = Field(
        default=100,
        description="Maximum number of records to return",
        gt=0,
        le=10000
    )
    
    offset: int = Field(
        default=0,
        description="Number of records to skip (for pagination)",
        ge=0
    )


class AuditTrailExport(BaseModel):
    """
    Configuration for exporting audit trail.
    
    Requirements:
        - 10.5: Export audit trails in standard formats
    """
    
    query: AuditTrailQuery = Field(
        ...,
        description="Query parameters for filtering records to export"
    )
    
    format: ExportFormat = Field(
        ...,
        description="Export format (JSON, CSV, XML)"
    )
    
    include_hash_verification: bool = Field(
        default=True,
        description="Whether to include hash verification in export"
    )
    
    output_path: Optional[str] = Field(
        None,
        description="S3 path or local path for export output"
    )
