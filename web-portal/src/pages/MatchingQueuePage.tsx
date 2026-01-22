import { useState } from 'react'
import {
  Box,
  Typography,
  Container as MuiContainer,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  PlayArrow as ProcessIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import GlassCard from '../components/common/GlassCard'
import { SkeletonGroup } from '../components/common/SkeletonLoader'
import CopyToClipboard from '../components/common/CopyToClipboard'
import { apiClient } from '../services/api'
import { fsiColors } from '../theme'

interface QueueItem {
  queueId: string
  sessionId: string
  tradeId: string
  counterpartyId: string
  status: 'PENDING' | 'PROCESSING' | 'WAITING' | 'COMPLETED' | 'FAILED'
  priority: 'HIGH' | 'MEDIUM' | 'LOW'
  queuedAt: string
  estimatedProcessingTime: number
  sourceType: string
  documentCount: number
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'PROCESSING': return fsiColors.status.info
    case 'PENDING': return fsiColors.status.warning
    case 'WAITING': return fsiColors.accent.purple
    case 'COMPLETED': return fsiColors.status.success
    case 'FAILED': return fsiColors.status.error
    default: return fsiColors.text.muted
  }
}

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'HIGH': return fsiColors.status.error
    case 'MEDIUM': return fsiColors.status.warning
    case 'LOW': return fsiColors.status.success
    default: return fsiColors.text.muted
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

export default function MatchingQueuePage() {
  const [selectedItem, setSelectedItem] = useState<string | null>(null)

  const { data: queueItems, isLoading, refetch } = useQuery<QueueItem[]>({
    queryKey: ['matchingQueue'],
    queryFn: () => apiClient.get<QueueItem[]>('/matching/queue'),
    refetchInterval: 10000,
  })

  const processingCount = queueItems?.filter(i => i.status === 'PROCESSING').length || 0
  const pendingCount = queueItems?.filter(i => i.status === 'PENDING').length || 0
  const waitingCount = queueItems?.filter(i => i.status === 'WAITING').length || 0

  return (
    <MuiContainer maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          animation: 'fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          '@keyframes fadeIn': {
            '0%': { opacity: 0, transform: 'translateY(-16px)' },
            '100%': { opacity: 1, transform: 'translateY(0)' },
          },
        }}
      >
        <Box>
          <Typography
            variant="overline"
            sx={{
              color: fsiColors.orange.main,
              letterSpacing: '0.15em',
              fontWeight: 600,
              display: 'block',
              mb: 0.5,
            }}
          >
            PROCESSING QUEUE
          </Typography>
          <Typography
            variant="h3"
            fontWeight={700}
            sx={{
              mb: 1,
              color: fsiColors.text.primary,
              letterSpacing: '-0.02em',
            }}
          >
            Matching Queue
          </Typography>
          <Typography variant="body1" sx={{ color: fsiColors.text.secondary }}>
            Trade confirmations waiting to be processed
          </Typography>
        </Box>
        <Tooltip title="Refresh queue">
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
            <Typography variant="h4" fontWeight={700} sx={{ color: '#3B82F6' }}>
              {processingCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Processing
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} sx={{ color: '#F59E0B' }}>
              {pendingCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Pending
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} sx={{ color: '#8B5CF6' }}>
              {waitingCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Waiting
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} color="text.primary">
              {queueItems?.length || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total in Queue
            </Typography>
          </Box>
        </Box>
      </GlassCard>

      {/* Queue Items */}
      <GlassCard variant="default" animateIn animationDelay={0.1} sx={{ p: 0 }}>
        <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <Typography variant="h6" fontWeight={600}>
            Queue Items
          </Typography>
        </Box>

        {isLoading ? (
          <Box sx={{ p: 3 }}>
            <SkeletonGroup variant="table" count={5} />
          </Box>
        ) : !queueItems || queueItems.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">
              No items in the matching queue
            </Typography>
          </Box>
        ) : (
          <Box>
            {queueItems.map((item, index) => (
              <Box
                key={item.queueId}
                onClick={() => setSelectedItem(selectedItem === item.queueId ? null : item.queueId)}
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
                  bgcolor: selectedItem === item.queueId ? 'rgba(255,153,0,0.05)' : 'transparent',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="body1" fontWeight={600}>
                      {item.tradeId}
                    </Typography>
                    <Chip
                      label={item.status}
                      size="small"
                      sx={{
                        height: 24,
                        fontSize: '0.75rem',
                        bgcolor: `${getStatusColor(item.status)}20`,
                        color: getStatusColor(item.status),
                        border: `1px solid ${getStatusColor(item.status)}40`,
                      }}
                    />
                    <Chip
                      label={item.priority}
                      size="small"
                      sx={{
                        height: 24,
                        fontSize: '0.75rem',
                        bgcolor: `${getPriorityColor(item.priority)}20`,
                        color: getPriorityColor(item.priority),
                        border: `1px solid ${getPriorityColor(item.priority)}40`,
                      }}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Tooltip title="View details">
                      <IconButton size="small">
                        <ViewIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Process now">
                      <IconButton size="small" sx={{ color: '#10B981' }}>
                        <ProcessIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" color="text.disabled">Session:</Typography>
                    <CopyToClipboard text={item.sessionId} truncate maxLength={12} />
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">Counterparty: </Typography>
                    <Typography variant="caption" color="text.secondary">{item.counterpartyId}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">Source: </Typography>
                    <Typography variant="caption" color="text.secondary">{item.sourceType}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">Documents: </Typography>
                    <Typography variant="caption" color="text.secondary">{item.documentCount}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">Queued: </Typography>
                    <Typography variant="caption" color="text.secondary">{formatTime(item.queuedAt)}</Typography>
                  </Box>
                </Box>

                {item.status === 'PROCESSING' && (
                  <LinearProgress
                    sx={{
                      mt: 1,
                      height: 4,
                      borderRadius: 2,
                      bgcolor: 'rgba(59, 130, 246, 0.1)',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: '#3B82F6',
                      },
                    }}
                  />
                )}
              </Box>
            ))}
          </Box>
        )}
      </GlassCard>
    </MuiContainer>
  )
}
