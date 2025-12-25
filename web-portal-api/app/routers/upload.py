"""
Upload router for trade confirmation PDF files.

Handles file uploads to S3 and initiates agent processing workflow.
"""

import logging
import os
import re
import uuid
import urllib.parse
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from ..auth import get_current_user, User
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

# S3 client
s3_client = boto3.client('s3', region_name=settings.aws_region)

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


class UploadResponse(BaseModel):
    """Response model for file upload."""
    uploadId: str
    s3Uri: str
    status: str
    sessionId: str
    traceId: str


@router.post("/upload", response_model=UploadResponse)
async def upload_confirmation(
    file: UploadFile = File(...),
    sourceType: str = Form(...),
    sessionId: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user)
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
        
        # Session ID must match orchestrator format: session-{document_id}
        # document_id = {upload_id}-{filename_without_extension}
        return UploadResponse(
            uploadId=upload_id,
            s3Uri=s3_uri,
            status='success',
            sessionId=f"session-{document_id}",  # Match orchestrator format exactly
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
