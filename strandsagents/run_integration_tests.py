#!/usr/bin/env python3
"""
Integration Test Execution Script

This script executes the comprehensive integration and final testing suite
for the enhanced AI reconciliation system.
"""

import asyncio
import sys
import logging
import argparse
from pathlib import Path
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the integration testing suite
from integration_final_testing import (
    run_integration_final_testing,
    print_integration_test_report,
    IntegrationTestSuite
)


async def run_specific_test_category(category: str) -> Dict[str, Any]:
    """Run a specific test category."""
    test_suite = IntegrationTestSuite()
    
    category_methods = {
        'strands': test_suite._test_strands_integration,
        'ai_providers': test_suite._test_end_to_end_with_ai_providers,
        'performance': test_suite._test_performance_and_scalability,
        'deployment': test_suite._test_deployment_environments,
        'compatibility': test_suite._test_backward_compatibility,
        'uat': test_suite._simulate_user_acceptance_testing
    }
    
    if category not in category_methods:
        raise ValueError(f"Unknown test category: {category}")
    
    logger.info(f"Running specific test category: {category}")
    
    test_suite.start_time = time.time()
    
    try:
        await category_methods[category]()
        test_suite.end_time = time.time()
        
        return {
            'category': category,
            'status': 'completed',
            'results': test_suite.test_results,
            'execution_time': test_suite.end_time - test_suite.start_time
        }
        
    except Exception as e:
        test_suite.end_time = time.time()
        logger.error(f"Test category {category} failed: {e}")
        
        return {
            'category': category,
            'status': 'failed',
            'error': str(e),
            'execution_time': test_suite.end_time - test_suite.start_time
        }


async def validate_system_prerequisites() -> bool:
    """Validate system prerequisites before running tests."""
    logger.info("Validating system prerequisites...")
    
    prerequisites = {
        'python_version': sys.version_info >= (3, 8),
        'required_modules': [],
        'configuration_files': [],
        'test_data': True
    }
    
    # Check required modules
    required_modules = [
        'asyncio', 'json', 'logging', 'pathlib', 'time',
        'unittest.mock', 'pytest'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    prerequisites['required_modules'] = len(missing_modules) == 0
    
    if missing_modules:
        logger.error(f"Missing required modules: {missing_modules}")
    
    # Check configuration files
    config_files = [
        'config/enhanced_config.yaml',
        'config/field_mappings.yaml',
        'config/workflows.yaml'
    ]
    
    missing_configs = []
    for config_file in config_files:
        if not Path(config_file).exists():
            missing_configs.append(config_file)
    
    prerequisites['configuration_files'] = len(missing_configs) == 0
    
    if missing_configs:
        logger.warning(f"Missing configuration files (will use defaults): {missing_configs}")
    
    # Overall validation
    all_valid = all(prerequisites.values())
    
    if all_valid:
        logger.info("✓ All system prerequisites validated")
    else:
        logger.error("✗ System prerequisites validation failed")
        for check, status in prerequisites.items():
            status_icon = "✓" if status else "✗"
            logger.info(f"  {status_icon} {check}")
    
    return all_valid


def create_test_environment():
    """Create necessary test environment setup."""
    logger.info("Setting up test environment...")
    
    # Create test directories
    test_dirs = [
        'test_results',
        'test_data',
        'config',
        'plugins'
    ]
    
    for test_dir in test_dirs:
        Path(test_dir).mkdir(exist_ok=True)
    
    # Create minimal configuration files if they don't exist
    config_dir = Path('config')
    
    # Enhanced config
    enhanced_config_path = config_dir / 'enhanced_config.yaml'
    if not enhanced_config_path.exists():
        enhanced_config = {
            'extensible_architecture': {
                'plugin_paths': ['./plugins'],
                'field_mapping_configs': ['./config/field_mappings.yaml'],
                'workflow_configs': ['./config/workflows.yaml']
            },
            'ai_providers': {
                'bedrock': {
                    'type': 'bedrock',
                    'config': {
                        'region': 'us-east-1',
                        'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0'
                    }
                }
            }
        }
        
        import yaml
        with open(enhanced_config_path, 'w') as f:
            yaml.dump(enhanced_config, f, default_flow_style=False)
    
    # Field mappings config
    field_mappings_path = config_dir / 'field_mappings.yaml'
    if not field_mappings_path.exists():
        field_mappings = {
            'email_format': {
                'trade_id': ['Trade ID', 'TradeId', 'trade_id'],
                'currency': ['Currency', 'Ccy', 'currency'],
                'notional': ['Notional', 'Amount', 'notional']
            }
        }
        
        with open(field_mappings_path, 'w') as f:
            yaml.dump(field_mappings, f, default_flow_style=False)
    
    # Workflows config
    workflows_path = config_dir / 'workflows.yaml'
    if not workflows_path.exists():
        workflows = {
            'standard_trade_reconciliation': {
                'steps': [
                    {'name': 'data_ingestion', 'type': 'data_format'},
                    {'name': 'trade_matching', 'type': 'ai_analysis'},
                    {'name': 'reconciliation', 'type': 'field_mapping'},
                    {'name': 'report_generation', 'type': 'reporting'}
                ]
            }
        }
        
        with open(workflows_path, 'w') as f:
            yaml.dump(workflows, f, default_flow_style=False)
    
    logger.info("✓ Test environment setup completed")


async def run_health_check() -> Dict[str, Any]:
    """Run system health check before integration tests."""
    logger.info("Running system health check...")
    
    health_results = {
        'system_status': 'unknown',
        'components': {},
        'recommendations': []
    }
    
    try:
        # Check core components
        components_to_check = [
            'enhanced_workflow',
            'enhanced_agents', 
            'enhanced_config',
            'ai_providers',
            'deployment_flexibility'
        ]
        
        for component in components_to_check:
            try:
                # Try to import component
                __import__(component)
                health_results['components'][component] = 'available'
                logger.info(f"✓ {component} available")
            except ImportError as e:
                health_results['components'][component] = f'unavailable: {e}'
                logger.warning(f"✗ {component} unavailable: {e}")
                health_results['recommendations'].append(f"Fix import issue for {component}")
        
        # Check if majority of components are available
        available_count = sum(1 for status in health_results['components'].values() if status == 'available')
        total_count = len(health_results['components'])
        
        if available_count >= total_count * 0.8:
            health_results['system_status'] = 'healthy'
            logger.info(f"✓ System health check passed ({available_count}/{total_count} components available)")
        else:
            health_results['system_status'] = 'degraded'
            logger.warning(f"⚠ System health check shows degraded state ({available_count}/{total_count} components available)")
            health_results['recommendations'].append("Address component availability issues before running full integration tests")
        
    except Exception as e:
        health_results['system_status'] = 'failed'
        health_results['error'] = str(e)
        logger.error(f"Health check failed: {e}")
    
    return health_results


def save_test_results(results: Dict[str, Any], filename: str = None):
    """Save test results to file."""
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"integration_test_results_{timestamp}.json"
    
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)
    
    results_path = results_dir / filename
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test results saved to: {results_path}")
    return results_path


