"""
Status writer for orchestrator agent.
Writes workflow status to DynamoDB after each agent step.

This implementation uses the Strands SDK use_aws tool when available,
with boto3 fallback for compatibility.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

# Try to import use_aws from strands_tools
try:
    from strands_tools import use_aws
    USE_STRANDS_TOOLS_AWS = True
except ImportError:
    USE_STRANDS_TOOLS_AWS = False
    import boto3

logger = logging.getLogger(__name__)

class StatusWriter:
    """Writes workflow status to DynamoDB for web portal consumption."""
    
    def __init__(self, table_name: str = "trade-matching-system-processing-status", 
                 region_name: str = "us-east-1"):
        """Initialize status writer with DynamoDB table."""
        self.table_name = table_name
        self.region_name = region_name
        self.use_strands_tool = USE_STRANDS_TOOLS_AWS
        
        # Initialize boto3 client only if not using strands tool
        if not self.use_strands_tool:
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        
        logger.info(f"StatusWriter initialized with table: {table_name}, using_strands_tool: {self.use_strands_tool}")
    
    def _call_dynamodb(self, operation: str, parameters: Dict[str, Any], 
                       correlation_id: str) -> Dict[str, Any]:
        """
        Call DynamoDB using use_aws tool.
        
        Args:
            operation: DynamoDB operation (PutItem, UpdateItem, GetItem)
            parameters: Operation parameters (native Python types)
            correlation_id: Correlation ID for logging
            
        Returns:
            Operation result
        """
        # Use strands_tools use_aws - it handles type conversion
        result_json = use_aws(
            service_name="dynamodb",
            operation_name=operation,
            parameters=parameters,
            region=self.region_name,
            label=f"Status write - {operation}"
        )
        result = json.loads(result_json)
        
        if not result.get("success"):
            raise Exception(f"DynamoDB {operation} failed: {result.get('error')}")
        
        return result.get("result", {})
    
    def initialize_status(self, session_id: str, correlation_id: str, 
                         document_id: str, source_type: str) -> None:
        """Write initial status when workflow starts."""
        try:
            now = datetime.now(timezone.utc)
            expires_at = int((now + timedelta(days=90)).timestamp())
            
            # Use boto3 native format (not typed) - boto3 handles conversion
            item = {
                "sessionId": session_id,
                "correlationId": correlation_id,
                "documentId": document_id,
                "sourceType": source_type,
                "overallStatus": "initializing",
                "pdfAdapter": self._pending_status(),
                "tradeExtraction": self._pending_status(),
                "tradeMatching": self._pending_status(),
                "exceptionManagement": self._pending_status(),
                "totalTokenUsage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0},
                "totalDuration": 0.0,
                "createdAt": now.isoformat(),
                "lastUpdated": now.isoformat(),
                "expiresAt": expires_at  # TTL attribute for DynamoDB automatic expiration (matches Terraform config)
            }
            
            if self.use_strands_tool:
                # use_aws expects native Python types, not DynamoDB typed format
                self._call_dynamodb(
                    operation="PutItem",
                    parameters={"TableName": self.table_name, "Item": item},
                    correlation_id=correlation_id
                )
            else:
                # boto3 resource API handles type conversion automatically
                self.table.put_item(Item=item)
            
            logger.info(f"[{correlation_id}] Initialized status for session: {session_id}")
        except Exception as e:
            logger.error(f"[{correlation_id}] Failed to initialize status: {e}")
            # Don't raise - status writes should not break workflow
    
    def update_agent_status(self, session_id: str, correlation_id: str,
                           agent_key: str, status: str, 
                           agent_response: Optional[Dict[str, Any]] = None) -> None:
        """Update status for a specific agent."""
        try:
            now = datetime.now(timezone.utc)
            
            # Build agent status object
            agent_status = {
                "status": status,
                "activity": self._get_activity_message(agent_key, status),
                "lastUpdated": now.isoformat()
            }
            
            if status == "in-progress":
                agent_status["startedAt"] = now.isoformat()
            
            if status in ["success", "error"] and agent_response:
                agent_status["completedAt"] = now.isoformat()
                
                # Use agent-reported processing time (more accurate than timestamp-based calculation)
                # This excludes orchestrator overhead and network latency
                if "processing_time_ms" in agent_response:
                    agent_status["duration"] = round(agent_response["processing_time_ms"] / 1000, 3)
                
                # Extract token usage from agent response
                if "token_usage" in agent_response:
                    agent_status["tokenUsage"] = {
                        "inputTokens": agent_response["token_usage"].get("input_tokens", 0),
                        "outputTokens": agent_response["token_usage"].get("output_tokens", 0),
                        "totalTokens": agent_response["token_usage"].get("total_tokens", 0)
                    }
                
                # Add error if failed
                if status == "error":
                    agent_status["error"] = agent_response.get("error", "Unknown error")
            
            # Update DynamoDB
            update_expression = "SET #agent = :status, lastUpdated = :updated, overallStatus = :overall"
            expression_attribute_names = {"#agent": agent_key}
            expression_attribute_values = {
                ":status": agent_status,
                ":updated": now.isoformat(),
                ":overall": "failed" if status == "error" else "processing"
            }
            
            if self.use_strands_tool:
                # use_aws expects native Python types
                self._call_dynamodb(
                    operation="UpdateItem",
                    parameters={
                        "TableName": self.table_name,
                        "Key": {"sessionId": session_id},
                        "UpdateExpression": update_expression,
                        "ExpressionAttributeNames": expression_attribute_names,
                        "ExpressionAttributeValues": expression_attribute_values
                    },
                    correlation_id=correlation_id
                )
            else:
                # boto3 resource API
                self.table.update_item(
                    Key={"sessionId": session_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeNames=expression_attribute_names,
                    ExpressionAttributeValues=expression_attribute_values
                )
            
            logger.info(f"[{correlation_id}] Updated {agent_key} status to {status}")
            
        except Exception as e:
            logger.error(f"[{correlation_id}] Failed to update {agent_key} status: {e}")
            # Don't raise - status writes should not break workflow
    
    def finalize_status(self, session_id: str, correlation_id: str, 
                       overall_status: str) -> None:
        """Mark workflow as completed or failed."""
        try:
            now = datetime.now(timezone.utc)
            
            if self.use_strands_tool:
                # use_aws expects native Python types
                self._call_dynamodb(
                    operation="UpdateItem",
                    parameters={
                        "TableName": self.table_name,
                        "Key": {"sessionId": session_id},
                        "UpdateExpression": "SET overallStatus = :status, lastUpdated = :updated",
                        "ExpressionAttributeValues": {
                            ":status": overall_status,
                            ":updated": now.isoformat()
                        }
                    },
                    correlation_id=correlation_id
                )
            else:
                # boto3 resource API
                self.table.update_item(
                    Key={"sessionId": session_id},
                    UpdateExpression="SET overallStatus = :status, lastUpdated = :updated",
                    ExpressionAttributeValues={
                        ":status": overall_status,
                        ":updated": now.isoformat()
                    }
                )
            
            logger.info(f"[{correlation_id}] Finalized workflow status: {overall_status}")
            
        except Exception as e:
            logger.error(f"[{correlation_id}] Failed to finalize status: {e}")
            # Don't raise - status writes should not break workflow
    
    @staticmethod
    def _pending_status() -> Dict[str, Any]:
        """Return pending status object."""
        return {
            "status": "pending",
            "activity": "Waiting to start",
            "tokenUsage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0}
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
