import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Container as MuiContainer,
  Grid,
  Chip,
  Divider,
  TextField,
  Stack,
  Badge,
} from '@mui/material'
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Compare as CompareIcon,
  Assignment as ReviewIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { hitlService, HITLDecision } from '../services/hitlService'
import { wsService } from '../services/websocket'
import GlassCard from '../components/common/GlassCard'
import GlassButton from '../components/common/GlassButton'
import { SkeletonLoader } from '../components/common/SkeletonLoader'
import StatusPulse from '../components/common/StatusPulse'
import CopyToClipboard from '../components/common/CopyToClipboard'
import { useToast } from '../hooks/useToast'
import { glowColors } from '../theme'
import type { HITLReview, WebSocketMessage } from '../types'

export default function HITLPanel() {
  const [selectedReview, setSelectedReview] = useState<HITLReview | null>(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [newReviewCount, setNewReviewCount] = useState(0)
  const queryClient = useQueryClient()
  const { success, error, info } = useToast()

  const { data: pendingReviews, isLoading, refetch } = useQuery<HITLReview[]>({
    queryKey: ['pendingReviews'],
    queryFn: hitlService.getPendingReviews,
    refetchInterval: 30000,
  })

  const decisionMutation = useMutation({
    mutationFn: (decision: HITLDecision) => hitlService.submitDecision(decision),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['pendingReviews'] })
      setSelectedReview(null)
      setRejectionReason('')
      success(`Trade ${variables.decision === 'APPROVED' ? 'approved' : 'rejected'} successfully`)
    },
    onError: (err) => {
      error(err instanceof Error ? err.message : 'Failed to submit decision')
    },
  })

  useEffect(() => {
    wsService.connect()
    const unsub = wsService.subscribe('HITL_REQUIRED', (_msg: WebSocketMessage) => {
      refetch()
      setNewReviewCount((prev) => prev + 1)
      info('New review requires attention')
    })
    return () => unsub()
  }, [refetch, info])

  const handleDecision = (decision: 'APPROVED' | 'REJECTED') => {
    if (selectedReview) {
      decisionMutation.mutate({
        reviewId: selectedReview.reviewId,
        decision,
        reason: decision === 'REJECTED' ? rejectionReason : undefined,
      })
    }
  }

  const handleSelectReview = (review: HITLReview) => {
    setSelectedReview(review)
    setRejectionReason('')
    if (newReviewCount > 0) {
      setNewReviewCount(0)
    }
  }

  // Calculate match status color
  const getMatchScoreColor = (score: number) => {
    if (score >= 0.9) return glowColors.success
    if (score >= 0.7) return glowColors.warning
    return glowColors.error
  }

  return (
    <MuiContainer maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box
        sx={{
          mb: 4,
          animation: 'fadeIn 0.5s ease-out',
          '@keyframes fadeIn': {
            '0%': { opacity: 0, transform: 'translateY(-10px)' },
            '100%': { opacity: 1, transform: 'translateY(0)' },
          },
        }}
      >
        <Box display="flex" alignItems="center" gap={2} mb={1}>
          <Typography
            variant="h3"
            fontWeight={700}
            sx={{
              color: '#232F3E',
            }}
          >
            Human-in-the-Loop Reviews
          </Typography>
          {newReviewCount > 0 && (
            <Badge
              badgeContent={newReviewCount}
              color="warning"
              sx={{
                '& .MuiBadge-badge': {
                  animation: 'pulse 2s ease-in-out infinite',
                  '@keyframes pulse': {
                    '0%': { transform: 'scale(1)' },
                    '50%': { transform: 'scale(1.15)' },
                    '100%': { transform: 'scale(1)' },
                  },
                },
              }}
            >
              <WarningIcon sx={{ color: glowColors.warning }} />
            </Badge>
          )}
        </Box>
        <Typography variant="body1" color="text.secondary">
          Review and approve trade matches requiring human verification
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Left Panel: Review List */}
        <Grid size={{ xs: 12, md: 4 }}>
          <GlassCard
            variant="default"
            hoverEffect="none"
            animateIn
            sx={{ height: '100%', minHeight: 600 }}
          >
            <Box sx={{ p: 3 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
                <Box display="flex" alignItems="center" gap={1}>
                  <ReviewIcon sx={{ color: glowColors.primary }} />
                  <Typography variant="h6" fontWeight={600}>
                    Pending Reviews
                  </Typography>
                </Box>
                <Chip
                  label={pendingReviews?.length || 0}
                  size="small"
                  sx={{
                    backgroundColor: 'rgba(255, 153, 0, 0.15)',
                    color: glowColors.primary,
                    fontWeight: 600,
                  }}
                />
              </Box>

              {isLoading ? (
                <Stack spacing={2}>
                  {[1, 2, 3].map((i) => (
                    <SkeletonLoader key={i} variant="card" height={100} />
                  ))}
                </Stack>
              ) : !pendingReviews || pendingReviews.length === 0 ? (
                <GlassCard variant="inset" hoverEffect="none">
                  <Box sx={{ p: 4, textAlign: 'center' }}>
                    <CompareIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography color="text.secondary">No pending reviews</Typography>
                  </Box>
                </GlassCard>
              ) : (
                <Stack spacing={2}>
                  {pendingReviews.map((review, index) => (
                    <GlassCard
                      key={review.reviewId}
                      variant="subtle"
                      glowColor={getMatchScoreColor(review.matchScore)}
                      hoverEffect="all"
                      animateIn
                      animationDelay={index * 0.05}
                      onClick={() => handleSelectReview(review)}
                      sx={{
                        cursor: 'pointer',
                        border: selectedReview?.reviewId === review.reviewId
                          ? `2px solid ${glowColors.primary}`
                          : undefined,
                      }}
                    >
                      <Box sx={{ p: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="body2" fontWeight={600} color="text.primary">
                            {review.tradeId}
                          </Typography>
                          <StatusPulse
                            status="pending"
                            size="small"
                            variant="badge"
                            showLabel={false}
                          />
                        </Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="caption" color="text.secondary">
                            Match Score
                          </Typography>
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            sx={{ color: getMatchScoreColor(review.matchScore) }}
                          >
                            {(review.matchScore * 100).toFixed(0)}%
                          </Typography>
                        </Box>
                      </Box>
                    </GlassCard>
                  ))}
                </Stack>
              )}
            </Box>
          </GlassCard>
        </Grid>

        {/* Right Panel: Review Details */}
        <Grid size={{ xs: 12, md: 8 }}>
          <GlassCard
            variant="default"
            hoverEffect="none"
            animateIn
            animationDelay={0.1}
            sx={{ height: '100%', minHeight: 600 }}
          >
            <Box sx={{ p: 3 }}>
              {!selectedReview ? (
                <Box
                  display="flex"
                  flexDirection="column"
                  alignItems="center"
                  justifyContent="center"
                  sx={{ height: 500 }}
                >
                  <CompareIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Select a review to see details
                  </Typography>
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    Click on a pending review to compare trade data
                  </Typography>
                </Box>
              ) : (
                <>
                  {/* Review Header */}
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                    <Box>
                      <Typography variant="h5" fontWeight={600}>
                        Trade: {selectedReview.tradeId}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={2} mt={1}>
                        <CopyToClipboard
                          text={selectedReview.sessionId || selectedReview.reviewId}
                          label="Session ID"
                          truncate
                          size="small"
                        />
                      </Box>
                    </Box>
                    <Box
                      sx={{
                        textAlign: 'center',
                        p: 2,
                        borderRadius: 2,
                        backgroundColor: `${getMatchScoreColor(selectedReview.matchScore)}15`,
                        border: `1px solid ${getMatchScoreColor(selectedReview.matchScore)}40`,
                      }}
                    >
                      <Typography variant="h3" fontWeight={700} sx={{ color: getMatchScoreColor(selectedReview.matchScore) }}>
                        {(selectedReview.matchScore * 100).toFixed(0)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Match Score
                      </Typography>
                    </Box>
                  </Box>

                  <Divider sx={{ mb: 3, borderColor: 'rgba(65, 77, 92, 0.3)' }} />

                  {/* Comparison Grid */}
                  <Grid container spacing={3} sx={{ mb: 3 }}>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <GlassCard variant="inset" hoverEffect="none">
                        <Box sx={{ p: 2 }}>
                          <Typography variant="subtitle2" color="text.secondary" mb={2}>
                            Bank Confirmation
                          </Typography>
                          <Stack spacing={1.5}>
                            <Box display="flex" justifyContent="space-between">
                              <Typography variant="body2" color="text.secondary">Trade Date</Typography>
                              <Typography variant="body2" fontWeight={500}>2024-01-15</Typography>
                            </Box>
                            <Box display="flex" justifyContent="space-between">
                              <Typography variant="body2" color="text.secondary">Amount</Typography>
                              <Typography variant="body2" fontWeight={500}>$1,250,000.00</Typography>
                            </Box>
                            <Box display="flex" justifyContent="space-between">
                              <Typography variant="body2" color="text.secondary">Currency</Typography>
                              <Typography variant="body2" fontWeight={500}>USD</Typography>
                            </Box>
                          </Stack>
                        </Box>
                      </GlassCard>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <GlassCard variant="inset" hoverEffect="none">
                        <Box sx={{ p: 2 }}>
                          <Typography variant="subtitle2" color="text.secondary" mb={2}>
                            Counterparty Confirmation
                          </Typography>
                          <Stack spacing={1.5}>
                            <Box display="flex" justifyContent="space-between">
                              <Typography variant="body2" color="text.secondary">Trade Date</Typography>
                              <Typography variant="body2" fontWeight={500}>2024-01-15</Typography>
                            </Box>
                            <Box display="flex" justifyContent="space-between">
                              <Typography variant="body2" color="text.secondary">Amount</Typography>
                              <Typography variant="body2" fontWeight={500}>$1,250,000.00</Typography>
                            </Box>
                            <Box display="flex" justifyContent="space-between">
                              <Typography variant="body2" color="text.secondary">Currency</Typography>
                              <Typography variant="body2" fontWeight={500}>USD</Typography>
                            </Box>
                          </Stack>
                        </Box>
                      </GlassCard>
                    </Grid>
                  </Grid>

                  {/* Rejection Reason */}
                  <Box sx={{ mb: 3 }}>
                    <TextField
                      fullWidth
                      label="Rejection Reason (optional)"
                      multiline
                      rows={2}
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      placeholder="Enter reason if rejecting this match..."
                      variant="outlined"
                    />
                  </Box>

                  {/* Action Buttons */}
                  <Box display="flex" gap={2} justifyContent="flex-end">
                    <GlassButton
                      variant="outlined"
                      onClick={() => handleDecision('REJECTED')}
                      loading={decisionMutation.isPending && rejectionReason !== ''}
                      glowColor={glowColors.error}
                      startIcon={<RejectIcon />}
                    >
                      Reject
                    </GlassButton>
                    <GlassButton
                      variant="contained"
                      onClick={() => handleDecision('APPROVED')}
                      loading={decisionMutation.isPending && rejectionReason === ''}
                      success={decisionMutation.isSuccess}
                      glowColor={glowColors.success}
                      startIcon={<ApproveIcon />}
                    >
                      Approve
                    </GlassButton>
                  </Box>
                </>
              )}
            </Box>
          </GlassCard>
        </Grid>
      </Grid>
    </MuiContainer>
  )
}
