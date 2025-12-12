from enum import Enum
from typing import Optional
from pydantic import BaseModel


class MatchClassification(str, Enum):
    MATCHED = "MATCHED"
    PROBABLE_MATCH = "PROBABLE_MATCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BREAK = "BREAK"
    DATA_ERROR = "DATA_ERROR"


class DecisionStatus(str, Enum):
    AUTO_MATCH = "AUTO_MATCH"
    ESCALATE = "ESCALATE"
    EXCEPTION = "EXCEPTION"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Trade(BaseModel):
    Trade_ID: str
    TRADE_SOURCE: str
    trade_date: str
    notional: float
    currency: str
    counterparty: str
    product_type: str
    effective_date: Optional[str] = None
    maturity_date: Optional[str] = None


class MatchingResult(BaseModel):
    tradeId: str
    classification: MatchClassification
    matchScore: float
    decisionStatus: DecisionStatus
    reasonCodes: list[str]
    bankTrade: Optional[Trade] = None
    counterpartyTrade: Optional[Trade] = None
    differences: dict[str, dict[str, str]]
    createdAt: str
