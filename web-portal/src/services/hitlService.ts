import { apiClient } from './api'
import type { HITLReview, MatchingResult } from '../types'

export interface HITLDecision {
  reviewId: string
  decision: 'APPROVED' | 'REJECTED'
  reason?: string
}

export const hitlService = {
  async getPendingReviews(): Promise<HITLReview[]> {
    return apiClient.get<HITLReview[]>('/hitl/pending')
  },

  async getReviewById(reviewId: string): Promise<HITLReview> {
    return apiClient.get<HITLReview>(`/hitl/${reviewId}`)
  },

  async submitDecision(decision: HITLDecision): Promise<MatchingResult> {
    return apiClient.post<MatchingResult>(`/hitl/${decision.reviewId}/decision`, {
      decision: decision.decision,
      reason: decision.reason,
    })
  },

  async getMatchingResults(params?: {
    startDate?: string
    endDate?: string
    classification?: string
  }): Promise<MatchingResult[]> {
    return apiClient.get<MatchingResult[]>('/matching/results', params)
  },
}
