import { FC, useState } from 'react'
import {
  ContentLayout,
  Header,
  SpaceBetween,
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
import { useToast } from '../hooks/useToast'
import GlassButton from '../components/common/GlassButton'

/**
 * TradeMatchingPage Component
 *
 * Main page component for trade confirmation upload and matching workflow.
 * Enhanced with glassmorphism styling and toast notifications.
 */
export const TradeMatchingPage: FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [traceId, setTraceId] = useState<string | null>(null)

  const { success, error, warning } = useToast()
  const queryClient = useQueryClient()

  // WebSocket connection for real-time updates
  useAgentWebSocket(
    sessionId,
    (state, message) => {
      if (state === 'fallback') {
        warning('Real-time updates unavailable. Using polling mode.')
      } else if (state === 'connected') {
        success('Real-time updates connected')
      } else if (state === 'failed') {
        error(message || 'Connection failed')
      }
    }
  )

  // Fetch agent status
  const { data: agentStatusResponse } = useAgentStatus(sessionId)

  // Invoke matching mutation
  const { mutate: invokeMatching, isPending: isInvoking } = useMutation({
    mutationFn: async () => {
      if (!sessionId) {
        throw new Error('Session ID is required')
      }
      return await workflowService.invokeMatching(sessionId)
    },
    onSuccess: (response) => {
      success(`Trade matching invoked. Invocation ID: ${response.invocationId}`)
      queryClient.invalidateQueries({ queryKey: ['agentStatus', sessionId] })
    },
    onError: (err) => {
      error(err instanceof Error ? err.message : 'Failed to invoke matching')
    },
  })

  /**
   * Handle bank file upload completion
   */
  const handleBankUploadComplete = (
    s3Uri: string,
    uploadSessionId?: string,
    uploadTraceId?: string
  ) => {
    console.log('Bank upload complete:', { s3Uri, uploadSessionId, uploadTraceId })

    if (uploadSessionId && !sessionId) {
      setSessionId(uploadSessionId)
      success(`Bank confirmation uploaded. Session: ${uploadSessionId.substring(0, 8)}...`)
    }

    if (uploadTraceId && !traceId) {
      setTraceId(uploadTraceId)
    }
  }

  /**
   * Handle counterparty file upload completion
   */
  const handleCounterpartyUploadComplete = (
    s3Uri: string,
    uploadSessionId?: string,
    uploadTraceId?: string
  ) => {
    console.log('Counterparty upload complete:', { s3Uri, uploadSessionId, uploadTraceId })

    if (uploadSessionId && !sessionId) {
      setSessionId(uploadSessionId)
      success(`Counterparty confirmation uploaded. Session: ${uploadSessionId.substring(0, 8)}...`)
    }

    if (uploadTraceId && !traceId) {
      setTraceId(uploadTraceId)
    }
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
              <GlassButton
                variant="outlined"
                onClick={handleRefresh}
                size="medium"
              >
                Refresh
              </GlassButton>
              <GlassButton
                variant="glass"
                disabled={!sessionId}
                size="medium"
              >
                Export Results
              </GlassButton>
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
