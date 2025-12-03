"""
SLA Monitoring Tool

This module provides SLA monitoring capabilities for the Orchestrator Agent.
It tracks processing time, throughput, and error rates against SLA targets
defined in the AgentRegistry.

Requirements: 4.1, 4.2, 4.3
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from datetime import datetime, timedelta
from enum import Enum
import boto3
import logging

from ..models.registry import AgentRegistry, AgentRegistryEntry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SLAMetricType(str, Enum):
    """Types of SLA metrics to monitor."""
    PROCESSING_TIME = "processing_time_ms"
    THROUGHPUT = "throughput_per_hour"
    ERROR_RATE = "error_rate"
    LATENCY = "latency_ms"


class SLAViolation(BaseModel):
    """
    Represents an SLA violation detected by the monitor.
    
    Validates: Requirements 4.2, 4.3
    """
    agent_id: str = Field(..., description="Agent that violated SLA")
    agent_name: str = Field(..., description="Human-readable agent name")
    metric_type: SLAMetricType = Field(..., description="Type of metric that violated SLA")
    target_value: float = Field(..., description="SLA target value")
    actual_value: float = Field(..., description="Actual measured value")
    violation_percentage: float = Field(..., description="Percentage over/under target")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(..., description="Violation severity")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When violation was detected")
    description: str = Field(..., description="Human-readable description of violation")


class SLAStatus(BaseModel):
    """
    Overall SLA status for an agent or the system.
    
    Validates: Requirements 4.1, 4.3
    """
    agent_id: Optional[str] = Field(None, description="Agent ID (None for system-wide)")
    status: Literal["COMPLIANT", "WARNING", "VIOLATED"] = Field(..., description="Overall SLA status")
    violations: List[SLAViolation] = Field(default_factory=list, description="List of violations")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Current metric values")
    targets: Dict[str, float] = Field(default_factory=dict, description="SLA target values")
    compliance_percentage: float = Field(..., description="Overall compliance percentage")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last check timestamp")


class SLAMonitorTool:
    """
    Tool for monitoring SLA compliance across all agents.
    
    This tool:
    1. Retrieves SLA targets from AgentRegistry
    2. Collects current metrics from agents
    3. Compares actual vs target values
    4. Detects and reports SLA violations
    5. Calculates severity based on violation magnitude
    
    Validates: Requirements 4.1, 4.2, 4.3
    """
    
    def __init__(
        self,
        region_name: str = "us-east-1",
        cloudwatch_namespace: str = "TradeMatchingSystem/Agents"
    ):
        """
        Initialize SLA Monitor Tool.
        
        Args:
            region_name: AWS region
            cloudwatch_namespace: CloudWatch namespace for metrics
        """
        self.region_name = region_name
        self.cloudwatch_namespace = cloudwatch_namespace
        
        # Initialize AWS clients
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.sqs = boto3.client('sqs', region_name=region_name)
        
        # Initialize registry
        self.registry = AgentRegistry(region_name=region_name)
        
        logger.info("SLA Monitor Tool initialized")
    
    def check_agent_sla(self, agent_id: str, time_window_minutes: int = 60) -> SLAStatus:
        """
        Check SLA compliance for a specific agent.
        
        Args:
            agent_id: Agent identifier
            time_window_minutes: Time window for metric aggregation
            
        Returns:
            SLAStatus: SLA status with any violations
            
        Validates: Requirements 4.1, 4.2, 4.3
        """
        logger.info(f"Checking SLA for agent: {agent_id}")
        
        try:
            # Get agent from registry
            agent = self.registry.get_agent(agent_id)
            
            if not agent:
                logger.error(f"Agent not found in registry: {agent_id}")
                return SLAStatus(
                    agent_id=agent_id,
                    status="VIOLATED",
                    violations=[],
                    compliance_percentage=0.0,
                    description=f"Agent {agent_id} not found in registry"
                )
            
            # Get SLA targets
            sla_targets = agent.sla_targets
            
            if not sla_targets:
                logger.warning(f"No SLA targets defined for agent: {agent_id}")
                return SLAStatus(
                    agent_id=agent_id,
                    status="COMPLIANT",
                    violations=[],
                    compliance_percentage=100.0,
                    targets={},
                    metrics={}
                )
            
            # Collect current metrics
            current_metrics = self._collect_agent_metrics(agent, time_window_minutes)
            
            # Check each SLA target
            violations = []
            
            for metric_name, target_value in sla_targets.items():
                actual_value = current_metrics.get(metric_name, 0.0)
                
                # Check if metric violates SLA
                violation = self._check_metric_violation(
                    agent=agent,
                    metric_name=metric_name,
                    target_value=target_value,
                    actual_value=actual_value
                )
                
                if violation:
                    violations.append(violation)
                    logger.warning(
                        f"SLA violation detected for {agent_id}: "
                        f"{metric_name} = {actual_value:.2f} (target: {target_value:.2f})"
                    )
            
            # Calculate compliance percentage
            total_metrics = len(sla_targets)
            compliant_metrics = total_metrics - len(violations)
            compliance_percentage = (compliant_metrics / total_metrics * 100) if total_metrics > 0 else 100.0
            
            # Determine overall status
            if not violations:
                status = "COMPLIANT"
            elif compliance_percentage >= 80.0:
                status = "WARNING"
            else:
                status = "VIOLATED"
            
            return SLAStatus(
                agent_id=agent_id,
                status=status,
                violations=violations,
                metrics=current_metrics,
                targets=sla_targets,
                compliance_percentage=compliance_percentage
            )
            
        except Exception as e:
            logger.error(f"Error checking SLA for agent {agent_id}: {e}")
            return SLAStatus(
                agent_id=agent_id,
                status="VIOLATED",
                violations=[],
                compliance_percentage=0.0
            )
    
    def check_all_agents_sla(self, time_window_minutes: int = 60) -> List[SLAStatus]:
        """
        Check SLA compliance for all active agents.
        
        Args:
            time_window_minutes: Time window for metric aggregation
            
        Returns:
            List[SLAStatus]: SLA status for each agent
            
        Validates: Requirements 4.1, 4.3
        """
        logger.info("Checking SLA for all active agents")
        
        try:
            # Get all active agents
            active_agents = self.registry.list_active_agents()
            
            if not active_agents:
                logger.warning("No active agents found in registry")
                return []
            
            logger.info(f"Found {len(active_agents)} active agents")
            
            # Check SLA for each agent
            sla_statuses = []
            for agent in active_agents:
                sla_status = self.check_agent_sla(agent.agent_id, time_window_minutes)
                sla_statuses.append(sla_status)
            
            return sla_statuses
            
        except Exception as e:
            logger.error(f"Error checking SLA for all agents: {e}")
            return []
    
    def get_system_wide_sla_status(self, time_window_minutes: int = 60) -> SLAStatus:
        """
        Get system-wide SLA status aggregated across all agents.
        
        Args:
            time_window_minutes: Time window for metric aggregation
            
        Returns:
            SLAStatus: System-wide SLA status
            
        Validates: Requirements 4.1, 4.5
        """
        logger.info("Getting system-wide SLA status")
        
        try:
            # Check all agents
            agent_statuses = self.check_all_agents_sla(time_window_minutes)
            
            if not agent_statuses:
                return SLAStatus(
                    agent_id=None,
                    status="COMPLIANT",
                    violations=[],
                    compliance_percentage=100.0
                )
            
            # Aggregate violations
            all_violations = []
            for status in agent_statuses:
                all_violations.extend(status.violations)
            
            # Calculate system-wide compliance
            total_agents = len(agent_statuses)
            compliant_agents = sum(1 for s in agent_statuses if s.status == "COMPLIANT")
            compliance_percentage = (compliant_agents / total_agents * 100) if total_agents > 0 else 100.0
            
            # Determine overall status
            if not all_violations:
                status = "COMPLIANT"
            elif compliance_percentage >= 80.0:
                status = "WARNING"
            else:
                status = "VIOLATED"
            
            # Aggregate metrics
            aggregated_metrics = {}
            aggregated_targets = {}
            
            for agent_status in agent_statuses:
                for metric_name, value in agent_status.metrics.items():
                    if metric_name not in aggregated_metrics:
                        aggregated_metrics[metric_name] = []
                    aggregated_metrics[metric_name].append(value)
                
                for metric_name, value in agent_status.targets.items():
                    if metric_name not in aggregated_targets:
                        aggregated_targets[metric_name] = []
                    aggregated_targets[metric_name].append(value)
            
            # Calculate averages
            avg_metrics = {k: sum(v) / len(v) for k, v in aggregated_metrics.items()}
            avg_targets = {k: sum(v) / len(v) for k, v in aggregated_targets.items()}
            
            return SLAStatus(
                agent_id=None,  # System-wide
                status=status,
                violations=all_violations,
                metrics=avg_metrics,
                targets=avg_targets,
                compliance_percentage=compliance_percentage
            )
            
        except Exception as e:
            logger.error(f"Error getting system-wide SLA status: {e}")
            return SLAStatus(
                agent_id=None,
                status="VIOLATED",
                violations=[],
                compliance_percentage=0.0
            )
    
    def _collect_agent_metrics(
        self,
        agent: AgentRegistryEntry,
        time_window_minutes: int
    ) -> Dict[str, float]:
        """
        Collect current metrics for an agent.
        
        Args:
            agent: Agent registry entry
            time_window_minutes: Time window for aggregation
            
        Returns:
            Dict[str, float]: Current metric values
        """
        metrics = {}
        
        try:
            # Get metrics from agent registry (most recent values)
            if agent.metrics:
                metrics.update(agent.metrics)
            
            # Get metrics from CloudWatch for more accurate time-window aggregation
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)
            
            # Query CloudWatch for each metric type
            for metric_name in agent.sla_targets.keys():
                try:
                    response = self.cloudwatch.get_metric_statistics(
                        Namespace=self.cloudwatch_namespace,
                        MetricName=metric_name,
                        Dimensions=[
                            {'Name': 'AgentId', 'Value': agent.agent_id}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=time_window_minutes * 60,
                        Statistics=['Average']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        # Use the most recent average
                        latest = max(datapoints, key=lambda x: x['Timestamp'])
                        metrics[metric_name] = latest['Average']
                        
                except Exception as e:
                    logger.debug(f"Could not get CloudWatch metric {metric_name} for {agent.agent_id}: {e}")
                    # Fall back to registry metrics
                    pass
            
            # Calculate derived metrics
            if "total_processed" in metrics and time_window_minutes > 0:
                # Calculate throughput per hour
                throughput = (metrics["total_processed"] / time_window_minutes) * 60
                metrics["throughput_per_hour"] = throughput
            
            # Get queue depth for the agent's subscriptions
            for queue_name in agent.event_subscriptions:
                try:
                    queue_url = self.sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
                    attrs = self.sqs.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=['ApproximateNumberOfMessages']
                    )
                    queue_depth = int(attrs['Attributes']['ApproximateNumberOfMessages'])
                    metrics[f"queue_depth_{queue_name}"] = float(queue_depth)
                except Exception as e:
                    logger.debug(f"Could not get queue depth for {queue_name}: {e}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics for agent {agent.agent_id}: {e}")
            return metrics
    
    def _check_metric_violation(
        self,
        agent: AgentRegistryEntry,
        metric_name: str,
        target_value: float,
        actual_value: float
    ) -> Optional[SLAViolation]:
        """
        Check if a metric violates its SLA target.
        
        Args:
            agent: Agent registry entry
            metric_name: Name of the metric
            target_value: SLA target value
            actual_value: Actual measured value
            
        Returns:
            Optional[SLAViolation]: Violation if detected, None otherwise
        """
        # Determine if this is a "lower is better" or "higher is better" metric
        lower_is_better = metric_name in [
            "processing_time_ms",
            "latency_ms",
            "error_rate"
        ]
        
        # Check for violation
        violated = False
        violation_percentage = 0.0
        
        if lower_is_better:
            # Actual should be <= target
            if actual_value > target_value:
                violated = True
                violation_percentage = ((actual_value - target_value) / target_value) * 100
        else:
            # Actual should be >= target (e.g., throughput)
            if actual_value < target_value:
                violated = True
                violation_percentage = ((target_value - actual_value) / target_value) * 100
        
        if not violated:
            return None
        
        # Determine severity based on violation percentage
        if violation_percentage >= 50.0:
            severity = "CRITICAL"
        elif violation_percentage >= 25.0:
            severity = "HIGH"
        elif violation_percentage >= 10.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        # Create description
        if lower_is_better:
            description = (
                f"{agent.agent_name} {metric_name} is {actual_value:.2f}, "
                f"exceeding target of {target_value:.2f} by {violation_percentage:.1f}%"
            )
        else:
            description = (
                f"{agent.agent_name} {metric_name} is {actual_value:.2f}, "
                f"below target of {target_value:.2f} by {violation_percentage:.1f}%"
            )
        
        return SLAViolation(
            agent_id=agent.agent_id,
            agent_name=agent.agent_name,
            metric_type=SLAMetricType(metric_name),
            target_value=target_value,
            actual_value=actual_value,
            violation_percentage=violation_percentage,
            severity=severity,
            description=description
        )
    
    def _run(self, agent_id: Optional[str] = None, time_window_minutes: int = 60) -> str:
        """
        Tool execution method for CrewAI/Strands integration.
        
        Args:
            agent_id: Optional agent ID to check (None for all agents)
            time_window_minutes: Time window for metric aggregation
            
        Returns:
            str: JSON string with SLA status
        """
        import json
        
        try:
            if agent_id:
                sla_status = self.check_agent_sla(agent_id, time_window_minutes)
                return json.dumps(sla_status.model_dump(), indent=2, default=str)
            else:
                sla_status = self.get_system_wide_sla_status(time_window_minutes)
                return json.dumps(sla_status.model_dump(), indent=2, default=str)
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "message": "Failed to check SLA status"
            }, indent=2)


if __name__ == "__main__":
    """Test SLA Monitor Tool."""
    import json
    
    # Initialize tool
    monitor = SLAMonitorTool()
    
    # Check system-wide SLA
    status = monitor.get_system_wide_sla_status(time_window_minutes=60)
    print("System-wide SLA Status:")
    print(json.dumps(status.model_dump(), indent=2, default=str))
    
    # Check individual agent SLAs
    agent_statuses = monitor.check_all_agents_sla(time_window_minutes=60)
    print(f"\nIndividual Agent SLA Statuses ({len(agent_statuses)} agents):")
    for agent_status in agent_statuses:
        print(f"\n{agent_status.agent_id}: {agent_status.status}")
        if agent_status.violations:
            print(f"  Violations: {len(agent_status.violations)}")
            for violation in agent_status.violations:
                print(f"    - {violation.description}")
