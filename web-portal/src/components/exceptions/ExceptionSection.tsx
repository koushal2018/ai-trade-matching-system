import { FC, useState, useEffect } from 'react'
import {
  Container,
  Header,
  SpaceBetween,
  Alert,
  Button,
  Box,
  Spinner,
} from '@cloudscape-design/components'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workflowService } from '../../services/workflowService'
import type { Exception } from '../../types'

export interface ExceptionSectionProps {
  sessionId: string
}

/**
 * ExceptionSection Component
 * 
 * Displays exceptions and errors from AgentCore agent processing using CloudScape Alert components.
 * Implements requirements 9.1, 9.2, 9.3, 9.8, 9.9, 9.11.
 * 
 * Features:
 * - Chronological ordering (oldest first)
 * - Severity-based Alert types (error, warning, info)
 * - Retry functionality for recoverable errors
 * - Format: "{message} - [{agentName}]"
 * - Exception counter in header
 */
export const ExceptionSection: FC<ExceptionSectionProps> = ({ sessionId }) => {
  const queryClient = useQueryClient()
  const [retryingExceptionId, setRetryingExceptionId] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  // Fetch exceptions using React Query
  const {
    data: exceptionsData,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['workflow', sessionId, 'exceptions'],
    queryFn: async () => {
      const response = await workflowService.getExceptions(sessionId)
      return response.exceptions
    },
    refetchInterval: 30000, // Refetch every 30 seconds
    enabled: !!sessionId,
  })

  // Update last updated timestamp when data changes
  useEffect(() => {
    if (exceptionsData) {
      setLastUpdated(new Date())
    }
  }, [exceptionsData])

  // Handle refresh (Requirement 10.3, 10.4, 10.5)
  const handleRefresh = () => {
    refetch()
  }

  // Retry mutation (placeholder - actual retry logic would depend on backend)
  const retryMutation = useMutation({
    mutationFn: async (exceptionId: string) => {
      // In a real implementation, this would call a retry endpoint
      // For now, we'll just refetch the exceptions after a delay
      await new Promise((resolve) => setTimeout(resolve, 1000))
      return exceptionId
    },
    onSuccess: () => {
      // Refetch exceptions after retry
      queryClient.invalidateQueries({ queryKey: ['workflow', sessionId, 'exceptions'] })
      queryClient.invalidateQueries({ queryKey: ['workflow', sessionId, 'status'] })
      setRetryingExceptionId(null)
    },
    onError: () => {
      setRetryingExceptionId(null)
    },
  })

  const handleRetry = (exceptionId: string) => {
    setRetryingExceptionId(exceptionId)
    retryMutation.mutate(exceptionId)
  }

  // Sort exceptions chronologically (oldest first) - Requirement 9.8
  const sortedExceptions = exceptionsData
    ? [...exceptionsData].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      )
    : []

  // Map severity to Alert type - Requirement 9.11
  const getAlertType = (severity: Exception['severity']): 'error' | 'warning' | 'info' => {
    return severity
  }

  // Loading state
  if (isLoading) {
    return (
      <Container
        header={
          <Header variant="h2" description="Errors and warnings from agent processing">
            Exceptions and Errors
          </Header>
        }
      >
        <Box textAlign="center" padding="xxl">
          <Spinner size="large" />
          <Box variant="p" color="text-body-secondary" margin={{ top: 's' }}>
            Loading exceptions...
          </Box>
        </Box>
      </Container>
    )
  }

  // Error state
  if (error) {
    return (
      <Container
        header={
          <Header variant="h2" description="Errors and warnings from agent processing">
            Exceptions and Errors
          </Header>
        }
      >
        <Alert
          type="error"
          header="Failed to load exceptions"
          action={
            <Button onClick={() => refetch()} iconName="refresh" ariaLabel="Retry loading exceptions">
              Retry
            </Button>
          }
        >
          {error instanceof Error ? error.message : 'An unexpected error occurred'}
        </Alert>
      </Container>
    )
  }

  // Empty state
  if (!sortedExceptions || sortedExceptions.length === 0) {
    return (
      <Container
        header={
          <Header variant="h2" description="Errors and warnings from agent processing">
            Exceptions and Errors
          </Header>
        }
      >
        <Box textAlign="center" padding="xxl">
          <Box variant="h3" color="text-body-secondary">
            No exceptions
          </Box>
          <Box variant="p" color="text-body-secondary" margin={{ top: 's' }}>
            All agents are processing successfully without errors.
          </Box>
        </Box>
      </Container>
    )
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Errors and warnings from agent processing"
          counter={`(${sortedExceptions.length})`}
          actions={
            <Button
              iconName="refresh"
              onClick={handleRefresh}
              loading={isFetching}
              ariaLabel="Refresh exceptions"
            >
              Refresh
            </Button>
          }
        >
          Exceptions and Errors
        </Header>
      }
    >
      <SpaceBetween direction="vertical" size="s">
        {sortedExceptions.map((exception) => (
          <Alert
            key={exception.id}
            type={getAlertType(exception.severity)}
            header={`${exception.severity.charAt(0).toUpperCase() + exception.severity.slice(1)} from ${exception.agentName}`}
            action={
              exception.recoverable ? (
                <Button
                  onClick={() => handleRetry(exception.id)}
                  iconName="refresh"
                  ariaLabel={`Retry processing for exception ${exception.id}`}
                  loading={retryingExceptionId === exception.id}
                  disabled={retryingExceptionId !== null}
                >
                  Retry
                </Button>
              ) : undefined
            }
          >
            {/* Format: "{message} - [{agentName}]" - Requirement 9.2 */}
            {exception.message} - [{exception.agentName}]
            {exception.details && (
              <Box margin={{ top: 'xs' }} variant="small" color="text-body-secondary">
                <Box variant="code">{JSON.stringify(exception.details, null, 2)}</Box>
              </Box>
            )}
          </Alert>
        ))}
        
        {/* Last updated timestamp (Requirement 10.8) */}
        <Box variant="small" color="text-body-secondary" textAlign="right">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </Box>
      </SpaceBetween>
    </Container>
  )
}
