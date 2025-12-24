import { FC, useState, useEffect } from 'react'
import {
  Container,
  Header,
  Button,
  SpaceBetween,
  Box,
  StatusIndicator,
  ExpandableSection,
} from '@cloudscape-design/components'
import { StepContent } from './StepContent'
import type { AgentStatus, AgentStatusType } from '../../types'

interface AgentProcessingSectionProps {
  sessionId: string
  agentStatus?: AgentStatus
  onInvokeMatching: () => void
  isInvoking?: boolean
}

interface StepConfig {
  title: string
  agentName: string
  status: AgentStatusType
}

const getStatusLabel = (status?: AgentStatusType): string => {
  switch (status) {
    case 'pending':
      return 'Pending'
    case 'loading':
      return 'Starting...'
    case 'in-progress':
      return 'In progress'
    case 'success':
      return 'Complete'
    case 'error':
      return 'Error'
    case 'warning':
      return 'Warning'
    case 'stopped':
      return 'Stopped'
    case 'info':
      return 'Info'
    default:
      return 'Pending'
  }
}

export const AgentProcessingSection: FC<AgentProcessingSectionProps> = ({
  sessionId,
  agentStatus,
  onInvokeMatching,
  isInvoking = false,
}) => {
  // Track last updated timestamp (Requirement 10.8)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Update timestamp when agentStatus changes
  useEffect(() => {
    if (agentStatus) {
      setLastUpdated(new Date())
      setIsRefreshing(false)
    }
  }, [agentStatus])

  // Handle refresh (Requirement 10.3, 10.4, 10.5)
  const handleRefresh = () => {
    setIsRefreshing(true)
    // Trigger a refetch by updating the timestamp
    // The parent component will refetch via React Query
    window.location.reload()
  }
  // Determine if matching is in progress
  const isMatchingInProgress = agentStatus?.tradeMatching.status === 'in-progress'

  const steps: StepConfig[] = [
    {
      title: 'PDF Adapter Agent',
      agentName: 'PDF Adapter Agent',
      status: agentStatus?.pdfAdapter.status || 'pending',
    },
    {
      title: 'Trade Extraction Agent',
      agentName: 'Trade Extraction Agent',
      status: agentStatus?.tradeExtraction.status || 'pending',
    },
    {
      title: 'Trade Matching Agent',
      agentName: 'Trade Matching Agent',
      status: agentStatus?.tradeMatching.status || 'pending',
    },
    {
      title: 'Exception Management Agent',
      agentName: 'Exception Management Agent',
      status: agentStatus?.exceptionManagement.status || 'pending',
    },
  ]

  const getStepData = (agentName: string) => {
    switch (agentName) {
      case 'PDF Adapter Agent':
        return agentStatus?.pdfAdapter
      case 'Trade Extraction Agent':
        return agentStatus?.tradeExtraction
      case 'Trade Matching Agent':
        return agentStatus?.tradeMatching
      case 'Exception Management Agent':
        return agentStatus?.exceptionManagement
      default:
        return undefined
    }
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Real-time AI agent processing workflow"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                iconName="refresh"
                onClick={handleRefresh}
                loading={isRefreshing}
                ariaLabel="Refresh agent status"
              >
                Refresh
              </Button>
              <Button
                variant="primary"
                iconName="gen-ai"
                iconAlign="left"
                onClick={onInvokeMatching}
                disabled={isInvoking || isMatchingInProgress || !sessionId}
                loading={isInvoking}
                loadingText="Invoking..."
                ariaLabel="Invoke AI-powered trade matching"
              >
                Invoke Matching
              </Button>
            </SpaceBetween>
          }
        >
          Agent Processing Status
        </Header>
      }
    >
      <SpaceBetween size="l">
        {steps.map((step, index) => (
          <Box key={index}>
            <SpaceBetween size="s">
              <Box>
                <SpaceBetween direction="horizontal" size="xs">
                  <StatusIndicator type={step.status}>
                    {step.title}
                  </StatusIndicator>
                  <Box variant="small" color="text-body-secondary">
                    {getStatusLabel(step.status)}
                  </Box>
                </SpaceBetween>
              </Box>
              <ExpandableSection headerText="Details" variant="footer">
                <StepContent
                  step={getStepData(step.agentName)}
                  agentName={step.agentName}
                />
              </ExpandableSection>
            </SpaceBetween>
          </Box>
        ))}
        
        {/* Last updated timestamp (Requirement 10.8) */}
        <Box variant="small" color="text-body-secondary" textAlign="right">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </Box>
      </SpaceBetween>
    </Container>
  )
}
