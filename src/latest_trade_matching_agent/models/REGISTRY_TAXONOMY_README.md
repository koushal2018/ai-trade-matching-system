# Registry and Taxonomy System

This document describes the registry and taxonomy system implemented for the AgentCore migration (Task 3).

## Overview

The registry and taxonomy system provides:

1. **Agent Registry**: Centralized tracking and management of all agents
2. **Workflow Taxonomy**: Hierarchical structure of workflows and their components
3. **Event Taxonomy**: Standardized event types and validation
4. **Reason Code Taxonomy**: Comprehensive reason codes for exceptions and mismatches

## Components

### 1. Agent Registry (`registry.py`)

The agent registry provides centralized management of all agents in the system.

#### Models

**AgentRegistryEntry**
- Represents a single agent in the registry
- Includes agent metadata, capabilities, event subscriptions/publications
- Supports DynamoDB serialization/deserialization
- Validates: Requirements 4.1, 4.3

**ScalingConfig**
- Configuration for agent auto-scaling
- Defines min/max instances, target queue depth, scale thresholds

**AgentRegistry**
- Main registry class for agent lifecycle management
- Operations:
  - `register_agent()`: Register new agent
  - `update_agent_status()`: Update agent health and metrics
  - `get_agent_by_capability()`: Find agents by capability
  - `list_active_agents()`: Get all active agents
  - `get_agent()`: Get specific agent by ID
  - `deregister_agent()`: Remove agent from registry

#### Usage Example

```python
from src.latest_trade_matching_agent.models.registry import (
    AgentRegistryEntry,
    AgentRegistry,
    ScalingConfig
)

# Create agent entry
entry = AgentRegistryEntry(
    agent_id="pdf_adapter_001",
    agent_name="PDF Adapter Agent",
    agent_type="ADAPTER",
    version="1.0.0",
    capabilities=["pdf_processing", "ocr_extraction"],
    event_subscriptions=["document-upload-events"],
    event_publications=["extraction-events"],
    sla_targets={"latency_ms": 10000.0, "throughput": 100.0},
    deployment_status="ACTIVE"
)

# Initialize registry
registry = AgentRegistry(table_name="AgentRegistry", region_name="us-east-1")

# Register agent
result = registry.register_agent(entry)

# Update agent status
registry.update_agent_status(
    agent_id="pdf_adapter_001",
    deployment_status="ACTIVE",
    metrics={"latency_ms": 8500.0, "throughput": 120.0},
    last_heartbeat=datetime.utcnow()
)

# Find agents by capability
pdf_agents = registry.get_agent_by_capability("pdf_processing")
```

### 2. Workflow Taxonomy (`taxonomy.py`)

Hierarchical taxonomy of workflows and their components.

#### Models

**WorkflowNode**
- Represents a node in the workflow hierarchy
- Includes parent/child relationships, agent type, event triggers/outputs
- Validates: Requirements 3.1

**WorkflowTaxonomy**
- Complete hierarchical workflow structure
- Operations:
  - `get_workflow()`: Get workflow by ID
  - `get_children()`: Get child workflows
  - `get_root_workflows()`: Get root-level workflows

**TaxonomyLoader**
- Loads/saves taxonomy from/to S3
- Operations:
  - `save_taxonomy()`: Save to S3
  - `load_taxonomy()`: Load from S3
  - `initialize_default_taxonomy()`: Create and save default

#### Workflow Structure

```
Trade Processing Workflow
├── Document Ingestion
│   ├── PDF Upload
│   ├── Chat Message
│   ├── Email Receipt
│   └── Voice Transcription
├── Data Extraction
│   ├── OCR Processing
│   ├── LLM Extraction
│   └── Field Validation
├── Trade Matching
│   ├── Fuzzy Matching
│   ├── Score Computation
│   └── Classification
└── Exception Handling
    ├── Triage
    ├── Delegation
    └── Resolution Tracking
```

#### Usage Example

