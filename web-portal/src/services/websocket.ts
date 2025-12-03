import type { WebSocketMessage, WebSocketEventType } from '../types'

type MessageHandler = (message: WebSocketMessage) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private handlers: Map<WebSocketEventType, Set<MessageHandler>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private url: string

  constructor() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    this.url = import.meta.env.VITE_WS_URL || `${wsProtocol}//${window.location.host}/ws`
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return

    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        this.notifyHandlers(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.attemptReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    setTimeout(() => this.connect(), delay)
  }


  private notifyHandlers(message: WebSocketMessage) {
    const handlers = this.handlers.get(message.type)
    if (handlers) {
      handlers.forEach((handler) => handler(message))
    }
  }

  subscribe(eventType: WebSocketEventType, handler: MessageHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set())
    }
    this.handlers.get(eventType)!.add(handler)
    return () => this.unsubscribe(eventType, handler)
  }

  unsubscribe(eventType: WebSocketEventType, handler: MessageHandler) {
    this.handlers.get(eventType)?.delete(handler)
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const wsService = new WebSocketService()
