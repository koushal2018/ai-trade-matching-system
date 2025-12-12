# AgentCore Memory Resources Configuration
# Note: AgentCore Memory is a managed service that needs to be configured via AWS CLI
# These resources document the configuration that should be applied

# Local file to store AgentCore Memory configuration for CLI deployment
resource "local_file" "agentcore_memory_config" {
  filename = "${path.module}/configs/agentcore_memory_config.json"
  content = jsonencode({
    memory_resources = [
      {
        name        = "${var.project_name}-trade-patterns-${var.environment}"
        description = "Semantic memory for trade patterns and historical context"
        strategy    = "semantic"
        configuration = {
          embedding_model      = "amazon.titan-embed-text-v2:0"
          vector_dimensions    = 1024
          similarity_threshold = 0.7
        }
        retention_policy = {
          enabled = false # No expiration for trade patterns
        }
        tags = {
          Component   = "AgentCore"
          Environment = var.environment
          Purpose     = "TradePatterns"
        }
      },
      {
        name        = "${var.project_name}-processing-history-${var.environment}"
        description = "Event memory for processing history and agent operations"
        strategy    = "event"
        configuration = {
          event_ordering       = "timestamp"
          max_events_per_query = 100
        }
        retention_policy = {
          enabled        = true
          retention_days = 90
        }
        tags = {
          Component   = "AgentCore"
          Environment = var.environment
          Purpose     = "ProcessingHistory"
        }
      },
      {
        name        = "${var.project_name}-exception-patterns-${var.environment}"
        description = "Memory for exception patterns and RL policies"
        strategy    = "semantic"
        configuration = {
          embedding_model      = "amazon.titan-embed-text-v2:0"
          vector_dimensions    = 1024
          similarity_threshold = 0.8
        }
        retention_policy = {
          enabled = false # Keep exception patterns indefinitely for learning
        }
        tags = {
          Component   = "AgentCore"
          Environment = var.environment
          Purpose     = "ExceptionPatterns"
        }
      },
      {
        name        = "${var.project_name}-matching-decisions-${var.environment}"
        description = "Semantic memory for matching decisions and HITL feedback"
        strategy    = "semantic"
        configuration = {
          embedding_model      = "amazon.titan-embed-text-v2:0"
          vector_dimensions    = 1024
          similarity_threshold = 0.75
        }
        retention_policy = {
          enabled = false # Keep matching decisions for continuous learning
        }
        tags = {
          Component   = "AgentCore"
          Environment = var.environment
          Purpose     = "MatchingDecisions"
        }
      }
    ]
  })
}

# Create deployment script for AgentCore Memory
resource "local_file" "deploy_agentcore_memory_script" {
  filename = "${path.module}/scripts/deploy_agentcore_memory.sh"
  content  = <<-EOT
#!/bin/bash
set -e

echo "Deploying AgentCore Memory resources..."

# Read configuration
CONFIG_FILE="${path.module}/configs/agentcore_memory_config.json"

# Deploy each memory resource using AWS CLI
# Note: Replace with actual AgentCore CLI commands when available

# Trade Patterns Memory (Semantic)
echo "Creating trade patterns memory resource..."
aws bedrock-agent create-memory-resource \
  --name "${var.project_name}-trade-patterns-${var.environment}" \
  --description "Semantic memory for trade patterns and historical context" \
  --memory-type SEMANTIC \
  --embedding-model-arn "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0" \
  --region ${var.aws_region} \
  --tags Component=AgentCore,Environment=${var.environment},Purpose=TradePatterns

# Processing History Memory (Event)
echo "Creating processing history memory resource..."
aws bedrock-agent create-memory-resource \
  --name "${var.project_name}-processing-history-${var.environment}" \
  --description "Event memory for processing history and agent operations" \
  --memory-type EVENT \
  --retention-days 90 \
  --region ${var.aws_region} \
  --tags Component=AgentCore,Environment=${var.environment},Purpose=ProcessingHistory

# Exception Patterns Memory (Semantic)
echo "Creating exception patterns memory resource..."
aws bedrock-agent create-memory-resource \
  --name "${var.project_name}-exception-patterns-${var.environment}" \
  --description "Memory for exception patterns and RL policies" \
  --memory-type SEMANTIC \
  --embedding-model-arn "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0" \
  --region ${var.aws_region} \
  --tags Component=AgentCore,Environment=${var.environment},Purpose=ExceptionPatterns

# Matching Decisions Memory (Semantic)
echo "Creating matching decisions memory resource..."
aws bedrock-agent create-memory-resource \
  --name "${var.project_name}-matching-decisions-${var.environment}" \
  --description "Semantic memory for matching decisions and HITL feedback" \
  --memory-type SEMANTIC \
  --embedding-model-arn "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0" \
  --region ${var.aws_region} \
  --tags Component=AgentCore,Environment=${var.environment},Purpose=MatchingDecisions

echo "AgentCore Memory resources deployed successfully!"
EOT

  file_permission = "0755"
}

