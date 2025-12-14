import {
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Box,
  LinearProgress,
  Avatar,
  Stack,
  Divider,
} from '@mui/material'
import {
  CheckCircle as HealthyIcon,
  Warning as DegradedIcon,
  Error as UnhealthyIcon,
  PowerOff as OfflineIcon,
  Speed as LatencyIcon,
  TrendingUp as ThroughputIcon,
  Token as TokenIcon,
  Assignment as TaskIcon,
} from '@mui/icons-material'
import LiveIndicator from '../common/LiveIndicator'
import type { AgentHealth, AgentStatus } from '../../types'

interface AgentHealthPanelProps {
  agents: AgentHealth[]
}

const statusConfig: Record<AgentStatus, { 
  color: 'success' | 'warning' | 'error' | 'default'
  icon: JSX.Element
  bgColor: string
  textColor: string
}> = {
  HEALTHY: { 
    color: 'success', 
    icon: <HealthyIcon />, 
    bgColor: '#1D8102',
    textColor: '#FFFFFF'
  },
  DEGRADED: { 
    color: 'warning', 
    icon: <DegradedIcon />, 
    bgColor: '#FF9900',
    textColor: '#FFFFFF'
  },
  UNHEALTHY: { 
    color: 'error', 
    icon: <UnhealthyIcon />, 
    bgColor: '#D13212',
    textColor: '#FFFFFF'
  },
  OFFLINE: { 
    color: 'default', 
    icon: <OfflineIcon />, 
    bgColor: '#687078',
    textColor: '#FFFFFF'
  },
}

export default function AgentHealthPanel({ agents }: AgentHealthPanelProps) {
  return (
    <Card sx={{ 
      background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(65, 77, 92, 0.3)',
    }}>
      <CardContent sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" mb={3}>
          <Avatar sx={{ 
            bgcolor: 'primary.main', 
            mr: 2,
            width: 40,
            height: 40
          }}>
            <HealthyIcon />
          </Avatar>
          <Typography variant="h5" fontWeight={600} color="text.primary">
            Agent Health Status
          </Typography>
        </Box>
        
        <Grid container spacing={3}>
          {agents.map((agent, index) => {
            const config = statusConfig[agent.status]
            return (
              <Grid item xs={12} sm={6} md={4} lg={2.4} key={agent.agentId}>
                <Card sx={{
                  background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.8) 0%, rgba(35, 42, 49, 0.8) 100%)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(65, 77, 92, 0.2)',
                  transition: 'all 0.3s ease-in-out',
                  animation: `slideInUp 0.6s ease-out ${index * 0.1}s both`,
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 8px 25px rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 153, 0, 0.3)',
                  },
                  '@keyframes slideInUp': {
                    '0%': {
                      opacity: 0,
                      transform: 'translateY(30px)',
                    },
                    '100%': {
                      opacity: 1,
                      transform: 'translateY(0)',
                    },
                  },
                }}>
                  <CardContent sx={{ p: 2.5 }}>
                    {/* Agent Header */}
                    <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                      <Typography variant="h6" fontWeight={600} noWrap color="text.primary">
                        {agent.agentName}
                      </Typography>
                      <LiveIndicator status={agent.status} size="small" />
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
                            backgroundColor: agent.metrics.successRate > 0.95 
                              ? '#1D8102' 
                              : agent.metrics.successRate > 0.85 
                                ? '#FF9900' 
                                : '#D13212',
                            borderRadius: 3,
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
                            backgroundColor: agent.metrics.errorRate > 0.05 ? '#D13212' : '#1D8102',
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
                </Card>
              </Grid>
            )
          })}
        </Grid>
        
        {agents.length === 0 && (
          <Box 
            display="flex" 
            flexDirection="column" 
            alignItems="center" 
            justifyContent="center" 
            py={6}
            sx={{
              background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.5) 0%, rgba(35, 42, 49, 0.5) 100%)',
              borderRadius: 2,
              border: '1px dashed rgba(65, 77, 92, 0.3)',
            }}
          >
            <OfflineIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" align="center">
              No agents registered
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center" mt={1}>
              Agents will appear here once they register with the system
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}
