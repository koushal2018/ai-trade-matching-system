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
    user: User = Depends(get_current_user)
):
    """Get matching results with optional filtering."""
    try:
        # Build filter expression
        conditions = []
        if startDate:
            conditions.append(Attr("created_at").gte(startDate))
        if endDate:
            conditions.append(Attr("created_at").lte(endDate + "T23:59:59Z"))
        if classification:
            conditions.append(Attr("classification").eq(classification))
        
        filter_expr = None
        if conditions:
            filter_expr = conditions[0]
            for cond in conditions[1:]:
                filter_expr = filter_expr & cond
        
        # Query audit trail for matching results
        items = db_service.scan_table(settings.dynamodb_audit_table, filter_expr, limit=500)
        
        results = []
        for item in items:
            if item.get("action_type") != "TRADE_MATCHED":
                continue
            
            details = item.get("details", {})
            results.append(MatchingResult(
                tradeId=item.get("trade_id", ""),
                classification=MatchClassification(details.get("classification", "MATCHED")),
                matchScore=float(details.get("match_score", 1.0)),
                decisionStatus=DecisionStatus(details.get("decision_status", "AUTO_MATCH")),
                reasonCodes=details.get("reason_codes", []),
                differences=details.get("differences", {}),
                createdAt=item.get("timestamp", "")
            ))
        
        return results
    except Exception:
        return []
