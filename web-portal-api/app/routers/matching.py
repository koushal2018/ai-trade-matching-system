from typing import Optional
from fastapi import APIRouter, Depends, Query
from boto3.dynamodb.conditions import Attr
from ..models import MatchingResult, MatchClassification, DecisionStatus
from ..services.dynamodb import db_service
from ..config import settings
from ..auth import get_current_user, User

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get("/results", response_model=list[MatchingResult])
async def get_matching_results(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    # user: User = Depends(get_current_user)  # Temporarily disabled for testing
):
    """Get matching results with optional filtering."""
    # Return mock data for demonstration
    results = [
        MatchingResult(
            tradeId="TRD-1001",
            classification=MatchClassification.MATCHED,
            matchScore=0.95,
            decisionStatus=DecisionStatus.AUTO_MATCH,
            reasonCodes=["CURRENCY_MATCH", "NOTIONAL_MATCH"],
            differences={},
            createdAt="2025-12-14T10:30:00Z"
        ),
        MatchingResult(
            tradeId="TRD-1002",
            classification=MatchClassification.REVIEW_REQUIRED,
            matchScore=0.75,
            decisionStatus=DecisionStatus.ESCALATE,
            reasonCodes=["NOTIONAL_DIFF"],
            differences={"notional": {"bank": "1000000", "counterparty": "1000500"}},
            createdAt="2025-12-14T09:15:00Z"
        ),
        MatchingResult(
            tradeId="TRD-1003",
            classification=MatchClassification.BREAK,
            matchScore=0.35,
            decisionStatus=DecisionStatus.EXCEPTION,
            reasonCodes=["CURRENCY_MISMATCH", "DATE_DIFF"],
            differences={"currency": {"bank": "USD", "counterparty": "EUR"}},
            createdAt="2025-12-14T08:45:00Z"
        )
    ]
    
    return results
