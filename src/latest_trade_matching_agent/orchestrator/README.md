# Orchestrator Agent Components

This directory contains the components for the Orchestrator Agent, which provides lightweight governance through SLA monitoring, compliance checking, and control command issuance.

## Overview

The Orchestrator Agent is a governance agent that:
- Monitors SLAs for all agents in the system
- Checks compliance with data integrity and regulatory requirements
- Issues control commands when violations are detected
- Aggregates metrics from all agents
- Provides system-wide status reporting

**Key Principle**: The Orchestrator does NOT directly invoke other agents. It monitors events and issues control commands reactively.

## Components

### 1. SLA Monitor Tool (`sla_monitor.py`)

Monitors Service Level Agreement compliance for all agents.

**Features**:
- Tracks processing time, throughput, and error rates
- Compares actual metrics against SLA targets from AgentRegistry
- Detects violations and calculates severity
- Provides system-wide and per-agent SLA status

**Usage**:
```python
from orchestrator import SLAMonitorTool

monitor = SLAMonitorTool()

# Check specific agent
status = monitor.check_agent_sla("pdf_adapter_agent", time_window_minutes=60)

# Check all agents
all_statuses = monitor.check_all_agents_sla(time_window_minutes=60)

# Get system-wide status
system_status = monitor.get_system_wide_sla_status(time_window_minutes=60)
```

**SLA Metrics**:
- `processing_time_ms`: Time to process a single item (lower is better)
- `throughput_per_hour`: Items processed per hour (higher is better)
- `error_rate`: Percentage of failed operations (lower is better)
- `latency_ms`: Response latency (lower is better)

**Violation Severity**:
- `LOW`: < 10% deviation from target
- `MEDIUM`: 10-25% deviation
- `HIGH`: 25-50% deviation
- `CRITICAL`: > 50% deviation

### 2. Compliance Checker Tool (`compliance_checker.py`)

Checks compliance with data integrity and regulatory requirements.

**Features**:
- Validates TRADE_SOURCE matches table location
- Checks required fields are present
- Detects data integrity violations
- Provides remediation recommendations

**Usage**:
```python
from orchestrator import ComplianceCheckerTool

checker = ComplianceCheckerTool()

# Check data integrity
status = checker.check_data_integrity(sample_size=100)

# Check specific trade routing
status = checker.check_trade_source_routing("GCS382857")

# Check regulatory requirements
status = checker.check_regulatory_requirements()

# Check all compliance
status = checker.check_all_compliance(sample_size=100)
```

**Compliance Checks**:
- `DATA_INTEGRITY`: TRADE_SOURCE matches table location
- `TRADE_SOURCE_ROUTING`: Trades are in correct tables
- `FIELD_VALIDATION`: Required fields are present
- `REGULATORY_REQUIREMENTS`: Regulatory compliance

**Violation Severity**:
- `LOW`: Minor issues, no immediate action needed
- `MEDIUM`: Issues requiring attention
- `HIGH`: Serious issues requiring prompt action
- `CRITICAL`: Critical issues requiring immediate action

### 3. Control Command Tool (`control_command.py`)

Issues control commands to agents and queues.

**Features**:
- Pause/resume processing
- Adjust priorities
- Trigger escalations
- Control queue processing
- Manage agent scaling

**Usage**:
```python
from orchestrator import ControlCommandTool

control = ControlCommandTool()

# Pause agent
result = control.pause_processing(
    agent_id="pdf_adapter_agent",
    reason="High error rate detected"
)

# Resume agent
result = control.resume_processing(
    agent_id="pdf_adapter_agent",
    reason="Issue resolved"
)

# Adjust priority
result = control.adjust_priority(
    agent_id="trade_matching_agent",
    priority_level=1,  # 1=highest, 5=lowest
    reason="Critical trades pending"
)

# Trigger escalation
result = control.trigger_escalation(
    resource_id="GCS382857",
    resource_type="trade",
    escalation_level="COMPLIANCE",
    reason="Data integrity violation"
)
```

**Command Types**:
- `PAUSE_PROCESSING`: Pause agent or queue
- `RESUME_PROCESSING`: Resume agent or queue
- `ADJUST_PRIORITY`: Change processing priority
- `TRIGGER_ESCALATION`: Escalate to human operators
- `SCALE_UP`: Increase agent instances
- `SCALE_DOWN`: Decrease agent instances

