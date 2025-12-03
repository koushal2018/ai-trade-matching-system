import { Card, CardContent, Typography, Box, Grid } from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { ProcessingMetrics } from '../../types'

interface ProcessingMetricsPanelProps {
  metrics?: ProcessingMetrics
}

export default function ProcessingMetricsPanel({ metrics }: ProcessingMetricsPanelProps) {
  const chartData = metrics
    ? [
        { name: 'Matched', value: metrics.matchedCount, fill: '#4caf50' },
        { name: 'Breaks', value: metrics.breakCount, fill: '#f44336' },
        { name: 'Pending', value: metrics.pendingReview, fill: '#ff9800' },
      ]
    : []

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Processing Metrics
        </Typography>
        {metrics ? (
          <>
            <Grid container spacing={2} mb={2}>
              <Grid item xs={6}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {metrics.totalProcessed}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Processed
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box textAlign="center">
                  <Typography variant="h4" color="secondary">
                    {metrics.throughputPerHour}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Trades/Hour
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            <Box textAlign="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Avg Processing Time: {metrics.avgProcessingTimeMs}ms
              </Typography>
            </Box>

            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" />
              </BarChart>
            </ResponsiveContainer>
          </>
        ) : (
          <Typography color="text.secondary" align="center" py={4}>
            Loading metrics...
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