# Create README for AgentCore Memory setup
resource "local_file" "agentcore_memory_readme" {
  filename = "${path.module}/configs/AGENTCORE_MEMORY_README.md"
  content  = <<-EOT
# AgentCore Memory Setup

This directory contains configuration for AgentCore Memory resources.

## Memory Resources

### 1. Trade Patterns Memory (Semantic)
- **Name**: ${var.project_name}-trade-patterns-${var.environment}
- **Strategy**: Semantic
- **Purpose**: Store trade patterns, counterparty information, and historical context
- **Retention**: Indefinite (no expiration)
- **Embedding Model**: amazon.titan-embed-text-v2:0

### 2. Processing History Memory (Event)
- **Name**: ${var.project_name}-processing-history-${var.environment}
- **Strategy**: Event
- **Purpose**: Track agent operations, processing steps, and workflow history
- **Retention**: 90 days
- **Ordering**: Timestamp-based

### 3. Exception Patterns Memory (Semantic)
- **Name**: ${var.project_name}-exception-patterns-${var.environment}
- **Strategy**: Semantic
- **Purpose**: Store error patterns, RL policies, and exception resolution strategies
- **Retention**: Indefinite (for continuous learning)
- **Embedding Model**: amazon.titan-embed-text-v2:0

### 4. Matching Decisions Memory (Semantic)
- **Name**: ${var.project_name}-matching-decisions-${var.environment}
- **Strategy**: Semantic
- **Purpose**: Store matching decisions, HITL feedback, and scoring patterns
- **Retention**: Indefinite (for continuous learning)
- **Embedding Model**: amazon.titan-embed-text-v2:0

## Deployment

### Using AWS CLI (Manual)

Run the deployment script:
```bash
cd ${path.module}/scripts
./deploy_agentcore_memory.sh
```

### Using AgentCore CLI (Recommended)

Once AgentCore CLI is available, use:
```bash
agentcore memory create --config ${path.module}/configs/agentcore_memory_config.json
```

## Verification

List all memory resources:
```bash
aws bedrock-agent list-memory-resources --region ${var.aws_region}
```

Get details of a specific memory resource:
```bash
aws bedrock-agent describe-memory-resource \
  --memory-resource-id <resource-id> \
  --region ${var.aws_region}
```

## Integration with Agents

Each agent should be configured to use the appropriate memory resources:

- **PDF Adapter Agent**: processing-history
- **Trade Extraction Agent**: trade-patterns, processing-history
- **Trade Matching Agent**: trade-patterns, matching-decisions
- **Exception Management Agent**: exception-patterns, processing-history
- **Orchestrator Agent**: processing-history

## Memory Operations

### Store Data
```python
from bedrock_agentcore import Memory

memory = Memory(resource_name="${var.project_name}-trade-patterns-${var.environment}")
memory.store({
    "trade_id": "GCS382857",
    "counterparty": "ABC Corp",
    "notional": 1000000,
    "pattern": "commodity_swap"
})
```

### Retrieve Data
```python
results = memory.query("commodity swap with ABC Corp", top_k=5)
```

### Event Memory
```python
event_memory = Memory(resource_name="${var.project_name}-processing-history-${var.environment}")
event_memory.add_event({
    "timestamp": "2025-01-15T10:30:00Z",
    "agent": "pdf_adapter",
    "action": "pdf_processed",
    "trade_id": "GCS382857"
})
```

## Monitoring

Monitor memory usage and performance:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgent \
  --metric-name MemoryStorageUsed \
  --dimensions Name=MemoryResourceName,Value=${var.project_name}-trade-patterns-${var.environment} \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 3600 \
  --statistics Average \
  --region ${var.aws_region}
```

## Cleanup

To delete memory resources:
```bash
aws bedrock-agent delete-memory-resource \
  --memory-resource-id <resource-id> \
  --region ${var.aws_region}
```
EOT
}

# Outputs
output "agentcore_memory_config_file" {
  description = "Path to AgentCore Memory configuration file"
  value       = local_file.agentcore_memory_config.filename
}

output "agentcore_memory_deployment_script" {
  description = "Path to AgentCore Memory deployment script"
  value       = local_file.deploy_agentcore_memory_script.filename
}

output "agentcore_memory_resources" {
  description = "List of AgentCore Memory resource names"
  value = [
    "${var.project_name}-trade-patterns-${var.environment}",
    "${var.project_name}-processing-history-${var.environment}",
    "${var.project_name}-exception-patterns-${var.environment}",
    "${var.project_name}-matching-decisions-${var.environment}"
  ]
}