async def main():
    """Main function for integration test execution."""
    parser = argparse.ArgumentParser(description="Run Enhanced AI Reconciliation Integration Tests")
    parser.add_argument("--category", choices=['strands', 'ai_providers', 'performance', 'deployment', 'compatibility', 'uat'], 
                       help="Run specific test category only")
    parser.add_argument("--skip-prerequisites", action="store_true", help="Skip prerequisite validation")
    parser.add_argument("--skip-health-check", action="store_true", help="Skip system health check")
    parser.add_argument("--output-file", help="Custom output file for results")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (skip performance tests)")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        print("Enhanced AI Reconciliation - Integration & Final Testing")
        print("=" * 60)
        
        # Setup test environment
        create_test_environment()
        
        # Validate prerequisites
        if not args.skip_prerequisites:
            prerequisites_valid = await validate_system_prerequisites()
            if not prerequisites_valid:
                print("⚠ Prerequisites validation failed. Use --skip-prerequisites to continue anyway.")
                return 1
        
        # Run health check
        if not args.skip_health_check:
            health_results = await run_health_check()
            if health_results['system_status'] == 'failed':
                print("⚠ System health check failed. Use --skip-health-check to continue anyway.")
                return 1
            elif health_results['system_status'] == 'degraded':
                print("⚠ System health check shows degraded state. Some tests may fail.")
        
        # Run tests
        if args.category:
            # Run specific category
            print(f"\nRunning specific test category: {args.category}")
            results = await run_specific_test_category(args.category)
            
            print(f"\nTest Category Results:")
            print(f"Category: {results['category']}")
            print(f"Status: {results['status']}")
            print(f"Execution Time: {results['execution_time']:.2f}s")
            
            if results['status'] == 'failed':
                print(f"Error: {results.get('error', 'Unknown error')}")
                return 1
            
        else:
            # Run complete integration test suite
            print("\nRunning complete integration test suite...")
            
            if args.quick:
                logger.info("Quick mode enabled - skipping performance tests")
            
            results = await run_integration_final_testing()
            
            # Print comprehensive report
            print_integration_test_report(results)
            
            # Save results
            results_path = save_test_results(results, args.output_file)
            print(f"\nDetailed results saved to: {results_path}")
            
            # Determine exit code
            overall_success = results['integration_test_summary']['overall_status'] == 'PASSED'
            
            if overall_success:
                print("\n🎉 All integration tests passed! System ready for deployment.")
                return 0
            else:
                print("\n⚠ Some integration tests failed. Please review and address issues.")
                return 1
        
    except KeyboardInterrupt:
        print("\n⚠ Integration testing interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Integration testing failed: {e}")
        logger.exception("Integration testing exception:")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)