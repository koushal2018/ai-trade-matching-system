import { FC, useState } from 'react'
import {
  Box,
  Typography,
  Container,
  Chip,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
} from '@mui/icons-material'
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
import GlassCard from '../components/common/GlassCard'
import { fsiColors } from '../theme'

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
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Page Header */}
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <Typography
              variant="overline"
              sx={{
                color: fsiColors.orange.main,
                letterSpacing: '0.15em',
                fontWeight: 600,
              }}
            >
              UPLOAD & PROCESS
            </Typography>
            <Chip
              icon={<UploadIcon sx={{ fontSize: 14 }} />}
              label="Ready"
              size="small"
              sx={{
                height: 22,
                fontSize: '0.7rem',
                fontWeight: 600,
                bgcolor: `${fsiColors.status.success}20`,
                color: fsiColors.status.success,
                border: `1px solid ${fsiColors.status.success}40`,
                '& .MuiChip-icon': {
                  color: fsiColors.status.success,
                },
              }}
            />
          </Box>
          <Typography
            variant="h4"
            fontWeight={700}
            sx={{
              mb: 1,
              color: fsiColors.text.primary,
              letterSpacing: '-0.02em',
            }}
          >
            Trade Matching Upload
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: fsiColors.text.secondary, maxWidth: 500 }}
          >
            Upload trade confirmations for AI-powered matching and reconciliation
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1.5 }}>
          <GlassButton
            variant="outlined"
            onClick={handleRefresh}
            startIcon={<RefreshIcon />}
          >
            Refresh
          </GlassButton>
          <GlassButton
            variant="contained"
            disabled={!sessionId}
            startIcon={<ExportIcon />}
          >
            Export Results
          </GlassButton>
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* File Upload Section */}
        <GlassCard variant="default" sx={{ p: 0, overflow: 'hidden' }}>
          <UploadSection
            onBankUploadComplete={handleBankUploadComplete}
            onCounterpartyUploadComplete={handleCounterpartyUploadComplete}
            disabled={false}
          />
        </GlassCard>

        {/* Workflow Identifiers - Only show after upload */}
        {sessionId && (
          <GlassCard variant="default" sx={{ p: 0, overflow: 'hidden' }}>
            <WorkflowIdentifierSection sessionId={sessionId} traceId={traceId} />
          </GlassCard>
        )}

        {/* Agent Processing Status - Only show after upload */}
        {sessionId && (
          <GlassCard variant="default" sx={{ p: 0, overflow: 'hidden' }}>
            <AgentProcessingSection
              sessionId={sessionId}
              agentStatus={agentStatusResponse?.agents}
              onInvokeMatching={() => invokeMatching()}
              isInvoking={isInvoking}
            />
          </GlassCard>
        )}

        {/* Match Results - Only show after upload */}
        {sessionId && (
          <GlassCard variant="default" sx={{ p: 0, overflow: 'hidden' }}>
            <MatchResultSection sessionId={sessionId} />
          </GlassCard>
        )}

        {/* Exceptions - Only show after upload */}
        {sessionId && (
          <GlassCard variant="default" sx={{ p: 0, overflow: 'hidden' }}>
            <ExceptionSection sessionId={sessionId} />
          </GlassCard>
        )}
      </Box>
    </Container>
  )
}

export default TradeMatchingPage
