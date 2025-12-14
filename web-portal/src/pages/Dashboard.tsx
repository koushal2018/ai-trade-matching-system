import { useEffect } from 'react'
import { Grid, Typography, Box } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import HeroMetrics from '../components/dashboard/HeroMetrics'
import AgentHealthPanel from '../components/dashboard/AgentHealthPanel'
import ProcessingMetricsPanel from '../components/dashboard/ProcessingMetricsPanel'
import MatchingResultsPanel from '../components/dashboard/MatchingResultsPanel'
import { agentService } from '../services/agentService'
import { hitlService } from '../services/hitlService'
import { wsService } from '../services/websocket'
import type { AgentHealth, ProcessingMetrics, WebSocketMessage } from '../types'

export default function Dashboard() {
  const { data: agents, refetch: refetchAgents } = useQuery<AgentHealth[]>({
    queryKey: ['agentStatus'],
    queryFn: agentService.getAgentStatus,
    refetchInterval: 30000,
  })

  const { data: metrics, refetch: refetchMetrics } = useQuery<ProcessingMetrics>({
    queryKey: ['processingMetrics'],
    queryFn: agentService.getProcessingMetrics,
    refetchInterval: 10000,
  })

  const { data: matchingResults } = useQuery({
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
  const activeAgents = agents?.filter(agent => agent.status === 'HEALTHY').length || 0

  return (
    <Box
      sx={{
        animation: 'fadeIn 0.6s ease-out',
        '@keyframes fadeIn': {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      }}
    >
      <Typography 
        variant="h4" 
        gutterBottom 
        sx={{ 
          fontWeight: 700,
          background: 'linear-gradient(135deg, #FF9900 0%, #146EB4 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          mb: 4
        }}
      >
        Dashboard
      </Typography>

      {/* Hero Metrics */}
      <HeroMetrics
        totalTrades={totalTrades}
        matchRate={matchRate}
        avgLatency={Math.round(avgLatency)}
        activeAgents={activeAgents}
      />

      {/* Main Content */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <AgentHealthPanel agents={agents || []} />
        </Grid>
        <Grid item xs={12} md={6}>
          <ProcessingMetricsPanel metrics={metrics} />
        </Grid>
        <Grid item xs={12}>
          <MatchingResultsPanel results={matchingResults || []} />
        </Grid>
      </Grid>
    </Box>
  )
}
