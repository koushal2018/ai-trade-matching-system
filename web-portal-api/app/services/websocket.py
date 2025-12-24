import json
import asyncio
import logging
from typing import Any, Dict, Optional
from fastapi import WebSocket
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.session_connections: Dict[str, list[WebSocket]] = {}  # sessionId -> connections
        self._polling_tasks: Dict[str, asyncio.Task] = {}  # sessionId -> polling task
        self._dynamodb = None
        self._status_table = None
    
    def _get_dynamodb_table(self):
        """Lazy init DynamoDB table."""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            self._status_table = self._dynamodb.Table('trade-matching-system-processing-status')
        return self._status_table
    
    async def connect(self, websocket: WebSocket, session_id: Optional[str] = None):
        # Only accept if not already in active connections
        if websocket not in self.active_connections:
            await websocket.accept()
            self.active_connections.append(websocket)
        
        # Track session-specific connections
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = []
            if websocket not in self.session_connections[session_id]:
                self.session_connections[session_id].append(websocket)
            
            # Start polling for this session if not already running
            if session_id not in self._polling_tasks or self._polling_tasks[session_id].done():
                self._polling_tasks[session_id] = asyncio.create_task(
                    self._poll_status(session_id)
                )
                logger.info(f"Started status polling for session: {session_id}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from session connections
        for session_id, connections in list(self.session_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                # Stop polling if no more connections for this session
                if not connections:
                    del self.session_connections[session_id]
                    if session_id in self._polling_tasks:
                        self._polling_tasks[session_id].cancel()
                        del self._polling_tasks[session_id]
                        logger.info(f"Stopped status polling for session: {session_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)
    
    async def broadcast_agent_status(self, agent_id: str, status: str, metrics: dict):
        await self.broadcast({
            "type": "AGENT_STATUS",
            "payload": {"agentId": agent_id, "status": status, "metrics": metrics},
            "timestamp": self._get_timestamp()
        })
    
    async def broadcast_trade_processed(self, trade_id: str, result: dict):
        await self.broadcast({
            "type": "TRADE_PROCESSED",
            "payload": {"tradeId": trade_id, "result": result},
            "timestamp": self._get_timestamp()
        })
    
    async def broadcast_hitl_required(self, review_id: str, trade_id: str, match_score: float):
        await self.broadcast({
            "type": "HITL_REQUIRED",
            "payload": {"reviewId": review_id, "tradeId": trade_id, "matchScore": match_score},
            "timestamp": self._get_timestamp()
        })
    
    async def broadcast_metrics_update(self, metrics: dict):
        await self.broadcast({
            "type": "METRICS_UPDATE",
            "payload": metrics,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    async def _poll_status(self, session_id: str):
        """Poll DynamoDB for status updates and broadcast to connected clients."""
        last_status = None
        
        while session_id in self.session_connections and self.session_connections[session_id]:
            try:
                # Query DynamoDB for current status
                table = self._get_dynamodb_table()
                response = table.get_item(Key={"processing_id": session_id})
                
                if "Item" in response:
                    current_status = response["Item"]
                    
                    # Check if status changed
                    if current_status != last_status:
                        last_status = current_status
                        
                        # Build status update message
                        agents = {}
                        for agent_key in ["pdfAdapter", "tradeExtraction", "tradeMatching", "exceptionManagement"]:
                            agent_data = current_status.get(agent_key, {})
                            agents[agent_key] = {
                                "status": agent_data.get("status", "pending"),
                                "activity": agent_data.get("activity", ""),
                                "startedAt": agent_data.get("startedAt"),
                                "completedAt": agent_data.get("completedAt"),
                                "duration": agent_data.get("duration"),
                                "error": agent_data.get("error"),
                                "tokenUsage": agent_data.get("tokenUsage")
                            }
                        
                        message = {
                            "type": "AGENT_STATUS_UPDATE",
                            "sessionId": session_id,
                            "data": agents,
                            "overallStatus": current_status.get("overallStatus", "pending"),
                            "timestamp": self._get_timestamp()
                        }
                        
                        # Broadcast to session connections
                        await self._broadcast_to_session(session_id, message)
                        logger.debug(f"Broadcast status update for session {session_id}: {current_status.get('overallStatus')}")
                        
                        # Stop polling if workflow completed or failed
                        overall = current_status.get("overallStatus", "")
                        if overall in ["completed", "failed"]:
                            logger.info(f"Workflow {overall} for session {session_id}, stopping poll")
                            break
                
            except ClientError as e:
                logger.warning(f"DynamoDB error polling session {session_id}: {e}")
            except Exception as e:
                logger.error(f"Error polling status for session {session_id}: {e}")
            
            # Poll every 2 seconds
            await asyncio.sleep(2)
    
    async def _broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all connections for a specific session."""
        if session_id not in self.session_connections:
            return
        
        disconnected = []
        for connection in self.session_connections[session_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()
