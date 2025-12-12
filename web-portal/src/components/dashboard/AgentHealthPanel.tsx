import {
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Box,
  LinearProgress,
} from '@mui/material'
import {
  CheckCircle as HealthyIcon,
  Warning as DegradedIcon,
  Error as UnhealthyIcon,
  PowerOff as OfflineIcon,
} from '@mui/icons-material'
import type { AgentHealth, AgentStatus } from '../../types'

interface AgentHealthPanelProps {
  agents: AgentHealth[]
}

const statusConfig: Record<AgentStatus, { color: 'success' | 'warning' | 'error' | 'default'; icon: JSX.Element }> = {
  HEALTHY: { color: 'success', icon: <HealthyIcon /> },
  DEGRADED: { color: 'warning', icon: <DegradedIcon /> },
  UNHEALTHY: { color: 'error', icon: <UnhealthyIcon /> },
  OFFLINE: { color: 'default', icon: <OfflineIcon /> },
}

export default function AgentHealthPanel({ agents }: AgentHealthPanelProps) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Agent Health Status
        </Typography>
        <Grid container spacing={2}>
          {agents.map((agent) => {
            const config = statusConfig[agent.status]
            return (
              <Grid item xs={12} sm={6} md={4} lg={2.4} key={agent.agentId}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                      <Typography variant="subtitle2" noWrap>
                        {agent.agentName}
                      </Typography>
                      <Chip
                        size="small"
                        label={agent.status}
                        color={config.color}
                        icon={config.icon}
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Latency: {agent.metrics.latencyMs}ms
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Throughput: {agent.metrics.throughput}/hr
                    </Typography>

                    <Box mt={1}>
                      <Typography variant="caption" color="text.secondary">
                        Error Rate: {(agent.metrics.errorRate * 100).toFixed(1)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(agent.metrics.errorRate * 100, 100)}
                        color={agent.metrics.errorRate > 0.05 ? 'error' : 'success'}
                        sx={{ mt: 0.5 }}
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                      Active Tasks: {agent.activeTasks}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )
          })}
        </Grid>
        {agents.length === 0 && (
          <Typography color="text.secondary" align="center" py={4}>
            No agents registered
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