```python
from src.latest_trade_matching_agent.models.taxonomy import (
    create_default_taxonomy,
    TaxonomyLoader
)

# Create default taxonomy
taxonomy = create_default_taxonomy()

# Get root workflows
root_workflows = taxonomy.get_root_workflows()

# Get specific workflow
trade_processing = taxonomy.get_workflow("trade_processing")

# Get children
children = taxonomy.get_children("trade_processing")

# Save to S3
loader = TaxonomyLoader(bucket_name="my-bucket")
loader.save_taxonomy(taxonomy)

# Load from S3
loaded_taxonomy = loader.load_taxonomy()
```

### 3. Event Taxonomy (`events.py`)

Standardized event types and validation functions.

#### Event Types

The `EventTaxonomy` class defines 22+ standardized event types:

**Document Processing Events**
- DOCUMENT_UPLOADED
- PDF_PROCESSED
- OCR_COMPLETED

**Extraction Events**
- EXTRACTION_STARTED
- TRADE_EXTRACTED
- EXTRACTION_FAILED

**Matching Events**
- MATCHING_STARTED
- MATCH_COMPLETED
- MATCHING_EXCEPTION

**Exception Events**
- EXCEPTION_RAISED
- EXCEPTION_TRIAGED
- EXCEPTION_DELEGATED
- EXCEPTION_RESOLVED

**HITL Events**
- HITL_REQUIRED
- HITL_DECISION_MADE

**Orchestration Events**
- SLA_VIOLATED
- COMPLIANCE_CHECK_FAILED
- CONTROL_COMMAND_ISSUED
- AGENT_HEALTH_CHANGED

**System Events**
- AGENT_STARTED
- AGENT_STOPPED
- CONFIGURATION_CHANGED

#### Models

**StandardEventMessage**
- Base schema for all SQS events
- Includes correlation_id for distributed tracing
- Validates: Requirements 3.1, 12.4

#### Validation Functions

- `validate_event_schema()`: Validate standard schema
- `validate_event_payload()`: Validate payload fields
- `validate_document_uploaded_event()`: Validate DOCUMENT_UPLOADED
- `validate_trade_extracted_event()`: Validate TRADE_EXTRACTED
- `validate_match_completed_event()`: Validate MATCH_COMPLETED
- `validate_exception_raised_event()`: Validate EXCEPTION_RAISED

#### Usage Example

```python
from src.latest_trade_matching_agent.models.events import (
    EventTaxonomy,
    StandardEventMessage,
    validate_document_uploaded_event
)

# Create event
event = StandardEventMessage(
    event_id="evt_123",
    event_type=EventTaxonomy.DOCUMENT_UPLOADED,
    source_agent="upload_service",
    correlation_id="corr_abc",
    payload={
        "document_id": "doc_456",
        "document_path": "s3://bucket/BANK/trade.pdf",
        "source_type": "BANK"
    }
)

# Serialize for SQS
sqs_message = event.to_sqs_message()

# Deserialize from SQS
restored_event = StandardEventMessage.from_sqs_message(sqs_message)

# Validate event
validation = validate_document_uploaded_event(event)
if not validation["valid"]:
    print(f"Validation errors: {validation['errors']}")
```

### 4. Reason Code Taxonomy (`taxonomy.py`)

Comprehensive reason codes for exceptions and mismatches.

#### Reason Code Categories

**Matching Reason Codes** (11 codes)
- NOTIONAL_MISMATCH, DATE_MISMATCH, COUNTERPARTY_MISMATCH, etc.

**Data Error Reason Codes** (6 codes)
- MISSING_REQUIRED_FIELD, INVALID_FIELD_FORMAT, MISPLACED_TRADE, etc.

**Processing Reason Codes** (6 codes)
- OCR_QUALITY_LOW, PDF_CORRUPTED, PARSING_ERROR, etc.

**System Reason Codes** (8 codes)
- SERVICE_UNAVAILABLE, TIMEOUT, RATE_LIMIT_EXCEEDED, etc.

