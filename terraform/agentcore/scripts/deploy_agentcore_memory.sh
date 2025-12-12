#!/bin/bash
set -e

echo "Deploying AgentCore Memory resources..."

# Read configuration
CONFIG_FILE="./configs/agentcore_memory_config.json"

# Deploy each memory resource using AWS CLI
# Note: Replace with actual AgentCore CLI commands when available

# Trade Patterns Memory (Semantic)
echo "Creating trade patterns memory resource..."
aws bedrock-agent create-memory-resource \
  --name "trade-matching-system-trade-patterns-production" \
  --description "Semantic memory for trade patterns and historical context" \
  --memory-type SEMANTIC \
  --embedding-model-arn "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0" \
  --region us-east-1 \
  --tags Component=AgentCore,Environment=production,Purpose=TradePatterns

# Processing History Memory (Event)
echo "Creating processing history memory resource..."
aws bedrock-agent create-memory-resource \
  --name "trade-matching-system-processing-history-production" \
  --description "Event memory for processing history and agent operations" \
  --memory-type EVENT \
  --retention-days 90 \
  --region us-east-1 \
  --tags Component=AgentCore,Environment=production,Purpose=ProcessingHistory

# Exception Patterns Memory (Semantic)
echo "Creating exception patterns memory resource..."
aws bedrock-agent create-memory-resource \
  --name "trade-matching-system-exception-patterns-production" \
  --description "Memory for exception patterns and RL policies" \
  --memory-type SEMANTIC \
  --embedding-model-arn "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0" \
  --region us-east-1 \
  --tags Component=AgentCore,Environment=production,Purpose=ExceptionPatterns

# Matching Decisions Memory (Semantic)
echo "Creating matching decisions memory resource..."
aws bedrock-agent create-memory-resource \
  --name "trade-matching-system-matching-decisions-production" \
  --description "Semantic memory for matching decisions and HITL feedback" \
  --memory-type SEMANTIC \
  --embedding-model-arn "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0" \
  --region us-east-1 \
  --tags Component=AgentCore,Environment=production,Purpose=MatchingDecisions

echo "AgentCore Memory resources deployed successfully!"
