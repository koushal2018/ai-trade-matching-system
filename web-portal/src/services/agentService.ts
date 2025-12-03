import { apiClient } from './api'
import type { AgentHealth, ProcessingMetrics } from '../types'

export const agentService = {
  async getAgentStatus(): Promise<AgentHealth[]> {
    return apiClient.get<AgentHealth[]>('/agents/status')
  },

  async getProcessingMetrics(): Promise<ProcessingMetrics> {
    return apiClient.get<ProcessingMetrics>('/metrics/processing')
  },
}
