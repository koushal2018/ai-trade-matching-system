import axios, { AxiosProgressEvent } from 'axios'
import { UploadResponse } from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8001') + '/api'

export type SourceType = 'BANK' | 'COUNTERPARTY'

export interface UploadOptions {
  file: File
  sourceType: SourceType
  onProgress?: (progress: number) => void
}

class UploadService {
  /**
   * Upload a PDF file to S3 via the backend API
   * @param options Upload configuration including file, source type, and progress callback
   * @returns Upload response with session ID, trace ID, and S3 URI
   */
  async uploadFile(options: UploadOptions): Promise<UploadResponse> {
    const { file, sourceType, onProgress } = options

    // Create FormData for multipart/form-data upload
    const formData = new FormData()
    formData.append('file', file)
    formData.append('sourceType', sourceType)

    try {
      const response = await axios.post<UploadResponse>(
        `${API_BASE_URL}/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 30000, // 30 second timeout
          onUploadProgress: (progressEvent: AxiosProgressEvent) => {
            if (progressEvent.total && onProgress) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              )
              onProgress(percentCompleted)
            }
          },
        }
      )

      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        // Handle specific error cases
        if (error.code === 'ECONNABORTED') {
          throw new Error('Upload timeout. Please try again.')
        }
        
        if (error.response) {
          // Server responded with error
          const errorData = error.response.data as { error?: string; message?: string }
          throw new Error(errorData.message || errorData.error || 'Upload failed')
        }
        
        if (error.request) {
          // Request made but no response
          throw new Error('Network error. Please check your connection.')
        }
      }
      
      // Generic error
      throw new Error('An unexpected error occurred during upload')
    }
  }

  /**
   * Validate file before upload
   * @param file File to validate
   * @returns Validation result with error message if invalid
   */
  validateFile(file: File): { valid: boolean; error?: string } {
    // Check file type
    if (file.type !== 'application/pdf') {
      return {
        valid: false,
        error: 'Invalid file format. Only PDF files are accepted.',
      }
    }

    // Check file size (10 MB = 10,485,760 bytes)
    const MAX_FILE_SIZE = 10 * 1024 * 1024
    if (file.size > MAX_FILE_SIZE) {
      return {
        valid: false,
        error: 'File size exceeds 10 MB limit.',
      }
    }

    return { valid: true }
  }
}

export const uploadService = new UploadService()
