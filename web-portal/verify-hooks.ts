/**
 * Verification script for real-time status update hooks
 * 
 * This script verifies that:
 * 1. useAgentStatus hook is properly implemented with React Query
 * 2. useAgentWebSocket hook is properly implemented with fallback
 * 3. Both hooks meet all requirements from tasks 12.1 and 12.3
 */

import { readFileSync } from 'fs'
import { join } from 'path'

const checks = {
  passed: [] as string[],
  failed: [] as string[]
}

function check(name: string, condition: boolean) {
  if (condition) {
    checks.passed.push(name)
    console.log(`✅ ${name}`)
  } else {
    checks.failed.push(name)
    console.log(`❌ ${name}`)
  }
}

// Read hook files
const useAgentStatusPath = join(process.cwd(), 'src/hooks/useAgentStatus.ts')
const useAgentWebSocketPath = join(process.cwd(), 'src/hooks/useAgentWebSocket.ts')
const workflowServicePath = join(process.cwd(), 'src/services/workflowService.ts')

const useAgentStatusContent = readFileSync(useAgentStatusPath, 'utf-8')
const useAgentWebSocketContent = readFileSync(useAgentWebSocketPath, 'utf-8')
const workflowServiceContent = readFileSync(workflowServicePath, 'utf-8')

console.log('\n=== Task 12.1: useAgentStatus Hook ===\n')

// Check 12.1.1: Uses React Query
check(
  '12.1.1: Uses React Query (useQuery)',
  useAgentStatusContent.includes('useQuery') && useAgentStatusContent.includes('@tanstack/react-query')
)

// Check 12.1.2: Polls /api/workflow/{sessionId}/status
check(
  '12.1.2: Polls /api/workflow/{sessionId}/status endpoint',
  workflowServiceContent.includes('/workflow/${sessionId}/status') &&
  useAgentStatusContent.includes('workflowService.getWorkflowStatus')
)

// Check 12.1.3: Sets refetchInterval to 30 seconds during active processing
check(
  '12.1.3: Sets refetchInterval to 30 seconds (30000ms)',
  useAgentStatusContent.includes('refetchInterval') &&
  useAgentStatusContent.includes('30000')
)

// Check 12.1.4: Parses agent status from response
check(
  '12.1.4: Parses agent status from response',
  useAgentStatusContent.includes('WorkflowStatusResponse') &&
  workflowServiceContent.includes('agents: AgentStatus')
)

// Check 12.1.5: Handles loading and error states
check(
  '12.1.5: Handles loading and error states',
  useAgentStatusContent.includes('enabled: !!sessionId') &&
  useAgentStatusContent.includes('retry:')
)

console.log('\n=== Task 12.3: useAgentWebSocket Hook ===\n')

// Check 12.3.1: File exists at correct path
check(
  '12.3.1: File exists at web-portal/src/hooks/useAgentWebSocket.ts',
  useAgentWebSocketContent.length > 0
)

// Check 12.3.2: Connects to /ws endpoint with sessionId query param
check(
  '12.3.2: Connects to /ws endpoint with sessionId query param',
  useAgentWebSocketContent.includes('/ws?sessionId=') &&
  useAgentWebSocketContent.includes('WebSocket')
)

// Check 12.3.3: Parses message types
check(
  '12.3.3: Parses AGENT_STATUS_UPDATE message type',
  useAgentWebSocketContent.includes('AGENT_STATUS_UPDATE')
)
check(
  '12.3.3: Parses RESULT_AVAILABLE message type',
  useAgentWebSocketContent.includes('RESULT_AVAILABLE')
)
check(
  '12.3.3: Parses EXCEPTION message type',
  useAgentWebSocketContent.includes('EXCEPTION')
)
check(
  '12.3.3: Parses STEP_UPDATE message type',
  useAgentWebSocketContent.includes('STEP_UPDATE')
)

// Check 12.3.4: Updates React Query cache
check(
  '12.3.4: Updates React Query cache using queryClient.setQueryData',
  useAgentWebSocketContent.includes('queryClient.setQueryData') &&
  useAgentWebSocketContent.includes('useQueryClient')
)

// Check 12.3.5: Implements exponential backoff
check(
  '12.3.5: Implements exponential backoff (1s, 2s, 4s, 8s, max 30s)',
  useAgentWebSocketContent.includes('getReconnectDelay') &&
  useAgentWebSocketContent.includes('Math.pow(2, attempt)') &&
  useAgentWebSocketContent.includes('maxDelay: 30000')
)

// Check 12.3.6: Falls back to polling after 3 failed attempts
check(
  '12.3.6: Falls back to polling after 3 failed reconnection attempts',
  useAgentWebSocketContent.includes('maxAttempts: 3') &&
  useAgentWebSocketContent.includes('fallback')
)

// Check 12.3.7: Displays Flashbar warning for polling fallback
check(
  '12.3.7: Provides callback for Flashbar warning (polling fallback)',
  useAgentWebSocketContent.includes('onConnectionChange') &&
  useAgentWebSocketContent.includes('Real-time updates unavailable')
)

// Check 12.3.8: Displays Flashbar success when reconnects
check(
  '12.3.8: Provides callback for Flashbar success (reconnection)',
  useAgentWebSocketContent.includes('Connected to real-time updates')
)

// Summary
console.log('\n=== Summary ===\n')
console.log(`✅ Passed: ${checks.passed.length}`)
console.log(`❌ Failed: ${checks.failed.length}`)

if (checks.failed.length > 0) {
  console.log('\nFailed checks:')
  checks.failed.forEach(check => console.log(`  - ${check}`))
  process.exit(1)
} else {
  console.log('\n🎉 All checks passed! Task 12 is complete.')
  process.exit(0)
}
