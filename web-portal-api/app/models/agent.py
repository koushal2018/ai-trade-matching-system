from enum import Enum
from pydantic import BaseModel


class AgentStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    OFFLINE = "OFFLINE"


class AgentMetrics(BaseModel):
    latencyMs: int
    throughput: int
    errorRate: float


class AgentHealth(BaseModel):
    agentId: str
    agentName: str
    status: AgentStatus
    lastHeartbeat: str
    metrics: AgentMetrics
    activeTasks: int
