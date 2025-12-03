# Design Document

## Overview

This document describes the architecture for migrating the AI Trade Matching System from CrewAI to Strands SDK with Amazon Bedrock AgentCore deployment. The new architecture transforms a monolithic multi-agent system into five independent, scalable agents with a React-based web portal for monitoring, human-in-the-loop interactions, and comprehensive audit trails.

The system will leverage Amazon Bedrock AgentCore services including Runtime (serverless deployment), Memory (persistent context), Observability (monitoring and tracing), Gateway (MCP tool integration), and Identity (authentication and authorization).

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         React Web Portal                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Dashboard   │  │  HITL Panel  │  │ Audit Trail  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└────────────────────────────┬────────────────────────────────────────┘
                             │ WebSocket + REST API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Amazon Bedrock AgentCore Runtime (us-east-1)            │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator Agent                         │  │
│  │  • Monitors all agents                                        │  │
│  │  • Coordinates workflows                                      │  │
│  │  • Aggregates metrics                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│         ┌───────────────────┼───────────────────┐                   │
│         ▼                   ▼                   ▼                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │ PDF Adapter │    │ Trade Data  │    │   Trade     │            │
│  │   Agent     │───▶│ Extraction  │───▶│  Matching   │            │
│  │             │    │   Agent     │    │   Agent     │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│         │                   │                   │                   │
│         └───────────────────┴───────────────────┘                   │
│                             │                                        │
│                             ▼                                        │
│                  ┌─────────────────────┐                            │
│                  │ Exception Mgmt Agent│                            │
│                  └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ AgentCore    │    │ AgentCore    │    │ AgentCore    │
│ Memory       │    │ Observability│    │ Gateway      │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AWS Services (us-east-1)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │    S3    │  │ DynamoDB │  │  Bedrock │  │   IAM    │           │
│  │  Bucket  │  │  Tables  │  │ Claude 4 │  │  Roles   │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Communication Pattern

The system uses **event-driven architecture** with Amazon SQS for complete agent decoupling:

1. **Orchestrator Agent** monitors SLAs, enforces compliance, and issues control commands (lightweight governance)
2. **PDF Adapter Agent** processes documents and publishes events to SQS
3. **Trade Data Extraction Agent** subscribes to PDF processing events
4. **Trade Matching Agent** subscribes to extraction events and publishes match results with scores
5. **Exception Management Agent** subscribes to all error events, performs scoring/triage, and routes to appropriate handlers

**Key Principles**:
- **Complete Decoupling**: Agents communicate only via SQS events
- **Independent Scaling**: Each agent scales based on its queue depth
- **Extensibility**: New adapter agents (chat, email, voice) can be added without modifying existing agents
- **Standardized Output**: All adapters produce output conforming to a canonical schema

## Components and Interfaces

### 1. Orchestrator Agent

**Purpose**: Lightweight governance agent that monitors SLAs, enforces compliance checkpoints, and issues control commands.

**Implementation**:
```python
from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp
import boto3

app = BedrockAgentCoreApp()
sqs = boto3.client('sqs', region_name='us-east-1')

@app.entrypoint
def invoke(payload, context):
    """
    Orchestrator subscribes to all agent events for monitoring.
    Does NOT directly invoke agents - only monitors and governs.
    """
    orchestrator = Agent(
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[sla_monitor_tool, compliance_checker_tool, control_command_tool]
    )
    
    # Subscribe to all event queues for monitoring
    event = payload.get("event")
    
    # Check SLAs
    sla_status = orchestrator.check_sla(event)
    
    # Enforce compliance checkpoints
    compliance_status = orchestrator.check_compliance(event)
    
    # Issue control commands if needed
    if sla_status.violated or compliance_status.failed:
        orchestrator.issue_control_command(event)
    
    return {"status": "monitored", "sla": sla_status, "compliance": compliance_status}
```

**Responsibilities**:
- Monitor SLAs for all agents (processing time, throughput, error rates)
- Enforce compliance checkpoints (data validation, regulatory requirements)
- Issue control commands (pause processing, trigger escalation, adjust priorities)
- Aggregate metrics and health status
- Maintain registry and taxonomy of all agents and workflows

**Event Subscriptions**:
- `pdf-processing-events` queue
- `extraction-events` queue
- `matching-events` queue
- `exception-events` queue

**Memory Strategy**: Semantic memory for SLA patterns, compliance rules, and agent performance metrics

### 2. PDF Adapter Agent (Extensible Adapter Pattern)

**Purpose**: Convert trade confirmation PDFs to standardized canonical format. Part of extensible adapter family (future: chat, email, voice adapters).

