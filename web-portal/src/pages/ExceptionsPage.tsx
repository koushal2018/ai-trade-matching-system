import { useState } from 'react'
import {
  Box,
  Typography,
  Container as MuiContainer,
  Chip,
  IconButton,
  Tooltip,
  Button,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  CheckCircle as ResolveIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import GlassCard from '../components/common/GlassCard'
import { SkeletonGroup } from '../components/common/SkeletonLoader'
import CopyToClipboard from '../components/common/CopyToClipboard'
import { useToast } from '../hooks/useToast'
import { apiClient } from '../services/api'

interface Exception {
  id: string
  sessionId: string
  tradeId: string
  agentName: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | 'warning'
  type: string
  message: string
  timestamp: string
  recoverable: boolean
  status: 'OPEN' | 'RESOLVED' | 'ESCALATED'
  details: {
    field?: string
    bankValue?: string
    counterpartyValue?: string
    confidence?: number
  }
}

interface ExceptionsResponse {
  exceptions: Exception[]
}

const getSeverityIcon = (severity: string) => {
  switch (severity.toUpperCase()) {
    case 'HIGH': return <ErrorIcon sx={{ color: '#EF4444', fontSize: 20 }} />
    case 'MEDIUM': return <WarningIcon sx={{ color: '#F59E0B', fontSize: 20 }} />
    case 'LOW': return <InfoIcon sx={{ color: '#3B82F6', fontSize: 20 }} />
    case 'WARNING': return <WarningIcon sx={{ color: '#F59E0B', fontSize: 20 }} />
    default: return <InfoIcon sx={{ color: '#6B7280', fontSize: 20 }} />
  }
}

const getSeverityColor = (severity: string) => {
  switch (severity.toUpperCase()) {
    case 'HIGH': return '#EF4444'
    case 'MEDIUM': return '#F59E0B'
    case 'LOW': return '#3B82F6'
    case 'WARNING': return '#F59E0B'
    default: return '#6B7280'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'OPEN': return '#EF4444'
    case 'RESOLVED': return '#10B981'
    case 'ESCALATED': return '#8B5CF6'
    default: return '#6B7280'
  }
}

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function ExceptionsPage() {
  const [selectedItem, setSelectedItem] = useState<string | null>(null)
  const { success } = useToast()

  const { data, isLoading, refetch } = useQuery<ExceptionsResponse>({
    queryKey: ['exceptions'],
    queryFn: () => apiClient.get<ExceptionsResponse>('/exceptions'),
    refetchInterval: 15000,
  })

  const exceptions = data?.exceptions || []
  const openCount = exceptions.filter(e => e.status === 'OPEN').length
  const highCount = exceptions.filter(e => e.severity.toUpperCase() === 'HIGH').length
  const mediumCount = exceptions.filter(e => e.severity.toUpperCase() === 'MEDIUM').length

  const handleResolve = (exceptionId: string) => {
    success(`Exception ${exceptionId} marked as resolved`)
  }

  return (
    <MuiContainer maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          animation: 'fadeIn 0.5s ease-out',
          '@keyframes fadeIn': {
            '0%': { opacity: 0, transform: 'translateY(-10px)' },
            '100%': { opacity: 1, transform: 'translateY(0)' },
          },
        }}
      >
        <Box>
          <Typography
            variant="h3"
            fontWeight={700}
            sx={{
              fontFamily: '"Amazon Ember", "Helvetica Neue", Helvetica, Arial, sans-serif',
              mb: 1,
              color: '#232F3E',
            }}
          >
            Exceptions
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Trade matching exceptions and errors requiring attention
          </Typography>
        </Box>
        <Tooltip title="Refresh exceptions">
          <IconButton
            onClick={() => refetch()}
            sx={{
              bgcolor: 'rgba(255, 153, 0, 0.1)',
              '&:hover': { bgcolor: 'rgba(255, 153, 0, 0.2)' },
            }}
          >
            <RefreshIcon sx={{ color: '#FF9900' }} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Stats Bar */}
      <GlassCard variant="elevated" animateIn sx={{ mb: 4, p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} sx={{ color: '#EF4444' }}>
              {openCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Open Exceptions
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} sx={{ color: '#EF4444' }}>
              {highCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              High Severity
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} sx={{ color: '#F59E0B' }}>
              {mediumCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Medium Severity
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} color="text.primary">
              {exceptions.length}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total Exceptions
            </Typography>
          </Box>
        </Box>
      </GlassCard>

      {/* Exceptions List */}
      <GlassCard variant="default" animateIn animationDelay={0.1} sx={{ p: 0 }}>
        <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <Typography variant="h6" fontWeight={600}>
            Exception Details
          </Typography>
        </Box>

        {isLoading ? (
          <Box sx={{ p: 3 }}>
            <SkeletonGroup variant="table" count={5} />
          </Box>
        ) : !exceptions || exceptions.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <ResolveIcon sx={{ fontSize: 48, color: '#10B981', mb: 2 }} />
            <Typography color="text.secondary">
              No exceptions to display - all trades processed successfully!
            </Typography>
          </Box>
        ) : (
          <Box>
            {exceptions.map((exception, index) => (
              <Box
                key={exception.id}
                onClick={() => setSelectedItem(selectedItem === exception.id ? null : exception.id)}
                sx={{
                  p: 2,
                  borderBottom: '1px solid rgba(255,255,255,0.05)',
                  cursor: 'pointer',
                  animation: `slideIn 0.3s ease-out ${index * 0.05}s both`,
                  '@keyframes slideIn': {
                    '0%': { opacity: 0, transform: 'translateX(-20px)' },
                    '100%': { opacity: 1, transform: 'translateX(0)' },
                  },
                  '&:hover': {
                    bgcolor: 'rgba(255,255,255,0.03)',
                  },
                  bgcolor: selectedItem === exception.id ? 'rgba(239,68,68,0.05)' : 'transparent',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {getSeverityIcon(exception.severity)}
                    <Typography variant="body1" fontWeight={600}>
                      {exception.tradeId}
                    </Typography>
                    <Chip
                      label={exception.severity.toUpperCase()}
                      size="small"
                      sx={{
                        height: 24,
                        fontSize: '0.75rem',
                        bgcolor: `${getSeverityColor(exception.severity)}20`,
                        color: getSeverityColor(exception.severity),
                        border: `1px solid ${getSeverityColor(exception.severity)}40`,
                      }}
                    />
                    <Chip
                      label={exception.status}
                      size="small"
                      sx={{
                        height: 24,
                        fontSize: '0.75rem',
                        bgcolor: `${getStatusColor(exception.status)}20`,
                        color: getStatusColor(exception.status),
                        border: `1px solid ${getStatusColor(exception.status)}40`,
                      }}
                    />
                    <Chip
                      label={exception.type}
                      size="small"
                      variant="outlined"
                      sx={{ height: 24, fontSize: '0.75rem' }}
                    />
                  </Box>
                  {exception.status === 'OPEN' && (
                    <Button
                      size="small"
                      startIcon={<ResolveIcon />}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleResolve(exception.id)
                      }}
                      sx={{
                        color: '#10B981',
                        '&:hover': { bgcolor: 'rgba(16, 185, 129, 0.1)' },
                      }}
                    >
                      Resolve
                    </Button>
                  )}
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 1, ml: 4 }}>
                  {exception.message}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap', ml: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" color="text.disabled">Session:</Typography>
                    <CopyToClipboard text={exception.sessionId} truncate maxLength={12} />
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">Agent: </Typography>
                    <Typography variant="caption" color="text.secondary">{exception.agentName}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">Time: </Typography>
                    <Typography variant="caption" color="text.secondary">{formatTime(exception.timestamp)}</Typography>
                  </Box>
                  {exception.recoverable && (
                    <Chip
                      label="Recoverable"
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.65rem',
                        bgcolor: 'rgba(16, 185, 129, 0.1)',
                        color: '#10B981',
                      }}
                    />
                  )}
                </Box>

                {/* Expanded Details */}
                {selectedItem === exception.id && exception.details && (
                  <Box
                    sx={{
                      mt: 2,
                      ml: 4,
                      p: 2,
                      borderRadius: 1,
                      bgcolor: 'rgba(255,255,255,0.03)',
                      border: '1px solid rgba(255,255,255,0.08)',
                    }}
                  >
                    <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>
                      Exception Details
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                      {exception.details.field && (
                        <Box>
                          <Typography variant="caption" color="text.disabled">Field</Typography>
                          <Typography variant="body2">{exception.details.field}</Typography>
                        </Box>
                      )}
                      {exception.details.bankValue && (
                        <Box>
                          <Typography variant="caption" color="text.disabled">Bank Value</Typography>
                          <Typography variant="body2">{exception.details.bankValue}</Typography>
                        </Box>
                      )}
                      {exception.details.counterpartyValue && (
                        <Box>
                          <Typography variant="caption" color="text.disabled">Counterparty Value</Typography>
                          <Typography variant="body2">{exception.details.counterpartyValue}</Typography>
                        </Box>
                      )}
                      {exception.details.confidence !== undefined && (
                        <Box>
                          <Typography variant="caption" color="text.disabled">Confidence</Typography>
                          <Typography variant="body2">{(exception.details.confidence * 100).toFixed(0)}%</Typography>
                        </Box>
                      )}
                    </Box>
                  </Box>
                )}
              </Box>
            ))}
          </Box>
        )}
      </GlassCard>
    </MuiContainer>
  )
}
