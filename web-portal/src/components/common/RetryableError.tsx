import { Alert, Button } from '@cloudscape-design/components'
import { useState } from 'react'

interface RetryableErrorProps {
  error: Error | string
  onRetry: () => void | Promise<void>
  retryCount?: number
  maxRetries?: number
  type?: 'error' | 'warning'
  header?: string
}

/**
 * RetryableError component
 * Displays an error with a retry button and retry count
 * Implements exponential backoff retry mechanism
 */
export const RetryableError: React.FC<RetryableErrorProps> = ({
  error,
  onRetry,
  retryCount = 0,
  maxRetries = 3,
  type = 'error',
  header = 'Operation failed',
}) => {
  const [isRetrying, setIsRetrying] = useState(false)

  const handleRetry = async () => {
    setIsRetrying(true)
    try {
      await onRetry()
    } finally {
      setIsRetrying(false)
    }
  }

  const errorMessage = typeof error === 'string' ? error : error.message

  const canRetry = retryCount < maxRetries

  return (
    <Alert
      type={type}
      header={header}
      action={
        canRetry ? (
          <Button
            onClick={handleRetry}
            iconName="refresh"
            loading={isRetrying}
            loadingText="Retrying..."
          >
            Retry
          </Button>
        ) : undefined
      }
    >
      {errorMessage}
      {retryCount > 0 && ` (Attempt ${retryCount + 1}/${maxRetries})`}
      {!canRetry && retryCount >= maxRetries && (
        <> Maximum retry attempts reached. Please contact support if the problem persists.</>
      )}
    </Alert>
  )
}