**Implementation**:
```python
from bedrock_agentcore import BedrockAgentCoreApp
import boto3
import json

app = BedrockAgentCoreApp()
sqs = boto3.client('sqs', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

@app.entrypoint
def invoke(payload, context):
    """
    PDF Adapter subscribes to document upload events.
    Produces standardized output conforming to canonical schema.
    """
    agent = Agent(
        system_prompt=PDF_ADAPTER_SYSTEM_PROMPT,
        tools=[pdf_to_image_tool, ocr_tool, s3_writer_tool]
    )
    
    # Process PDF
    document_path = payload.get("document_path")
    source_type = payload.get("source_type")
    
    # Convert and extract
    images = agent.convert_pdf_to_images(document_path, dpi=300)
    ocr_text = agent.extract_text_from_images(images)
    
    # Produce standardized output (canonical schema)
    canonical_output = {
        "adapter_type": "PDF",
        "document_id": payload.get("document_id"),
        "source_type": source_type,
        "extracted_text": ocr_text,
        "metadata": {
            "page_count": len(images),
            "dpi": 300,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "s3_location": f"s3://bucket/extracted/{source_type}/{document_id}.txt"
    }
    
    # Save to S3
    s3.put_object(
        Bucket='trade-matching-bucket',
        Key=f"extracted/{source_type}/{document_id}.json",
        Body=json.dumps(canonical_output)
    )
    
    # Publish event to SQS for Trade Extraction Agent
    sqs.send_message(
        QueueUrl='extraction-events-queue',
        MessageBody=json.dumps({
            "event_type": "PDF_PROCESSED",
            "document_id": document_id,
            "canonical_output_location": canonical_output["s3_location"]
        })
    )
    
    return {"status": "processed", "output": canonical_output}
```

**Canonical Output Schema**:
```python
class CanonicalAdapterOutput(BaseModel):
    adapter_type: Literal["PDF", "CHAT", "EMAIL", "VOICE"]  # Extensible
    document_id: str
    source_type: Literal["BANK", "COUNTERPARTY"]
    extracted_text: str
    metadata: Dict[str, Any]
    s3_location: str
```

**Responsibilities**:
- Subscribe to `document-upload-events` SQS queue
- Convert PDF to 300 DPI JPEG images
- Perform OCR extraction using AWS Bedrock
- Produce output conforming to canonical schema
- Publish `PDF_PROCESSED` event to `extraction-events` queue
- Write errors to `exception-events` queue

**Event Subscriptions**: `document-upload-events`

**Event Publications**: `extraction-events`, `exception-events`

**Memory Strategy**: Event memory for processing history

**Extensibility**: Future adapters (ChatAdapter, EmailAdapter, VoiceAdapter) will implement the same canonical output schema

### 3. Trade Data Extraction Agent

**Purpose**: Parse unstructured text into canonical trade model with mandatory and optional attributes.

**Implementation**:
```python
from bedrock_agentcore import BedrockAgentCoreApp
import boto3
import json

app = BedrockAgentCoreApp()
sqs = boto3.client('sqs', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

@app.entrypoint
def invoke(payload, context):
    """
    Trade Extraction Agent subscribes to extraction events.
    Produces canonical trade model and publishes to matching queue.
    """
    agent = Agent(
        system_prompt=TRADE_EXTRACTION_SYSTEM_PROMPT,
        tools=[s3_reader_tool, llm_extraction_tool, dynamodb_tool]
    )
    
    # Read canonical adapter output
    event = json.loads(payload.get("Body"))
    canonical_output_location = event.get("canonical_output_location")
    canonical_data = agent.read_from_s3(canonical_output_location)
    
    # Use LLM to extract trade information into canonical trade model
    trade_data = agent.extract_trade_fields(canonical_data["extracted_text"])
    
    # Validate against canonical trade model
    canonical_trade = CanonicalTradeModel(**trade_data)
    
    # Store in appropriate DynamoDB table
    table_name = "BankTradeData" if canonical_trade.TRADE_SOURCE == "BANK" else "CounterpartyTradeData"
    table = dynamodb.Table(table_name)
    table.put_item(Item=canonical_trade.to_dynamodb_format())
    
    # Publish event to matching queue
    sqs.send_message(
        QueueUrl='matching-events-queue',
        MessageBody=json.dumps({
            "event_type": "TRADE_EXTRACTED",
            "trade_id": canonical_trade.Trade_ID,
            "source_type": canonical_trade.TRADE_SOURCE,
            "table_name": table_name
        })
    )
    
    return {"status": "extracted", "trade_id": canonical_trade.Trade_ID}
```

**Canonical Trade Model**:
```python
class CanonicalTradeModel(BaseModel):
    # Mandatory attributes
    Trade_ID: str
    TRADE_SOURCE: Literal["BANK", "COUNTERPARTY"]
    trade_date: str
    notional: float
    currency: str
    counterparty: str
    product_type: str
    
    # Optional attributes
    effective_date: Optional[str]
    maturity_date: Optional[str]
    commodity_type: Optional[str]
    strike_price: Optional[float]
    settlement_type: Optional[str]
    # ... additional 20+ optional fields
    
    def to_dynamodb_format(self) -> dict:
        """Convert to DynamoDB typed format."""
        return {
            "Trade_ID": {"S": self.Trade_ID},
            "TRADE_SOURCE": {"S": self.TRADE_SOURCE},
            "notional": {"N": str(self.notional)},
            # ... all other fields with type markers
        }
```

