import { useState } from 'react'
import {
  Box,
  Typography,
  Container as MuiContainer,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Alert,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  PlayArrow as ProcessIcon,
  Visibility as ViewIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import GlassCard from '../components/common/GlassCard'
import { SkeletonGroup } from '../components/common/SkeletonLoader'
import CopyToClipboard from '../components/common/CopyToClipboard'
import { workflowService, type RecentSessionItem, type WorkflowStatusResponse } from '../services/workflowService'
import { mapOverallStatus } from '../utils/statusMapping'
import { fsiColors } from '../theme'

interface QueueItemWithDetails extends RecentSessionItem {
  details?: WorkflowStatusResponse
  hasExceptions?: boolean
}

const getStatusColor = (status: string) => {
  const mappedStatus = mapOverallStatus(status)
  switch (mappedStatus) {
    case 'In Progress': return fsiColors.status.info
    case 'Pending': return fsiColors.status.warning
    case 'Initializing': return fsiColors.accent.purple
    case 'Completed': return fsiColors.status.success
    case 'Failed': return fsiColors.status.error
    default: return fsiColors.text.muted
  }
}

/**
 * Check if a session has exceptions that require review
 */
const hasExceptions = (details?: WorkflowStatusResponse): boolean => {
  if (!details) return false
  
  // Check if exceptionManagement agent has error status
  if (details.agents.exceptionManagement?.status === 'error') {
    return true
  }
  
  // Check if any agent has error status
  const agentKeys = ['pdfAdapter', 'tradeExtraction', 'tradeMatching', 'exceptionManagement'] as const
  return agentKeys.some(key => details.agents[key]?.status === 'error')
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

  // Fetch recent sessions from Processing_Status table
  const { data: queueItems, isLoading, error, refetch } = useQuery<QueueItemWithDetails[]>({
    queryKey: ['matchingQueue'],
    queryFn: async () => {
      // Get recent sessions
      const sessions = await workflowService.getRecentSessions(50)
      
      // Fetch details for each session to check for exceptions
      const itemsWithDetails = await Promise.all(
        sessions.map(async (session) => {
          try {
            const details = await workflowService.getWorkflowStatus(session.sessionId)
            return {
              ...session,
              details,
              hasExceptions: hasExceptions(details)
            }
          } catch (err) {
            // If we can't get details, just return the session without details
            return {
              ...session,
              details: undefined,
              hasExceptions: false
            }
          }
        })
      )
      
      return itemsWithDetails
    },
    refetchInterval: 10000, // Poll every 10 seconds
  })

  // Calculate status counts using mapped statuses
  const processingCount = queueItems?.filter(i => 
    i.status === 'processing'
  ).length || 0
  
  const pendingCount = queueItems?.filter(i => 
    i.status === 'pending' || i.status === 'initializing'
  ).length || 0
  
  const completedCount = queueItems?.filter(i => 
    i.status === 'completed'
  ).length || 0
  
  const exceptionsCount = queueItems?.filter(i => 
    i.hasExceptions
  ).length || 0

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
            <Typography variant="h4" fontWeight={700} sx={{ color: '#10B981' }}>
              {completedCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Completed
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} sx={{ color: '#EF4444' }}>
              {exceptionsCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Exceptions
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

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          Unable to load queue. {error instanceof Error ? error.message : 'Please try again.'}
        </Alert>
      )}

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
            {queueItems.map((item, index) => {
              const displayStatus = mapOverallStatus(item.status)
              const statusColor = getStatusColor(item.status)
              
              return (
                <Box
                  key={item.sessionId}
                  onClick={() => setSelectedItem(selectedItem === item.sessionId ? null : item.sessionId)}
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
                    bgcolor: selectedItem === item.sessionId ? 'rgba(255,153,0,0.05)' : 'transparent',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                      <Typography variant="body1" fontWeight={600}>
                        Session {item.sessionId.substring(0, 8)}...
                      </Typography>
                      <Chip
                        label={displayStatus}
                        size="small"
                        sx={{
                          height: 24,
                          fontSize: '0.75rem',
                          bgcolor: `${statusColor}20`,
                          color: statusColor,
                          border: `1px solid ${statusColor}40`,
                        }}
                      />
                      {item.hasExceptions && (
                        <Chip
                          icon={<WarningIcon sx={{ fontSize: '0.875rem' }} />}
                          label="Requires Review"
                          size="small"
                          sx={{
                            height: 24,
                            fontSize: '0.75rem',
                            bgcolor: `${fsiColors.status.error}20`,
                            color: fsiColors.status.error,
                            border: `1px solid ${fsiColors.status.error}40`,
                          }}
                        />
                      )}
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Tooltip title="View details">
                        <IconButton 
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            window.location.href = `/workflow/${item.sessionId}/result`
                          }}
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {item.status !== 'completed' && (
                        <Tooltip title="Process now">
                          <IconButton 
                            size="small" 
                            sx={{ color: '#10B981' }}
                            onClick={(e) => {
                              e.stopPropagation()
                              // TODO: Implement manual processing trigger
                            }}
                          >
                            <ProcessIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="caption" color="text.disabled">Session ID:</Typography>
                      <CopyToClipboard text={item.sessionId} truncate maxLength={12} />
                    </Box>
                    {item.createdAt && (
                      <Box>
                        <Typography variant="caption" color="text.disabled">Created: </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(item.createdAt)}
                        </Typography>
                      </Box>
                    )}
                    {item.lastUpdated && (
                      <Box>
                        <Typography variant="caption" color="text.disabled">Updated: </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(item.lastUpdated)}
                        </Typography>
                      </Box>
                    )}
                  </Box>

                  {item.status === 'processing' && (
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
              )
            })}
          </Box>
        )}
      </GlassCard>
    </MuiContainer>
  )
}
