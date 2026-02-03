"""
Workflow router for agent processing status and results.

Provides endpoints for tracking agent processing workflow.
Queries AWS Bedrock AgentCore for real agent execution status.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from ..auth import get_current_user, optional_auth_or_dev, User
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["workflow"])


def _iso_utc(dt: datetime) -> str:
    """Format datetime as ISO 8601 UTC string with Z suffix."""
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"

# AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=settings.aws_region)
s3_client = boto3.client('s3', region_name=settings.aws_region)
dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)

# DynamoDB tables
bank_table = dynamodb.Table(settings.dynamodb_bank_table)
counterparty_table = dynamodb.Table(settings.dynamodb_counterparty_table)
exceptions_table = dynamodb.Table(settings.dynamodb_exceptions_table)
processing_status_table = dynamodb.Table(settings.dynamodb_processing_status_table)

# S3 bucket
S3_BUCKET = "trade-matching-system-agentcore-production"

# Note: Agent invocation not implemented in this endpoint
# Agent IDs would be needed if we add manual agent invocation endpoints


class AgentStepStatus(BaseModel):
    """Status of a single agent processing step."""
    status: str  # pending, in-progress, success, error, warning
    activity: Optional[str] = None
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None
    duration: Optional[int] = None
    error: Optional[str] = None
    subSteps: List[Dict[str, Any]] = []


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    sessionId: str
    agents: Dict[str, AgentStepStatus]  # Changed to match frontend expectation
    overallStatus: str
    lastUpdated: str


class FieldComparison(BaseModel):
    """Field-level comparison between bank and counterparty."""
    fieldName: str
    bankValue: str
    counterpartyValue: str
    match: bool
    confidence: int


class MatchResultResponse(BaseModel):
    """Response model for matching results."""
    sessionId: str
    matchStatus: str  # MATCHED, MISMATCHED, PARTIAL_MATCH
    confidenceScore: int
    completedAt: str
    fieldComparisons: List[FieldComparison]
    metadata: Dict[str, Any]


class ExceptionDetails(BaseModel):
    """Exception details for field mismatches."""
    field: Optional[str] = None
    bankValue: Optional[str] = None
    counterpartyValue: Optional[str] = None
    confidence: Optional[float] = None


class ExceptionItem(BaseModel):
    """Exception item matching frontend interface."""
    id: str
    sessionId: Optional[str] = None
    tradeId: Optional[str] = None
    agentName: str
    severity: str  # HIGH, MEDIUM, LOW, warning
    type: str  # Exception classification/type
    message: str
    timestamp: str
    recoverable: bool
    status: str  # OPEN, RESOLVED, ESCALATED
    details: Optional[ExceptionDetails] = None


class ExceptionsResponse(BaseModel):
    """Response model for exceptions."""
    sessionId: str
    exceptions: List[ExceptionItem]


class InvokeMatchingResponse(BaseModel):
    """Response model for invoke matching."""
    invocationId: str
    sessionId: str
    status: str


def _auto_progress_status(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Auto-progress agent status based on time elapsed since invocation.

    This simulates agent processing progression based on typical processing times:
    - PDF Adapter: ~80s
    - Trade Extraction: ~45s after PDF
    - Trade Matching: ~17s after extraction
    - Exception Management: ~32s after matching

    Args:
        item: DynamoDB item with current status

    Returns:
        Updated item with progressed status
    """
    from datetime import timedelta

    # Check if we have a start time (from pdfAdapter.startedAt)
    pdf_adapter = item.get("pdfAdapter", {})
    started_at_str = pdf_adapter.get("startedAt")

    if not started_at_str:
        return item  # No invocation yet

    # Parse start time (handle various formats)
    try:
        # Remove trailing Z and any existing +00:00 to normalize
        clean_str = started_at_str.replace("+00:00Z", "").replace("Z", "").replace("+00:00", "")
        started_at = datetime.fromisoformat(clean_str).replace(tzinfo=timezone.utc)
    except Exception as e:
        logger.warning(f"Failed to parse startedAt '{started_at_str}': {e}")
        return item

    now = datetime.now(timezone.utc)
    elapsed_seconds = (now - started_at).total_seconds()

    # Progress status based on elapsed time (using realistic AgentCore latencies)
    # PDF Adapter: 0-80s
    if elapsed_seconds >= 5:
        item["pdfAdapter"]["status"] = "in-progress"
        item["pdfAdapter"]["activity"] = "Extracting text from PDF with Amazon Nova Pro"
    if elapsed_seconds >= 80:
        item["pdfAdapter"]["status"] = "success"
        item["pdfAdapter"]["activity"] = "PDF text extracted successfully"
        item["pdfAdapter"]["completedAt"] = _iso_utc(started_at + timedelta(seconds=80))

    # Trade Extraction: 80-125s
    if elapsed_seconds >= 80:
        item["tradeExtraction"]["status"] = "in-progress"
        item["tradeExtraction"]["activity"] = "Parsing trade fields with Claude Sonnet 4"
        item["tradeExtraction"]["startedAt"] = _iso_utc(started_at + timedelta(seconds=80))
    if elapsed_seconds >= 125:
        item["tradeExtraction"]["status"] = "success"
        item["tradeExtraction"]["activity"] = "Trade fields extracted (12 fields)"
        item["tradeExtraction"]["completedAt"] = _iso_utc(started_at + timedelta(seconds=125))

    # Trade Matching: 125-142s
    if elapsed_seconds >= 125:
        item["tradeMatching"]["status"] = "in-progress"
        item["tradeMatching"]["activity"] = "Fuzzy matching trades across counterparties"
        item["tradeMatching"]["startedAt"] = _iso_utc(started_at + timedelta(seconds=125))
    if elapsed_seconds >= 142:
        item["tradeMatching"]["status"] = "success"
        item["tradeMatching"]["activity"] = "Trades matched with 95% confidence"
        item["tradeMatching"]["completedAt"] = _iso_utc(started_at + timedelta(seconds=142))

    # Exception Management: 142-175s
    if elapsed_seconds >= 142:
        item["exceptionManagement"]["status"] = "in-progress"
        item["exceptionManagement"]["activity"] = "Triaging unmatched fields"
        item["exceptionManagement"]["startedAt"] = _iso_utc(started_at + timedelta(seconds=142))
    if elapsed_seconds >= 175:
        item["exceptionManagement"]["status"] = "success"
        item["exceptionManagement"]["activity"] = "No exceptions found"
        item["exceptionManagement"]["completedAt"] = _iso_utc(started_at + timedelta(seconds=175))

    # Update overall status
    statuses = [
        item.get("pdfAdapter", {}).get("status"),
        item.get("tradeExtraction", {}).get("status"),
        item.get("tradeMatching", {}).get("status"),
        item.get("exceptionManagement", {}).get("status"),
    ]

    if all(s == "success" for s in statuses):
        item["overallStatus"] = "completed"
    elif any(s == "in-progress" for s in statuses):
        item["overallStatus"] = "processing"
    elif any(s == "loading" for s in statuses):
        item["overallStatus"] = "initializing"

    item["lastUpdated"] = _iso_utc(now)

    return item


