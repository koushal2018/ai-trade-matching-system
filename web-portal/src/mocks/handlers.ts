import { http, HttpResponse } from 'msw'
import type { StrictRequest } from 'msw'

// Mock API handlers for development and testing
export const handlers = [
  // Dashboard: Agent Status
  http.get('/api/agents/status', () => {
    return HttpResponse.json([
      {
        agentId: 'agent-1',
        agentName: 'PDF Adapter',
        status: 'HEALTHY',
        activeTasks: 2,
        metrics: {
          latencyMs: 145,
          throughput: 120,
          successRate: 0.98,
          errorRate: 0.02,
          totalTokens: 15420,
          cycleCount: 89
        }
      },
      {
        agentId: 'agent-2',
        agentName: 'Trade Extraction',
        status: 'HEALTHY',
        activeTasks: 1,
        metrics: {
          latencyMs: 230,
          throughput: 85,
          successRate: 0.96,
          errorRate: 0.04,
          totalTokens: 28750,
          cycleCount: 156
        }
      },
      {
        agentId: 'agent-3',
        agentName: 'Trade Matching',
        status: 'DEGRADED',
        activeTasks: 3,
        metrics: {
          latencyMs: 890,
          throughput: 45,
          successRate: 0.89,
          errorRate: 0.11,
          totalTokens: 42100,
          cycleCount: 234
        }
      },
      {
        agentId: 'agent-4',
        agentName: 'Exception Handler',
        status: 'HEALTHY',
        activeTasks: 0,
        metrics: {
          latencyMs: 95,
          throughput: 200,
          successRate: 0.99,
          errorRate: 0.01,
          totalTokens: 8920,
          cycleCount: 67
        }
      },
      {
        agentId: 'agent-5',
        agentName: 'HITL Coordinator',
        status: 'HEALTHY',
        activeTasks: 1,
        metrics: {
          latencyMs: 180,
          throughput: 95,
          successRate: 0.97,
          errorRate: 0.03,
          totalTokens: 12340,
          cycleCount: 112
        }
      }
    ])
  }),

  // Dashboard: Processing Metrics
  http.get('/api/metrics/processing', () => {
    return HttpResponse.json({
      totalProcessed: 1247,
      matchedCount: 1156,
      unmatchedCount: 91,
      pendingCount: 23,
      errorCount: 12
    })
  }),

  // Dashboard: Matching Results
  http.get('/api/matching/results', () => {
    return HttpResponse.json([
      {
        sessionId: 'sess-abc123',
        tradeId: 'TRD-2024-0001',
        matchStatus: 'MATCHED',
        classification: 'MATCHED',
        confidenceScore: 98,
        matchScore: 0.98,
        decisionStatus: 'AUTO_MATCH',
        completedAt: new Date(Date.now() - 300000).toISOString(),
        createdAt: new Date(Date.now() - 350000).toISOString(),
        fieldComparisons: [],
        metadata: { processingTime: 12, agentVersion: '1.0.0' }
      },
      {
        sessionId: 'sess-def456',
        tradeId: 'TRD-2024-0002',
        matchStatus: 'PARTIAL_MATCH',
        classification: 'PROBABLE_MATCH',
        confidenceScore: 76,
        matchScore: 0.76,
        decisionStatus: 'ESCALATE',
        completedAt: new Date(Date.now() - 600000).toISOString(),
        createdAt: new Date(Date.now() - 650000).toISOString(),
        fieldComparisons: [],
        metadata: { processingTime: 18, agentVersion: '1.0.0' }
      },
      {
        sessionId: 'sess-ghi789',
        tradeId: 'TRD-2024-0003',
        matchStatus: 'MATCHED',
        classification: 'MATCHED',
        confidenceScore: 95,
        matchScore: 0.95,
        decisionStatus: 'AUTO_MATCH',
        completedAt: new Date(Date.now() - 900000).toISOString(),
        createdAt: new Date(Date.now() - 950000).toISOString(),
        fieldComparisons: [],
        metadata: { processingTime: 14, agentVersion: '1.0.0' }
      },
      {
        sessionId: 'sess-jkl012',
        tradeId: 'TRD-2024-0004',
        matchStatus: 'MISMATCHED',
        classification: 'REVIEW_REQUIRED',
        confidenceScore: 42,
        matchScore: 0.42,
        decisionStatus: 'ESCALATE',
        completedAt: new Date(Date.now() - 1200000).toISOString(),
        createdAt: new Date(Date.now() - 1250000).toISOString(),
        fieldComparisons: [],
        metadata: { processingTime: 22, agentVersion: '1.0.0' }
      },
      {
        sessionId: 'sess-mno345',
        tradeId: 'TRD-2024-0005',
        matchStatus: 'MATCHED',
        classification: 'MATCHED',
        confidenceScore: 99,
        matchScore: 0.99,
        decisionStatus: 'AUTO_MATCH',
        completedAt: new Date(Date.now() - 1500000).toISOString(),
        createdAt: new Date(Date.now() - 1550000).toISOString(),
        fieldComparisons: [],
        metadata: { processingTime: 10, agentVersion: '1.0.0' }
      },
      {
        sessionId: 'sess-pqr678',
        tradeId: 'TRD-2024-0006',
        matchStatus: 'MISMATCHED',
        classification: 'BREAK',
        confidenceScore: 28,
        matchScore: 0.28,
        decisionStatus: 'EXCEPTION',
        completedAt: new Date(Date.now() - 1800000).toISOString(),
        createdAt: new Date(Date.now() - 1850000).toISOString(),
        fieldComparisons: [],
        metadata: { processingTime: 25, agentVersion: '1.0.0' }
      },
      {
        sessionId: 'sess-stu901',
        tradeId: 'TRD-2024-0007',
        matchStatus: 'PARTIAL_MATCH',
        classification: 'PROBABLE_MATCH',
        confidenceScore: 82,
        matchScore: 0.82,
        decisionStatus: 'PENDING',
        completedAt: new Date(Date.now() - 2100000).toISOString(),
        createdAt: new Date(Date.now() - 2150000).toISOString(),
        fieldComparisons: [],
        metadata: { processingTime: 16, agentVersion: '1.0.0' }
      },
      {
        sessionId: 'sess-vwx234',
        tradeId: 'TRD-2024-0008',
        matchStatus: 'MATCHED',
        classification: 'MATCHED',
        confidenceScore: 97,
        matchScore: 0.97,
        decisionStatus: 'APPROVED',
        completedAt: new Date(Date.now() - 2400000).toISOString(),
        createdAt: new Date(Date.now() - 2450000).toISOString(),
        fieldComparisons: [],
        metadata: { processingTime: 11, agentVersion: '1.0.0' }
      }
    ])
  }),

  // HITL: Pending Reviews
  http.get('/api/hitl/reviews', () => {
    return HttpResponse.json([
      {
        reviewId: 'rev-001',
        tradeId: 'TRD-2024-1234',
        sessionId: 'sess-abc123',
        matchScore: 0.76,
        createdAt: new Date(Date.now() - 600000).toISOString()
      },
      {
        reviewId: 'rev-002',
        tradeId: 'TRD-2024-5678',
        sessionId: 'sess-def456',
        matchScore: 0.82,
        createdAt: new Date(Date.now() - 1200000).toISOString()
      },
      {
        reviewId: 'rev-003',
        tradeId: 'TRD-2024-9012',
        sessionId: 'sess-ghi789',
        matchScore: 0.68,
        createdAt: new Date(Date.now() - 1800000).toISOString()
      }
    ])
  }),

  // HITL: Submit Decision
  http.post('/api/hitl/decision', async ({ request }: { request: StrictRequest<any> }) => {
    const body = await request.json()
    return HttpResponse.json({
      success: true,
      reviewId: body.reviewId,
      decision: body.decision
    })
  }),
  // Upload endpoint
  http.post('/api/upload', async ({ request }: { request: StrictRequest<any> }) => {
    const formData = await request.formData()
    const file = formData.get('file')
    const sourceType = formData.get('sourceType')

    if (!file || !sourceType) {
      return HttpResponse.json(
        { error: 'Missing required fields', message: 'File and sourceType are required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      uploadId: `upload-${Date.now()}`,
      s3Uri: `s3://trade-matching-system-agentcore-production/${sourceType}/${file}`,
      status: 'success',
      sessionId: `session-${Date.now()}`,
      traceId: `trace-${Date.now()}`
    })
  }),

  // Workflow status endpoint
  http.get('/api/workflow/:sessionId/status', ({ params }: { params: Record<string, string> }) => {
    const { sessionId } = params

    return HttpResponse.json({
      sessionId,
      pdfAdapter: {
        status: 'success',
        activity: 'Extracted text from 2 pages',
        startedAt: new Date(Date.now() - 30000).toISOString(),
        completedAt: new Date(Date.now() - 25000).toISOString(),
        duration: 5,
        subSteps: [
          { title: 'Convert PDF to images', status: 'success', description: 'Converted 2 pages' },
          { title: 'Extract text', status: 'success', description: 'Extracted 1,234 characters' }
        ]
      },
      tradeExtraction: {
        status: 'in-progress',
        activity: 'Extracting structured trade data...',
        startedAt: new Date(Date.now() - 20000).toISOString(),
        subSteps: [
          { title: 'Parse trade fields', status: 'in-progress', description: 'Processing...' }
        ]
      },
      tradeMatching: {
        status: 'pending',
        activity: 'Waiting for trade extraction to complete'
      },
      exceptionManagement: {
        status: 'pending',
        activity: 'No exceptions detected'
      }
    })
  }),

  // Invoke matching endpoint
  http.post('/api/workflow/:sessionId/invoke-matching', ({ params }: { params: Record<string, string> }) => {
    const { sessionId } = params

    return HttpResponse.json({
      invocationId: `invoke-${Date.now()}`,
      sessionId,
      status: 'initiated'
    })
  }),

  // Matching result endpoint
  http.get('/api/workflow/:sessionId/result', ({ params }: { params: Record<string, string> }) => {
    const { sessionId } = params

    return HttpResponse.json({
      sessionId,
      matchStatus: 'MATCHED',
      confidenceScore: 92,
      completedAt: new Date().toISOString(),
      fieldComparisons: [
        {
          fieldName: 'Trade ID',
          bankValue: 'TRD-2024-001',
          counterpartyValue: 'TRD-2024-001',
          match: true,
          confidence: 100
        },
        {
          fieldName: 'Notional Amount',
          bankValue: '1000000',
          counterpartyValue: '1000000',
          match: true,
          confidence: 100
        },
        {
          fieldName: 'Trade Date',
          bankValue: '2024-12-23',
          counterpartyValue: '2024-12-23',
          match: true,
          confidence: 100
        },
        {
          fieldName: 'Maturity Date',
          bankValue: '2025-12-23',
          counterpartyValue: '2025-12-23',
          match: true,
          confidence: 100
        }
      ],
      metadata: {
        processingTime: 15,
        agentVersion: '1.0.0'
      }
    })
  }),

  // Exceptions endpoint
  http.get('/api/workflow/:sessionId/exceptions', ({ params }: { params: Record<string, string> }) => {
    const { sessionId } = params

    return HttpResponse.json({
      exceptions: [
        {
          id: 'exc-1',
          sessionId,
          agentName: 'PDF Adapter Agent',
          severity: 'warning',
          message: 'Low confidence in text extraction from page 2',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          recoverable: true,
          details: {
            page: 2,
            confidence: 0.75
          }
        },
        {
          id: 'exc-2', 
          sessionId,
          agentName: 'Trade Extraction Agent',
          severity: 'info',
          message: 'Used fallback parsing for currency field',
          timestamp: new Date(Date.now() - 240000).toISOString(),
          recoverable: false,
          details: {
            field: 'currency',
            fallbackValue: 'USD'
          }
        }
      ]
    })
  }),

  // Feedback endpoint
  http.post('/api/feedback', async ({ request }: { request: StrictRequest<any> }) => {
    await request.json()

    return HttpResponse.json({
      success: true,
      message: 'Feedback recorded',
      feedbackId: `feedback-${Date.now()}`
    })
  })
]