**Responsibilities**:
- Subscribe to `extraction-events` SQS queue
- Use LLM to extract trade fields from unstructured text
- Validate against canonical trade model schema
- Store in appropriate DynamoDB table (routing based on TRADE_SOURCE)
- Publish `TRADE_EXTRACTED` event to `matching-events` queue
- Write extraction errors to `exception-events` queue

**Event Subscriptions**: `extraction-events`

**Event Publications**: `matching-events`, `exception-events`

**Memory Strategy**: Semantic memory for trade patterns, extraction rules, and field mappings

### 4. Trade Matching Agent (with Scoring and Triage)

**Purpose**: Identify discrepancies between bank and counterparty trades, compute match scores, and classify results for triage.

**Implementation**:
```python
from bedrock_agentcore import BedrockAgentCoreApp
import boto3
import json

app = BedrockAgentCoreApp()
sqs = boto3.client('sqs', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

@app.entrypoint
def invoke(payload, context):
    """
    Trade Matching Agent subscribes to matching events.
    Computes match scores and publishes results with triage classification.
    """
    agent = Agent(
        system_prompt=TRADE_MATCHING_SYSTEM_PROMPT,
        tools=[dynamodb_scan_tool, scoring_tool, s3_writer_tool]
    )
    
    # Read event
    event = json.loads(payload.get("Body"))
    trade_id = event.get("trade_id")
    
    # Retrieve trades from both tables
    bank_table = dynamodb.Table("BankTradeData")
    cp_table = dynamodb.Table("CounterpartyTradeData")
    
    bank_trade = bank_table.get_item(Key={"Trade_ID": trade_id}).get("Item")
    cp_trade = cp_table.get_item(Key={"Trade_ID": trade_id}).get("Item")
    
    # Perform fuzzy matching with tolerances
    match_result = agent.fuzzy_match(bank_trade, cp_trade)
    
    # Compute match score (0.0 to 1.0)
    match_score = agent.compute_match_score(match_result)
    
    # Classify based on score and reason codes
    classification = agent.classify_match(match_score, match_result.reason_codes)
    
    # Determine decision status
    if match_score >= 0.85:
        decision_status = "AUTO_MATCH"
    elif match_score >= 0.70:
        decision_status = "ESCALATE"  # Requires HITL
    else:
        decision_status = "EXCEPTION"  # Requires exception handling
    
    # Create match result with score
    result = MatchingResult(
        trade_id=trade_id,
        classification=classification,
        match_score=match_score,
        decision_status=decision_status,
        reason_codes=match_result.reason_codes,
        bank_trade=bank_trade,
        counterparty_trade=cp_trade,
        differences=match_result.differences
    )
    
    # Save report to S3
    report_path = agent.generate_report(result)
    
    # Publish result event
    if decision_status == "EXCEPTION":
        # Send to exception queue for triage
        sqs.send_message(
            QueueUrl='exception-events-queue',
            MessageBody=json.dumps({
                "event_type": "MATCHING_EXCEPTION",
                "trade_id": trade_id,
                "match_score": match_score,
                "reason_codes": match_result.reason_codes,
                "report_path": report_path
            })
        )
    elif decision_status == "ESCALATE":
        # Send to HITL queue
        sqs.send_message(
            QueueUrl='hitl-review-queue',
            MessageBody=json.dumps({
                "event_type": "HITL_REQUIRED",
                "trade_id": trade_id,
                "match_score": match_score,
                "report_path": report_path
            })
        )
    
    return {"status": "matched", "decision": decision_status, "score": match_score}
```

**Scoring System**:
```python
def compute_match_score(match_result: MatchResult) -> float:
    """
    Compute match score based on field comparisons.
    Score = weighted average of field match scores.
    """
    weights = {
        "Trade_ID": 0.30,      # Exact match required
        "trade_date": 0.20,    # ±1 day tolerance
        "notional": 0.25,      # ±0.01% tolerance
        "counterparty": 0.15,  # Fuzzy match
        "currency": 0.10       # Exact match
    }
    
    field_scores = {}
    for field, weight in weights.items():
        if field == "Trade_ID":
            field_scores[field] = 1.0 if match_result.trade_id_match else 0.0
        elif field == "trade_date":
            field_scores[field] = compute_date_score(match_result.date_diff)
        elif field == "notional":
            field_scores[field] = compute_notional_score(match_result.notional_diff_pct)
        elif field == "counterparty":
            field_scores[field] = compute_fuzzy_score(match_result.counterparty_similarity)
        else:
            field_scores[field] = 1.0 if match_result.exact_matches[field] else 0.0
    
    # Weighted average
    total_score = sum(field_scores[f] * weights[f] for f in weights)
    return round(total_score, 2)
```

