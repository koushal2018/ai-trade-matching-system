import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { WebSocketMessage, AgentStatus, AgentStepStatus } from '../types'
import { agentStatusKeys } from './useAgentStatus'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001'

/**
 * WebSocket connection states
 */
type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'failed' | 'fallback'

/**
 * Exponential backoff configuration for reconnection
 */
interface ReconnectConfig {
  maxAttempts: number
  baseDelay: number // milliseconds
  maxDelay: number // milliseconds
}

const DEFAULT_RECONNECT_CONFIG: ReconnectConfig = {
  maxAttempts: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 30000, // 30 seconds (1s, 2s, 4s, 8s, max 30s)
}

/**
 * Calculate exponential backoff delay
 */
function getReconnectDelay(attempt: number, config: ReconnectConfig): number {
  const delay = config.baseDelay * Math.pow(2, attempt)
  return Math.min(delay, config.maxDelay)
}

/**
 * Hook to manage WebSocket connection for real-time agent status updates
 * 
 * Features:
 * - Automatic connection when sessionId is provided
 * - Exponential backoff reconnection (1s, 2s, 4s, 8s, max 30s)
 * - Fallback to polling after 3 failed reconnection attempts
 * - Updates React Query cache on message receipt
 * - Flashbar notifications for connection state changes
 * 
 * @param sessionId - Workflow session ID (null to disable WebSocket)
 * @param onConnectionChange - Callback for connection state changes (for Flashbar notifications)
 * @returns Connection state and reconnect function
 */
export function useAgentWebSocket(
  sessionId: string | null,
  onConnectionChange?: (state: ConnectionState, message: string) => void
) {
  const queryClient = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')

  /**
   * Update connection state and notify callback
   */
  const updateConnectionState = (state: ConnectionState, message: string) => {
    setConnectionState(state)
    onConnectionChange?.(state, message)
  }

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = (event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)

      // Validate message has required fields
      if (!message.type || !message.sessionId) {
        console.warn('Invalid WebSocket message format:', message)
        return
      }

      // Only process messages for the current session
      if (message.sessionId !== sessionId) {
        return
      }

      // Update React Query cache based on message type
      switch (message.type) {
        case 'AGENT_STATUS_UPDATE': {
          // Update full agent status
          const agentStatus = message.data as AgentStatus
          queryClient.setQueryData(
            agentStatusKeys.bySession(sessionId),
            (oldData: any) => ({
              ...oldData,
              agents: agentStatus,
              lastUpdated: message.timestamp,
            })
          )
          break
        }

        case 'STEP_UPDATE': {
          // Update individual step status
          const stepUpdate = message.data as AgentStepStatus & { agentName: string }
          queryClient.setQueryData(
            agentStatusKeys.bySession(sessionId),
            (oldData: any) => {
              if (!oldData) return oldData

              const agentKey = stepUpdate.agentName as keyof AgentStatus
              return {
                ...oldData,
                agents: {
                  ...oldData.agents,
                  [agentKey]: stepUpdate,
                },
                lastUpdated: message.timestamp,
              }
            }
          )
          break
        }

        case 'RESULT_AVAILABLE': {
          // Invalidate match result query to trigger refetch
          queryClient.invalidateQueries({
            queryKey: ['matchResult', sessionId],
          })
          break
        }

        case 'EXCEPTION': {
          // Invalidate exceptions query to trigger refetch
          queryClient.invalidateQueries({
            queryKey: ['exceptions', sessionId],
          })
          break
        }

        default:
          console.warn('Unknown WebSocket message type:', message.type)
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }

  /**
   * Connect to WebSocket server
   */
  const connect = () => {
    if (!sessionId) {
      return
    }

    // Don't create new connection if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    try {
      updateConnectionState('connecting', 'Connecting to real-time updates...')

      const ws = new WebSocket(`${WS_BASE_URL}/ws?sessionId=${sessionId}`)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        reconnectAttemptsRef.current = 0 // Reset reconnect attempts on successful connection
        updateConnectionState('connected', 'Connected to real-time updates')
      }

      ws.onmessage = handleMessage

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        wsRef.current = null

        // Don't reconnect if closed normally or if sessionId is null
        if (event.code === 1000 || !sessionId) {
          updateConnectionState('disconnected', 'Disconnected from real-time updates')
          return
        }

        // Attempt reconnection with exponential backoff
        if (reconnectAttemptsRef.current < DEFAULT_RECONNECT_CONFIG.maxAttempts) {
          const delay = getReconnectDelay(reconnectAttemptsRef.current, DEFAULT_RECONNECT_CONFIG)
          reconnectAttemptsRef.current++

          console.log(
            `Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${DEFAULT_RECONNECT_CONFIG.maxAttempts})`
          )

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else {
          // Fall back to polling after max reconnection attempts
          console.log('Max reconnection attempts reached. Falling back to polling.')
          updateConnectionState(
            'fallback',
            'Real-time updates unavailable. Using polling mode.'
          )
        }
      }
    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
      updateConnectionState('failed', 'Failed to connect to real-time updates')
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = () => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Close WebSocket connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounted')
      wsRef.current = null
    }

    updateConnectionState('disconnected', 'Disconnected from real-time updates')
  }

  /**
   * Manually trigger reconnection (resets attempt counter)
   */
  const reconnect = () => {
    reconnectAttemptsRef.current = 0
    disconnect()
    connect()
  }

  // Connect when sessionId changes
  useEffect(() => {
    if (sessionId) {
      connect()
    }

    // Cleanup on unmount or sessionId change
    return () => {
      disconnect()
    }
  }, [sessionId])

  return {
    connectionState,
    reconnect,
    isConnected: connectionState === 'connected',
    isFallback: connectionState === 'fallback',
  }
}
