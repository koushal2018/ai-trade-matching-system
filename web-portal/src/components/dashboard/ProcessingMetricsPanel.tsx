import { Card, CardContent, Typography, Box, Grid, Avatar, Stack, Divider } from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import {
  Analytics as MetricsIcon,
  Speed as SpeedIcon,
  Timer as TimerIcon,
} from '@mui/icons-material'
import type { ProcessingMetrics } from '../../types'

interface ProcessingMetricsPanelProps {
  metrics?: ProcessingMetrics
}

export default function ProcessingMetricsPanel({ metrics }: ProcessingMetricsPanelProps) {
  const chartData = metrics
    ? [
        { name: 'Matched', value: metrics.matchedCount, fill: '#1D8102' },
        { name: 'Breaks', value: metrics.breakCount, fill: '#D13212' },
        { name: 'Pending', value: metrics.pendingReview, fill: '#FF9900' },
      ]
    : []

  return (
    <Card sx={{ 
      height: '100%',
      background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(65, 77, 92, 0.3)',
    }}>
      <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box display="flex" alignItems="center" mb={3}>
          <Avatar sx={{ 
            bgcolor: 'primary.main', 
            mr: 2,
            width: 40,
            height: 40
          }}>
            <MetricsIcon />
          </Avatar>
          <Typography variant="h5" fontWeight={600} color="text.primary">
            Processing Metrics
          </Typography>
        </Box>

        {metrics ? (
          <>
            {/* Key Metrics Grid */}
            <Grid container spacing={3} mb={3}>
              <Grid item xs={12} sm={4}>
                <Box 
                  textAlign="center" 
                  sx={{
                    p: 2,
                    background: 'linear-gradient(135deg, rgba(255, 153, 0, 0.1) 0%, rgba(255, 153, 0, 0.05) 100%)',
                    borderRadius: 2,
                    border: '1px solid rgba(255, 153, 0, 0.2)',
                  }}
                >
                  <Typography variant="h3" fontWeight={700} color="primary.main">
                    {metrics.totalProcessed.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight={500}>
                    Total Processed
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box 
                  textAlign="center"
                  sx={{
                    p: 2,
                    background: 'linear-gradient(135deg, rgba(20, 110, 180, 0.1) 0%, rgba(20, 110, 180, 0.05) 100%)',
                    borderRadius: 2,
                    border: '1px solid rgba(20, 110, 180, 0.2)',
                  }}
                >
                  <Typography variant="h3" fontWeight={700} color="secondary.main">
                    {metrics.throughputPerHour}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight={500}>
                    Trades/Hour
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box 
                  textAlign="center"
                  sx={{
                    p: 2,
                    background: 'linear-gradient(135deg, rgba(155, 167, 180, 0.1) 0%, rgba(155, 167, 180, 0.05) 100%)',
                    borderRadius: 2,
                    border: '1px solid rgba(155, 167, 180, 0.2)',
                  }}
                >
                  <Box display="flex" alignItems="center" justifyContent="center" mb={1}>
                    <TimerIcon sx={{ fontSize: 20, mr: 1, color: 'text.secondary' }} />
                    <Typography variant="h4" fontWeight={700} color="text.primary">
                      {(metrics.avgProcessingTimeMs / 1000).toFixed(1)}s
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" fontWeight={500}>
                    Avg Processing Time
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            <Divider sx={{ mb: 3, borderColor: 'rgba(65, 77, 92, 0.3)' }} />

            {/* Chart Section */}
            <Box flexGrow={1} minHeight={200}>
              <Typography variant="h6" fontWeight={600} color="text.primary" mb={2}>
                Trade Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid 
                    strokeDasharray="3 3" 
                    stroke="rgba(65, 77, 92, 0.3)"
                    horizontal={true}
                    vertical={false}
                  />
                  <XAxis 
                    dataKey="name" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9BA7B4', fontSize: 12, fontWeight: 500 }}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#9BA7B4', fontSize: 12, fontWeight: 500 }}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'rgba(28, 33, 39, 0.95)',
                      border: '1px solid rgba(65, 77, 92, 0.3)',
                      borderRadius: '8px',
                      color: '#FFFFFF',
                      backdropFilter: 'blur(10px)',
                    }}
                    labelStyle={{ color: '#9BA7B4' }}
                  />
                  <Bar 
                    dataKey="value" 
                    radius={[4, 4, 0, 0]}
                    stroke="rgba(255, 255, 255, 0.1)"
                    strokeWidth={1}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>

            {/* Performance Indicators */}
            <Stack direction="row" spacing={2} mt={2}>
              <Box display="flex" alignItems="center">
                <Box 
                  sx={{ 
                    width: 12, 
                    height: 12, 
                    backgroundColor: '#1D8102', 
                    borderRadius: '50%', 
                    mr: 1 
                  }} 
                />
                <Typography variant="caption" color="text.secondary">
                  Matched ({metrics.matchedCount})
                </Typography>
              </Box>
              <Box display="flex" alignItems="center">
                <Box 
                  sx={{ 
                    width: 12, 
                    height: 12, 
                    backgroundColor: '#D13212', 
                    borderRadius: '50%', 
                    mr: 1 
                  }} 
                />
                <Typography variant="caption" color="text.secondary">
                  Breaks ({metrics.breakCount})
                </Typography>
              </Box>
              <Box display="flex" alignItems="center">
                <Box 
                  sx={{ 
                    width: 12, 
                    height: 12, 
                    backgroundColor: '#FF9900', 
                    borderRadius: '50%', 
                    mr: 1 
                  }} 
                />
                <Typography variant="caption" color="text.secondary">
                  Pending ({metrics.pendingReview})
                </Typography>
              </Box>
            </Stack>
          </>
        ) : (
          <Box 
            display="flex" 
            flexDirection="column" 
            alignItems="center" 
            justifyContent="center" 
            flexGrow={1}
            sx={{
              background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.5) 0%, rgba(35, 42, 49, 0.5) 100%)',
              borderRadius: 2,
              border: '1px dashed rgba(65, 77, 92, 0.3)',
            }}
          >
            <SpeedIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" align="center">
              Loading metrics...
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center" mt={1}>
              Processing metrics will appear here
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}
