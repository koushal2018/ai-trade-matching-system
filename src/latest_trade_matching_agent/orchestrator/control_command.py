"""
Control Command Tool

This module provides control command capabilities for the Orchestrator Agent.
It supports pause/resume processing, priority adjustment, and escalation triggers.

Requirements: 4.1, 4.2
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from enum import Enum
import boto3
import json
import logging

from ..models.registry import AgentRegistry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandType(str, Enum):
    """Types of control commands."""
    PAUSE_PROCESSING = "pause_processing"
    RESUME_PROCESSING = "resume_processing"
    ADJUST_PRIORITY = "adjust_priority"
    TRIGGER_ESCALATION = "trigger_escalation"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    DRAIN_QUEUE = "drain_queue"
    CLEAR_BACKLOG = "clear_backlog"


class CommandStatus(str, Enum):
    """Status of a control command."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ControlCommand(BaseModel):
    """
    Represents a control command issued by the Orchestrator.
    
    Validates: Requirements 4.1, 4.2
    """
    command_id: str = Field(..., description="Unique command identifier")
    command_type: CommandType = Field(..., description="Type of command")
    target_agent_id: Optional[str] = Field(None, description="Target agent (None for system-wide)")
    target_queue: Optional[str] = Field(None, description="Target SQS queue")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    reason: str = Field(..., description="Reason for issuing command")
    issued_by: str = Field(default="orchestrator_agent", description="Agent that issued command")
    issued_at: datetime = Field(default_factory=datetime.utcnow, description="When command was issued")
    status: CommandStatus = Field(default=CommandStatus.PENDING, description="Command status")
    result: Optional[Dict[str, Any]] = Field(None, description="Command execution result")
    completed_at: Optional[datetime] = Field(None, description="When command completed")


