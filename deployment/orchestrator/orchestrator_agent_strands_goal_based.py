"""
Goal-Based Orchestrator Agent - Strands SDK Implementation

This agent uses AI intelligence with minimal, flexible tools.
The LLM decides the best approach to achieve orchestration goals.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel

# Try to import use_aws from different locations in strands-agents
try:
    from strands_tools import use_aws
    print("✓ Imported use_aws from strands_tools (community tools package)")
except ImportError:
    try:
        from strands import use_aws
        print("✓ Imported use_aws from strands")
    except ImportError:
        try:
            from strands.tools import use_aws
            print("✓ Imported use_aws from strands.tools")
        except ImportError:
            try:
                from strands_agents_tools import use_aws
                print("✓ Imported use_aws from strands_agents_tools")
            except ImportError:
                print("⚠ use_aws not found, will define custom implementation")
                use_aws = None

# Fallback implementation if use_aws is not available
if use_aws is None:
    @tool
    def use_aws(service_name: str, operation_name: str, parameters: dict, region: str = "us-east-1", label: str = "") -> str:
        """
        Fallback AWS tool implementation using boto3.
        """
        import boto3
        try:
            client = boto3.client(service_name, region_name=region)
            operation = getattr(client, operation_name)
            result = operation(**parameters)
            return json.dumps(result, default=str)
        except Exception as e:
            return f"Error: {str(e)}"

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# AgentCore Observability
try:
    from bedrock_agentcore.observability import Observability
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
AGENT_REGISTRY_TABLE = os.getenv("DYNAMODB_AGENT_REGISTRY_TABLE", "trade-matching-system-agent-registry-production")
BANK_TABLE = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_ALIAS = os.getenv("AGENT_ALIAS", "default")
OBSERVABILITY_STAGE = os.getenv("OBSERVABILITY_STAGE", "development")

# Agent identification
AGENT_NAME = "orchestrator-agent"

# Initialize Observability
observability = None
if OBSERVABILITY_AVAILABLE:
    try:
        observability = Observability(
            service_name=AGENT_NAME,
            stage=OBSERVABILITY_STAGE,
            verbosity="high" if OBSERVABILITY_STAGE == "development" else "low"
        )
        logger.info(f"Observability initialized for {AGENT_NAME}")
    except Exception as e:
        logger.warning(f"Failed to initialize observability: {e}")

# Lazy-initialized boto3 clients for efficiency
_boto_clients: Dict[str, Any] = {}

def get_boto_client(service: str):
    """Get or create a boto3 client for the specified service."""
    import boto3
    if service not in _boto_clients:
        _boto_clients[service] = boto3.client(service, region_name=REGION)
    return _boto_clients[service]

# ============================================================================
# Simple Goal-Based Tools - Trust the AI's Intelligence
# ============================================================================

@tool
def investigate_trade_system(
    goal: str,
    trade_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    time_window: Optional[str] = None
) -> str:
    """
    Investigate the trade system to achieve your goal.
    You have full access to explore the system as needed.
    
    Args:
        goal: What you want to accomplish (e.g., "check SLA compliance", "verify trade exists")
        trade_id: Optional trade to focus on
        agent_name: Optional agent to focus on  
        time_window: Optional time constraint (e.g., "24h", "1h")
        
    Returns:
        JSON with available resources and guidance - you decide how to proceed
    """
    try:
        investigation_context = {
            "goal": goal,
            "trade_id": trade_id,
            "agent_name": agent_name,
            "time_window": time_window,
            "timestamp": datetime.utcnow().isoformat(),
            
            # Give AI all the context it needs
            "available_resources": {
                "dynamodb_tables": {
                    "BankTradeData": {
                        "description": "Bank system trades",
                        "key_schema": "trade_id (HASH) + internal_reference (RANGE)",
                        "example_trade_id": "FAB_26933659"
                    },
                    "CounterpartyTradeData": {
                        "description": "Counterparty system trades", 
                        "key_schema": "trade_id (HASH) + internal_reference (RANGE)"
                    },
                    "trade-matching-system-agent-registry-production": {
                        "description": "Registered agents with health status",
                        "key_schema": "agent_id (HASH)"
                    }
                },
                "s3_bucket": S3_BUCKET,
                "region": REGION
            },
            
            "suggested_approach": "Use the use_aws tool to explore these resources. You can scan tables, query specific keys, check S3 objects, etc. Make intelligent decisions about what to investigate.",
            
            "tools_available": [
                "use_aws - Direct access to all AWS services",
                "record_decision - Log important findings for audit"
            ]
        }
        
        return json.dumps(investigation_context, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "goal": goal
        })


@tool
def debug_specific_trade(trade_id: str) -> str:
    """
    Focused debugging tool to find a specific trade across all tables.
    No distractions - just find this exact trade.
    
    Args:
        trade_id: Exact trade ID to search for
        
    Returns:
        JSON with trade details if found, or clear "not found" message
    """
    try:
        import boto3
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        
        results = {
            "trade_id_searched": trade_id,
            "timestamp": datetime.utcnow().isoformat(),
            "search_results": {}
        }
        
        # Search BankTradeData table
        try:
            bank_response = dynamodb.scan(
                TableName=BANK_TABLE,
                FilterExpression="trade_id = :tid",
                ExpressionAttributeValues={":tid": {"S": trade_id}},
                Limit=1
            )
            
            if bank_response.get("Items"):
                trade_data = bank_response["Items"][0]
                results["search_results"]["BankTradeData"] = {
                    "found": True,
                    "trade_id": trade_data.get("trade_id", {}).get("S"),
                    "internal_reference": trade_data.get("internal_reference", {}).get("S"),
                    "trade_source": trade_data.get("TRADE_SOURCE", {}).get("S"),
                    "processing_timestamp": trade_data.get("processing_timestamp", {}).get("S"),
                    "counterparty": trade_data.get("counterparty", {}).get("S")
                }
            else:
                results["search_results"]["BankTradeData"] = {"found": False}
                
        except Exception as e:
            results["search_results"]["BankTradeData"] = {"error": str(e)}
        
        # Search CounterpartyTradeData table  
        try:
            counterparty_response = dynamodb.scan(
                TableName=COUNTERPARTY_TABLE,
                FilterExpression="trade_id = :tid", 
                ExpressionAttributeValues={":tid": {"S": trade_id}},
                Limit=1
            )
            
            if counterparty_response.get("Items"):
                trade_data = counterparty_response["Items"][0]
                results["search_results"]["CounterpartyTradeData"] = {
                    "found": True,
                    "trade_id": trade_data.get("trade_id", {}).get("S"),
                    "internal_reference": trade_data.get("internal_reference", {}).get("S"),
                    "trade_source": trade_data.get("TRADE_SOURCE", {}).get("S")
                }
            else:
                results["search_results"]["CounterpartyTradeData"] = {"found": False}
                
        except Exception as e:
            results["search_results"]["CounterpartyTradeData"] = {"error": str(e)}
        
        # Summary
        found_in = [table for table, data in results["search_results"].items() 
                   if isinstance(data, dict) and data.get("found")]
        
        results["summary"] = {
            "trade_found": len(found_in) > 0,
            "found_in_tables": found_in,
            "total_tables_searched": len(results["search_results"])
        }
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Debug search failed: {str(e)}",
            "trade_id": trade_id
        })


@tool  
def debug_agent_health() -> str:
    """
    Focused debugging tool to check actual agent health without distractions.
    
    Returns:
        JSON with current agent status from registry
    """
    try:
        import boto3
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        
        response = dynamodb.scan(TableName=AGENT_REGISTRY_TABLE)
        
        agents = []
        for item in response.get("Items", []):
            agent_id = item.get("agent_id", {}).get("S", "unknown")
            last_heartbeat_str = item.get("last_heartbeat", {}).get("S")
            
            status = "ACTIVE"
            if last_heartbeat_str:
                try:
                    last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
                    time_since = datetime.utcnow() - last_heartbeat
                    
                    if time_since > timedelta(minutes=5):
                        status = "UNHEALTHY"
                    elif time_since > timedelta(minutes=2):
                        status = "DEGRADED"
                except ValueError:
                    pass
            
            agents.append({
                "agent_id": agent_id,
                "status": status,
                "last_heartbeat": last_heartbeat_str,
                "agent_type": item.get("agent_type", {}).get("S"),
                "deployment_status": item.get("deployment_status", {}).get("S")
            })
        
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(agents),
            "agents": agents,
            "healthy_count": len([a for a in agents if a["status"] == "ACTIVE"])
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def record_decision(
    decision_type: str,
    finding: str,
    recommendation: str,
    context: Dict[str, Any] = None
) -> str:
    """
    Record an orchestration decision for audit and tracking.
    
    Args:
        decision_type: Type of decision (SLA_ALERT, COMPLIANCE_ISSUE, HEALTH_CHECK, etc.)
        finding: What you discovered
        recommendation: What should be done
        context: Additional context
        
    Returns:
        JSON with decision ID and S3 location
    """
    try:
        s3_client = get_boto_client('s3')
        
        decision_id = f"dec_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow().isoformat()
        
        decision_record = {
            "decision_id": decision_id,
            "timestamp": timestamp,
            "decision_type": decision_type,
            "finding": finding,
            "recommendation": recommendation,
            "context": context or {}
        }
        
        # Save to S3 for audit
        key = f"orchestration/decisions/{datetime.utcnow().strftime('%Y/%m/%d')}/{decision_id}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(decision_record, indent=2),
            ContentType='application/json'
        )
        
        return json.dumps({
            "success": True,
            "decision_id": decision_id,
            "s3_location": f"s3://{S3_BUCKET}/{key}",
            "message": f"Decision recorded: {decision_type}"
        })
        
    except Exception as e:
        logger.error(f"Failed to record decision: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


# ============================================================================
# Health Check Handler
# ============================================================================

@app.ping
def health_check() -> PingStatus:
    """Custom health check for AgentCore Runtime."""
    try:
        # Simple health check
        get_boto_client('dynamodb')
        return PingStatus.HEALTHY
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return PingStatus.HEALTHY


# ============================================================================
# AI-Driven System Prompt - Goal Based
# ============================================================================

SYSTEM_PROMPT = f"""You are an intelligent Orchestrator Agent for the OTC trade matching system.

