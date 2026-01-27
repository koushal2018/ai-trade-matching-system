# Bug Report - Trade Matching System Web Portal

**Date:** January 26, 2026
**Environment:** Development (localhost)
**Reported By:** User Testing

---

## Critical Issues

### 1. Real-Time Monitor - Activity Stream Not Working ❌
**Severity:** HIGH
**Page:** Real-Time Monitor (`/monitor`)
**Status:** In Progress

**Description:**
The Real-Time Monitor displays "Waiting for events..." but never shows any activity even when processing sessions are running.

**Expected Behavior:**
- Should display real-time activity as agents process files
- Should show agent status updates (PDF Adapter, Trade Extraction, Trade Matching)
- Activity stream should update automatically with Live toggle ON

**Actual Behavior:**
- Empty state showing "Waiting for events..."
- No activity displayed even with active processing sessions
- WebSocket connection established but not receiving broadcasts

**Root Cause:**
- Frontend connects to WebSocket but doesn't subscribe to specific sessions
- Backend only polls DynamoDB when a session ID is provided
- Missing session subscription mechanism

**Fix in Progress:**
- Added `/api/workflow/recent` endpoint to fetch active sessions
- Modified Real-Time Monitor to subscribe to active sessions via WebSocket
- Added `send()` method to WebSocket service
- Backend WebSocket manager handles SUBSCRIBE messages

**Testing Required:**
- Upload a new PDF file
- Monitor should auto-subscribe to the new session
- Activity stream should show status updates every 2 seconds

---

### 2. Audit Trail Not Working ❌
**Severity:** HIGH
**Page:** Audit Trail (`/audit`)

**Description:**
Audit Trail page shows "No audit records found" with no data displayed.

**Expected Behavior:**
- Should display audit logs of all system activities
- Should show user actions, agent invocations, status changes
- Should support filtering and pagination

**Actual Behavior:**
- Empty state with no records
- Appears to be querying data but returning no results

**Possible Causes:**
- Audit logging not implemented in backend
- Audit DynamoDB table empty or not being written to
- Frontend querying wrong table or incorrect parameters

**Investigation Needed:**
- Check if audit events are being written to DynamoDB
- Verify audit table name and schema
- Review audit API endpoint implementation

---

## High Priority Issues

### 3. Dashboard - Active Agents Showing 0 ⚠️
**Severity:** MEDIUM
**Page:** Dashboard (`/`)

**Description:**
Dashboard displays "0" for active agents count despite 6 healthy agents showing in the agent status table below.

**Expected Behavior:**
- Active agent counter should show "6" (matching the number of HEALTHY agents)
- Counter should update automatically as agent status changes

**Actual Behavior:**
- Shows "0" active agents
- Agent status table correctly shows 6 HEALTHY agents

**Root Cause:**
- Agent counter calculation logic incorrect
- Likely filtering by wrong status field or using outdated data

**Fix Required:**
- Review Dashboard component agent count calculation
- Ensure it counts agents with `status: "HEALTHY"`
- Match the logic used in the agent status table

---

### 4. Dashboard - Workload Showing 100% ⚠️
**Severity:** MEDIUM
**Page:** Dashboard (`/`)

**Description:**
Workload percentage shows "100%" which doesn't appear to be accurate based on system activity.

**Expected Behavior:**
- Workload should show actual percentage based on:
  - Active tasks vs. capacity
  - Processing queue length
  - Agent utilization metrics

**Actual Behavior:**
- Always shows 100%
- Doesn't change even when no processing is happening

**Root Cause:**
- Hardcoded value or incorrect calculation
- Not using actual metrics from agents

**Fix Required:**
- Calculate workload from agent metrics
- Use formula: `(active_tasks / total_capacity) * 100`
- Default to 0% when no active processing

---

### 5. Dashboard - Showing Unverified Agents ⚠️
**Severity:** MEDIUM
**Page:** Dashboard (`/`)

**Description:**
Dashboard displays two agents marked as "Unverified" that should not be shown to users.

**Expected Behavior:**
- Only show verified/deployed agents
- Filter out agents without proper deployment status

**Actual Behavior:**
- Shows 2 unverified agents in the list
- These agents appear to be test/development agents

**Fix Required:**
- Add filter to agent query: `deployment_status === 'ACTIVE'`
- Or filter out agents with `verified: false`
- Update agent registry cleanup to remove test agents

---

