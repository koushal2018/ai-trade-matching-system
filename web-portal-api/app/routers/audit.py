import csv
import io
import json
import xml.etree.ElementTree as ET
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from boto3.dynamodb.conditions import Attr
from ..models import AuditRecord, AuditActionType, AuditResponse
from ..services.dynamodb import db_service
from ..config import settings
from ..auth import require_auth, User

router = APIRouter(prefix="/audit", tags=["audit"])


def build_filter_expression(start_date: Optional[str], end_date: Optional[str],
                            agent_id: Optional[str], action_type: Optional[str]):
    """Build DynamoDB filter expression from query params."""
    conditions = []
    if start_date:
        conditions.append(Attr("timestamp").gte(start_date))
    if end_date:
        conditions.append(Attr("timestamp").lte(end_date + "T23:59:59Z"))
    if agent_id:
        conditions.append(Attr("agent_id").eq(agent_id))
    if action_type:
        conditions.append(Attr("action_type").eq(action_type))
    
    if not conditions:
        return None
    
    expr = conditions[0]
    for cond in conditions[1:]:
        expr = expr & cond
    return expr


@router.get("", response_model=AuditResponse)
async def get_audit_records(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    agentId: Optional[str] = Query(None),
    actionType: Optional[str] = Query(None),
    page: int = Query(0, ge=0),
    pageSize: int = Query(25, ge=1, le=100),
    user: User = Depends(require_auth)
):
    """Get audit records with filtering and pagination."""
    filter_expr = build_filter_expression(startDate, endDate, agentId, actionType)
    
    try:
        items, total = db_service.query_with_pagination(
            settings.dynamodb_audit_table, page, pageSize, filter_expr
        )
        
        records = [
            AuditRecord(
                auditId=item.get("audit_id", ""),
                timestamp=item.get("timestamp", ""),
                agentId=item.get("agent_id", ""),
                agentName=item.get("agent_name", ""),
                actionType=AuditActionType(item.get("action_type", "PDF_PROCESSED")),
                tradeId=item.get("trade_id"),
                outcome=item.get("outcome", "SUCCESS"),
                details=item.get("details", {}),
                immutableHash=item.get("immutable_hash", "")
            )
            for item in items
        ]
        
        return AuditResponse(records=records, total=total, page=page, pageSize=pageSize)
    except Exception:
        return AuditResponse(records=[], total=0, page=page, pageSize=pageSize)


@router.get("/export")
async def export_audit_records(
    format: str = Query("csv", regex="^(csv|json|xml)$"),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    agentId: Optional[str] = Query(None),
    actionType: Optional[str] = Query(None),
    user: User = Depends(require_auth)
):
    """Export audit records in CSV, JSON, or XML format."""
    filter_expr = build_filter_expression(startDate, endDate, agentId, actionType)
    
    try:
        items = db_service.scan_table(settings.dynamodb_audit_table, filter_expr, limit=10000)
    except Exception:
        items = []
    
    records = [
        {
            "auditId": item.get("audit_id", ""),
            "timestamp": item.get("timestamp", ""),
            "agentId": item.get("agent_id", ""),
            "agentName": item.get("agent_name", ""),
            "actionType": item.get("action_type", ""),
            "tradeId": item.get("trade_id", ""),
            "outcome": item.get("outcome", ""),
            "immutableHash": item.get("immutable_hash", "")
        }
        for item in items
    ]
    
    if format == "json":
        content = json.dumps(records, indent=2)
        media_type = "application/json"
        filename = "audit_trail.json"
    elif format == "xml":
        root = ET.Element("auditTrail")
        for record in records:
            rec_elem = ET.SubElement(root, "record")
            for key, value in record.items():
                child = ET.SubElement(rec_elem, key)
                child.text = str(value) if value else ""
        content = ET.tostring(root, encoding="unicode")
        media_type = "application/xml"
        filename = "audit_trail.xml"
    else:  # csv
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        content = output.getvalue()
        media_type = "text/csv"
        filename = "audit_trail.csv"
    
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
