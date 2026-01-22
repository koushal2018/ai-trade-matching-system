import { useEffect } from 'react'
import { Box, Typography, Container as MuiContainer, Chip } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp as TrendingIcon } from '@mui/icons-material'
import { agentService } from '../services/agentService'
import { hitlService } from '../services/hitlService'
import { wsService } from '../services/websocket'
import HeroMetrics from '../components/dashboard/HeroMetrics'
import AgentHealthPanel from '../components/dashboard/AgentHealthPanel'
import MatchingResultsPanel from '../components/dashboard/MatchingResultsPanel'
import GlassCard from '../components/common/GlassCard'
import { SkeletonGroup } from '../components/common/SkeletonLoader'
import { fsiColors } from '../theme'
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
      {/* Page Header with FSI Styling */}
      <Box
        sx={{
          mb: 5,
          animation: 'fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          '@keyframes fadeIn': {
            '0%': { opacity: 0, transform: 'translateY(-16px)' },
            '100%': { opacity: 1, transform: 'translateY(0)' },
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <Typography
            variant="overline"
            sx={{
              color: fsiColors.orange.main,
              letterSpacing: '0.15em',
              fontWeight: 600,
            }}
          >
            AWS FSI TRADE MATCHING
          </Typography>
          <Chip
            icon={<TrendingIcon sx={{ fontSize: 14 }} />}
            label="Live"
            size="small"
            sx={{
              height: 22,
              fontSize: '0.7rem',
              fontWeight: 600,
              bgcolor: `${fsiColors.status.success}20`,
              color: fsiColors.status.success,
              border: `1px solid ${fsiColors.status.success}40`,
              '& .MuiChip-icon': {
                color: fsiColors.status.success,
              },
            }}
          />
        </Box>
        <Typography
          variant="h3"
          fontWeight={700}
          sx={{
            mb: 1.5,
            color: fsiColors.text.primary,
            letterSpacing: '-0.02em',
          }}
        >
          Dashboard
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: fsiColors.text.secondary,
            maxWidth: 600,
          }}
        >
          Real-time overview of trade confirmation matching powered by AI agents
        </Typography>
      </Box>

      {/* Hero Metrics */}
      {isLoading && !metrics ? (
        <Box sx={{ mb: 4 }}>
          <SkeletonGroup variant="metric-cards" count={4} />
        </Box>
      ) : (
        <HeroMetrics
          totalTrades={totalTrades}
          matchRate={matchRate}
          avgLatency={avgLatency}
          activeAgents={activeAgents}
          isLoading={isLoading}
        />
      )}

      {/* Agent Health Panel */}
      <GlassCard
        variant="default"
        hoverEffect="none"
        animateIn
        animationDelay={0.2}
        sx={{ mb: 4, p: 0, overflow: 'hidden' }}
      >
        {agentsLoading && !agents ? (
          <Box sx={{ p: 3 }}>
            <SkeletonGroup variant="metric-cards" count={5} />
          </Box>
        ) : (
          <AgentHealthPanel agents={agents || []} />
        )}
      </GlassCard>

      {/* Matching Results Panel */}
      <GlassCard
        variant="default"
        hoverEffect="none"
        animateIn
        animationDelay={0.3}
        sx={{ mb: 4, p: 0, overflow: 'hidden' }}
      >
        {resultsLoading && !matchingResults ? (
          <Box sx={{ p: 3 }}>
            <SkeletonGroup variant="table" count={5} />
          </Box>
        ) : (
          <MatchingResultsPanel results={matchingResults || []} />
        )}
      </GlassCard>
    </MuiContainer>
  )
}