**Triage Classification**:
```python
class TriageClassification(BaseModel):
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    routing: Literal["AUTO_CONFIRM", "OPS_DESK", "SENIOR_OPS", "COMPLIANCE"]
    reason_codes: List[str]
    
def classify_for_triage(match_score: float, reason_codes: List[str]) -> TriageClassification:
    """
    Classify exceptions by severity and determine routing.
    """
    if "NOTIONAL_MISMATCH" in reason_codes:
        return TriageClassification(
            severity="HIGH",
            routing="OPS_DESK",
            reason_codes=reason_codes
        )
    elif "DATE_MISMATCH" in reason_codes:
        return TriageClassification(
            severity="MEDIUM",
            routing="OPS_DESK",
            reason_codes=reason_codes
        )
    elif "COUNTERPARTY_MISMATCH" in reason_codes:
        return TriageClassification(
            severity="CRITICAL",
            routing="SENIOR_OPS",
            reason_codes=reason_codes
        )
    elif match_score >= 0.70:
        return TriageClassification(
            severity="LOW",
            routing="AUTO_CONFIRM",
            reason_codes=reason_codes
        )
    else:
        return TriageClassification(
            severity="MEDIUM",
            routing="OPS_DESK",
            reason_codes=reason_codes
        )
```

**Matching Criteria with Scoring**:
- Trade_ID: Exact match required (weight: 0.30)
- Trade_Date: ±1 business day tolerance (weight: 0.20)
- Notional: ±0.01% tolerance (weight: 0.25)
- Counterparty: Fuzzy string match (weight: 0.15)
- Currency: Exact match (weight: 0.10)

**Decision Thresholds**:
- Score ≥ 0.85: AUTO_MATCH (auto-confirm)
- Score 0.70-0.84: ESCALATE (requires HITL review)
- Score < 0.70: EXCEPTION (requires exception handling and triage)

**Responsibilities**:
- Subscribe to `matching-events` SQS queue
- Retrieve trades from both DynamoDB tables
- Perform fuzzy matching with tolerances
- Compute match score (0.0 to 1.0)
- Classify results with reason codes
- Determine decision status (AUTO_MATCH, ESCALATE, EXCEPTION)
- Generate detailed markdown reports
- Publish results to appropriate queues based on decision status

**Event Subscriptions**: `matching-events`

**Event Publications**: `exception-events`, `hitl-review-queue`

**Memory Strategy**: Semantic memory for matching decisions, HITL feedback, and scoring patterns

### 5. Exception Management Agent (with Scoring, Triage, and RL)

**Purpose**: Collect, classify, rank, and route exceptions with intelligent triage and continuous learning.

**Implementation**:
```python
from bedrock_agentcore import BedrockAgentCoreApp
import boto3
import json

app = BedrockAgentCoreApp()
sqs = boto3.client('sqs', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

@app.entrypoint
def invoke(payload, context):
    """
    Exception Management Agent subscribes to exception events.
    Performs scoring, triage, delegation, and tracks resolution.
    Integrates RL for continuous improvement.
    """
    agent = Agent(
        system_prompt=EXCEPTION_MGMT_SYSTEM_PROMPT,
        tools=[scoring_tool, triage_tool, delegation_tool, rl_tool]
    )
    
    # Read exception event
    event = json.loads(payload.get("Body"))
    exception_type = event.get("event_type")
    
    # Collect exception details
    exception = ExceptionRecord(
        exception_id=generate_id(),
        timestamp=datetime.utcnow(),
        event_type=exception_type,
        trade_id=event.get("trade_id"),
        match_score=event.get("match_score"),
        reason_codes=event.get("reason_codes", []),
        context=event
    )
    
    # Classify exception
    classification = agent.classify_exception(exception)
    
    # Rank by severity (using scoring)
    severity_score = agent.compute_severity_score(exception, classification)
    
    # Triage: determine routing based on severity and reason codes
    triage_result = agent.triage_exception(exception, severity_score)
    
    # Delegate to appropriate handler
    delegation = agent.delegate_exception(triage_result)
    
    # Store exception with triage info
    exceptions_table = dynamodb.Table("ExceptionsTable")
    exceptions_table.put_item(Item={
        "exception_id": exception.exception_id,
        "timestamp": exception.timestamp.isoformat(),
        "classification": classification,
        "severity_score": severity_score,
        "triage_routing": triage_result.routing,
        "delegation_status": delegation.status,
        "assigned_to": delegation.assigned_to,
        "resolution_status": "PENDING"
    })
    
    # Send to appropriate queue for delegation
    if triage_result.routing == "OPS_DESK":
        sqs.send_message(
            QueueUrl='ops-desk-queue',
            MessageBody=json.dumps(exception.dict())
        )
    elif triage_result.routing == "SENIOR_OPS":
        sqs.send_message(
            QueueUrl='senior-ops-queue',
            MessageBody=json.dumps(exception.dict())
        )
    
    # Track for RL: record state, action, and await reward
    agent.record_rl_episode(
        state=exception.to_state_vector(),
        action=triage_result.routing,
        context=exception.dict()
    )
    
    return {"status": "triaged", "routing": triage_result.routing}
```