**Business Logic Reason Codes** (6 codes)
- TRADE_NOT_FOUND, NO_MATCH_FOUND, CONFIDENCE_TOO_LOW, etc.

#### Functions

**ReasonCodeTaxonomy Class**
- `all_reason_codes()`: Get all reason codes
- `is_valid_reason_code()`: Validate reason code
- `get_reason_code_description()`: Get human-readable description
- `get_reason_code_category()`: Get category (MATCHING, DATA_ERROR, etc.)
- `get_base_severity_score()`: Get severity score (0.0-1.0)

**Helper Functions**
- `classify_reason_codes()`: Classify list of reason codes
- `get_recommended_routing()`: Get routing recommendation

#### Usage Example

```python
from src.latest_trade_matching_agent.models.taxonomy import (
    ReasonCodeTaxonomy,
    classify_reason_codes,
    get_recommended_routing
)

# Get description
description = ReasonCodeTaxonomy.get_reason_code_description("NOTIONAL_MISMATCH")
# "Trade notional amounts differ beyond tolerance (±0.01%)"

# Get category
category = ReasonCodeTaxonomy.get_reason_code_category("NOTIONAL_MISMATCH")
# "MATCHING"

# Get severity
severity = ReasonCodeTaxonomy.get_base_severity_score("NOTIONAL_MISMATCH")
# 0.8 (high severity)

# Classify multiple reason codes
reason_codes = ["NOTIONAL_MISMATCH", "DATE_MISMATCH", "CURRENCY_MISMATCH"]
classification = classify_reason_codes(reason_codes)
# {
#     "categories": ["MATCHING"],
#     "primary_category": "MATCHING",
#     "max_severity": 0.8,
#     "avg_severity": 0.75,
#     "reason_code_count": 3
# }

# Get routing recommendation
routing = get_recommended_routing(reason_codes)
# "OPS_DESK"
```

## Requirements Validation

### Task 3.1: Agent Registry Implementation
✅ AgentRegistryEntry model created
✅ register_agent() function implemented
✅ update_agent_status() function implemented
✅ get_agent_by_capability() function implemented
✅ DynamoDB AgentRegistry table integration
✅ Validates Requirements 4.1, 4.3

### Task 3.2: Workflow Taxonomy Configuration
✅ Hierarchical workflow structure defined (18 nodes)
✅ JSON configuration support
✅ S3 storage at config/taxonomy.json
✅ TaxonomyLoader implemented
✅ Validates Requirements 3.1

### Task 3.3: Event Taxonomy
✅ EventTaxonomy class with 22+ event types
✅ Event schemas documented
✅ Event validation functions created
✅ Validates Requirements 3.1, 3.2, 3.3, 3.4, 3.5

### Task 3.4: Reason Code Taxonomy
✅ ReasonCodeTaxonomy class with 37+ codes
✅ All reason codes documented with descriptions
✅ Reason code classification logic implemented
✅ Validates Requirements 7.2, 7.5, 8.1

## Testing

All components have been tested and verified:

```bash
# Run tests
python3 test_registry_taxonomy_simple.py

# Expected output:
# ✓ All imports successful
# ✓ AgentRegistryEntry creation and serialization works
# ✓ Workflow taxonomy created with 18 workflows
# ✓ Event taxonomy with 22 event types works
# ✓ Reason code taxonomy with 37 codes works
# ✓ Event validation functions work correctly
# ✓ All tests passed successfully!
```

## Integration

These components integrate with:

1. **DynamoDB**: Agent registry storage
2. **S3**: Workflow taxonomy configuration storage
3. **SQS**: Event message validation
4. **AgentCore Runtime**: Agent deployment and monitoring
5. **Exception Management**: Reason code classification and routing

## Next Steps

With the registry and taxonomy system complete, the next tasks are:

- Task 4: Implement PDF Adapter Agent
- Task 5: Checkpoint - Ensure PDF Adapter tests pass
- Task 6: Implement Trade Data Extraction Agent

The registry and taxonomy system provides the foundation for all subsequent agent implementations.
