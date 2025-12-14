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
    # Strands-specific metrics
    totalTokens: int = 0
    inputTokens: int = 0
    outputTokens: int = 0
    cycleCount: int = 0
    toolCallCount: int = 0
    successRate: float = 1.0


class AgentHealth(BaseModel):
    agentId: str
    agentName: str
    status: AgentStatus
    lastHeartbeat: str
    metrics: AgentMetrics
    activeTasks: int
