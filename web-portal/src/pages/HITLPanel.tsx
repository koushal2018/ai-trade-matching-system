import { useState, useEffect } from 'react'
import {
  Typography,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Chip,
  Box,
  CircularProgress,
} from '@mui/material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import TradeComparisonCard from '../components/hitl/TradeComparisonCard'
import { hitlService, HITLDecision } from '../services/hitlService'
import { wsService } from '../services/websocket'
import type { HITLReview, WebSocketMessage } from '../types'

export default function HITLPanel() {
  const [selectedReview, setSelectedReview] = useState<HITLReview | null>(null)
  const queryClient = useQueryClient()

  const { data: pendingReviews, isLoading, refetch } = useQuery<HITLReview[]>({
    queryKey: ['pendingReviews'],
    queryFn: hitlService.getPendingReviews,
    refetchInterval: 30000,
  })

  const decisionMutation = useMutation({
    mutationFn: (decision: HITLDecision) => hitlService.submitDecision(decision),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingReviews'] })
      setSelectedReview(null)
    },
  })

  useEffect(() => {
    wsService.connect()
    const unsub = wsService.subscribe('HITL_REQUIRED', (_msg: WebSocketMessage) => {
      refetch()
    })
    return () => unsub()
  }, [refetch])

  const handleDecision = (decision: 'APPROVED' | 'REJECTED', reason?: string) => {
    if (selectedReview) {
      decisionMutation.mutate({
        reviewId: selectedReview.reviewId,
        decision,
        reason,
      })
    }
  }


  return (
    <>
      <Typography variant="h4" gutterBottom>
        Human-in-the-Loop Reviews
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Pending Reviews ({pendingReviews?.length || 0})
              </Typography>
              {isLoading ? (
                <Box display="flex" justifyContent="center" py={4}>
                  <CircularProgress />
                </Box>
              ) : (
                <List>
                  {pendingReviews?.map((review) => (
                    <ListItem key={review.reviewId} disablePadding>
                      <ListItemButton
                        selected={selectedReview?.reviewId === review.reviewId}
                        onClick={() => setSelectedReview(review)}
                      >
                        <ListItemText
                          primary={`Trade: ${review.tradeId}`}
                          secondary={`Score: ${(review.matchScore * 100).toFixed(0)}%`}
                        />
                        <Chip
                          size="small"
                          label={review.status}
                          color={review.status === 'PENDING' ? 'warning' : 'default'}
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                  {(!pendingReviews || pendingReviews.length === 0) && (
                    <Typography color="text.secondary" align="center" py={2}>
                      No pending reviews
                    </Typography>
                  )}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          {selectedReview ? (
            <TradeComparisonCard
              review={selectedReview}
              onApprove={(reason) => handleDecision('APPROVED', reason)}
              onReject={(reason) => handleDecision('REJECTED', reason)}
              isSubmitting={decisionMutation.isPending}
            />
          ) : (
            <Card>
              <CardContent>
                <Typography color="text.secondary" align="center" py={8}>
                  Select a review from the list to view details
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </>
  )
}
