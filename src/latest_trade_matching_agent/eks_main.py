"""
EKS-optimized FastAPI application for trade document processing.
This module provides HTTP endpoints for event-driven trade document processing on Kubernetes.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio
import boto3
import tempfile
import os
from pathlib import Path
from datetime import datetime
import logging
import json
import shutil
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

try:
    from .crew_fixed import LatestTradeMatchingAgent
    from mcp import StdioServerParameters
    from crewai_tools import MCPServerAdapter
    CREWAI_AVAILABLE = True
except ImportError as e:
    # CrewAI dependencies not available - continue with basic API functionality
    LatestTradeMatchingAgent = None
    CREWAI_AVAILABLE = False

# Configure structured logging
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Request/Response Models
class ProcessingRequest(BaseModel):
    """Request model for trade document processing"""
    s3_bucket: str = Field(..., description="S3 bucket containing the document")
    s3_key: str = Field(..., description="S3 key (path) to the document")
    source_type: str = Field(..., description="Document source: BANK or COUNTERPARTY")
    event_time: str = Field(..., description="Timestamp of the S3 event")
    unique_identifier: str = Field(..., description="Unique identifier for this processing")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ProcessingResponse(BaseModel):
    """Response model for processing requests"""
    status: str
    message: str
    unique_identifier: str
    processing_id: str

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    version: str = "1.0.0"

class ReadinessResponse(BaseModel):
    """Readiness check response model"""
    status: str
    timestamp: str
    services: Dict[str, bool]

# Global processing status tracker
processing_status: Dict[str, Dict[str, Any]] = {}

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Trade Matching System", version="1.0.0")

    # Initialize AWS clients
    try:
        app.state.s3_client = boto3.client('s3')
        app.state.dynamodb_client = boto3.client('dynamodb')
        app.state.sns_client = boto3.client('sns')
        logger.info("AWS clients initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize AWS clients", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Trade Matching System")
    # Clean up temporary files
    temp_dir = Path("/tmp/processing")
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

# Initialize FastAPI application
app = FastAPI(
    title="Trade Matching System",
    version="1.0.0",
    description="Event-driven trade document processing on EKS",
    lifespan=lifespan
)

# Health and Readiness Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for Kubernetes liveness probe.
    Returns basic health status without checking external dependencies.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes readiness probe.
    Verifies connectivity to required AWS services.
    """
    services_status = {
        "s3": False,
        "dynamodb": False,
        "sns": False
    }

    try:
        # Test S3 connectivity
        app.state.s3_client.list_buckets()
        services_status["s3"] = True
    except Exception as e:
        logger.warning("S3 connectivity check failed", error=str(e))

    try:
        # Test DynamoDB connectivity
        app.state.dynamodb_client.list_tables()
        services_status["dynamodb"] = True
    except Exception as e:
        logger.warning("DynamoDB connectivity check failed", error=str(e))

    try:
        # Test SNS connectivity (if configured)
        if os.getenv('SNS_TOPIC_ARN'):
            app.state.sns_client.list_topics()
            services_status["sns"] = True
        else:
            services_status["sns"] = True  # Mark as ready if not configured
    except Exception as e:
        logger.warning("SNS connectivity check failed", error=str(e))

    # Determine overall readiness
    is_ready = all(services_status.values())

    if not is_ready:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready. Services status: {services_status}"
        )

    return ReadinessResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        services=services_status
    )

