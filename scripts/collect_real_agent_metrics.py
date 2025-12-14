#!/usr/bin/env python3
"""
Production script to collect real metrics from Strands agents.
This demonstrates how to properly collect and store agent metrics.
"""

import boto3
import json
from datetime import datetime, timezone
from decimal import Decimal
from strands import Agent
from strands_tools import calculator, python_repl

# Configuration
TABLE_NAME = "trade-matching-system-agent-registry-production"
REGION = "us-east-1"

def collect_agent_metrics(agent: Agent, agent_id: str, agent_type: str, test_prompt: str):
    """Collect real metrics from a Strands agent execution."""
    
    start_time = datetime.now(timezone.utc)
    
    # Execute agent and collect metrics
    result = agent(test_prompt)
    
    end_time = datetime.now(timezone.utc)
    execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # Extract Strands SDK metrics
    metrics = result.metrics
    usage = metrics.accumulated_usage
    
    # Calculate derived metrics
    tool_metrics = {}
    for tool_name, tool_metric in metrics.tool_metrics.items():
        tool_metrics[tool_name] = {
            "call_count": tool_metric.call_count,
            "success_count": tool_metric.success_count,
            "error_count": tool_metric.error_count,
            "success_rate": tool_metric.success_count / tool_metric.call_count if tool_metric.call_count > 0 else 0,
            "avg_execution_time_ms": tool_metric.total_time * 1000 / tool_metric.call_count if tool_metric.call_count > 0 else 0
        }
    
    # Build agent record
    agent_record = {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "deployment_status": "ACTIVE",
        "last_heartbeat": end_time.isoformat().replace("+00:00", "Z"),
        "description": f"Real metrics from {agent_type} agent",
        
        # Core performance metrics
        "avg_latency_ms": execution_time_ms,
        "total_tokens": usage.get("totalTokens", 0),
        "input_tokens": usage.get("inputTokens", 0),
        "output_tokens": usage.get("outputTokens", 0),
        
        # Strands-specific metrics
        "avg_cycles": metrics.total_cycles,
        "avg_cycle_time_ms": int(sum(metrics.cycle_durations) * 1000 / len(metrics.cycle_durations)) if metrics.cycle_durations else 0,
        "tool_calls": sum(tm.call_count for tm in metrics.tool_metrics.values()),
        "tool_success_rate": Decimal(str(round(
            sum(tm.success_count for tm in metrics.tool_metrics.values()) / 
            sum(tm.call_count for tm in metrics.tool_metrics.values()) 
            if sum(tm.call_count for tm in metrics.tool_metrics.values()) > 0 else 1.0, 4
        ))),
        
        # Execution context
        "model_provider": "amazon.nova-pro-v1:0",  # Would extract from agent.model in real implementation
        "stop_reason": result.stop_reason,
        "tools": list(metrics.tool_metrics.keys()),
        "tool_metrics": tool_metrics,
        
        # Calculated rates
        "success_rate": Decimal("1.0000"),  # Would calculate based on error tracking
        "error_rate": Decimal("0.0000"),    # Would calculate based on error tracking
        "active_tasks": 1,  # Current execution
    }
    
    return agent_record

def update_agent_registry_with_real_metrics():
    """Update the agent registry with real metrics from agent executions."""
    
    # Example agents (in production, these would be your actual trade matching agents)
    test_agents = [
        {
            "agent": Agent(tools=[calculator], system_prompt="You are a PDF processing agent."),
            "agent_id": "pdf_adapter_agent_real",
            "agent_type": "PDF_ADAPTER",
            "test_prompt": "Calculate the file size of a 10-page PDF at 300 DPI"
        },
        {
            "agent": Agent(tools=[python_repl], system_prompt="You are a trade extraction agent."),
            "agent_id": "trade_extraction_agent_real", 
            "agent_type": "TRADE_EXTRACTOR",
            "test_prompt": "Extract trade data: Currency=USD, Notional=1000000, Date=2024-01-15"
        }
    ]
    
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(TABLE_NAME)
        
        print("Collecting real agent metrics...")
        
        for agent_config in test_agents:
            print(f"\nTesting {agent_config['agent_id']}...")
            
            # Collect real metrics
            record = collect_agent_metrics(
                agent_config["agent"],
                agent_config["agent_id"],
                agent_config["agent_type"],
                agent_config["test_prompt"]
            )
            
            # Display metrics
            print(f"  - Execution Time: {record['avg_latency_ms']}ms")
            print(f"  - Cycles: {record['avg_cycles']}")
            print(f"  - Total Tokens: {record['total_tokens']:,}")
            print(f"  - Tools Used: {', '.join(record['tools'])}")
            print(f"  - Stop Reason: {record['stop_reason']}")
            
            # Store in DynamoDB
            table.put_item(Item=record)
            print(f"  ✅ Stored real metrics for {agent_config['agent_id']}")
        
        print(f"\n✅ Successfully collected and stored real agent metrics!")
        
    except Exception as e:
        print(f"❌ Error collecting real metrics: {e}")

if __name__ == "__main__":
    update_agent_registry_with_real_metrics()