**Escalation Levels**:
- `OPS_DESK`: Operations desk for routine issues
- `SENIOR_OPS`: Senior operations for complex issues
- `COMPLIANCE`: Compliance team for regulatory issues
- `ENGINEERING`: Engineering team for technical issues

## Orchestrator Agent

The main Orchestrator Agent (`agents/orchestrator_agent.py`) integrates all three tools.

**Event-Driven Architecture**:
1. Subscribes to `orchestrator-monitoring-queue` (fanout from all agent queues)
2. Processes events from all agents
3. Performs periodic SLA checks (every 5 minutes by default)
4. Performs periodic compliance checks (every 15 minutes by default)
5. Issues control commands when violations detected

**Usage**:
```python
from agents import OrchestratorAgent

# Initialize agent
agent = OrchestratorAgent()

# Register in AgentRegistry
agent.register()

# Get system status
status = agent.get_system_status()

# Run continuously
agent.run(continuous=True)
```

**Monitoring Flow**:
```
All Agent Events → orchestrator-monitoring-queue → Orchestrator Agent
                                                    ↓
                                            SLA Monitor Tool
                                            Compliance Checker Tool
                                                    ↓
                                            Control Command Tool
                                                    ↓
                                            Agents/Queues
```

## Configuration

### SLA Targets

SLA targets are defined in the AgentRegistry for each agent:

```python
sla_targets = {
    "processing_time_ms": 30000.0,  # 30 seconds
    "throughput_per_hour": 120.0,   # 120 items/hour
    "error_rate": 0.05              # 5% error rate
}
```

### Check Intervals

Configure how often the Orchestrator performs checks:

```python
agent = OrchestratorAgent(
    sla_check_interval_minutes=5,        # Check SLAs every 5 minutes
    compliance_check_interval_minutes=15  # Check compliance every 15 minutes
)
```

## Metrics

The Orchestrator emits metrics to CloudWatch:

**Orchestrator Metrics**:
- `EventsProcessed`: Total events processed
- `SLAViolationsDetected`: Number of SLA violations
- `ComplianceViolationsDetected`: Number of compliance violations
- `ControlCommandsIssued`: Number of control commands issued

**System Metrics**:
- `SystemSLACompliance`: Overall SLA compliance percentage
- `SystemCompliancePercentage`: Overall compliance percentage
- `SLAViolations`: Current SLA violations count
- `ComplianceViolations`: Current compliance violations count

## Testing

Run individual tools:

```bash
# Test SLA Monitor
python -m src.latest_trade_matching_agent.orchestrator.sla_monitor

# Test Compliance Checker
python -m src.latest_trade_matching_agent.orchestrator.compliance_checker

# Test Control Command
python -m src.latest_trade_matching_agent.orchestrator.control_command
```

Run Orchestrator Agent:

```bash
# Register agent
python src/latest_trade_matching_agent/agents/orchestrator_agent.py register

# Get system status
python src/latest_trade_matching_agent/agents/orchestrator_agent.py status

# Test with sample event
python src/latest_trade_matching_agent/agents/orchestrator_agent.py test

# Run continuously
python src/latest_trade_matching_agent/agents/orchestrator_agent.py
```

## Requirements Validation

This implementation validates the following requirements:

- **3.1**: Orchestrator monitors and coordinates all agents
- **4.1**: Orchestrator initializes and registers all agents
- **4.2**: Orchestrator detects failures and triggers recovery
- **4.3**: Orchestrator provides real-time status of all agents
- **4.4**: Orchestrator coordinates handoffs between agents
- **4.5**: Orchestrator aggregates metrics from all agents

## Architecture Notes

**Lightweight Governance**: The Orchestrator provides governance without being a bottleneck:
- Does NOT directly invoke agents (agents are event-driven)
- Monitors passively through event fanout
- Issues control commands reactively when violations detected
- Scales independently of agent workload

**Event-Driven Monitoring**: All agent events are fanned out to the orchestrator-monitoring-queue:
- PDF processing events
- Extraction events
- Matching events
- Exception events
- All events include processing metrics

**Reactive Control**: The Orchestrator issues commands based on detected violations:
- SLA violations → Pause agent, trigger escalation
- Compliance violations → Escalate to appropriate team
- High error rates → Pause for investigation
- Low throughput → Monitor for scaling needs
