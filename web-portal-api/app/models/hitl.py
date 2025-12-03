from enum import Enum
from typing import Optional
from pydantic import BaseModel
from .trade import Trade


class HITLStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class HITLReview(BaseModel):
    reviewId: str
    tradeId: str
    matchScore: float
    reasonCodes: list[str]
    bankTrade: Trade
    counterpartyTrade: Trade
    differences: dict[str, dict[str, str]]
    status: HITLStatus
    createdAt: str
    assignedTo: Optional[str] = None


class HITLDecision(BaseModel):
    decision: str  # "APPROVED" or "REJECTED"
    reason: Optional[str] = None
