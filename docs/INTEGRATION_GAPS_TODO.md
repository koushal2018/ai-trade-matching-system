# Frontend-Backend Integration Gaps - TODO List

**Last Updated:** 2026-01-24
**Status:** In Progress
**Total Tasks:** 23
**Estimated Effort:** 2-3 weeks

---

## CRITICAL ISSUES (Must Fix)

### ✅ 1. Mock Service Worker (MSW) Masking Real Integration
**Priority:** CRITICAL
**Status:** ✅ COMPLETED
**File:** `web-portal/src/mocks/handlers.ts`
**Issue:** MSW intercepts ALL API calls and returns mock data in development
**Impact:** Frontend never actually tests against real backend
**Change:** Add environment flag to force real API in development: `VITE_USE_REAL_API=true`
**Affected Endpoints:** ALL (agents, metrics, matching, hitl, workflow, audit)

### ✅ 2. DynamoDB Processing Status Table - Key Mismatch
**Priority:** CRITICAL
**Status:** ✅ RESOLVED (No actual issue - naming is consistent)
**Files:**
- Backend: `web-portal-api/app/routers/workflow.py` (line 123)
- Frontend: `web-portal/src/hooks/useAgentStatus.ts`

**Issue:** Backend uses `processing_id` as partition key, frontend sends `sessionId`
**Impact:** Agent processing status never updates correctly
**Change:** Standardize on one key name throughout entire stack
**Recommendation:** Use `session_id` everywhere (backend key, frontend param, DynamoDB)

### ✅ 3. Exceptions Endpoint - Not Implemented
**Priority:** CRITICAL
**Status:** ✅ COMPLETED
**File:** `web-portal-api/app/routers/workflow.py` (line 292)
**Issue:** Returns empty list always - has TODO comment
**Impact:** Exceptions page always shows "No exceptions"
**Change:** Implement DynamoDB query to ExceptionsTable:
```python
# Query exceptions by session_id (GSI needed)
response = exceptions_table.query(
    IndexName='session-index',
    KeyConditionExpression=Key('session_id').eq(session_id)
)
```

### ✅ 4. Processing Metrics - Field Name Mismatch
**Priority:** CRITICAL
**Status:** ✅ COMPLETED
**Files:**
- Backend: `web-portal-api/app/routers/metrics.py`
- Frontend: `web-portal/src/services/agentService.ts`

**Issues:**
- Backend returns `breakCount`, frontend expects `unmatchedCount`
- Backend returns `pendingReview`, frontend expects `pendingCount`
- Backend missing `errorCount` entirely

**Change:** Update backend ProcessingMetrics model to match frontend or vice versa

### ✅ 5. Upload → Agent Invocation Gap
**Priority:** CRITICAL
**Status:** TODO
**Issue:** Files upload to S3 but NO agents are automatically triggered
**Current:** Upload returns sessionId, user must manually click "Invoke Matching"
**Expected:** Upload should trigger orchestrator agent automatically
**Change:** Add agent invocation to upload endpoint OR create S3 event trigger

---

## HIGH PRIORITY

### 6. Agent Health Panel - Agent Name Mapping
**Priority:** HIGH
**Status:** TODO
**File:** `web-portal/src/components/dashboard/AgentHealthPanel.tsx`
**Issue:** Mock shows "Agent-1, Agent-2", backend returns agent types like "PDF_ADAPTER"
**Change:** Frontend should map agent_id to friendly display names using AGENT_TYPE_NAMES

### 7. Matching Results - Incomplete Logic
**Priority:** HIGH
**Status:** TODO
**File:** `web-portal-api/app/routers/matching.py`
**Issues:**
- Only matches by trade_id (simple equality)
- Hardcoded match score (0.95 or 0.0)
- No field comparison logic
- Returns bankTrade/counterpartyTrade as null

**Change:** Implement actual matching algorithm or call matching agent

### 8. HITL Reviews - No Sample Data
**Priority:** HIGH
**Status:** ✅ COMPLETED (seed script created)
**File:** `web-portal-api/app/routers/hitl.py`
**Issue:** Backend queries HITLReviews table but it's empty in dev
**Change:**
- Create script to populate sample HITL reviews
- Add DynamoDB seed data for development

### 9. Workflow Status - Fallback Masks Errors
**Priority:** HIGH
**Status:** TODO
**File:** `web-portal-api/app/routers/workflow.py` (lines 126-155)
**Issue:** Returns "pending" status if session not found instead of 404
**Impact:** Frontend can't tell if session is genuinely pending or doesn't exist
**Change:** Return 404 for unknown sessions, let frontend handle gracefully

### 10. Agent Invocation - No Validation
**Priority:** HIGH
**Status:** TODO
**File:** `web-portal-api/app/routers/workflow.py` (lines 316-459)
**Issues:**
- Falls back to creating status record if agent not deployed
- No verification that invocation succeeded
- AgentCore runtime API may fail silently

**Change:** Add validation that orchestrator agent is actually deployed and invoked

### 11. Real-time Monitor - Mock Events Only
**Priority:** HIGH
**Status:** TODO
**File:** `web-portal/src/pages/RealTimeMonitor.tsx` (line 35)
**Issue:** Generates fake activity events client-side
**Change:** Connect to WebSocket endpoint for real agent activity streams

