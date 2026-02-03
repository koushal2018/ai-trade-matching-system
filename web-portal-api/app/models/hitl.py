from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel


class HITLStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class HITLReview(BaseModel):
    reviewId: str
    tradeId: str
    matchScore: float
    reasonCodes: list[str]
    bankTrade: Dict[str, Any]  # Flexible trade data structure
    counterpartyTrade: Dict[str, Any]  # Flexible trade data structure
    differences: Dict[str, Any]
    status: HITLStatus
    createdAt: str
    assignedTo: Optional[str] = None
    sessionId: Optional[str] = None  # Optional session reference


class HITLDecision(BaseModel):
    decision: str  # "APPROVED" or "REJECTED"
    reason: Optional[str] = None
