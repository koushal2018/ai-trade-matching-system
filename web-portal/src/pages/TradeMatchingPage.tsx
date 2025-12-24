import { FC, useState } from 'react'
import {
  ContentLayout,
  Header,
  SpaceBetween,
  Button,
} from '@cloudscape-design/components'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { UploadSection } from '../components/upload/UploadSection'
import { WorkflowIdentifierSection } from '../components/workflow/WorkflowIdentifierSection'
import { AgentProcessingSection } from '../components/agent/AgentProcessingSection'
import { MatchResultSection } from '../components/results/MatchResultSection'
import { ExceptionSection } from '../components/exceptions/ExceptionSection'
import { useAgentWebSocket } from '../hooks/useAgentWebSocket'
import { useAgentStatus } from '../hooks/useAgentStatus'
import { workflowService } from '../services/workflowService'
import { useNotifications } from '../hooks/useNotifications'

/**
 * TradeMatchingPage Component
 * 
 * Main page component for trade confirmation upload and matching workflow.
 * Integrates all components following CloudScape Design System patterns.
 * 
 * Features:
 * - File upload for bank and counterparty confirmations (Requirement 2.1)
 * - Workflow identifier display with Session ID and Trace ID (Requirement 3.1, 3.2)
 * - Real-time agent processing status with WebSocket updates (Requirement 4.19, 4.20)
 * - Match results with confidence scoring (Requirement 7.1)
 * - Exception handling and display (Requirement 9.1)
 * 
 * Upload Flow (Task 18.2):
 * 1. User uploads bank and/or counterparty PDF files
 * 2. Files are validated and uploaded to S3 with appropriate prefix (BANK/ or COUNTERPARTY/)
 * 3. Upload API returns sessionId and traceId
 * 4. Page initializes workflow session with these identifiers
 * 5. SessionId and traceId are passed to all child components
 * 6. When both files are uploaded, Lambda trigger automatically initiates agent processing
 * 7. WebSocket connection provides real-time status updates
 * 
 * Requirements: 1.1, 1.2, 2.1, 2.11, 3.1, 3.2, 4.19, 6.2, 7.1, 9.1
 */