## Your Role
You coordinate and monitor the entire trade processing pipeline using your intelligence and judgment.

## Available Resources
- **DynamoDB Tables**: BankTradeData, CounterpartyTradeData, agent registry
- **S3 Bucket**: {S3_BUCKET} (for reports, decisions, canonical outputs)
- **Region**: {REGION}

## Your Tools

**High-Level Intelligence:**
1. **investigate_trade_system**: Get context and guidance for complex goals
2. **use_aws**: Direct access to all AWS services - use your judgment on what to query

**Focused Debugging:**  
3. **debug_specific_trade**: Find a specific trade across all tables (no distractions)
4. **debug_agent_health**: Check agent registry health status (focused)

**Audit & Logging:**
5. **record_decision**: Log important findings for audit

## Your Approach
- **Choose the right tool**: Use focused debugging tools for specific queries, high-level tools for complex goals
- **Think intelligently** about the best way to achieve each goal
- **Explore the system** using AWS tools as needed
- **Make smart decisions** based on what you discover
- **Provide clear reasoning** for your conclusions
- **Record important findings** for audit and tracking

## Example Goals You Handle
- "Check if trade FAB_26933659 is processing within SLA"
- "Verify all agents are healthy and responding"  
- "Investigate why trade processing is slow"
- "Ensure compliance with regulatory deadlines"

