import { describe, it, expect } from 'vitest'
import { uploadService } from './uploadService'

describe('uploadService', () => {
  describe('validateFile', () => {
    it('accepts valid PDF files under 10MB', () => {
      const validFile = new File(['test content'], 'test.pdf', {
        type: 'application/pdf',
      })
      
      const result = uploadService.validateFile(validFile)
      
      expect(result.valid).toBe(true)
      expect(result.error).toBeUndefined()
    })

    it('rejects non-PDF files', () => {
      const invalidFile = new File(['test content'], 'test.txt', {
        type: 'text/plain',
      })
      
      const result = uploadService.validateFile(invalidFile)
      
      expect(result.valid).toBe(false)
      expect(result.error).toBe('Invalid file format. Only PDF files are accepted.')
    })

    it('rejects files larger than 10MB', () => {
      // Create a file larger than 10MB
      const largeContent = new Array(11 * 1024 * 1024).fill('a').join('')
      const largeFile = new File([largeContent], 'large.pdf', {
        type: 'application/pdf',
      })
      
      const result = uploadService.validateFile(largeFile)
      
      expect(result.valid).toBe(false)
      expect(result.error).toBe('File size exceeds 10 MB limit.')
    })

    it('accepts PDF files exactly at 10MB limit', () => {
      // Create a file exactly 10MB
      const content = new Array(10 * 1024 * 1024).fill('a').join('')
      const file = new File([content], 'exact.pdf', {
        type: 'application/pdf',
      })
      
      const result = uploadService.validateFile(file)
      
      expect(result.valid).toBe(true)
      expect(result.error).toBeUndefined()
    })
  })
})