### 6. Dashboard - Matching Status Wrong ⚠️
**Severity:** MEDIUM
**Page:** Dashboard (`/`)

**Description:**
Matching status display shows incorrect values or misleading information.

**Expected Behavior:**
- Show accurate count of:
  - Matched trades
  - Unmatched trades
  - Pending matches
  - Exceptions requiring review

**Actual Behavior:**
- Status values don't match actual data
- Numbers appear inconsistent

**Investigation Needed:**
- Verify data source (which DynamoDB table)
- Check status field mapping
- Review filtering logic

---

### 7. Dashboard - Recent Results Data Source Unclear ⚠️
**Severity:** LOW
**Page:** Dashboard (`/`)

**Description:**
"Recent Results" section is pulling data from unclear source. Values don't match processing history.

**Expected Behavior:**
- Should show recent matching results from processing_status table
- Should be sorted by completion time (most recent first)
- Should link to actual result details

**Actual Behavior:**
- Data source unclear
- Results don't correspond to actual processing sessions

**Investigation Needed:**
- Identify which API endpoint/table is being used
- Verify data is from correct source
- Add proper data transformation

---

### 8. Matching Queue - Incorrect Status Values ⚠️
**Severity:** MEDIUM
**Page:** Matching Queue

**Description:**
Matching Queue table displays incorrect or inconsistent status values for queue items.

**Expected Behavior:**
- Status should reflect actual processing state:
  - `pending`: Waiting to be processed
  - `in-progress`: Currently processing
  - `completed`: Successfully matched
  - `failed`: Error during processing
  - `requires_review`: Needs HITL review

**Actual Behavior:**
- Status values appear incorrect
- May be using wrong status field or old data

**Investigation Needed:**
- Check DynamoDB table and field names
- Verify status mapping in frontend
- Ensure status updates are propagating correctly

---

### 9. Agent Status - Wrong Status Indicators ⚠️
**Severity:** LOW
**Page:** Multiple pages (Dashboard, Real-Time Monitor)

**Description:**
Agent health status indicators (HEALTHY, DEGRADED, OFFLINE) showing incorrect colors or wrong status.

**Expected Behavior:**
- HEALTHY: Green indicator, agent responding
- DEGRADED: Yellow indicator, high latency or error rate
- OFFLINE: Red indicator, no heartbeat in last 5 minutes

**Actual Behavior:**
- Status colors or labels may be incorrect
- Inconsistent between different pages

**Fix Required:**
- Standardize status determination logic
- Use consistent color scheme across all pages
- Update status based on latest heartbeat timestamp

---

## Summary

**Total Issues:** 9
**Critical:** 2 (Real-Time Monitor, Audit Trail)
**High Priority:** 7 (Dashboard metrics, Matching Queue, Agent Status)

**Priority Fix Order:**
1. Real-Time Monitor activity stream (in progress)
2. Audit Trail functionality
3. Dashboard active agent counter
4. Dashboard workload percentage
5. Remove unverified agents
6. Fix matching status display
7. Fix matching queue status values
8. Clarify recent results data source
9. Standardize agent status indicators

---

## Testing Checklist

After fixes are deployed:

- [ ] Upload a PDF file and verify Real-Time Monitor shows activity
- [ ] Check Audit Trail shows audit records
- [ ] Verify Dashboard active agent count is correct (should show 6)
- [ ] Check Dashboard workload shows accurate percentage
- [ ] Confirm no unverified agents displayed
- [ ] Verify matching status values are correct
- [ ] Test Matching Queue status accuracy
- [ ] Review Recent Results data source
- [ ] Check agent status indicators across all pages
- [ ] Verify all WebSocket connections remain stable
- [ ] Test with multiple concurrent sessions

---

## Technical Notes

**Backend:**
- API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws
- Region: us-east-1
- DynamoDB Tables:
  - `trade-matching-system-agent-registry-production`
  - `trade-matching-system-processing-status`
  - `trade-matching-system-audit-logs` (needs verification)

**Frontend:**
- URL: http://localhost:3000
- Framework: React + TypeScript + Vite
- State Management: React Query
- WebSocket Service: Custom implementation

**Current Work:**
- Fixed agent health display (all 6 agents showing HEALTHY)
- Fixed file upload with CORS configuration
- Fixed agent invocation after upload (orchestrator ARN updated)
- In progress: Real-Time Monitor WebSocket subscription

---

**Last Updated:** January 26, 2026, 8:15 PM
