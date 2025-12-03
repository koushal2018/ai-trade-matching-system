# Data Models for AgentCore Trade Matching System

This directory contains all Pydantic data models used across the AgentCore Trade Matching System. These models provide type safety, validation, and serialization for the event-driven architecture.

## Overview

The models are organized into six main modules:

1. **adapter.py** - Canonical adapter output schemas
2. **trade.py** - Trade data models
3. **matching.py** - Matching result models
4. **exception.py** - Exception and triage models
5. **audit.py** - Audit trail models
6. **events.py** - Event message schemas

## Module Details

### 1. adapter.py - Canonical Adapter Output

**Purpose**: Standardized output format for all adapter agents (PDF, Chat, Email, Voice).

**Key Models**:
- `CanonicalAdapterOutput`: Base schema for all adapters

**Features**:
- Supports multiple adapter types (PDF, CHAT, EMAIL, VOICE)
- Enforces 300 DPI for PDF processing (requirement 5.1)
- Extensible metadata fields
- S3 location tracking
- Distributed tracing support

**Requirements**: 3.2, 5.1, 5.2, 5.3

### 2. trade.py - Canonical Trade Model

**Purpose**: Standardized trade data representation with 30+ fields.

**Key Models**:
- `CanonicalTradeModel`: Complete trade data model

**Features**:
- 7 mandatory fields (Trade_ID, TRADE_SOURCE, trade_date, notional, currency, counterparty, product_type)
- 30+ optional fields for comprehensive trade representation
- DynamoDB format conversion (`to_dynamodb_format()`, `from_dynamodb_format()`)
- Field validation (currency codes, date formats, positive amounts)
- Support for various derivative products (swaps, options, forwards)

**Requirements**: 6.1, 6.2, 6.3, 6.4

### 3. matching.py - Matching Results

**Purpose**: Trade matching results with classification and scoring.

**Key Models**:
- `MatchClassification`: Enum for match types (MATCHED, PROBABLE_MATCH, REVIEW_REQUIRED, BREAK, DATA_ERROR)
- `DecisionStatus`: Workflow routing (AUTO_MATCH, ESCALATE, EXCEPTION)
- `FieldDifference`: Detailed field-level differences
- `MatchingResult`: Complete matching result

**Features**:
- Match score (0.0 to 1.0)
- Decision thresholds (≥0.85: AUTO_MATCH, 0.70-0.84: ESCALATE, <0.70: EXCEPTION)
- Reason codes for mismatches
- HITL requirement tracking
- Validation ensures decision status aligns with match score

**Requirements**: 7.1, 7.2, 7.3

### 4. exception.py - Exception Management

**Purpose**: Exception handling, triage, and routing with RL support.

**Key Models**:
- `ExceptionType`: Types of exceptions
- `SeverityLevel`: LOW, MEDIUM, HIGH, CRITICAL
- `RoutingDestination`: AUTO_RESOLVE, OPS_DESK, SENIOR_OPS, COMPLIANCE, ENGINEERING
- `ExceptionRecord`: Complete exception details
- `TriageResult`: Triage decision with severity and routing
- `ReasonCodeTaxonomy`: Standardized reason codes
- `DelegationResult`: Delegation tracking
- `ResolutionOutcome`: Resolution data for RL learning

**Features**:
- Severity scoring (0.0 to 1.0)
- SLA tracking
- State vector generation for RL
- Priority assignment
- Validation ensures severity matches score

**Requirements**: 8.1, 8.2, 8.3, 8.4, 8.5

### 5. audit.py - Audit Trail

**Purpose**: Immutable audit records with tamper-evidence.

**Key Models**:
- `ActionType`: Types of auditable actions
- `ActionOutcome`: SUCCESS, FAILURE, PARTIAL_SUCCESS, PENDING
- `AuditRecord`: Immutable audit record with SHA-256 hash
- `AuditTrailQuery`: Query parameters for filtering
- `AuditTrailExport`: Export configuration
- `ExportFormat`: JSON, CSV, XML

**Features**:
- SHA-256 hash computation for tamper-evidence
- Blockchain-style previous hash linking
- Hash verification (`verify_hash()`)
- Multiple export formats (JSON, CSV, XML)
- Filtering by date, agent, action type
- Correlation ID for distributed tracing

**Requirements**: 10.1, 10.2, 10.3, 10.4, 10.5

### 6. events.py - Event Messages

**Purpose**: Standardized SQS event messages for event-driven architecture.

**Key Models**:
- `EventTaxonomy`: Centralized event type definitions (22 event types)
- `StandardEventMessage`: Base event schema
- Specific event types (DocumentUploadedEvent, PDFProcessedEvent, etc.)
- `EventFactory`: Factory for creating events

**Features**:
- Correlation ID for distributed tracing
- Event type validation
- SQS serialization/deserialization
- Extensible payload and metadata
- Type-safe event creation

