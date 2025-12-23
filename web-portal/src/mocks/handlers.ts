import { http, HttpResponse } from 'msw'
import type { StrictRequest } from 'msw'

// Mock API handlers for development and testing
export const handlers = [
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
      sessionId,
      exceptions: []
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
