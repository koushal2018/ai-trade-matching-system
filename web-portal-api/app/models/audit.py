from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel


class AuditActionType(str, Enum):
    PDF_PROCESSED = "PDF_PROCESSED"
    TRADE_EXTRACTED = "TRADE_EXTRACTED"
    TRADE_MATCHED = "TRADE_MATCHED"
    EXCEPTION_RAISED = "EXCEPTION_RAISED"
    HITL_DECISION = "HITL_DECISION"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_STOPPED = "AGENT_STOPPED"


class AuditRecord(BaseModel):
    auditId: str
    timestamp: str
    agentId: str
    agentName: str
    actionType: AuditActionType
    tradeId: Optional[str] = None
    outcome: str
    details: dict[str, Any]
    immutableHash: str


class AuditQueryParams(BaseModel):
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    agentId: Optional[str] = None
    actionType: Optional[AuditActionType] = None
    page: int = 0
    pageSize: int = 25


class AuditResponse(BaseModel):
    records: list[AuditRecord]
    total: int
    page: int
    pageSize: int
