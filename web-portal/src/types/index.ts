// Core workflow types
export interface WorkflowSession {
  sessionId: string
  traceId: string
  createdAt: string
  status: 'active' | 'completed' | 'failed'
}

// Agent health/status for dashboard (legacy system)
export type AgentStatusLegacy = 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY' | 'OFFLINE'

export interface AgentMetrics {
  latencyMs: number
  throughput: number
  successRate: number
  errorRate: number
  totalTokens: number
  cycleCount: number
  inputTokens?: number
  outputTokens?: number
  toolCallCount?: number
}

export interface AgentHealth {
  agentId: string
  agentName: string
  status: AgentStatusLegacy
  activeTasks: number
  metrics: AgentMetrics
  lastUpdated?: string
  lastHeartbeat?: string
}

export interface ProcessingMetrics {
  totalProcessed: number
  matchedCount: number
  unmatchedCount: number
  pendingCount: number
  errorCount: number
  breakCount: number
  pendingReview: number
  throughputPerHour: number
  avgProcessingTimeMs: number
}

// HITL Review types
export interface HITLReview {
  reviewId: string
  tradeId: string
  sessionId?: string
  matchScore: number
  bankData?: Record<string, unknown>
  counterpartyData?: Record<string, unknown>
  bankTrade?: Record<string, unknown>
  counterpartyTrade?: Record<string, unknown>
  discrepancies?: string[]
  differences?: Record<string, { bankValue: unknown; counterpartyValue: unknown }>
  reasonCodes?: string[]
  createdAt?: string
}

// Agent status types
export type AgentStatusType = 'pending' | 'loading' | 'in-progress' | 'success' | 'error' | 'warning' | 'info' | 'stopped'

export interface SubStepStatus {
  title: string
  status: AgentStatusType
  description?: string
}

export interface AgentStepStatus {
  status: AgentStatusType
  activity?: string
  startedAt?: string
  completedAt?: string
  duration?: number
  error?: string
  subSteps?: SubStepStatus[]
}

export interface AgentStatus {
  sessionId: string
  pdfAdapter: AgentStepStatus
  tradeExtraction: AgentStepStatus
  tradeMatching: AgentStepStatus
  exceptionManagement: AgentStepStatus
  lastUpdated?: string
}

// Upload types
export interface UploadResponse {
  uploadId: string
  s3Uri: string
  status: 'success' | 'error'
  sessionId?: string
  traceId?: string
  error?: string
  message?: string
}

// Match result types
export type MatchStatus = 'MATCHED' | 'MISMATCHED' | 'PARTIAL_MATCH'
export type MatchClassification = 'MATCHED' | 'PROBABLE_MATCH' | 'REVIEW_REQUIRED' | 'BREAK' | 'DATA_ERROR'
export type DecisionStatus = 'AUTO_MATCH' | 'ESCALATE' | 'EXCEPTION' | 'PENDING' | 'APPROVED' | 'REJECTED'

export interface FieldComparison {
  fieldName: string
  bankValue: string | number
  counterpartyValue: string | number
  match: boolean
  confidence: number
}

export interface MatchResult {
  sessionId: string
  tradeId: string
  matchStatus: MatchStatus
  classification: MatchClassification
  confidenceScore: number
  matchScore: number
  decisionStatus: DecisionStatus
  completedAt: string
  createdAt: string
  fieldComparisons: FieldComparison[]
  metadata: {
    processingTime: number
    agentVersion: string
  }
}

// Exception types
export type ExceptionSeverity = 'error' | 'warning' | 'info'

export interface Exception {
  id: string
  sessionId: string
  agentName: string
  severity: ExceptionSeverity
  message: string
  timestamp: string
  recoverable: boolean
  details?: Record<string, unknown>
}

// Feedback types
export interface FeedbackRequest {
  sessionId: string
  rating: 'positive' | 'negative'
  comment?: string
}

export interface FeedbackResponse {
  success: boolean
  message: string
  feedbackId: string
}

// WebSocket message types
export type WebSocketMessageType =
  | 'AGENT_STATUS_UPDATE'
  | 'RESULT_AVAILABLE'
  | 'EXCEPTION'
  | 'STEP_UPDATE'

// WebSocket event types (for subscription)
export type WebSocketEventType =
  | WebSocketMessageType
  | 'HITL_REQUIRED'
  | 'PROCESSING_COMPLETE'
  | 'ERROR'
  | 'AGENT_STATUS'
  | 'METRICS_UPDATE'

export interface WebSocketMessage {
  type: WebSocketMessageType
  sessionId: string
  timestamp: string
  data: AgentStatus | MatchResult | Exception | AgentStepStatus
}

// API error types
export interface APIError {
  error: string
  message: string
  details?: Record<string, unknown>
}

// Audit trail types
export type AuditActionType = 
  | 'Upload'
  | 'Invoke'
  | 'Match Complete'
  | 'Exception'
  | 'Feedback'
  | 'PDF_PROCESSED'
  | 'TRADE_EXTRACTED'
  | 'TRADE_MATCHED'
  | 'EXCEPTION_RAISED'
  | 'HITL_DECISION'
  | 'AGENT_STARTED'
  | 'AGENT_STOPPED'

export interface AuditEntry {
  id: string
  timestamp: string
  sessionId: string
  action: AuditActionType
  user: string
  status: AgentStatusType
  details: Record<string, unknown>
}

export interface AuditRecord {
  auditId: string
  timestamp: string
  sessionId: string
  agentName: string
  actionType: AuditActionType
  tradeId?: string
  outcome: 'SUCCESS' | 'FAILURE' | 'PENDING'
  immutableHash: string
  details?: Record<string, unknown>
  user?: string
  agentSteps?: AgentStepStatus[]
  matchResult?: MatchResult
  exceptions?: Exception[]
}

