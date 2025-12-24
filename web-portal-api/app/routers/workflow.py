"""
Workflow router for agent processing status and results.

Provides endpoints for tracking agent processing workflow.
Queries AWS Bedrock AgentCore for real agent execution status.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from ..auth import get_current_user, User
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["workflow"])

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


class ExceptionItem(BaseModel):
    """Exception item."""
    id: str
    agentName: str
    severity: str  # error, warning, info
    message: str
    timestamp: str
    recoverable: bool


class ExceptionsResponse(BaseModel):
    """Response model for exceptions."""
    sessionId: str
    exceptions: List[ExceptionItem]


class InvokeMatchingResponse(BaseModel):
    """Response model for invoke matching."""
    invocationId: str
    sessionId: str
    status: str


@router.get("/workflow/{session_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get agent processing status for a workflow session from DynamoDB.
    
    Queries the trade-matching-system-processing-status table for real-time agent execution status.
    
    Args:
        session_id: Workflow session identifier (correlation_id)
        current_user: Optional authenticated user
        
    Returns:
        WorkflowStatusResponse with real agent processing status from DynamoDB
    """
    try:
        # Query DynamoDB status table by processing_id (partition key)
        # ⚠️ CRITICAL: Table uses 'processing_id' as partition key, NOT 'sessionId'
        # This has been a recurring issue - verify with:
        # aws dynamodb describe-table --table-name trade-matching-system-processing-status
        response = processing_status_table.get_item(Key={"processing_id": session_id})
        
        # Handle sessionId not found - return all pending
        if "Item" not in response:
            logger.info(f"Session {session_id} not found in status table, returning pending status")
            now = datetime.now(timezone.utc)
            return WorkflowStatusResponse(
                sessionId=session_id,
                agents={
                    "pdfAdapter": AgentStepStatus(
                        status="pending",
                        activity="Waiting for upload",
                        subSteps=[]
                    ),
                    "tradeExtraction": AgentStepStatus(
                        status="pending",
                        activity="Waiting for PDF processing",
                        subSteps=[]
                    ),
                    "tradeMatching": AgentStepStatus(
                        status="pending",
                        activity="Waiting for extraction",
                        subSteps=[]
                    ),
                    "exceptionManagement": AgentStepStatus(
                        status="pending",
                        activity="No exceptions",
                        subSteps=[]
                    )
                },
                overallStatus="pending",
                lastUpdated=now.isoformat() + "Z"
            )
        
        # Transform DynamoDB item to frontend API format
        item = response["Item"]
        
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
            lastUpdated=item.get("lastUpdated", datetime.now(timezone.utc).isoformat() + "Z")
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
                lastUpdated=now.isoformat() + "Z"
            )
        
        logger.error(f"[{session_id}] DynamoDB query failed: {error_code} - {error_message}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {error_message}"
        )
    except Exception as e:
        logger.error(f"[{session_id}] Error getting workflow status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.get("/workflow/{session_id}/result", response_model=MatchResultResponse)
async def get_match_result(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user)
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
        completedAt=datetime.utcnow().isoformat() + "Z",
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


@router.get("/workflow/{session_id}/exceptions", response_model=ExceptionsResponse)
async def get_exceptions(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get exceptions for a workflow session.
    
    Args:
        session_id: Workflow session identifier
        current_user: Optional authenticated user
        
    Returns:
        ExceptionsResponse with exception list
    """
    # TODO: Query DynamoDB exceptions table
    # For now, return empty list
    
    return ExceptionsResponse(
        sessionId=session_id,
        exceptions=[]
    )


@router.post("/workflow/{session_id}/invoke-matching", response_model=InvokeMatchingResponse)
async def invoke_matching(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Manually invoke the Trade Matching Agent.
    
    Args:
        session_id: Workflow session identifier
        current_user: Optional authenticated user
        
    Returns:
        InvokeMatchingResponse with invocation details
    """
    # TODO: Invoke AgentCore Trade Matching Agent
    # For now, return mock response
    
    import uuid
    
    logger.info(f"Invoking Trade Matching Agent for session: {session_id}")
    
    return InvokeMatchingResponse(
        invocationId=f"invoke-{uuid.uuid4()}",
        sessionId=session_id,
        status="initiated"
    )
