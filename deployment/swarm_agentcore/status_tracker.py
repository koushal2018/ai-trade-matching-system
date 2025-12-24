"""
Status Tracker Helper for HTTP Agent Orchestrator

Provides simple helper methods for writing workflow status to DynamoDB.
This is NOT a Strands agent - just utility functions for the orchestrator.

⚠️ CRITICAL - PARTITION KEY NAME:
The table 'trade-matching-system-processing-status' uses 'processing_id' as partition key.
DO NOT use 'sessionId' - this has been a recurring issue (missed 10-20+ times).

Verify with:
aws dynamodb describe-table --table-name trade-matching-system-processing-status \
  --region us-east-1 --query 'Table.KeySchema'

Expected output: [{"AttributeName": "processing_id", "KeyType": "HASH"}]
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class StatusTracker:
    """Helper class for tracking workflow status in DynamoDB."""
    
    def __init__(
        self, 
        table_name: str = "trade-matching-system-processing-status",
        region_name: str = "us-east-1"
    ):
        """Initialize status tracker with DynamoDB table."""
        self.table_name = table_name
        self.region_name = region_name
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        logger.info(f"StatusTracker initialized with table: {table_name}")
    
    def initialize_status(
        self,
        session_id: str,
        correlation_id: str,
        document_id: str,
        source_type: str
    ) -> bool:
        """
        Initialize workflow status with all agents set to pending.
        
        Returns:
            True if successful, False otherwise (non-blocking)
        """
        try:
            now = datetime.now(timezone.utc)
            expires_at = int((now + timedelta(days=90)).timestamp())
            
            item = {
                "processing_id": {"S": session_id},  # Partition key (actual table schema)
                "correlationId": {"S": correlation_id},
                "documentId": {"S": document_id},
                "sourceType": {"S": source_type},
                "overallStatus": {"S": "initializing"},
                "pdfAdapter": {"M": self._pending_status()},
                "tradeExtraction": {"M": self._pending_status()},
                "tradeMatching": {"M": self._pending_status()},
                "exceptionManagement": {"M": self._pending_status()},
                "totalTokenUsage": {"M": {
                    "inputTokens": {"N": "0"},
                    "outputTokens": {"N": "0"},
                    "totalTokens": {"N": "0"}
                }},
                "createdAt": {"S": now.isoformat() + "Z"},
                "lastUpdated": {"S": now.isoformat() + "Z"},
                "expiresAt": {"N": str(expires_at)}
            }
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            
            logger.info(f"[{correlation_id}] Status initialized for session: {session_id}")
            return True
            
        except Exception as e:
            logger.warning(f"[{correlation_id}] Failed to initialize status: {e}")
            return False
    
    def update_agent_status(
        self,
        session_id: str,
        correlation_id: str,
        agent_key: str,
        status: str,
        agent_response: Optional[Dict[str, Any]] = None,
        started_at: Optional[str] = None
    ) -> bool:
        """
        Update status for a specific agent.
        
        Args:
            session_id: Session ID
            correlation_id: Correlation ID for logging
            agent_key: Agent key (pdfAdapter, tradeExtraction, etc.)
            status: Status value (in-progress, success, error)
            agent_response: Optional agent response with token usage
            started_at: Optional start timestamp for duration calculation
            
        Returns:
            True if successful, False otherwise (non-blocking)
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Build agent status object
            agent_status = {
                "status": {"S": status},
                "activity": {"S": self._get_activity_message(agent_key, status)},
                "lastUpdated": {"S": now.isoformat() + "Z"}
            }
            
            if status == "in-progress":
                agent_status["startedAt"] = {"S": now.isoformat() + "Z"}
            
            if status in ["success", "error"] and agent_response:
                agent_status["completedAt"] = {"S": now.isoformat() + "Z"}
                
                # Calculate duration if we have started_at
                if started_at:
                    try:
                        started = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        duration = (now - started).total_seconds()
                        agent_status["duration"] = {"N": str(round(duration, 3))}
                    except Exception:
                        pass
                
                # Extract token usage from agent response
                token_usage = agent_response.get("token_usage", {})
                if token_usage:
                    agent_status["tokenUsage"] = {"M": {
                        "inputTokens": {"N": str(token_usage.get("input_tokens", 0))},
                        "outputTokens": {"N": str(token_usage.get("output_tokens", 0))},
                        "totalTokens": {"N": str(token_usage.get("total_tokens", 0))}
                    }}
                
                # Add error if failed
                if status == "error":
                    error_msg = agent_response.get("error", "Unknown error")
                    agent_status["error"] = {"S": str(error_msg)}
            
            # Determine overall status
            overall_status = "failed" if status == "error" else "processing"
            
            # Update DynamoDB
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={"processing_id": {"S": session_id}},  # ⚠️ CRITICAL: Use processing_id, NOT sessionId
                UpdateExpression="SET #agent = :status, lastUpdated = :updated, overallStatus = :overall",
                ExpressionAttributeNames={"#agent": agent_key},
                ExpressionAttributeValues={
                    ":status": {"M": agent_status},
                    ":updated": {"S": now.isoformat() + "Z"},
                    ":overall": {"S": overall_status}
                }
            )
            
            logger.info(f"[{correlation_id}] Updated {agent_key} status to {status}")
            return True
            
        except Exception as e:
            logger.warning(f"[{correlation_id}] Failed to update {agent_key} status: {e}")
            return False
    
    def finalize_status(
        self,
        session_id: str,
        correlation_id: str,
        overall_status: str
    ) -> bool:
        """
        Mark workflow as completed or failed.
        
        Returns:
            True if successful, False otherwise (non-blocking)
        """
        try:
            now = datetime.now(timezone.utc)
            
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={"processing_id": {"S": session_id}},  # ⚠️ CRITICAL: Use processing_id, NOT sessionId
                UpdateExpression="SET overallStatus = :status, lastUpdated = :updated",
                ExpressionAttributeValues={
                    ":status": {"S": overall_status},
                    ":updated": {"S": now.isoformat() + "Z"}
                }
            )
            
            logger.info(f"[{correlation_id}] Finalized workflow status: {overall_status}")
            return True
            
        except Exception as e:
            logger.warning(f"[{correlation_id}] Failed to finalize status: {e}")
            return False
    
    @staticmethod
    def _pending_status() -> Dict[str, Any]:
        """Return pending status object in DynamoDB format."""
        return {
            "status": {"S": "pending"},
            "activity": {"S": "Waiting to start"},
            "tokenUsage": {"M": {
                "inputTokens": {"N": "0"},
                "outputTokens": {"N": "0"},
                "totalTokens": {"N": "0"}
            }}
        }
    
    @staticmethod
    def _get_activity_message(agent_key: str, status: str) -> str:
        """Get human-readable activity message."""
        messages = {
            "pdfAdapter": {
                "in-progress": "Extracting text from PDF document",
                "success": "Text extraction complete",
                "error": "Text extraction failed"
            },
            "tradeExtraction": {
                "in-progress": "Extracting structured trade data",
                "success": "Trade data extraction complete",
                "error": "Trade extraction failed"
            },
            "tradeMatching": {
                "in-progress": "Matching bank and counterparty trades",
                "success": "Trade matching complete",
                "error": "Trade matching failed"
            },
            "exceptionManagement": {
                "in-progress": "Processing exceptions",
                "success": "Exception handling complete",
                "error": "Exception handling failed"
            }
        }
        return messages.get(agent_key, {}).get(status, "Processing")
