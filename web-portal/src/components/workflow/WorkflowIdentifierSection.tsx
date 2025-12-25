import { FC } from 'react'
import {
  Container,
  Header,
  ColumnLayout,
  SpaceBetween,
  Box,
  Badge,
  Button,
} from '@cloudscape-design/components'
import { useNotifications } from '../../hooks/useNotifications'

export interface WorkflowIdentifierSectionProps {
  sessionId: string | null
  traceId: string | null
}

export const WorkflowIdentifierSection: FC<WorkflowIdentifierSectionProps> = ({
  sessionId,
  traceId,
}) => {
  const { addNotification } = useNotifications()

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      addNotification({
        type: 'success',
        header: `${label} copied to clipboard`,
        dismissible: true,
      })
    } catch (error) {
      // Handle clipboard API errors gracefully
      addNotification({
        type: 'error',
        header: 'Failed to copy to clipboard',
        content: 'Please try again or copy manually.',
        dismissible: true,
      })
    }
  }

  return (
    <Container header={<Header variant="h3">Workflow Identifiers</Header>}>
      <ColumnLayout columns={2} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Session ID</Box>
          <SpaceBetween direction="horizontal" size="xs">
            <Badge color="blue">{sessionId || '—'}</Badge>
            {sessionId && (
              <Button
                iconName="copy"
                variant="inline-icon"
                ariaLabel="Copy Session ID"
                onClick={() => copyToClipboard(sessionId, 'Session ID')}
              />
            )}
          </SpaceBetween>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Trace ID</Box>
          <SpaceBetween direction="horizontal" size="xs">
            <Box variant="code">{traceId || '—'}</Box>
            {traceId && (
              <Button
                iconName="copy"
                variant="inline-icon"
                ariaLabel="Copy Trace ID"
                onClick={() => copyToClipboard(traceId, 'Trace ID')}
              />
            )}
          </SpaceBetween>
        </SpaceBetween>
      </ColumnLayout>
    </Container>
  )
}
