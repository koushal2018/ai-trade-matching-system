// Core workflow types
export interface WorkflowSession {
  sessionId: string
  traceId: string
  createdAt: string
  status: 'active' | 'completed' | 'failed'
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

export interface FieldComparison {
  fieldName: string
  bankValue: string | number
  counterpartyValue: string | number
  match: boolean
  confidence: number
}

export interface MatchResult {
  sessionId: string
  matchStatus: MatchStatus
  confidenceScore: number
  completedAt: string
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
export interface AuditEntry {
  id: string
  timestamp: string
  sessionId: string
  action: 'Upload' | 'Invoke' | 'Match Complete' | 'Exception' | 'Feedback'
  user: string
  status: AgentStatusType
  details: Record<string, unknown>
}
