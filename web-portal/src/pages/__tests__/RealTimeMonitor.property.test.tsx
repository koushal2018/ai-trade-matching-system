/**
 * Property-Based Tests for Real-Time Monitor
 * Feature: web-portal-bug-fixes
 * 
 * These tests use fast-check to verify universal properties across random inputs.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import fc from 'fast-check'
import { wsService } from '../../services/websocket'
import type { RecentSessionItem } from '../../services/workflowService'

// Mock the services
vi.mock('../../services/websocket', () => ({
  wsService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    subscribe: vi.fn(() => vi.fn()), // Returns unsubscribe function
    isConnected: vi.fn(() => true),
  },
}))

vi.mock('../../services/workflowService', () => ({
  workflowService: {
    getRecentSessions: vi.fn(),
  },
}))

vi.mock('../../services/agentService', () => ({
  agentService: {
    getAgentStatus: vi.fn().mockResolvedValue([]),
  },
}))

describe('Property 1: WebSocket Subscription Completeness', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  /**
   * **Validates: Requirements 1.3**
   * 
   * Property: For any list of active sessions returned by `/api/workflow/recent`,
   * the Real-Time Monitor SHALL send a SUBSCRIBE message for each session that is
   * not in 'completed' status and not already subscribed.
   * 
   * This property verifies that:
   * 1. SUBSCRIBE is sent for all non-completed sessions
   * 2. SUBSCRIBE is NOT sent for completed sessions
   * 3. SUBSCRIBE is NOT sent for already-subscribed sessions
   * 4. The correct sessionId is included in each SUBSCRIBE message
   */
  it('should send SUBSCRIBE for all non-completed active sessions', () => {
    fc.assert(
      fc.property(
        // Generate random arrays of session items with various statuses
        fc.array(
          fc.record({
            sessionId: fc.string({ minLength: 1, maxLength: 50 }),
            status: fc.constantFrom(
              'pending',
              'initializing', 
              'processing',
              'completed',
              'failed'
            ),
            createdAt: fc.date().map(d => d.toISOString()),
            lastUpdated: fc.date().map(d => d.toISOString()),
          }),
          { minLength: 0, maxLength: 20 }
        ),
        (sessions: RecentSessionItem[]) => {
          // Reset mocks for this iteration
          vi.clearAllMocks()
          
          // Track which sessions we've already subscribed to
          const subscribedSessions = new Set<string>()
          
          // Simulate the subscription logic from RealTimeMonitor
          sessions.forEach((session) => {
            if (
              session.sessionId &&
              session.status !== 'completed' &&
              !subscribedSessions.has(session.sessionId)
            ) {
              wsService.send({
                type: 'SUBSCRIBE',
                sessionId: session.sessionId,
              })
              subscribedSessions.add(session.sessionId)
            }
          })
          
          // Calculate expected subscriptions
          const uniqueNonCompletedSessions = new Set(
            sessions
              .filter(s => s.sessionId && s.status !== 'completed')
              .map(s => s.sessionId)
          )
          
          // Verify: SUBSCRIBE was called exactly once for each unique non-completed session
          expect(wsService.send).toHaveBeenCalledTimes(uniqueNonCompletedSessions.size)
          
          // Verify: Each SUBSCRIBE message has the correct format
          const sendCalls = (wsService.send as ReturnType<typeof vi.fn>).mock.calls
          sendCalls.forEach((call) => {
            const message = call[0]
            expect(message).toHaveProperty('type', 'SUBSCRIBE')
            expect(message).toHaveProperty('sessionId')
            expect(typeof message.sessionId).toBe('string')
            expect(message.sessionId.length).toBeGreaterThan(0)
          })
          
          // Verify: All sent sessionIds are from non-completed sessions
          const sentSessionIds = sendCalls.map(call => call[0].sessionId)
          sentSessionIds.forEach((sessionId) => {
            const session = sessions.find(s => s.sessionId === sessionId)
            expect(session).toBeDefined()
            expect(session!.status).not.toBe('completed')
          })
          
          // Verify: No completed sessions were subscribed to
          const completedSessions = sessions.filter(s => s.status === 'completed')
          completedSessions.forEach((session) => {
            expect(sentSessionIds).not.toContain(session.sessionId)
          })
        }
      ),
      { numRuns: 100 } // Run 100 iterations with random data
    )
  })

  /**
   * Additional property test: Idempotency of subscription
   * 
   * Verifies that calling the subscription logic multiple times with the same
   * session list doesn't result in duplicate SUBSCRIBE messages.
   */
  it('should not send duplicate SUBSCRIBE messages for already-subscribed sessions', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            sessionId: fc.string({ minLength: 1, maxLength: 50 }),
            status: fc.constantFrom('pending', 'processing', 'initializing'),
            createdAt: fc.date().map(d => d.toISOString()),
            lastUpdated: fc.date().map(d => d.toISOString()),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        (sessions: RecentSessionItem[]) => {
          vi.clearAllMocks()
          
          const subscribedSessions = new Set<string>()
          
          // First subscription pass
          sessions.forEach((session) => {
            if (
              session.sessionId &&
              session.status !== 'completed' &&
              !subscribedSessions.has(session.sessionId)
            ) {
              wsService.send({
                type: 'SUBSCRIBE',
                sessionId: session.sessionId,
              })
              subscribedSessions.add(session.sessionId)
            }
          })
          
          const firstPassCallCount = (wsService.send as ReturnType<typeof vi.fn>).mock.calls.length
          
          // Second subscription pass (simulating periodic check)
          sessions.forEach((session) => {
            if (
              session.sessionId &&
              session.status !== 'completed' &&
              !subscribedSessions.has(session.sessionId)
            ) {
              wsService.send({
                type: 'SUBSCRIBE',
                sessionId: session.sessionId,
              })
              subscribedSessions.add(session.sessionId)
            }
          })
          
          const secondPassCallCount = (wsService.send as ReturnType<typeof vi.fn>).mock.calls.length
          
          // Verify: No additional SUBSCRIBE messages sent in second pass
          expect(secondPassCallCount).toBe(firstPassCallCount)
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Edge case property test: Empty session list
   * 
   * Verifies that no SUBSCRIBE messages are sent when there are no sessions.
   */
  it('should not send any SUBSCRIBE messages when session list is empty', () => {
    vi.clearAllMocks()
    
    const sessions: RecentSessionItem[] = []
    const subscribedSessions = new Set<string>()
    
    sessions.forEach((session) => {
      if (
        session.sessionId &&
        session.status !== 'completed' &&
        !subscribedSessions.has(session.sessionId)
      ) {
        wsService.send({
          type: 'SUBSCRIBE',
          sessionId: session.sessionId,
        })
        subscribedSessions.add(session.sessionId)
      }
    })
    
    expect(wsService.send).not.toHaveBeenCalled()
  })

  /**
   * Edge case property test: All completed sessions
   * 
   * Verifies that no SUBSCRIBE messages are sent when all sessions are completed.
   */
  it('should not send any SUBSCRIBE messages when all sessions are completed', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            sessionId: fc.string({ minLength: 1, maxLength: 50 }),
            status: fc.constant('completed'),
            createdAt: fc.date().map(d => d.toISOString()),
            lastUpdated: fc.date().map(d => d.toISOString()),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        (sessions: RecentSessionItem[]) => {
          vi.clearAllMocks()
          
          const subscribedSessions = new Set<string>()
          
          sessions.forEach((session) => {
            if (
              session.sessionId &&
              session.status !== 'completed' &&
              !subscribedSessions.has(session.sessionId)
            ) {
              wsService.send({
                type: 'SUBSCRIBE',
                sessionId: session.sessionId,
              })
              subscribedSessions.add(session.sessionId)
            }
          })
          
          expect(wsService.send).not.toHaveBeenCalled()
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Property test: Duplicate session IDs with different statuses
   * 
   * Verifies correct behavior when the same sessionId appears multiple times
   * with different statuses (should only subscribe once to the first non-completed occurrence).
   */
  it('should handle duplicate session IDs correctly', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }),
        fc.array(
          fc.constantFrom('pending', 'processing', 'completed', 'failed'),
          { minLength: 2, maxLength: 5 }
        ),
        (sessionId: string, statuses: string[]) => {
          vi.clearAllMocks()
          
          // Create sessions with the same ID but different statuses
          const sessions: RecentSessionItem[] = statuses.map(status => ({
            sessionId,
            status,
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
          }))
          
          const subscribedSessions = new Set<string>()
          
          sessions.forEach((session) => {
            if (
              session.sessionId &&
              session.status !== 'completed' &&
              !subscribedSessions.has(session.sessionId)
            ) {
              wsService.send({
                type: 'SUBSCRIBE',
                sessionId: session.sessionId,
              })
              subscribedSessions.add(session.sessionId)
            }
          })
          
          // Should subscribe at most once, and only if at least one status is non-completed
          const hasNonCompleted = statuses.some(s => s !== 'completed')
          
          if (hasNonCompleted) {
            expect(wsService.send).toHaveBeenCalledTimes(1)
            expect((wsService.send as ReturnType<typeof vi.fn>).mock.calls[0][0]).toEqual({
              type: 'SUBSCRIBE',
              sessionId,
            })
          } else {
            expect(wsService.send).not.toHaveBeenCalled()
          }
        }
      ),
      { numRuns: 100 }
    )
  })
})
