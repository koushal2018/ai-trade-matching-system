import { Typography, Box, Avatar, Stack, Chip } from '@mui/material'
import {
  TableChart as TableIcon,
  CheckCircle as CompletedIcon,
  HourglassEmpty as PendingIcon,
  Error as ErrorIcon,
  Sync as ProcessingIcon,
} from '@mui/icons-material'
import DataTable, { Column } from '../common/DataTable'
import type { RecentSessionItem } from '../../types'
import { useNavigate } from 'react-router-dom'

interface MatchingResultsPanelProps {
  results: RecentSessionItem[]
}

const STATUS_CONFIG: Record<string, { icon: JSX.Element; label: string; color: string }> = {
  completed: { icon: <CompletedIcon />, label: 'Completed', color: '#1D8102' },
  processing: { icon: <ProcessingIcon />, label: 'Processing', color: '#FF9900' },
  initializing: { icon: <PendingIcon />, label: 'Initializing', color: '#0073BB' },
  failed: { icon: <ErrorIcon />, label: 'Failed', color: '#D13212' },
  pending: { icon: <PendingIcon />, label: 'Pending', color: '#9BA7B4' },
}

export default function MatchingResultsPanel({ results }: MatchingResultsPanelProps) {
  const navigate = useNavigate()

  // Define table columns for recent sessions
  const columns: Column<RecentSessionItem>[] = [
    {
      id: 'sessionId',
      label: 'Session ID',
      minWidth: 200,
      sortable: true,
      filterable: true,
    },
    {
      id: 'status',
      label: 'Status',
      minWidth: 140,
      sortable: true,
      filterable: true,
      filterType: 'select',
      filterOptions: [
        { value: 'completed', label: 'Completed' },
        { value: 'processing', label: 'Processing' },
        { value: 'initializing', label: 'Initializing' },
        { value: 'failed', label: 'Failed' },
        { value: 'pending', label: 'Pending' },
      ],
      format: (value: string) => {
        const config = STATUS_CONFIG[value] || STATUS_CONFIG.pending
        return (
          <Chip
            size="small"
            label={config.label}
            icon={config.icon}
            sx={{
              backgroundColor: config.color,
              color: '#FFFFFF',
              fontWeight: 600,
              fontSize: '0.75rem',
            }}
          />
        )
      },
    },
    {
      id: 'lastUpdated',
      label: 'Last Updated',
      minWidth: 180,
      sortable: true,
      format: (value?: string) => value ? new Date(value).toLocaleString() : 'N/A',
    },
    {
      id: 'createdAt',
      label: 'Created',
      minWidth: 180,
      sortable: true,
      format: (value?: string) => value ? new Date(value).toLocaleString() : 'N/A',
    },
  ]

  // Calculate status counts
  const statusCounts = results.reduce(
    (acc, result) => {
      const status = result.status || 'pending'
      acc[status] = (acc[status] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  return (
    <Box sx={{ p: 3 }}>
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
          Recent Processing Sessions
        </Typography>
      </Box>

      {results.length > 0 ? (
        <>
          {/* Status Summary */}
          <Stack direction="row" spacing={2} mb={3} flexWrap="wrap">
            {Object.entries(statusCounts).map(([status, count]) => {
              const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending
              return (
                <Box 
                  key={status}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    p: 1.5,
                    borderRadius: 1,
                    background: `linear-gradient(135deg, ${config.color}15 0%, ${config.color}08 100%)`,
                    border: `1px solid ${config.color}30`,
                  }}
                >
                  <Box 
                    sx={{ 
                      width: 12, 
                      height: 12, 
                      backgroundColor: config.color, 
                      borderRadius: '50%',
                    }} 
                  />
                  <Typography variant="body2" color="text.primary" fontWeight={500}>
                    {config.label}
                  </Typography>
                  <Chip
                    size="small"
                    label={count}
                    sx={{
                      backgroundColor: config.color,
                      color: '#FFFFFF',
                      fontWeight: 600,
                      minWidth: 32,
                      height: 24,
                    }}
                  />
                </Box>
              )
            })}
          </Stack>

          {/* Results Table */}
          <DataTable
            columns={columns}
            data={results}
            loading={false}
            searchable={true}
            filterable={true}
            pagination={true}
            emptyMessage="No recent sessions available"
            onRowClick={(row) => {
              // Navigate to workflow result page
              navigate(`/workflow/${row.sessionId}/result`)
            }}
          />
        </>
      ) : (
        <Box 
          display="flex" 
          flexDirection="column" 
          alignItems="center" 
          justifyContent="center" 
          sx={{
            py: 8,
            background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.5) 0%, rgba(35, 42, 49, 0.5) 100%)',
            borderRadius: 2,
            border: '1px dashed rgba(65, 77, 92, 0.3)',
          }}
        >
          <TableIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" align="center">
            No recent sessions yet
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center" mt={1}>
            Sessions will appear here after processing starts
          </Typography>
        </Box>
      )}
    </Box>
  )
}
