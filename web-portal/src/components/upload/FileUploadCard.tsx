import { FC, useState } from 'react'
import {
  FileUpload,
  FormField,
  Box,
  ProgressBar,
  StatusIndicator,
  FileUploadProps,
  NonCancelableCustomEvent
} from '@cloudscape-design/components'
import { uploadService } from '../../services'

export interface FileUploadCardProps {
  label: 'Bank Confirmation' | 'Counterparty Confirmation'
  sourceType: 'BANK' | 'COUNTERPARTY'
  onUploadComplete: (s3Uri: string, sessionId?: string, traceId?: string) => void
  disabled?: boolean
}

interface UploadState {
  files: File[]
  uploadProgress: number
  status: 'idle' | 'uploading' | 'success' | 'error'
  errorText: string | null
}

export const FileUploadCard: FC<FileUploadCardProps> = ({
  label,
  sourceType,
  onUploadComplete,
  disabled = false
}) => {
  const [state, setState] = useState<UploadState>({
    files: [],
    uploadProgress: 0,
    status: 'idle',
    errorText: null
  })

  const uploadFile = async (file: File) => {
    setState(prev => ({ ...prev, status: 'uploading', uploadProgress: 0 }))

    try {
      // Use uploadService for consistent error handling and progress tracking
      const response = await uploadService.uploadFile({
        file,
        sourceType,
        onProgress: (progress) => {
          setState(prev => ({
            ...prev,
            uploadProgress: progress
          }))
        }
      })

      setState(prev => ({
        ...prev,
        status: 'success',
        uploadProgress: 100,
        errorText: null
      }))

      // Call onUploadComplete with s3Uri and optional sessionId/traceId
      onUploadComplete(response.s3Uri, response.sessionId, response.traceId)
    } catch (error) {
      setState(prev => ({
        ...prev,
        status: 'error',
        uploadProgress: 0,
        errorText: error instanceof Error ? error.message : 'Upload failed'
      }))
    }
  }

  const handleChange = ({ detail }: NonCancelableCustomEvent<FileUploadProps.ChangeDetail>) => {
    // Don't process if disabled or uploading
    if (disabled || state.status === 'uploading') {
      return
    }

    const file = detail.value[0]

    // Clear previous state
    setState(prev => ({
      ...prev,
      files: detail.value,
      errorText: null,
      status: 'idle'
    }))

    // Validate file if present using uploadService
    if (file) {
      const validation = uploadService.validateFile(file)
      if (!validation.valid) {
        setState(prev => ({
          ...prev,
          errorText: validation.error || 'Invalid file',
          status: 'error'
        }))
        return
      }

      // Start upload
      uploadFile(file)
    }
  }

  return (
    <FormField
      label={label}
      constraintText="Accepted file types: PDF. Maximum file size: 10 MB."
      errorText={state.errorText || undefined}
    >
      <FileUpload
        onChange={handleChange}
        value={state.files}
        i18nStrings={{
          uploadButtonText: () => disabled || state.status === 'uploading' ? 'Uploading...' : 'Choose file',
          dropzoneText: () => disabled || state.status === 'uploading' ? 'Upload in progress...' : 'Drop PDF file here',
          removeFileAriaLabel: (index) => `Remove file ${index + 1}`,
          errorIconAriaLabel: 'Error'
        }}
        accept=".pdf,application/pdf"
        showFileLastModified
        showFileSize
      />
      
      {/* Display progress bar during upload */}
      {state.status === 'uploading' && (
        <Box margin={{ top: 's' }}>
          <ProgressBar
            value={state.uploadProgress}
            label="Uploading to S3..."
            status="in-progress"
          />
        </Box>
      )}

      {/* Display success indicator */}
      {state.status === 'success' && state.files.length > 0 && (
        <Box margin={{ top: 's' }}>
          <StatusIndicator type="success" ariaLabel={`File ${state.files[0].name} uploaded successfully`}>
            {state.files[0].name} uploaded successfully
          </StatusIndicator>
        </Box>
      )}

      {/* Display error indicator */}
      {state.status === 'error' && !state.errorText && (
        <Box margin={{ top: 's' }}>
          <StatusIndicator type="error" ariaLabel="Upload failed">
            Upload failed. Please try again.
          </StatusIndicator>
        </Box>
      )}
    </FormField>
  )
}
