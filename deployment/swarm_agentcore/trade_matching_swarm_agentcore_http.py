"""
Trade Matching Swarm - AgentCore Runtime Entrypoint (HTTP Orchestrator)

This version uses HTTP orchestration to call deployed AgentCore agents
instead of running local Strands agents. This is the production mode.

AgentCore Best Practices Implemented:
- Security: IAM-based authentication via SigV4 signing
- Observability: Enhanced logging with correlation tracking and custom spans
- Error Handling: Comprehensive error categorization and retry logic
- Modular Services: Integration with AgentCore Memory for workflow state
"""

import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging
import asyncio

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# Initialize AgentCore app
app = BedrockAgentCoreApp()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEPLOYMENT_STAGE = os.getenv("DEPLOYMENT_STAGE", "development")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
REGION = os.getenv("AWS_REGION", "us-east-1")

# AgentCore Observability Integration
try:
    from bedrock_agentcore.observability import Observability
    observability = Observability(
        service_name="trade_matching_http_orchestrator",
        stage=DEPLOYMENT_STAGE,
        verbosity="high" if DEPLOYMENT_STAGE == "development" else "medium"
    )
    OBSERVABILITY_AVAILABLE = True
    logger.info("✅ AgentCore Observability initialized")
except ImportError:
    observability = None
    OBSERVABILITY_AVAILABLE = False
    logger.warning("⚠️ AgentCore Observability not available")

