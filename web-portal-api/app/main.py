import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import agents_router, hitl_router, audit_router, metrics_router, matching_router
from .services.websocket import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Web Portal API...")
    yield
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
app.include_router(agents_router, prefix="/api")
app.include_router(hitl_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(matching_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - in production, handle specific message types
            await manager.send_personal_message({"type": "ACK", "data": data}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