**Event Categories**:
- Document Processing (DOCUMENT_UPLOADED, PDF_PROCESSED, OCR_COMPLETED)
- Extraction (EXTRACTION_STARTED, TRADE_EXTRACTED, EXTRACTION_FAILED)
- Matching (MATCHING_STARTED, MATCH_COMPLETED, MATCHING_EXCEPTION)
- Exception (EXCEPTION_RAISED, EXCEPTION_TRIAGED, EXCEPTION_RESOLVED)
- HITL (HITL_REQUIRED, HITL_DECISION_MADE)
- Orchestration (SLA_VIOLATED, COMPLIANCE_CHECK_FAILED, CONTROL_COMMAND_ISSUED)

**Requirements**: 3.1, 12.4

## Usage Examples

### Creating a Canonical Adapter Output

```python
from models import CanonicalAdapterOutput

output = CanonicalAdapterOutput(
    adapter_type="PDF",
    document_id="doc_123",
    source_type="BANK",
    extracted_text="Trade confirmation text...",
    metadata={
        "page_count": 3,
        "dpi": 300,
        "ocr_confidence": 0.95
    },
    s3_location="s3://bucket/extracted/BANK/doc_123.json",
    correlation_id="corr_abc"
)
```

### Creating a Trade Model

```python
from models import CanonicalTradeModel

trade = CanonicalTradeModel(
    Trade_ID="GCS382857",
    TRADE_SOURCE="COUNTERPARTY",
    trade_date="2024-10-15",
    notional=1000000.00,
    currency="USD",
    counterparty="Goldman Sachs",
    product_type="SWAP"
)

# Convert to DynamoDB format
dynamodb_item = trade.to_dynamodb_format()
```

### Creating a Matching Result

```python
from models import MatchingResult, MatchClassification, DecisionStatus

result = MatchingResult(
    trade_id="GCS382857",
    classification=MatchClassification.MATCHED,
    match_score=0.95,
    decision_status=DecisionStatus.AUTO_MATCH,
    reason_codes=[],
    requires_hitl=False
)
```

### Creating an Audit Record

```python
from models import AuditRecord, ActionType, ActionOutcome

audit = AuditRecord(
    record_id="audit_001",
    agent_id="pdf_adapter_agent",
    action_type=ActionType.PDF_PROCESSED,
    resource_id="doc_456",
    outcome=ActionOutcome.SUCCESS,
    details={"page_count": 5, "dpi": 300}
)

# Finalize to compute hash
audit.finalize()

# Verify hash
assert audit.verify_hash()
```

### Creating an Event Message

```python
from models import StandardEventMessage, EventTaxonomy

event = StandardEventMessage(
    event_id="evt_123",
    event_type=EventTaxonomy.PDF_PROCESSED,
    source_agent="pdf_adapter_agent",
    correlation_id="corr_abc",
    payload={
        "document_id": "doc_456",
        "page_count": 5
    }
)

# Serialize for SQS
sqs_message = event.to_sqs_message()
```

## Testing

Run the test suite to validate all models:

```bash
python src/latest_trade_matching_agent/models/test_models.py
```

The test suite covers:
- Model creation and validation
- Field validators
- Serialization/deserialization
- DynamoDB format conversion
- Hash computation and verification
- Export formats (JSON, CSV, XML)
- SQS message handling

## Validation Rules

### Canonical Adapter Output
- PDF adapters must include `page_count` and `dpi` in metadata
- DPI must be exactly 300 (requirement 5.1)
- Extracted text cannot be empty

### Canonical Trade Model
- Notional must be positive
- Currency codes must be 3 characters (ISO 4217)
- Date fields must follow YYYY-MM-DD format
- TRADE_SOURCE must be BANK or COUNTERPARTY

### Matching Result
- Match score must be 0.0 to 1.0
- Decision status must align with match score:
  - ≥0.85: AUTO_MATCH
  - 0.70-0.84: ESCALATE
  - <0.70: EXCEPTION
- ESCALATE status requires `requires_hitl=True`

### Triage Result
- Severity must align with severity score:
  - <0.3: LOW
  - 0.3-0.6: MEDIUM
  - 0.6-0.8: HIGH
  - ≥0.8: CRITICAL
- Priority must align with severity (CRITICAL=1, HIGH≤2)

### Audit Record
- Immutable hash is computed via SHA-256
- Hash verification detects tampering
- Previous hash creates blockchain-style chain

### Event Message
- Event type must be from EventTaxonomy
- Correlation ID required for distributed tracing

## Integration with AgentCore

These models are designed to work seamlessly with:

- **AgentCore Runtime**: Agents use these models for input/output
- **AgentCore Memory**: Models are stored in semantic and event memory
- **AgentCore Gateway**: Models are passed through MCP tools
- **AgentCore Observability**: Correlation IDs enable distributed tracing
- **Amazon SQS**: Events are serialized for queue messages
- **Amazon DynamoDB**: Trades are stored in typed format
- **Amazon S3**: Models are serialized to JSON for storage

## Next Steps

After implementing these models, the next tasks are:

1. **Task 3**: Implement registry and taxonomy system
2. **Task 4**: Implement PDF Adapter Agent
3. **Task 5**: Implement Trade Data Extraction Agent
4. **Task 6**: Implement Trade Matching Agent
5. **Task 7**: Implement Exception Management Agent

All agents will use these models for consistent data handling across the system.
