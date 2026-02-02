import json
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import boto3
from .config import settings
from .routers import agents_router, hitl_router, audit_router, metrics_router, matching_router, upload_router, workflow_router, logs_router
from .services.websocket import manager
from .routers.logs import log_poller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background heartbeat task handle
_heartbeat_task = None


async def heartbeat_loop():
    """Background task to update agent heartbeats every 2 minutes."""
    dynamodb = boto3.client('dynamodb', region_name=settings.aws_region)
    agent_ids = [
        "orchestrator_otc",
        "trade_matching_agent",
        "trade_extraction_agent",
        "pdf_adapter_agent",
        "exception_manager"
    ]

    while True:
        try:
            current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000+00:00")
            for agent_id in agent_ids:
                try:
                    dynamodb.update_item(
                        TableName=settings.dynamodb_agent_registry_table,
                        Key={"agent_id": {"S": agent_id}},
                        UpdateExpression="SET last_heartbeat = :hb",
                        ExpressionAttributeValues={":hb": {"S": current_time}}
                    )
                except Exception as e:
                    logger.warning(f"Failed to update heartbeat for {agent_id}: {e}")

            logger.debug(f"Updated heartbeats for {len(agent_ids)} agents")
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")

        # Sleep for 2 minutes
        await asyncio.sleep(120)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _heartbeat_task
    logger.info("Starting Web Portal API...")
    # Set up log poller with WebSocket manager
    log_poller.set_websocket_manager(manager)
    # Start background heartbeat task
    _heartbeat_task = asyncio.create_task(heartbeat_loop())
    logger.info("Started agent heartbeat background task (every 2 minutes)")
    yield
    # Stop heartbeat task
    if _heartbeat_task:
        _heartbeat_task.cancel()
        try:
            await _heartbeat_task
        except asyncio.CancelledError:
            pass
    # Stop log polling on shutdown
    log_poller.stop_polling()
    logger.info("Shutting down Web Portal API...")


app = FastAPI(
    title="Trade Matching Web Portal API",
    description="Backend API for the AI Trade Matching Web Portal",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router, prefix="/api")
app.include_router(workflow_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(hitl_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(matching_router, prefix="/api")
app.include_router(logs_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, sessionId: str = ""):
    await manager.connect(websocket, session_id=sessionId if sessionId else None)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages (e.g., subscribe to different sessions)
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")

                if msg_type == "SUBSCRIBE" and msg.get("sessionId"):
                    # Client wants to subscribe to a session
                    new_session_id = msg["sessionId"]
                    await manager.handle_subscribe(websocket, new_session_id)

                elif msg_type == "LOG_SUBSCRIBE" and msg.get("logGroups"):
                    # Client wants to subscribe to CloudWatch logs
                    log_groups = msg["logGroups"]
                    await log_poller.start_polling(log_groups)
                    await manager.send_personal_message({
                        "type": "LOG_SUBSCRIBED",
                        "logGroups": log_groups
                    }, websocket)
                    logger.info(f"Client subscribed to log groups: {log_groups}")

                elif msg_type == "LOG_UNSUBSCRIBE":
                    # Client wants to stop log streaming
                    log_poller.stop_polling()
                    await manager.send_personal_message({
                        "type": "LOG_UNSUBSCRIBED"
                    }, websocket)

                else:
                    await manager.send_personal_message({"type": "ACK", "data": data}, websocket)
            except json.JSONDecodeError:
                await manager.send_personal_message({"type": "ACK", "data": data}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
