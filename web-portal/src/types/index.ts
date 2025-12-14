// Agent types
export type AgentStatus = 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY' | 'OFFLINE'

export interface AgentHealth {
  agentId: string
  agentName: string
  status: AgentStatus
  lastHeartbeat: string
  metrics: {
    latencyMs: number
    throughput: number
    errorRate: number
    // Strands-specific metrics
    totalTokens: number
    inputTokens: number
    outputTokens: number
    cycleCount: number
    toolCallCount: number
    successRate: number
  }
  activeTasks: number
}

// Trade types
export interface Trade {
  Trade_ID: string
  TRADE_SOURCE: 'BANK' | 'COUNTERPARTY'
  trade_date: string
  notional: number
  currency: string
  counterparty: string
  product_type: string
  effective_date?: string
  maturity_date?: string
}

// Matching types
export type MatchClassification = 'MATCHED' | 'PROBABLE_MATCH' | 'REVIEW_REQUIRED' | 'BREAK' | 'DATA_ERROR'
export type DecisionStatus = 'AUTO_MATCH' | 'ESCALATE' | 'EXCEPTION' | 'PENDING' | 'APPROVED' | 'REJECTED'

export interface MatchingResult {
  tradeId: string
  classification: MatchClassification
  matchScore: number
  decisionStatus: DecisionStatus
  reasonCodes: string[]
  bankTrade?: Trade
  counterpartyTrade?: Trade
  differences: Record<string, { bank: string; counterparty: string }>
  createdAt: string
}

// HITL types
export interface HITLReview {
  reviewId: string
  tradeId: string
  matchScore: number
  reasonCodes: string[]
  bankTrade: Trade
  counterpartyTrade: Trade
  differences: Record<string, { bank: string; counterparty: string }>
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  createdAt: string
  assignedTo?: string
}


// Audit types
export type AuditActionType = 
  | 'PDF_PROCESSED'
  | 'TRADE_EXTRACTED'
  | 'TRADE_MATCHED'
  | 'EXCEPTION_RAISED'
  | 'HITL_DECISION'
  | 'AGENT_STARTED'
  | 'AGENT_STOPPED'

export interface AuditRecord {
  auditId: string
  timestamp: string
  agentId: string
  agentName: string
  actionType: AuditActionType
  tradeId?: string
  outcome: 'SUCCESS' | 'FAILURE' | 'PENDING'
  details: Record<string, unknown>
  immutableHash: string
}

// Processing metrics
export interface ProcessingMetrics {
  totalProcessed: number
  matchedCount: number
  breakCount: number
  pendingReview: number
  avgProcessingTimeMs: number
  throughputPerHour: number
}

// WebSocket event types
export type WebSocketEventType = 
  | 'AGENT_STATUS'
  | 'TRADE_PROCESSED'
  | 'HITL_REQUIRED'
  | 'METRICS_UPDATE'

export interface WebSocketMessage {
  type: WebSocketEventType
  payload: unknown
  timestamp: string
  correlationId?: string
}
