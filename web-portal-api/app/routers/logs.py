"""
CloudWatch Logs streaming router.

Provides endpoints for subscribing to CloudWatch log streams
and broadcasting log events via WebSocket.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from ..auth import optional_auth_or_dev, User
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["logs"])

# AWS CloudWatch Logs client
logs_client = boto3.client('logs', region_name=settings.aws_region)

# Active log polling tasks
_log_polling_tasks: Dict[str, asyncio.Task] = {}

# Allowed log groups (security: only allow specific log groups)
ALLOWED_LOG_GROUPS = [
    "/aws/bedrock-agentcore/runtimes/http_agent_orchestrator-lKzrI47Hgd-DEFAULT",
    "/aws/bedrock-agentcore/runtimes/pdf_adapter_agent-Az72YP53FJ-DEFAULT",
    "/aws/bedrock-agentcore/runtimes/agent_matching_ai-KrY5QeCyXe-DEFAULT",
    "/aws/bedrock-agentcore/runtimes/trade_matching_ai-r8eaGb4u7B-DEFAULT",
    "/ecs/trade-matching-system-backend",
]

# Log group display names
LOG_GROUP_NAMES = {
    "/aws/bedrock-agentcore/runtimes/http_agent_orchestrator-lKzrI47Hgd-DEFAULT": "Orchestrator Agent",
    "/aws/bedrock-agentcore/runtimes/pdf_adapter_agent-Az72YP53FJ-DEFAULT": "PDF Adapter Agent",
    "/aws/bedrock-agentcore/runtimes/agent_matching_ai-KrY5QeCyXe-DEFAULT": "Trade Extraction Agent",
    "/aws/bedrock-agentcore/runtimes/trade_matching_ai-r8eaGb4u7B-DEFAULT": "Trade Matching Agent",
    "/ecs/trade-matching-system-backend": "Backend API",
}


class LogEvent(BaseModel):
    """Log event model."""
    timestamp: str
    message: str
    logGroup: str
    logGroupName: str
    logStream: Optional[str] = None
    level: str = "INFO"


class LogSubscription(BaseModel):
    """Log subscription request."""
    logGroups: List[str]


class LogGroupInfo(BaseModel):
    """Log group information."""
    logGroup: str
    displayName: str
    available: bool


class CloudWatchLogPoller:
    """Polls CloudWatch logs and broadcasts to WebSocket clients."""

    def __init__(self):
        self._last_timestamps: Dict[str, int] = {}
        self._active = False
        self._subscribed_groups: set = set()
        self._websocket_manager = None

    def set_websocket_manager(self, manager):
        """Set the WebSocket manager for broadcasting."""
        self._websocket_manager = manager

    async def start_polling(self, log_groups: List[str]):
        """Start polling specified log groups."""
        for log_group in log_groups:
            if log_group in ALLOWED_LOG_GROUPS:
                self._subscribed_groups.add(log_group)
                # Initialize last timestamp to now (only get new logs)
                if log_group not in self._last_timestamps:
                    self._last_timestamps[log_group] = int(datetime.now(timezone.utc).timestamp() * 1000)

        if not self._active and self._subscribed_groups:
            self._active = True
            asyncio.create_task(self._poll_loop())
            logger.info(f"Started log polling for {len(self._subscribed_groups)} log groups")

    def stop_polling(self):
        """Stop polling all log groups."""
        self._active = False
        self._subscribed_groups.clear()
        logger.info("Stopped log polling")

    async def _poll_loop(self):
        """Main polling loop."""
        while self._active and self._subscribed_groups:
            try:
                for log_group in list(self._subscribed_groups):
                    await self._poll_log_group(log_group)
            except Exception as e:
                logger.error(f"Error in log polling loop: {e}")

            # Poll every 2 seconds
            await asyncio.sleep(2)

    async def _poll_log_group(self, log_group: str):
        """Poll a single log group for new events."""
        try:
            start_time = self._last_timestamps.get(log_group, 0)

            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time + 1,  # Exclude already seen events
                limit=50,
                interleaved=True
            )

            events = response.get('events', [])

            if events:
                # Update last timestamp
                max_timestamp = max(e['timestamp'] for e in events)
                self._last_timestamps[log_group] = max_timestamp

                # Broadcast events
                for event in events:
                    log_event = self._transform_event(event, log_group)
                    await self._broadcast_log_event(log_event)

                logger.debug(f"Polled {len(events)} events from {log_group}")

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code != 'ResourceNotFoundException':
                logger.error(f"CloudWatch error for {log_group}: {e}")
        except Exception as e:
            logger.error(f"Error polling {log_group}: {e}")

    def _transform_event(self, event: dict, log_group: str) -> dict:
        """Transform CloudWatch event to broadcast format."""
        message = event.get('message', '')

        # Detect log level from message
        level = "INFO"
        if "ERROR" in message or "error" in message.lower():
            level = "ERROR"
        elif "WARNING" in message or "WARN" in message:
            level = "WARNING"
        elif "DEBUG" in message:
            level = "DEBUG"

        return {
            "type": "LOG_EVENT",
            "timestamp": datetime.fromtimestamp(
                event['timestamp'] / 1000,
                tz=timezone.utc
            ).isoformat(),
            "message": message,
            "logGroup": log_group,
            "logGroupName": LOG_GROUP_NAMES.get(log_group, log_group.split('/')[-1]),
            "logStream": event.get('logStreamName', ''),
            "level": level
        }

    async def _broadcast_log_event(self, log_event: dict):
        """Broadcast log event to WebSocket clients."""
        if self._websocket_manager:
            await self._websocket_manager.broadcast(log_event)


# Global log poller instance
log_poller = CloudWatchLogPoller()


@router.get("/logs/groups", response_model=List[LogGroupInfo])
async def get_available_log_groups(
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Get list of available log groups for streaming.

    Returns:
        List of log groups with display names and availability status
    """
    result = []

    for log_group in ALLOWED_LOG_GROUPS:
        # Check if log group exists
        available = False
        try:
            response = logs_client.describe_log_groups(
                logGroupNamePrefix=log_group,
                limit=1
            )
            available = len(response.get('logGroups', [])) > 0
        except Exception:
            pass

        result.append(LogGroupInfo(
            logGroup=log_group,
            displayName=LOG_GROUP_NAMES.get(log_group, log_group.split('/')[-1]),
            available=available
        ))

    return result


@router.get("/logs/recent")
async def get_recent_logs(
    log_group: str = Query(..., description="Log group name"),
    limit: int = Query(50, ge=1, le=200),
    current_user: Optional[User] = Depends(optional_auth_or_dev)
):
    """
    Get recent logs from a log group.

    Args:
        log_group: CloudWatch log group name
        limit: Maximum number of log events to return

    Returns:
        List of recent log events
    """
    # Security check
    if log_group not in ALLOWED_LOG_GROUPS:
        raise HTTPException(
            status_code=403,
            detail=f"Access to log group '{log_group}' is not allowed"
        )

    try:
        # Get logs from the last 10 minutes
        start_time = int((datetime.now(timezone.utc).timestamp() - 600) * 1000)

        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            limit=limit,
            interleaved=True
        )

        events = []
        for event in response.get('events', []):
            events.append(log_poller._transform_event(event, log_group))

        return {
            "logGroup": log_group,
            "logGroupName": LOG_GROUP_NAMES.get(log_group, log_group.split('/')[-1]),
            "events": events
        }

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            raise HTTPException(
                status_code=404,
                detail=f"Log group '{log_group}' not found"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch logs: {str(e)}"
        )
