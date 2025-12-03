from datetime import datetime
from fastapi import APIRouter, Depends
from ..models import AgentHealth, AgentStatus
from ..services.dynamodb import db_service
from ..config import settings
from ..auth import get_current_user, User

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status", response_model=list[AgentHealth])
async def get_agent_status(user: User = Depends(get_current_user)):
    """Get health status of all registered agents."""
    try:
        items = db_service.scan_table(settings.dynamodb_agent_registry_table)
        agents = []
        for item in items:
            # Determine status based on last heartbeat
            last_heartbeat = item.get("last_heartbeat", "")
            status = AgentStatus.HEALTHY
            if last_heartbeat:
                try:
                    hb_time = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
                    age_seconds = (datetime.utcnow() - hb_time.replace(tzinfo=None)).total_seconds()
                    if age_seconds > 300:
                        status = AgentStatus.OFFLINE
                    elif age_seconds > 60:
                        status = AgentStatus.DEGRADED
                except Exception:
                    status = AgentStatus.UNHEALTHY
            
            agents.append(AgentHealth(
                agentId=item.get("agent_id", ""),
                agentName=item.get("agent_name", ""),
                status=status,
                lastHeartbeat=last_heartbeat,
                metrics={
                    "latencyMs": int(item.get("avg_latency_ms", 0)),
                    "throughput": int(item.get("throughput_per_hour", 0)),
                    "errorRate": float(item.get("error_rate", 0))
                },
                activeTasks=int(item.get("active_tasks", 0))
            ))
        return agents
    except Exception:
        # Return empty list if table doesn't exist or other error
        return []
