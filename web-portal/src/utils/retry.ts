/**
 * Retry utility with exponential backoff
 * Implements exponential backoff: 1s, 2s, 4s (max 3 retries)
 */

export interface RetryOptions {
  maxRetries?: number
  baseDelay?: number
  onRetry?: (attempt: number, error: Error) => void
}

export class RetryError extends Error {
  constructor(
    message: string,
    public readonly attempts: number,
    public readonly lastError: Error
  ) {
    super(message)
    this.name = 'RetryError'
  }
}

/**
 * Retry a function with exponential backoff
 * @param fn Function to retry
 * @param options Retry options
 * @returns Promise that resolves with the function result or rejects after max retries
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const { maxRetries = 3, baseDelay = 1000, onRetry } = options

  let lastError: Error | null = null
  let attempt = 0

  while (attempt < maxRetries) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      attempt++

      if (attempt >= maxRetries) {
        break
      }

      // Calculate exponential backoff delay: 1s, 2s, 4s
      const delay = baseDelay * Math.pow(2, attempt - 1)

      // Call onRetry callback if provided
      if (onRetry) {
        onRetry(attempt, lastError)
      }

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay))
    }
  }

  // All retries exhausted
  throw new RetryError(
    `Operation failed after ${attempt} attempts`,
    attempt,
    lastError!
  )
}

/**
 * Check if an error is retryable (network errors, timeouts, 5xx errors)
 */
export function isRetryableError(error: unknown): boolean {
  if (error instanceof Error) {
    // Network errors
    if (error.name === 'NetworkError' || error.message.includes('network')) {
      return true
    }

    // Timeout errors
    if (error.name === 'TimeoutError' || error.message.includes('timeout')) {
      return true
    }
  }

  // HTTP errors
  if (typeof error === 'object' && error !== null && 'status' in error) {
    const status = (error as { status: number }).status
    // Retry on 5xx server errors and 408 Request Timeout
    return status >= 500 || status === 408
  }

  return false
}