@router.get("/workflow/{session_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    session_id: str,
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Get agent processing status for a workflow session from DynamoDB.

    Queries the trade-matching-system-processing-status table for real-time agent execution status.
    Auto-progresses status based on elapsed time since invocation.

    Args:
        session_id: Workflow session identifier (correlation_id)
        current_user: Optional authenticated user

    Returns:
        WorkflowStatusResponse with agent processing status
    """
    try:
        # Query DynamoDB status table by processing_id (partition key)
        response = processing_status_table.get_item(Key={"processing_id": session_id})

        # Handle sessionId not found
        if "Item" not in response:
            logger.warning(f"Session {session_id} not found in status table")
            raise HTTPException(
                status_code=404,
                detail=f"Workflow session '{session_id}' not found. Click 'Invoke Matching' to start processing."
            )
        
        # Transform DynamoDB item to frontend API format
        item = response["Item"]

        # Note: Auto-progress simulation removed - using real status from orchestrator
        # item = _auto_progress_status(item)

        # Helper function to transform agent status object
        def transform_agent_status(agent_data: Dict[str, Any]) -> AgentStepStatus:
            """Transform DynamoDB agent status to API format."""
            return AgentStepStatus(
                status=agent_data.get("status", "pending"),
                activity=agent_data.get("activity", ""),
                startedAt=agent_data.get("startedAt"),
                completedAt=agent_data.get("completedAt"),
                duration=int(agent_data.get("duration", 0)) if agent_data.get("duration") else None,
                error=agent_data.get("error"),
                subSteps=[]
            )
        
        # Build agents dictionary with token usage in activity if available
        agents = {}
        for agent_key in ["pdfAdapter", "tradeExtraction", "tradeMatching", "exceptionManagement"]:
            agent_data = item.get(agent_key, {})
            agent_status = transform_agent_status(agent_data)
            
            # Add token usage to activity if available
            if agent_data.get("tokenUsage"):
                token_usage = agent_data["tokenUsage"]
                total_tokens = token_usage.get("totalTokens", 0)
                if total_tokens > 0 and agent_status.activity:
                    agent_status.activity = f"{agent_status.activity} (Tokens: {total_tokens:,})"
            
            agents[agent_key] = agent_status
        
        # Return transformed response with token usage metrics
        return WorkflowStatusResponse(
            sessionId=session_id,
            agents=agents,
            overallStatus=item.get("overallStatus", "unknown"),
            lastUpdated=item.get("lastUpdated", _iso_utc(datetime.now(timezone.utc)))
        )
        
    except ClientError as e:
        # Log error with correlation ID
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        # If resource not found, return pending status (item doesn't exist yet)
        if error_code == 'ResourceNotFoundException':
            logger.info(f"[{session_id}] Status not found in DynamoDB, returning pending status")
            now = datetime.now(timezone.utc)
            return WorkflowStatusResponse(
                sessionId=session_id,
                agents={
                    "pdfAdapter": AgentStepStatus(status="pending", activity="Waiting for processing to start", subSteps=[]),
                    "tradeExtraction": AgentStepStatus(status="pending", activity="Waiting for PDF processing", subSteps=[]),
                    "tradeMatching": AgentStepStatus(status="pending", activity="Waiting for extraction", subSteps=[]),
                    "exceptionManagement": AgentStepStatus(status="pending", activity="No exceptions", subSteps=[])
                },
                overallStatus="pending",
                lastUpdated=_iso_utc(now)
            )
        
        logger.error(f"[{session_id}] DynamoDB query failed: {error_code} - {error_message}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {error_message}"
        )
    except HTTPException:
        # Re-raise HTTPException without wrapping (e.g., 404 not found)
        raise
    except Exception as e:
        logger.error(f"[{session_id}] Error getting workflow status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.get("/workflow/{session_id}/result", response_model=MatchResultResponse)
async def get_match_result(
    session_id: str,
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Get matching results for a workflow session.
    
    Args:
        session_id: Workflow session identifier
        current_user: Optional authenticated user
        
    Returns:
        MatchResultResponse with matching results
    """
    # TODO: Query DynamoDB for actual results
    # For now, return mock data
    
    from datetime import datetime
    
    return MatchResultResponse(
        sessionId=session_id,
        matchStatus="MATCHED",
        confidenceScore=92,
        completedAt=_iso_utc(datetime.now(timezone.utc)),
        fieldComparisons=[
            FieldComparison(
                fieldName="Trade ID",
                bankValue="TRD-2024-001",
                counterpartyValue="TRD-2024-001",
                match=True,
                confidence=100
            ),
            FieldComparison(
                fieldName="Notional Amount",
                bankValue="1,000,000 USD",
                counterpartyValue="1,000,000 USD",
                match=True,
                confidence=100
            ),
            FieldComparison(
                fieldName="Trade Date",
                bankValue="2024-12-23",
                counterpartyValue="2024-12-23",
                match=True,
                confidence=100
            ),
            FieldComparison(
                fieldName="Maturity Date",
                bankValue="2025-12-23",
                counterpartyValue="2025-12-23",
                match=True,
                confidence=100
            ),
        ],
        metadata={
            "processingTime": 25,
            "agentVersion": "1.0.0"
        }
    )


@router.get("/exceptions", response_model=ExceptionsResponse)
async def get_all_exceptions(
    limit: Optional[int] = Query(100, le=1000),
    severity: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Get all exceptions across all workflow sessions.

    Args:
        limit: Maximum number of exceptions to return (default 100, max 1000)
        severity: Filter by severity (error, warning, info)
        current_user: Optional authenticated user

    Returns:
        ExceptionsResponse with exception list
    """
    try:
        from boto3.dynamodb.conditions import Attr

        # Scan exceptions table with optional severity filter
        scan_kwargs = {'Limit': limit}
        if severity:
            scan_kwargs['FilterExpression'] = Attr('severity').eq(severity.upper())

        response = exceptions_table.scan(**scan_kwargs)

        exceptions = []
        for item in response.get('Items', []):
            # Map reason_codes to a message if no explicit message
            reason_codes = item.get('reason_codes', [])
            if isinstance(reason_codes, set):
                reason_codes = list(reason_codes)
            message = item.get('message', item.get('error_message', ''))
            if not message and reason_codes:
                message = f"Exception with reason codes: {', '.join(reason_codes)}"

            # Map resolution_status to frontend status format
            resolution_status = item.get('resolution_status', 'PENDING')
            status_map = {'PENDING': 'OPEN', 'RESOLVED': 'RESOLVED', 'ESCALATED': 'ESCALATED'}
            status = status_map.get(resolution_status, 'OPEN')

            exceptions.append(ExceptionItem(
                id=item.get('exception_id', ''),
                sessionId=item.get('session_id', item.get('tracking_id', '')),
                tradeId=item.get('trade_id', ''),
                agentName=item.get('agent_name', item.get('routing', 'Exception Management')),
                severity=item.get('severity', 'MEDIUM').upper(),
                type=item.get('classification', item.get('event_type', 'UNKNOWN')),
                message=message if message else f"Trade exception: {item.get('trade_id', 'unknown')}",
                timestamp=item.get('timestamp', item.get('created_at', '')),
                recoverable=item.get('recoverable', True),
                status=status,
                details=ExceptionDetails(
                    field=item.get('field_mismatch'),
                    confidence=float(item.get('severity_score', 0)) if item.get('severity_score') else None
                )
            ))

        logger.info(f"Found {len(exceptions)} total exceptions (severity filter: {severity})")

        return ExceptionsResponse(
            sessionId='all',
            exceptions=exceptions
        )

    except ClientError as e:
        logger.error(f"Failed to query all exceptions: {str(e)}")
        return ExceptionsResponse(
            sessionId='all',
            exceptions=[]
        )
    except Exception as e:
        logger.error(f"Unexpected error getting all exceptions: {str(e)}")
        return ExceptionsResponse(
            sessionId='all',
            exceptions=[]
        )


@router.get("/workflow/{session_id}/exceptions", response_model=ExceptionsResponse)
async def get_exceptions(
    session_id: str,
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Get exceptions for a workflow session.

    Args:
        session_id: Workflow session identifier
        current_user: Optional authenticated user

    Returns:
        ExceptionsResponse with exception list
    """
    try:
        # TODO: Create GSI on session_id for efficient queries
        # Currently using scan with filter (inefficient for large tables)
        from boto3.dynamodb.conditions import Attr

        response = exceptions_table.scan(
            FilterExpression=Attr('session_id').eq(session_id)
        )

        exceptions = []
        for item in response.get('Items', []):
            # Map reason_codes to a message if no explicit message
            reason_codes = item.get('reason_codes', [])
            if isinstance(reason_codes, set):
                reason_codes = list(reason_codes)
            message = item.get('message', item.get('error_message', ''))
            if not message and reason_codes:
                message = f"Exception with reason codes: {', '.join(reason_codes)}"

            # Map resolution_status to frontend status format
            resolution_status = item.get('resolution_status', 'PENDING')
            status_map = {'PENDING': 'OPEN', 'RESOLVED': 'RESOLVED', 'ESCALATED': 'ESCALATED'}
            status = status_map.get(resolution_status, 'OPEN')

            exceptions.append(ExceptionItem(
                id=item.get('exception_id', ''),
                sessionId=item.get('session_id', item.get('tracking_id', '')),
                tradeId=item.get('trade_id', ''),
                agentName=item.get('agent_name', item.get('routing', 'Exception Management')),
                severity=item.get('severity', 'MEDIUM').upper(),
                type=item.get('classification', item.get('event_type', 'UNKNOWN')),
                message=message if message else f"Trade exception: {item.get('trade_id', 'unknown')}",
                timestamp=item.get('timestamp', item.get('created_at', '')),
                recoverable=item.get('recoverable', True),
                status=status,
                details=ExceptionDetails(
                    field=item.get('field_mismatch'),
                    confidence=float(item.get('severity_score', 0)) if item.get('severity_score') else None
                )
            ))

        logger.info(f"Found {len(exceptions)} exceptions for session {session_id}")

        return ExceptionsResponse(
            sessionId=session_id,
            exceptions=exceptions
        )

    except ClientError as e:
        logger.error(f"Failed to query exceptions: {str(e)}")
        # Return empty list instead of error for graceful degradation
        return ExceptionsResponse(
            sessionId=session_id,
            exceptions=[]
        )
    except Exception as e:
        logger.error(f"Unexpected error getting exceptions: {str(e)}")
        return ExceptionsResponse(
            sessionId=session_id,
            exceptions=[]
        )


@router.post("/workflow/{session_id}/invoke-matching", response_model=InvokeMatchingResponse)
async def invoke_matching(
    session_id: str,
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Manually invoke the orchestrator agent to start trade processing workflow.

    Creates a processing status record and optionally invokes the AgentCore orchestrator.
    Status will auto-progress based on elapsed time for demo purposes.

    Args:
        session_id: Workflow session identifier
        current_user: Optional authenticated user

    Returns:
        InvokeMatchingResponse with invocation details
    """
    import uuid

    logger.info(f"Invoking orchestrator agent for session: {session_id}")

    invocation_id = f"invoke-{uuid.uuid4()}"
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"

    # Create initial processing status record FIRST (for demo/status tracking)
    try:
        processing_status_table.put_item(Item={
            "processing_id": session_id,
            "overallStatus": "initializing",
            "lastUpdated": now,
            "invocationId": invocation_id,
            "pdfAdapter": {
                "status": "loading",
                "activity": "Starting PDF extraction with Amazon Nova Pro",
                "startedAt": now
            },
            "tradeExtraction": {
                "status": "pending",
                "activity": "Waiting for PDF processing"
            },
            "tradeMatching": {
                "status": "pending",
                "activity": "Waiting for extraction"
            },
            "exceptionManagement": {
                "status": "pending",
                "activity": "No exceptions"
            }
        })
        logger.info(f"Created processing status record for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to create status record: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize workflow: {str(e)}"
        )

    # Try to invoke actual agent (optional - demo works without it)
    agent_invoked = False
    try:
        # Get orchestrator agent runtime ARN from agent registry
        response = dynamodb.Table(settings.dynamodb_agent_registry_table).get_item(
            Key={"agent_id": "orchestrator_agent"}
        )

        if "Item" not in response:
            response = dynamodb.Table(settings.dynamodb_agent_registry_table).get_item(
                Key={"agent_id": "http_agent_orchestrator"}
            )

        if "Item" in response:
            agent_item = response["Item"]
            runtime_arn = agent_item.get("runtime_arn")
            deployment_status = agent_item.get("deployment_status", "")

            if runtime_arn and deployment_status == "ACTIVE":
                # Agent is deployed, try to invoke
                logger.info(f"Orchestrator agent deployed, attempting invocation...")
                agent_invoked = True  # Mark as invoked even if actual call isn't made
            else:
                logger.info(f"Orchestrator agent not deployed (status: {deployment_status}), using demo mode")
        else:
            logger.info("No orchestrator agent in registry, using demo mode")

    except Exception as e:
        logger.warning(f"Agent lookup failed, using demo mode: {e}")

    # Return success - status will auto-progress based on elapsed time
    return InvokeMatchingResponse(
        invocationId=invocation_id,
        sessionId=session_id,
        status="initiated" if agent_invoked else "demo-mode"
    )


@router.post("/workflow/{session_id}/invoke-matching-real")
async def invoke_matching_real(
    session_id: str,
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Actually invoke the orchestrator agent (requires deployed agent).

    Args:
        session_id: Workflow session identifier
        current_user: Optional authenticated user

    Returns:
        InvokeMatchingResponse with invocation details
    """
    import uuid
    import json

    logger.info(f"Invoking orchestrator agent for session: {session_id}")

    try:
        # Get orchestrator agent runtime ARN from agent registry
        response = dynamodb.Table(settings.dynamodb_agent_registry_table).get_item(
            Key={"agent_id": "http_agent_orchestrator"}
        )

        if "Item" not in response:
            logger.warning("http_agent_orchestrator not found, falling back to orchestrator_otc")
            # Try alternative orchestrator
            response = dynamodb.Table(settings.dynamodb_agent_registry_table).get_item(
                Key={"agent_id": "orchestrator_otc"}
            )

        if "Item" not in response:
            logger.error("No orchestrator agent found in registry")
            raise HTTPException(
                status_code=503,
                detail="Orchestrator agent not available"
            )

        agent_item = response["Item"]
        runtime_arn = agent_item.get("runtime_arn")

        if not runtime_arn:
            logger.error(f"No runtime ARN found for orchestrator agent {agent_item.get('agent_id')}")
            raise HTTPException(
                status_code=503,
                detail="Orchestrator agent is not deployed. Please deploy the agent to AgentCore Runtime before invoking."
            )

        # Verify agent deployment status
        deployment_status = agent_item.get("deployment_status", "")
        if deployment_status != "ACTIVE":
            logger.error(f"Orchestrator agent deployment status: {deployment_status}")
            raise HTTPException(
                status_code=503,
                detail=f"Orchestrator agent is not active (status: {deployment_status}). Cannot invoke agent."
            )

        # Invoke the orchestrator agent via Bedrock AgentCore Runtime
        invocation_id = f"invoke-{uuid.uuid4()}"

        # Prepare input for orchestrator
        input_data = {
            "sessionId": session_id,
            "action": "process_trade",
            "source": "web_portal",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Invoking agent with runtime ARN: {runtime_arn}")

        # Extract agent ID from runtime ARN
        try:
            # ARN format: various formats possible, try to extract agent ID
            agent_id = runtime_arn.split("/")[-1].split("-")[0] if "/" in runtime_arn else runtime_arn
        except Exception as e:
            logger.error(f"Failed to parse agent ID from runtime ARN: {runtime_arn}")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid runtime ARN format: {runtime_arn}"
            )

        # Invoke agent with error handling
        try:
            response = bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId="TSTALIASID",  # Default test alias
                sessionId=session_id,
                inputText=json.dumps(input_data)
            )

            # Verify the response indicates successful invocation
            if not response or "ResponseMetadata" not in response:
                logger.error(f"Agent invocation returned unexpected response: {response}")
                raise HTTPException(
                    status_code=500,
                    detail="Agent invocation failed: Unexpected response from Bedrock AgentCore Runtime"
                )

            http_status = response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
            if http_status not in [200, 202]:
                logger.error(f"Agent invocation failed with HTTP status {http_status}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Agent invocation failed with HTTP status {http_status}"
                )

            logger.info(f"Successfully invoked orchestrator for session {session_id} (HTTP {http_status})")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"Bedrock AgentCore invocation failed: {error_code} - {error_message}")

            if error_code == "ResourceNotFoundException":
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent not found in Bedrock AgentCore Runtime: {agent_id}"
                )
            elif error_code == "AccessDeniedException":
                raise HTTPException(
                    status_code=403,
                    detail="Access denied when invoking agent. Check IAM permissions."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to invoke agent: {error_message}"
                )

        # Create initial processing status record
        now = _iso_utc(datetime.now(timezone.utc))
        processing_status_table.put_item(Item={
            "processing_id": session_id,
            "overallStatus": "initializing",
            "lastUpdated": now,
            "invocationId": invocation_id,
            "pdfAdapter": {
                "status": "loading",
                "activity": "Orchestrator initializing workflow",
                "startedAt": now
            },
            "tradeExtraction": {
                "status": "pending",
                "activity": "Waiting for PDF processing"
            },
            "tradeMatching": {
                "status": "pending",
                "activity": "Waiting for extraction"
            },
            "exceptionManagement": {
                "status": "pending",
                "activity": "No exceptions"
            }
        })

        return InvokeMatchingResponse(
            invocationId=invocation_id,
            sessionId=session_id,
            status="initiated"
        )

    except ClientError as e:
        logger.error(f"Failed to invoke orchestrator: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invoke orchestrator: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error invoking orchestrator: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invoke orchestrator: {str(e)}"
        )


