import {
  CardContent,
  Typography,
  Grid,
  Box,
  LinearProgress,
  Avatar,
  Stack,
  Divider,
} from '@mui/material'
import {
  CheckCircle as HealthyIcon,
  PowerOff as OfflineIcon,
  Speed as LatencyIcon,
  TrendingUp as ThroughputIcon,
  Token as TokenIcon,
  Assignment as TaskIcon,
} from '@mui/icons-material'
import GlassCard from '../common/GlassCard'
import StatusPulse, { mapLegacyStatus } from '../common/StatusPulse'
import type { AgentHealth } from '../../types'
import { glowColors } from '../../theme'

interface AgentHealthPanelProps {
  agents: AgentHealth[]
}

export default function AgentHealthPanel({ agents }: AgentHealthPanelProps) {
  return (
    <CardContent sx={{ p: 3 }}>
      <Box display="flex" alignItems="center" mb={3}>
        <Avatar sx={{
          bgcolor: 'rgba(255, 153, 0, 0.15)',
          color: glowColors.primary,
          mr: 2,
          width: 40,
          height: 40,
          border: `2px solid ${glowColors.primary}30`,
        }}>
          <HealthyIcon />
        </Avatar>
        <Typography variant="h5" fontWeight={600} color="text.primary">
          Agent Health Status
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {agents.map((agent, index) => {
          const statusType = mapLegacyStatus(agent.status)
          const statusColor = statusType === 'healthy' ? glowColors.success :
                             statusType === 'degraded' ? glowColors.warning :
                             statusType === 'unhealthy' ? glowColors.error :
                             glowColors.neutral

          return (
            <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2.4 }} key={agent.agentId}>
              <GlassCard
                variant="subtle"
                glowColor={statusColor}
                hoverEffect="all"
                animateIn
                animationDelay={index * 0.1}
                borderRadius={12}
              >
                <CardContent sx={{ p: 2.5 }}>
                  {/* Agent Header */}
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Typography variant="h6" fontWeight={600} noWrap color="text.primary" sx={{ flex: 1 }}>
                      {agent.agentName}
                    </Typography>
                    <StatusPulse
                      status={statusType}
                      size="small"
                      variant="badge"
                      showLabel={false}
                    />
                  </Box>

                  <Divider sx={{ mb: 2, borderColor: 'rgba(65, 77, 92, 0.3)' }} />

                  {/* Key Metrics */}
                  <Stack spacing={1.5}>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center">
                        <LatencyIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          Latency
                        </Typography>
                      </Box>
                      <Typography variant="body2" fontWeight={600} color="text.primary">
                        {agent.metrics.latencyMs}ms
                      </Typography>
                    </Box>

                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center">
                        <ThroughputIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          Throughput
                        </Typography>
                      </Box>
                      <Typography variant="body2" fontWeight={600} color="text.primary">
                        {agent.metrics.throughput}/hr
                      </Typography>
                    </Box>

                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center">
                        <TaskIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          Active Tasks
                        </Typography>
                      </Box>
                      <Typography variant="body2" fontWeight={600} color="text.primary">
                        {agent.activeTasks}
                      </Typography>
                    </Box>
                  </Stack>

                  <Divider sx={{ my: 2, borderColor: 'rgba(65, 77, 92, 0.3)' }} />

                  {/* Success Rate */}
                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Typography variant="body2" color="text.secondary">
                        Success Rate
                      </Typography>
                      <Typography variant="body2" fontWeight={600} color="text.primary">
                        {(agent.metrics.successRate * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={agent.metrics.successRate * 100}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(65, 77, 92, 0.3)',
                        '& .MuiLinearProgress-bar': {
                          background: agent.metrics.successRate > 0.95
                            ? `linear-gradient(90deg, ${glowColors.success} 0%, ${glowColors.success}80 100%)`
                            : agent.metrics.successRate > 0.85
                              ? `linear-gradient(90deg, ${glowColors.warning} 0%, ${glowColors.warning}80 100%)`
                              : `linear-gradient(90deg, ${glowColors.error} 0%, ${glowColors.error}80 100%)`,
                          borderRadius: 3,
                          boxShadow: agent.metrics.successRate > 0.95
                            ? `0 0 8px ${glowColors.success}50`
                            : agent.metrics.successRate > 0.85
                              ? `0 0 8px ${glowColors.warning}50`
                              : `0 0 8px ${glowColors.error}50`,
                        }
                      }}
                    />
                  </Box>

                  {/* Error Rate */}
                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Typography variant="body2" color="text.secondary">
                        Error Rate
                      </Typography>
                      <Typography variant="body2" fontWeight={600} color="text.primary">
                        {(agent.metrics.errorRate * 100).toFixed(2)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(agent.metrics.errorRate * 100, 100)}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'rgba(65, 77, 92, 0.3)',
                        '& .MuiLinearProgress-bar': {
                          background: agent.metrics.errorRate > 0.05
                            ? `linear-gradient(90deg, ${glowColors.error} 0%, ${glowColors.error}80 100%)`
                            : `linear-gradient(90deg, ${glowColors.success} 0%, ${glowColors.success}80 100%)`,
                          borderRadius: 3,
                        }
                      }}
                    />
                  </Box>

                  {/* Token Usage */}
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box display="flex" alignItems="center">
                      <TokenIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        Tokens
                      </Typography>
                    </Box>
                    <Typography variant="caption" fontWeight={600} color="text.primary">
                      {agent.metrics.totalTokens.toLocaleString()} ({agent.metrics.cycleCount} cycles)
                    </Typography>
                  </Box>
                </CardContent>
              </GlassCard>
            </Grid>
          )
        })}
      </Grid>

      {agents.length === 0 && (
        <GlassCard
          variant="inset"
          hoverEffect="none"
          animateIn
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            py: 6,
          }}
        >
          <OfflineIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" align="center">
            No agents registered
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center" mt={1}>
            Agents will appear here once they register with the system
          </Typography>
        </GlassCard>
      )}
    </CardContent>
  )
}
