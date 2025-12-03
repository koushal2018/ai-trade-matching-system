import json
import hashlib
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
import boto3
from ..models import HITLReview, HITLDecision, MatchingResult, DecisionStatus, MatchClassification
from ..models.hitl import HITLStatus
from ..services.dynamodb import db_service
from ..services.websocket import manager
from ..config import settings
from ..auth import require_auth, User

router = APIRouter(prefix="/hitl", tags=["hitl"])


@router.get("/pending", response_model=list[HITLReview])
async def get_pending_reviews(user: User = Depends(require_auth)):
    """Get all pending HITL reviews."""
    try:
        items = db_service.scan_table(settings.dynamodb_hitl_table)
        reviews = [
            HITLReview(
                reviewId=item.get("review_id", ""),
                tradeId=item.get("trade_id", ""),
                matchScore=float(item.get("match_score", 0)),
                reasonCodes=item.get("reason_codes", []),
                bankTrade=item.get("bank_trade", {}),
                counterpartyTrade=item.get("counterparty_trade", {}),
                differences=item.get("differences", {}),
                status=HITLStatus(item.get("status", "PENDING")),
                createdAt=item.get("created_at", ""),
                assignedTo=item.get("assigned_to")
            )
            for item in items
            if item.get("status") == "PENDING"
        ]
        return reviews
    except Exception:
        return []


@router.get("/{review_id}", response_model=HITLReview)
async def get_review(review_id: str, user: User = Depends(require_auth)):
    """Get a specific HITL review by ID."""
    item = db_service.get_item(settings.dynamodb_hitl_table, {"review_id": review_id})
    if not item:
        raise HTTPException(status_code=404, detail="Review not found")
    return HITLReview(
        reviewId=item.get("review_id", ""),
        tradeId=item.get("trade_id", ""),
        matchScore=float(item.get("match_score", 0)),
        reasonCodes=item.get("reason_codes", []),
        bankTrade=item.get("bank_trade", {}),
        counterpartyTrade=item.get("counterparty_trade", {}),
        differences=item.get("differences", {}),
        status=HITLStatus(item.get("status", "PENDING")),
        createdAt=item.get("created_at", ""),
        assignedTo=item.get("assigned_to")
    )


@router.post("/{review_id}/decision", response_model=MatchingResult)
async def submit_decision(review_id: str, decision: HITLDecision, user: User = Depends(require_auth)):
    """Submit a HITL decision for a review."""
    # Get the review
    item = db_service.get_item(settings.dynamodb_hitl_table, {"review_id": review_id})
    if not item:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if item.get("status") != "PENDING":
        raise HTTPException(status_code=400, detail="Review already processed")
    
    # Update the review status
    new_status = "APPROVED" if decision.decision == "APPROVED" else "REJECTED"
    db_service.update_item(
        settings.dynamodb_hitl_table,
        {"review_id": review_id},
        "SET #status = :status, resolved_by = :user, resolved_at = :time, resolution_reason = :reason",
        {
            ":status": new_status,
            ":user": user.username,
            ":time": datetime.utcnow().isoformat() + "Z",
            ":reason": decision.reason or ""
        }
    )
    
    # Create audit record
    audit_record = {
        "audit_id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_id": "web-portal",
        "agent_name": "Web Portal",
        "action_type": "HITL_DECISION",
        "trade_id": item.get("trade_id"),
        "outcome": "SUCCESS",
        "details": {
            "review_id": review_id,
            "decision": decision.decision,
            "reason": decision.reason,
            "user": user.username
        },
        "immutable_hash": hashlib.sha256(
            json.dumps({"review_id": review_id, "decision": decision.decision, "user": user.username}).encode()
        ).hexdigest()
    }
    db_service.put_item(settings.dynamodb_audit_table, audit_record)
    
    # Publish to SQS for agent processing
    if settings.hitl_queue_url:
        sqs = boto3.client("sqs", region_name=settings.aws_region)
        sqs.send_message(
            QueueUrl=settings.hitl_queue_url,
            MessageBody=json.dumps({
                "event_type": "HITL_DECISION",
                "review_id": review_id,
                "trade_id": item.get("trade_id"),
                "decision": decision.decision,
                "reason": decision.reason
            })
        )
    
    # Return matching result
    decision_status = DecisionStatus.APPROVED if decision.decision == "APPROVED" else DecisionStatus.REJECTED
    return MatchingResult(
        tradeId=item.get("trade_id", ""),
        classification=MatchClassification.MATCHED if decision.decision == "APPROVED" else MatchClassification.BREAK,
        matchScore=float(item.get("match_score", 0)),
        decisionStatus=decision_status,
        reasonCodes=item.get("reason_codes", []),
        differences=item.get("differences", {}),
        createdAt=datetime.utcnow().isoformat() + "Z"
    )
