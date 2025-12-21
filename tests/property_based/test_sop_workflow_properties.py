"""
Property-based tests for SOP Workflow Engine.

These tests validate the workflow step logging and execution tracking
using Hypothesis for comprehensive property testing.
"""

import pytest
from hypothesis import given, strategies as st, assume
import os
import sys
import time
from datetime import datetime

# Add the deployment directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'deployment', 'trade_extraction'))

from sop_workflow import SOPWorkflowEngine, WorkflowStepStatus


class TestSOPWorkflowProperties:
    """Property-based tests for SOP workflow functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.engine = SOPWorkflowEngine("test_workflow")
    
    @given(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    def test_property_3_workflow_step_logging(self, correlation_id: str):
        """
        Property 3: Workflow Step Logging
        
        For any valid correlation_id, the workflow engine must:
        1. Successfully start a workflow execution
        2. Track all workflow steps with proper status transitions
        3. Log step start/completion times accurately
        4. Calculate step durations correctly
        5. Maintain execution state consistently
        """
        # Clean correlation_id for testing
        clean_correlation_id = correlation_id.strip()[:12]
        
        # Start workflow
        execution_id = self.engine.start_workflow(clean_correlation_id)
        
        # Verify workflow started
        assert execution_id is not None
        assert execution_id.endswith(clean_correlation_id)
        assert self.engine.current_execution is not None
        assert self.engine.current_execution.correlation_id == clean_correlation_id
        assert self.engine.current_execution.status == WorkflowStepStatus.IN_PROGRESS
        
        # Get workflow status
        status = self.engine.get_workflow_status()
        assert status is not None
        assert status['correlation_id'] == clean_correlation_id
        assert status['execution_id'] == execution_id
        assert len(status['steps']) == 8  # Should have 8 predefined steps
        
        # Test step execution
        step_id = "1_request_validation"
        
        # Start step
        start_success = self.engine.start_step(step_id)
        assert start_success is True
        
        # Verify step started
        status = self.engine.get_workflow_status()
        step_status = next(s for s in status['steps'] if s['step_id'] == step_id)
        assert step_status['status'] == WorkflowStepStatus.IN_PROGRESS.value
        assert step_status['start_time'] is not None
        assert step_status['end_time'] is None
        
        # Small delay to ensure measurable duration
        time.sleep(0.01)
        
        # Complete step
        complete_success = self.engine.complete_step(step_id)
        assert complete_success is True
        
        # Verify step completed
        status = self.engine.get_workflow_status()
        step_status = next(s for s in status['steps'] if s['step_id'] == step_id)
        assert step_status['status'] == WorkflowStepStatus.COMPLETED.value
        assert step_status['start_time'] is not None
        assert step_status['end_time'] is not None
        assert step_status['duration_ms'] is not None
        assert step_status['duration_ms'] >= 0
        
        # Verify time ordering
        start_time = datetime.fromisoformat(step_status['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(step_status['end_time'].replace('Z', '+00:00'))
        assert end_time >= start_time
        
        # Complete workflow
        completed_execution = self.engine.complete_workflow(success=True)
        assert completed_execution is not None
        assert completed_execution.status == WorkflowStepStatus.COMPLETED
        assert completed_execution.total_duration_ms is not None
        assert completed_execution.total_duration_ms >= 0
    
    @given(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    def test_property_3_workflow_failure_handling(self, correlation_id: str):
        """
        Property 3 Extension: Workflow failure handling must be consistent.
        """
        clean_correlation_id = correlation_id.strip()[:12]
        
        # Start workflow
        execution_id = self.engine.start_workflow(clean_correlation_id)
        step_id = "2_document_retrieval"
        
        # Start and fail a step
        self.engine.start_step(step_id)
        error_message = "Test error message"
        fail_success = self.engine.fail_step(step_id, error_message)
        
        assert fail_success is True
        
        # Verify step failed properly
        status = self.engine.get_workflow_status()
        step_status = next(s for s in status['steps'] if s['step_id'] == step_id)
        assert step_status['status'] == WorkflowStepStatus.FAILED.value
        assert step_status['error_message'] == error_message
        assert step_status['duration_ms'] is not None
        
        # Complete workflow as failed
        completed_execution = self.engine.complete_workflow(success=False)
        assert completed_execution.status == WorkflowStepStatus.FAILED
    
    def test_property_3_step_metadata_tracking(self):
        """
        Property 3 Extension: Step metadata must be tracked correctly.
        """
        correlation_id = "test_corr_123"
        execution_id = self.engine.start_workflow(correlation_id)
        step_id = "3_trade_extraction"
        
        # Start step with metadata
        start_metadata = {"input_size": 1024, "model": "nova-pro"}
        self.engine.start_step(step_id, metadata=start_metadata)
        
        # Complete step with additional metadata
        complete_metadata = {"output_size": 512, "confidence": 0.95}
        self.engine.complete_step(step_id, metadata=complete_metadata)
        
        # Verify metadata is preserved and merged
        step = self.engine._find_step(step_id)
        assert step is not None
        assert step.metadata["input_size"] == 1024
        assert step.metadata["model"] == "nova-pro"
        assert step.metadata["output_size"] == 512
        assert step.metadata["confidence"] == 0.95
    
    def test_property_3_concurrent_workflow_isolation(self):
        """
        Property 3 Extension: Multiple workflow engines should be isolated.
        """
        engine1 = SOPWorkflowEngine("workflow_1")
        engine2 = SOPWorkflowEngine("workflow_2")
        
        # Start workflows on both engines
        exec_id_1 = engine1.start_workflow("corr_1")
        exec_id_2 = engine2.start_workflow("corr_2")
        
        # Verify isolation
        assert exec_id_1 != exec_id_2
        assert engine1.current_execution.correlation_id == "corr_1"
        assert engine2.current_execution.correlation_id == "corr_2"
        
        # Operations on one engine shouldn't affect the other
        engine1.start_step("1_request_validation")
        
        status_1 = engine1.get_workflow_status()
        status_2 = engine2.get_workflow_status()
        
        step_1 = next(s for s in status_1['steps'] if s['step_id'] == "1_request_validation")
        step_2 = next(s for s in status_2['steps'] if s['step_id'] == "1_request_validation")
        
        assert step_1['status'] == WorkflowStepStatus.IN_PROGRESS.value
        assert step_2['status'] == WorkflowStepStatus.PENDING.value
    
    def test_property_3_invalid_operations_fail_gracefully(self):
        """
        Property 3 Extension: Invalid operations must fail gracefully.
        """
        # Operations without active workflow should fail
        assert self.engine.start_step("1_request_validation") is False
        assert self.engine.complete_step("1_request_validation") is False
        assert self.engine.fail_step("1_request_validation", "error") is False
        assert self.engine.get_workflow_status() is None
        assert self.engine.complete_workflow() is None
        
        # Start workflow and test invalid step IDs
        self.engine.start_workflow("test_corr")
        assert self.engine.start_step("invalid_step_id") is False
        assert self.engine.complete_step("invalid_step_id") is False
        assert self.engine.fail_step("invalid_step_id", "error") is False
    
    @given(st.lists(st.sampled_from([
        "1_request_validation", "2_document_retrieval", "3_trade_extraction",
        "4_data_validation", "5_table_routing", "6_data_storage",
        "7_audit_trail", "8_response_generation"
    ]), min_size=1, max_size=8, unique=True))
    def test_property_3_multiple_steps_execution(self, step_ids: list):
        """
        Property 3 Extension: Multiple steps can be executed in sequence.
        """
        correlation_id = "multi_step_test"
        self.engine.start_workflow(correlation_id)
        
        # Execute all provided steps
        for step_id in step_ids:
            assert self.engine.start_step(step_id) is True
            assert self.engine.complete_step(step_id) is True
        
        # Verify all steps were completed
        status = self.engine.get_workflow_status()
        for step_id in step_ids:
            step_status = next(s for s in status['steps'] if s['step_id'] == step_id)
            assert step_status['status'] == WorkflowStepStatus.COMPLETED.value
            assert step_status['duration_ms'] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])