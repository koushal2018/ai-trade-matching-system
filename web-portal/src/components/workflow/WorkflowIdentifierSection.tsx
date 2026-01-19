import { FC } from 'react'
import {
  Container,
  Header,
  ColumnLayout,
  SpaceBetween,
  Box,
} from '@cloudscape-design/components'
import CopyToClipboard from '../common/CopyToClipboard'

export interface WorkflowIdentifierSectionProps {
  sessionId: string | null
  traceId: string | null
}

export const WorkflowIdentifierSection: FC<WorkflowIdentifierSectionProps> = ({
  sessionId,
  traceId,
}) => {
  return (
    <Container header={<Header variant="h3">Workflow Identifiers</Header>}>
      <ColumnLayout columns={2} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Session ID</Box>
          {sessionId ? (
            <CopyToClipboard
              text={sessionId}
              label="Session ID"
              truncate
              maxLength={32}
              showToast
              size="small"
            />
          ) : (
            <Box variant="p" color="text-body-secondary">—</Box>
          )}
        </SpaceBetween>

        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Trace ID</Box>
          {traceId ? (
            <CopyToClipboard
              text={traceId}
              label="Trace ID"
              truncate
              maxLength={32}
              showToast
              size="small"
            />
          ) : (
            <Box variant="p" color="text-body-secondary">—</Box>
          )}
        </SpaceBetween>
      </ColumnLayout>
    </Container>
  )
}
