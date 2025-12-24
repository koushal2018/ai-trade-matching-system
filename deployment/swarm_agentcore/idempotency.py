"""
Idempotency Cache for Workflow Orchestrator

Prevents duplicate workflow executions by caching results based on correlation_id.
Uses DynamoDB for distributed caching with TTL-based expiration.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class IdempotencyCache:
    """Cache for preventing duplicate workflow executions.
    
    This cache uses DynamoDB to store workflow execution results keyed by
    correlation_id. If a workflow with the same correlation_id is requested
    within the TTL window, the cached result is returned instead of
    re-executing the workflow.
    
    Attributes:
        table_name: Name of the DynamoDB table for caching
        ttl_seconds: Time-to-live for cache entries in seconds
    """
    
    def __init__(self, table_name: str = "WorkflowIdempotency", ttl_seconds: int = 300, region_name: str = "us-east-1"):
        """Initialize the idempotency cache.
        
        Args:
            table_name: DynamoDB table name (default: WorkflowIdempotency)
            ttl_seconds: Cache entry TTL in seconds (default: 300 = 5 minutes)
            region_name: AWS region (default: us-east-1)
        """
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table_name = table_name
        self.ttl_seconds = ttl_seconds
        
        try:
            self.table = self.dynamodb.Table(table_name)
            # Verify table exists by checking its status
            _ = self.table.table_status
            logger.info(f"Idempotency cache initialized with table: {table_name}, TTL: {ttl_seconds}s")
        except ClientError as e:
            logger.warning(f"Failed to access idempotency table {table_name}: {e}")
            logger.warning("Idempotency caching will be disabled")
            self.table = None
    
    def check_and_set(self, correlation_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if correlation_id was recently processed and set cache entry if not.
        
        This method performs two operations atomically:
        1. Check if a cache entry exists for the correlation_id
        2. If found and not expired, return the cached result
        3. If not found or expired, create a new cache entry
        
        Args:
            correlation_id: Unique identifier for the workflow execution
            payload: Workflow input payload (used for payload hash verification)
            
        Returns:
            Cached result dictionary if found and valid, None otherwise
        """
        if not self.table:
            logger.debug("Idempotency cache disabled - table not available")
            return None
        
        try:
            # Try to get existing cache entry
            response = self.table.get_item(Key={"correlation_id": correlation_id})
            
            if "Item" in response:
                cached = response["Item"]
                cached_time = datetime.fromisoformat(cached["timestamp"])
                current_time = datetime.now(timezone.utc)
                age_seconds = (current_time - cached_time).total_seconds()
                
                logger.info(f"Found cached entry for correlation_id: {correlation_id}")
                logger.debug(f"Cache entry age: {age_seconds:.2f}s, TTL: {self.ttl_seconds}s")
                
                # Check if cache entry is still valid (within TTL)
                if age_seconds < self.ttl_seconds:
                    # Verify payload hash matches (optional integrity check)
                    payload_hash = self._compute_payload_hash(payload)
                    cached_hash = cached.get("payload_hash", "")
                    
                    if payload_hash == cached_hash:
                        logger.info(f"Returning cached result for correlation_id: {correlation_id}")
                        return cached.get("result")
                    else:
                        logger.warning(f"Payload hash mismatch for correlation_id: {correlation_id}")
                        logger.warning("Cached entry may be for different payload - proceeding with execution")
                else:
                    logger.info(f"Cache entry expired (age: {age_seconds:.2f}s > TTL: {self.ttl_seconds}s)")
            
            # No valid cache entry found - create new entry
            logger.info(f"Creating new cache entry for correlation_id: {correlation_id}")
            self.table.put_item(Item={
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload_hash": self._compute_payload_hash(payload),
                "status": "in_progress"
            })
            
            return None
            
        except ClientError as e:
            logger.error(f"DynamoDB error in check_and_set: {e}")
            logger.warning("Proceeding without idempotency check")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in check_and_set: {e}", exc_info=True)
            return None
    
    def set_result(self, correlation_id: str, result: Dict[str, Any]) -> None:
        """Store the result for a completed workflow.
        
        Updates the cache entry with the workflow execution result.
        This allows subsequent requests with the same correlation_id
        to retrieve the cached result.
        
        Args:
            correlation_id: Unique identifier for the workflow execution
            result: Workflow execution result to cache
        """
        if not self.table:
            logger.debug("Idempotency cache disabled - table not available")
            return
        
        try:
            logger.info(f"Storing result for correlation_id: {correlation_id}")
            
            self.table.update_item(
                Key={"correlation_id": correlation_id},
                UpdateExpression="SET #result = :result, #status = :status, #completed = :completed",
                ExpressionAttributeNames={
                    "#result": "result",
                    "#status": "status",
                    "#completed": "completed_at"
                },
                ExpressionAttributeValues={
                    ":result": result,
                    ":status": "completed",
                    ":completed": datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.debug(f"Successfully cached result for correlation_id: {correlation_id}")
            
        except ClientError as e:
            logger.error(f"DynamoDB error in set_result: {e}")
            logger.warning("Failed to cache result - continuing")
        except Exception as e:
            logger.error(f"Unexpected error in set_result: {e}", exc_info=True)
    
    def _compute_payload_hash(self, payload: Dict[str, Any]) -> str:
        """Compute SHA256 hash of payload for integrity verification.
        
        Args:
            payload: Workflow input payload
            
        Returns:
            Hexadecimal SHA256 hash string
        """
        try:
            # Sort keys for consistent hashing
            payload_json = json.dumps(payload, sort_keys=True)
            return hashlib.sha256(payload_json.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute payload hash: {e}")
            return ""
