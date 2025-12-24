import { useEffect } from 'react'
import { ContentLayout, Header, Container, SpaceBetween, Box, Alert } from '@cloudscape-design/components'
import { useQuery } from '@tanstack/react-query'
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
    <ContentLayout
      header={
        <Header
          variant="h1"
          description="Real-time overview of trade confirmation matching"
        >
          Dashboard
        </Header>
      }
    >
      <SpaceBetween size="l">
        <Alert type="info" header="Dashboard Under Construction">
          The dashboard is being migrated to CloudScape Design System. Full functionality coming soon.
        </Alert>
        
        <Container header={<Header variant="h2">Quick Stats</Header>}>
          <SpaceBetween size="m">
            <Box>Total Trades: {totalTrades}</Box>
            <Box>Match Rate: {(matchRate * 100).toFixed(1)}%</Box>
            <Box>Avg Latency: {Math.round(avgLatency)}ms</Box>
            <Box>Active Agents: {activeAgents}</Box>
          </SpaceBetween>
        </Container>
      </SpaceBetween>
    </ContentLayout>
  )
}