# Main Processing Endpoint
@app.post("/process", response_model=ProcessingResponse)
async def process_trade_document(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Process trade document from S3 event trigger.
    Initiates asynchronous processing and returns immediately.
    """
    # Generate processing ID
    processing_id = f"{request.unique_identifier}_{int(datetime.utcnow().timestamp())}"

    try:
        # Validate source type
        if request.source_type not in ["BANK", "COUNTERPARTY"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source_type: {request.source_type}. Must be BANK or COUNTERPARTY"
            )

        # Log processing initiation
        logger.info(
            "Processing initiated",
            processing_id=processing_id,
            s3_bucket=request.s3_bucket,
            s3_key=request.s3_key,
            source_type=request.source_type,
            unique_identifier=request.unique_identifier
        )

        # Initialize processing status
        processing_status[processing_id] = {
            "status": "initiated",
            "message": f"Processing started for {request.s3_key}",
            "progress": 0,
            "unique_identifier": request.unique_identifier,
            "source_type": request.source_type,
            "s3_bucket": request.s3_bucket,
            "s3_key": request.s3_key,
            "started_at": datetime.utcnow().isoformat(),
            "metadata": request.metadata
        }

        # Add background task
        background_tasks.add_task(
            process_document_async,
            request,
            processing_id,
            app.state.s3_client,
            app.state.sns_client
        )

        return ProcessingResponse(
            status="initiated",
            message="Processing initiated successfully",
            unique_identifier=request.unique_identifier,
            processing_id=processing_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to initiate processing",
            processing_id=processing_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate processing: {str(e)}"
        )

# Status Monitoring Endpoint
@app.get("/status/{processing_id}")
async def get_processing_status(processing_id: str):
    """
    Get processing status for a specific document.
    Returns current status and progress information.
    """
    if processing_id not in processing_status:
        raise HTTPException(
            status_code=404,
            detail=f"Processing ID {processing_id} not found"
        )

    return processing_status[processing_id]

# List Active Processing Jobs
@app.get("/status")
async def list_processing_status():
    """
    List all active processing jobs.
    Returns summary of all ongoing and recent processing tasks.
    """
    # Filter out old completed jobs (older than 1 hour)
    cutoff_time = datetime.utcnow().timestamp() - 3600
    active_status = {}

    for pid, status in processing_status.items():
        # Parse processing ID to get timestamp
        try:
            _, timestamp_str = pid.rsplit('_', 1)
            timestamp = int(timestamp_str)

            # Keep if recent or still processing
            if (timestamp > cutoff_time or
                status.get("status") in ["initiated", "downloading", "processing"]):
                active_status[pid] = status
        except (ValueError, AttributeError):
            # Keep if can't parse timestamp
            active_status[pid] = status

    return {
        "total": len(active_status),
        "jobs": active_status
    }

# Background Processing Function
async def process_document_async(
    request: ProcessingRequest,
    processing_id: str,
    s3_client,
    sns_client
):
    """
    Background task to process trade document.
    Downloads from S3, runs CrewAI pipeline, and stores results.
    """
    try:
        # Update status: Downloading
        processing_status[processing_id].update({
            "status": "downloading",
            "message": "Downloading document from S3",
            "progress": 10
        })

        logger.info(
            "Downloading document from S3",
            processing_id=processing_id,
            s3_bucket=request.s3_bucket,
            s3_key=request.s3_key
        )

        # Create temporary directory structure
        temp_dir = Path(f"/tmp/processing/{processing_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Create folder structure matching source type
        local_dir = temp_dir / "data" / request.source_type
        local_dir.mkdir(parents=True, exist_ok=True)

        # Download file from S3
        local_file_path = local_dir / Path(request.s3_key).name
        s3_client.download_file(
            request.s3_bucket,
            request.s3_key,
            str(local_file_path)
        )

        logger.info(
            "Document downloaded successfully",
            processing_id=processing_id,
            local_path=str(local_file_path)
        )

        # Update status: Processing
        processing_status[processing_id].update({
            "status": "processing",
            "message": "Running CrewAI processing pipeline",
            "progress": 30
        })

        if not CREWAI_AVAILABLE:
            # Simulate processing when CrewAI is not available
            logger.warning(
                "CrewAI not available - running in simulation mode",
                processing_id=processing_id
            )

            processing_status[processing_id].update({
                "status": "processing",
                "message": "Running in simulation mode (CrewAI not available)",
                "progress": 60
            })

            # Simulate processing time
            import time
            time.sleep(2)

            result = f"Simulated processing result for {request.unique_identifier}"
        else:
            logger.info(
                "Starting CrewAI processing with MCP DynamoDB integration",
                processing_id=processing_id
            )

            # Set up DynamoDB MCP server parameters
            dynamodb_params = StdioServerParameters(
                command="uvx",
                args=["awslabs.dynamodb-mcp-server@latest"],
                env={
                    "DDB-MCP-READONLY": "false",
                    "AWS_PROFILE": "default",
                    "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
                    "FASTMCP_LOG_LEVEL": "ERROR"
                }
            )

            # Use context manager to ensure proper cleanup with extended timeout
            with MCPServerAdapter(dynamodb_params, connect_timeout=120) as dynamodb_tools:
                logger.info(
                    "Connected to DynamoDB MCP server",
                    processing_id=processing_id,
                    tool_count=len(list(dynamodb_tools))
                )

                # Create crew instance with DynamoDB tools
                crew_instance = LatestTradeMatchingAgent(
                    dynamodb_tools=list(dynamodb_tools),
                    request_context=request.dict()
                )

                # Prepare inputs for crew
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                inputs = {
                    'document_path': str(local_file_path),
                    'unique_identifier': request.unique_identifier,
                    's3_bucket': request.s3_bucket,
                    's3_key': request.s3_key,
                    'source_type': request.source_type,
                    'timestamp': timestamp,
                    'dynamodb_bank_table': os.getenv('DYNAMODB_BANK_TABLE', 'BankTradeData'),
                    'dynamodb_counterparty_table': os.getenv('DYNAMODB_COUNTERPARTY_TABLE', 'CounterpartyTradeData')
                }

                # Update progress
                processing_status[processing_id].update({
                    "status": "processing",
                    "message": "CrewAI agents processing document",
                    "progress": 60
                })

                # Execute crew
                result = crew_instance.crew().kickoff(inputs=inputs)

            logger.info(
                "CrewAI processing completed",
                processing_id=processing_id,
                result_length=len(str(result))
            )

            # Update status: Completed
            processing_status[processing_id].update({
                "status": "completed",
                "message": "Document processing completed successfully",
                "progress": 100,
                "completed_at": datetime.utcnow().isoformat(),
                "result": str(result)[:1000]  # Store first 1000 chars of result
            })

        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Send completion notification
        await send_completion_notification(
            request,
            processing_id,
            "success",
            sns_client
        )

    except Exception as e:
        logger.error(
            "Processing failed",
            processing_id=processing_id,
            error=str(e),
            exc_info=True
        )

        # Update status: Failed
        processing_status[processing_id].update({
            "status": "failed",
            "message": f"Processing failed: {str(e)}",
            "progress": -1,
            "failed_at": datetime.utcnow().isoformat(),
            "error": str(e)
        })

        # Send failure notification
        await send_completion_notification(
            request,
            processing_id,
            "failure",
            sns_client,
            str(e)
        )

# SNS Notification Function
async def send_completion_notification(
    request: ProcessingRequest,
    processing_id: str,
    status: str,
    sns_client,
    error: Optional[str] = None
):
    """
    Send SNS notification on processing completion.
    Notifies subscribers about success or failure.
    """
    try:
        topic_arn = os.getenv('SNS_TOPIC_ARN')

        if not topic_arn:
            logger.debug("SNS notifications not configured")
            return

        # Prepare message
        message_body = {
            "processing_id": processing_id,
            "unique_identifier": request.unique_identifier,
            "source_type": request.source_type,
            "s3_bucket": request.s3_bucket,
            "s3_key": request.s3_key,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }

        if error:
            message_body["error"] = error

        # Publish to SNS
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=f"Trade Processing {status.title()} - {request.source_type}",
            Message=json.dumps(message_body, indent=2),
            MessageAttributes={
                'source_type': {'DataType': 'String', 'StringValue': request.source_type},
                'status': {'DataType': 'String', 'StringValue': status},
                'processing_id': {'DataType': 'String', 'StringValue': processing_id}
            }
        )

        logger.info(
            "Notification sent",
            processing_id=processing_id,
            status=status,
            topic_arn=topic_arn
        )

    except Exception as e:
        logger.error(
            "Failed to send notification",
            processing_id=processing_id,
            error=str(e)
        )

# Metrics Endpoint (for Prometheus)
@app.get("/metrics")
async def get_metrics():
    """
    Expose metrics for Prometheus monitoring.
    Returns processing statistics and system health metrics.
    """
    metrics = []

    # Processing metrics
    total_jobs = len(processing_status)
    completed_jobs = sum(1 for s in processing_status.values() if s.get("status") == "completed")
    failed_jobs = sum(1 for s in processing_status.values() if s.get("status") == "failed")
    active_jobs = sum(1 for s in processing_status.values()
                      if s.get("status") in ["initiated", "downloading", "processing"])

    metrics.append(f"# HELP trade_processing_total Total number of processing jobs")
    metrics.append(f"# TYPE trade_processing_total counter")
    metrics.append(f"trade_processing_total {total_jobs}")

    metrics.append(f"# HELP trade_processing_completed Completed processing jobs")
    metrics.append(f"# TYPE trade_processing_completed counter")
    metrics.append(f"trade_processing_completed {completed_jobs}")

    metrics.append(f"# HELP trade_processing_failed Failed processing jobs")
    metrics.append(f"# TYPE trade_processing_failed counter")
    metrics.append(f"trade_processing_failed {failed_jobs}")

    metrics.append(f"# HELP trade_processing_active Currently active processing jobs")
    metrics.append(f"# TYPE trade_processing_active gauge")
    metrics.append(f"trade_processing_active {active_jobs}")

    return "\n".join(metrics)

# Main entry point
if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8080"))
    workers = int(os.getenv("APP_WORKERS", "1"))

    # Run with uvicorn
    uvicorn.run(
        "eks_main:app",
        host=host,
        port=port,
        workers=workers,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "json",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"]
            }
        }
    )