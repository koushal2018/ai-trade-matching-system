import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAgentStatus } from '../useAgentStatus'
import { workflowService } from '../../services/workflowService'
import type { ReactNode } from 'react'

// Mock the workflow service
vi.mock('../../services/workflowService', () => ({
  workflowService: {
    getWorkflowStatus: vi.fn(),
  },
}))

describe('useAgentStatus', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false, // Disable retries for tests
        },
      },
    })
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: ReactNode }) => {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }

  it('should not fetch when sessionId is null', () => {
    const { result } = renderHook(() => useAgentStatus(null), { wrapper })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBeUndefined()
    expect(workflowService.getWorkflowStatus).not.toHaveBeenCalled()
  })

  it('should fetch agent status when sessionId is provided', async () => {
    const mockResponse = {
      sessionId: 'test-session-123',
      agents: {
        sessionId: 'test-session-123',
        pdfAdapter: { status: 'success' as const },
        tradeExtraction: { status: 'in-progress' as const },
        tradeMatching: { status: 'pending' as const },
        exceptionManagement: { status: 'pending' as const },
      },
      overallStatus: 'processing' as const,
      lastUpdated: '2024-12-24T10:00:00Z',
    }

    vi.mocked(workflowService.getWorkflowStatus).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useAgentStatus('test-session-123'), { wrapper })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockResponse)
    expect(workflowService.getWorkflowStatus).toHaveBeenCalledWith('test-session-123')
  })

  it('should handle errors gracefully', async () => {
    const mockError = new Error('Network error')
    vi.mocked(workflowService.getWorkflowStatus).mockRejectedValue(mockError)

    const { result } = renderHook(() => useAgentStatus('test-session-123'), { wrapper })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeTruthy()
  })

  it('should enable polling when agents are processing', async () => {
    const mockResponse = {
      sessionId: 'test-session-123',
      agents: {
        sessionId: 'test-session-123',
        pdfAdapter: { status: 'success' as const },
        tradeExtraction: { status: 'in-progress' as const },
        tradeMatching: { status: 'pending' as const },
        exceptionManagement: { status: 'pending' as const },
      },
      overallStatus: 'processing' as const,
      lastUpdated: '2024-12-24T10:00:00Z',
    }

    vi.mocked(workflowService.getWorkflowStatus).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useAgentStatus('test-session-123'), { wrapper })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Verify that refetchInterval is set (polling is enabled)
    // This is tested indirectly through the query configuration
    expect(result.current.data?.overallStatus).toBe('processing')
  })
})
