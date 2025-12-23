import { FC, useState } from 'react'
import { UploadSection } from './UploadSection'
import { SpaceBetween, Box } from '@cloudscape-design/components'

/**
 * Example usage of UploadSection component
 * This demonstrates how to integrate the UploadSection into a page
 */
export const UploadSectionExample: FC = () => {
  const [bankS3Uri, setBankS3Uri] = useState<string | null>(null)
  const [counterpartyS3Uri, setCounterpartyS3Uri] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [traceId, setTraceId] = useState<string | null>(null)

  const handleBankUpload = (s3Uri: string, session?: string, trace?: string) => {
    setBankS3Uri(s3Uri)
    if (session) setSessionId(session)
    if (trace) setTraceId(trace)
    console.log('Bank upload complete:', { s3Uri, session, trace })
  }

  const handleCounterpartyUpload = (s3Uri: string, session?: string, trace?: string) => {
    setCounterpartyS3Uri(s3Uri)
    if (session) setSessionId(session)
    if (trace) setTraceId(trace)
    console.log('Counterparty upload complete:', { s3Uri, session, trace })
  }

  return (
    <SpaceBetween size="l">
      <UploadSection
        onBankUploadComplete={handleBankUpload}
        onCounterpartyUploadComplete={handleCounterpartyUpload}
      />

      {/* Display upload status */}
      {(bankS3Uri || counterpartyS3Uri) && (
        <Box>
          <Box variant="h3">Upload Status</Box>
          {bankS3Uri && (
            <Box>Bank S3 URI: {bankS3Uri}</Box>
          )}
          {counterpartyS3Uri && (
            <Box>Counterparty S3 URI: {counterpartyS3Uri}</Box>
          )}
          {sessionId && (
            <Box>Session ID: {sessionId}</Box>
          )}
          {traceId && (
            <Box>Trace ID: {traceId}</Box>
          )}
        </Box>
      )}
    </SpaceBetween>
  )
}