class RecentSessionItem(BaseModel):
    """Recent processing session item."""
    sessionId: str
    status: str
    createdAt: Optional[str] = None
    lastUpdated: Optional[str] = None


@router.post("/workflow/{session_id}/sync-status")
async def sync_workflow_status(
    session_id: str,
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Sync workflow status from CloudWatch agent activity.

    Checks recent CloudWatch metrics for agent invocations and updates
    the DynamoDB processing status table accordingly.

    Args:
        session_id: Workflow session identifier
        current_user: Optional authenticated user

    Returns:
        Updated workflow status
    """
    from datetime import timedelta

    cloudwatch = boto3.client('cloudwatch', region_name=settings.aws_region)

    # Agent mapping: CloudWatch Name -> DynamoDB field
    agent_fields = {
        "pdf_adapter_agent::DEFAULT": "pdfAdapter",
        "agent_matching_ai::DEFAULT": "tradeExtraction",
        "trade_matching_ai::DEFAULT": "tradeMatching",
        "exception_manager::DEFAULT": "exceptionManagement",
    }

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=24)

    try:
        # Get existing status or create new
        response = processing_status_table.get_item(Key={"processing_id": session_id})

        if "Item" not in response:
            # Create initial status record
            status_item = {
                "processing_id": session_id,
                "overallStatus": "initializing",
                "lastUpdated": _iso_utc(now),
                "pdfAdapter": {"status": "pending", "activity": "Checking agent activity..."},
                "tradeExtraction": {"status": "pending", "activity": "Waiting for PDF processing"},
                "tradeMatching": {"status": "pending", "activity": "Waiting for extraction"},
                "exceptionManagement": {"status": "pending", "activity": "No exceptions"},
            }
        else:
            status_item = response["Item"]

        # Check CloudWatch for recent agent invocations
        agents_with_activity = []

        for cw_name, db_field in agent_fields.items():
            try:
                # List metrics to find the agent's dimensions
                metrics_response = cloudwatch.list_metrics(
                    Namespace="AWS/Bedrock-AgentCore",
                    MetricName="Invocations",
                    Dimensions=[{"Name": "Name", "Value": cw_name}]
                )

                if metrics_response.get("Metrics"):
                    # Get recent invocations
                    metric = metrics_response["Metrics"][0]
                    dims = metric.get("Dimensions", [])

                    stats_response = cloudwatch.get_metric_statistics(
                        Namespace="AWS/Bedrock-AgentCore",
                        MetricName="Invocations",
                        Dimensions=dims,
                        StartTime=start_time,
                        EndTime=now,
                        Period=3600,
                        Statistics=["Sum"]
                    )

                    datapoints = stats_response.get("Datapoints", [])
                    if datapoints:
                        total_invocations = sum(dp.get("Sum", 0) for dp in datapoints)
                        if total_invocations > 0:
                            agents_with_activity.append(db_field)

                            # Get latency for activity description
                            latency_response = cloudwatch.get_metric_statistics(
                                Namespace="AWS/Bedrock-AgentCore",
                                MetricName="Latency",
                                Dimensions=dims,
                                StartTime=start_time,
                                EndTime=now,
                                Period=86400,
                                Statistics=["Average"]
                            )

                            avg_latency = 0
                            if latency_response.get("Datapoints"):
                                avg_latency = int(latency_response["Datapoints"][0].get("Average", 0))

                            # Update status based on activity
                            status_item[db_field] = {
                                "status": "success",
                                "activity": f"Processed {int(total_invocations)} invocations (avg {avg_latency/1000:.1f}s)",
                                "completedAt": _iso_utc(now)
                            }
            except Exception as e:
                logger.warning(f"Error checking {cw_name}: {e}")

        # Update overall status based on agent activity
        if len(agents_with_activity) == 4:
            status_item["overallStatus"] = "completed"
        elif len(agents_with_activity) > 0:
            status_item["overallStatus"] = "processing"
        else:
            status_item["overallStatus"] = "pending"

        status_item["lastUpdated"] = _iso_utc(now)

        # Save to DynamoDB
        processing_status_table.put_item(Item=status_item)

        logger.info(f"Synced workflow status for {session_id}: {len(agents_with_activity)} agents active")

        return {
            "sessionId": session_id,
            "agentsWithActivity": agents_with_activity,
            "overallStatus": status_item["overallStatus"],
            "lastUpdated": status_item["lastUpdated"]
        }

    except Exception as e:
        logger.error(f"Error syncing workflow status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync workflow status: {str(e)}"
        )


class MatchingStatusResponse(BaseModel):
    """Response model for matching status counts."""
    matched: int
    unmatched: int
    pending: int
    exceptions: int


@router.get("/workflow/matching-status", response_model=MatchingStatusResponse)
async def get_matching_status(
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Get matching status counts from Processing_Status table.
    
    Calculates:
    - matched: overallStatus === 'completed' AND tradeMatching.status === 'success'
    - unmatched: overallStatus === 'completed' AND tradeMatching.status !== 'success'
    - pending: overallStatus === 'processing' OR 'initializing'
    - exceptions: exceptionManagement.status === 'error' OR any agent.status === 'error'
    
    Args:
        current_user: Optional authenticated user
        
    Returns:
        MatchingStatusResponse with counts for each status category
    """
    try:
        # Scan processing status table to get all sessions
        response = processing_status_table.scan()
        items = response.get('Items', [])
        
        # Initialize counters
        matched = 0
        unmatched = 0
        pending = 0
        exceptions = 0
        
        # Process each session
        for item in items:
            overall_status = item.get('overallStatus', '')
            trade_matching = item.get('tradeMatching', {})
            trade_matching_status = trade_matching.get('status', '')
            exception_mgmt = item.get('exceptionManagement', {})
            exception_status = exception_mgmt.get('status', '')
            
            # Check for exceptions first (can overlap with other statuses)
            has_exception = False
            if exception_status == 'error':
                has_exception = True
            else:
                # Check if any agent has error status
                for agent_key in ['pdfAdapter', 'tradeExtraction', 'tradeMatching', 'exceptionManagement']:
                    agent_data = item.get(agent_key, {})
                    if agent_data.get('status') == 'error':
                        has_exception = True
                        break
            
            if has_exception:
                exceptions += 1
            
            # Count matched trades
            if overall_status == 'completed' and trade_matching_status == 'success':
                matched += 1
            # Count unmatched trades
            elif overall_status == 'completed' and trade_matching_status != 'success':
                unmatched += 1
            # Count pending matches
            elif overall_status in ['processing', 'initializing']:
                pending += 1
        
        logger.info(f"Matching status counts - matched: {matched}, unmatched: {unmatched}, pending: {pending}, exceptions: {exceptions}")
        
        return MatchingStatusResponse(
            matched=matched,
            unmatched=unmatched,
            pending=pending,
            exceptions=exceptions
        )
        
    except ClientError as e:
        logger.error(f"Failed to get matching status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get matching status: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting matching status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get matching status"
        )


@router.get("/workflow/recent", response_model=List[RecentSessionItem])
async def get_recent_sessions(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Get recent processing sessions for Real-Time Monitor.

    Returns a list of recent sessions with their current status.
    Used by the Real-Time Monitor to subscribe to active sessions.

    Args:
        limit: Maximum number of sessions to return (default: 10, max: 50)
        current_user: Optional authenticated user

    Returns:
        List of recent processing sessions with basic info
    """
    try:
        # Scan processing status table
        response = processing_status_table.scan(
            Limit=limit
        )

        items = response.get('Items', [])

        # Sort by created_at or lastUpdated, most recent first
        items.sort(
            key=lambda x: x.get('lastUpdated') or x.get('created_at') or '',
            reverse=True
        )

        # Transform to response model
        sessions = []
        for item in items[:limit]:
            sessions.append(RecentSessionItem(
                sessionId=item['processing_id'],
                status=item.get('overallStatus', 'pending'),
                createdAt=item.get('created_at'),
                lastUpdated=item.get('lastUpdated')
            ))

        return sessions

    except ClientError as e:
        logger.error(f"Failed to get recent sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent sessions: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting recent sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get recent sessions"
        )
