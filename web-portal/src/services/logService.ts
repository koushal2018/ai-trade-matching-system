import axios from 'axios'

const API_BASE_URL = '/api'

export interface LogEvent {
  timestamp: string
  message: string
  logGroup: string
  logGroupName: string
  logStream?: string
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG'
}

export interface LogGroupInfo {
  logGroup: string
  displayName: string
  available: boolean
}

export interface RecentLogsResponse {
  logGroup: string
  logGroupName: string
  events: LogEvent[]
}

class LogService {
  /**
   * Get available log groups for streaming
   */
  async getAvailableLogGroups(): Promise<LogGroupInfo[]> {
    const response = await axios.get<LogGroupInfo[]>(`${API_BASE_URL}/logs/groups`)
    return response.data
  }

  /**
   * Get recent logs from a specific log group
   */
  async getRecentLogs(logGroup: string, limit: number = 50): Promise<RecentLogsResponse> {
    const response = await axios.get<RecentLogsResponse>(`${API_BASE_URL}/logs/recent`, {
      params: { log_group: logGroup, limit }
    })
    return response.data
  }
}

export const logService = new LogService()
