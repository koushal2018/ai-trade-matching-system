import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  Divider,
  Chip,
} from '@mui/material'
import {
  Speed as LatencyIcon,
  TrendingUp as ThroughputIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Token as TokenIcon,
  Loop as CycleIcon,
  Build as ToolIcon,
} from '@mui/icons-material'
import type { AgentHealth } from '../../types'

interface AgentMetricsDetailProps {
  agent: AgentHealth
}

interface MetricCardProps {
  title: string
  value: string | number
  icon: JSX.Element
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error'
  subtitle?: string
}

function MetricCard({ title, value, icon, color = 'primary', subtitle }: MetricCardProps) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={1}>
          <Box color={`${color}.main`} mr={1}>
            {icon}
          </Box>
          <Typography variant="subtitle2" color="text.secondary">
            {title}
          </Typography>
        </Box>
        <Typography variant="h6" component="div">
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

export default function AgentMetricsDetail({ agent }: AgentMetricsDetailProps) {
  const { metrics } = agent

  // Calculate derived metrics
  const avgTokensPerCycle = metrics.cycleCount > 0 ? Math.round(metrics.totalTokens / metrics.cycleCount) : 0
  const toolCallsPerCycle = metrics.cycleCount > 0 ? (metrics.toolCallCount / metrics.cycleCount).toFixed(1) : '0'
  const tokenEfficiency = metrics.totalTokens > 0 ? (metrics.outputTokens / metrics.totalTokens * 100).toFixed(1) : '0'

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6">
            {agent.agentName} - Detailed Metrics
          </Typography>
          <Chip
            label={agent.status}
            color={
              agent.status === 'HEALTHY' ? 'success' :
              agent.status === 'DEGRADED' ? 'warning' :
              agent.status === 'OFFLINE' ? 'default' : 'error'
            }
            size="small"
          />
        </Box>

        <Grid container spacing={2}>
          {/* Performance Metrics */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Performance Metrics
            </Typography>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Latency"
              value={`${metrics.latencyMs}ms`}
              icon={<LatencyIcon />}
              color={metrics.latencyMs > 10000 ? 'error' : metrics.latencyMs > 5000 ? 'warning' : 'success'}
              subtitle="Avg response time"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Throughput"
              value={`${metrics.throughput}/hr`}
              icon={<ThroughputIcon />}
              color="primary"
              subtitle="Trades processed"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Success Rate"
              value={`${(metrics.successRate * 100).toFixed(1)}%`}
              icon={<SuccessIcon />}
              color={metrics.successRate > 0.95 ? 'success' : metrics.successRate > 0.85 ? 'warning' : 'error'}
              subtitle="Successful completions"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Error Rate"
              value={`${(metrics.errorRate * 100).toFixed(2)}%`}
              icon={<ErrorIcon />}
              color={metrics.errorRate > 0.05 ? 'error' : metrics.errorRate > 0.02 ? 'warning' : 'success'}
              subtitle="Failed operations"
            />
          </Grid>

          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom>
              Strands Agent Metrics
            </Typography>
          </Grid>

          {/* Token Usage */}
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Tokens"
              value={metrics.totalTokens.toLocaleString()}
              icon={<TokenIcon />}
              color="secondary"
              subtitle={`${metrics.inputTokens.toLocaleString()} in / ${metrics.outputTokens.toLocaleString()} out`}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Avg Cycles"
              value={metrics.cycleCount}
              icon={<CycleIcon />}
              color="secondary"
              subtitle={`${avgTokensPerCycle} tokens/cycle`}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Tool Calls"
              value={metrics.toolCallCount}
              icon={<ToolIcon />}
              color="secondary"
              subtitle={`${toolCallsPerCycle} calls/cycle`}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Token Efficiency"
              value={`${tokenEfficiency}%`}
              icon={<TokenIcon />}
              color={parseFloat(tokenEfficiency) > 25 ? 'success' : parseFloat(tokenEfficiency) > 15 ? 'warning' : 'error'}
              subtitle="Output/Total ratio"
            />
          </Grid>

          {/* Current Status */}
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom>
              Current Status
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Active Tasks
                </Typography>
                <Typography variant="h4" component="div" color={agent.activeTasks > 5 ? 'warning.main' : 'text.primary'}>
                  {agent.activeTasks}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Currently processing
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Last Heartbeat
                </Typography>
                <Typography variant="body2" component="div">
                  {agent.lastHeartbeat ? new Date(agent.lastHeartbeat).toLocaleString() : 'Never'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Health check timestamp
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  )
}