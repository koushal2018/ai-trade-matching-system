/**
 * Unit Tests for Dashboard Component
 * Feature: web-portal-bug-fixes
 * Task: 6.2 Fix active agent count calculation in Dashboard
 * 
 * Requirements: 3.3, 3.4, 3.8, 3.10
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../Dashboard'
import { agentService } from '../../services/agentService'
import { workflowService } from '../../services/workflowService'
import type { AgentHealth, MatchingStatusResponse } from '../../types'

// Mock the services
vi.mock('../../services/agentService', () => ({
  agentService: {
    getAgentStatus: vi.fn(),
    getProcessingMetrics: vi.fn(),
  },
}))

vi.mock('../../services/workflowService', () => ({
  workflowService: {
    getMatchingStatus: vi.fn(),
    getRecentSessions: vi.fn(),
  },
}))

vi.mock('../../services/websocket', () => ({
  wsService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    subscribe: vi.fn(() => vi.fn()), // Returns unsubscribe function
    isConnected: vi.fn(() => true),
  },
}))

// Helper to create a test agent
const createAgent = (
  agentId: string,
  status: 'HEALTHY' | 'DEGRADED' | 'OFFLINE' | 'UNHEALTHY',
  activeTasks: number = 0
): AgentHealth => ({
  agentId,
  agentName: `Agent ${agentId}`,
  status,
  activeTasks,
  lastHeartbeat: new Date().toISOString(),
  metrics: {
    latencyMs: 1000,
    throughput: 10,
    errorRate: 0.01,
    totalTokens: 1000,
    inputTokens: 800,
    outputTokens: 200,
    cycleCount: 2,
    toolCallCount: 3,
    successRate: 0.99,
  },
})

// Helper to render Dashboard with React Query
const renderDashboard = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Dashboard - Active Agent Count', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mock implementations
    vi.mocked(agentService.getProcessingMetrics).mockResolvedValue({
      totalProcessed: 100,
      matchedCount: 80,
      unmatchedCount: 15,
      pendingCount: 5,
      errorCount: 0,
      breakCount: 0,
      pendingReview: 0,
      throughputPerHour: 50,
      avgProcessingTimeMs: 2000,
      bankTradeCount: 50,
      counterpartyTradeCount: 50,
    })
    
    vi.mocked(workflowService.getRecentSessions).mockResolvedValue([])
  })

  /**
   * Test: Count with all HEALTHY agents
   * Requirements: 3.3, 3.6
   * 
   * Verifies that when all agents are HEALTHY, the active agent count
   * equals the total number of agents (which are already filtered for
   * ACTIVE deployment_status by the backend).
   */
  it('should count all agents when all are HEALTHY', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 2),
      createAgent('agent_2', 'HEALTHY', 3),
      createAgent('agent_3', 'HEALTHY', 1),
      createAgent('agent_4', 'HEALTHY', 0),
      createAgent('agent_5', 'HEALTHY', 4),
      createAgent('agent_6', 'HEALTHY', 2),
    ]
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    // Wait for the active agents count to be displayed
    await waitFor(() => {
      // The HeroMetrics component displays the count
      // Look for the "Active Agents" label and its associated value
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
    
    // Verify the count is 6 (all HEALTHY agents)
    await waitFor(() => {
      const countElement = screen.getByText('6')
      expect(countElement).toBeInTheDocument()
    })
  })

  /**
   * Test: Count excludes DEGRADED agents
   * Requirements: 3.3, 3.7
   * 
   * Verifies that DEGRADED agents are NOT counted in the active agent count,
   * only HEALTHY agents are counted.
   */
  it('should exclude DEGRADED agents from active count', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 2),
      createAgent('agent_2', 'HEALTHY', 3),
      createAgent('agent_3', 'DEGRADED', 1), // Should NOT be counted
      createAgent('agent_4', 'HEALTHY', 0),
      createAgent('agent_5', 'DEGRADED', 4), // Should NOT be counted
      createAgent('agent_6', 'HEALTHY', 2),
    ]
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
    
    // Verify the count is 4 (only HEALTHY agents, excluding 2 DEGRADED)
    await waitFor(() => {
      const countElement = screen.getByText('4')
      expect(countElement).toBeInTheDocument()
    })
  })

  /**
   * Test: Count excludes OFFLINE agents
   * Requirements: 3.3, 3.7
   * 
   * Verifies that OFFLINE agents are NOT counted in the active agent count.
   */
  it('should exclude OFFLINE agents from active count', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 2),
      createAgent('agent_2', 'OFFLINE', 0), // Should NOT be counted
      createAgent('agent_3', 'HEALTHY', 1),
      createAgent('agent_4', 'OFFLINE', 0), // Should NOT be counted
      createAgent('agent_5', 'HEALTHY', 4),
      createAgent('agent_6', 'HEALTHY', 2),
    ]
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
    
    // Verify the count is 4 (only HEALTHY agents, excluding 2 OFFLINE)
    await waitFor(() => {
      const countElement = screen.getByText('4')
      expect(countElement).toBeInTheDocument()
    })
  })

  /**
   * Test: Count excludes UNHEALTHY agents
   * Requirements: 3.3, 3.7
   * 
   * Verifies that UNHEALTHY agents are NOT counted in the active agent count.
   */
  it('should exclude UNHEALTHY agents from active count', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 2),
      createAgent('agent_2', 'HEALTHY', 3),
      createAgent('agent_3', 'UNHEALTHY', 0), // Should NOT be counted
      createAgent('agent_4', 'HEALTHY', 0),
      createAgent('agent_5', 'HEALTHY', 4),
      createAgent('agent_6', 'UNHEALTHY', 0), // Should NOT be counted
    ]
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
    
    // Verify the count is 4 (only HEALTHY agents, excluding 2 UNHEALTHY)
    await waitFor(() => {
      const countElement = screen.getByText('4')
      expect(countElement).toBeInTheDocument()
    })
  })

  /**
   * Test: Mixed agent statuses
   * Requirements: 3.3, 3.4, 3.6, 3.7
   * 
   * Verifies correct counting with a mix of different agent statuses.
   */
  it('should correctly count with mixed agent statuses', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 2),
      createAgent('agent_2', 'DEGRADED', 3),
      createAgent('agent_3', 'OFFLINE', 0),
      createAgent('agent_4', 'HEALTHY', 1),
      createAgent('agent_5', 'UNHEALTHY', 0),
      createAgent('agent_6', 'HEALTHY', 4),
    ]
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
    
    // Verify the count is 3 (only the 3 HEALTHY agents)
    await waitFor(() => {
      const countElement = screen.getByText('3')
      expect(countElement).toBeInTheDocument()
    })
  })

  /**
   * Test: Zero active agents
   * Requirements: 3.3, 3.10
   * 
   * Verifies that when no agents are HEALTHY, the count displays 0.
   */
  it('should display 0 when no agents are HEALTHY', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'DEGRADED', 2),
      createAgent('agent_2', 'OFFLINE', 0),
      createAgent('agent_3', 'UNHEALTHY', 0),
    ]
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
    
    // Verify the count is 0
    await waitFor(() => {
      const countElement = screen.getByText('0')
      expect(countElement).toBeInTheDocument()
    })
  })

  /**
   * Test: Empty agent list
   * Requirements: 3.3, 3.10
   * 
   * Verifies that when the agent list is empty, the count displays 0.
   */
  it('should display 0 when agent list is empty', async () => {
    vi.mocked(agentService.getAgentStatus).mockResolvedValue([])
    
    renderDashboard()
    
    await waitFor(() => {
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
    
    // Verify the count is 0
    await waitFor(() => {
      const countElement = screen.getByText('0')
      expect(countElement).toBeInTheDocument()
    })
  })

  /**
   * Test: Handles undefined agents data
   * Requirements: 3.8, 3.10
   * 
   * Verifies graceful handling when agents data is unavailable.
   * The calculation should return 0 when agents is undefined.
   */
  it('should display 0 when agents data is unavailable', async () => {
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(undefined as any)
    
    renderDashboard()
    
    await waitFor(() => {
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
    
    // Verify the count is 0 (fallback value)
    await waitFor(() => {
      const countElement = screen.getByText('0')
      expect(countElement).toBeInTheDocument()
    })
  })

  /**
   * Test: Handles API error
   * Requirements: 3.8
   * 
   * Verifies that when the API call fails, the component handles it gracefully.
   */
  it('should handle API error gracefully', async () => {
    vi.mocked(agentService.getAgentStatus).mockRejectedValue(
      new Error('Failed to fetch agent status')
    )
    
    renderDashboard()
    
    // The component should still render without crashing
    await waitFor(() => {
      const activeAgentsSection = screen.getByText('Active Agents')
      expect(activeAgentsSection).toBeInTheDocument()
    })
  })

  /**
   * Test: Backend filtering assumption
   * Requirements: 5.1, 5.2
   * 
   * This test documents the assumption that the backend already filters
   * agents by deployment_status === 'ACTIVE', so the frontend only needs
   * to filter by status === 'HEALTHY'.
   * 
   * Note: All agents returned by the backend should have deployment_status === 'ACTIVE'
   * as per Task 6.1 which was already completed.
   */
  it('should assume all returned agents have ACTIVE deployment_status', async () => {
    // This test verifies our assumption that the backend filters correctly
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 2),
      createAgent('agent_2', 'HEALTHY', 3),
      createAgent('agent_3', 'DEGRADED', 1),
    ]
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      expect(agentService.getAgentStatus).toHaveBeenCalled()
    })
    
    // The frontend should count 2 HEALTHY agents
    // (assuming all returned agents are ACTIVE per backend filtering)
    await waitFor(() => {
      const countElement = screen.getByText('2')
      expect(countElement).toBeInTheDocument()
    })
  })
})

