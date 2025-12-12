# Exception Handling Module

This module provides comprehensive exception management capabilities including classification, severity scoring, triage, delegation, and reinforcement learning.

## Overview

The Exception Handling module is designed to handle exceptions in the AI Trade Matching System with intelligent triage and continuous learning capabilities. It implements:

1. **Exception Classification**: Categorizes exceptions based on type and reason codes
2. **Severity Scoring**: Computes severity scores (0.0-1.0) based on multiple factors
3. **Triage System**: Determines routing, priority, and SLA for exceptions
4. **Delegation**: Routes exceptions to appropriate handlers and tracks lifecycle
5. **Reinforcement Learning**: Learns optimal routing policies from historical outcomes

## Components

### 1. Classifier (`classifier.py`)

Classifies exceptions into triage categories:
- `AUTO_RESOLVABLE`: Can be automatically resolved
- `OPERATIONAL_ISSUE`: Requires operational review
- `DATA_QUALITY_ISSUE`: Data quality problems
- `SYSTEM_ISSUE`: System-level problems
- `COMPLIANCE_ISSUE`: Compliance/security concerns

**Usage:**
```python
from exception_handling.classifier import classify_exception

classification = classify_exception(exception)
print(f"Classification: {classification.value}")
```

### 2. Scorer (`scorer.py`)

Computes severity scores based on:
- Base scores from reason codes
- Match score adjustments
- Retry count adjustments
- RL-based historical patterns

**Severity Levels:**
- `LOW`: Score < 0.3
- `MEDIUM`: Score 0.3-0.6
- `HIGH`: Score 0.6-0.8
- `CRITICAL`: Score >= 0.8

**Usage:**
```python
from exception_handling.scorer import compute_severity_score, get_severity_level

score = compute_severity_score(exception)
level = get_severity_level(score)
print(f"Severity: {level.value} (Score: {score})")
```

### 3. Triage (`triage.py`)

Determines routing, priority, and SLA:

**Routing Destinations:**
- `AUTO_RESOLVE`: System auto-resolution
- `OPS_DESK`: Operations desk
- `SENIOR_OPS`: Senior operations team
- `COMPLIANCE`: Compliance team
- `ENGINEERING`: Engineering team

**Priority Levels:** 1 (highest) to 5 (lowest)

**SLA Hours:**
- CRITICAL: 2 hours
- HIGH: 4 hours
- MEDIUM: 8 hours
- LOW: 24 hours

**Usage:**
```python
from exception_handling.triage import triage_exception

triage_result = triage_exception(exception, severity_score)
print(f"Routing: {triage_result.routing.value}")
print(f"Priority: {triage_result.priority}")
print(f"SLA: {triage_result.sla_hours} hours")
```

### 4. Delegation (`delegation.py`)

Delegates exceptions to appropriate handlers:
- Sends to SQS queues
- Creates tracking records in DynamoDB
- Sends notifications to assigned teams

**Usage:**
```python
from exception_handling.delegation import delegate_exception

delegation_result = delegate_exception(exception, triage_result)
print(f"Delegated to: {delegation_result.assigned_to}")
print(f"Tracking ID: {delegation_result.tracking_id}")
```

### 5. RL Handler (`rl_handler.py`)

Reinforcement learning for optimal routing:
- Q-learning algorithm
- Supervised learning from human decisions
- Experience replay buffer
- Model persistence

**Usage:**
```python
from exception_handling.rl_handler import RLExceptionHandler

rl_handler = RLExceptionHandler()

# Record episode
rl_handler.record_episode(exception_id, state, action, context)

# Update with resolution
rl_handler.update_with_resolution(exception_id, resolution_outcome)

# Predict best action
action = rl_handler.predict(state)
```

## Exception Management Agent

The `ExceptionManagementAgent` orchestrates all components:

```python
from agents.exception_management_agent import ExceptionManagementAgent

# Create agent
agent = ExceptionManagementAgent(
    region_name="us-east-1",
    exception_queue_name="exception-events"
)

# Register agent
agent.register_agent()

# Process single event
result = agent.process_exception_event(event_message)

# Run continuously
agent.run()
```

## Event-Driven Architecture

The agent subscribes to SQS queues:
- **Input**: `exception-events` queue
- **Output**: `ops-desk-queue`, `senior-ops-queue`, `compliance-queue`, `engineering-queue`

**Event Message Format:**
```json
{
  "exception_id": "exc_123",
  "exception_type": "MATCHING_EXCEPTION",
  "event_type": "MATCHING_EXCEPTION",
  "trade_id": "GCS382857",
  "agent_id": "trade_matching_agent",
  "reason_codes": ["NOTIONAL_MISMATCH"],
  "error_message": "Notional mismatch detected",
  "match_score": 0.65,
  "context": {...},
  "timestamp": "2025-01-15T10:30:00Z",
  "correlation_id": "corr_abc"
}
```

## Reason Code Taxonomy

