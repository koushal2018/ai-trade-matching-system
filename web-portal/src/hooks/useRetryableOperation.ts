import { useState, useCallback } from 'react'
import { retryWithBackoff, RetryError } from '../utils/retry'

interface UseRetryableOperationOptions {
  maxRetries?: number
  baseDelay?: number
  onSuccess?: () => void
  onError?: (error: Error) => void
}

interface UseRetryableOperationResult<T> {
  execute: () => Promise<T | undefined>
  isLoading: boolean
  error: Error | null
  retryCount: number
  reset: () => void
}

/**
 * Hook for managing retryable operations with exponential backoff
 * @param operation Function to execute with retry logic
 * @param options Configuration options
 * @returns Object with execute function, loading state, error, and retry count
 */
export function useRetryableOperation<T>(
  operation: () => Promise<T>,
  options: UseRetryableOperationOptions = {}
): UseRetryableOperationResult<T> {
  const { maxRetries = 3, baseDelay = 1000, onSuccess, onError } = options

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  const execute = useCallback(async (): Promise<T | undefined> => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await retryWithBackoff(operation, {
        maxRetries,
        baseDelay,
        onRetry: (attempt, retryError) => {
          setRetryCount(attempt)
          console.log(`Retry attempt ${attempt} after error:`, retryError)
        },
      })

      setRetryCount(0)
      onSuccess?.()
      return result
    } catch (err) {
      const finalError = err instanceof RetryError ? err.lastError : (err as Error)
      setError(finalError)
      setRetryCount(err instanceof RetryError ? err.attempts : 0)
      onError?.(finalError)
      return undefined
    } finally {
      setIsLoading(false)
    }
  }, [operation, maxRetries, baseDelay, onSuccess, onError])

  const reset = useCallback(() => {
    setIsLoading(false)
    setError(null)
    setRetryCount(0)
  }, [])

  return {
    execute,
    isLoading,
    error,
    retryCount,
    reset,
  }
}