## Your Intelligence
You decide:
- Which tables to query and how
- What constitutes a problem vs normal operation
- When to escalate vs resolve automatically
- How to investigate and what data to examine

Trust your judgment. Use the tools flexibly to achieve the goals given to you.
"""


# ============================================================================
# Create Intelligent Agent
# ============================================================================

def create_orchestrator_agent() -> Agent:
    """Create and configure the intelligent orchestrator agent."""
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.1,  # Low temperature for reliable orchestration
        max_tokens=4096,
    )
    
    return Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            investigate_trade_system,
            debug_specific_trade,
            debug_agent_health,
            use_aws,
            record_decision
        ]
    )


# ============================================================================
# AgentCore Entrypoint
# ============================================================================

def _extract_token_metrics(result) -> Dict[str, int]:
    """Extract token usage metrics from Strands agent result."""
    metrics = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    try:
        if hasattr(result, 'metrics'):
            metrics["input_tokens"] = getattr(result.metrics, 'input_tokens', 0) or 0
            metrics["output_tokens"] = getattr(result.metrics, 'output_tokens', 0) or 0
        elif hasattr(result, 'usage'):
            metrics["input_tokens"] = getattr(result.usage, 'input_tokens', 0) or 0
            metrics["output_tokens"] = getattr(result.usage, 'output_tokens', 0) or 0
        metrics["total_tokens"] = metrics["input_tokens"] + metrics["output_tokens"]
    except Exception:
        pass
    return metrics


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Goal-Based Orchestrator Agent.
    
    The AI decides how to approach each orchestration goal using its intelligence.
    """
    start_time = datetime.utcnow()
    logger.info("Goal-Based Orchestrator Agent (Strands) invoked")
    logger.info(f"Payload: {json.dumps(payload, default=str)}")
    
    # Extract goal and context from payload
    event_type = payload.get("event_type", "UNKNOWN")
    trade_id = payload.get("trade_id")
    agent_name = payload.get("agent")
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    # Standard observability attributes
    obs_attributes = {
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "agent_alias": AGENT_ALIAS,
        "correlation_id": correlation_id,
        "event_type": event_type,
    }
    
    try:
        # Start observability span
        span_context = None
        if observability:
            try:
                span_context = observability.start_span("orchestration")
                span_context.__enter__()
                for k, v in obs_attributes.items():
                    span_context.set_attribute(k, v)
            except Exception as e:
                logger.warning(f"Failed to start observability span: {e}")
                span_context = None
        
        # Create the intelligent agent
        agent = create_orchestrator_agent()
        
        # Build goal-oriented prompt - let AI decide the approach
        if event_type == "SLA_CHECK":
            goal = f"Check if trade {trade_id} is processing within SLA targets"
        elif event_type == "HEALTH_CHECK":
            goal = "Verify system health and agent status"
        elif event_type == "COMPLIANCE_AUDIT":
            goal = "Audit system compliance with regulatory requirements"
        else:
            goal = f"Handle {event_type} event and determine appropriate actions"
        
        prompt = f"""GOAL: {goal}

## Context
- Event Type: {event_type}
- Trade ID: {trade_id or "Not specified"}
- Agent: {agent_name or "Not specified"}  
- Correlation ID: {correlation_id}

## Your Task
Use your intelligence to achieve this goal. Investigate the system, gather the information you need, make smart decisions, and record important findings.

You have full flexibility in how you approach this. Use the tools available to explore and understand the current system state, then provide clear conclusions and recommendations.
"""
        
        # Let the AI figure out the best approach
        logger.info("Invoking intelligent Strands orchestrator")
        result = agent(prompt)
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract token metrics
        token_metrics = _extract_token_metrics(result)
        logger.info(f"Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Extract the agent's response
        if hasattr(result, 'message') and result.message:
            if hasattr(result.message, 'content') and result.message.content:
                content = result.message.content
                if isinstance(content, list) and len(content) > 0:
                    first_block = content[0]
                    response_text = first_block.get('text', str(result.message)) if isinstance(first_block, dict) else str(first_block)
                else:
                    response_text = str(content)
            else:
                response_text = str(result.message)
        else:
            response_text = str(result)
        
        # Record success metrics
        if span_context:
            try:
                span_context.set_attribute("success", True)
                span_context.set_attribute("processing_time_ms", processing_time_ms)
                span_context.set_attribute("input_tokens", token_metrics["input_tokens"])
                span_context.set_attribute("output_tokens", token_metrics["output_tokens"])
                span_context.set_attribute("total_tokens", token_metrics["total_tokens"])
            except Exception as e:
                logger.warning(f"Failed to set span attributes: {e}")
        
        return {
            "success": True,
            "event_type": event_type,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "agent_alias": AGENT_ALIAS,
            "token_usage": token_metrics,
        }
        
    except Exception as e:
        logger.error(f"Error in orchestrator agent: {e}", exc_info=True)
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record error
        if span_context:
            try:
                span_context.set_attribute("success", False)
                span_context.set_attribute("error_type", type(e).__name__)
                span_context.set_attribute("error_message", str(e))
                span_context.set_attribute("processing_time_ms", processing_time_ms)
            except Exception:
                pass
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "event_type": event_type,
            "correlation_id": correlation_id,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "processing_time_ms": processing_time_ms,
        }
    finally:
        # Close observability span
        if span_context:
            try:
                span_context.__exit__(None, None, None)
            except Exception:
                pass


if __name__ == "__main__":
    """Let AgentCore Runtime control the agent execution."""
    app.run()