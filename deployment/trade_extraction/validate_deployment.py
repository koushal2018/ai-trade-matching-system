#!/usr/bin/env python3
"""
Deployment Validation Script for Trade Extraction Agent.

This script validates the deployment of the Trade Extraction Agent by testing:
- Agent registration in DynamoDB
- Integration with existing HTTP orchestrator
- CloudWatch metrics and logging configuration
- AgentCore runtime status

Requirements: 7.1, 7.2, 7.3, 7.5
"""

import os
import sys
import json
import time
import boto3
import logging
import argparse
import subprocess
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_registry import AgentRegistryManager
except ImportError as e:
    print(f"❌ Error importing agent_registry module: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentValidator:
    """
    Validates Trade Extraction Agent deployment.
    
    This class performs comprehensive validation of the agent deployment
    including registry, integration, and monitoring configuration.
    """
    
    def __init__(self, agent_name: str, region: str, environment: str):
        """
        Initialize the deployment validator.
        
        Args:
            agent_name: Name of the agent to validate
            region: AWS region
            environment: Deployment environment
        """
        self.agent_name = agent_name
        self.region = region
        self.environment = environment
        
        # Initialize AWS clients
        try:
            self.dynamodb = boto3.client('dynamodb', region_name=region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
            self.logs = boto3.client('logs', region_name=region)
            self.sts = boto3.client('sts', region_name=region)
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            raise
        
        # Initialize registry manager
        self.registry = AgentRegistryManager(region_name=region)
        
        logger.info(f"DeploymentValidator initialized for {agent_name} in {region}")
    
    def validate_deployment(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Run complete deployment validation.
        
        Returns:
            Tuple of (overall_success, validation_results)
        """
        logger.info("Starting deployment validation...")
        
        validation_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'agent_name': self.agent_name,
            'region': self.region,
            'environment': self.environment,
            'tests': {}
        }
        
        # Define validation tests
        validation_tests = [
            ('aws_credentials', self._validate_aws_credentials),
            ('agent_registration', self._validate_agent_registration),
            ('agentcore_runtime', self._validate_agentcore_runtime),
            ('http_orchestrator_integration', self._validate_http_orchestrator_integration),
            ('cloudwatch_logs', self._validate_cloudwatch_logs),
            ('cloudwatch_metrics', self._validate_cloudwatch_metrics),
            ('cloudwatch_alarms', self._validate_cloudwatch_alarms)
        ]
        
        overall_success = True
        
        for test_name, test_func in validation_tests:
            logger.info(f"Running validation test: {test_name}")
            
            try:
                success, details = test_func()
                validation_results['tests'][test_name] = {
                    'success': success,
                    'details': details,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                if success:
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED - {details.get('error', 'Unknown error')}")
                    overall_success = False
                    
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {str(e)}")
                validation_results['tests'][test_name] = {
                    'success': False,
                    'details': {'error': str(e)},
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                overall_success = False
        
        validation_results['overall_success'] = overall_success
        
        logger.info(f"Deployment validation completed. Overall success: {overall_success}")
        return overall_success, validation_results
    
    def _validate_aws_credentials(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate AWS credentials and permissions."""
        try:
            identity = self.sts.get_caller_identity()
            
            return True, {
                'account_id': identity['Account'],
                'user_arn': identity['Arn'],
                'user_id': identity['UserId']
            }
            
        except Exception as e:
            return False, {'error': f"AWS credentials validation failed: {str(e)}"}
    
    def _validate_agent_registration(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate agent registration in DynamoDB.
        Requirements: 7.1
        """
        try:
            success, agent_info, error = self.registry.get_agent_info(self.agent_name)
            
            if not success:
                return False, {'error': f"Agent not found in registry: {error}"}
            
            if not agent_info:
                return False, {'error': "Agent info is None"}
            
            # Validate required fields
            required_fields = [
                'agent_id', 'agent_name', 'agent_type', 'runtime_arn',
                'status', 'version', 'capabilities', 'created_at', 'updated_at'
            ]
            
            missing_fields = []
            for field in required_fields:
                if not hasattr(agent_info, field) or getattr(agent_info, field) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return False, {
                    'error': f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Validate agent is active
            if agent_info.status != 'active':
                return False, {
                    'error': f"Agent status is '{agent_info.status}', expected 'active'"
                }
            
            # Validate capabilities
            expected_capabilities = [
                'pdf_processing', 'trade_data_extraction', 'data_validation',
                'table_routing', 'sop_workflow'
            ]
            
            missing_capabilities = []
            for capability in expected_capabilities:
                if capability not in agent_info.capabilities:
                    missing_capabilities.append(capability)
            
            if missing_capabilities:
                logger.warning(f"Missing capabilities: {', '.join(missing_capabilities)}")
            
            return True, {
                'agent_id': agent_info.agent_id,
                'agent_name': agent_info.agent_name,
                'agent_type': agent_info.agent_type,
                'status': agent_info.status,
                'version': agent_info.version,
                'runtime_arn': agent_info.runtime_arn,
                'capabilities': agent_info.capabilities,
                'sop_enabled': agent_info.sop_enabled,
                'sop_version': agent_info.sop_version,
                'created_at': agent_info.created_at,
                'updated_at': agent_info.updated_at,
                'missing_capabilities': missing_capabilities
            }
            
        except Exception as e:
            return False, {'error': f"Agent registration validation failed: {str(e)}"}
    
    def _validate_agentcore_runtime(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate AgentCore runtime status.
        Requirements: 7.5
        """
        try:
            # Try to get agent status from AgentCore CLI
            result = subprocess.run(
                ['agentcore', 'status', '--agent', self.agent_name, '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False, {
                    'error': f"AgentCore status command failed: {result.stderr}"
                }
            
            try:
                status_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                return False, {
                    'error': f"Failed to parse AgentCore status JSON: {str(e)}"
                }
            
            # Validate runtime status
            runtime_status = status_data.get('status', 'unknown')
            if runtime_status.lower() not in ['active', 'running', 'ready']:
                return False, {
                    'error': f"Runtime status is '{runtime_status}', expected active/running/ready"
                }
            
            return True, {
                'runtime_status': runtime_status,
                'runtime_arn': status_data.get('runtime_arn'),
                'agent_version': status_data.get('version'),
                'last_updated': status_data.get('last_updated'),
                'configuration': status_data.get('configuration', {})
            }
            
        except subprocess.TimeoutExpired:
            return False, {'error': "AgentCore status command timed out"}
        except FileNotFoundError:
            return False, {'error': "AgentCore CLI not found"}
        except Exception as e:
            return False, {'error': f"AgentCore runtime validation failed: {str(e)}"}
    
    def _validate_http_orchestrator_integration(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate integration with HTTP orchestrator.
        Requirements: 7.2
        """
        try:
            # Create a test payload
            test_payload = {
                "document_id": "validation_test_001",
                "canonical_output_location": f"s3://test-bucket/extracted/BANK/validation_test_001.json",
                "source_type": "BANK",
                "correlation_id": "corr_validation_001"
            }
            
            # Try to invoke the agent
            start_time = time.time()
            result = subprocess.run(
                ['agentcore', 'invoke', '--agent', self.agent_name, json.dumps(test_payload)],
                capture_output=True,
                text=True,
                timeout=60  # Allow more time for actual processing
            )
            end_time = time.time()
            
            processing_time_ms = int((end_time - start_time) * 1000)
            
            if result.returncode != 0:
                # Check if it's a timeout or other error
                if "timeout" in result.stderr.lower():
                    return False, {
                        'error': f"Agent invocation timed out: {result.stderr}",
                        'processing_time_ms': processing_time_ms
                    }
                else:
                    return False, {
                        'error': f"Agent invocation failed: {result.stderr}",
                        'processing_time_ms': processing_time_ms
                    }
            
            # Try to parse the response
            try:
                response_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                return False, {
                    'error': f"Failed to parse agent response JSON: {str(e)}",
                    'raw_response': result.stdout[:500],  # First 500 chars
                    'processing_time_ms': processing_time_ms
                }
            
            # Validate response structure
            required_fields = ['success', 'correlation_id']
            missing_fields = []
            for field in required_fields:
                if field not in response_data:
                    missing_fields.append(field)
            
            if missing_fields:
                return False, {
                    'error': f"Response missing required fields: {', '.join(missing_fields)}",
                    'response': response_data,
                    'processing_time_ms': processing_time_ms
                }
            
            # Check if correlation_id matches
            if response_data.get('correlation_id') != test_payload['correlation_id']:
                return False, {
                    'error': "Correlation ID mismatch in response",
                    'expected': test_payload['correlation_id'],
                    'actual': response_data.get('correlation_id'),
                    'processing_time_ms': processing_time_ms
                }
            
            return True, {
                'response_structure_valid': True,
                'correlation_id_match': True,
                'processing_time_ms': processing_time_ms,
                'response_success': response_data.get('success'),
                'response_size_bytes': len(result.stdout),
                'test_payload': test_payload,
                'agent_response': response_data
            }
            
        except subprocess.TimeoutExpired:
            return False, {'error': "Agent invocation timed out"}
        except Exception as e:
            return False, {'error': f"HTTP orchestrator integration validation failed: {str(e)}"}
    
    def _validate_cloudwatch_logs(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate CloudWatch logs configuration.
        Requirements: 7.3
        """
        try:
            # Check for agent log groups
            log_group_patterns = [
                f'/aws/bedrock-agentcore/{self.agent_name}',
                f'/aws/bedrock-agentcore/{self.agent_name}-{self.environment}',
                f'/aws/bedrock-agent/{self.agent_name}'
            ]
            
            found_log_groups = []
            
            for pattern in log_group_patterns:
                try:
                    response = self.logs.describe_log_groups(
                        logGroupNamePrefix=pattern,
                        limit=10
                    )
                    
                    for log_group in response.get('logGroups', []):
                        found_log_groups.append({
                            'name': log_group['logGroupName'],
                            'creation_time': log_group.get('creationTime'),
                            'retention_days': log_group.get('retentionInDays'),
                            'stored_bytes': log_group.get('storedBytes', 0)
                        })
                        
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceNotFoundException':
                        logger.warning(f"Error checking log group {pattern}: {e}")
            
            if not found_log_groups:
                return False, {
                    'error': "No log groups found for agent",
                    'searched_patterns': log_group_patterns
                }
            
            # Check for recent log entries (optional)
            recent_logs = []
            for log_group in found_log_groups[:1]:  # Check only the first log group
                try:
                    streams_response = self.logs.describe_log_streams(
                        logGroupName=log_group['name'],
                        orderBy='LastEventTime',
                        descending=True,
                        limit=5
                    )
                    
                    for stream in streams_response.get('logStreams', []):
                        if stream.get('lastEventTime'):
                            recent_logs.append({
                                'stream_name': stream['logStreamName'],
                                'last_event_time': stream['lastEventTime'],
                                'stored_bytes': stream.get('storedBytes', 0)
                            })
                            
                except ClientError as e:
                    logger.warning(f"Error checking log streams: {e}")
            
            return True, {
                'log_groups_found': len(found_log_groups),
                'log_groups': found_log_groups,
                'recent_log_streams': recent_logs
            }
            
        except Exception as e:
            return False, {'error': f"CloudWatch logs validation failed: {str(e)}"}
    
    def _validate_cloudwatch_metrics(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate CloudWatch metrics configuration.
        Requirements: 7.3
        """
        try:
            # Check for agent-specific metrics
            metrics_namespaces = [
                'TradeMatching/Agents',
                'AWS/BedrockAgentCore',
                f'Custom/{self.agent_name}'
            ]
            
            found_metrics = []
            
            for namespace in metrics_namespaces:
                try:
                    response = self.cloudwatch.list_metrics(
                        Namespace=namespace,
                        Dimensions=[
                            {
                                'Name': 'AgentName',
                                'Value': self.agent_name
                            }
                        ]
                    )
                    
                    for metric in response.get('Metrics', []):
                        found_metrics.append({
                            'namespace': metric['Namespace'],
                            'metric_name': metric['MetricName'],
                            'dimensions': metric.get('Dimensions', [])
                        })
                        
                except ClientError as e:
                    if e.response['Error']['Code'] != 'InvalidParameterValue':
                        logger.warning(f"Error checking metrics in namespace {namespace}: {e}")
            
            # Check for expected metric names
            expected_metrics = [
                'ExtractionSuccessRate',
                'ProcessingTimeMs',
                'TokenUsage',
                'ExtractionConfidence'
            ]
            
            found_metric_names = [m['metric_name'] for m in found_metrics]
            missing_metrics = [m for m in expected_metrics if m not in found_metric_names]
            
            return True, {
                'metrics_found': len(found_metrics),
                'metrics': found_metrics,
                'expected_metrics': expected_metrics,
                'missing_metrics': missing_metrics,
                'namespaces_checked': metrics_namespaces
            }
            
        except Exception as e:
            return False, {'error': f"CloudWatch metrics validation failed: {str(e)}"}
    
    def _validate_cloudwatch_alarms(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate CloudWatch alarms configuration.
        Requirements: 7.3
        """
        try:
            # Check for agent-specific alarms
            response = self.cloudwatch.describe_alarms(
                AlarmNamePrefix=f'{self.agent_name}',
                MaxRecords=50
            )
            
            found_alarms = []
            for alarm in response.get('MetricAlarms', []):
                found_alarms.append({
                    'alarm_name': alarm['AlarmName'],
                    'metric_name': alarm['MetricName'],
                    'namespace': alarm['Namespace'],
                    'statistic': alarm['Statistic'],
                    'threshold': alarm['Threshold'],
                    'comparison_operator': alarm['ComparisonOperator'],
                    'evaluation_periods': alarm['EvaluationPeriods'],
                    'state_value': alarm['StateValue'],
                    'state_reason': alarm.get('StateReason', '')
                })
            
            # Check for expected alarms
            expected_alarm_patterns = [
                'high-error-rate',
                'high-latency',
                'low-extraction-confidence'
            ]
            
            found_alarm_names = [a['alarm_name'].lower() for a in found_alarms]
            missing_alarms = []
            
            for pattern in expected_alarm_patterns:
                if not any(pattern in name for name in found_alarm_names):
                    missing_alarms.append(pattern)
            
            return True, {
                'alarms_found': len(found_alarms),
                'alarms': found_alarms,
                'expected_alarm_patterns': expected_alarm_patterns,
                'missing_alarms': missing_alarms
            }
            
        except Exception as e:
            return False, {'error': f"CloudWatch alarms validation failed: {str(e)}"}


def main():
    """Main function for deployment validation."""
    parser = argparse.ArgumentParser(
        description='Validate Trade Extraction Agent deployment'
    )
    
    parser.add_argument(
        '--agent-name',
        default='trade-extraction-agent',
        help='Name of the agent to validate (default: trade-extraction-agent)'
    )
    
    parser.add_argument(
        '--region',
        default=os.getenv('AWS_REGION', 'us-east-1'),
        help='AWS region (default: us-east-1 or AWS_REGION env var)'
    )
    
    parser.add_argument(
        '--environment',
        default='production',
        choices=['development', 'staging', 'production'],
        help='Deployment environment (default: production)'
    )
    
    parser.add_argument(
        '--output-file',
        help='Output validation results to JSON file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"🔍 Validating deployment of {args.agent_name} in {args.region} ({args.environment})")
    print("=" * 80)
    
    try:
        validator = DeploymentValidator(
            agent_name=args.agent_name,
            region=args.region,
            environment=args.environment
        )
        
        success, results = validator.validate_deployment()
        
        # Print summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        for test_name, test_result in results['tests'].items():
            status = "✅ PASSED" if test_result['success'] else "❌ FAILED"
            print(f"{test_name:30} {status}")
            
            if not test_result['success'] and 'error' in test_result['details']:
                print(f"{'':32} Error: {test_result['details']['error']}")
        
        print("=" * 80)
        overall_status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"OVERALL RESULT: {overall_status}")
        
        # Save results to file if requested
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to: {args.output_file}")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        print(f"\n❌ VALIDATION ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()