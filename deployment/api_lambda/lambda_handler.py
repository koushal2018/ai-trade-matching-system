"""
Trade Matching API - Lambda Handler

This Lambda function serves as the API backend for the Trade Matching Portal.
It provides endpoints for agent status, metrics, matching results, HITL reviews, etc.
"""

import json
import os
import uuid
import random
import base64
import boto3
from datetime import datetime, timedelta
from typing import Any, Dict, List

# S3 client for presigned URLs
s3_client = boto3.client('s3', region_name='us-east-1')
S3_BUCKET = os.environ.get('S3_BUCKET', 'trade-matching-uploads-979873657001')

# ============================================================================
# CONSISTENT MOCK DATA - Shared across all endpoints for data consistency
# ============================================================================

# Fixed session IDs for consistency
SESSIONS = [
    {"sessionId": "sess-abc12345", "tradeId": "TRD-2024-0001", "counterpartyId": "CP-GOLDMAN"},
    {"sessionId": "sess-def67890", "tradeId": "TRD-2024-0002", "counterpartyId": "CP-JPMORGAN"},
    {"sessionId": "sess-ghi11223", "tradeId": "TRD-2024-0003", "counterpartyId": "CP-CITBANK"},
    {"sessionId": "sess-jkl44556", "tradeId": "TRD-2024-0004", "counterpartyId": "CP-BARCLAYS"},
    {"sessionId": "sess-mno77889", "tradeId": "TRD-2024-0005", "counterpartyId": "CP-DEUTSCHE"},
    {"sessionId": "sess-pqr00112", "tradeId": "TRD-2024-0006", "counterpartyId": "CP-HSBC"},
    {"sessionId": "sess-stu33445", "tradeId": "TRD-2024-0007", "counterpartyId": "CP-UBS"},
    {"sessionId": "sess-vwx66778", "tradeId": "TRD-2024-0008", "counterpartyId": "CP-MORGAN"},
]