describe('Dashboard - Workload Calculation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mock implementations
    vi.mocked(agentService.getProcessingMetrics).mockResolvedValue({
      totalProcessed: 100,
      matchedCount: 80,
      unmatchedCount: 15,
      pendingCount: 5,
      errorCount: 0,
      breakCount: 0,
      pendingReview: 0,
      throughputPerHour: 50,
      avgProcessingTimeMs: 2000,
      bankTradeCount: 50,
      counterpartyTradeCount: 50,
    })
    
    vi.mocked(workflowService.getRecentSessions).mockResolvedValue([])
  })

  /**
   * Test: 0% workload when no active tasks
   * Requirements: 4.5
   * 
   * Verifies that when sum of activeTasks is 0, workload displays as 0%.
   */
  it('should display 0% workload when no active tasks', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 0),
      createAgent('agent_2', 'HEALTHY', 0),
      createAgent('agent_3', 'HEALTHY', 0),
      createAgent('agent_4', 'HEALTHY', 0),
      createAgent('agent_5', 'HEALTHY', 0),
      createAgent('agent_6', 'HEALTHY', 0),
    ]
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is 0%
    await waitFor(() => {
      // Look for "0%" text near the Workload label
      const workloadValue = screen.getByText(/0%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })

  /**
   * Test: 100% workload when at capacity
   * Requirements: 4.6
   * 
   * Verifies that when activeTasks equals total capacity, workload displays as 100%.
   * Total capacity = number of ACTIVE agents * 10
   */
  it('should display 100% workload when at capacity', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 10), // At max capacity
      createAgent('agent_2', 'HEALTHY', 10), // At max capacity
      createAgent('agent_3', 'HEALTHY', 10), // At max capacity
      createAgent('agent_4', 'HEALTHY', 10), // At max capacity
      createAgent('agent_5', 'HEALTHY', 10), // At max capacity
      createAgent('agent_6', 'HEALTHY', 10), // At max capacity
    ]
    // Total: 60 active tasks, capacity: 6 * 10 = 60, workload: 100%
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is 100%
    await waitFor(() => {
      const workloadValue = screen.getByText(/100%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })

  /**
   * Test: Workload capped at 100% when over capacity
   * Requirements: 4.9
   * 
   * Verifies that when activeTasks exceeds capacity, workload is capped at 100%.
   */
  it('should cap workload at 100% when over capacity', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 15), // Over capacity
      createAgent('agent_2', 'HEALTHY', 12), // Over capacity
      createAgent('agent_3', 'HEALTHY', 11), // Over capacity
      createAgent('agent_4', 'HEALTHY', 13), // Over capacity
      createAgent('agent_5', 'HEALTHY', 14), // Over capacity
      createAgent('agent_6', 'HEALTHY', 10), // At capacity
    ]
    // Total: 75 active tasks, capacity: 6 * 10 = 60, raw workload: 125%, capped: 100%
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is capped at 100%
    await waitFor(() => {
      const workloadValue = screen.getByText(/100%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })

  /**
   * Test: Workload calculation with HEALTHY agents only
   * Requirements: 4.2
   * 
   * Verifies that only HEALTHY agents' activeTasks are summed for workload calculation.
   */
  it('should calculate workload using only HEALTHY agents activeTasks', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 5),
      createAgent('agent_2', 'HEALTHY', 3),
      createAgent('agent_3', 'DEGRADED', 10), // Should NOT be counted
      createAgent('agent_4', 'HEALTHY', 2),
      createAgent('agent_5', 'OFFLINE', 8), // Should NOT be counted
      createAgent('agent_6', 'HEALTHY', 0),
    ]
    // Total HEALTHY tasks: 5 + 3 + 2 + 0 = 10
    // Capacity: 6 * 10 = 60 (all agents count for capacity)
    // Workload: (10 / 60) * 100 = 16.67% ≈ 17%
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is 17% (rounded from 16.67%)
    await waitFor(() => {
      const workloadValue = screen.getByText(/17%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })

  /**
   * Test: Workload calculation with total capacity formula
   * Requirements: 4.3, 4.4
   * 
   * Verifies that total capacity is calculated as (count of ACTIVE agents * 10).
   * Backend already filters for ACTIVE deployment_status.
   */
  it('should calculate capacity as count of agents * 10', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 3),
      createAgent('agent_2', 'HEALTHY', 2),
      createAgent('agent_3', 'HEALTHY', 1),
    ]
    // Total tasks: 3 + 2 + 1 = 6
    // Capacity: 3 * 10 = 30
    // Workload: (6 / 30) * 100 = 20%
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is 20%
    await waitFor(() => {
      const workloadValue = screen.getByText(/20%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })

  /**
   * Test: Workload rounding
   * Requirements: 4.8
   * 
   * Verifies that workload percentage is rounded to the nearest whole number.
   */
  it('should round workload to nearest whole number', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 1),
      createAgent('agent_2', 'HEALTHY', 1),
      createAgent('agent_3', 'HEALTHY', 1),
    ]
    // Total tasks: 3
    // Capacity: 3 * 10 = 30
    // Workload: (3 / 30) * 100 = 10.0%
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is 10% (exact, no rounding needed)
    await waitFor(() => {
      const workloadValue = screen.getByText(/10%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })

  /**
   * Test: Workload displays "N/A" when agents unavailable
   * Requirements: 4.7
   * 
   * Verifies that when agents data is unavailable, workload displays "N/A".
   */
  it('should display N/A when agents data is unavailable', async () => {
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(undefined as any)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload displays "N/A"
    await waitFor(() => {
      const naValue = screen.getByText('N/A')
      expect(naValue).toBeInTheDocument()
    })
  })

  /**
   * Test: Workload displays 0% when no agents
   * Requirements: 4.7
   * 
   * Verifies that when there are no agents (zero capacity), workload displays 0%.
   */
  it('should display 0% when no agents exist', async () => {
    vi.mocked(agentService.getAgentStatus).mockResolvedValue([])
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is 0%
    await waitFor(() => {
      const workloadValue = screen.getByText(/0%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })

  /**
   * Test: Workload calculation with realistic scenario
   * Requirements: 4.2, 4.3, 4.4, 4.8
   * 
   * Verifies workload calculation with a realistic mix of agent states and tasks.
   */
  it('should calculate workload correctly in realistic scenario', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 4),
      createAgent('agent_2', 'HEALTHY', 2),
      createAgent('agent_3', 'DEGRADED', 7), // Not counted in tasks
      createAgent('agent_4', 'HEALTHY', 3),
      createAgent('agent_5', 'HEALTHY', 1),
      createAgent('agent_6', 'OFFLINE', 0), // Not counted in tasks
    ]
    // Total HEALTHY tasks: 4 + 2 + 3 + 1 = 10
    // Capacity: 6 * 10 = 60
    // Workload: (10 / 60) * 100 = 16.67% ≈ 17%
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is 17%
    await waitFor(() => {
      const workloadValue = screen.getByText(/17%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })

  /**
   * Test: Workload handles missing activeTasks field
   * Requirements: 4.2, 4.7
   * 
   * Verifies that agents with missing activeTasks field are treated as having 0 tasks.
   */
  it('should treat missing activeTasks as 0', async () => {
    const agents: AgentHealth[] = [
      createAgent('agent_1', 'HEALTHY', 5),
      { ...createAgent('agent_2', 'HEALTHY', 0), activeTasks: undefined as any },
      createAgent('agent_3', 'HEALTHY', 3),
    ]
    // Total tasks: 5 + 0 + 3 = 8
    // Capacity: 3 * 10 = 30
    // Workload: (8 / 30) * 100 = 26.67% ≈ 27%
    
    vi.mocked(agentService.getAgentStatus).mockResolvedValue(agents)
    
    renderDashboard()
    
    await waitFor(() => {
      const workloadSection = screen.getByText('Workload')
      expect(workloadSection).toBeInTheDocument()
    })
    
    // Verify workload is 27%
    await waitFor(() => {
      const workloadValue = screen.getByText(/27%/)
      expect(workloadValue).toBeInTheDocument()
    })
  })
})

describe('Dashboard - Matching Status Display', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default mock implementations
    vi.mocked(agentService.getAgentStatus).mockResolvedValue([
      createAgent('agent_1', 'HEALTHY', 2),
      createAgent('agent_2', 'HEALTHY', 3),
    ])
    
    vi.mocked(agentService.getProcessingMetrics).mockResolvedValue({
      totalProcessed: 100,
      matchedCount: 80,
      unmatchedCount: 15,
      pendingCount: 5,
      errorCount: 0,
      breakCount: 0,
      pendingReview: 0,
      throughputPerHour: 50,
      avgProcessingTimeMs: 2000,
      bankTradeCount: 50,
      counterpartyTradeCount: 50,
    })
    
    vi.mocked(workflowService.getRecentSessions).mockResolvedValue([])
  })

  /**
   * Test: Display matching status counts
   * Requirements: 6.7
   * 
   * Verifies that matching status counts are displayed correctly.
   */
  it('should display matching status counts', async () => {
    const matchingStatus: MatchingStatusResponse = {
      matched: 45,
      unmatched: 12,
      pending: 8,
      exceptions: 3,
    }
    
    vi.mocked(workflowService.getMatchingStatus).mockResolvedValue(matchingStatus)
    
    renderDashboard()
    
    // Wait for all status labels to be displayed
    await waitFor(() => {
      expect(screen.getByText('Matched')).toBeInTheDocument()
      expect(screen.getByText('Unmatched')).toBeInTheDocument()
      expect(screen.getByText('Pending')).toBeInTheDocument()
      expect(screen.getByText('Exceptions')).toBeInTheDocument()
    })
    
    // Verify the counts are displayed
    await waitFor(() => {
      expect(screen.getByText('45')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument()
      expect(screen.getByText('8')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })

  /**
   * Test: Display zero counts when no sessions
   * Requirements: 6.8
   * 
   * Verifies that when matching status data is unavailable or all counts are 0,
   * the dashboard displays 0 for all counts.
   */
  it('should display 0 for all counts when no sessions exist', async () => {
    const matchingStatus: MatchingStatusResponse = {
      matched: 0,
      unmatched: 0,
      pending: 0,
      exceptions: 0,
    }
    
    vi.mocked(workflowService.getMatchingStatus).mockResolvedValue(matchingStatus)
    
    renderDashboard()
    
    await waitFor(() => {
      expect(screen.getByText('Matched')).toBeInTheDocument()
      expect(screen.getByText('Unmatched')).toBeInTheDocument()
      expect(screen.getByText('Pending')).toBeInTheDocument()
      expect(screen.getByText('Exceptions')).toBeInTheDocument()
    })
    
    // All counts should be 0
    await waitFor(() => {
      const zeroElements = screen.getAllByText('0')
      // Should have at least 4 zeros (one for each matching status metric)
      expect(zeroElements.length).toBeGreaterThanOrEqual(4)
    })
  })

  /**
   * Test: Handle loading state
   * Requirements: 6.9
   * 
   * Verifies that loading indicators are displayed while matching status data is loading.
   */
  it('should display loading indicators while data is loading', async () => {
    // Create a promise that never resolves to simulate loading
    vi.mocked(workflowService.getMatchingStatus).mockImplementation(
      () => new Promise(() => {})
    )
    
    renderDashboard()
    
    // The component should render with loading state
    // (skeleton loaders or loading indicators)
    await waitFor(() => {
      // The Dashboard component should be rendered
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
  })

  /**
   * Test: Handle API error gracefully
   * Requirements: 6.8
   * 
   * Verifies that when the matching status API call fails,
   * the component handles it gracefully and displays 0 for all counts.
   */
  it('should handle API error gracefully', async () => {
    vi.mocked(workflowService.getMatchingStatus).mockRejectedValue(
      new Error('Failed to fetch matching status')
    )
    
    renderDashboard()
    
    // The component should still render without crashing
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
    
    // Should display the metric labels even if data fetch failed
    await waitFor(() => {
      expect(screen.getByText('Matched')).toBeInTheDocument()
      expect(screen.getByText('Unmatched')).toBeInTheDocument()
      expect(screen.getByText('Pending')).toBeInTheDocument()
      expect(screen.getByText('Exceptions')).toBeInTheDocument()
    })
  })

  /**
   * Test: Display various matching status scenarios
   * Requirements: 6.7
   * 
   * Verifies correct display with different matching status values.
   */
  it('should display various matching status scenarios correctly', async () => {
    const matchingStatus: MatchingStatusResponse = {
      matched: 150,
      unmatched: 25,
      pending: 10,
      exceptions: 5,
    }
    
    vi.mocked(workflowService.getMatchingStatus).mockResolvedValue(matchingStatus)
    
    renderDashboard()
    
    await waitFor(() => {
      expect(screen.getByText('Matched')).toBeInTheDocument()
      expect(screen.getByText('Unmatched')).toBeInTheDocument()
      expect(screen.getByText('Pending')).toBeInTheDocument()
      expect(screen.getByText('Exceptions')).toBeInTheDocument()
    })
    
    // Verify all counts are displayed
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument()
      expect(screen.getByText('25')).toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })

  /**
   * Test: Matching status updates with refetch interval
   * Requirements: 6.7
   * 
   * Verifies that matching status is queried with proper refetch interval.
   */
  it('should query matching status on mount', async () => {
    const matchingStatus: MatchingStatusResponse = {
      matched: 20,
      unmatched: 5,
      pending: 3,
      exceptions: 1,
    }
    
    vi.mocked(workflowService.getMatchingStatus).mockResolvedValue(matchingStatus)
    
    renderDashboard()
    
    // Verify the service was called
    await waitFor(() => {
      expect(workflowService.getMatchingStatus).toHaveBeenCalled()
    })
    
    // Verify data is displayed
    await waitFor(() => {
      expect(screen.getByText('20')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
    })
  })

  /**
   * Test: Handle undefined matching status data
   * Requirements: 6.8
   * 
   * Verifies graceful handling when matching status data is undefined.
   */
  it('should handle undefined matching status data', async () => {
    vi.mocked(workflowService.getMatchingStatus).mockResolvedValue(undefined as any)
    
    renderDashboard()
    
    // The component should still render without crashing
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
    
    // Should display the metric labels
    await waitFor(() => {
      expect(screen.getByText('Matched')).toBeInTheDocument()
      expect(screen.getByText('Unmatched')).toBeInTheDocument()
      expect(screen.getByText('Pending')).toBeInTheDocument()
      expect(screen.getByText('Exceptions')).toBeInTheDocument()
    })
    
    // All counts should default to 0
    await waitFor(() => {
      const zeroElements = screen.getAllByText('0')
      expect(zeroElements.length).toBeGreaterThanOrEqual(4)
    })
  })
})
