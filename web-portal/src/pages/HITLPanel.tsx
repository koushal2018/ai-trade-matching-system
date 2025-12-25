import { useState, useEffect } from 'react'
import {
  ContentLayout,
  Header,
  Container,
  SpaceBetween,
  Box,
  Alert,
  Spinner,
} from '@cloudscape-design/components'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
    <ContentLayout
      header={
        <Header
          variant="h1"
          description="Review and approve trade matches requiring human verification"
        >
          Human-in-the-Loop Reviews
        </Header>
      }
    >
      <SpaceBetween size="l">
        <Alert type="info" header="HITL Panel Under Construction">
          The HITL panel is being migrated to CloudScape Design System. Full functionality coming soon.
        </Alert>
        
        {isLoading ? (
          <Container>
            <Box textAlign="center" padding="xxl">
              <Spinner size="large" />
              <Box variant="p" color="text-body-secondary" margin={{ top: 's' }}>
                Loading pending reviews...
              </Box>
            </Box>
          </Container>
        ) : (
          <Container header={<Header variant="h2">Pending Reviews ({pendingReviews?.length || 0})</Header>}>
            {(!pendingReviews || pendingReviews.length === 0) ? (
              <Box textAlign="center" padding="xxl">
                <Box variant="p" color="text-body-secondary">
                  No pending reviews
                </Box>
              </Box>
            ) : (
              <Box>
                {pendingReviews.map((review) => (
                  <Box key={review.reviewId} padding="s">
                    Trade: {review.tradeId} - Score: {(review.matchScore * 100).toFixed(0)}%
                  </Box>
                ))}
              </Box>
            )}
          </Container>
        )}
      </SpaceBetween>
    </ContentLayout>
  )
}