**Exception Scoring System**:
```python
def compute_severity_score(exception: ExceptionRecord, classification: str) -> float:
    """
    Compute severity score (0.0 to 1.0) based on multiple factors.
    """
    base_scores = {
        "NOTIONAL_MISMATCH": 0.8,
        "DATE_MISMATCH": 0.5,
        "COUNTERPARTY_MISMATCH": 0.9,
        "MISSING_FIELD": 0.6,
        "PROCESSING_ERROR": 0.4
    }
    
    # Start with base score from reason codes
    score = max([base_scores.get(code, 0.5) for code in exception.reason_codes])
    
    # Adjust based on match score (if available)
    if exception.match_score is not None:
        score = score * (1 - exception.match_score)  # Lower match score = higher severity
    
    # Adjust based on historical patterns (from RL)
    historical_adjustment = get_rl_severity_adjustment(exception)
    score = min(1.0, score + historical_adjustment)
    
    return round(score, 2)
```

**Triage System**:
```python
class TriageResult(BaseModel):
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    routing: Literal["AUTO_RESOLVE", "OPS_DESK", "SENIOR_OPS", "COMPLIANCE", "ENGINEERING"]
    priority: int  # 1 (highest) to 5 (lowest)
    sla_hours: int  # Resolution SLA in hours
    
def triage_exception(exception: ExceptionRecord, severity_score: float) -> TriageResult:
    """
    Triage exception based on severity score and reason codes.
    Uses RL-learned policies for optimal routing.
    """
    # Use RL policy to determine routing
    rl_policy = load_rl_policy()
    state = exception.to_state_vector()
    recommended_routing = rl_policy.predict(state)
    
    # Apply business rules
    if "NOTIONAL_MISMATCH" in exception.reason_codes and severity_score > 0.7:
        return TriageResult(
            severity="HIGH",
            routing="OPS_DESK",
            priority=2,
            sla_hours=4
        )
    elif "COUNTERPARTY_MISMATCH" in exception.reason_codes:
        return TriageResult(
            severity="CRITICAL",
            routing="SENIOR_OPS",
            priority=1,
            sla_hours=2
        )
    elif severity_score < 0.3:
        return TriageResult(
            severity="LOW",
            routing="AUTO_RESOLVE",
            priority=4,
            sla_hours=24
        )
    else:
        # Use RL recommendation
        return TriageResult(
            severity="MEDIUM",
            routing=recommended_routing,
            priority=3,
            sla_hours=8
        )
```

**Reinforcement Learning Integration**:
```python
class RLExceptionHandler:
    """
    RL agent that learns optimal exception routing policies.
    Uses supervised learning from historical resolutions.
    """
    
    def __init__(self):
        self.model = load_or_initialize_model()
        self.replay_buffer = []
    
    def record_episode(self, state, action, context):
        """Record state-action pair for later reward assignment."""
        self.replay_buffer.append({
            "state": state,
            "action": action,
            "context": context,
            "timestamp": datetime.utcnow()
        })
    
    def update_with_resolution(self, exception_id, resolution_outcome):
        """
        Update RL model when exception is resolved.
        Reward based on resolution time and outcome.
        """
        # Find episode in replay buffer
        episode = find_episode_by_exception_id(exception_id)
        
        # Compute reward
        reward = compute_reward(resolution_outcome)
        
        # Update model
        self.model.update(
            state=episode["state"],
            action=episode["action"],
            reward=reward
        )
        
        # Supervised learning: learn from human decisions
        if resolution_outcome.human_decision:
            self.model.supervised_update(
                state=episode["state"],
                correct_action=resolution_outcome.human_decision
            )
    
    def compute_reward(self, outcome):
        """
        Reward function:
        +1.0: Resolved within SLA, correct routing
        +0.5: Resolved within SLA, suboptimal routing
        -0.5: Resolved late, correct routing
        -1.0: Resolved late, incorrect routing
        """
        if outcome.resolved_within_sla and outcome.routing_correct:
            return 1.0
        elif outcome.resolved_within_sla:
            return 0.5
        elif outcome.routing_correct:
            return -0.5
        else:
            return -1.0
```

**Delegation and Tracking**:
```python
def delegate_exception(triage_result: TriageResult) -> DelegationResult:
    """
    Delegate exception to appropriate handler and track.
    """
    # Assign to specific user/team based on routing
    assignment = assign_to_handler(triage_result.routing)
    
    # Create tracking record
    tracking = ExceptionTracking(
        exception_id=exception.exception_id,
        assigned_to=assignment.user_id,
        assigned_team=assignment.team,
        assigned_at=datetime.utcnow(),
        sla_deadline=datetime.utcnow() + timedelta(hours=triage_result.sla_hours),
        status="ASSIGNED"
    )
    
    # Send notification
    send_notification(assignment.user_id, exception, triage_result)
    
    return DelegationResult(
        status="DELEGATED",
        assigned_to=assignment.user_id,
        tracking_id=tracking.tracking_id
    )

def track_resolution(exception_id: str, resolution: Resolution):
    """
    Track exception resolution and update RL model.
    """
    # Update tracking record
    update_exception_status(exception_id, "RESOLVED", resolution)
    
    # Compute resolution metrics
    resolution_time = resolution.resolved_at - exception.assigned_at
    within_sla = resolution_time < exception.sla_deadline
    
    # Update RL model with reward
    rl_handler.update_with_resolution(
        exception_id,
        ResolutionOutcome(
            resolved_within_sla=within_sla,
            routing_correct=resolution.routing_was_correct,
            human_decision=resolution.human_decision
        )
    )
```

