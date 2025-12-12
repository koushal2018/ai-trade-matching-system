import { apiClient } from './api'
import type { AuditRecord, AuditActionType } from '../types'

export interface AuditQueryParams {
  startDate?: string
  endDate?: string
  agentId?: string
  actionType?: AuditActionType
  page?: number
  pageSize?: number
}

export interface AuditResponse {
  records: AuditRecord[]
  total: number
  page: number
  pageSize: number
}

export const auditService = {
  async getAuditRecords(params: AuditQueryParams = {}): Promise<AuditResponse> {
    return apiClient.get<AuditResponse>('/audit', params as Record<string, unknown>)
  },

  async exportAuditRecords(
    params: AuditQueryParams,
    format: 'json' | 'csv' | 'xml'
  ): Promise<Blob> {
    const response = await fetch(
      `/api/audit/export?format=${format}&${new URLSearchParams(
        params as Record<string, string>
      )}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
      }
    )
    return response.blob()
  },
}
