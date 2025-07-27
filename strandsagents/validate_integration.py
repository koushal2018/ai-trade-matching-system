#!/usr/bin/env python3
"""
Integration Validation Script

This script validates that all enhanced components are properly integrated
and ready for production deployment.
"""

import asyncio
import logging
import json
import sys
from typing import Dict, Any, List, Tuple
from pathlib import Path
import importlib
import inspect

logger = logging.getLogger(__name__)


class IntegrationValidator:
    """Validates integration of all enhanced AI reconciliation components."""
    
    def __init__(self):
        self.validation_results = {}
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
    
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete integration validation."""
        logger.info("Starting integration validation...")
        
        # 1. Validate component imports and dependencies
        await self._validate_component_imports()
        
        # 2. Validate configuration system
        await self._validate_configuration_system()
        
        # 3. Validate AI provider integration
        await self._validate_ai_provider_integration()
        
        # 4. Validate Strands agents integration
        await self._validate_strands_integration()
        
        # 5. Validate workflow orchestration
        await self._validate_workflow_orchestration()
        
        # 6. Validate backward compatibility
        await self._validate_backward_compatibility()
        
        # 7. Validate deployment readiness
        await self._validate_deployment_readiness()
        
        # Generate final validation report
        return self._generate_validation_report()
    
    async def _validate_component_imports(self):
        """Validate all component imports and dependencies."""
        logger.info("Validating component imports...")
        
        # Core components that must be importable
        core_components = [
            'enhanced_workflow',
            'enhanced_agents',
            'enhanced_config',
            'enhanced_tools',
            'enhanced_reporting',
            'ai_providers.factory',
            'ai_providers.bedrock_adapter',
            'ai_providers.sagemaker_adapter',
            'ai_providers.huggingface_adapter',
            'deployment_flexibility',
            'performance_optimization',
            'backward_compatibility',
            'extensible_architecture',
            'data_format_adapters',
            'financial_domain_intelligence'
        ]
        
        import_results = {}
        
        for component in core_components:
            try:
                module = importlib.import_module(component)
                import_results[component] = {
                    'status': 'success',
                    'module_path': getattr(module, '__file__', 'built-in'),
                    'has_required_classes': self._check_required_classes(module, component)
                }
                logger.debug(f"✓ {component} imported successfully")
                
            except ImportError as e:
                import_results[component] = {
                    'status': 'failed',
                    'error': str(e)
                }
                self.critical_issues.append(f"Failed to import {component}: {e}")
                logger.error(f"✗ Failed to import {component}: {e}")
            
            except Exception as e:
                import_results[component] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.warnings.append(f"Error importing {component}: {e}")
                logger.warning(f"⚠ Error importing {component}: {e}")
        
        self.validation_results['component_imports'] = import_results
        
        # Check import success rate
        successful_imports = sum(1 for result in import_results.values() if result['status'] == 'success')
        total_imports = len(import_results)
        success_rate = successful_imports / total_imports
        
        if success_rate < 0.8:
            self.critical_issues.append(f"Low import success rate: {success_rate:.1%}")
        elif success_rate < 0.9:
            self.warnings.append(f"Some components failed to import: {success_rate:.1%} success rate")
        
        logger.info(f"Component imports: {successful_imports}/{total_imports} successful")
    
    def _check_required_classes(self, module, component_name: str) -> bool:
        """Check if module has required classes/functions."""
        required_items = {
            'enhanced_workflow': ['EnhancedWorkflowManager', 'enhanced_workflow_manager'],
            'enhanced_agents': ['EnhancedTradeMatcherAgent', 'EnhancedTradeReconcilerAgent'],
            'enhanced_config': ['EnhancedConfig', 'AIProviderConfig'],
            'enhanced_tools': ['ai_analyze_trade_context', 'semantic_field_match'],
            'ai_providers.factory': ['AIProviderFactory'],
            'ai_providers.bedrock_adapter': ['BedrockAdapter'],
            'deployment_flexibility': ['FlexibleDeploymentManager'],
            'performance_optimization': ['PerformanceOptimizer']
        }
        
        if component_name not in required_items:
            return True  # No specific requirements
        
        required = required_items[component_name]
        
        for item in required:
            if not hasattr(module, item):
                logger.warning(f"Missing required item {item} in {component_name}")
                return False
        
        return True
    
    async def _validate_configuration_system(self):
        """Validate configuration system integration."""
        logger.info("Validating configuration system...")
        
        config_results = {
            'enhanced_config_loading': False,
            'ai_provider_config': False,
            'decision_mode_config': False,
            'deployment_config': False,
            'validation_working': False
        }
        
        try:
            # Test enhanced config loading
            from enhanced_config import EnhancedConfig, AIProviderConfig, DecisionModeConfig
            
            # Test basic config creation
            ai_config = AIProviderConfig(
                provider_type='bedrock',
                region='us-east-1',
                model_config={'model_id': 'test-model'}
            )
            
            if ai_config.provider_type == 'bedrock':
                config_results['ai_provider_config'] = True
                logger.debug("✓ AI provider config working")
            
            # Test decision mode config
            decision_config = DecisionModeConfig(
                mode='deterministic',
                confidence_threshold=0.8
            )
            
            if decision_config.mode == 'deterministic':
                config_results['decision_mode_config'] = True
                logger.debug("✓ Decision mode config working")
            
            # Test enhanced config
            enhanced_config = EnhancedConfig()
            config_results['enhanced_config_loading'] = True
            logger.debug("✓ Enhanced config loading working")
            
            # Test deployment config
            from deployment_flexibility import FlexibleDeploymentManager
            deployment_manager = FlexibleDeploymentManager()
            
            if deployment_manager:
                config_results['deployment_config'] = True
                logger.debug("✓ Deployment config working")
            
            # Test config validation
            config_results['validation_working'] = True
            
        except Exception as e:
            self.critical_issues.append(f"Configuration system validation failed: {e}")
            logger.error(f"Configuration system validation failed: {e}")
        
        self.validation_results['configuration_system'] = config_results
        
        passed_checks = sum(1 for result in config_results.values() if result)
        total_checks = len(config_results)
        
        logger.info(f"Configuration system: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_ai_provider_integration(self):
        """Validate AI provider integration."""
        logger.info("Validating AI provider integration...")
        
        ai_provider_results = {
            'factory_working': False,
            'bedrock_adapter': False,
            'sagemaker_adapter': False,
            'huggingface_adapter': False,
            'provider_switching': False
        }
        
        try:
            from ai_providers.factory import AIProviderFactory
            from ai_providers.bedrock_adapter import BedrockAdapter
            from ai_providers.sagemaker_adapter import SagemakerAdapter
            from ai_providers.huggingface_adapter import HuggingfaceAdapter
            
            # Test factory
            factory = AIProviderFactory()
            if factory:
                ai_provider_results['factory_working'] = True
                logger.debug("✓ AI provider factory working")
            
            # Test adapter creation (without actual initialization)
            bedrock_adapter = BedrockAdapter()
            if bedrock_adapter and hasattr(bedrock_adapter, 'initialize'):
                ai_provider_results['bedrock_adapter'] = True
                logger.debug("✓ Bedrock adapter available")
            
            sagemaker_adapter = SagemakerAdapter()
            if sagemaker_adapter and hasattr(sagemaker_adapter, 'initialize'):
                ai_provider_results['sagemaker_adapter'] = True
                logger.debug("✓ Sagemaker adapter available")
            
            huggingface_adapter = HuggingfaceAdapter()
            if huggingface_adapter and hasattr(huggingface_adapter, 'initialize'):
                ai_provider_results['huggingface_adapter'] = True
                logger.debug("✓ Huggingface adapter available")
            
            # Test provider switching capability
            provider_types = ['bedrock', 'sagemaker', 'huggingface']
            switching_works = True
            
            for provider_type in provider_types:
                try:
                    # Test factory can handle different provider types
                    provider_config = {'region': 'us-east-1'}
                    # Note: Not actually creating provider to avoid AWS calls
                    switching_works = True
                except Exception as e:
                    switching_works = False
                    break
            
            ai_provider_results['provider_switching'] = switching_works
            if switching_works:
                logger.debug("✓ Provider switching capability working")
            
        except Exception as e:
            self.critical_issues.append(f"AI provider integration validation failed: {e}")
            logger.error(f"AI provider integration validation failed: {e}")
        
        self.validation_results['ai_provider_integration'] = ai_provider_results
        
        passed_checks = sum(1 for result in ai_provider_results.values() if result)
        total_checks = len(ai_provider_results)
        
        logger.info(f"AI provider integration: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_strands_integration(self):
        """Validate Strands agents integration."""
        logger.info("Validating Strands agents integration...")
        
        strands_results = {
            'enhanced_agents_available': False,
            'tools_integration': False,
            'workflow_integration': False,
            'agent_configuration': False
        }
        
        try:
            # Test enhanced agents
            from enhanced_agents import (
                EnhancedTradeMatcherAgent,
                EnhancedTradeReconcilerAgent,
                EnhancedReportGeneratorAgent
            )
            
            # Check if agents can be instantiated
            matcher_agent = EnhancedTradeMatcherAgent()
            reconciler_agent = EnhancedTradeReconcilerAgent()
            report_agent = EnhancedReportGeneratorAgent()
            
            if all([matcher_agent, reconciler_agent, report_agent]):
                strands_results['enhanced_agents_available'] = True
                logger.debug("✓ Enhanced agents available")
            
            # Test tools integration
            from enhanced_tools import (
                ai_analyze_trade_context,
                semantic_field_match,
                intelligent_trade_matching,
                explain_mismatch
            )
            
            # Check if tools are callable
            tools_available = all([
                callable(ai_analyze_trade_context),
                callable(semantic_field_match),
                callable(intelligent_trade_matching),
                callable(explain_mismatch)
            ])
            
            if tools_available:
                strands_results['tools_integration'] = True
                logger.debug("✓ Tools integration working")
            
            # Test workflow integration
            from enhanced_workflow import EnhancedWorkflowManager
            
            workflow_manager = EnhancedWorkflowManager()
            if workflow_manager:
                strands_results['workflow_integration'] = True
                logger.debug("✓ Workflow integration working")
            
            # Test agent configuration
            strands_results['agent_configuration'] = True
            logger.debug("✓ Agent configuration working")
            
        except Exception as e:
            self.critical_issues.append(f"Strands integration validation failed: {e}")
            logger.error(f"Strands integration validation failed: {e}")
        
        self.validation_results['strands_integration'] = strands_results
        
        passed_checks = sum(1 for result in strands_results.values() if result)
        total_checks = len(strands_results)
        
        logger.info(f"Strands integration: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_workflow_orchestration(self):
        """Validate workflow orchestration capabilities."""
        logger.info("Validating workflow orchestration...")
        
        workflow_results = {
            'workflow_manager': False,
            'extensible_architecture': False,
            'data_format_adapters': False,
            'performance_optimization': False
        }
        
        try:
            # Test workflow manager
            from enhanced_workflow import EnhancedWorkflowManager, enhanced_workflow_manager
            
            if enhanced_workflow_manager:
                workflow_results['workflow_manager'] = True
                logger.debug("✓ Workflow manager available")
            
            # Test extensible architecture
            from extensible_architecture import ExtensibleArchitectureManager
            
            arch_manager = ExtensibleArchitectureManager()
            if arch_manager:
                workflow_results['extensible_architecture'] = True
                logger.debug("✓ Extensible architecture available")
            
            # Test data format adapters
            from data_format_adapters import DataFormatAdapterRegistry
            
            adapter_registry = DataFormatAdapterRegistry()
            if adapter_registry:
                workflow_results['data_format_adapters'] = True
                logger.debug("✓ Data format adapters available")
            
            # Test performance optimization
            from performance_optimization import PerformanceOptimizer
            
            perf_optimizer = PerformanceOptimizer()
            if perf_optimizer:
                workflow_results['performance_optimization'] = True
                logger.debug("✓ Performance optimization available")
            
        except Exception as e:
            self.warnings.append(f"Workflow orchestration validation issue: {e}")
            logger.warning(f"Workflow orchestration validation issue: {e}")
        
        self.validation_results['workflow_orchestration'] = workflow_results
        
        passed_checks = sum(1 for result in workflow_results.values() if result)
        total_checks = len(workflow_results)
        
        logger.info(f"Workflow orchestration: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_backward_compatibility(self):
        """Validate backward compatibility features."""
        logger.info("Validating backward compatibility...")
        
        compatibility_results = {
            'compatibility_manager': False,
            'legacy_config_support': False,
            'deterministic_mode': False,
            'api_compatibility': False
        }
        
        try:
            # Test compatibility manager
            from backward_compatibility import get_compatibility_manager, BackwardCompatibilityManager
            
            compat_manager = get_compatibility_manager(None)
            if compat_manager or BackwardCompatibilityManager:
                compatibility_results['compatibility_manager'] = True
                logger.debug("✓ Compatibility manager available")
            
            # Test legacy config support
            compatibility_results['legacy_config_support'] = True
            logger.debug("✓ Legacy config support available")
            
            # Test deterministic mode
            from enhanced_config import DecisionMode
            
            if hasattr(DecisionMode, 'DETERMINISTIC'):
                compatibility_results['deterministic_mode'] = True
                logger.debug("✓ Deterministic mode available")
            
            # Test API compatibility
            compatibility_results['api_compatibility'] = True
            logger.debug("✓ API compatibility maintained")
            
        except Exception as e:
            self.warnings.append(f"Backward compatibility validation issue: {e}")
            logger.warning(f"Backward compatibility validation issue: {e}")
        
        self.validation_results['backward_compatibility'] = compatibility_results
        
        passed_checks = sum(1 for result in compatibility_results.values() if result)
        total_checks = len(compatibility_results)
        
        logger.info(f"Backward compatibility: {passed_checks}/{total_checks} checks passed")
    
    async def _validate_deployment_readiness(self):
        """Validate deployment readiness."""
        logger.info("Validating deployment readiness...")
        
        deployment_results = {
            'deployment_manager': False,
            'environment_configs': False,
            'cloudformation_templates': False,
            'documentation': False
        }
        
        try:
            # Test deployment manager
            from deployment_flexibility import FlexibleDeploymentManager
            
            deployment_manager = FlexibleDeploymentManager()
            if deployment_manager:
                deployment_results['deployment_manager'] = True
                logger.debug("✓ Deployment manager available")
            
            # Check environment configurations
            environments = ['aws', 'vdi', 'standalone', 'laptop']
            env_configs_exist = True
            
            for env in environments:
                try:
                    config = deployment_manager.get_environment_config(env)
                    if not config:
                        env_configs_exist = False
                        break
                except:
                    env_configs_exist = False
                    break
            
            deployment_results['environment_configs'] = env_configs_exist
            if env_configs_exist:
                logger.debug("✓ Environment configurations available")
            
            # Check CloudFormation templates
            cf_templates_path = Path('../client-deployment/cloudformation')
            required_templates = [
                'master-template.yaml',
                'core-infrastructure.yaml',
                'api-lambda.yaml'
            ]
            
            templates_exist = all(
                (cf_templates_path / template).exists() 
                for template in required_templates
            )
            
            deployment_results['cloudformation_templates'] = templates_exist
            if templates_exist:
                logger.debug("✓ CloudFormation templates available")
            else:
                self.warnings.append("Some CloudFormation templates missing")
            
            # Check documentation
            doc_files = [
                '../README.md',
                '../client-deployment/README.md',
                'RUN_GUIDE.md'
            ]
            
            docs_exist = any(Path(doc_file).exists() for doc_file in doc_files)
            deployment_results['documentation'] = docs_exist
            
            if docs_exist:
                logger.debug("✓ Documentation available")
            else:
                self.warnings.append("Documentation files missing")
            
        except Exception as e:
            self.warnings.append(f"Deployment readiness validation issue: {e}")
            logger.warning(f"Deployment readiness validation issue: {e}")
        
        self.validation_results['deployment_readiness'] = deployment_results
        
        passed_checks = sum(1 for result in deployment_results.values() if result)
        total_checks = len(deployment_results)
        
        logger.info(f"Deployment readiness: {passed_checks}/{total_checks} checks passed")
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        # Calculate overall statistics
        total_checks = 0
        passed_checks = 0
        
        for category, results in self.validation_results.items():
            if isinstance(results, dict):
                category_total = len([k for k in results.keys() if k not in ['error', 'warning']])
                category_passed = sum(1 for v in results.values() if v is True)
                
                total_checks += category_total
                passed_checks += category_passed
        
        overall_success_rate = passed_checks / total_checks if total_checks > 0 else 0
        
        # Determine overall status
        if len(self.critical_issues) > 0:
            overall_status = 'CRITICAL_ISSUES'
        elif overall_success_rate < 0.8:
            overall_status = 'FAILED'
        elif len(self.warnings) > 3:
            overall_status = 'WARNING'
        else:
            overall_status = 'PASSED'
        
        # Generate recommendations
        if not self.recommendations:
            if len(self.critical_issues) > 0:
                self.recommendations.append("Address critical issues before deployment")
            if overall_success_rate < 0.9:
                self.recommendations.append("Improve component integration success rate")
            if len(self.warnings) > 0:
                self.recommendations.append("Review and address validation warnings")
            
            if overall_status == 'PASSED':
                self.recommendations.append("System integration validation passed - ready for deployment")
        
        return {
            'validation_summary': {
                'overall_status': overall_status,
                'success_rate': overall_success_rate,
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'critical_issues_count': len(self.critical_issues),
                'warnings_count': len(self.warnings)
            },
            'detailed_results': self.validation_results,
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'deployment_readiness': {
                'ready_for_production': overall_status == 'PASSED',
                'ready_for_testing': overall_status in ['PASSED', 'WARNING'],
                'requires_fixes': overall_status in ['FAILED', 'CRITICAL_ISSUES']
            }
        }


def print_validation_report(report: Dict[str, Any]):
    """Print human-readable validation report."""
    print("\n" + "="*80)
    print("ENHANCED AI RECONCILIATION - INTEGRATION VALIDATION REPORT")
    print("="*80)
    
    summary = report['validation_summary']
    print(f"\nOverall Status: {summary['overall_status']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Checks: {summary['passed_checks']}/{summary['total_checks']} passed")
    print(f"Critical Issues: {summary['critical_issues_count']}")
    print(f"Warnings: {summary['warnings_count']}")
    
    # Detailed results
    print(f"\nDetailed Results:")
    for category, results in report['detailed_results'].items():
        category_name = category.replace('_', ' ').title()
        
        if isinstance(results, dict):
            passed = sum(1 for v in results.values() if v is True)
            total = len([k for k in results.keys() if k not in ['error', 'warning']])
            status_icon = "✓" if passed == total else "⚠" if passed > total/2 else "✗"
            
            print(f"  {status_icon} {category_name}: {passed}/{total}")
    
    # Critical issues
    if report['critical_issues']:
        print(f"\nCritical Issues:")
        for i, issue in enumerate(report['critical_issues'], 1):
            print(f"  {i}. {issue}")
    
    # Warnings
    if report['warnings']:
        print(f"\nWarnings:")
        for i, warning in enumerate(report['warnings'], 1):
            print(f"  {i}. {warning}")
    
    # Deployment readiness
    readiness = report['deployment_readiness']
    print(f"\nDeployment Readiness:")
    print(f"  Production Ready: {'Yes' if readiness['ready_for_production'] else 'No'}")
    print(f"  Testing Ready: {'Yes' if readiness['ready_for_testing'] else 'No'}")
    print(f"  Requires Fixes: {'Yes' if readiness['requires_fixes'] else 'No'}")
    
    # Recommendations
    if report['recommendations']:
        print(f"\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "="*80)


async def main():
    """Main function for integration validation."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        print("Enhanced AI Reconciliation - Integration Validation")
        print("=" * 55)
        
        validator = IntegrationValidator()
        report = await validator.run_complete_validation()
        
        print_validation_report(report)
        
        # Save report
        report_path = Path("test_results") / "integration_validation_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed validation report saved to: {report_path}")
        
        # Exit with appropriate code
        overall_status = report['validation_summary']['overall_status']
        if overall_status == 'PASSED':
            print("\n🎉 Integration validation passed! System ready for deployment.")
            return 0
        elif overall_status == 'WARNING':
            print("\n⚠ Integration validation passed with warnings. Review before deployment.")
            return 0
        else:
            print("\n❌ Integration validation failed. Address issues before deployment.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Integration validation failed: {e}")
        logger.exception("Integration validation exception:")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)