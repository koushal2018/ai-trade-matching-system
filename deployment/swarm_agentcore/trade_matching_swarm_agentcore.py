"""
Trade Matching Swarm - AgentCore Runtime Entrypoint

This module provides the AgentCore Runtime entrypoint for deploying the
Trade Matching Swarm as a serverless agent with memory integration.

Supports two modes:
1. Strands Swarm Mode: Local agents with emergent collaboration
2. A2A Mode: Agent-to-Agent communication with deployed AgentCore agents

The mode is determined by the A2A_MODE environment variable.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging
import asyncio

from bedrock_agentcore import BedrockAgentCoreApp

# Initialize AgentCore app
app = BedrockAgentCoreApp()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import swarm creation function
from trade_matching_swarm import (
    create_trade_matching_swarm_with_memory,
    get_config
)

# Import A2A integration (optional)
try:
    from a2a_client_integration import (
        process_trade_with_a2a,
        get_bearer_token_from_env
    )
    A2A_AVAILABLE = True
except ImportError as e:
    logger.warning(f"A2A integration not available: {e}")
    A2A_AVAILABLE = False
    
    # Create dummy functions for graceful degradation
    async def process_trade_with_a2a(*args, **kwargs):
        raise RuntimeError("A2A integration not available. Install dependencies: pip install python-a2a httpx")
    
    def get_bearer_token_from_env():
        raise RuntimeError("A2A integration not available")


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Trade Matching Swarm.
    
    This function is called by AgentCore Runtime when the agent is invoked.
    It supports two modes:
    1. Strands Swarm Mode (default): Local agents with emergent collaboration
    2. A2A Mode: Agent-to-Agent communication with deployed AgentCore agents
    
    Mode is determined by A2A_MODE environment variable.
    
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
        Processing result with status and details
    """
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
        
        # Check execution mode
        a2a_mode = os.environ.get("A2A_MODE", "false").lower() == "true"
        
        logger.info(f"Processing trade confirmation: {document_id}")
        logger.info(f"Execution mode: {'A2A' if a2a_mode else 'Strands Swarm'}")
        logger.info(f"S3 Location: {document_path}")
        logger.info(f"Source Type: {source_type}")
        
        start_time = datetime.utcnow()
        
        if a2a_mode:
            # A2A Mode: Use deployed AgentCore agents
            logger.info("Using A2A mode - communicating with deployed AgentCore agents")
            
            # Check if A2A is available
            if not A2A_AVAILABLE:
                logger.error("A2A mode requested but A2A integration not available")
                return {
                    "success": False,
                    "document_id": document_id,
                    "correlation_id": correlation_id,
                    "error": "A2A integration not available. Install dependencies: pip install python-a2a httpx",
                    "error_type": "A2ANotAvailableError"
                }
            
            # Get bearer token from environment
            try:
                bearer_token = get_bearer_token_from_env()
            except (ValueError, RuntimeError) as e:
                logger.error(f"A2A authentication failed: {e}")
                return {
                    "success": False,
                    "document_id": document_id,
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": "AuthenticationError"
                }
            
            # Execute A2A workflow
            try:
                # Run async A2A processing
                result = asyncio.run(process_trade_with_a2a(
                    document_path=document_path,
                    source_type=source_type,
                    document_id=document_id,
                    correlation_id=correlation_id,
                    bearer_token=bearer_token
                ))
                
                processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                result["processing_time_ms"] = processing_time_ms
                result["execution_mode"] = "A2A"
                
                logger.info(f"A2A workflow completed for {document_id}")
                return result
                
            except Exception as e:
                logger.error(f"A2A workflow failed: {e}", exc_info=True)
                processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return {
                    "success": False,
                    "document_id": document_id,
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_mode": "A2A",
                    "processing_time_ms": processing_time_ms
                }
        
        else:
            # Strands Swarm Mode: Local agents with memory integration
            logger.info("Using Strands Swarm mode - local agents with emergent collaboration")
            
            # Get configuration from environment
            config = get_config()
            memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
            
            if not memory_id:
                logger.warning("AGENTCORE_MEMORY_ID not set - memory integration disabled")
            
            # Parse S3 path
            if document_path.startswith("s3://"):
                parts = document_path.replace("s3://", "").split("/", 1)
                bucket = parts[0]
                key = parts[1]
            else:
                bucket = config["s3_bucket"]
                key = document_path
            
            # Create swarm with memory integration
            swarm = create_trade_matching_swarm_with_memory(
                document_id=document_id,
                memory_id=memory_id
            )
            
            # Build task prompt
            memory_note = " All agents have access to historical patterns stored in memory to improve decision-making." if memory_id else ""
            
            task = f"""Process this trade confirmation PDF and match it against existing trades.

## Document Details
- Document ID: {document_id}
- S3 Location: s3://{bucket}/{key}
- Source Type: {source_type}
- Correlation ID: {correlation_id}

## Goal
Extract trade data from the PDF, store it in DynamoDB, analyze matches against existing trades, and handle any exceptions that arise.

The swarm will coordinate the work - each agent will decide when to hand off based on their expertise and the task context.{memory_note}
"""
            
            logger.info(f"Starting swarm processing for {document_id}")
            
            # Execute swarm
            result = swarm(task)
            
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"Swarm processing completed for {document_id}")
            logger.info(f"Status: {result.status}")
            logger.info(f"Execution count: {result.execution_count}")
            
            return {
                "success": True,
                "document_id": document_id,
                "correlation_id": correlation_id,
                "status": str(result.status),
                "node_history": [node.node_id for node in result.node_history],
                "execution_count": result.execution_count,
                "execution_time_ms": result.execution_time,
                "processing_time_ms": processing_time_ms,
                "accumulated_usage": result.accumulated_usage,
                "execution_mode": "Strands Swarm"
            }
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {
            "success": False,
            "document_id": document_id if 'document_id' in locals() else "unknown",
            "correlation_id": correlation_id if 'correlation_id' in locals() else "unknown",
            "error": str(e),
            "error_type": "ValidationError"
        }
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        
        return {
            "success": False,
            "document_id": document_id if 'document_id' in locals() else "unknown",
            "correlation_id": correlation_id if 'correlation_id' in locals() else "unknown",
            "error": str(e),
            "error_type": type(e).__name__
        }


if __name__ == "__main__":
    # For local testing
    test_payload = {
        "document_path": "data/BANK/FAB_26933659.pdf",
        "source_type": "BANK",
        "document_id": "test_doc_123",
        "correlation_id": "test_corr_123"
    }
    
    result = invoke(test_payload, None)
    print(json.dumps(result, indent=2, default=str))
