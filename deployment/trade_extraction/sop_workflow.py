"""
SOP Workflow Engine for Trade Extraction Agent.

This module implements the Strands Agent SOP execution engine integration
with progress tracking and logging for each workflow step.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class WorkflowStepStatus(Enum):
    """Status enumeration for workflow steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Represents a single step in the SOP workflow."""
    step_id: str
    step_name: str
    description: str
    required: bool = True
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Represents a complete workflow execution."""
    execution_id: str
    correlation_id: str
    workflow_name: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_duration_ms: Optional[int] = None
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SOPWorkflowEngine:
    """
    SOP Workflow Engine for executing standardized workflows.
    
    This class manages the execution of SOP-defined workflows with
    comprehensive progress tracking and logging.
    """
    
    def __init__(self, workflow_name: str = "trade_extraction_sop"):
        """
        Initialize the SOP Workflow Engine.
        
        Args:
            workflow_name: Name of the workflow being executed
        """
        self.workflow_name = workflow_name
        self.current_execution: Optional[WorkflowExecution] = None
        
        # Define the standard trade extraction workflow steps
        self.workflow_steps = [
            WorkflowStep(
                step_id="1_request_validation",
                step_name="Request Validation",
                description="Validate incoming request parameters",
                required=True
            ),
            WorkflowStep(
                step_id="2_document_retrieval",
                step_name="Document Retrieval",
                description="Retrieve PDF document from S3",
                required=True
            ),
            WorkflowStep(
                step_id="3_trade_extraction",
                step_name="Trade Data Extraction",
                description="Extract structured trade data using LLM",
                required=True
            ),
            WorkflowStep(
                step_id="4_data_validation",
                step_name="Data Validation and Normalization",
                description="Validate and normalize extracted data",
                required=True
            ),
            WorkflowStep(
                step_id="5_table_routing",
                step_name="Table Routing",
                description="Route data to correct DynamoDB table",
                required=True
            ),
            WorkflowStep(
                step_id="6_data_storage",
                step_name="Data Storage",
                description="Store validated trade data in DynamoDB",
                required=True
            ),
            WorkflowStep(
                step_id="7_audit_trail",
                step_name="Audit Trail Creation",
                description="Create comprehensive audit trails",
                required=True
            ),
            WorkflowStep(
                step_id="8_response_generation",
                step_name="Response Generation",
                description="Generate standardized response",
                required=True
            )
        ]
    
    def start_workflow(self, correlation_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new workflow execution.
        
        Args:
            correlation_id: Correlation ID for tracing
            metadata: Optional metadata for the workflow execution
            
        Returns:
            Execution ID for the started workflow
        """
        execution_id = f"exec_{int(time.time() * 1000)}_{correlation_id}"
        
        self.current_execution = WorkflowExecution(
            execution_id=execution_id,
            correlation_id=correlation_id,
            workflow_name=self.workflow_name,
            status=WorkflowStepStatus.IN_PROGRESS,
            start_time=datetime.now(timezone.utc).isoformat(),
            steps=[WorkflowStep(**step.__dict__) for step in self.workflow_steps],
            metadata=metadata or {}
        )
        
        logger.info(f"Started SOP workflow execution {execution_id} for correlation_id {correlation_id}")
        return execution_id
    
    def start_step(self, step_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Start execution of a workflow step.
        
        Args:
            step_id: ID of the step to start
            metadata: Optional metadata for the step
            
        Returns:
            True if step started successfully, False otherwise
        """
        if not self.current_execution:
            logger.error(f"Cannot start step {step_id}: No active workflow execution")
            return False
        
        step = self._find_step(step_id)
        if not step:
            logger.error(f"Step {step_id} not found in workflow")
            return False
        
        step.status = WorkflowStepStatus.IN_PROGRESS
        step.start_time = datetime.now(timezone.utc).isoformat()
        if metadata:
            step.metadata.update(metadata)
        
        logger.info(f"Started workflow step {step_id} ({step.step_name}) "
                   f"for execution {self.current_execution.execution_id}")
        return True
    
    def complete_step(self, step_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a workflow step as completed.
        
        Args:
            step_id: ID of the step to complete
            metadata: Optional metadata for the step completion
            
        Returns:
            True if step completed successfully, False otherwise
        """
        if not self.current_execution:
            logger.error(f"Cannot complete step {step_id}: No active workflow execution")
            return False
        
        step = self._find_step(step_id)
        if not step:
            logger.error(f"Step {step_id} not found in workflow")
            return False
        
        if step.status != WorkflowStepStatus.IN_PROGRESS:
            logger.warning(f"Step {step_id} is not in progress (status: {step.status})")
        
        step.status = WorkflowStepStatus.COMPLETED
        step.end_time = datetime.now(timezone.utc).isoformat()
        
        # Calculate duration if start time is available
        if step.start_time:
            start_dt = datetime.fromisoformat(step.start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(step.end_time.replace('Z', '+00:00'))
            step.duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
        
        if metadata:
            step.metadata.update(metadata)
        
        logger.info(f"Completed workflow step {step_id} ({step.step_name}) "
                   f"in {step.duration_ms}ms for execution {self.current_execution.execution_id}")
        return True
    
    def fail_step(self, step_id: str, error_message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a workflow step as failed.
        
        Args:
            step_id: ID of the step that failed
            error_message: Description of the failure
            metadata: Optional metadata for the step failure
            
        Returns:
            True if step marked as failed successfully, False otherwise
        """
        if not self.current_execution:
            logger.error(f"Cannot fail step {step_id}: No active workflow execution")
            return False
        
        step = self._find_step(step_id)
        if not step:
            logger.error(f"Step {step_id} not found in workflow")
            return False
        
        step.status = WorkflowStepStatus.FAILED
        step.end_time = datetime.now(timezone.utc).isoformat()
        step.error_message = error_message
        
        # Calculate duration if start time is available
        if step.start_time:
            start_dt = datetime.fromisoformat(step.start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(step.end_time.replace('Z', '+00:00'))
            step.duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
        
        if metadata:
            step.metadata.update(metadata)
        
        logger.error(f"Failed workflow step {step_id} ({step.step_name}): {error_message} "
                    f"for execution {self.current_execution.execution_id}")
        return True
    
    def complete_workflow(self, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> Optional[WorkflowExecution]:
        """
        Complete the current workflow execution.
        
        Args:
            success: Whether the workflow completed successfully
            metadata: Optional metadata for the workflow completion
            
        Returns:
            The completed WorkflowExecution or None if no active execution
        """
        if not self.current_execution:
            logger.error("Cannot complete workflow: No active workflow execution")
            return None
        
        self.current_execution.status = WorkflowStepStatus.COMPLETED if success else WorkflowStepStatus.FAILED
        self.current_execution.end_time = datetime.now(timezone.utc).isoformat()
        
        # Calculate total duration
        if self.current_execution.start_time:
            start_dt = datetime.fromisoformat(self.current_execution.start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(self.current_execution.end_time.replace('Z', '+00:00'))
            self.current_execution.total_duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
        
        if metadata:
            self.current_execution.metadata.update(metadata)
        
        completed_execution = self.current_execution
        self.current_execution = None
        
        logger.info(f"Completed SOP workflow execution {completed_execution.execution_id} "
                   f"with status {completed_execution.status} "
                   f"in {completed_execution.total_duration_ms}ms")
        
        return completed_execution
    
    def get_workflow_status(self) -> Optional[Dict[str, Any]]:
        """
        Get the current workflow execution status.
        
        Returns:
            Dictionary containing workflow status or None if no active execution
        """
        if not self.current_execution:
            return None
        
        return {
            'execution_id': self.current_execution.execution_id,
            'correlation_id': self.current_execution.correlation_id,
            'workflow_name': self.current_execution.workflow_name,
            'status': self.current_execution.status.value,
            'start_time': self.current_execution.start_time,
            'steps': [
                {
                    'step_id': step.step_id,
                    'step_name': step.step_name,
                    'status': step.status.value,
                    'start_time': step.start_time,
                    'end_time': step.end_time,
                    'duration_ms': step.duration_ms,
                    'error_message': step.error_message
                }
                for step in self.current_execution.steps
            ]
        }
    
    def _find_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Find a workflow step by ID."""
        if not self.current_execution:
            return None
        
        for step in self.current_execution.steps:
            if step.step_id == step_id:
                return step
        return None