export const TradeMatchingPage: FC = () => {
  // State management for workflow identifiers (Requirement 3.5, 3.6)
  // Session ID: Primary workflow identifier from AgentCore session
  // Trace ID: AWS X-Ray trace identifier for debugging and monitoring
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [traceId, setTraceId] = useState<string | null>(null)

  // Hooks
  const { addNotification } = useNotifications()
  const queryClient = useQueryClient()
  
  // WebSocket connection for real-time updates (Requirement 4.19, 4.20)
  // Connects when sessionId is available and provides real-time agent status updates
  // Falls back to polling if WebSocket is unavailable
  const { reconnect } = useAgentWebSocket(
    sessionId,
    (state, message) => {
      // Display Flashbar notifications for connection state changes
      if (state === 'fallback') {
        // Display warning when falling back to polling (Requirement 4.20)
        addNotification({
          type: 'warning',
          header: 'Real-time updates unavailable',
          content: 'Using polling mode. Updates will refresh every 30 seconds.',
          dismissible: true,
          action: {
            text: 'Retry Connection',
            onClick: reconnect,
          },
        })
      } else if (state === 'connected') {
        // Display success when WebSocket reconnects
        addNotification({
          type: 'success',
          header: 'Real-time updates connected',
          content: 'WebSocket connection established.',
          dismissible: true,
        })
      } else if (state === 'failed') {
        // Display error for connection failures
        addNotification({
          type: 'error',
          header: 'Connection failed',
          content: message,
          dismissible: true,
          action: {
            text: 'Retry Connection',
            onClick: reconnect,
          },
        })
      }
    }
  )
  
  // Fetch agent status using React Query (Requirement 4.19, 4.20)
  // Polls every 30 seconds during active processing as fallback to WebSocket
  const { data: agentStatusResponse } = useAgentStatus(sessionId)
  
  // Invoke matching mutation (Requirement 6.2, 6.3, 6.4)
  // Manually triggers the Trade Matching Agent via POST /api/workflow/{sessionId}/invoke-matching
  const { mutate: invokeMatching, isPending: isInvoking } = useMutation({
    mutationFn: async () => {
      if (!sessionId) {
        throw new Error('Session ID is required')
      }
      return await workflowService.invokeMatching(sessionId)
    },
    onSuccess: (response) => {
      addNotification({
        type: 'success',
        header: 'Trade matching invoked',
        content: `Invocation ID: ${response.invocationId}`,
        dismissible: true,
      })
      // Invalidate agent status to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['agentStatus', sessionId] })
    },
    onError: (error) => {
      addNotification({
        type: 'error',
        header: 'Failed to invoke matching',
        content: error instanceof Error ? error.message : 'An unexpected error occurred',
        dismissible: true,
      })
    },
  })

  /**
   * Handle bank file upload completion
   * Requirements: 2.1, 2.11, 3.1, 3.2
   * 
   * When a bank confirmation is uploaded:
   * 1. File is saved to S3 with BANK/ prefix (handled by uploadService)
   * 2. Initialize workflow session with sessionId and traceId from response
   * 3. Display success notification
   */
  const handleBankUploadComplete = (
    s3Uri: string,
    uploadSessionId?: string,
    uploadTraceId?: string
  ) => {
    console.log('Bank upload complete:', { s3Uri, uploadSessionId, uploadTraceId })
    
    // Initialize workflow session on first upload (Requirement 3.1, 3.2)
    if (uploadSessionId && !sessionId) {
      setSessionId(uploadSessionId)
      addNotification({
        type: 'success',
        header: 'Bank confirmation uploaded',
        content: `Session ID: ${uploadSessionId}`,
        dismissible: true,
      })
    }
    
    // Set trace ID for debugging and monitoring (Requirement 3.2)
    if (uploadTraceId && !traceId) {
      setTraceId(uploadTraceId)
    }
  }

  /**
   * Handle counterparty file upload completion
   * Requirements: 2.1, 2.11, 3.1, 3.2
   * 
   * When a counterparty confirmation is uploaded:
   * 1. File is saved to S3 with COUNTERPARTY/ prefix (handled by uploadService)
   * 2. Initialize workflow session with sessionId and traceId from response
   * 3. Display success notification
   * 4. If both files are uploaded, Lambda trigger automatically initiates agent processing (Requirement 2.12)
   */
  const handleCounterpartyUploadComplete = (
    s3Uri: string,
    uploadSessionId?: string,
    uploadTraceId?: string
  ) => {
    console.log('Counterparty upload complete:', { s3Uri, uploadSessionId, uploadTraceId })
    
    // Initialize workflow session on first upload (Requirement 3.1, 3.2)
    if (uploadSessionId && !sessionId) {
      setSessionId(uploadSessionId)
      addNotification({
        type: 'success',
        header: 'Counterparty confirmation uploaded',
        content: `Session ID: ${uploadSessionId}`,
        dismissible: true,
      })
    }
    
    // Set trace ID for debugging and monitoring (Requirement 3.2)
    if (uploadTraceId && !traceId) {
      setTraceId(uploadTraceId)
    }
    
    // Note: When both files are uploaded to S3, Lambda trigger automatically
    // initiates agent processing (Requirement 2.12). The WebSocket connection
    // will receive real-time updates as agents process the files.
  }

  // Handle page refresh
  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <ContentLayout
      header={
        <Header
          variant="h1"
          description="Upload trade confirmations for AI-powered matching"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button iconName="refresh" onClick={handleRefresh} ariaLabel="Refresh page data">
                Refresh
              </Button>
              <Button iconName="download" disabled={!sessionId} ariaLabel="Export matching results">
                Export Results
              </Button>
            </SpaceBetween>
          }
        >
          Trade Matching Upload
        </Header>
      }
    >
      <SpaceBetween size="l">
        {/* File Upload Section */}
        <UploadSection
          onBankUploadComplete={handleBankUploadComplete}
          onCounterpartyUploadComplete={handleCounterpartyUploadComplete}
          disabled={false}
        />

        {/* Workflow Identifiers - Only show after upload */}
        {sessionId && (
          <WorkflowIdentifierSection sessionId={sessionId} traceId={traceId} />
        )}

        {/* Agent Processing Status - Only show after upload */}
        {sessionId && (
          <AgentProcessingSection
            sessionId={sessionId}
            agentStatus={agentStatusResponse?.agents}
            onInvokeMatching={() => invokeMatching()}
            isInvoking={isInvoking}
          />
        )}

        {/* Match Results - Only show after upload */}
        {sessionId && <MatchResultSection sessionId={sessionId} />}

        {/* Exceptions - Only show after upload */}
        {sessionId && <ExceptionSection sessionId={sessionId} />}
      </SpaceBetween>
    </ContentLayout>
  )
}

export default TradeMatchingPage
