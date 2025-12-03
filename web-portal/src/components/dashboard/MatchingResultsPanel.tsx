import { Card, CardContent, Typography, Box } from '@mui/material'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import type { MatchingResult, MatchClassification } from '../../types'

interface MatchingResultsPanelProps {
  results: MatchingResult[]
}

const COLORS: Record<MatchClassification, string> = {
  MATCHED: '#4caf50',
  PROBABLE_MATCH: '#8bc34a',
  REVIEW_REQUIRED: '#ff9800',
  BREAK: '#f44336',
  DATA_ERROR: '#9c27b0',
}

export default function MatchingResultsPanel({ results }: MatchingResultsPanelProps) {
  const classificationCounts = results.reduce(
    (acc, result) => {
      acc[result.classification] = (acc[result.classification] || 0) + 1
      return acc
    },
    {} as Record<MatchClassification, number>
  )

  const chartData = Object.entries(classificationCounts).map(([name, value]) => ({
    name,
    value,
    color: COLORS[name as MatchClassification],
  }))

  const matchRate = results.length > 0
    ? ((classificationCounts.MATCHED || 0) / results.length * 100).toFixed(1)
    : '0'

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Matching Results
        </Typography>
        {results.length > 0 ? (
          <>
            <Box textAlign="center" mb={2}>
              <Typography variant="h3" color="success.main">
                {matchRate}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Match Rate
              </Typography>
            </Box>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >

                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </>
        ) : (
          <Typography color="text.secondary" align="center" py={4}>
            No matching results yet
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
