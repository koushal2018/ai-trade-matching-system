import axios, { AxiosError } from 'axios'
import type {
  AgentStatus,
  MatchResult,
  Exception,
  FeedbackRequest,
  FeedbackResponse,
  APIError,
  MatchingStatusResponse,
} from '../types'

// Use relative URL to leverage Vite's proxy configuration
const API_BASE_URL = '/api'

/**
 * Response type for invoke matching endpoint
 */
export interface InvokeMatchingResponse {
  success: boolean
  message: string
  invocationId: string
}

/**
 * Response type for workflow status endpoint
 */
export interface WorkflowStatusResponse {
  sessionId: string
  agents: AgentStatus
  overallStatus: 'initializing' | 'processing' | 'complete' | 'failed'
  lastUpdated: string
}

/**
 * Response type for match result endpoint
 */
export interface MatchResultResponse {
  available: boolean
  result: MatchResult | null
}

/**
 * Response type for exceptions endpoint
 */
export interface ExceptionsResponse {
  exceptions: Exception[]
}

/**
 * Recent session item
 */
export interface RecentSessionItem {
  sessionId: string
  status: string
  createdAt?: string
  lastUpdated?: string
}

/**
 * Exponential backoff configuration
 */
interface RetryConfig {
  maxRetries: number
  baseDelay: number // milliseconds
  maxDelay: number // milliseconds
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 8000, // 8 seconds (1s, 2s, 4s, 8s)
}

/**
 * Calculate exponential backoff delay
 */
function getBackoffDelay(attempt: number, config: RetryConfig): number {
  const delay = config.baseDelay * Math.pow(2, attempt)
  return Math.min(delay, config.maxDelay)
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Determine if error is retryable
 */
function isRetryableError(error: AxiosError): boolean {
  // Retry on network errors
  if (!error.response) {
    return true
  }

  // Retry on 5xx server errors and 503 Service Unavailable
  const status = error.response.status
  return status >= 500 && status < 600
}

/**
 * Make HTTP request with exponential backoff retry logic
 */
async function requestWithRetry<T>(
  requestFn: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> {
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error as Error

      // Don't retry if not an Axios error or not retryable
      if (!axios.isAxiosError(error) || !isRetryableError(error)) {
        throw error
      }

      // Don't retry if this was the last attempt
      if (attempt === config.maxRetries) {
        throw error
      }

      // Wait before retrying
      const delay = getBackoffDelay(attempt, config)
      await sleep(delay)
    }
  }

  // Should never reach here, but TypeScript needs this
  throw lastError || new Error('Request failed after retries')
}

/**
 * Handle API errors and convert to user-friendly messages
 */
function handleApiError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    // Handle timeout
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout. The operation took too long. Please try again.')
    }

    // Handle server response errors
    if (error.response) {
      const status = error.response.status
      const errorData = error.response.data as APIError

      switch (status) {
        case 400:
          throw new Error(errorData.message || 'Invalid request. Please check your input.')
        case 401:
          throw new Error('Authentication required. Please log in.')
        case 403:
          throw new Error('Access denied. You do not have permission to perform this action.')
        case 404:
          throw new Error(errorData.message || 'Resource not found.')
        case 503:
          throw new Error('Service temporarily unavailable. The agent may be processing. Please try again.')
        default:
          throw new Error(errorData.message || 'An error occurred. Please try again.')
      }
    }

    // Handle network errors
    if (error.request) {
      throw new Error('Network error. Please check your connection and try again.')
    }
  }

  // Generic error
  throw new Error('An unexpected error occurred. Please try again.')
}

/**
 * Workflow Service
 * Handles all workflow-related API calls with error handling and retry logic
 */
class WorkflowService {
  /**
   * Get current status of all agents in workflow
   * @param sessionId Workflow session ID
   * @returns Agent status for all agents
   */
  async getWorkflowStatus(sessionId: string): Promise<WorkflowStatusResponse> {
    try {
      return await requestWithRetry(async () => {
        const response = await axios.get<WorkflowStatusResponse>(
          `${API_BASE_URL}/workflow/${sessionId}/status`,
          {
            timeout: 30000, // 30 second timeout
          }
        )
        return response.data
      })
    } catch (error) {
      handleApiError(error)
    }
  }

  /**
   * Manually trigger Trade Matching Agent
   * @param sessionId Workflow session ID
   * @returns Invocation response with invocation ID
   */
  async invokeMatching(sessionId: string): Promise<InvokeMatchingResponse> {
    try {
      return await requestWithRetry(async () => {
        const response = await axios.post<InvokeMatchingResponse>(
          `${API_BASE_URL}/workflow/${sessionId}/invoke-matching`,
          { sessionId },
          {
            timeout: 30000, // 30 second timeout
            headers: {
              'Content-Type': 'application/json',
            },
          }
        )
        return response.data
      })
    } catch (error) {
      handleApiError(error)
    }
  }

  /**
   * Retrieve matching results
   * @param sessionId Workflow session ID
   * @returns Match result if available
   */
  async getMatchResult(sessionId: string): Promise<MatchResultResponse> {
    try {
      return await requestWithRetry(async () => {
        const response = await axios.get<MatchResultResponse>(
          `${API_BASE_URL}/workflow/${sessionId}/result`,
          {
            timeout: 30000, // 30 second timeout
          }
        )
        return response.data
      })
    } catch (error) {
      handleApiError(error)
    }
  }

  /**
   * Retrieve exceptions and errors for workflow
   * @param sessionId Workflow session ID
   * @returns List of exceptions
   */
  async getExceptions(sessionId: string): Promise<ExceptionsResponse> {
    try {
      return await requestWithRetry(async () => {
        const response = await axios.get<ExceptionsResponse>(
          `${API_BASE_URL}/workflow/${sessionId}/exceptions`,
          {
            timeout: 30000, // 30 second timeout
          }
        )
        return response.data
      })
    } catch (error) {
      handleApiError(error)
    }
  }

  /**
   * Submit user feedback on match quality
   * @param feedback Feedback request with session ID, rating, and optional comment
   * @returns Feedback response with feedback ID
   */
  async submitFeedback(feedback: FeedbackRequest): Promise<FeedbackResponse> {
    try {
      // Don't retry feedback submissions to avoid duplicates
      const response = await axios.post<FeedbackResponse>(
        `${API_BASE_URL}/feedback`,
        feedback,
        {
          timeout: 30000, // 30 second timeout
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )
      return response.data
    } catch (error) {
      handleApiError(error)
    }
  }

  /**
   * Get recent processing sessions
   * @param limit Maximum number of sessions to return (default 10, max 50)
   * @returns List of recent sessions
   */
  async getRecentSessions(limit: number = 10): Promise<RecentSessionItem[]> {
    try {
      return await requestWithRetry(async () => {
        const response = await axios.get<RecentSessionItem[]>(
          `${API_BASE_URL}/workflow/recent`,
          {
            params: { limit },
            timeout: 30000, // 30 second timeout
          }
        )
        return response.data
      })
    } catch (error) {
      handleApiError(error)
    }
  }

  /**
   * Get matching status counts
   * @returns Matching status counts (matched, unmatched, pending, exceptions)
   */
  async getMatchingStatus(): Promise<MatchingStatusResponse> {
    try {
      return await requestWithRetry(async () => {
        const response = await axios.get<MatchingStatusResponse>(
          `${API_BASE_URL}/workflow/matching-status`,
          {
            timeout: 30000, // 30 second timeout
          }
        )
        return response.data
      })
    } catch (error) {
      handleApiError(error)
    }
  }
}

export const workflowService = new WorkflowService()