The system uses standardized reason codes:

**Matching Codes:**
- `NOTIONAL_MISMATCH`: Notional amounts differ
- `DATE_MISMATCH`: Trade dates differ
- `COUNTERPARTY_MISMATCH`: Counterparty names don't match
- `CURRENCY_MISMATCH`: Currency codes don't match

**Data Error Codes:**
- `MISSING_REQUIRED_FIELD`: Required field missing
- `INVALID_FIELD_FORMAT`: Invalid field format
- `MISPLACED_TRADE`: Trade in wrong table

**Processing Codes:**
- `OCR_QUALITY_LOW`: Low OCR quality
- `PDF_CORRUPTED`: Corrupted PDF
- `EXTRACTION_TIMEOUT`: Extraction timeout

**System Codes:**
- `SERVICE_UNAVAILABLE`: Service unavailable
- `TIMEOUT`: Operation timeout
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded

## Reinforcement Learning

The RL handler learns optimal routing policies:

**Reward Function:**
- +1.0: Resolved within SLA, correct routing
- +0.5: Resolved within SLA, suboptimal routing
- -0.5: Resolved late, correct routing
- -1.0: Resolved late, incorrect routing

**Learning Process:**
1. Record state-action pairs when exceptions are triaged
2. Compute rewards when exceptions are resolved
3. Update Q-table using Q-learning
4. Learn from human decisions via supervised learning

**Model Persistence:**
```python
# Save model
rl_handler.save_model("rl_model.pkl")

# Load model
rl_handler.load_model("rl_model.pkl")
```

## DynamoDB Tables

### ExceptionsTable

Tracks exception lifecycle:
- `exception_id` (Primary Key)
- `tracking_id`
- `severity`, `severity_score`
- `routing`, `priority`, `sla_hours`
- `resolution_status`
- `assigned_to`, `assigned_at`
- `resolved_at`, `resolution_notes`

### AgentRegistry

Registers the agent:
- `agent_id` (Primary Key)
- `agent_name`: "Exception Management Agent"
- `agent_type`: "EXCEPTION_HANDLER"
- `capabilities`: ["exception_classification", "severity_scoring", "triage", "delegation", "rl_learning"]
- `event_subscriptions`: ["exception-events"]
- `event_publications`: ["ops-desk-queue", "senior-ops-queue", ...]

## Testing

Run tests:
```bash
pytest src/latest_trade_matching_agent/exception_handling/test_exception_handling.py -v
```

## Requirements

Validates requirements:
- 8.1: Log all errors with full context
- 8.2: Rank exceptions by severity
- 8.3: Delegate to appropriate handlers
- 8.4: Track exception lifecycle
- 8.5: Learn from resolution patterns

## Configuration

Environment variables:
- `AWS_DEFAULT_REGION`: AWS region (default: us-east-1)
- `EXCEPTION_QUEUE_NAME`: Exception events queue name
- `RL_MODEL_PATH`: Path to RL model file (optional)

## Example Workflow

```python
# 1. Create exception record
exception = ExceptionRecord(
    exception_id="exc_123",
    exception_type=ExceptionType.MATCHING_EXCEPTION,
    event_type="MATCHING_EXCEPTION",
    agent_id="trade_matching_agent",
    reason_codes=["NOTIONAL_MISMATCH"],
    error_message="Notional mismatch detected",
    match_score=0.65
)

# 2. Classify
classification = classify_exception(exception)

# 3. Score
severity_score = compute_severity_score(exception)

# 4. Triage
triage_result = triage_exception(exception, severity_score)

# 5. Delegate
delegation_result = delegate_exception(exception, triage_result)

# 6. Record for RL
rl_handler.record_episode(
    exception.exception_id,
    exception.to_state_vector(),
    triage_result.routing.value,
    {}
)

# 7. Later: Update with resolution
resolution = ResolutionOutcome(
    exception_id=exception.exception_id,
    resolved_at=datetime.utcnow(),
    resolution_time_hours=2.5,
    resolved_within_sla=True,
    routing_was_correct=True
)
rl_handler.update_with_resolution(exception.exception_id, resolution)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              Exception Management Agent                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Classifier  │  │    Scorer    │  │   Triage     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                   ┌────────▼────────┐                       │
│                   │   Delegation    │                       │
│                   └────────┬────────┘                       │
│                            │                                │
│                   ┌────────▼────────┐                       │
│                   │   RL Handler    │                       │
│                   └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  OPS_DESK    │    │  SENIOR_OPS  │    │  COMPLIANCE  │
│    Queue     │    │    Queue     │    │    Queue     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Performance

- Classification: < 10ms
- Scoring: < 20ms
- Triage: < 50ms
- Delegation: < 100ms
- Total processing: < 200ms per exception

## Future Enhancements

1. Deep learning models for classification
2. Multi-armed bandit algorithms for routing
3. Anomaly detection for exception patterns
4. Automated root cause analysis
5. Integration with external ticketing systems
