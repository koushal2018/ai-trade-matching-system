import { FC, useState, useEffect } from 'react'
import {
  Box,
  SpaceBetween,
  StatusIndicator,
  ExpandableSection,
  Popover,
  Button,
  Alert,
} from '@cloudscape-design/components'
import { LoadingBar } from '@cloudscape-design/chat-components'
import type { AgentStepStatus } from '../../types'

interface StepContentProps {
  step?: AgentStepStatus
  agentName: string
}

// Estimated duration for each agent in seconds
const getEstimatedDuration = (agentName: string): number => {
  switch (agentName) {
    case 'PDF Adapter Agent':
      return 15 // PDF processing typically takes 10-20 seconds
    case 'Trade Extraction Agent':
      return 20 // LLM extraction takes 15-25 seconds
    case 'Trade Matching Agent':
      return 12 // Matching logic takes 8-15 seconds
    case 'Exception Management Agent':
      return 8 // Exception handling is faster
    default:
      return 10
  }
}

export const StepContent: FC<StepContentProps> = ({ step, agentName }) => {
  // ISSUE 5 FIX: Delay showing loading indicator by 1 second to avoid flicker
  const [showLoading, setShowLoading] = useState(false)
  const estimatedDuration = getEstimatedDuration(agentName)

  useEffect(() => {
    if (step?.status === 'in-progress') {
      // Wait 1 second before showing loading indicator
      const timer = setTimeout(() => setShowLoading(true), 1000)
      return () => clearTimeout(timer)
    }
    setShowLoading(false)
  }, [step?.status])

  if (!step) return null

  return (
    <SpaceBetween size="s">
      {/* Activity Description */}
      {step.activity && (
        <Box variant="p" color="text-body-secondary">
          {step.activity}
        </Box>
      )}

      {/* ISSUE 2 & 5: LoadingBar for >10 second operations, with 1s delay */}
      {showLoading && estimatedDuration > 10 && (
        <Box>
          <LoadingBar variant="gen-ai" />
          <Box variant="small" color="text-body-secondary" margin={{ top: 'xs' }}>
            Processing... Estimated time: ~{estimatedDuration}s
          </Box>
        </Box>
      )}

      {/* ISSUE 4: Popover for supplemental step details */}
      {(step.startedAt || step.duration || step.completedAt) && (
        <Popover
          dismissButton={false}
          position="right"
          size="medium"
          triggerType="custom"
          content={
            <SpaceBetween size="s">
              {step.startedAt && (
                <>
                  <Box variant="awsui-key-label">Started</Box>
                  <Box>{new Date(step.startedAt).toLocaleString()}</Box>
                </>
              )}
              {step.duration !== undefined && (
                <>
                  <Box variant="awsui-key-label">Duration</Box>
                  <Box>{step.duration}s</Box>
                </>
              )}
              {step.completedAt && (
                <>
                  <Box variant="awsui-key-label">Completed</Box>
                  <Box>{new Date(step.completedAt).toLocaleString()}</Box>
                </>
              )}
            </SpaceBetween>
          }
        >
          <Button
            variant="inline-icon"
            iconName="status-info"
            ariaLabel={`${agentName} details`}
          />
        </Popover>
      )}

      {/* Sub-steps (expandable) */}
      {step.subSteps && step.subSteps.length > 0 && (
        <ExpandableSection header="Processing details" variant="footer">
          <SpaceBetween size="xs">
            {step.subSteps.map((subStep, idx) => (
              <SpaceBetween key={idx} direction="horizontal" size="xs">
                <StatusIndicator type={subStep.status}>
                  {subStep.title}
                </StatusIndicator>
                {subStep.description && (
                  <Box variant="small" color="text-body-secondary">
                    {subStep.description}
                  </Box>
                )}
              </SpaceBetween>
            ))}
          </SpaceBetween>
        </ExpandableSection>
      )}

      {/* Error Message */}
      {step.status === 'error' && step.error && (
        <Alert type="error" header="Processing failed">
          {step.error}
        </Alert>
      )}
    </SpaceBetween>
  )
}
