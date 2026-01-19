import axios, { AxiosError, AxiosInstance } from 'axios'

// When MSW is enabled, use relative URLs so MSW can intercept
// Otherwise use the configured API URL
const isMSWEnabled = import.meta.env.VITE_ENABLE_MSW === 'true'
const API_BASE_URL = isMSWEnabled
  ? '/api'
  : (import.meta.env.VITE_API_URL || 'http://localhost:8001') + '/api'

console.log('[API] MSW enabled:', isMSWEnabled)
console.log('[API] Base URL:', API_BASE_URL)

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
    })

    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`
      }
      return config
    })

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.token = null
          window.location.href = '/login'
        }
        throw error
      }
    )
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('auth_token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('auth_token')
  }

  loadToken() {
    this.token = localStorage.getItem('auth_token')
  }

  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }
}

export const apiClient = new ApiClient()
apiClient.loadToken()
