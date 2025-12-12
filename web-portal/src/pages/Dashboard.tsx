import { useEffect } from 'react'
import { Grid, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
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


  return (
    <>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <AgentHealthPanel agents={agents || []} />
        </Grid>
        <Grid item xs={12} md={6}>
          <ProcessingMetricsPanel metrics={metrics} />
        </Grid>
        <Grid item xs={12} md={6}>
          <MatchingResultsPanel results={matchingResults || []} />
        </Grid>
      </Grid>
    </>
  )
}
