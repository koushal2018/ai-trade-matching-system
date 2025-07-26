"""
Enhanced Workflow Integration for Extensible Architecture

This module integrates all extensible architecture components with the existing
Strands agents framework to provide a comprehensive enhanced reconciliation system.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml

from .extensible_architecture import (
    ExtensibleArchitectureManager,
    PluginRegistry,
    FieldMappingEngine,
    RuleEngine,
    WorkflowEngine,
    PluginType
)
from .data_format_adapters import (
    DataFormatAdapterRegistry,
    register_builtin_adapters,
    ProcessingResult
)
from .backward_compatibility import (
    BackwardCompatibilityManager,
    get_compatibility_manager
)
from .ai_providers.factory import AIProviderFactory
from .enhanced_config import EnhancedConfig
from .models import (
    EnhancedMatcherConfig,
    EnhancedReconcilerConfig,
    AIProviderConfig,
    DecisionModeConfig
)

logger = logging.getLogger(__name__)


# ============================================================================
# Enhanced Workflow Manager
# ============================================================================

@dataclass
class WorkflowExecutionContext:
    """Context for workflow execution"""
    workflow_id: str
    input_data: Dict[str, Any]
    configuration: Dict[str, Any]
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class EnhancedWorkflowManager:
    """
    Main manager for enhanced reconciliation workflows integrating all
    extensible architecture components
    """
    
    def __init__(self):
        self.architecture_manager = ExtensibleArchitectureManager()
        self.data_format_registry = DataFormatAdapterRegistry()
        self.compatibility_manager = None
        self.ai_provider_factory = AIProviderFactory()
        self.config = None
        self._initialized = False
        
        # Register built-in adapters
        register_builtin_adapters(self.data_format_registry)
        
    async def initialize(self, config_path: str):
        """Initialize the enhanced workflow manager"""
        try:
            # Load configuration
            self.config = await self._load_configuration(config_path)
            
            # Initialize architecture manager
            await self.architecture_manager.initialize(self.config.get('extensible_architecture', {}))
            
            # Initialize data format adapters
            await self.data_format_registry.initialize_adapters(
                self.config.get('data_format_adapters', {})
            )
            
            # Initialize compatibility manager
            self.compatibility_manager = get_compatibility_manager(self)
            
            # Setup AI providers
            await self._setup_ai_providers()
            
            # Register custom step processors
            await self._register_custom_step_processors()
            
            self._initialized = True
            logger.info("Enhanced workflow manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced workflow manager: {e}")
            raise
    
    async def _load_configuration(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        # Migrate legacy configuration if needed
        if self.compatibility_manager:
            config = self.compatibility_manager.enable_legacy_support(config)
        
        return config
    
    async def _setup_ai_providers(self):
        """Setup AI providers based on configuration"""
        ai_config = self.config.get('ai_providers', {})
        
        for provider_name, provider_config in ai_config.items():
            try:
                provider = await self.ai_provider_factory.create_provider(
                    provider_config['type'],
                    provider_config.get('config', {})
                )
                
                if provider:
                    # Register as plugin
                    self.architecture_manager.plugin_registry.register_plugin(provider.__class__)
                    logger.info(f"Registered AI provider: {provider_name}")
                    
            except Exception as e:
                logger.error(f"Failed to setup AI provider {provider_name}: {e}")
    
    async def _register_custom_step_processors(self):
        """Register custom step processors for workflow execution"""
        
        async def data_format_processor(step, context):
            """Process data format adaptation step"""
            step_config = step.configuration
            input_data = context.get('input_data', {})
            
            # Get data to process
            data_key = step_config.get('data_key', 'raw_data')
            data = input_data.get(data_key)
            
            if not data:
                return {'status': 'failed', 'error': f'No data found for key: {data_key}'}
            
            # Process with appropriate adapter
            result = await self.data_format_registry.process_data(data)
            
            if result and result.success:
                return {
                    'status': 'completed',
                    'extracted_data': result.extracted_data,
                    'metadata': result.metadata
                }
            else:
                return {
                    'status': 'failed',
                    'errors': result.errors if result else ['No suitable adapter found']
                }
        
        async def ai_analysis_processor(step, context):
            """Process AI analysis step"""
            step_config = step.configuration
            ai_provider_name = step_config.get('ai_provider', 'default')
            
            # Get AI provider instance
            ai_provider = await self._get_ai_provider_instance(ai_provider_name)
            
            if not ai_provider:
                return {'status': 'failed', 'error': f'AI provider not available: {ai_provider_name}'}
            
            # Get input data
            input_data = context.get('step_results', {}).get(
                step_config.get('input_step', 'data_ingestion'), {}
            )
            
            try:
                # Perform AI analysis
                analysis_result = await ai_provider.analyze_document_context(input_data)
                
                return {
                    'status': 'completed',
                    'analysis_result': analysis_result,
                    'ai_provider': ai_provider_name
                }
                
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                return {'status': 'failed', 'error': str(e)}
        
        async def field_mapping_processor(step, context):
            """Process field mapping step"""
            step_config = step.configuration
            format_name = step_config.get('format_name')
            
            # Get input data
            input_step = step_config.get('input_step', 'data_ingestion')
            input_data = context.get('step_results', {}).get(input_step, {})
            
            if not format_name:
                return {'status': 'failed', 'error': 'Format name not specified'}
            
            try:
                # Apply field mapping
                mapped_data = self.architecture_manager.field_mapping_engine.map_fields(
                    input_data, format_name
                )
                
                return {
                    'status': 'completed',
                    'mapped_data': mapped_data,
                    'format_name': format_name
                }
                
            except Exception as e:
                logger.error(f"Field mapping failed: {e}")
                return {'status': 'failed', 'error': str(e)}
        
        # Register processors
        workflow_engine = self.architecture_manager.workflow_engine
        workflow_engine.register_step_processor("data_format", data_format_processor)
        workflow_engine.register_step_processor("ai_analysis", ai_analysis_processor)
        workflow_engine.register_step_processor("field_mapping", field_mapping_processor)
    
    async def _get_ai_provider_instance(self, provider_name: str):
        """Get AI provider instance"""
        # This would retrieve the configured AI provider instance
        # For now, return None as placeholder
        return None
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        input_data: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a complete reconciliation workflow"""
        
        if not self._initialized:
            raise RuntimeError("Workflow manager not initialized")
        
        # Create execution context
        context = WorkflowExecutionContext(
            workflow_id=f"{workflow_name}_{asyncio.get_event_loop().time()}",
            input_data=input_data,
            configuration=configuration or {},
            execution_metadata={
                'workflow_name': workflow_name,
                'start_time': asyncio.get_event_loop().time(),
                'version': '2.0'
            }
        )
        
        try:
            logger.info(f"Starting workflow execution: {workflow_name}")
            
            # Execute workflow using workflow engine
            result = await self.architecture_manager.workflow_engine.execute_workflow(
                workflow_name, input_data
            )
            
            # Update context with results
            context.step_results = result.get('results', {})
            context.execution_metadata['end_time'] = asyncio.get_event_loop().time()
            context.execution_metadata['duration'] = (
                context.execution_metadata['end_time'] - 
                context.execution_metadata['start_time']
            )
            
            # Generate final result
            final_result = {
                'workflow_id': context.workflow_id,
                'status': result.get('status', 'unknown'),
                'results': context.step_results,
                'metadata': context.execution_metadata,
                'errors': context.errors,
                'warnings': context.warnings
            }
            
            logger.info(f"Workflow execution completed: {workflow_name}")
            return final_result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            context.errors.append(str(e))
            
            return {
                'workflow_id': context.workflow_id,
                'status': 'failed',
                'error': str(e),
                'partial_results': context.step_results,
                'metadata': context.execution_metadata
            }
    
    async def process_document(
        self, 
        document_data: Union[str, bytes, Dict[str, Any]],
        format_hint: Optional[str] = None
    ) -> ProcessingResult:
        """Process a document using appropriate data format adapter"""
        
        if not self._initialized:
            raise RuntimeError("Workflow manager not initialized")
        
        try:
            # If format hint provided, try specific adapter first
            if format_hint:
                # This would use a specific adapter based on format hint
                pass
            
            # Use registry to find appropriate adapter
            result = await self.data_format_registry.process_data(document_data)
            
            if result:
                logger.info(f"Document processed successfully with format: {result.metadata.get('format_type')}")
                return result
            else:
                logger.warning("No suitable adapter found for document")
                return ProcessingResult(
                    success=False,
                    extracted_data={},
                    errors=["No suitable adapter found for document format"]
                )
                
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return ProcessingResult(
                success=False,
                extracted_data={},
                errors=[str(e)]
            )
    
    async def run_compatibility_tests(self) -> Dict[str, Any]:
        """Run backward compatibility tests"""
        if not self.compatibility_manager:
            return {'status': 'skipped', 'reason': 'Compatibility manager not available'}
        
        return self.compatibility_manager.run_compatibility_tests()
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflows"""
        return list(self.architecture_manager.workflow_engine._workflows.keys())
    
    def get_available_data_formats(self) -> List[str]:
        """Get list of supported data formats"""
        formats = []
        for adapter in self.data_format_registry._initialized_adapters.values():
            formats.extend(adapter.supported_formats)
        return list(set(formats))
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'initialized': self._initialized,
            'architecture_manager': self.architecture_manager.is_initialized(),
            'available_workflows': len(self.get_available_workflows()),
            'available_data_formats': len(self.get_available_data_formats()),
            'ai_providers': len(self.config.get('ai_providers', {})) if self.config else 0,
            'compatibility_enabled': self.compatibility_manager is not None
        }
    
    async def cleanup(self):
        """Cleanup all components"""
        try:
            await self.architecture_manager.cleanup()
            await self.data_format_registry.cleanup_all()
            
            if self.compatibility_manager:
                # Compatibility manager cleanup if needed
                pass
            
            self._initialized = False
            logger.info("Enhanced workflow manager cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# ============================================================================
# Enhanced Workflow Factory
# ============================================================================

class EnhancedWorkflowFactory:
    """Factory for creating enhanced workflow configurations"""
    
    @staticmethod
    def create_standard_config() -> Dict[str, Any]:
        """Create standard enhanced workflow configuration"""
        return {
            'extensible_architecture': {
                'plugin_paths': ['./plugins', './custom_plugins'],
                'field_mapping_configs': ['./config/field_mappings.yaml'],
                'workflow_configs': ['./config/workflows.yaml']
            },
            'data_format_adapters': {
                'EmailAdapter': {
                    'extraction_patterns': {
                        'custom_field': r'Custom:\s*([^\n\r]+)'
                    }
                },
                'SwiftMessageAdapter': {
                    'field_mappings': {
                        '25': 'account_identification'
                    }
                }
            },
            'ai_providers': {
                'bedrock': {
                    'type': 'bedrock',
                    'config': {
                        'region': 'us-east-1',
                        'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0'
                    }
                },
                'sagemaker': {
                    'type': 'sagemaker',
                    'config': {
                        'region': 'me-central-1',
                        'endpoint_name': 'trade-reconciliation-endpoint'
                    }
                }
            },
            'workflow_execution': {
                'default_timeout': 3600,
                'max_concurrent_workflows': 5,
                'error_handling': 'continue_on_error',
                'logging_level': 'INFO'
            }
        }
    
    @staticmethod
    def create_high_performance_config() -> Dict[str, Any]:
        """Create configuration optimized for high performance"""
        config = EnhancedWorkflowFactory.create_standard_config()
        
        config.update({
            'performance_optimization': {
                'parallel_processing': True,
                'batch_size': 1000,
                'memory_optimization': True,
                'caching_enabled': True
            },
            'workflow_execution': {
                'default_timeout': 7200,
                'max_concurrent_workflows': 10,
                'error_handling': 'fail_fast',
                'logging_level': 'WARNING'
            }
        })
        
        return config
    
    @staticmethod
    def create_ai_focused_config() -> Dict[str, Any]:
        """Create configuration focused on AI capabilities"""
        config = EnhancedWorkflowFactory.create_standard_config()
        
        config.update({
            'ai_enhancement': {
                'default_mode': 'llm',
                'confidence_threshold': 0.8,
                'explanation_required': True,
                'learning_enabled': True
            },
            'ai_providers': {
                'bedrock': {
                    'type': 'bedrock',
                    'config': {
                        'region': 'us-east-1',
                        'model_id': 'anthropic.claude-3-opus-20240229-v1:0'  # More powerful model
                    }
                }
            }
        })
        
        return config


# ============================================================================
# Global Enhanced Workflow Manager Instance
# ============================================================================

# Global instance for easy access
enhanced_workflow_manager = EnhancedWorkflowManager()


async def initialize_enhanced_system(config_path: str = "./config/enhanced_config.yaml"):
    """Initialize the global enhanced workflow system"""
    await enhanced_workflow_manager.initialize(config_path)
    return enhanced_workflow_manager


def get_enhanced_workflow_manager() -> EnhancedWorkflowManager:
    """Get the global enhanced workflow manager instance"""
    return enhanced_workflow_manager


# ============================================================================
# Convenience Functions
# ============================================================================

async def execute_enhanced_reconciliation(
    input_data: Dict[str, Any],
    workflow_type: str = "standard_trade_reconciliation",
    configuration: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to execute enhanced reconciliation workflow
    """
    manager = get_enhanced_workflow_manager()
    
    if not manager._initialized:
        await initialize_enhanced_system()
    
    return await manager.execute_workflow(workflow_type, input_data, configuration)


async def process_trade_document(
    document_data: Union[str, bytes, Dict[str, Any]],
    format_hint: Optional[str] = None
) -> ProcessingResult:
    """
    Convenience function to process trade document
    """
    manager = get_enhanced_workflow_manager()
    
    if not manager._initialized:
        await initialize_enhanced_system()
    
    return await manager.process_document(document_data, format_hint)


def create_enhanced_config(config_type: str = "standard") -> Dict[str, Any]:
    """
    Convenience function to create enhanced configuration
    """
    factory = EnhancedWorkflowFactory()
    
    if config_type == "standard":
        return factory.create_standard_config()
    elif config_type == "high_performance":
        return factory.create_high_performance_config()
    elif config_type == "ai_focused":
        return factory.create_ai_focused_config()
    else:
        raise ValueError(f"Unknown configuration type: {config_type}")