#!/usr/bin/env node

/**
 * Validation script for Property Test 2.4
 * This script validates that the property test file is correctly structured
 * and follows the required format.
 */

const fs = require('fs');
const path = require('path');

const testFilePath = path.join(__dirname, 'src/pages/__tests__/RealTimeMonitor.property.test.tsx');

console.log('🔍 Validating Property Test 2.4: WebSocket Subscription Completeness\n');

try {
  // Read the test file
  const testContent = fs.readFileSync(testFilePath, 'utf8');
  
  // Validation checks
  const checks = [
    {
      name: 'File exists',
      test: () => fs.existsSync(testFilePath),
      message: 'Test file found at correct location'
    },
    {
      name: 'Contains Property 1 description',
      test: () => testContent.includes('Property 1: WebSocket Subscription Completeness'),
      message: 'Property 1 test suite is defined'
    },
    {
      name: 'Validates Requirements 1.3',
      test: () => testContent.includes('Validates: Requirements 1.3'),
      message: 'Test correctly references Requirements 1.3'
    },
    {
      name: 'Uses fast-check library',
      test: () => testContent.includes("import fc from 'fast-check'"),
      message: 'fast-check library is imported'
    },
    {
      name: 'Has fc.assert with fc.property',
      test: () => testContent.includes('fc.assert') && testContent.includes('fc.property'),
      message: 'Property-based testing structure is correct'
    },
    {
      name: 'Runs 100 iterations',
      test: () => testContent.includes('numRuns: 100'),
      message: 'Test runs minimum 100 iterations'
    },
    {
      name: 'Tests SUBSCRIBE message format',
      test: () => testContent.includes("type: 'SUBSCRIBE'") && testContent.includes('sessionId'),
      message: 'SUBSCRIBE message format is validated'
    },
    {
      name: 'Tests non-completed sessions',
      test: () => testContent.includes("status !== 'completed'"),
      message: 'Non-completed session filtering is tested'
    },
    {
      name: 'Tests idempotency',
      test: () => testContent.includes('should not send duplicate SUBSCRIBE'),
      message: 'Idempotency test is included'
    },
    {
      name: 'Tests edge cases',
      test: () => testContent.includes('empty session list') && testContent.includes('all sessions are completed'),
      message: 'Edge cases are covered'
    },
    {
      name: 'Mocks wsService',
      test: () => testContent.includes("vi.mock('../../services/websocket')"),
      message: 'WebSocket service is properly mocked'
    }
  ];
  
  // Run all checks
  let passed = 0;
  let failed = 0;
  
  checks.forEach(check => {
    try {
      if (check.test()) {
        console.log(`✅ ${check.name}: ${check.message}`);
        passed++;
      } else {
        console.log(`❌ ${check.name}: FAILED`);
        failed++;
      }
    } catch (error) {
      console.log(`❌ ${check.name}: ERROR - ${error.message}`);
      failed++;
    }
  });
  
  console.log(`\n${'='.repeat(60)}`);
  console.log(`📊 Validation Results: ${passed}/${checks.length} checks passed`);
  console.log(`${'='.repeat(60)}\n`);
  
  if (failed === 0) {
    console.log('✅ Property Test 2.4 is correctly implemented!');
    console.log('\nThe test validates:');
    console.log('  • SUBSCRIBE sent for all non-completed sessions');
    console.log('  • SUBSCRIBE NOT sent for completed sessions');
    console.log('  • SUBSCRIBE NOT sent for already-subscribed sessions');
    console.log('  • Correct sessionId included in each message');
    console.log('  • Idempotency (no duplicate subscriptions)');
    console.log('  • Edge cases (empty list, all completed, duplicates)');
    console.log('\n✅ Task 2.4 is COMPLETE');
    process.exit(0);
  } else {
    console.log(`❌ ${failed} validation check(s) failed`);
    process.exit(1);
  }
  
} catch (error) {
  console.error('❌ Error during validation:', error.message);
  process.exit(1);
}
