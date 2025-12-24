import { useQuery } from '@tanstack/react-query'
import { workflowService, type WorkflowStatusResponse } from '../services/workflowService'

/**
 * Query key factory for agent status queries
 */
export const agentStatusKeys = {
  all: ['agentStatus'] as const,
  bySession: (sessionId: string) => [...agentStatusKeys.all, sessionId] as const,
}

/**
 * Hook to fetch and poll agent status using React Query
 * 
 * Features:
 * - Automatic polling every 30 seconds during active processing
 * - Caching with 10-second stale time
 * - Error handling with retry logic
 * - Loading and error states
 * 
 * @param sessionId - Workflow session ID (null to disable query)
 * @returns React Query result with agent status data
 */
export function useAgentStatus(sessionId: string | null) {
  return useQuery({
    queryKey: agentStatusKeys.bySession(sessionId || ''),
    queryFn: async () => {
      if (!sessionId) {
        throw new Error('Session ID is required')
      }
      return await workflowService.getWorkflowStatus(sessionId)
    },
    enabled: !!sessionId, // Only run query if sessionId exists
    staleTime: 10000, // Consider data stale after 10 seconds
    refetchInterval: (query) => {
      // Poll every 30 seconds if processing is active
      const data = query.state.data as WorkflowStatusResponse | undefined
      
      if (!data) {
        return false // Don't poll if no data yet
      }
      
      // Check if any agent is actively processing
      const isProcessing = 
        data.overallStatus === 'processing' ||
        data.overallStatus === 'initializing' ||
        data.agents.pdfAdapter.status === 'in-progress' ||
        data.agents.pdfAdapter.status === 'loading' ||
        data.agents.tradeExtraction.status === 'in-progress' ||
        data.agents.tradeExtraction.status === 'loading' ||
        data.agents.tradeMatching.status === 'in-progress' ||
        data.agents.tradeMatching.status === 'loading' ||
        data.agents.exceptionManagement.status === 'in-progress' ||
        data.agents.exceptionManagement.status === 'loading'
      
      return isProcessing ? 30000 : false // 30 seconds if processing, otherwise stop polling
    },
    retry: 3, // Retry failed requests up to 3 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  })
}