# Agent definitions
AGENTS = [
    {"agentId": "agent-1", "agentName": "PDF Adapter", "status": "HEALTHY", "activeTasks": 2},
    {"agentId": "agent-2", "agentName": "Trade Extraction", "status": "HEALTHY", "activeTasks": 1},
    {"agentId": "agent-3", "agentName": "Trade Matching", "status": "DEGRADED", "activeTasks": 3},
    {"agentId": "agent-4", "agentName": "Exception Handler", "status": "HEALTHY", "activeTasks": 0},
    {"agentId": "agent-5", "agentName": "HITL Coordinator", "status": "HEALTHY", "activeTasks": 1},
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_agent_metrics():
    """Generate dynamic agent metrics."""
    return {
        "latencyMs": random.randint(80, 300),
        "throughput": random.randint(50, 200),
        "successRate": round(random.uniform(0.85, 0.99), 2),
        "errorRate": round(random.uniform(0.01, 0.15), 2),
        "totalTokens": random.randint(5000, 50000),
        "cycleCount": random.randint(50, 300)
    }

def cors_response(status_code: int, body: Any) -> Dict:
    """Build response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body, default=str)
    }

# ============================================================================
# API ENDPOINT HANDLERS
# ============================================================================

def get_agent_status() -> List[Dict]:
    """Get status of all agents with dynamic metrics."""
    return [
        {
            **agent,
            "metrics": generate_agent_metrics(),
            "lastUpdated": datetime.utcnow().isoformat() + "Z"
        }
        for agent in AGENTS
    ]

def get_processing_metrics() -> Dict:
    """Get processing metrics."""
    return {
        "totalProcessed": 1247,
        "matchedCount": 1156,
        "unmatchedCount": 52,
        "pendingCount": 24,
        "errorCount": 15
    }

def get_matching_results() -> List[Dict]:
    """Get recent matching results - consistent with other endpoints."""
    results = []
    classifications = ["MATCHED", "MATCHED", "MATCHED", "PROBABLE_MATCH", "REVIEW_REQUIRED", "BREAK", "MATCHED", "PROBABLE_MATCH"]
    decision_statuses = ["AUTO_MATCH", "AUTO_MATCH", "AUTO_MATCH", "ESCALATE", "ESCALATE", "EXCEPTION", "APPROVED", "PENDING"]

    for i, session in enumerate(SESSIONS):
        classification = classifications[i % len(classifications)]
        confidence = 95 if classification == "MATCHED" else (78 if classification == "PROBABLE_MATCH" else (62 if classification == "REVIEW_REQUIRED" else 35))

        results.append({
            "sessionId": session["sessionId"],
            "tradeId": session["tradeId"],
            "counterpartyId": session["counterpartyId"],
            "matchStatus": "MATCHED" if classification in ["MATCHED", "PROBABLE_MATCH"] else "MISMATCHED",
            "classification": classification,
            "confidenceScore": confidence,
            "matchScore": confidence / 100,
            "decisionStatus": decision_statuses[i % len(decision_statuses)],
            "completedAt": (datetime.utcnow() - timedelta(minutes=i*15)).isoformat() + "Z",
            "createdAt": (datetime.utcnow() - timedelta(minutes=i*15 + 5)).isoformat() + "Z",
            "fieldComparisons": [
                {"fieldName": "Trade ID", "bankValue": session["tradeId"], "counterpartyValue": session["tradeId"], "match": True, "confidence": 100},
                {"fieldName": "Notional Amount", "bankValue": "1,000,000 USD", "counterpartyValue": "1,000,000 USD", "match": True, "confidence": 100},
                {"fieldName": "Trade Date", "bankValue": "2024-12-15", "counterpartyValue": "2024-12-15", "match": True, "confidence": 100},
                {"fieldName": "Settlement Date", "bankValue": "2024-12-17", "counterpartyValue": "2024-12-17", "match": classification == "MATCHED", "confidence": confidence},
            ],
            "metadata": {"processingTime": random.randint(10, 30), "agentVersion": "1.0.0"}
        })
    return results

def get_hitl_reviews() -> List[Dict]:
    """Get pending HITL reviews - uses sessions that need review."""
    reviews = []
    # Sessions 3, 4, 5 need HITL review (REVIEW_REQUIRED, BREAK, etc.)
    review_sessions = [SESSIONS[3], SESSIONS[4], SESSIONS[5]]

    for i, session in enumerate(review_sessions):
        reviews.append({
            "reviewId": f"rev-{str(i+1).zfill(3)}",
            "sessionId": session["sessionId"],
            "tradeId": session["tradeId"],
            "counterpartyId": session["counterpartyId"],
            "matchScore": round(0.62 - (i * 0.1), 2),
            "status": "PENDING",
            "priority": "HIGH" if i == 0 else "MEDIUM",
            "assignedTo": None,
            "createdAt": (datetime.utcnow() - timedelta(hours=i+1)).isoformat() + "Z",
            "bankData": {
                "tradeId": session["tradeId"],
                "notionalAmount": "1,000,000 USD",
                "tradeDate": "2024-12-15",
                "settlementDate": "2024-12-17",
                "counterparty": session["counterpartyId"],
                "product": "Interest Rate Swap"
            },
            "counterpartyData": {
                "tradeId": session["tradeId"],
                "notionalAmount": "1,000,000 USD",
                "tradeDate": "2024-12-15",
                "settlementDate": "2024-12-18" if i > 0 else "2024-12-17",  # Mismatch
                "counterparty": "ACME Bank",
                "product": "Interest Rate Swap"
            },
            "discrepancies": [
                {"field": "Settlement Date", "bankValue": "2024-12-17", "counterpartyValue": "2024-12-18", "severity": "HIGH"} if i > 0 else None
            ]
        })
    return [r for r in reviews if r]  # Filter None

def get_hitl_review_by_id(review_id: str) -> Dict:
    """Get a specific HITL review by ID."""
    reviews = get_hitl_reviews()
    for review in reviews:
        if review["reviewId"] == review_id:
            return review
    return {"error": "Review not found", "reviewId": review_id}

def get_audit_records(params: Dict) -> Dict:
    """Get audit trail records - consistent with sessions."""
    records = []
    action_types = ["Upload", "Invoke", "Match Complete", "Exception", "HITL_DECISION", "TRADE_MATCHED"]
    outcomes = ["SUCCESS", "SUCCESS", "SUCCESS", "FAILURE", "SUCCESS", "SUCCESS"]
    users = ["system", "john.doe@bank.com", "system", "system", "jane.smith@bank.com", "system"]

    for i, session in enumerate(SESSIONS):
        records.append({
            "id": f"audit-{str(i+1).zfill(4)}",
            "sessionId": session["sessionId"],
            "tradeId": session["tradeId"],
            "actionType": action_types[i % len(action_types)],
            "outcome": outcomes[i % len(outcomes)],
            "user": users[i % len(users)],
            "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat() + "Z",
            "details": {
                "agentName": AGENTS[i % len(AGENTS)]["agentName"],
                "processingTime": random.randint(100, 500),
                "message": f"Processed {session['tradeId']} successfully"
            }
        })

    # Add more recent audit records
    for i in range(8, 20):
        session = SESSIONS[i % len(SESSIONS)]
        records.append({
            "id": f"audit-{str(i+1).zfill(4)}",
            "sessionId": session["sessionId"],
            "tradeId": session["tradeId"],
            "actionType": random.choice(action_types),
            "outcome": random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "FAILURE"]),
            "user": random.choice(users),
            "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat() + "Z",
            "details": {
                "agentName": random.choice(AGENTS)["agentName"],
                "processingTime": random.randint(100, 500),
                "message": f"Operation on {session['tradeId']}"
            }
        })

    page = int(params.get("page", 0))
    page_size = int(params.get("pageSize", 25))
    start = page * page_size
    end = start + page_size

    return {
        "records": records[start:end],
        "total": len(records),
        "page": page,
        "pageSize": page_size
    }

def get_matching_queue() -> List[Dict]:
    """Get items in matching queue."""
    queue_items = []
    for i, session in enumerate(SESSIONS[:5]):
        queue_items.append({
            "queueId": f"q-{str(i+1).zfill(3)}",
            "sessionId": session["sessionId"],
            "tradeId": session["tradeId"],
            "counterpartyId": session["counterpartyId"],
            "status": ["PENDING", "PROCESSING", "PENDING", "WAITING", "PENDING"][i],
            "priority": ["HIGH", "MEDIUM", "HIGH", "LOW", "MEDIUM"][i],
            "queuedAt": (datetime.utcnow() - timedelta(minutes=i*10)).isoformat() + "Z",
            "estimatedProcessingTime": random.randint(30, 120),
            "sourceType": ["BANK", "COUNTERPARTY"][i % 2],
            "documentCount": random.randint(1, 3)
        })
    return queue_items

def get_exceptions_list() -> List[Dict]:
    """Get list of all exceptions."""
    exceptions = []
    # Sessions with exceptions
    exception_sessions = [SESSIONS[3], SESSIONS[5]]

    for i, session in enumerate(exception_sessions):
        exceptions.append({
            "id": f"exc-{str(i+1).zfill(3)}",
            "sessionId": session["sessionId"],
            "tradeId": session["tradeId"],
            "agentName": ["Trade Matching", "Exception Handler"][i],
            "severity": ["HIGH", "MEDIUM"][i],
            "type": ["FIELD_MISMATCH", "LOW_CONFIDENCE"][i],
            "message": ["Settlement date mismatch detected", "Confidence score below threshold"][i],
            "timestamp": (datetime.utcnow() - timedelta(hours=i+1)).isoformat() + "Z",
            "recoverable": True,
            "status": "OPEN",
            "details": {
                "field": "Settlement Date" if i == 0 else "Overall Match",
                "bankValue": "2024-12-17",
                "counterpartyValue": "2024-12-18" if i == 0 else "2024-12-17",
                "confidence": 0.62 - (i * 0.1)
            }
        })
    return exceptions

def handle_upload(body: Dict, is_multipart: bool = False, raw_body: str = None) -> Dict:
    """Handle file upload - either via presigned URL request or direct upload."""
    source_type = body.get("sourceType", "UNKNOWN")
    file_name = body.get("fileName", "document.pdf")
    session_id = f"session-{uuid.uuid4().hex[:12]}"
    trace_id = f"trace-{uuid.uuid4().hex[:12]}"
    upload_id = f"upload-{uuid.uuid4().hex[:12]}"

    # Generate S3 key
    s3_key = f"{source_type}/{session_id}/{file_name}"

    # Try to generate presigned URL for upload
    try:
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': s3_key,
                'ContentType': 'application/pdf'
            },
            ExpiresIn=300  # 5 minutes
        )

        return {
            "uploadId": upload_id,
            "sessionId": session_id,
            "traceId": trace_id,
            "s3Uri": f"s3://{S3_BUCKET}/{s3_key}",
            "presignedUrl": presigned_url,
            "status": "success",
            "message": "Use presignedUrl to upload file directly to S3"
        }
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        # Fallback response for demo mode
        return {
            "uploadId": upload_id,
            "sessionId": session_id,
            "traceId": trace_id,
            "s3Uri": f"s3://{S3_BUCKET}/{s3_key}",
            "status": "success",
            "message": "Upload simulated (S3 bucket may not exist)"
        }

def get_workflow_status(session_id: str) -> Dict:
    """Get workflow status for a session."""
    return {
        "sessionId": session_id,
        "overallStatus": "complete",
        "lastUpdated": datetime.utcnow().isoformat() + "Z",
        "agents": {
            "pdfAdapter": {
                "status": "success",
                "activity": "Extracted text from 2 pages",
                "startedAt": (datetime.utcnow() - timedelta(seconds=30)).isoformat() + "Z",
                "completedAt": (datetime.utcnow() - timedelta(seconds=25)).isoformat() + "Z",
                "duration": 5,
                "subSteps": [
                    {"title": "Convert PDF to images", "status": "success", "description": "Converted 2 pages"},
                    {"title": "Extract text", "status": "success", "description": "Extracted 1,234 characters"}
                ]
            },
            "tradeExtraction": {
                "status": "success",
                "activity": "Extracted structured trade data",
                "startedAt": (datetime.utcnow() - timedelta(seconds=20)).isoformat() + "Z",
                "completedAt": (datetime.utcnow() - timedelta(seconds=15)).isoformat() + "Z",
                "duration": 5,
                "subSteps": [
                    {"title": "Parse trade fields", "status": "success", "description": "Parsed all fields"}
                ]
            },
            "tradeMatching": {
                "status": "success",
                "activity": "Trade matched successfully",
                "startedAt": (datetime.utcnow() - timedelta(seconds=10)).isoformat() + "Z",
                "completedAt": (datetime.utcnow() - timedelta(seconds=5)).isoformat() + "Z",
                "duration": 5
            },
            "exceptionManagement": {
                "status": "success",
                "activity": "No exceptions detected"
            }
        }
    }

def get_workflow_exceptions(session_id: str) -> Dict:
    """Get exceptions for a specific workflow session."""
    all_exceptions = get_exceptions_list()
    session_exceptions = [e for e in all_exceptions if e["sessionId"] == session_id]

    if not session_exceptions:
        # Return a sample exception for demo
        return {
            "exceptions": [
                {
                    "id": "exc-demo",
                    "sessionId": session_id,
                    "agentName": "PDF Adapter Agent",
                    "severity": "warning",
                    "message": "Low confidence in text extraction from page 2",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
                    "recoverable": True,
                    "details": {"page": 2, "confidence": 0.75}
                }
            ]
        }

    return {"exceptions": session_exceptions}

# ============================================================================
# MAIN HANDLER
# ============================================================================

def handler(event, context):
    """Main Lambda handler."""
    print(f"Event: {json.dumps(event)}")

    # Handle OPTIONS for CORS preflight
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "GET")
    if http_method == "OPTIONS":
        return cors_response(200, {"message": "OK"})

    # Get path from various event formats (API Gateway v1, v2, ALB)
    path = event.get("path") or event.get("rawPath") or "/"
    path = path.replace("/api", "")  # Remove /api prefix if present

    # Get query parameters
    query_params = event.get("queryStringParameters") or {}

    # Parse body if present
    body = {}
    raw_body = event.get("body", "")
    is_base64 = event.get("isBase64Encoded", False)
    content_type = ""

    # Get content type from headers
    headers = event.get("headers", {})
    for key, value in headers.items():
        if key.lower() == "content-type":
            content_type = value.lower()
            break

    if raw_body:
        try:
            # Handle base64 encoded body
            if is_base64:
                raw_body = base64.b64decode(raw_body).decode('utf-8', errors='ignore')

            # Parse JSON body
            if "application/json" in content_type or (isinstance(raw_body, str) and raw_body.startswith('{')):
                body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
            # Handle multipart form data
            elif "multipart/form-data" in content_type:
                # Extract sourceType from multipart data
                if "sourceType" in str(raw_body):
                    if 'name="sourceType"' in str(raw_body):
                        parts = str(raw_body).split('name="sourceType"')
                        if len(parts) > 1:
                            value_part = parts[1].split('\r\n\r\n')[1].split('\r\n')[0] if '\r\n\r\n' in parts[1] else ""
                            body["sourceType"] = value_part.strip()
                # Extract fileName
                if 'filename="' in str(raw_body):
                    start = str(raw_body).index('filename="') + len('filename="')
                    end = str(raw_body).index('"', start)
                    body["fileName"] = str(raw_body)[start:end]
        except (json.JSONDecodeError, Exception) as e:
            print(f"Body parse error: {e}")

    # Route handling
    try:
        # ===== AGENT ENDPOINTS =====
        if path == "/agents/status" and http_method == "GET":
            return cors_response(200, get_agent_status())

        # ===== METRICS ENDPOINTS =====
        if path == "/metrics/processing" and http_method == "GET":
            return cors_response(200, get_processing_metrics())

        # ===== MATCHING ENDPOINTS =====
        if path == "/matching/results" and http_method == "GET":
            return cors_response(200, get_matching_results())

        if path == "/matching/queue" and http_method == "GET":
            return cors_response(200, get_matching_queue())

        # ===== HITL ENDPOINTS =====
        if path == "/hitl/reviews" and http_method == "GET":
            return cors_response(200, get_hitl_reviews())

        if path == "/hitl/pending" and http_method == "GET":
            return cors_response(200, get_hitl_reviews())

        if path.startswith("/hitl/") and path.endswith("/decision") and http_method == "POST":
            review_id = path.split("/")[2]
            return cors_response(200, {
                "success": True,
                "reviewId": review_id,
                "decision": body.get("decision"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        if path.startswith("/hitl/") and http_method == "GET":
            review_id = path.split("/")[2]
            return cors_response(200, get_hitl_review_by_id(review_id))

        if path == "/hitl/decision" and http_method == "POST":
            return cors_response(200, {
                "success": True,
                "reviewId": body.get("reviewId"),
                "decision": body.get("decision"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        # ===== AUDIT ENDPOINTS =====
        if path == "/audit" and http_method == "GET":
            return cors_response(200, get_audit_records(query_params))

        # ===== EXCEPTION ENDPOINTS =====
        if path == "/exceptions" and http_method == "GET":
            return cors_response(200, {"exceptions": get_exceptions_list()})

        # ===== UPLOAD ENDPOINTS =====
        if path == "/upload" and http_method == "POST":
            return cors_response(200, handle_upload(body))

        if path == "/upload/presign" and http_method == "POST":
            return cors_response(200, handle_upload(body))

        # ===== WORKFLOW ENDPOINTS =====
        if path.startswith("/workflow/") and path.endswith("/status"):
            session_id = path.split("/")[2]
            return cors_response(200, get_workflow_status(session_id))

        if path.startswith("/workflow/") and path.endswith("/invoke-matching"):
            session_id = path.split("/")[2]
            return cors_response(200, {
                "success": True,
                "invocationId": f"invoke-{uuid.uuid4().hex[:12]}",
                "sessionId": session_id,
                "status": "initiated",
                "message": "Trade matching initiated"
            })

        if path.startswith("/workflow/") and path.endswith("/result"):
            session_id = path.split("/")[2]
            # Find matching session data
            session_data = next((s for s in SESSIONS if s["sessionId"] == session_id), SESSIONS[0])
            return cors_response(200, {
                "available": True,
                "result": {
                    "sessionId": session_id,
                    "tradeId": session_data["tradeId"],
                    "matchStatus": "MATCHED",
                    "confidenceScore": 92,
                    "completedAt": datetime.utcnow().isoformat() + "Z",
                    "fieldComparisons": [
                        {"fieldName": "Trade ID", "bankValue": session_data["tradeId"], "counterpartyValue": session_data["tradeId"], "match": True, "confidence": 100},
                        {"fieldName": "Notional Amount", "bankValue": "1,000,000 USD", "counterpartyValue": "1,000,000 USD", "match": True, "confidence": 100},
                        {"fieldName": "Trade Date", "bankValue": "2024-12-15", "counterpartyValue": "2024-12-15", "match": True, "confidence": 100},
                        {"fieldName": "Settlement Date", "bankValue": "2024-12-17", "counterpartyValue": "2024-12-17", "match": True, "confidence": 100}
                    ],
                    "metadata": {"processingTime": 15, "agentVersion": "1.0.0"}
                }
            })

        if path.startswith("/workflow/") and path.endswith("/exceptions"):
            session_id = path.split("/")[2]
            return cors_response(200, get_workflow_exceptions(session_id))

        # ===== FEEDBACK ENDPOINTS =====
        if path == "/feedback" and http_method == "POST":
            return cors_response(200, {
                "success": True,
                "message": "Feedback recorded",
                "feedbackId": f"feedback-{uuid.uuid4().hex[:12]}"
            })

        # ===== HEALTH CHECK =====
        if path == "/health" or path == "/":
            return cors_response(200, {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"})

        # ===== NOT FOUND =====
        return cors_response(404, {"error": "Not found", "path": path})

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return cors_response(500, {"error": str(e)})