**Responsibilities**:
- Subscribe to `exception-events` SQS queue
- Collect and classify all exceptions
- Compute severity scores for ranking
- Triage exceptions based on severity and reason codes
- Delegate to appropriate handlers (Ops Desk, Senior Ops, Compliance, Engineering)
- Track exception resolution and SLA compliance
- Integrate RL for continuous improvement of triage policies
- Learn from human decisions via supervised learning
- Update audit trail with exception lifecycle

**Event Subscriptions**: `exception-events`, `matching-exception-events`, `processing-error-events`

**Event Publications**: `ops-desk-queue`, `senior-ops-queue`, `compliance-queue`, `engineering-queue`

**Memory Strategy**: 
- Event memory for exception patterns and resolutions
- Semantic memory for RL policies and learned routing strategies
- Historical resolution data for supervised learning

**RL/ML Integration**:
- Reinforcement learning for optimal exception routing
- Supervised learning from human resolution decisions
- Continuous model updates based on resolution outcomes
- Reward function based on SLA compliance and routing correctness

### 6. React Web Portal

**Purpose**: Provide user interface for monitoring and HITL interactions.

**Technology Stack**:
- React 18+ with TypeScript
- Material-UI or Ant Design for components
- WebSocket for real-time updates
- React Query for data fetching
- Recharts for visualizations

**Components**:

#### Dashboard Component
```typescript
interface DashboardProps {
  agents: AgentStatus[];
  metrics: SystemMetrics;
}

const Dashboard: React.FC<DashboardProps> = ({ agents, metrics }) => {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <AgentHealthPanel agents={agents} />
      </Grid>
      <Grid item xs={6}>
        <ProcessingMetrics metrics={metrics} />
      </Grid>
      <Grid item xs={6}>
        <MatchingResults results={metrics.matching} />
      </Grid>
    </Grid>
  );
};
```

#### HITL Panel Component
```typescript
interface HITLPanelProps {
  pendingReviews: TradeReview[];
  onDecision: (reviewId: string, decision: Decision) => void;
}

const HITLPanel: React.FC<HITLPanelProps> = ({ pendingReviews, onDecision }) => {
  return (
    <List>
      {pendingReviews.map(review => (
        <TradeComparisonCard
          key={review.id}
          bankTrade={review.bankTrade}
          counterpartyTrade={review.counterpartyTrade}
          onApprove={() => onDecision(review.id, 'APPROVE')}
          onReject={() => onDecision(review.id, 'REJECT')}
        />
      ))}
    </List>
  );
};
```

#### Audit Trail Component
```typescript
interface AuditTrailProps {
  filters: AuditFilters;
}

const AuditTrail: React.FC<AuditTrailProps> = ({ filters }) => {
  const { data, isLoading } = useQuery(['audit', filters], 
    () => fetchAuditTrail(filters)
  );
  
  return (
    <DataGrid
      rows={data?.records || []}
      columns={auditColumns}
      loading={isLoading}
      pagination
    />
  );
};
```

**API Integration**:
```typescript
// WebSocket connection for real-time updates
const ws = new WebSocket('wss://api.example.com/ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  switch (update.type) {
    case 'AGENT_STATUS':
      updateAgentStatus(update.payload);
      break;
    case 'TRADE_PROCESSED':
      updateMetrics(update.payload);
      break;
    case 'HITL_REQUIRED':
      addPendingReview(update.payload);
      break;
  }
};

// REST API for actions
const api = {
  submitDecision: (reviewId: string, decision: Decision) =>
    fetch(`/api/hitl/${reviewId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision })
    }),
  
  fetchAuditTrail: (filters: AuditFilters) =>
    fetch(`/api/audit?${new URLSearchParams(filters)}`),
};
```

## Registry and Taxonomy

### Agent Registry

The system maintains a centralized registry of all agents, their capabilities, and event subscriptions:

```python
class AgentRegistryEntry(BaseModel):
    agent_id: str
    agent_name: str
    agent_type: Literal["ORCHESTRATOR", "ADAPTER", "EXTRACTOR", "MATCHER", "EXCEPTION_HANDLER"]
    version: str
    capabilities: List[str]
    event_subscriptions: List[str]
    event_publications: List[str]
    sla_targets: Dict[str, float]
    scaling_config: ScalingConfig
    deployment_status: Literal["ACTIVE", "INACTIVE", "DEGRADED"]
