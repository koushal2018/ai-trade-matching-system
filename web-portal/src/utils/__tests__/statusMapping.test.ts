/**
 * Unit tests for status mapping utilities
 */

import { describe, it, expect } from 'vitest'
import { mapOverallStatus } from '../statusMapping'

describe('mapOverallStatus', () => {
  it('should map "pending" to "Pending"', () => {
    expect(mapOverallStatus('pending')).toBe('Pending')
  })

  it('should map "initializing" to "Initializing"', () => {
    expect(mapOverallStatus('initializing')).toBe('Initializing')
  })

  it('should map "processing" to "In Progress"', () => {
    expect(mapOverallStatus('processing')).toBe('In Progress')
  })

  it('should map "completed" to "Completed"', () => {
    expect(mapOverallStatus('completed')).toBe('Completed')
  })

  it('should map "failed" to "Failed"', () => {
    expect(mapOverallStatus('failed')).toBe('Failed')
  })

  it('should return "Unknown" for unmapped values', () => {
    expect(mapOverallStatus('invalid-status')).toBe('Unknown')
    expect(mapOverallStatus('random')).toBe('Unknown')
    expect(mapOverallStatus('')).toBe('Unknown')
  })

  it('should handle case-sensitive values correctly', () => {
    // Should not match uppercase
    expect(mapOverallStatus('PENDING')).toBe('Unknown')
    expect(mapOverallStatus('Pending')).toBe('Unknown')
    expect(mapOverallStatus('PROCESSING')).toBe('Unknown')
  })

  it('should handle null and undefined gracefully', () => {
    // TypeScript will prevent these at compile time, but testing runtime behavior
    expect(mapOverallStatus(null as any)).toBe('Unknown')
    expect(mapOverallStatus(undefined as any)).toBe('Unknown')
  })
})
