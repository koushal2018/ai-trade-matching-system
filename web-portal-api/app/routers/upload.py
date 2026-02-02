"""
Upload router for trade confirmation PDF files.

Handles file uploads to S3 and initiates agent processing workflow.
"""

import logging
import os
import re
import uuid
import urllib.parse
import json
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from ..auth import get_current_user, optional_auth_or_dev, User
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

# AWS clients
s3_client = boto3.client('s3', region_name=settings.aws_region)
dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=settings.aws_region)

# S3 bucket name (from environment or default)
S3_BUCKET = os.getenv('S3_BUCKET_NAME', 'trade-matching-system-agentcore-production')


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and special characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for S3 keys
    """
    # Remove path separators
    filename = os.path.basename(filename)
    # Remove special characters except alphanumeric, spaces, dots, hyphens, underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Limit length
    return filename[:255]


class PresignedUrlRequest(BaseModel):
    """Request model for presigned URL generation."""
    sourceType: str
    fileName: str
    contentType: str
    existingSessionId: Optional[str] = None  # For pairing bank + counterparty uploads


class UploadResponse(BaseModel):
    """Response model for file upload."""
    uploadId: str
    s3Uri: str
    status: str
    sessionId: str
    traceId: str
    presignedUrl: Optional[str] = None


@router.post("/upload", response_model=UploadResponse)
async def get_presigned_upload_url(
    request: PresignedUrlRequest,
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Generate presigned URL for direct S3 upload from browser.

    Args:
        request: Upload request with sourceType, fileName, contentType
        current_user: Optional authenticated user

    Returns:
        UploadResponse with presigned URL and workflow identifiers

    Raises:
        HTTPException: If validation fails or presigned URL generation fails
    """
    # Validate source type
    if request.sourceType not in ['BANK', 'COUNTERPARTY']:
        raise HTTPException(
            status_code=400,
            detail="Invalid sourceType. Must be 'BANK' or 'COUNTERPARTY'"
        )

    # Validate content type
    if request.contentType != 'application/pdf':
        raise HTTPException(
            status_code=400,
            detail="Invalid content type. Only application/pdf is accepted."
        )

    # Validate file extension
    _, ext = os.path.splitext(request.fileName.lower())
    if ext != '.pdf':
        raise HTTPException(
            status_code=400,
            detail="Invalid file extension. Only .pdf files are accepted."
        )

    # Generate unique identifiers
    upload_id = str(uuid.uuid4())
    trace_id = f"trace-{uuid.uuid4()}"

    # Sanitize filename and construct S3 key
    safe_filename = sanitize_filename(request.fileName)
    safe_filename_no_ext = safe_filename.rsplit('.', 1)[0] if '.' in safe_filename else safe_filename
    document_id = f"{upload_id}-{safe_filename_no_ext}"
    s3_key = f"{request.sourceType}/{upload_id}-{safe_filename}"

    # Use existing session ID if provided (for pairing bank + counterparty uploads)
    # Otherwise create new session ID
    if request.existingSessionId:
        session_id = request.existingSessionId
        logger.info(f"Using existing session ID for paired upload: {session_id}")
    else:
        session_id = f"session-{document_id}"
        logger.info(f"Created new session ID: {session_id}")

    try:
        # Generate presigned URL for PUT operation (15 minute expiry)
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': s3_key,
                'ContentType': 'application/pdf',
                'Metadata': {
                    'source-type': request.sourceType,
                    'upload-id': upload_id,
                    'trace-id': trace_id,
                    'original-filename': urllib.parse.quote(request.fileName),
                    'uploaded-by': current_user.username if current_user else 'anonymous'
                }
            },
            ExpiresIn=900  # 15 minutes
        )

        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"

        logger.info(
            f"Generated presigned URL for upload: {s3_uri}",
            extra={
                'upload_id': upload_id,
                'trace_id': trace_id,
                'source_type': request.sourceType,
                'user': current_user.username if current_user else 'anonymous'
            }
        )

        # Session ID must match orchestrator format
        return UploadResponse(
            uploadId=upload_id,
            s3Uri=s3_uri,
            status='success',
            sessionId=session_id,
            traceId=trace_id,
            presignedUrl=presigned_url
        )

    except ClientError as e:
        logger.error(
            f"Failed to generate presigned URL: {str(e)}",
            extra={
                'upload_id': upload_id,
                'source_type': request.sourceType,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error generating presigned URL: {str(e)}",
            extra={
                'upload_id': upload_id,
                'source_type': request.sourceType,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


class ConfirmUploadRequest(BaseModel):
    """Request model for confirming S3 upload completion."""
    sessionId: str
    s3Uri: str


class ConfirmUploadResponse(BaseModel):
    """Response model for upload confirmation."""
    success: bool
    sessionId: str
    message: str
    agentInvoked: bool
    invocationId: Optional[str] = None


@router.post("/upload/confirm", response_model=ConfirmUploadResponse)
async def confirm_upload_and_invoke_agent(
    request: ConfirmUploadRequest,
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Confirm S3 upload completion and automatically invoke orchestrator agent.

    This endpoint should be called by the frontend after successfully uploading
    to S3 using the presigned URL. It verifies the file exists in S3 and then
    automatically triggers the orchestrator agent to begin processing.

    Args:
        request: Upload confirmation with sessionId and s3Uri
        current_user: Optional authenticated user

    Returns:
        ConfirmUploadResponse with invocation status

    Raises:
        HTTPException: If S3 verification fails or agent invocation fails
    """
    session_id = request.sessionId
    s3_uri = request.s3Uri

    logger.info(f"Confirming upload for session {session_id}: {s3_uri}")

    try:
        # Parse S3 URI to get bucket and key
        if not s3_uri.startswith('s3://'):
            raise HTTPException(status_code=400, detail="Invalid S3 URI format")

        s3_parts = s3_uri.replace('s3://', '').split('/', 1)
        bucket = s3_parts[0]
        key = s3_parts[1] if len(s3_parts) > 1 else ''

        # Verify file exists in S3
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            logger.info(f"Verified S3 object exists: {s3_uri}")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise HTTPException(
                    status_code=404,
                    detail="File not found in S3. Upload may have failed."
                )
            raise

        # Get orchestrator agent from registry
        response = dynamodb.Table(settings.dynamodb_agent_registry_table).get_item(
            Key={"agent_id": "http_agent_orchestrator"}
        )

        if "Item" not in response:
            logger.warning("http_agent_orchestrator not found, trying orchestrator_otc")
            response = dynamodb.Table(settings.dynamodb_agent_registry_table).get_item(
                Key={"agent_id": "orchestrator_otc"}
            )

        agent_invoked = False
        invocation_id = None

        if "Item" in response:
            agent_item = response["Item"]
            runtime_arn = agent_item.get("runtime_arn")

            if runtime_arn:
                # Invoke orchestrator agent via Bedrock AgentCore Runtime
                invocation_id = f"invoke-{uuid.uuid4()}"

                input_data = {
                    "sessionId": session_id,
                    "s3Uri": s3_uri,
                    "action": "process_upload"
                }

                try:
                    logger.info(f"Invoking AgentCore runtime {runtime_arn} for session {session_id}")

                    # Invoke AgentCore runtime
                    response = bedrock_agentcore.invoke_agent_runtime(
                        agentRuntimeArn=runtime_arn,
                        runtimeSessionId=session_id,
                        contentType='application/json',
                        accept='application/json',
                        payload=json.dumps(input_data).encode('utf-8')
                    )

                    logger.info(f"Successfully invoked orchestrator agent for session {session_id}, status: {response.get('statusCode')}")
                    agent_invoked = True

                except Exception as e:
                    logger.error(f"Failed to invoke AgentCore runtime: {str(e)}", exc_info=True)
                    # Don't fail the request - just mark agent as not invoked

        # Create or update processing status record
        processing_status_table = dynamodb.Table(settings.dynamodb_processing_status_table)
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"

        processing_status_table.put_item(Item={
            "processing_id": session_id,
            "overallStatus": "initializing" if agent_invoked else "pending",
            "created_at": now,
            "lastUpdated": now,
            "s3_uri": s3_uri,
            "pdfAdapter": {
                "status": "loading" if agent_invoked else "pending",
                "activity": "Orchestrator initializing workflow" if agent_invoked else "Waiting for agent invocation",
                "startedAt": now if agent_invoked else None
            },
            "tradeExtraction": {
                "status": "pending",
                "activity": "Waiting for PDF adapter completion"
            },
            "tradeMatching": {
                "status": "pending",
                "activity": "Waiting for extraction completion"
            },
            "exceptionManagement": {
                "status": "pending",
                "activity": "Monitoring for exceptions"
            }
        })

        message = "Upload confirmed and agent invoked successfully" if agent_invoked else "Upload confirmed, agent invocation pending"

        return ConfirmUploadResponse(
            success=True,
            sessionId=session_id,
            message=message,
            agentInvoked=agent_invoked,
            invocationId=invocation_id
        )

    except HTTPException:
        raise
    except ClientError as e:
        logger.error(f"AWS error confirming upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm upload: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error confirming upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@router.post("/upload/direct", response_model=UploadResponse)
async def upload_confirmation_direct(
    file: UploadFile = File(...),
    sourceType: str = Form(...),
    sessionId: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Upload trade confirmation PDF to S3.
    
    Args:
        file: PDF file to upload
        sourceType: Either 'BANK' or 'COUNTERPARTY'
        sessionId: Optional existing session ID (for matching bank and counterparty uploads)
        current_user: Optional authenticated user
        
    Returns:
        UploadResponse with upload details and workflow identifiers
        
    Raises:
        HTTPException: If upload fails or validation fails
    """
    # Validate source type
    if sourceType not in ['BANK', 'COUNTERPARTY']:
        raise HTTPException(
            status_code=400,
            detail="Invalid sourceType. Must be 'BANK' or 'COUNTERPARTY'"
        )
    
    # Validate file type (content type)
    if not file.content_type or file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF files are accepted."
        )
    
    # Validate file extension
    if file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        if ext != '.pdf':
            raise HTTPException(
                status_code=400,
                detail="Invalid file extension. Only .pdf files are accepted."
            )
    
    # Validate file size (10 MB limit) - check before reading if size is available
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10 MB limit."
        )
    
    # Read file content
    file_content = await file.read()
    
    # Double-check size after reading (in case size wasn't available)
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10 MB limit."
        )
    
    # Generate unique identifiers
    upload_id = str(uuid.uuid4())
    trace_id = f"trace-{uuid.uuid4()}"

    # Sanitize filename and construct S3 key with appropriate prefix
    safe_filename = sanitize_filename(file.filename or 'unknown.pdf')
    # Remove .pdf extension for document_id (orchestrator uses this for session_id)
    safe_filename_no_ext = safe_filename.rsplit('.', 1)[0] if '.' in safe_filename else safe_filename
    document_id = f"{upload_id}-{safe_filename_no_ext}"
    s3_key = f"{sourceType}/{upload_id}-{safe_filename}"

    # Use existing session ID if provided (for pairing bank + counterparty uploads)
    # Otherwise create new session ID
    if sessionId:
        session_id_to_use = sessionId
        logger.info(f"Using existing session ID for paired upload: {sessionId}")
    else:
        session_id_to_use = f"session-{document_id}"
        logger.info(f"Created new session ID: {session_id_to_use}")
    
    try:
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType='application/pdf',
            Metadata={
                'source-type': sourceType,
                'upload-id': upload_id,
                'trace-id': trace_id,
                # URL-encode filename to handle special characters
                'original-filename': urllib.parse.quote(file.filename or 'unknown.pdf'),
                'uploaded-by': current_user.username if current_user else 'anonymous'
            }
        )
        
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
        
        logger.info(
            f"File uploaded successfully: {s3_uri}",
            extra={
                'upload_id': upload_id,
                'trace_id': trace_id,
                'source_type': sourceType,
                'file_size': len(file_content),
                'user': current_user.username if current_user else 'anonymous'
            }
        )
        
        # Session ID matches orchestrator format or uses provided session ID for pairing
        return UploadResponse(
            uploadId=upload_id,
            s3Uri=s3_uri,
            status='success',
            sessionId=session_id_to_use,
            traceId=trace_id
        )
        
    except ClientError as e:
        logger.error(
            f"S3 upload failed: {str(e)}",
            extra={
                'upload_id': upload_id,
                'source_type': sourceType,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file to S3: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected upload error: {str(e)}",
            extra={
                'upload_id': upload_id,
                'source_type': sourceType,
                'error': str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during upload"
        )