```

**Registry Storage**: DynamoDB table `AgentRegistry` with agent_id as primary key

**Registry Operations**:
- `register_agent()`: Register new agent on deployment
- `update_agent_status()`: Update agent health and metrics
- `get_agent_by_capability()`: Find agents by capability
- `list_active_agents()`: Get all active agents

### Workflow Taxonomy

Hierarchical taxonomy of workflows and their components:

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

**Taxonomy Storage**: JSON configuration in S3 `s3://config/taxonomy.json`

### Event Taxonomy

Standardized event types and their schemas:

```python
class EventTaxonomy:
    # Document Processing Events
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    PDF_PROCESSED = "PDF_PROCESSED"
    OCR_COMPLETED = "OCR_COMPLETED"
    
    # Extraction Events
    EXTRACTION_STARTED = "EXTRACTION_STARTED"
    TRADE_EXTRACTED = "TRADE_EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    
    # Matching Events
    MATCHING_STARTED = "MATCHING_STARTED"
    MATCH_COMPLETED = "MATCH_COMPLETED"
    MATCHING_EXCEPTION = "MATCHING_EXCEPTION"
    
    # Exception Events
    EXCEPTION_RAISED = "EXCEPTION_RAISED"
    EXCEPTION_TRIAGED = "EXCEPTION_TRIAGED"
    EXCEPTION_RESOLVED = "EXCEPTION_RESOLVED"
    
    # HITL Events
    HITL_REQUIRED = "HITL_REQUIRED"
    HITL_DECISION_MADE = "HITL_DECISION_MADE"
    
    # Orchestration Events
    SLA_VIOLATED = "SLA_VIOLATED"
    COMPLIANCE_CHECK_FAILED = "COMPLIANCE_CHECK_FAILED"
    CONTROL_COMMAND_ISSUED = "CONTROL_COMMAND_ISSUED"
```

### Reason Code Taxonomy

Standardized reason codes for exceptions and mismatches:

```python
class ReasonCodeTaxonomy:
    # Matching Reason Codes
    NOTIONAL_MISMATCH = "NOTIONAL_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    COUNTERPARTY_MISMATCH = "COUNTERPARTY_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    PRODUCT_TYPE_MISMATCH = "PRODUCT_TYPE_MISMATCH"
    
    # Extraction Reason Codes
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_FORMAT = "INVALID_FIELD_FORMAT"
    AMBIGUOUS_FIELD_VALUE = "AMBIGUOUS_FIELD_VALUE"
    
    # Processing Reason Codes
    OCR_QUALITY_LOW = "OCR_QUALITY_LOW"
    PDF_CORRUPTED = "PDF_CORRUPTED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    
    # System Reason Codes
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
```

## SQS Event Architecture

### Queue Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     SQS Queue Architecture                   │
└─────────────────────────────────────────────────────────────┘

document-upload-events (FIFO)
    ↓
PDF Adapter Agent
    ↓
extraction-events (Standard)
    ↓
Trade Data Extraction Agent
    ↓
matching-events (Standard)
    ↓
Trade Matching Agent
    ↓
    ├─→ hitl-review-queue (FIFO)
    │       ↓
    │   Web Portal HITL Panel
    │
    └─→ exception-events (Standard)
            ↓
        Exception Management Agent
            ↓
            ├─→ ops-desk-queue (FIFO)
            ├─→ senior-ops-queue (FIFO)
            ├─→ compliance-queue (FIFO)
            └─→ engineering-queue (Standard)

All queues → orchestrator-monitoring-queue (Fanout)
    ↓
Orchestrator Agent (SLA & Compliance Monitoring)
```

### Queue Configurations

```python
QUEUE_CONFIGS = {
    "document-upload-events": {
        "type": "FIFO",
        "visibility_timeout": 300,  # 5 minutes
        "message_retention": 345600,  # 4 days
        "max_receives": 3,
        "dead_letter_queue": "document-upload-dlq"
    },
    "extraction-events": {
        "type": "Standard",
        "visibility_timeout": 600,  # 10 minutes
        "message_retention": 345600,
        "max_receives": 3,
        "dead_letter_queue": "extraction-dlq"
    },
    "matching-events": {
        "type": "Standard",
        "visibility_timeout": 900,  # 15 minutes
        "message_retention": 345600,
        "max_receives": 3,
        "dead_letter_queue": "matching-dlq"
    },
    "exception-events": {
        "type": "Standard",
        "visibility_timeout": 300,
        "message_retention": 1209600,  # 14 days (longer retention for exceptions)
        "max_receives": 5,  # More retries for exceptions
        "dead_letter_queue": "exception-dlq"
    },
    "hitl-review-queue": {
        "type": "FIFO",
        "visibility_timeout": 3600,  # 1 hour (human review time)
        "message_retention": 1209600,  # 14 days
        "max_receives": 1,  # No retries for HITL
        "dead_letter_queue": "hitl-dlq"
    }
}
```

### Event Message Schema

```python
class StandardEventMessage(BaseModel):
    """Standard schema for all SQS events."""
    event_id: str  # Unique event ID
    event_type: str  # From EventTaxonomy
    timestamp: datetime
    source_agent: str  # Agent that published the event
    correlation_id: str  # For tracing across agents
    payload: Dict[str, Any]  # Event-specific data
    metadata: Dict[str, Any]  # Additional context