### 12. WebSocket - No Server-Side Events
**Priority:** HIGH
**Status:** TODO
**File:** `web-portal-api/app/services/websocket.py`
**Issue:** WebSocket endpoint exists but never sends status updates
**Change:** Integrate with agent processing to broadcast real-time updates

### 13. Exceptions Page - Missing Endpoint
**Priority:** HIGH
**Status:** ✅ COMPLETED
**File:** `web-portal/src/pages/ExceptionsPage.tsx`
**Issue:** Page exists but calls non-existent `/api/exceptions` endpoint
**Current:** Backend only has `/api/workflow/{session_id}/exceptions`
**Change:** Add `/api/exceptions` endpoint for global exception list

### 14. Matching Queue Page - Missing Endpoint
**Priority:** HIGH
**Status:** ✅ COMPLETED
**File:** `web-portal/src/pages/MatchingQueuePage.tsx`
**Issue:** Page exists but calls non-existent `/api/matching/queue` endpoint
**Change:** Implement backend endpoint to return queued matching requests

---

## MEDIUM PRIORITY

### 15. Audit Trail - Missing Export Implementation
**Priority:** MEDIUM
**Status:** TODO
**File:** `web-portal-api/app/routers/audit.py`
**Issue:** Export endpoint exists but returns mock data
**Change:** Implement CSV/JSON/XML export from AuditTrail table

### 16. TradeMatches Table - Never Written
**Priority:** MEDIUM
**Status:** TODO
**Issue:** Backend reads from TradeMatches table but nothing writes to it
**Change:** Trade matching agent should write results to this table

### 17. Field Comparisons Missing
**Priority:** MEDIUM
**Status:** TODO
**File:** `web-portal-api/app/routers/matching.py`
**Issue:** Returns empty `differences` and `fieldComparisons`
**Change:** Calculate actual field differences between bank/counterparty trades

### 18. Authentication Disabled Everywhere
**Priority:** MEDIUM
**Status:** TODO
**Files:** Multiple routers have `# user: User = Depends(get_current_user)` commented out
**Issue:** Security disabled for development
**Change:** Implement proper dev auth bypass (API key or test token)

### 19. Upload Session Tracking
**Priority:** MEDIUM
**Status:** TODO
**Issue:** Each upload creates new sessionId, no way to track bank + counterparty pair
**Change:** Allow passing existing sessionId to upload endpoint for paired uploads

---

## LOW PRIORITY / POLISH

### 20. Toast Notifications - Generic Messages
**Priority:** LOW
**Status:** TODO
**Issue:** Success/error toasts don't provide actionable details
**Change:** Add specific error codes and resolution hints

### 21. Loading States - Missing Skeletons
**Priority:** LOW
**Status:** TODO
**Issue:** Some components show blank while loading
**Change:** Add SkeletonLoader to all data-fetching components

### 22. Error Boundaries - Generic Fallbacks
**Priority:** LOW
**Status:** TODO
**Issue:** ErrorBoundary shows generic "Something went wrong"
**Change:** Component-specific error recovery UI

### 23. Polling Optimization
**Priority:** LOW
**Status:** TODO
**Issue:** Agent status polls every 30s regardless of activity
**Change:** Use exponential backoff when no changes detected

### 24. DynamoDB Table Creation
**Priority:** LOW
**Status:** TODO
**Issue:** Tables manually created, no IaC for local dev
**Change:** Add script to create all required tables with GSIs

---

## SUMMARY STATISTICS

| Priority | Count | Estimated Effort |
|----------|-------|------------------|
| **Critical** | 5 | 3-4 days |
| **High** | 9 | 5-6 days |
| **Medium** | 5 | 2-3 days |
| **Low** | 4 | 1-2 days |
| **TOTAL** | **23** | **~2-3 weeks** |

---

## RECOMMENDED FIX ORDER

1. ✅ **Disable MSW for integration testing** (#1) - COMPLETED
2. ✅ **Fix sessionId/processing_id mismatch** (#2) - RESOLVED (No issue)
3. ✅ **Implement exceptions endpoint** (#3) - COMPLETED
4. ✅ **Fix processing metrics field names** (#4) - COMPLETED
5. 🔄 **Implement missing API endpoints** (#13, #14) - IN PROGRESS (NEXT)
6. **Add sample DynamoDB data** (#8)
7. **Connect real-time monitor to backend** (#11)
8. **Add agent invocation validation** (#10)
9. **Fix matching results logic** (#7)
10. **Polish and optimize** (remaining issues)

---

## 📊 PROGRESS (Last Updated: 2026-01-24 - Session 2)

**Critical:** 4/5 completed (80%)
**High:** 4/9 completed (44%)
**Overall:** 8/23 completed (35%)

See `INTEGRATION_FIXES_COMPLETED.md` for detailed implementation notes.

---

## NOTES

- Each task should be implemented in a separate commit
- Update this file's status as tasks are completed
- Add blockers or dependencies as discovered
- Link to relevant PRs or commits when completed