# Import HTTP orchestrator
from http_agent_orchestrator import TradeMatchingHTTPOrchestrator


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Trade Matching Swarm (HTTP Orchestrator mode).
    
    This entrypoint uses HTTP orchestration to call deployed AgentCore agents.
    Each agent runs in its own AgentCore Runtime instance.
    
    AgentCore Best Practices:
    - Observability: Comprehensive span tracking with custom attributes
    - Error Handling: Categorized errors with retry recommendations
    - Security: IAM-based authentication for agent invocations
    - Performance: Async execution with timeout management
    
    Args:
        payload: Request payload with document_path, source_type, etc.
            Required fields:
            - document_path: S3 path to the PDF (s3://bucket/key or just key)
            - source_type: BANK or COUNTERPARTY
            Optional fields:
            - document_id: Unique document identifier (generated if not provided)
            - correlation_id: Correlation ID for tracing (generated if not provided)
        context: AgentCore Runtime context
        
    Returns:
        Orchestration result with status and details from all agents
    """
    start_time = datetime.utcnow()
    span_context = None
    
    try:
        # Extract parameters from payload
        document_path = payload.get("document_path")
        source_type = payload.get("source_type")
        document_id = payload.get("document_id") or f"doc_{uuid.uuid4().hex[:12]}"
        correlation_id = payload.get("correlation_id") or f"corr_{uuid.uuid4().hex[:12]}"
        
        # Validate required parameters
        if not document_path:
            raise ValueError("document_path is required in payload")
        if not source_type:
            raise ValueError("source_type is required in payload")
        if source_type not in ["BANK", "COUNTERPARTY"]:
            raise ValueError(f"source_type must be BANK or COUNTERPARTY, got: {source_type}")
        
        logger.info(f"Processing trade confirmation: {document_id}")
        logger.info("Execution mode: HTTP Orchestrator (deployed agents)")
        logger.info(f"Document Path: {document_path}")
        logger.info(f"Source Type: {source_type}")
        
        # Start observability span
        if observability:
            try:
                span_context = observability.start_span(f"http_orchestration.{source_type.lower()}")
                span_context.__enter__()
                
                # Set standard AgentCore attributes
                span_context.set_attribute("orchestrator_type", "http")
                span_context.set_attribute("agent_version", AGENT_VERSION)
                span_context.set_attribute("correlation_id", correlation_id)
                span_context.set_attribute("document_id", document_id)
                span_context.set_attribute("source_type", source_type)
                span_context.set_attribute("deployment_stage", DEPLOYMENT_STAGE)
                span_context.set_attribute("orchestration_stage", "initialization")
                
            except Exception as e:
                logger.warning(f"Failed to start observability span: {e}")
                span_context = None
        
        # Create HTTP orchestrator
        orchestrator = TradeMatchingHTTPOrchestrator()
        
        # Update orchestration stage
        if span_context:
            span_context.set_attribute("orchestration_stage", "processing")
        
        # Process trade confirmation using HTTP orchestration
        # Run async function in sync context
        result = asyncio.run(
            orchestrator.process_trade_confirmation(
                document_path=document_path,
                source_type=source_type,
                document_id=document_id,
                correlation_id=correlation_id
            )
        )
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        result["processing_time_ms"] = processing_time_ms
        result["agent_version"] = AGENT_VERSION
        result["deployment_stage"] = DEPLOYMENT_STAGE
        
        # Record success metrics in observability span
        if span_context:
            try:
                span_context.set_attribute("success", True)
                span_context.set_attribute("orchestration_stage", "completed")
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                
                # Track agent execution counts
                workflow_steps = result.get("workflow_steps", {})
                span_context.set_attribute("agents_invoked", len(workflow_steps))
                span_context.set_attribute("agent_names", ",".join(workflow_steps.keys()))
                
                # Performance classification
                if processing_time_ms < 30000:  # < 30 seconds
                    span_context.set_attribute("performance_tier", "fast")
                elif processing_time_ms < 60000:  # < 60 seconds
                    span_context.set_attribute("performance_tier", "normal")
                else:
                    span_context.set_attribute("performance_tier", "slow")
                    
            except Exception as e:
                logger.warning(f"Failed to set span attributes: {e}")
        
        logger.info(f"HTTP orchestration completed in {processing_time_ms:.2f}ms")
        
        return result
        
    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error: {e}")
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if span_context:
            try:
                span_context.set_attribute("success", False)
                span_context.set_attribute("error_category", "validation")
                span_context.set_attribute("error_type", "ValueError")
                span_context.set_attribute("error_message", str(e)[:500])
                span_context.set_attribute("processing_time_ms", processing_time_ms)
            except Exception:
                pass
        
        return {
            "success": False,
            "error": str(e),
            "error_type": "ValidationError",
            "error_category": "validation",
            "document_id": payload.get("document_id", "unknown"),
            "correlation_id": payload.get("correlation_id", "unknown"),
            "processing_time_ms": processing_time_ms,
            "execution_mode": "HTTP Orchestrator",
            "retry_recommended": False
        }
        
    except asyncio.TimeoutError as e:
        # Timeout errors
        logger.error(f"Orchestration timeout: {e}")
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if span_context:
            try:
                span_context.set_attribute("success", False)
                span_context.set_attribute("error_category", "performance")
                span_context.set_attribute("error_type", "TimeoutError")
                span_context.set_attribute("error_message", str(e)[:500])
                span_context.set_attribute("processing_time_ms", processing_time_ms)
            except Exception:
                pass
        
        return {
            "success": False,
            "error": "Orchestration timed out",
            "error_type": "TimeoutError",
            "error_category": "performance",
            "document_id": payload.get("document_id", "unknown"),
            "correlation_id": payload.get("correlation_id", "unknown"),
            "processing_time_ms": processing_time_ms,
            "execution_mode": "HTTP Orchestrator",
            "retry_recommended": True
        }
        
    except Exception as e:
        # General errors
        logger.error(f"HTTP orchestration failed: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Enhanced error categorization
        error_str = str(e).lower()
        if "agent" in error_str or "invocation" in error_str:
            error_category = "agent_communication"
            retry_recommended = True
        elif "network" in error_str or "connection" in error_str:
            error_category = "network"
            retry_recommended = True
        elif "permission" in error_str or "access" in error_str:
            error_category = "security"
            retry_recommended = False
        else:
            error_category = "unknown"
            retry_recommended = True
        
        if span_context:
            try:
                span_context.set_attribute("success", False)
                span_context.set_attribute("error_category", error_category)
                span_context.set_attribute("error_type", type(e).__name__)
                span_context.set_attribute("error_message", str(e)[:500])
                span_context.set_attribute("processing_time_ms", processing_time_ms)
            except Exception:
                pass
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "error_category": error_category,
            "document_id": payload.get("document_id", "unknown"),
            "correlation_id": payload.get("correlation_id", "unknown"),
            "processing_time_ms": processing_time_ms,
            "execution_mode": "HTTP Orchestrator",
            "retry_recommended": retry_recommended
        }
    
    finally:
        # Close observability span
        if span_context:
            try:
                span_context.__exit__(None, None, None)
            except Exception:
                pass


@app.ping
def health_check() -> PingStatus:
    """
    Health check endpoint for AgentCore Runtime.
    
    Verifies that the HTTP orchestrator can communicate with deployed agents.
    In production, this should validate connectivity to all downstream agents.
    
    Returns:
        PingStatus.HEALTHY if all systems operational
    """
    try:
        # Basic health check - verify environment configuration
        required_env_vars = ["AWS_REGION"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            return PingStatus.UNHEALTHY
        
        # TODO: Add connectivity checks to downstream agents in production
        # For now, return healthy if basic configuration is present
        return PingStatus.HEALTHY
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return PingStatus.UNHEALTHY


if __name__ == "__main__":
    """Let AgentCore Runtime control the execution."""
    app.run()