```

### Event Flow Example

```python
# 1. PDF Upload Event
{
    "event_id": "evt_123",
    "event_type": "DOCUMENT_UPLOADED",
    "timestamp": "2025-01-15T10:30:00Z",
    "source_agent": "upload_service",
    "correlation_id": "corr_abc",
    "payload": {
        "document_id": "doc_456",
        "document_path": "s3://bucket/COUNTERPARTY/trade.pdf",
        "source_type": "COUNTERPARTY"
    },
    "metadata": {
        "user_id": "user_789",
        "file_size_bytes": 245678
    }
}

# 2. PDF Processed Event
{
    "event_id": "evt_124",
    "event_type": "PDF_PROCESSED",
    "timestamp": "2025-01-15T10:31:30Z",
    "source_agent": "pdf_adapter_agent",
    "correlation_id": "corr_abc",  # Same correlation ID
    "payload": {
        "document_id": "doc_456",
        "canonical_output_location": "s3://bucket/extracted/COUNTERPARTY/doc_456.json",
        "page_count": 5,
        "processing_time_ms": 8500
    },
    "metadata": {
        "dpi": 300,
        "ocr_confidence": 0.95
    }
}

# 3. Trade Extracted Event
{
    "event_id": "evt_125",
    "event_type": "TRADE_EXTRACTED",
    "timestamp": "2025-01-15T10:33:00Z",
    "source_agent": "trade_extraction_agent",
    "correlation_id": "corr_abc",
    "payload": {
        "trade_id": "GCS382857",
        "source_type": "COUNTERPARTY",
        "table_name": "CounterpartyTradeData"
    },
    "metadata": {
        "extraction_confidence": 0.92,
        "fields_extracted": 28
    }
}
```

## Data Models

### Agent Status Model
```python
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class AgentHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class AgentStatus(BaseModel):
    agent_id: str
    agent_name: str
    health: AgentHealth
    last_heartbeat: datetime
    active_tasks: int
    total_processed: int
    error_count: int
    average_latency_ms: float
```

### Trade Data Model
```python
class TradeData(BaseModel):
    Trade_ID: str
    TRADE_SOURCE: Literal["BANK", "COUNTERPARTY"]
    trade_date: str
    effective_date: str
    maturity_date: str
    notional: float
    currency: str
    commodity_type: str
    product_type: str
    counterparty: str
    s3_source: str
    processing_timestamp: datetime
    # ... additional 20+ fields
```

### Matching Result Model
```python
class MatchClassification(str, Enum):
    MATCHED = "MATCHED"
    PROBABLE_MATCH = "PROBABLE_MATCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BREAK = "BREAK"
    DATA_ERROR = "DATA_ERROR"

class MatchingResult(BaseModel):
    trade_id: str
    classification: MatchClassification
    bank_trade: Optional[TradeData]
    counterparty_trade: Optional[TradeData]
    differences: List[FieldDifference]
    confidence_score: float
    requires_hitl: bool
```

### Audit Trail Model
```python
class AuditRecord(BaseModel):
    record_id: str
    timestamp: datetime
    agent_id: str
    action_type: str
    resource_id: str
    outcome: Literal["SUCCESS", "FAILURE"]
    user_id: Optional[str]
    details: dict
    immutable_hash: str  # SHA-256 hash for tamper-evidence
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

**Note**: Due to the comprehensive nature of this migration (57 correctness properties), the complete properties section, error handling strategy, testing strategy, deployment plan, and additional design details are documented in [design_properties.md](design_properties.md).

### Summary of Key Properties

The system includes 57 correctness properties covering:

- **Functional Parity** (Property 1): Equivalence with CrewAI implementation
- **Agent Independence** (Properties 2-6): Each agent operates independently
- **Orchestration** (Properties 7-10): Proper coordination and monitoring
- **PDF Processing** (Properties 11-15): 300 DPI conversion and OCR
- **Data Extraction** (Properties 16-20): Complete field extraction and routing
- **Trade Matching** (Properties 21-25): Fuzzy matching with tolerances
- **Error Handling** (Properties 26-30): Retry logic and escalation
- **Web Portal** (Properties 31-33): Real-time updates and HITL
- **Audit Trail** (Properties 34-38): Immutable logging and compliance
- **Memory Integration** (Properties 39-42): Context storage and retrieval
- **Observability** (Properties 43-46): Tracing and metrics
- **Gateway Integration** (Properties 47-49): MCP tool usage
- **HITL Workflow** (Properties 50-53): Human review and learning
- **Security** (Properties 54-56): Authentication and authorization
- **Quality Maintenance** (Property 57): OCR accuracy preservation

See [design_properties.md](design_properties.md) for complete property definitions, testing strategy, deployment plan, and operational details.
