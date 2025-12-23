/**
 * Example usage of FileUploadCard component
 * 
 * This file demonstrates how to use the FileUploadCard component
 * in a CloudScape Container with proper layout.
 */

import { FC, useState } from 'react'
import { Container, Header, ColumnLayout, SpaceBetween } from '@cloudscape-design/components'
import { FileUploadCard } from './FileUploadCard'

export const FileUploadExample: FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [traceId, setTraceId] = useState<string | null>(null)

  const handleBankUploadComplete = (s3Uri: string, sessionId?: string, traceId?: string) => {
    console.log('Bank file uploaded:', s3Uri)
    if (sessionId) setSessionId(sessionId)
    if (traceId) setTraceId(traceId)
  }

  const handleCounterpartyUploadComplete = (s3Uri: string, sessionId?: string, traceId?: string) => {
    console.log('Counterparty file uploaded:', s3Uri)
    if (sessionId) setSessionId(sessionId)
    if (traceId) setTraceId(traceId)
  }

  return (
    <Container
      header={
        <Header variant="h2" description="Upload trade confirmation PDFs for matching">
          Upload Trade Confirmations
        </Header>
      }
    >
      <SpaceBetween size="l">
        <ColumnLayout columns={2}>
          <FileUploadCard
            label="Bank Confirmation"
            sourceType="BANK"
            onUploadComplete={handleBankUploadComplete}
          />
          <FileUploadCard
            label="Counterparty Confirmation"
            sourceType="COUNTERPARTY"
            onUploadComplete={handleCounterpartyUploadComplete}
          />
        </ColumnLayout>

        {sessionId && (
          <div>
            <strong>Session ID:</strong> {sessionId}
            {traceId && (
              <>
                <br />
                <strong>Trace ID:</strong> {traceId}
              </>
            )}
          </div>
        )}
      </SpaceBetween>
    </Container>
  )
}
