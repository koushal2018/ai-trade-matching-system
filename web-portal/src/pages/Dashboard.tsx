import { useEffect } from 'react'
import { Box, Typography, Container as MuiContainer } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { agentService } from '../services/agentService'
import { hitlService } from '../services/hitlService'
import { wsService } from '../services/websocket'
import HeroMetrics from '../components/dashboard/HeroMetrics'
import AgentHealthPanel from '../components/dashboard/AgentHealthPanel'
import MatchingResultsPanel from '../components/dashboard/MatchingResultsPanel'
import type { AgentHealth, ProcessingMetrics, WebSocketMessage, MatchResult } from '../types'

export default function Dashboard() {
  const { data: agents, refetch: refetchAgents, isLoading: agentsLoading } = useQuery<AgentHealth[]>({
    queryKey: ['agentStatus'],
    queryFn: agentService.getAgentStatus,
    refetchInterval: 30000,
  })

  const { data: metrics, refetch: refetchMetrics, isLoading: metricsLoading } = useQuery<ProcessingMetrics>({
    queryKey: ['processingMetrics'],
    queryFn: agentService.getProcessingMetrics,
    refetchInterval: 10000,
  })

  const { data: matchingResults, isLoading: resultsLoading } = useQuery<MatchResult[]>({
    queryKey: ['matchingResults'],
    queryFn: () => hitlService.getMatchingResults(),
    refetchInterval: 15000,
  })

  useEffect(() => {
    wsService.connect()

    const unsubStatus = wsService.subscribe('AGENT_STATUS', (_msg: WebSocketMessage) => {
      refetchAgents()
    })

    const unsubMetrics = wsService.subscribe('METRICS_UPDATE', (_msg: WebSocketMessage) => {
      refetchMetrics()
    })

    return () => {
      unsubStatus()
      unsubMetrics()
    }
  }, [refetchAgents, refetchMetrics])

  // Calculate hero metrics
  const totalTrades = metrics?.totalProcessed || 0
  const matchRate = totalTrades > 0 ? (metrics?.matchedCount || 0) / totalTrades : 0
  const avgLatency = agents && agents.length > 0
    ? agents.reduce((sum, agent) => sum + (agent.metrics.latencyMs || 0), 0) / agents.length
    : 0
  const activeAgents = agents?.filter(agent =>
    agent.status === 'HEALTHY' || agent.status === 'DEGRADED'
  ).length || 0

  const isLoading = agentsLoading || metricsLoading || resultsLoading

  return (
    <MuiContainer maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box mb={4}>
        <Typography
          variant="h3"
          fontWeight={700}
          color="text.primary"
          sx={{
            fontFamily: '"Amazon Ember", "Helvetica Neue", Helvetica, Arial, sans-serif',
            mb: 1
          }}
        >
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time overview of trade confirmation matching
        </Typography>
      </Box>

      {/* Hero Metrics */}
      <HeroMetrics
        totalTrades={totalTrades}
        matchRate={matchRate}
        avgLatency={avgLatency}
        activeAgents={activeAgents}
      />

      {/* Agent Health Panel */}
      <Box mb={4}>
        <AgentHealthPanel agents={agents || []} />
      </Box>

      {/* Matching Results Panel */}
      <Box mb={4}>
        <MatchingResultsPanel results={matchingResults || []} />
      </Box>
    </MuiContainer>
  )
}
