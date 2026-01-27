from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from ..models import AgentHealth, AgentStatus
from ..services.dynamodb import db_service
from ..config import settings
from ..auth import get_current_user, get_current_user_or_dev, optional_auth_or_dev, User

router = APIRouter(prefix="/agents", tags=["agents"])

# Map agent_type to friendly names
AGENT_TYPE_NAMES = {
    "PDF_ADAPTER": "PDF Adapter",
    "TRADE_EXTRACTOR": "Trade Extraction",
    "TRADE_MATCHER": "Trade Matching",
    "EXCEPTION_HANDLER": "Exception Handler",
    "ORCHESTRATOR": "Orchestrator",
}

# Fallback mapping for agent_id when agent_type is not set
AGENT_ID_TO_NAME = {
    "pdf_adapter_agent": "PDF Adapter",
    "trade_extraction_agent": "Trade Extraction",
    "trade-extraction-agent": "Trade Extraction",
    "trade_matching_agent": "Trade Matching",
    "trade-matching-agent": "Trade Matching",
    "exception_manager": "Exception Handler",
    "exception_management": "Exception Management",
    "orchestrator_otc": "Orchestrator",
    "http_agent_orchestrator": "HTTP Orchestrator",
}

# Agent-specific health thresholds for trade processing
AGENT_HEALTH_THRESHOLDS = {
    "PDF_ADAPTER": {"max_latency": 20000, "max_error_rate": 0.02},  # PDF processing can be slow
    "TRADE_EXTRACTOR": {"max_latency": 15000, "max_error_rate": 0.015},  # Critical for data accuracy
    "TRADE_MATCHER": {"max_latency": 20000, "max_error_rate": 0.01},  # Complex matching logic
    "EXCEPTION_HANDLER": {"max_latency": 5000, "max_error_rate": 0.05},  # Fast triage needed
    "ORCHESTRATOR": {"max_latency": 3000, "max_error_rate": 0.01},  # SLA monitoring
}


def _calculate_agent_status(item: dict) -> tuple[AgentStatus, str]:
    """Calculate agent status based on heartbeat and metrics."""
    last_heartbeat = item.get("last_heartbeat", "")
    deployment_status = item.get("deployment_status", "")
    status = AgentStatus.HEALTHY
    
    if deployment_status != "ACTIVE":
        return AgentStatus.OFFLINE, last_heartbeat
    
    if not last_heartbeat:
        return AgentStatus.UNHEALTHY, last_heartbeat
    
    try:
        # Handle timezone-aware datetime parsing
        if last_heartbeat.endswith("Z"):
            hb_time = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
        else:
            hb_time = datetime.fromisoformat(last_heartbeat)
            if hb_time.tzinfo is None:
                hb_time = hb_time.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        age_seconds = (now - hb_time).total_seconds()
        
        # Get agent-specific thresholds
        agent_type = item.get("agent_type", "")
        thresholds = AGENT_HEALTH_THRESHOLDS.get(agent_type, {
            "max_latency": 10000, "max_error_rate": 0.03
        })
        
        error_rate = float(item.get("error_rate", 0))
        avg_latency = int(item.get("avg_latency_ms", 2500))
        active_tasks = int(item.get("active_tasks", 0))
        
        if age_seconds > 300:  # 5 minutes
            status = AgentStatus.OFFLINE
        elif (age_seconds > 120 or 
              error_rate > thresholds["max_error_rate"] or
              avg_latency > thresholds["max_latency"] or
              active_tasks > 10):  # High load indicator
            status = AgentStatus.DEGRADED
            
    except Exception:
        status = AgentStatus.UNHEALTHY
    
    return status, last_heartbeat


def _build_agent_health(item: dict) -> AgentHealth:
    """Build AgentHealth object from DynamoDB item."""
    status, last_heartbeat = _calculate_agent_status(item)
    agent_type = item.get("agent_type", "")
    agent_id = item.get("agent_id", "Unknown")

    # Try agent_type mapping first, then agent_id mapping, finally use agent_id as-is
    agent_name = AGENT_TYPE_NAMES.get(agent_type) or AGENT_ID_TO_NAME.get(agent_id, agent_id)
    
    return AgentHealth(
        agentId=item.get("agent_id", ""),
        agentName=agent_name,
        status=status,
        lastHeartbeat=last_heartbeat,
        metrics={
            "latencyMs": int(item.get("avg_latency_ms", 2500)),
            "throughput": int(item.get("throughput_per_hour", 40)),
            "errorRate": float(item.get("error_rate", 0.02)),
            "totalTokens": int(item.get("total_tokens", 4000)),
            "inputTokens": int(item.get("input_tokens", 3200)),
            "outputTokens": int(item.get("output_tokens", 800)),
            "cycleCount": int(item.get("avg_cycles", 2)),
            "toolCallCount": int(item.get("tool_calls", 3)),
            "successRate": float(item.get("success_rate", 0.98))
        },
        activeTasks=int(item.get("active_tasks", 0))
    )


@router.get("/status", response_model=List[AgentHealth])
async def get_agent_status(user: Optional[User] = Depends(optional_auth_or_dev)):
    """Get health status of all ACTIVE agents."""
    try:
        items = db_service.scan_table(settings.dynamodb_agent_registry_table)
        
        # Filter for ACTIVE deployment status only (Requirements 5.1, 5.2)
        active_items = [item for item in items if item.get("deployment_status") == "ACTIVE"]
        
        agents = [_build_agent_health(item) for item in active_items]
        return agents
    except Exception as e:
        print(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent status")


@router.get("/{agent_id}", response_model=AgentHealth)
async def get_agent_details(agent_id: str, user: User = Depends(get_current_user_or_dev)):
    """Get detailed information for a specific agent."""
    try:
        item = db_service.get_item(settings.dynamodb_agent_registry_table, {"agent_id": agent_id})
        if not item:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return _build_agent_health(item)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent details")


@router.get("/{agent_id}/metrics")
async def get_agent_metrics_history(
    agent_id: str,
    hours: int = 24,
    user: User = Depends(get_current_user_or_dev)
):
    """Get historical metrics for an agent over the specified time period."""
    try:
        # This would typically query a time-series database or metrics table
        # For now, return current metrics as a time series
        item = db_service.get_item(settings.dynamodb_agent_registry_table, {"agent_id": agent_id})
        if not item:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Mock time series data - in production this would come from CloudWatch or similar
        current_time = datetime.now(timezone.utc)
        metrics_history = []
        
        for i in range(hours):
            timestamp = current_time - timedelta(hours=i)
            metrics_history.append({
                "timestamp": timestamp.isoformat(),
                "latencyMs": int(item.get("avg_latency_ms", 2500)) + (i * 100),  # Mock variation
                "throughput": int(item.get("throughput_per_hour", 40)) - (i * 2),
                "errorRate": max(0, float(item.get("error_rate", 0.02)) - (i * 0.001)),
                "activeTasks": max(0, int(item.get("active_tasks", 0)) - i),
                "successRate": min(1.0, float(item.get("success_rate", 0.98)) + (i * 0.001))
            })
        
        return {
            "agentId": agent_id,
            "timeRange": f"{hours}h",
            "metrics": list(reversed(metrics_history))  # Chronological order
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching metrics for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent metrics")
