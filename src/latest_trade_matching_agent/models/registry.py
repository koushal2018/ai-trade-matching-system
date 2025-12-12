"""
Agent Registry Models and Operations

This module provides the agent registry system for tracking and managing
all agents in the AgentCore deployment.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
import boto3
from decimal import Decimal


class ScalingConfig(BaseModel):
    """Configuration for agent auto-scaling."""
    min_instances: int = Field(default=1, ge=1)
    max_instances: int = Field(default=10, ge=1)
    target_queue_depth: int = Field(default=100, ge=1)
    scale_up_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    scale_down_threshold: float = Field(default=0.2, ge=0.0, le=1.0)


class AgentRegistryEntry(BaseModel):
    """
    Registry entry for an agent in the system.
    
    Validates: Requirements 4.1, 4.3
    """
    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_name: str = Field(..., description="Human-readable agent name")
    agent_type: Literal["ORCHESTRATOR", "ADAPTER", "EXTRACTOR", "MATCHER", "EXCEPTION_HANDLER"] = Field(
        ..., description="Type of agent"
    )
    version: str = Field(..., description="Agent version")
    capabilities: List[str] = Field(default_factory=list, description="List of agent capabilities")
    event_subscriptions: List[str] = Field(default_factory=list, description="SQS queues this agent subscribes to")
    event_publications: List[str] = Field(default_factory=list, description="SQS queues this agent publishes to")
    sla_targets: Dict[str, float] = Field(default_factory=dict, description="SLA targets (e.g., latency_ms, throughput)")
    scaling_config: ScalingConfig = Field(default_factory=ScalingConfig, description="Auto-scaling configuration")
    deployment_status: Literal["ACTIVE", "INACTIVE", "DEGRADED"] = Field(
        default="ACTIVE", description="Current deployment status"
    )
    last_heartbeat: Optional[datetime] = Field(default=None, description="Last heartbeat timestamp")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Current agent metrics")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Registration timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    def to_dynamodb_format(self) -> dict:
        """Convert to DynamoDB typed format."""
        return {
            "agent_id": {"S": self.agent_id},
            "agent_name": {"S": self.agent_name},
            "agent_type": {"S": self.agent_type},
            "version": {"S": self.version},
            "capabilities": {"L": [{"S": cap} for cap in self.capabilities]},
            "event_subscriptions": {"L": [{"S": sub} for sub in self.event_subscriptions]},
            "event_publications": {"L": [{"S": pub} for pub in self.event_publications]},
            "sla_targets": {"M": {k: {"N": str(v)} for k, v in self.sla_targets.items()}},
            "scaling_config": {"M": {
                "min_instances": {"N": str(self.scaling_config.min_instances)},
                "max_instances": {"N": str(self.scaling_config.max_instances)},
                "target_queue_depth": {"N": str(self.scaling_config.target_queue_depth)},
                "scale_up_threshold": {"N": str(self.scaling_config.scale_up_threshold)},
                "scale_down_threshold": {"N": str(self.scaling_config.scale_down_threshold)}
            }},
            "deployment_status": {"S": self.deployment_status},
            "last_heartbeat": {"S": self.last_heartbeat.isoformat() if self.last_heartbeat else ""},
            "metrics": {"M": {k: {"N": str(v)} for k, v in self.metrics.items()}},
            "created_at": {"S": self.created_at.isoformat()},
            "updated_at": {"S": self.updated_at.isoformat()}
        }

    @classmethod
    def from_dynamodb_format(cls, item: dict) -> "AgentRegistryEntry":
        """Create from DynamoDB typed format."""
        return cls(
            agent_id=item["agent_id"]["S"],
            agent_name=item["agent_name"]["S"],
            agent_type=item["agent_type"]["S"],
            version=item["version"]["S"],
            capabilities=[cap["S"] for cap in item.get("capabilities", {}).get("L", [])],
            event_subscriptions=[sub["S"] for sub in item.get("event_subscriptions", {}).get("L", [])],
            event_publications=[pub["S"] for pub in item.get("event_publications", {}).get("L", [])],
            sla_targets={k: float(v["N"]) for k, v in item.get("sla_targets", {}).get("M", {}).items()},
            scaling_config=ScalingConfig(
                min_instances=int(item.get("scaling_config", {}).get("M", {}).get("min_instances", {}).get("N", "1")),
                max_instances=int(item.get("scaling_config", {}).get("M", {}).get("max_instances", {}).get("N", "10")),
                target_queue_depth=int(item.get("scaling_config", {}).get("M", {}).get("target_queue_depth", {}).get("N", "100")),
                scale_up_threshold=float(item.get("scaling_config", {}).get("M", {}).get("scale_up_threshold", {}).get("N", "0.8")),
                scale_down_threshold=float(item.get("scaling_config", {}).get("M", {}).get("scale_down_threshold", {}).get("N", "0.2"))
            ),
            deployment_status=item.get("deployment_status", {}).get("S", "ACTIVE"),
            last_heartbeat=datetime.fromisoformat(item["last_heartbeat"]["S"]) if item.get("last_heartbeat", {}).get("S") else None,
            metrics={k: float(v["N"]) for k, v in item.get("metrics", {}).get("M", {}).items()},
            created_at=datetime.fromisoformat(item["created_at"]["S"]),
            updated_at=datetime.fromisoformat(item["updated_at"]["S"])
        )


class AgentRegistry:
    """
    Agent Registry for managing agent lifecycle and discovery.
    
    Validates: Requirements 4.1, 4.3
    """
    
    def __init__(self, table_name: str = "AgentRegistry", region_name: str = "us-east-1"):
        """Initialize the agent registry."""
        self.table_name = table_name
        self.region_name = region_name
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
    
    def register_agent(self, entry: AgentRegistryEntry) -> dict:
        """
        Register a new agent in the registry.
        
        Args:
            entry: AgentRegistryEntry to register
            
        Returns:
            dict: Response from DynamoDB
            
        Validates: Requirements 4.1
        """
        try:
            response = self.dynamodb.put_item(
                TableName=self.table_name,
                Item=entry.to_dynamodb_format()
            )
            return {
                "success": True,
                "agent_id": entry.agent_id,
                "message": f"Agent {entry.agent_name} registered successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to register agent {entry.agent_name}"
            }
    
    def update_agent_status(
        self, 
        agent_id: str, 
        deployment_status: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None,
        last_heartbeat: Optional[datetime] = None
    ) -> dict:
        """
        Update agent status and metrics.
        
        Args:
            agent_id: Agent identifier
            deployment_status: New deployment status (ACTIVE, INACTIVE, DEGRADED)
            metrics: Updated metrics dictionary
            last_heartbeat: Heartbeat timestamp
            
        Returns:
            dict: Response from DynamoDB
            
        Validates: Requirements 4.3
        """
        try:
            # Build update expression
            update_parts = []
            expression_values = {}
            expression_names = {}
            
            if deployment_status:
                update_parts.append("#status = :status")
                expression_values[":status"] = {"S": deployment_status}
                expression_names["#status"] = "deployment_status"
            
            if metrics:
                update_parts.append("#metrics = :metrics")
                expression_values[":metrics"] = {"M": {k: {"N": str(v)} for k, v in metrics.items()}}
                expression_names["#metrics"] = "metrics"
            
            if last_heartbeat:
                update_parts.append("last_heartbeat = :heartbeat")
                expression_values[":heartbeat"] = {"S": last_heartbeat.isoformat()}
            
            # Always update updated_at
            update_parts.append("updated_at = :updated")
            expression_values[":updated"] = {"S": datetime.utcnow().isoformat()}
            
            if not update_parts:
                return {
                    "success": False,
                    "message": "No updates provided"
                }
            
            update_expression = "SET " + ", ".join(update_parts)
            
            response = self.dynamodb.update_item(
                TableName=self.table_name,
                Key={"agent_id": {"S": agent_id}},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names if expression_names else None,
                ReturnValues="ALL_NEW"
            )
            
            return {
                "success": True,
                "agent_id": agent_id,
                "message": "Agent status updated successfully",
                "updated_attributes": response.get("Attributes", {})
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update agent {agent_id}"
            }
    
    def get_agent_by_capability(self, capability: str) -> List[AgentRegistryEntry]:
        """
        Find all agents with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List[AgentRegistryEntry]: List of agents with the capability
            
        Validates: Requirements 4.3
        """
        try:
            # Scan table for agents with the capability
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression="contains(capabilities, :cap)",
                ExpressionAttributeValues={
                    ":cap": {"S": capability}
                }
            )
            
            agents = []
            for item in response.get("Items", []):
                try:
                    agent = AgentRegistryEntry.from_dynamodb_format(item)
                    agents.append(agent)
                except Exception as e:
                    print(f"Error parsing agent entry: {e}")
                    continue
            
            return agents
        except Exception as e:
            print(f"Error querying agents by capability: {e}")
            return []
    
    def list_active_agents(self) -> List[AgentRegistryEntry]:
        """
        Get all active agents.
        
        Returns:
            List[AgentRegistryEntry]: List of active agents
            
        Validates: Requirements 4.3
        """
        try:
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression="deployment_status = :status",
                ExpressionAttributeValues={
                    ":status": {"S": "ACTIVE"}
                }
            )
            
            agents = []
            for item in response.get("Items", []):
                try:
                    agent = AgentRegistryEntry.from_dynamodb_format(item)
                    agents.append(agent)
                except Exception as e:
                    print(f"Error parsing agent entry: {e}")
                    continue
            
            return agents
        except Exception as e:
            print(f"Error listing active agents: {e}")
            return []
    
    def get_agent(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """
        Get a specific agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Optional[AgentRegistryEntry]: Agent entry or None if not found
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={"agent_id": {"S": agent_id}}
            )
            
            item = response.get("Item")
            if not item:
                return None
            
            return AgentRegistryEntry.from_dynamodb_format(item)
        except Exception as e:
            print(f"Error getting agent {agent_id}: {e}")
            return None
    
    def deregister_agent(self, agent_id: str) -> dict:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            dict: Response indicating success or failure
        """
        try:
            self.dynamodb.delete_item(
                TableName=self.table_name,
                Key={"agent_id": {"S": agent_id}}
            )
            
            return {
                "success": True,
                "agent_id": agent_id,
                "message": "Agent deregistered successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to deregister agent {agent_id}"
            }
