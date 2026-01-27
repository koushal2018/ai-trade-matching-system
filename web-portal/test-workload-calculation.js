/**
 * Standalone validation script for workload calculation logic
 * Task 7.1: Implement workload calculation logic in Dashboard
 * Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9
 */

// Workload calculation function (extracted from Dashboard.tsx)
function calculateWorkload(agents) {
  // Handle edge case: no agents data available
  if (!agents || !Array.isArray(agents)) {
    return 'N/A'
  }

  // Backend already filters for ACTIVE deployment_status
  const activeAgentsList = agents

  // Handle edge case: no active agents (zero capacity)
  if (activeAgentsList.length === 0) {
    return 0
  }

  // Calculate sum of activeTasks for HEALTHY agents only
  const totalActiveTasks = activeAgentsList
    .filter(agent => agent.status === 'HEALTHY')
    .reduce((sum, agent) => sum + (agent.activeTasks || 0), 0)

  // Calculate total capacity: count of ACTIVE agents * 10 (max concurrent tasks per agent)
  const totalCapacity = activeAgentsList.length * 10

  // Apply formula: min(100, round((totalTasks / capacity) * 100))
  const calculatedWorkload = Math.min(100, Math.round((totalActiveTasks / totalCapacity) * 100))

  return calculatedWorkload
}

// Test cases
const testCases = [
  {
    name: 'No active tasks (Requirement 4.5)',
    agents: [
      { status: 'HEALTHY', activeTasks: 0 },
      { status: 'HEALTHY', activeTasks: 0 },
      { status: 'HEALTHY', activeTasks: 0 },
    ],
    expected: 0
  },
  {
    name: 'At capacity (Requirement 4.6)',
    agents: [
      { status: 'HEALTHY', activeTasks: 10 },
      { status: 'HEALTHY', activeTasks: 10 },
      { status: 'HEALTHY', activeTasks: 10 },
    ],
    expected: 100
  },
  {
    name: 'Over capacity - capped at 100% (Requirement 4.9)',
    agents: [
      { status: 'HEALTHY', activeTasks: 15 },
      { status: 'HEALTHY', activeTasks: 12 },
      { status: 'HEALTHY', activeTasks: 11 },
    ],
    expected: 100
  },
  {
    name: 'Only HEALTHY agents counted (Requirement 4.2)',
    agents: [
      { status: 'HEALTHY', activeTasks: 5 },
      { status: 'HEALTHY', activeTasks: 3 },
      { status: 'DEGRADED', activeTasks: 10 }, // Not counted
      { status: 'OFFLINE', activeTasks: 8 }, // Not counted
    ],
    expected: 20 // (8 / 40) * 100 = 20%
  },
  {
    name: 'Capacity calculation (Requirements 4.3, 4.4)',
    agents: [
      { status: 'HEALTHY', activeTasks: 3 },
      { status: 'HEALTHY', activeTasks: 2 },
      { status: 'HEALTHY', activeTasks: 1 },
    ],
    expected: 20 // (6 / 30) * 100 = 20%
  },
  {
    name: 'Rounding (Requirement 4.8)',
    agents: [
      { status: 'HEALTHY', activeTasks: 1 },
      { status: 'HEALTHY', activeTasks: 1 },
      { status: 'HEALTHY', activeTasks: 1 },
    ],
    expected: 10 // (3 / 30) * 100 = 10%
  },
  {
    name: 'No agents data - N/A (Requirement 4.7)',
    agents: undefined,
    expected: 'N/A'
  },
  {
    name: 'Empty agents array (Requirement 4.7)',
    agents: [],
    expected: 0
  },
  {
    name: 'Realistic scenario',
    agents: [
      { status: 'HEALTHY', activeTasks: 4 },
      { status: 'HEALTHY', activeTasks: 2 },
      { status: 'DEGRADED', activeTasks: 7 },
      { status: 'HEALTHY', activeTasks: 3 },
      { status: 'HEALTHY', activeTasks: 1 },
      { status: 'OFFLINE', activeTasks: 0 },
    ],
    expected: 17 // (10 / 60) * 100 = 16.67% ≈ 17%
  },
  {
    name: 'Missing activeTasks field',
    agents: [
      { status: 'HEALTHY', activeTasks: 5 },
      { status: 'HEALTHY' }, // Missing activeTasks
      { status: 'HEALTHY', activeTasks: 3 },
    ],
    expected: 27 // (8 / 30) * 100 = 26.67% ≈ 27%
  }
]

// Run tests
console.log('Testing Workload Calculation Logic\n')
console.log('=' .repeat(60))

let passed = 0
let failed = 0

testCases.forEach((testCase, index) => {
  const result = calculateWorkload(testCase.agents)
  const success = result === testCase.expected
  
  if (success) {
    passed++
    console.log(`✓ Test ${index + 1}: ${testCase.name}`)
    console.log(`  Expected: ${testCase.expected}, Got: ${result}`)
  } else {
    failed++
    console.log(`✗ Test ${index + 1}: ${testCase.name}`)
    console.log(`  Expected: ${testCase.expected}, Got: ${result}`)
  }
  console.log()
})

console.log('=' .repeat(60))
console.log(`Results: ${passed} passed, ${failed} failed out of ${testCases.length} tests`)

if (failed === 0) {
  console.log('\n✓ All tests passed!')
  process.exit(0)
} else {
  console.log('\n✗ Some tests failed!')
  process.exit(1)
}
