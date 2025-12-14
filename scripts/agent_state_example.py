#!/usr/bin/env python3
"""
Example of how to track agent state in production Strands agents.
This shows the pattern for monitoring conversation context and state.
"""

from strands import Agent
from strands_tools import calculator
import json

def track_agent_state_example():
    """Example of tracking agent state for monitoring."""
    
    agent = Agent(
        tools=[calculator],
        system_prompt="You are a financial calculation assistant."
    )
    
    # In production, you'd track this data
    state_metrics = {
        "conversation_length": 0,  # Number of messages in conversation
        "context_tokens": 0,       # Tokens used for context
        "state_size_bytes": 0,     # Size of agent state
        "last_tool_used": None,    # Most recent tool
        "conversation_id": "conv_123",  # Unique conversation ID
    }
    
    # Example conversation
    result1 = agent("Calculate 15% of $10,000")
    
    # Update state tracking
    state_metrics["conversation_length"] += 1
    state_metrics["context_tokens"] = result1.metrics.accumulated_usage.get("totalTokens", 0)
    state_metrics["last_tool_used"] = list(result1.metrics.tool_metrics.keys())[-1] if result1.metrics.tool_metrics else None
    
    # Continue conversation (agent maintains context)
    result2 = agent("Now add $500 to that result")
    
    # Update metrics
    state_metrics["conversation_length"] += 1
    state_metrics["context_tokens"] = result2.metrics.accumulated_usage.get("totalTokens", 0)
    
    print("Agent State Metrics:")
    print(json.dumps(state_metrics, indent=2))
    
    return state_metrics

if __name__ == "__main__":
    track_agent_state_example()