class CommandResult(BaseModel):
    """Result of executing a control command."""
    success: bool = Field(..., description="Whether command succeeded")
    command_id: str = Field(..., description="Command identifier")
    message: str = Field(..., description="Result message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class ControlCommandTool:
    """
    Tool for issuing control commands to agents and queues.
    
    This tool:
    1. Issues pause/resume commands to agents
    2. Adjusts processing priorities
    3. Triggers escalations
    4. Controls queue processing
    5. Manages agent scaling
    
    Validates: Requirements 4.1, 4.2
    """
    
    def __init__(
        self,
        region_name: str = "us-east-1",
        control_table_name: str = "ControlCommands"
    ):
        """
        Initialize Control Command Tool.
        
        Args:
            region_name: AWS region
            control_table_name: DynamoDB table for storing control commands
        """
        self.region_name = region_name
        self.control_table_name = control_table_name
        
        # Initialize AWS clients
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.sns = boto3.client('sns', region_name=region_name)
        
        # Initialize registry
        self.registry = AgentRegistry(region_name=region_name)
        
        logger.info("Control Command Tool initialized")
    
    def pause_processing(
        self,
        agent_id: Optional[str] = None,
        queue_name: Optional[str] = None,
        reason: str = "Manual pause requested"
    ) -> CommandResult:
        """
        Pause processing for an agent or queue.
        
        Args:
            agent_id: Agent to pause (None for all agents)
            queue_name: Queue to pause (None for agent's queues)
            reason: Reason for pausing
            
        Returns:
            CommandResult: Result of pause command
            
        Validates: Requirements 4.2
        """
        logger.info(f"Issuing PAUSE command: agent={agent_id}, queue={queue_name}")
        
        try:
            # Create command
            command = ControlCommand(
                command_id=f"cmd_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                command_type=CommandType.PAUSE_PROCESSING,
                target_agent_id=agent_id,
                target_queue=queue_name,
                reason=reason
            )
            
            # Store command
            self._store_command(command)
            
            # Execute pause
            if queue_name:
                # Pause specific queue by setting visibility timeout to max
                result = self._pause_queue(queue_name)
            elif agent_id:
                # Pause agent by updating status
                result = self._pause_agent(agent_id)
            else:
                # Pause all agents
                result = self._pause_all_agents()
            
            # Update command status
            command.status = CommandStatus.COMPLETED if result["success"] else CommandStatus.FAILED
            command.result = result
            command.completed_at = datetime.utcnow()
            self._update_command(command)
            
            return CommandResult(
                success=result["success"],
                command_id=command.command_id,
                message=result.get("message", "Pause command executed"),
                details=result
            )
            
        except Exception as e:
            logger.error(f"Error executing pause command: {e}")
            return CommandResult(
                success=False,
                command_id="",
                message=f"Failed to pause: {str(e)}",
                details={"error": str(e)}
            )
    
    def resume_processing(
        self,
        agent_id: Optional[str] = None,
        queue_name: Optional[str] = None,
        reason: str = "Manual resume requested"
    ) -> CommandResult:
        """
        Resume processing for an agent or queue.
        
        Args:
            agent_id: Agent to resume (None for all agents)
            queue_name: Queue to resume (None for agent's queues)
            reason: Reason for resuming
            
        Returns:
            CommandResult: Result of resume command
            
        Validates: Requirements 4.2
        """
        logger.info(f"Issuing RESUME command: agent={agent_id}, queue={queue_name}")
        
        try:
            # Create command
            command = ControlCommand(
                command_id=f"cmd_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                command_type=CommandType.RESUME_PROCESSING,
                target_agent_id=agent_id,
                target_queue=queue_name,
                reason=reason
            )
            
            # Store command
            self._store_command(command)
            
            # Execute resume
            if queue_name:
                # Resume specific queue by resetting visibility timeout
                result = self._resume_queue(queue_name)
            elif agent_id:
                # Resume agent by updating status
                result = self._resume_agent(agent_id)
            else:
                # Resume all agents
                result = self._resume_all_agents()
            
            # Update command status
            command.status = CommandStatus.COMPLETED if result["success"] else CommandStatus.FAILED
            command.result = result
            command.completed_at = datetime.utcnow()
            self._update_command(command)
            
            return CommandResult(
                success=result["success"],
                command_id=command.command_id,
                message=result.get("message", "Resume command executed"),
                details=result
            )
            
        except Exception as e:
            logger.error(f"Error executing resume command: {e}")
            return CommandResult(
                success=False,
                command_id="",
                message=f"Failed to resume: {str(e)}",
                details={"error": str(e)}
            )
    
    def adjust_priority(
        self,
        agent_id: str,
        priority_level: int,
        reason: str = "Priority adjustment requested"
    ) -> CommandResult:
        """
        Adjust processing priority for an agent.
        
        Args:
            agent_id: Agent to adjust
            priority_level: New priority level (1=highest, 5=lowest)
            reason: Reason for adjustment
            
        Returns:
            CommandResult: Result of priority adjustment
            
        Validates: Requirements 4.2
        """
        logger.info(f"Issuing ADJUST_PRIORITY command: agent={agent_id}, priority={priority_level}")
        
        try:
            # Validate priority level
            if not 1 <= priority_level <= 5:
                raise ValueError("Priority level must be between 1 (highest) and 5 (lowest)")
            
            # Create command
            command = ControlCommand(
                command_id=f"cmd_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                command_type=CommandType.ADJUST_PRIORITY,
                target_agent_id=agent_id,
                parameters={"priority_level": priority_level},
                reason=reason
            )
            
            # Store command
            self._store_command(command)
            
            # Update agent priority in registry
            result = self.registry.update_agent_status(
                agent_id=agent_id,
                metrics={"priority_level": float(priority_level)}
            )
            
            # Update command status
            command.status = CommandStatus.COMPLETED if result["success"] else CommandStatus.FAILED
            command.result = result
            command.completed_at = datetime.utcnow()
            self._update_command(command)
            
            return CommandResult(
                success=result["success"],
                command_id=command.command_id,
                message=f"Priority adjusted to {priority_level} for {agent_id}",
                details=result
            )
            
        except Exception as e:
            logger.error(f"Error adjusting priority: {e}")
            return CommandResult(
                success=False,
                command_id="",
                message=f"Failed to adjust priority: {str(e)}",
                details={"error": str(e)}
            )
    
    def trigger_escalation(
        self,
        resource_id: str,
        resource_type: str,
        escalation_level: Literal["OPS_DESK", "SENIOR_OPS", "COMPLIANCE", "ENGINEERING"],
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ) -> CommandResult:
        """
        Trigger an escalation for a resource.
        
        Args:
            resource_id: ID of resource to escalate (e.g., trade_id, exception_id)
            resource_type: Type of resource (e.g., trade, exception)
            escalation_level: Level to escalate to
            reason: Reason for escalation
            details: Additional escalation details
            
        Returns:
            CommandResult: Result of escalation
            
        Validates: Requirements 4.2
        """
        logger.info(f"Issuing TRIGGER_ESCALATION command: {resource_type} {resource_id} to {escalation_level}")
        
        try:
            # Create command
            command = ControlCommand(
                command_id=f"cmd_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                command_type=CommandType.TRIGGER_ESCALATION,
                parameters={
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "escalation_level": escalation_level,
                    "details": details or {}
                },
                reason=reason
            )
            
            # Store command
            self._store_command(command)
            
            # Send escalation to appropriate queue
            queue_name = f"trade-matching-system-{escalation_level.lower().replace('_', '-')}-production"
            
            try:
                queue_url = self.sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
                
                escalation_message = {
                    "escalation_id": command.command_id,
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "escalation_level": escalation_level,
                    "reason": reason,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                self.sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(escalation_message)
                )
                
                result = {
                    "success": True,
                    "message": f"Escalation sent to {escalation_level}",
                    "queue": queue_name
                }
                
            except Exception as e:
                logger.error(f"Error sending escalation to queue: {e}")
                result = {
                    "success": False,
                    "message": f"Failed to send escalation: {str(e)}"
                }
            
            # Update command status
            command.status = CommandStatus.COMPLETED if result["success"] else CommandStatus.FAILED
            command.result = result
            command.completed_at = datetime.utcnow()
            self._update_command(command)
            
            return CommandResult(
                success=result["success"],
                command_id=command.command_id,
                message=result["message"],
                details=result
            )
            
        except Exception as e:
            logger.error(f"Error triggering escalation: {e}")
            return CommandResult(
                success=False,
                command_id="",
                message=f"Failed to trigger escalation: {str(e)}",
                details={"error": str(e)}
            )
    
    def _pause_queue(self, queue_name: str) -> Dict[str, Any]:
        """Pause a queue by setting visibility timeout to maximum."""
        try:
            queue_url = self.sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
            
            # Set visibility timeout to 12 hours (maximum)
            self.sqs.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'VisibilityTimeout': '43200'  # 12 hours in seconds
                }
            )
            
            return {
                "success": True,
                "message": f"Queue {queue_name} paused",
                "queue": queue_name
            }
        except Exception as e:
            logger.error(f"Error pausing queue {queue_name}: {e}")
            return {
                "success": False,
                "message": f"Failed to pause queue: {str(e)}"
            }
    
    def _resume_queue(self, queue_name: str) -> Dict[str, Any]:
        """Resume a queue by resetting visibility timeout."""
        try:
            queue_url = self.sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
            
            # Reset visibility timeout to default (5 minutes)
            self.sqs.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'VisibilityTimeout': '300'  # 5 minutes in seconds
                }
            )
            
            return {
                "success": True,
                "message": f"Queue {queue_name} resumed",
                "queue": queue_name
            }
        except Exception as e:
            logger.error(f"Error resuming queue {queue_name}: {e}")
            return {
                "success": False,
                "message": f"Failed to resume queue: {str(e)}"
            }
    
    def _pause_agent(self, agent_id: str) -> Dict[str, Any]:
        """Pause an agent by updating its status."""
        try:
            result = self.registry.update_agent_status(
                agent_id=agent_id,
                deployment_status="INACTIVE"
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Agent {agent_id} paused",
                    "agent_id": agent_id
                }
            else:
                return result
        except Exception as e:
            logger.error(f"Error pausing agent {agent_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to pause agent: {str(e)}"
            }
    
    def _resume_agent(self, agent_id: str) -> Dict[str, Any]:
        """Resume an agent by updating its status."""
        try:
            result = self.registry.update_agent_status(
                agent_id=agent_id,
                deployment_status="ACTIVE"
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Agent {agent_id} resumed",
                    "agent_id": agent_id
                }
            else:
                return result
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to resume agent: {str(e)}"
            }
    
    def _pause_all_agents(self) -> Dict[str, Any]:
        """Pause all active agents."""
        try:
            active_agents = self.registry.list_active_agents()
            paused_count = 0
            
            for agent in active_agents:
                result = self._pause_agent(agent.agent_id)
                if result["success"]:
                    paused_count += 1
            
            return {
                "success": True,
                "message": f"Paused {paused_count} agents",
                "paused_count": paused_count,
                "total_agents": len(active_agents)
            }
        except Exception as e:
            logger.error(f"Error pausing all agents: {e}")
            return {
                "success": False,
                "message": f"Failed to pause all agents: {str(e)}"
            }
    
    def _resume_all_agents(self) -> Dict[str, Any]:
        """Resume all inactive agents."""
        try:
            # Get all agents (including inactive)
            response = self.dynamodb.scan(TableName="AgentRegistry")
            items = response.get('Items', [])
            
            resumed_count = 0
            for item in items:
                agent_id = item.get("agent_id", {}).get("S", "")
                status = item.get("deployment_status", {}).get("S", "")
                
                if status == "INACTIVE":
                    result = self._resume_agent(agent_id)
                    if result["success"]:
                        resumed_count += 1
            
            return {
                "success": True,
                "message": f"Resumed {resumed_count} agents",
                "resumed_count": resumed_count
            }
        except Exception as e:
            logger.error(f"Error resuming all agents: {e}")
            return {
                "success": False,
                "message": f"Failed to resume all agents: {str(e)}"
            }
    
    def _store_command(self, command: ControlCommand) -> None:
        """Store control command in DynamoDB."""
        try:
            item = {
                "command_id": {"S": command.command_id},
                "command_type": {"S": command.command_type.value},
                "target_agent_id": {"S": command.target_agent_id or ""},
                "target_queue": {"S": command.target_queue or ""},
                "parameters": {"S": json.dumps(command.parameters)},
                "reason": {"S": command.reason},
                "issued_by": {"S": command.issued_by},
                "issued_at": {"S": command.issued_at.isoformat()},
                "status": {"S": command.status.value}
            }
            
            self.dynamodb.put_item(
                TableName=self.control_table_name,
                Item=item
            )
        except Exception as e:
            logger.error(f"Error storing command: {e}")
    
    def _update_command(self, command: ControlCommand) -> None:
        """Update control command in DynamoDB."""
        try:
            self.dynamodb.update_item(
                TableName=self.control_table_name,
                Key={"command_id": {"S": command.command_id}},
                UpdateExpression="SET #status = :status, #result = :result, completed_at = :completed",
                ExpressionAttributeNames={
                    "#status": "status",
                    "#result": "result"
                },
                ExpressionAttributeValues={
                    ":status": {"S": command.status.value},
                    ":result": {"S": json.dumps(command.result or {})},
                    ":completed": {"S": command.completed_at.isoformat() if command.completed_at else ""}
                }
            )
        except Exception as e:
            logger.error(f"Error updating command: {e}")
    
    def _run(
        self,
        command_type: str,
        agent_id: Optional[str] = None,
        queue_name: Optional[str] = None,
        priority_level: Optional[int] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        escalation_level: Optional[str] = None,
        reason: str = "Command issued by orchestrator"
    ) -> str:
        """
        Tool execution method for CrewAI/Strands integration.
        
        Args:
            command_type: Type of command to execute
            agent_id: Target agent ID
            queue_name: Target queue name
            priority_level: Priority level for adjustment
            resource_id: Resource ID for escalation
            resource_type: Resource type for escalation
            escalation_level: Escalation level
            reason: Reason for command
            
        Returns:
            str: JSON string with command result
        """
        try:
            if command_type == "pause":
                result = self.pause_processing(agent_id, queue_name, reason)
            elif command_type == "resume":
                result = self.resume_processing(agent_id, queue_name, reason)
            elif command_type == "adjust_priority":
                if not priority_level:
                    raise ValueError("priority_level required for adjust_priority command")
                result = self.adjust_priority(agent_id, priority_level, reason)
            elif command_type == "escalate":
                if not all([resource_id, resource_type, escalation_level]):
                    raise ValueError("resource_id, resource_type, and escalation_level required for escalate command")
                result = self.trigger_escalation(resource_id, resource_type, escalation_level, reason)
            else:
                raise ValueError(f"Unknown command type: {command_type}")
            
            return json.dumps(result.model_dump(), indent=2, default=str)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": "Failed to execute control command"
            }, indent=2)


if __name__ == "__main__":
    """Test Control Command Tool."""
    
    # Initialize tool
    tool = ControlCommandTool()
    
    # Test pause command
    print("Testing PAUSE command:")
    result = tool.pause_processing(
        agent_id="pdf_adapter_agent",
        reason="Testing pause functionality"
    )
    print(json.dumps(result.model_dump(), indent=2, default=str))
    
    # Test resume command
    print("\nTesting RESUME command:")
    result = tool.resume_processing(
        agent_id="pdf_adapter_agent",
        reason="Testing resume functionality"
    )
    print(json.dumps(result.model_dump(), indent=2, default=str))
