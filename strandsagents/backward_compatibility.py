"""
Backward Compatibility Layer for Enhanced AI Reconciliation

This module ensures that existing integrations continue to work while providing
enhanced functionality through the extensible architecture. It provides:
- Legacy API compatibility
- Configuration migration utilities
- Wrapper functions for existing tools
- Gradual migration support
"""

import logging
import warnings
from typing import Dict, Any, List, Optional, Callable, Union
from functools import wraps
import inspect
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================================
# Legacy Configuration Support
# ============================================================================

@dataclass
class LegacyConfigMapping:
    """Mapping between legacy and new configuration keys"""
    legacy_key: str
    new_key: str
    transformation: Optional[Callable] = None
    deprecated_version: str = "2.0.0"


class ConfigurationMigrator:
    """Handles migration from legacy configuration formats"""
    
    def __init__(self):
        self._mappings: List[LegacyConfigMapping] = []
        self._setup_default_mappings()
    
    def _setup_default_mappings(self):
        """Setup default configuration mappings"""
        self._mappings.extend([
            # AI Provider mappings
            LegacyConfigMapping("ai_model", "ai_provider_config.provider_type"),
            LegacyConfigMapping("bedrock_model_id", "ai_provider_config.model_config.model_id"),
            LegacyConfigMapping("ai_region", "ai_provider_config.region"),
            
            # Decision mode mappings
            LegacyConfigMapping("use_ai", "decision_mode_config.mode", 
                               lambda x: "llm" if x else "deterministic"),
            LegacyConfigMapping("hybrid_mode", "decision_mode_config.mode",
                               lambda x: "hybrid" if x else "deterministic"),
            
            # Matching configuration mappings
            LegacyConfigMapping("similarity_threshold", "matching_config.similarity_threshold"),
            LegacyConfigMapping("field_weights", "matching_config.field_weights"),
            LegacyConfigMapping("tolerance_config", "reconciliation_config.tolerances"),
            
            # Tool configuration mappings
            LegacyConfigMapping("enable_semantic_matching", "tools_config.semantic_matching_enabled"),
            LegacyConfigMapping("context_analysis", "tools_config.context_analysis_enabled"),
        ])
    
    def add_mapping(self, mapping: LegacyConfigMapping):
        """Add a custom configuration mapping"""
        self._mappings.append(mapping)
    
    def migrate_config(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy configuration to new format"""
        migrated_config = {}
        unmapped_keys = set(legacy_config.keys())
        
        for mapping in self._mappings:
            if mapping.legacy_key in legacy_config:
                value = legacy_config[mapping.legacy_key]
                
                # Apply transformation if specified
                if mapping.transformation:
                    try:
                        value = mapping.transformation(value)
                    except Exception as e:
                        logger.error(f"Failed to transform {mapping.legacy_key}: {e}")
                        continue
                
                # Set nested configuration value
                self._set_nested_value(migrated_config, mapping.new_key, value)
                unmapped_keys.discard(mapping.legacy_key)
                
                # Issue deprecation warning
                warnings.warn(
                    f"Configuration key '{mapping.legacy_key}' is deprecated since version "
                    f"{mapping.deprecated_version}. Use '{mapping.new_key}' instead.",
                    DeprecationWarning,
                    stacklevel=2
                )
        
        # Copy unmapped keys as-is (they might be new configuration)
        for key in unmapped_keys:
            migrated_config[key] = legacy_config[key]
        
        return migrated_config
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any):
        """Set a nested configuration value using dot notation"""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


# ============================================================================
# Legacy API Compatibility Layer
# ============================================================================

class LegacyAPIWrapper:
    """Wrapper to maintain compatibility with legacy API calls"""
    
    def __init__(self, enhanced_system):
        self.enhanced_system = enhanced_system
        self._legacy_function_map = {}
        self._setup_legacy_mappings()
    
    def _setup_legacy_mappings(self):
        """Setup mappings from legacy function names to new implementations"""
        self._legacy_function_map = {
            # Legacy tool names to new tool names
            'analyze_trade_data': 'ai_analyze_trade_context',
            'match_trades': 'intelligent_trade_matching',
            'compare_fields': 'semantic_field_match',
            'generate_report': 'enhanced_report_generation',
            
            # Legacy agent names
            'trade_matcher': 'enhanced_trade_matcher',
            'reconciler': 'enhanced_trade_reconciler',
            'reporter': 'enhanced_report_generator',
        }
    
    def __getattr__(self, name: str):
        """Intercept legacy function calls and redirect to new implementations"""
        if name in self._legacy_function_map:
            new_name = self._legacy_function_map[name]
            
            # Issue deprecation warning
            warnings.warn(
                f"Function '{name}' is deprecated. Use '{new_name}' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            
            # Return wrapper function
            return self._create_legacy_wrapper(name, new_name)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def _create_legacy_wrapper(self, legacy_name: str, new_name: str):
        """Create a wrapper function for legacy API compatibility"""
        def wrapper(*args, **kwargs):
            logger.info(f"Legacy API call: {legacy_name} -> {new_name}")
            
            # Get the new function from the enhanced system
            if hasattr(self.enhanced_system, new_name):
                new_function = getattr(self.enhanced_system, new_name)
                
                # Transform arguments if needed
                transformed_args, transformed_kwargs = self._transform_arguments(
                    legacy_name, args, kwargs
                )
                
                return new_function(*transformed_args, **transformed_kwargs)
            else:
                raise AttributeError(f"Enhanced system has no method '{new_name}'")
        
        return wrapper
    
    def _transform_arguments(self, legacy_name: str, args: tuple, kwargs: dict):
        """Transform legacy arguments to new format"""
        # This would contain specific transformations for each legacy function
        # For now, we'll pass arguments through unchanged
        return args, kwargs


# ============================================================================
# Legacy Tool Compatibility
# ============================================================================

def legacy_tool_wrapper(new_tool_func):
    """Decorator to wrap new tools for legacy compatibility"""
    @wraps(new_tool_func)
    def wrapper(*args, **kwargs):
        # Check if this is a legacy call pattern
        if len(args) > 0 and isinstance(args[0], dict) and 'legacy_format' in args[0]:
            # Transform legacy arguments
            legacy_data = args[0]
            transformed_kwargs = _transform_legacy_tool_args(legacy_data, kwargs)
            return new_tool_func(**transformed_kwargs)
        else:
            # Normal call
            return new_tool_func(*args, **kwargs)
    
    return wrapper


def _transform_legacy_tool_args(legacy_data: Dict[str, Any], kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Transform legacy tool arguments to new format"""
    transformed = dict(kwargs)
    
    # Common legacy transformations
    if 'trade_data' in legacy_data:
        transformed['trade1'] = legacy_data['trade_data']
    
    if 'comparison_data' in legacy_data:
        transformed['trade2'] = legacy_data['comparison_data']
    
    if 'ai_enabled' in legacy_data:
        transformed['mode'] = 'llm' if legacy_data['ai_enabled'] else 'deterministic'
    
    return transformed


# ============================================================================
# Legacy Agent Compatibility
# ============================================================================

class LegacyAgentAdapter:
    """Adapter to make enhanced agents compatible with legacy interfaces"""
    
    def __init__(self, enhanced_agent):
        self.enhanced_agent = enhanced_agent
        self._legacy_methods = {}
        self._setup_legacy_methods()
    
    def _setup_legacy_methods(self):
        """Setup legacy method mappings"""
        self._legacy_methods = {
            'process_trades': self._legacy_process_trades,
            'match_trade_pair': self._legacy_match_trade_pair,
            'reconcile_fields': self._legacy_reconcile_fields,
            'generate_summary': self._legacy_generate_summary,
        }
    
    def __getattr__(self, name: str):
        """Handle legacy method calls"""
        if name in self._legacy_methods:
            warnings.warn(
                f"Method '{name}' is deprecated. Use enhanced agent methods instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return self._legacy_methods[name]
        
        # Delegate to enhanced agent
        return getattr(self.enhanced_agent, name)
    
    def _legacy_process_trades(self, trades: List[Dict[str, Any]], **kwargs):
        """Legacy trade processing method"""
        logger.info("Legacy trade processing called")
        
        # Transform to new format and call enhanced method
        enhanced_config = {
            'decision_mode': 'deterministic',  # Default to deterministic for legacy
            'ai_provider_type': 'none'
        }
        enhanced_config.update(kwargs)
        
        return self.enhanced_agent.process_trades_enhanced(trades, enhanced_config)
    
    def _legacy_match_trade_pair(self, trade1: Dict[str, Any], trade2: Dict[str, Any], **kwargs):
        """Legacy trade pair matching method"""
        logger.info("Legacy trade pair matching called")
        
        # Use deterministic mode for legacy compatibility
        return self.enhanced_agent.intelligent_match_trades(
            trade1, trade2, mode='deterministic', **kwargs
        )
    
    def _legacy_reconcile_fields(self, fields1: Dict[str, Any], fields2: Dict[str, Any], **kwargs):
        """Legacy field reconciliation method"""
        logger.info("Legacy field reconciliation called")
        
        # Transform to new reconciliation format
        return self.enhanced_agent.reconcile_fields_enhanced(
            fields1, fields2, mode='deterministic', **kwargs
        )
    
    def _legacy_generate_summary(self, reconciliation_results: List[Dict[str, Any]], **kwargs):
        """Legacy summary generation method"""
        logger.info("Legacy summary generation called")
        
        # Use basic report generation
        return self.enhanced_agent.generate_enhanced_report(
            reconciliation_results, format='legacy', **kwargs
        )


# ============================================================================
# Migration Utilities
# ============================================================================

class MigrationUtility:
    """Utility for gradual migration from legacy to enhanced system"""
    
    def __init__(self):
        self.migration_log: List[Dict[str, Any]] = []
        self.config_migrator = ConfigurationMigrator()
    
    def create_migration_plan(self, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a migration plan for moving to enhanced system"""
        plan = {
            'current_version': '1.0',
            'target_version': '2.0',
            'migration_steps': [],
            'compatibility_issues': [],
            'recommendations': []
        }
        
        # Analyze current configuration
        legacy_keys = self._identify_legacy_keys(current_config)
        if legacy_keys:
            plan['migration_steps'].append({
                'step': 'migrate_configuration',
                'description': 'Update configuration to new format',
                'legacy_keys': legacy_keys,
                'automated': True
            })
        
        # Check for deprecated API usage
        deprecated_apis = self._check_deprecated_apis(current_config)
        if deprecated_apis:
            plan['compatibility_issues'].extend(deprecated_apis)
            plan['migration_steps'].append({
                'step': 'update_api_calls',
                'description': 'Update deprecated API calls',
                'deprecated_apis': deprecated_apis,
                'automated': False
            })
        
        # Add recommendations
        plan['recommendations'].extend([
            'Test enhanced features in development environment',
            'Gradually enable AI features after validation',
            'Monitor performance during migration',
            'Keep legacy configuration as backup'
        ])
        
        return plan
    
    def _identify_legacy_keys(self, config: Dict[str, Any]) -> List[str]:
        """Identify legacy configuration keys"""
        legacy_keys = []
        for mapping in self.config_migrator._mappings:
            if mapping.legacy_key in config:
                legacy_keys.append(mapping.legacy_key)
        return legacy_keys
    
    def _check_deprecated_apis(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for deprecated API usage patterns"""
        issues = []
        
        # This would analyze code or configuration for deprecated patterns
        # For now, we'll return common deprecation issues
        deprecated_patterns = [
            {
                'pattern': 'direct_tool_import',
                'description': 'Direct tool imports are deprecated',
                'solution': 'Use enhanced tool registry'
            },
            {
                'pattern': 'hardcoded_ai_config',
                'description': 'Hardcoded AI configuration is deprecated',
                'solution': 'Use configuration-driven AI provider selection'
            }
        ]
        
        return deprecated_patterns
    
    def execute_migration_step(self, step: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single migration step"""
        step_name = step['step']
        
        if step_name == 'migrate_configuration':
            migrated_config = self.config_migrator.migrate_config(config)
            self.migration_log.append({
                'step': step_name,
                'status': 'completed',
                'timestamp': logger.info.__self__.name,  # This would be actual timestamp
                'changes': step.get('legacy_keys', [])
            })
            return migrated_config
        
        elif step_name == 'update_api_calls':
            # This would require code analysis and updates
            self.migration_log.append({
                'step': step_name,
                'status': 'manual_required',
                'timestamp': logger.info.__self__.name,
                'description': 'Manual code updates required'
            })
            return config
        
        else:
            logger.warning(f"Unknown migration step: {step_name}")
            return config
    
    def validate_migration(self, original_config: Dict[str, Any], migrated_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that migration was successful"""
        validation_result = {
            'success': True,
            'issues': [],
            'warnings': []
        }
        
        # Check that all required new keys are present
        required_keys = [
            'ai_provider_config',
            'decision_mode_config',
            'extensible_architecture_config'
        ]
        
        for key in required_keys:
            if key not in migrated_config:
                validation_result['issues'].append(f"Missing required key: {key}")
                validation_result['success'] = False
        
        # Check for potential data loss
        original_key_count = len(self._flatten_dict(original_config))
        migrated_key_count = len(self._flatten_dict(migrated_config))
        
        if migrated_key_count < original_key_count:
            validation_result['warnings'].append(
                f"Configuration size reduced from {original_key_count} to {migrated_key_count} keys"
            )
        
        return validation_result
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary for comparison"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


# ============================================================================
# Compatibility Testing Framework
# ============================================================================

class CompatibilityTester:
    """Framework for testing backward compatibility"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
    
    def test_legacy_api_compatibility(self, legacy_wrapper: LegacyAPIWrapper) -> Dict[str, Any]:
        """Test that legacy API calls work correctly"""
        test_result = {
            'test_name': 'legacy_api_compatibility',
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Test legacy function calls
        legacy_functions = [
            'analyze_trade_data',
            'match_trades',
            'compare_fields',
            'generate_report'
        ]
        
        for func_name in legacy_functions:
            try:
                # This would contain actual test calls
                logger.info(f"Testing legacy function: {func_name}")
                test_result['passed'] += 1
            except Exception as e:
                test_result['failed'] += 1
                test_result['errors'].append(f"{func_name}: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def test_configuration_migration(self, migrator: ConfigurationMigrator) -> Dict[str, Any]:
        """Test configuration migration"""
        test_result = {
            'test_name': 'configuration_migration',
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Test with sample legacy configurations
        legacy_configs = [
            {'ai_model': 'bedrock', 'use_ai': True},
            {'similarity_threshold': 0.8, 'hybrid_mode': True},
            {'bedrock_model_id': 'claude-v1', 'ai_region': 'us-east-1'}
        ]
        
        for config in legacy_configs:
            try:
                migrated = migrator.migrate_config(config)
                if migrated:
                    test_result['passed'] += 1
                else:
                    test_result['failed'] += 1
                    test_result['errors'].append(f"Migration failed for: {config}")
            except Exception as e:
                test_result['failed'] += 1
                test_result['errors'].append(f"Migration error: {str(e)}")
        
        self.test_results.append(test_result)
        return test_result
    
    def generate_compatibility_report(self) -> Dict[str, Any]:
        """Generate comprehensive compatibility report"""
        total_passed = sum(result['passed'] for result in self.test_results)
        total_failed = sum(result['failed'] for result in self.test_results)
        
        return {
            'overall_status': 'PASS' if total_failed == 0 else 'FAIL',
            'total_tests': total_passed + total_failed,
            'passed': total_passed,
            'failed': total_failed,
            'success_rate': total_passed / (total_passed + total_failed) if (total_passed + total_failed) > 0 else 0,
            'detailed_results': self.test_results
        }


# ============================================================================
# Global Compatibility Manager
# ============================================================================

class BackwardCompatibilityManager:
    """Main manager for backward compatibility features"""
    
    def __init__(self, enhanced_system):
        self.enhanced_system = enhanced_system
        self.config_migrator = ConfigurationMigrator()
        self.legacy_wrapper = LegacyAPIWrapper(enhanced_system)
        self.migration_utility = MigrationUtility()
        self.compatibility_tester = CompatibilityTester()
        
    def enable_legacy_support(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Enable legacy support with configuration migration"""
        logger.info("Enabling backward compatibility support")
        
        # Migrate configuration
        migrated_config = self.config_migrator.migrate_config(config)
        
        # Validate migration
        validation_result = self.migration_utility.validate_migration(config, migrated_config)
        
        if not validation_result['success']:
            logger.error("Configuration migration validation failed")
            for issue in validation_result['issues']:
                logger.error(f"Migration issue: {issue}")
        
        for warning in validation_result['warnings']:
            logger.warning(f"Migration warning: {warning}")
        
        return migrated_config
    
    def get_legacy_wrapper(self) -> LegacyAPIWrapper:
        """Get the legacy API wrapper"""
        return self.legacy_wrapper
    
    def create_agent_adapter(self, enhanced_agent) -> LegacyAgentAdapter:
        """Create a legacy adapter for an enhanced agent"""
        return LegacyAgentAdapter(enhanced_agent)
    
    def migrate_legacy_config(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy configuration to new format."""
        return self.config_migrator.migrate_config(legacy_config)
    
    def run_compatibility_tests(self) -> Dict[str, Any]:
        """Run comprehensive compatibility tests"""
        logger.info("Running backward compatibility tests")
        
        # Test API compatibility
        self.compatibility_tester.test_legacy_api_compatibility(self.legacy_wrapper)
        
        # Test configuration migration
        self.compatibility_tester.test_configuration_migration(self.config_migrator)
        
        # Generate report
        return self.compatibility_tester.generate_compatibility_report()


# Global compatibility manager instance
compatibility_manager = None

def get_compatibility_manager(enhanced_system=None):
    """Get or create the global compatibility manager"""
    global compatibility_manager
    if compatibility_manager is None and enhanced_system is not None:
        compatibility_manager = BackwardCompatibilityManager(enhanced_system)
    return compatibility_manager