/**
 * ExceptionSection Example
 * 
 * This file demonstrates the usage of the ExceptionSection component
 * and can be used for manual testing and verification.
 */

import { ExceptionSection } from './ExceptionSection'

/**
 * Example 1: Basic usage with session ID
 */
export const BasicExample = () => {
  return <ExceptionSection sessionId="session-123" />
}

/**
 * Example 2: Usage in a page context
 */
export const PageExample = () => {
  const sessionId = 'test-session-456'

  return (
    <div style={{ padding: '20px' }}>
      <h1>Trade Matching Workflow</h1>
      <ExceptionSection sessionId={sessionId} />
    </div>
  )
}

/**
 * Mock data for testing (to be used with MSW)
 * 
 * Example exceptions that would be returned from the API:
 */
export const mockExceptions = [
  {
    id: 'exc-1',
    sessionId: 'session-123',
    agentName: 'PDF Adapter Agent',
    severity: 'error' as const,
    message: 'Failed to extract text from PDF',
    timestamp: '2024-12-23T10:00:00Z',
    recoverable: true,
    details: {
      fileName: 'bank_confirmation.pdf',
      errorCode: 'PDF_EXTRACTION_FAILED',
    },
  },
  {
    id: 'exc-2',
    sessionId: 'session-123',
    agentName: 'Trade Extraction Agent',
    severity: 'warning' as const,
    message: 'Low confidence in extracted trade date',
    timestamp: '2024-12-23T10:05:00Z',
    recoverable: false,
    details: {
      field: 'tradeDate',
      confidence: 0.65,
    },
  },
  {
    id: 'exc-3',
    sessionId: 'session-123',
    agentName: 'Trade Matching Agent',
    severity: 'info' as const,
    message: 'Manual review recommended for partial match',
    timestamp: '2024-12-23T10:10:00Z',
    recoverable: false,
    details: {
      matchConfidence: 0.75,
      mismatchedFields: ['notionalAmount'],
    },
  },
]

/**
 * Component Features Demonstrated:
 * 
 * 1. Chronological Ordering (Requirement 9.8)
 *    - Exceptions are sorted oldest first
 *    - Timestamps: 10:00, 10:05, 10:10
 * 
 * 2. Severity-Based Alert Types (Requirement 9.11)
 *    - error → Alert type="error" (red)
 *    - warning → Alert type="warning" (yellow)
 *    - info → Alert type="info" (blue)
 * 
 * 3. Message Formatting (Requirement 9.2)
 *    - Format: "{message} - [{agentName}]"
 *    - Example: "Failed to extract text from PDF - [PDF Adapter Agent]"
 * 
 * 4. Retry Functionality (Requirement 9.3)
 *    - Retry button shown for recoverable errors
 *    - Button disabled during retry operation
 * 
 * 5. Exception Counter (Requirement 9.1)
 *    - Header shows count: "Exceptions and Errors (3)"
 * 
 * 6. Empty State
 *    - Displays friendly message when no exceptions
 * 
 * 7. Loading State
 *    - Shows spinner while fetching exceptions
 * 
 * 8. Error State
 *    - Shows error alert with retry button if fetch fails
 */

/**
 * Integration with MSW (Mock Service Worker)
 * 
 * Add this handler to your MSW handlers:
 * 
 * ```typescript
 * import { http, HttpResponse } from 'msw'
 * import { mockExceptions } from './components/exceptions/ExceptionSection.example'
 * 
 * export const handlers = [
 *   http.get('/api/workflow/:sessionId/exceptions', () => {
 *     return HttpResponse.json({
 *       exceptions: mockExceptions
 *     })
 *   })
 * ]
 * ```
 */

/**
 * Usage in TradeMatchingPage:
 * 
 * ```typescript
 * import { ExceptionSection } from '@/components/exceptions'
 * 
 * export const TradeMatchingPage = () => {
 *   const [sessionId, setSessionId] = useState<string | null>(null)
 *   
 *   return (
 *     <ContentLayout>
 *       <SpaceBetween size="l">
 *         {sessionId && (
 *           <>
 *             <UploadSection />
 *             <WorkflowIdentifierSection sessionId={sessionId} />
 *             <AgentProcessingSection sessionId={sessionId} />
 *             <MatchResultSection sessionId={sessionId} />
 *             <ExceptionSection sessionId={sessionId} />
 *           </>
 *         )}
 *       </SpaceBetween>
 *     </ContentLayout>
 *   )
 * }
 * ```
 */
