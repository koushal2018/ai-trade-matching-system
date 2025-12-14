"""
Trade Matching Swarm - AgentCore Runtime Entrypoint (Simplified)

This is a simplified version that only supports Strands Swarm mode
for local development and testing. Use this for `agentcore dev`.

For A2A mode, use the full trade_matching_swarm_agentcore.py after
setting up the A2A dependencies.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

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


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Trade Matching Swarm (Strands mode only).
    
    This simplified entrypoint only supports Strands Swarm mode with local agents.
    Use this for development and testing with `agentcore dev`.
    
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
        Swarm execution result with status and details
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
        
        logger.info(f"Processing trade confirmation: {document_id}")
        logger.info("Execution mode: Strands Swarm (local agents)")
        logger.info(f"S3 Location: {document_path}")
        logger.info(f"Source Type: {source_type}")
        
        start_time = datetime.utcnow()
        
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