#!/usr/bin/env python3
"""Seed the AgentRegistry table with the 4 Strands agents."""

import boto3
from datetime import datetime

dynamodb = boto3.client('dynamodb', region_name='us-east-1')

AGENTS = [
    {
        "agent_id": {"S": "pdf_adapter"},
        "agent_name": {"S": "PDF Adapter"},
        "description": {"S": "Downloads PDFs from S3 and extracts text using Bedrock multimodal"},
        "status": {"S": "HEALTHY"},
        "last_heartbeat": {"S": datetime.utcnow().isoformat() + "Z"},
        "avg_latency_ms": {"N": "2500"},
        "throughput_per_hour": {"N": "45"},
        "error_rate": {"N": "0.02"},
        "active_tasks": {"N": "0"},
    },
    {
        "agent_id": {"S": "trade_extractor"},
        "agent_name": {"S": "Trade Extraction"},
        "description": {"S": "Extracts structured trade data from canonical output"},
        "status": {"S": "HEALTHY"},
        "last_heartbeat": {"S": datetime.utcnow().isoformat() + "Z"},
        "avg_latency_ms": {"N": "3200"},
        "throughput_per_hour": {"N": "40"},
        "error_rate": {"N": "0.01"},
        "active_tasks": {"N": "0"},
    },
    {
        "agent_id": {"S": "trade_matcher"},
        "agent_name": {"S": "Trade Matching"},
        "description": {"S": "Matches bank and counterparty trades by attributes"},
        "status": {"S": "HEALTHY"},
        "last_heartbeat": {"S": datetime.utcnow().isoformat() + "Z"},
        "avg_latency_ms": {"N": "4100"},
        "throughput_per_hour": {"N": "35"},
        "error_rate": {"N": "0.03"},
        "active_tasks": {"N": "0"},
    },
    {
        "agent_id": {"S": "exception_handler"},
        "agent_name": {"S": "Exception Handler"},
        "description": {"S": "Analyzes exceptions and calculates SLA deadlines"},
        "status": {"S": "HEALTHY"},
        "last_heartbeat": {"S": datetime.utcnow().isoformat() + "Z"},
        "avg_latency_ms": {"N": "1800"},
        "throughput_per_hour": {"N": "50"},
        "error_rate": {"N": "0.01"},
        "active_tasks": {"N": "0"},
    },
]

def seed_agents():
    print("Seeding AgentRegistry table...")
    for agent in AGENTS:
        try:
            dynamodb.put_item(TableName="AgentRegistry", Item=agent)
            print(f"  ✓ Added {agent['agent_name']['S']}")
        except Exception as e:
            print(f"  ✗ Failed to add {agent['agent_name']['S']}: {e}")
    print("Done!")

if __name__ == "__main__":
    seed_agents()
