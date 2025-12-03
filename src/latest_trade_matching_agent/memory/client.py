"""AgentCore Memory client for semantic and event memory operations."""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Any
import boto3
from botocore.exceptions import ClientError


class AgentCoreMemoryClient:
    """Client for interacting with Amazon Bedrock AgentCore Memory."""
    
    def __init__(
        self,
        memory_id: Optional[str] = None,
        region: str = "us-east-1"
    ):
        self.region = region
        self.memory_id = memory_id or os.getenv("AGENTCORE_MEMORY_ID", "trade-matching-memory")
        
        # Initialize boto3 clients
        self.bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=region)
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        
        # Fallback table for local development
        self.fallback_table_name = os.getenv("MEMORY_FALLBACK_TABLE", "AgentCoreMemoryFallback")
    
    def _get_fallback_table(self):
        """Get DynamoDB fallback table for local development."""
        return self.dynamodb.Table(self.fallback_table_name)
    
    def _compute_embedding_key(self, content: str) -> str:
        """Compute a hash key for content-based retrieval."""
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    async def store_semantic(
        self,
        content: str,
        metadata: dict[str, Any],
        namespace: str = "default"
    ) -> dict:
        """
        Store content in semantic memory for similarity-based retrieval.
        
        Args:
            content: Text content to store
            metadata: Additional metadata to associate with the content
            namespace: Logical grouping for the memory entry
        
        Returns:
            Storage result with memory_id
        """
        memory_entry = {
            "memory_id": self._compute_embedding_key(content),
            "namespace": namespace,
            "content": content,
            "metadata": json.dumps(metadata),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "memory_type": "semantic"
        }
        
        try:
            # Try AgentCore Memory API first
            # Note: This is a placeholder - actual API may differ
            response = self.bedrock_agent.invoke_agent(
                agentId=self.memory_id,
                agentAliasId="TSTALIASID",
                sessionId="memory-session",
                inputText=json.dumps({
                    "action": "store",
                    "type": "semantic",
                    "content": content,
                    "metadata": metadata,
                    "namespace": namespace
                })
            )
            return {"status": "stored", "memory_id": memory_entry["memory_id"]}
        except (ClientError, Exception):
            # Fallback to DynamoDB
            table = self._get_fallback_table()
            table.put_item(Item=memory_entry)
            return {"status": "stored_fallback", "memory_id": memory_entry["memory_id"]}

    
    async def retrieve_semantic(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 5,
        threshold: float = 0.7
    ) -> list[dict]:
        """
        Retrieve similar content from semantic memory.
        
        Args:
            query: Search query text
            namespace: Namespace to search within
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)
        
        Returns:
            List of matching memory entries with similarity scores
        """
        try:
            # Try AgentCore Memory API first
            response = self.bedrock_agent.invoke_agent(
                agentId=self.memory_id,
                agentAliasId="TSTALIASID",
                sessionId="memory-session",
                inputText=json.dumps({
                    "action": "retrieve",
                    "type": "semantic",
                    "query": query,
                    "namespace": namespace,
                    "limit": limit,
                    "threshold": threshold
                })
            )
            # Parse response
            return []  # Placeholder - parse actual response
        except (ClientError, Exception):
            # Fallback to DynamoDB scan (not ideal for semantic search)
            table = self._get_fallback_table()
            response = table.scan(
                FilterExpression="namespace = :ns AND memory_type = :mt",
                ExpressionAttributeValues={
                    ":ns": namespace,
                    ":mt": "semantic"
                },
                Limit=limit
            )
            items = response.get("Items", [])
            # Simple keyword matching as fallback
            results = []
            query_lower = query.lower()
            for item in items:
                content = item.get("content", "").lower()
                if any(word in content for word in query_lower.split()):
                    results.append({
                        "memory_id": item.get("memory_id"),
                        "content": item.get("content"),
                        "metadata": json.loads(item.get("metadata", "{}")),
                        "similarity": 0.5  # Placeholder score
                    })
            return results[:limit]
    
    async def store_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> dict:
        """
        Store an event in event memory for temporal retrieval.
        
        Args:
            event_type: Type of event (e.g., PDF_PROCESSED, TRADE_EXTRACTED)
            event_data: Event payload
            correlation_id: Optional correlation ID for tracing
        
        Returns:
            Storage result with event_id
        """
        event_id = f"{event_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        event_entry = {
            "memory_id": event_id,
            "event_type": event_type,
            "event_data": json.dumps(event_data),
            "correlation_id": correlation_id or "",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "memory_type": "event"
        }
        
        try:
            # Try AgentCore Memory API
            response = self.bedrock_agent.invoke_agent(
                agentId=self.memory_id,
                agentAliasId="TSTALIASID",
                sessionId="memory-session",
                inputText=json.dumps({
                    "action": "store",
                    "type": "event",
                    "event_type": event_type,
                    "event_data": event_data,
                    "correlation_id": correlation_id
                })
            )
            return {"status": "stored", "event_id": event_id}
        except (ClientError, Exception):
            # Fallback to DynamoDB
            table = self._get_fallback_table()
            table.put_item(Item=event_entry)
            return {"status": "stored_fallback", "event_id": event_id}

    
    async def retrieve_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Retrieve events from event memory.
        
        Args:
            event_type: Filter by event type
            start_time: Filter events after this time (ISO format)
            end_time: Filter events before this time (ISO format)
            correlation_id: Filter by correlation ID
            limit: Maximum number of results
        
        Returns:
            List of matching events
        """
        try:
            # Try AgentCore Memory API
            response = self.bedrock_agent.invoke_agent(
                agentId=self.memory_id,
                agentAliasId="TSTALIASID",
                sessionId="memory-session",
                inputText=json.dumps({
                    "action": "retrieve",
                    "type": "event",
                    "event_type": event_type,
                    "start_time": start_time,
                    "end_time": end_time,
                    "correlation_id": correlation_id,
                    "limit": limit
                })
            )
            return []  # Placeholder
        except (ClientError, Exception):
            # Fallback to DynamoDB
            table = self._get_fallback_table()
            
            filter_parts = ["memory_type = :mt"]
            expr_values = {":mt": "event"}
            
            if event_type:
                filter_parts.append("event_type = :et")
                expr_values[":et"] = event_type
            if correlation_id:
                filter_parts.append("correlation_id = :cid")
                expr_values[":cid"] = correlation_id
            if start_time:
                filter_parts.append("#ts >= :st")
                expr_values[":st"] = start_time
            if end_time:
                filter_parts.append("#ts <= :et")
                expr_values[":et"] = end_time
            
            response = table.scan(
                FilterExpression=" AND ".join(filter_parts),
                ExpressionAttributeValues=expr_values,
                ExpressionAttributeNames={"#ts": "timestamp"} if start_time or end_time else {},
                Limit=limit
            )
            
            items = response.get("Items", [])
            return [
                {
                    "event_id": item.get("memory_id"),
                    "event_type": item.get("event_type"),
                    "event_data": json.loads(item.get("event_data", "{}")),
                    "correlation_id": item.get("correlation_id"),
                    "timestamp": item.get("timestamp")
                }
                for item in items
            ]


# Global client instance
memory_client = AgentCoreMemoryClient()
