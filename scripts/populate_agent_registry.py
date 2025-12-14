#!/usr/bin/env python3
"""
Script to populate the Agent Registry DynamoDB table with realistic mock data.
This simulates real agent metrics for testing the web portal.
"""

import boto3
import json
from datetime import datetime, timezone, timedelta
import random
from decimal import Decimal

# Configuration
TABLE_NAME = "trade-matching-system-agent-registry-production"
REGION = "us-east-1"

# Agent definitions with realistic performance characteristics
AGENTS = [
    {
        "agent_id": "pdf_adapter_agent",
        "agent_type": "PDF_ADAPTER",
        "base_latency": 15000,  # PDF processing is slower
        "base_throughput": 25,
        "base_error_rate": 0.015,
        "tools": ["download_pdf_from_s3", "extract_text_with_bedrock", "save_canonical_output"],
        "description": "Downloads PDFs from S3 and extracts text using Bedrock multimodal"
    },
    {
        "agent_id": "trade_extraction_agent", 
        "agent_type": "TRADE_EXTRACTOR",
        "base_latency": 8000,   # Text extraction is fast
        "base_throughput": 45,
        "base_error_rate": 0.008,
        "tools": ["use_aws", "store_trade_in_dynamodb"],
        "description": "Extracts structured trade data from canonical output"
    },
    {
        "agent_id": "trade_matching_agent",
        "agent_type": "TRADE_MATCHER", 
        "base_latency": 12000,  # Matching logic takes time
        "base_throughput": 35,
        "base_error_rate": 0.012,
        "tools": ["scan_trades_table", "save_matching_report"],
        "description": "Matches trades by attributes across bank and counterparty tables"
    },
    {
        "agent_id": "exception_manager",
        "agent_type": "EXCEPTION_HANDLER",
        "base_latency": 3000,   # Exception handling is fast
        "base_throughput": 60,
        "base_error_rate": 0.005,
        "tools": ["get_severity_guidelines", "store_exception_record"],
        "description": "Analyzes exceptions and determines severity with SLA tracking"
    },
    {
        "agent_id": "orchestrator_otc",
        "agent_type": "ORCHESTRATOR",
        "base_latency": 2000,   # Orchestration is very fast
        "base_throughput": 80,
        "base_error_rate": 0.003,
        "tools": ["use_aws", "scan_trades_table"],
        "description": "Coordinates agent handoffs and monitors SLA compliance"
    }
]

def generate_realistic_metrics(agent_config):
    """Generate realistic metrics with some variation."""
    base_latency = agent_config["base_latency"]
    base_throughput = agent_config["base_throughput"] 
    base_error_rate = agent_config["base_error_rate"]
    
    # Add realistic variation (±20%)
    latency_variation = random.uniform(0.8, 1.2)
    throughput_variation = random.uniform(0.8, 1.2)
    error_variation = random.uniform(0.5, 1.5)
    
    # Calculate realistic token usage based on agent type
    if agent_config["agent_type"] == "PDF_ADAPTER":
        # PDF processing uses more tokens for OCR
        base_tokens = random.randint(8000, 15000)
    elif agent_config["agent_type"] == "TRADE_EXTRACTOR":
        # Text extraction uses moderate tokens
        base_tokens = random.randint(5000, 10000)
    elif agent_config["agent_type"] == "TRADE_MATCHER":
        # Matching uses many tokens for comparison
        base_tokens = random.randint(10000, 20000)
    else:
        # Other agents use fewer tokens
        base_tokens = random.randint(2000, 6000)
    
    input_tokens = int(base_tokens * 0.8)
    output_tokens = int(base_tokens * 0.2)
    
    return {
        "avg_latency_ms": int(base_latency * latency_variation),
        "throughput_per_hour": int(base_throughput * throughput_variation),
        "error_rate": Decimal(str(round(min(0.05, base_error_rate * error_variation), 4))),  # Cap at 5%
        "total_tokens": input_tokens + output_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "avg_cycles": random.randint(2, 5),
        "tool_calls": random.randint(3, 8),
        "success_rate": Decimal(str(round(max(0.90, 1.0 - (base_error_rate * error_variation)), 4))),
        "active_tasks": random.randint(0, 5),
        # Additional Strands SDK metrics
        "avg_cycle_time_ms": random.randint(800, 2000),  # Average time per cycle
        "tool_success_rate": Decimal(str(round(max(0.95, 1.0 - (base_error_rate * error_variation * 0.5)), 4))),  # Tools are more reliable
        "cache_hit_rate": Decimal(str(round(random.uniform(0.15, 0.35), 4))),  # Cache efficiency for repeated operations
        "model_provider": "amazon.nova-pro-v1:0",  # Track which model is being used
    }

def create_agent_record(agent_config):
    """Create a complete agent registry record."""
    metrics = generate_realistic_metrics(agent_config)
    
    # Simulate recent heartbeat (within last 2 minutes)
    heartbeat_age = random.randint(10, 120)  # 10 seconds to 2 minutes
    last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=heartbeat_age)
    
    return {
        "agent_id": agent_config["agent_id"],
        "agent_type": agent_config["agent_type"],
        "deployment_status": "ACTIVE",
        "last_heartbeat": last_heartbeat.isoformat().replace("+00:00", "Z"),
        "description": agent_config["description"],
        "tools": agent_config["tools"],
        **metrics
    }

def populate_table():
    """Populate the DynamoDB table with mock agent data."""
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(TABLE_NAME)
        
        print(f"Populating {TABLE_NAME} with mock agent data...")
        
        # Create and insert agent records
        for agent_config in AGENTS:
            record = create_agent_record(agent_config)
            
            print(f"Inserting {record['agent_id']} ({agent_config['agent_type']}):")
            print(f"  - Description: {record['description']}")
            print(f"  - Tools: {', '.join(record['tools'])}")
            print(f"  - Latency: {record['avg_latency_ms']}ms")
            print(f"  - Throughput: {record['throughput_per_hour']}/hr")
            print(f"  - Error Rate: {float(record['error_rate']):.1%}")
            print(f"  - Tokens: {record['total_tokens']:,}")
            print(f"  - Success Rate: {float(record['success_rate']):.1%}")
            print(f"  - Model: {record['model_provider']}")
            
            # Insert into DynamoDB
            table.put_item(Item=record)
            
        print(f"\n✅ Successfully populated {len(AGENTS)} agent records!")
        print(f"🌐 View the results at: http://localhost:3000")
        print(f"📊 Check agent health status in the web portal dashboard")
        print(f"🔍 Monitor metrics in real-time using the AgentHealthPanel component")
        
        # Verify data was inserted correctly
        print(f"\n🔍 Verifying data insertion...")
        for agent_config in AGENTS:
            try:
                response = table.get_item(Key={"agent_id": agent_config["agent_id"]})
                if "Item" in response:
                    print(f"  ✅ {agent_config['agent_id']}: Successfully stored")
                else:
                    print(f"  ❌ {agent_config['agent_id']}: Not found after insertion")
            except Exception as verify_error:
                print(f"  ⚠️  {agent_config['agent_id']}: Verification failed - {verify_error}")
        
    except Exception as e:
        print(f"❌ Error populating table: {e}")
        print(f"Make sure:")
        print(f"  1. AWS credentials are configured")
        print(f"  2. DynamoDB table '{TABLE_NAME}' exists")
        print(f"  3. You have write permissions to the table")

if __name__ == "__main__":
    populate_table()