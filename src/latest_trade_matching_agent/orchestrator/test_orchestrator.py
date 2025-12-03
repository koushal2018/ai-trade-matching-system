"""
Test suite for Orchestrator Agent components

This module provides basic tests for the SLA Monitor, Compliance Checker,
and Control Command tools.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from .sla_monitor import SLAMonitorTool, SLAStatus, SLAViolation, SLAMetricType
from .compliance_checker import ComplianceCheckerTool, ComplianceStatus, ComplianceViolation, ComplianceCheckType
from .control_command import ControlCommandTool, ControlCommand, CommandType, CommandResult


class TestSLAMonitor(unittest.TestCase):
    """Test SLA Monitor Tool."""
    
    @patch('boto3.client')
    def setUp(self, mock_boto_client):
        """Set up test fixtures."""
        self.mock_cloudwatch = Mock()
        self.mock_sqs = Mock()
        mock_boto_client.side_effect = lambda service, **kwargs: {
            'cloudwatch': self.mock_cloudwatch,
            'sqs': self.mock_sqs
        }.get(service)
        
        self.monitor = SLAMonitorTool()
    
    def test_check_metric_violation_lower_is_better(self):
        """Test violation detection for 'lower is better' metrics."""
        from ..models.registry import AgentRegistryEntry, ScalingConfig
        
        agent = AgentRegistryEntry(
            agent_id="test_agent",
            agent_name="Test Agent",
            agent_type="ADAPTER",
            version="1.0.0",
            sla_targets={"processing_time_ms": 1000.0},
            scaling_config=ScalingConfig()
        )
        
        # Test violation (actual > target)
        violation = self.monitor._check_metric_violation(
            agent=agent,
            metric_name="processing_time_ms",
            target_value=1000.0,
            actual_value=1500.0
        )
        
        self.assertIsNotNone(violation)
        self.assertEqual(violation.severity, "CRITICAL")  # 50% violation is CRITICAL
        self.assertAlmostEqual(violation.violation_percentage, 50.0)
        
        # Test no violation (actual <= target)
        violation = self.monitor._check_metric_violation(
            agent=agent,
            metric_name="processing_time_ms",
            target_value=1000.0,
            actual_value=800.0
        )
        
        self.assertIsNone(violation)
    
    def test_check_metric_violation_higher_is_better(self):
        """Test violation detection for 'higher is better' metrics."""
        from ..models.registry import AgentRegistryEntry, ScalingConfig
        
        agent = AgentRegistryEntry(
            agent_id="test_agent",
            agent_name="Test Agent",
            agent_type="ADAPTER",
            version="1.0.0",
            sla_targets={"throughput_per_hour": 100.0},
            scaling_config=ScalingConfig()
        )
        
        # Test violation (actual < target)
        violation = self.monitor._check_metric_violation(
            agent=agent,
            metric_name="throughput_per_hour",
            target_value=100.0,
            actual_value=50.0
        )
        
        self.assertIsNotNone(violation)
        self.assertEqual(violation.severity, "CRITICAL")
        self.assertAlmostEqual(violation.violation_percentage, 50.0)
        
        # Test no violation (actual >= target)
        violation = self.monitor._check_metric_violation(
            agent=agent,
            metric_name="throughput_per_hour",
            target_value=100.0,
            actual_value=120.0
        )
        
        self.assertIsNone(violation)


class TestComplianceChecker(unittest.TestCase):
    """Test Compliance Checker Tool."""
    
    @patch('boto3.client')
    def setUp(self, mock_boto_client):
        """Set up test fixtures."""
        self.mock_dynamodb = Mock()
        mock_boto_client.return_value = self.mock_dynamodb
        
        self.checker = ComplianceCheckerTool()
    
    def test_check_table_data_integrity_compliant(self):
        """Test data integrity check with compliant data."""
        # Mock DynamoDB response with compliant data
        self.mock_dynamodb.scan.return_value = {
            'Items': [
                {
                    'Trade_ID': {'S': 'TRADE001'},
                    'TRADE_SOURCE': {'S': 'BANK'}
                },
                {
                    'Trade_ID': {'S': 'TRADE002'},
                    'TRADE_SOURCE': {'S': 'BANK'}
                }
            ]
        }
        
        violations = self.checker._check_table_data_integrity(
            table_name="BankTradeData",
            expected_source="BANK",
            sample_size=10
        )
        
        self.assertEqual(len(violations), 0)
    
    def test_check_table_data_integrity_violations(self):
        """Test data integrity check with violations."""
        # Mock DynamoDB response with violations
        self.mock_dynamodb.scan.return_value = {
            'Items': [
                {
                    'Trade_ID': {'S': 'TRADE001'},
                    'TRADE_SOURCE': {'S': 'BANK'}
                },
                {
                    'Trade_ID': {'S': 'TRADE002'},
                    'TRADE_SOURCE': {'S': 'COUNTERPARTY'}  # Wrong source!
                }
            ]
        }
        
        violations = self.checker._check_table_data_integrity(
            table_name="BankTradeData",
            expected_source="BANK",
            sample_size=10
        )
        
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].resource_id, 'TRADE002')
        self.assertEqual(violations[0].severity, 'HIGH')
        self.assertEqual(violations[0].check_type, ComplianceCheckType.DATA_INTEGRITY)


class TestControlCommand(unittest.TestCase):
    """Test Control Command Tool."""
    
    @patch('boto3.client')
    def setUp(self, mock_boto_client):
        """Set up test fixtures."""
        self.mock_dynamodb = Mock()
        self.mock_sqs = Mock()
        self.mock_sns = Mock()
        
        mock_boto_client.side_effect = lambda service, **kwargs: {
            'dynamodb': self.mock_dynamodb,
            'sqs': self.mock_sqs,
            'sns': self.mock_sns
        }.get(service)
        
        self.control = ControlCommandTool()
    
    def test_pause_queue(self):
        """Test pausing a queue."""
        self.mock_sqs.get_queue_url.return_value = {'QueueUrl': 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue'}
        self.mock_sqs.set_queue_attributes.return_value = {}
        
        result = self.control._pause_queue("test-queue")
        
        self.assertTrue(result['success'])
        self.assertIn('paused', result['message'].lower())
        
        # Verify visibility timeout was set to 12 hours
        self.mock_sqs.set_queue_attributes.assert_called_once()
        call_args = self.mock_sqs.set_queue_attributes.call_args
        self.assertEqual(call_args[1]['Attributes']['VisibilityTimeout'], '43200')
    
    def test_resume_queue(self):
        """Test resuming a queue."""
        self.mock_sqs.get_queue_url.return_value = {'QueueUrl': 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue'}
        self.mock_sqs.set_queue_attributes.return_value = {}
        
        result = self.control._resume_queue("test-queue")
        
        self.assertTrue(result['success'])
        self.assertIn('resumed', result['message'].lower())
        
        # Verify visibility timeout was reset to 5 minutes
        self.mock_sqs.set_queue_attributes.assert_called_once()
        call_args = self.mock_sqs.set_queue_attributes.call_args
        self.assertEqual(call_args[1]['Attributes']['VisibilityTimeout'], '300')
    
    def test_adjust_priority_validation(self):
        """Test priority adjustment with validation."""
        # Test invalid priority (too low)
        result = self.control.adjust_priority(
            agent_id="test_agent",
            priority_level=0,
            reason="Test"
        )
        self.assertFalse(result.success)
        
        # Test invalid priority (too high)
        result = self.control.adjust_priority(
            agent_id="test_agent",
            priority_level=6,
            reason="Test"
        )
        self.assertFalse(result.success)


class TestControlCommandModel(unittest.TestCase):
    """Test Control Command models."""
    
    def test_control_command_creation(self):
        """Test creating a control command."""
        command = ControlCommand(
            command_id="cmd_001",
            command_type=CommandType.PAUSE_PROCESSING,
            target_agent_id="test_agent",
            reason="Testing pause"
        )
        
        self.assertEqual(command.command_id, "cmd_001")
        self.assertEqual(command.command_type, CommandType.PAUSE_PROCESSING)
        self.assertEqual(command.target_agent_id, "test_agent")
        self.assertEqual(command.reason, "Testing pause")
    
    def test_command_result_creation(self):
        """Test creating a command result."""
        result = CommandResult(
            success=True,
            command_id="cmd_001",
            message="Command executed successfully",
            details={"agent_id": "test_agent"}
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.command_id, "cmd_001")
        self.assertIn("successfully", result.message)


if __name__ == '__main__':
    unittest.main()
