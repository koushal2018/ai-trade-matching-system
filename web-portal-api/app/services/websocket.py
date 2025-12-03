import json
from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
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


manager = ConnectionManager()
