/**
 * Simple verification script for active agent count calculation
 * This tests the logic without needing to run the full test suite
 */

// Simulate the agent filtering logic from Dashboard.tsx
function calculateActiveAgents(agents) {
  if (!agents) return 0
  return agents.filter(agent => agent.status === 'HEALTHY').length
}

// Test cases
const testCases = [
  {
    name: 'All HEALTHY agents',
    agents: [
      { agentId: '1', status: 'HEALTHY' },
      { agentId: '2', status: 'HEALTHY' },
      { agentId: '3', status: 'HEALTHY' },
      { agentId: '4', status: 'HEALTHY' },
      { agentId: '5', status: 'HEALTHY' },
      { agentId: '6', status: 'HEALTHY' },
    ],
    expected: 6,
  },
  {
    name: 'Mixed statuses',
    agents: [
      { agentId: '1', status: 'HEALTHY' },
      { agentId: '2', status: 'DEGRADED' },
      { agentId: '3', status: 'OFFLINE' },
      { agentId: '4', status: 'HEALTHY' },
      { agentId: '5', status: 'UNHEALTHY' },
      { agentId: '6', status: 'HEALTHY' },
    ],
    expected: 3,
  },
  {
    name: 'Only DEGRADED agents',
    agents: [
      { agentId: '1', status: 'DEGRADED' },
      { agentId: '2', status: 'DEGRADED' },
      { agentId: '3', status: 'DEGRADED' },
    ],
    expected: 0,
  },
  {
    name: 'Empty agent list',
    agents: [],
    expected: 0,
  },
  {
    name: 'Undefined agents',
    agents: undefined,
    expected: 0,
  },
  {
    name: 'Null agents',
    agents: null,
    expected: 0,
  },
]

// Run tests
console.log('Testing active agent count calculation...\n')

let passed = 0
let failed = 0

testCases.forEach(({ name, agents, expected }) => {
  const result = calculateActiveAgents(agents)
  const success = result === expected
  
  if (success) {
    console.log(`✓ ${name}: ${result} (expected ${expected})`)
    passed++
  } else {
    console.log(`✗ ${name}: ${result} (expected ${expected})`)
    failed++
  }
})

console.log(`\n${passed} passed, ${failed} failed`)

if (failed === 0) {
  console.log('\n✓ All tests passed!')
  process.exit(0)
} else {
  console.log('\n✗ Some tests failed')
  process.exit(1)
}
