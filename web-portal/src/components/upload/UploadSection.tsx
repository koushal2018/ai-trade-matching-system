import { FC } from 'react'
import {
  Container,
  Header,
  ColumnLayout
} from '@cloudscape-design/components'
import { FileUploadCard } from './FileUploadCard'

export interface UploadSectionProps {
  onBankUploadComplete: (s3Uri: string, sessionId?: string, traceId?: string) => void
  onCounterpartyUploadComplete: (s3Uri: string, sessionId?: string, traceId?: string) => void
  disabled?: boolean
}

export const UploadSection: FC<UploadSectionProps> = ({
  onBankUploadComplete,
  onCounterpartyUploadComplete,
  disabled = false
}) => {
  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Upload trade confirmation PDFs from both bank and counterparty sides"
        >
          Upload Trade Confirmations
        </Header>
      }
    >
      <ColumnLayout columns={2}>
        <FileUploadCard
          label="Bank Confirmation"
          sourceType="BANK"
          onUploadComplete={onBankUploadComplete}
          disabled={disabled}
        />
        
        <FileUploadCard
          label="Counterparty Confirmation"
          sourceType="COUNTERPARTY"
          onUploadComplete={onCounterpartyUploadComplete}
          disabled={disabled}
        />
      </ColumnLayout>
    </Container>
  )
}
