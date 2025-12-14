import { Card, CardContent, Typography, Box, Avatar, Stack, Divider, Chip, Grid } from '@mui/material'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import {
  PieChart as PieChartIcon,
  CheckCircle as MatchedIcon,
  Warning as ReviewIcon,
  Error as BreakIcon,
  DataUsage as DataIcon,
  TableChart as TableIcon,
} from '@mui/icons-material'
import DataTable, { Column } from '../common/DataTable'
import type { MatchingResult, MatchClassification } from '../../types'

interface MatchingResultsPanelProps {
  results: MatchingResult[]
}

const COLORS: Record<MatchClassification, string> = {
  MATCHED: '#1D8102',
  PROBABLE_MATCH: '#8BC34A',
  REVIEW_REQUIRED: '#FF9900',
  BREAK: '#D13212',
  DATA_ERROR: '#9C27B0',
}

const CLASSIFICATION_CONFIG: Record<MatchClassification, { icon: JSX.Element; label: string }> = {
  MATCHED: { icon: <MatchedIcon />, label: 'Matched' },
  PROBABLE_MATCH: { icon: <MatchedIcon />, label: 'Probable Match' },
  REVIEW_REQUIRED: { icon: <ReviewIcon />, label: 'Review Required' },
  BREAK: { icon: <BreakIcon />, label: 'Break' },
  DATA_ERROR: { icon: <DataIcon />, label: 'Data Error' },
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
    label: CLASSIFICATION_CONFIG[name as MatchClassification]?.label || name,
  }))

  const matchRate = results.length > 0
    ? ((classificationCounts.MATCHED || 0) / results.length * 100).toFixed(1)
    : '0'

  const totalMatched = (classificationCounts.MATCHED || 0) + (classificationCounts.PROBABLE_MATCH || 0)
  const successRate = results.length > 0 ? (totalMatched / results.length * 100).toFixed(1) : '0'

  // Define table columns for detailed results
  const columns: Column<MatchingResult>[] = [
    {
      id: 'tradeId',
      label: 'Trade ID',
      minWidth: 120,
      sortable: true,
      filterable: true,
    },
    {
      id: 'classification',
      label: 'Classification',
      minWidth: 140,
      sortable: true,
      filterable: true,
      filterType: 'select',
      filterOptions: [
        { value: 'MATCHED', label: 'Matched' },
        { value: 'PROBABLE_MATCH', label: 'Probable Match' },
        { value: 'REVIEW_REQUIRED', label: 'Review Required' },
        { value: 'BREAK', label: 'Break' },
        { value: 'DATA_ERROR', label: 'Data Error' },
      ],
      format: (value: MatchClassification) => (
        <Chip
          size="small"
          label={CLASSIFICATION_CONFIG[value]?.label || value}
          icon={CLASSIFICATION_CONFIG[value]?.icon}
          sx={{
            backgroundColor: COLORS[value],
            color: '#FFFFFF',
            fontWeight: 600,
            fontSize: '0.75rem',
          }}
        />
      ),
    },
    {
      id: 'matchScore',
      label: 'Match Score',
      minWidth: 100,
      align: 'center',
      sortable: true,
      format: (value: number) => `${(value * 100).toFixed(1)}%`,
    },
    {
      id: 'decisionStatus',
      label: 'Decision Status',
      minWidth: 120,
      sortable: true,
      filterable: true,
      filterType: 'select',
      filterOptions: [
        { value: 'AUTO_MATCH', label: 'Auto Match' },
        { value: 'ESCALATE', label: 'Escalate' },
        { value: 'EXCEPTION', label: 'Exception' },
        { value: 'PENDING', label: 'Pending' },
        { value: 'APPROVED', label: 'Approved' },
        { value: 'REJECTED', label: 'Rejected' },
      ],
    },
    {
      id: 'createdAt',
      label: 'Created',
      minWidth: 140,
      sortable: true,
      format: (value: string) => new Date(value).toLocaleString(),
    },
  ]

  return (
    <Grid container spacing={3}>
      {/* Summary Card */}
      <Grid item xs={12} md={6}>
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
                <PieChartIcon />
              </Avatar>
              <Typography variant="h5" fontWeight={600} color="text.primary">
                Matching Summary
              </Typography>
            </Box>

            {results.length > 0 ? (
              <>
                {/* Success Rate Display */}
                <Box 
                  textAlign="center" 
                  mb={3}
                  sx={{
                    p: 3,
                    background: 'linear-gradient(135deg, rgba(29, 129, 2, 0.1) 0%, rgba(29, 129, 2, 0.05) 100%)',
                    borderRadius: 2,
                    border: '1px solid rgba(29, 129, 2, 0.2)',
                  }}
                >
                  <Typography variant="h2" fontWeight={700} sx={{ color: '#1D8102' }}>
                    {matchRate}%
                  </Typography>
                  <Typography variant="body1" color="text.secondary" fontWeight={500}>
                    Direct Match Rate
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Success Rate (including probable): {successRate}%
                  </Typography>
                </Box>

                {/* Chart */}
                <Box flexGrow={1} display="flex" flexDirection="column">
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={90}
                        dataKey="value"
                        stroke="rgba(255, 255, 255, 0.1)"
                        strokeWidth={2}
                      >
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: 'rgba(28, 33, 39, 0.95)',
                          border: '1px solid rgba(65, 77, 92, 0.3)',
                          borderRadius: '8px',
                          color: '#FFFFFF',
                          backdropFilter: 'blur(10px)',
                        }}
                        formatter={(value, name) => [value, CLASSIFICATION_CONFIG[name as MatchClassification]?.label || name]}
                      />
                    </PieChart>
                  </ResponsiveContainer>

                  <Divider sx={{ my: 2, borderColor: 'rgba(65, 77, 92, 0.3)' }} />

                  {/* Classification Breakdown */}
                  <Stack spacing={1}>
                    {Object.entries(classificationCounts).map(([classification, count]) => {
                      const config = CLASSIFICATION_CONFIG[classification as MatchClassification]
                      const color = COLORS[classification as MatchClassification]
                      const percentage = ((count / results.length) * 100).toFixed(1)
                      
                      return (
                        <Box 
                          key={classification}
                          display="flex" 
                          alignItems="center" 
                          justifyContent="space-between"
                          sx={{
                            p: 1.5,
                            borderRadius: 1,
                            background: `linear-gradient(135deg, ${color}15 0%, ${color}08 100%)`,
                            border: `1px solid ${color}30`,
                          }}
                        >
                          <Box display="flex" alignItems="center">
                            <Box 
                              sx={{ 
                                width: 12, 
                                height: 12, 
                                backgroundColor: color, 
                                borderRadius: '50%', 
                                mr: 2 
                              }} 
                            />
                            <Typography variant="body2" color="text.primary" fontWeight={500}>
                              {config?.label || classification}
                            </Typography>
                          </Box>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip
                              size="small"
                              label={count}
                              sx={{
                                backgroundColor: color,
                                color: '#FFFFFF',
                                fontWeight: 600,
                                minWidth: 40,
                              }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {percentage}%
                            </Typography>
                          </Box>
                        </Box>
                      )
                    })}
                  </Stack>

                  {/* Summary Stats */}
                  <Box 
                    mt={2} 
                    p={2} 
                    sx={{
                      background: 'linear-gradient(135deg, rgba(155, 167, 180, 0.1) 0%, rgba(155, 167, 180, 0.05) 100%)',
                      borderRadius: 2,
                      border: '1px solid rgba(155, 167, 180, 0.2)',
                    }}
                  >
                    <Typography variant="caption" color="text.secondary" display="block">
                      Total Results: {results.length.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Requires Review: {(classificationCounts.REVIEW_REQUIRED || 0) + (classificationCounts.BREAK || 0)}
                    </Typography>
                  </Box>
                </Box>
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
                <PieChartIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" align="center">
                  No matching results yet
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center" mt={1}>
                  Results will appear here after trade processing
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Detailed Results Table */}
      <Grid item xs={12} md={6}>
        <Card sx={{ 
          height: '100%',
          background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(65, 77, 92, 0.3)',
        }}>
          <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box display="flex" alignItems="center" mb={3}>
              <Avatar sx={{ 
                bgcolor: 'secondary.main', 
                mr: 2,
                width: 40,
                height: 40
              }}>
                <TableIcon />
              </Avatar>
              <Typography variant="h5" fontWeight={600} color="text.primary">
                Recent Results
              </Typography>
            </Box>

            <Box flexGrow={1}>
              <DataTable
                columns={columns}
                data={results.slice(0, 10)} // Show only recent 10 results
                loading={false}
                searchable={true}
                filterable={true}
                pagination={false}
                emptyMessage="No matching results available"
                onRowClick={(row) => {
                  console.log('View details for:', row.tradeId)
                  // TODO: Implement row click handler
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  )
}
