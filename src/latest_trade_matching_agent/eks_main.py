"""
EKS-optimized FastAPI application for health and readiness checks.
This module provides HTTP endpoints for Kubernetes liveness and readiness probes.

Note: CrewAI processing has been removed. For trade processing, use the Strands Swarm
implementation in deployment/swarm/trade_matching_swarm.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import os
from datetime import datetime
from typing import Dict
from contextlib import asynccontextmanager

# CrewAI has been removed - this API now only provides health/readiness checks
# For trade processing, use the Strands Swarm implementation in deployment/swarm/

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

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Trade Matching System Health API", version="1.0.0")

    # Initialize AWS clients for health checks
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
    logger.info("Shutting down Trade Matching System Health API")

# Initialize FastAPI application
app = FastAPI(
    title="Trade Matching System Health API",
    version="1.0.0",
    description="Health and readiness checks for Kubernetes deployment",
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

# Processing endpoint removed - use Strands Swarm implementation instead
# See deployment/swarm/trade_matching_swarm.py for trade processing

# Status and metrics endpoints removed - this API now only provides health/readiness checks

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