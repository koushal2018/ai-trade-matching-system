"""
Extensible Architecture Components for Enhanced AI Reconciliation

This module provides the core extensible architecture components including:
- Plugin architecture for AI providers
- Configuration-driven field mapping system
- Extensible rule engine
- Custom workflow support
- Data format adapters
- Backward compatibility layer
"""

import logging
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Plugin Architecture for AI Providers
# ============================================================================

class PluginType(Enum):
    """Types of plugins supported by the system"""
    AI_PROVIDER = "ai_provider"
    DATA_FORMAT_ADAPTER = "data_format_adapter"
    RULE_ENGINE = "rule_engine"
    WORKFLOW_PROCESSOR = "workflow_processor"


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""
    name: str
    version: str
    plugin_type: PluginType
    description: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    supported_regions: List[str] = field(default_factory=list)
    priority: int = 100  # Lower numbers = higher priority


class PluginInterface(ABC):
    """Base interface that all plugins must implement"""
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup plugin resources"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        pass


class PluginRegistry:
    """Registry for managing plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, Dict[str, Type[PluginInterface]]] = {}
        self._instances: Dict[str, PluginInterface] = {}
        self._plugin_paths: List[str] = []
        
    def add_plugin_path(self, path: str):
        """Add a path to search for plugins"""
        self._plugin_paths.append(path)
        
    def register_plugin(self, plugin_class: Type[PluginInterface]):
        """Register a plugin class"""
        # Create temporary instance to get metadata
        temp_instance = plugin_class()
        metadata = temp_instance.get_metadata()
        
        plugin_type = metadata.plugin_type.value
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}
            
        self._plugins[plugin_type][metadata.name] = plugin_class
        logger.info(f"Registered plugin: {metadata.name} (type: {plugin_type})")
        
    def discover_plugins(self):
        """Discover plugins from configured paths"""
        for path in self._plugin_paths:
            self._discover_plugins_in_path(path)
            
    def _discover_plugins_in_path(self, path: str):
        """Discover plugins in a specific path"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"Plugin path does not exist: {path}")
                return
                
            for py_file in path_obj.glob("*_plugin.py"):
                try:
                    module_name = py_file.stem
                    spec = importlib.util.spec_from_file_location(module_name, py_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for plugin classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, PluginInterface) and 
                            obj != PluginInterface):
                            self.register_plugin(obj)
                            
                except Exception as e:
                    logger.error(f"Failed to load plugin from {py_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to discover plugins in {path}: {e}")
    
    def get_plugins(self, plugin_type: PluginType) -> Dict[str, Type[PluginInterface]]:
        """Get all plugins of a specific type"""
        return self._plugins.get(plugin_type.value, {})
    
    def get_plugin(self, plugin_type: PluginType, name: str) -> Optional[Type[PluginInterface]]:
        """Get a specific plugin by type and name"""
        return self._plugins.get(plugin_type.value, {}).get(name)
    
    async def create_plugin_instance(
        self, 
        plugin_type: PluginType, 
        name: str, 
        config: Dict[str, Any]
    ) -> Optional[PluginInterface]:
        """Create and initialize a plugin instance"""
        plugin_class = self.get_plugin(plugin_type, name)
        if not plugin_class:
            logger.error(f"Plugin not found: {name} (type: {plugin_type.value})")
            return None
            
        try:
            instance = plugin_class()
            if not instance.validate_config(config):
                logger.error(f"Invalid configuration for plugin: {name}")
                return None
                
            if await instance.initialize(config):
                instance_key = f"{plugin_type.value}:{name}"
                self._instances[instance_key] = instance
                return instance
            else:
                logger.error(f"Failed to initialize plugin: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create plugin instance {name}: {e}")
            return None
    
    async def cleanup_all(self):
        """Cleanup all plugin instances"""
        for instance in self._instances.values():
            try:
                await instance.cleanup()
            except Exception as e:
                logger.error(f"Failed to cleanup plugin: {e}")
        self._instances.clear()


# Global plugin registry instance
plugin_registry = PluginRegistry()


# ============================================================================
# Configuration-Driven Field Mapping System
# ============================================================================

@dataclass
class FieldMapping:
    """Configuration for field mapping between different document formats"""
    source_field: str
    target_field: str
    transformation: Optional[str] = None  # Python expression for transformation
    validation: Optional[str] = None  # Validation rule
    required: bool = True
    default_value: Any = None


@dataclass
class DocumentFormatConfig:
    """Configuration for a specific document format"""
    format_name: str
    format_type: str  # pdf, csv, json, xml, email, swift, etc.
    field_mappings: List[FieldMapping]
    extraction_rules: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    preprocessing_steps: List[str] = field(default_factory=list)


class FieldMappingEngine:
    """Engine for handling configuration-driven field mapping"""
    
    def __init__(self):
        self._format_configs: Dict[str, DocumentFormatConfig] = {}
        self._transformation_functions: Dict[str, Callable] = {}
        
    def register_format_config(self, config: DocumentFormatConfig):
        """Register a document format configuration"""
        self._format_configs[config.format_name] = config
        logger.info(f"Registered format config: {config.format_name}")
        
    def load_format_configs_from_file(self, config_file: str):
        """Load format configurations from a YAML or JSON file"""
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                    
            for format_data in data.get('formats', []):
                mappings = [
                    FieldMapping(**mapping) for mapping in format_data.get('field_mappings', [])
                ]
                
                config = DocumentFormatConfig(
                    format_name=format_data['format_name'],
                    format_type=format_data['format_type'],
                    field_mappings=mappings,
                    extraction_rules=format_data.get('extraction_rules', {}),
                    validation_rules=format_data.get('validation_rules', {}),
                    preprocessing_steps=format_data.get('preprocessing_steps', [])
                )
                
                self.register_format_config(config)
                
        except Exception as e:
            logger.error(f"Failed to load format configs from {config_file}: {e}")
            
    def register_transformation_function(self, name: str, func: Callable):
        """Register a custom transformation function"""
        self._transformation_functions[name] = func
        
    def map_fields(self, source_data: Dict[str, Any], format_name: str) -> Dict[str, Any]:
        """Map fields from source format to target format"""
        if format_name not in self._format_configs:
            logger.error(f"Unknown format: {format_name}")
            return source_data
            
        config = self._format_configs[format_name]
        mapped_data = {}
        
        for mapping in config.field_mappings:
            try:
                # Get source value
                source_value = source_data.get(mapping.source_field)
                
                if source_value is None:
                    if mapping.required and mapping.default_value is None:
                        logger.warning(f"Required field missing: {mapping.source_field}")
                        continue
                    source_value = mapping.default_value
                    
                # Apply transformation if specified
                if mapping.transformation:
                    source_value = self._apply_transformation(
                        source_value, mapping.transformation
                    )
                    
                # Apply validation if specified
                if mapping.validation:
                    if not self._validate_value(source_value, mapping.validation):
                        logger.warning(f"Validation failed for {mapping.source_field}")
                        continue
                        
                mapped_data[mapping.target_field] = source_value
                
            except Exception as e:
                logger.error(f"Failed to map field {mapping.source_field}: {e}")
                
        return mapped_data
    
    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply transformation to a value"""
        try:
            # Check if it's a registered function
            if transformation in self._transformation_functions:
                return self._transformation_functions[transformation](value)
                
            # Otherwise, evaluate as Python expression
            # Note: In production, this should be more restricted for security
            local_vars = {'value': value, 'str': str, 'int': int, 'float': float}
            return eval(transformation, {"__builtins__": {}}, local_vars)
            
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            return value
    
    def _validate_value(self, value: Any, validation: str) -> bool:
        """Validate a value against a validation rule"""
        try:
            local_vars = {'value': value}
            return bool(eval(validation, {"__builtins__": {}}, local_vars))
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False


# ============================================================================
# Extensible Rule Engine
# ============================================================================

class RuleType(Enum):
    """Types of rules supported by the rule engine"""
    DETERMINISTIC = "deterministic"
    AI_POWERED = "ai_powered"
    HYBRID = "hybrid"


@dataclass
class Rule:
    """Definition of a rule"""
    name: str
    rule_type: RuleType
    condition: str  # Python expression or AI prompt
    action: str  # Action to take when rule matches
    priority: int = 100
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuleEngine:
    """Extensible rule engine supporting deterministic and AI-powered rules"""
    
    def __init__(self, ai_provider=None):
        self._rules: List[Rule] = []
        self._ai_provider = ai_provider
        self._rule_functions: Dict[str, Callable] = {}
        
    def add_rule(self, rule: Rule):
        """Add a rule to the engine"""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)
        logger.info(f"Added rule: {rule.name} (type: {rule.rule_type.value})")
        
    def register_rule_function(self, name: str, func: Callable):
        """Register a custom rule function"""
        self._rule_functions[name] = func
        
    async def evaluate_rules(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all enabled rules against the given context"""
        results = []
        
        for rule in self._rules:
            if not rule.enabled:
                continue
                
            try:
                result = await self._evaluate_rule(rule, context)
                if result:
                    results.append({
                        'rule_name': rule.name,
                        'rule_type': rule.rule_type.value,
                        'result': result,
                        'metadata': rule.metadata
                    })
            except Exception as e:
                logger.error(f"Failed to evaluate rule {rule.name}: {e}")
                
        return results
    
    async def _evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> Optional[Any]:
        """Evaluate a single rule"""
        if rule.rule_type == RuleType.DETERMINISTIC:
            return self._evaluate_deterministic_rule(rule, context)
        elif rule.rule_type == RuleType.AI_POWERED:
            return await self._evaluate_ai_rule(rule, context)
        elif rule.rule_type == RuleType.HYBRID:
            return await self._evaluate_hybrid_rule(rule, context)
        else:
            logger.error(f"Unknown rule type: {rule.rule_type}")
            return None
    
    def _evaluate_deterministic_rule(self, rule: Rule, context: Dict[str, Any]) -> Optional[Any]:
        """Evaluate a deterministic rule"""
        try:
            # Check if condition is a registered function
            if rule.condition in self._rule_functions:
                condition_result = self._rule_functions[rule.condition](context)
            else:
                # Evaluate as Python expression
                local_vars = dict(context)
                local_vars.update(self._rule_functions)
                condition_result = eval(rule.condition, {"__builtins__": {}}, local_vars)
                
            if condition_result:
                # Execute action
                if rule.action in self._rule_functions:
                    return self._rule_functions[rule.action](context)
                else:
                    local_vars = dict(context)
                    local_vars.update(self._rule_functions)
                    return eval(rule.action, {"__builtins__": {}}, local_vars)
                    
        except Exception as e:
            logger.error(f"Deterministic rule evaluation failed: {e}")
            
        return None
    
    async def _evaluate_ai_rule(self, rule: Rule, context: Dict[str, Any]) -> Optional[Any]:
        """Evaluate an AI-powered rule"""
        if not self._ai_provider:
            logger.error("AI provider not available for AI-powered rule")
            return None
            
        try:
            # Use AI provider to evaluate the rule condition
            prompt = f"""
            Rule: {rule.name}
            Condition: {rule.condition}
            Context: {json.dumps(context, indent=2)}
            
            Evaluate whether this rule condition is met and return the appropriate action result.
            """
            
            # This would use the AI provider's analyze_document_context method
            # or a specialized rule evaluation method
            result = await self._ai_provider.analyze_document_context({
                'rule_prompt': prompt,
                'context': context,
                'rule_metadata': rule.metadata
            })
            
            return result
            
        except Exception as e:
            logger.error(f"AI rule evaluation failed: {e}")
            return None
    
    async def _evaluate_hybrid_rule(self, rule: Rule, context: Dict[str, Any]) -> Optional[Any]:
        """Evaluate a hybrid rule (deterministic + AI)"""
        # First try deterministic evaluation
        deterministic_result = self._evaluate_deterministic_rule(rule, context)
        
        # If deterministic evaluation is uncertain, use AI
        if deterministic_result is None or deterministic_result == "UNCERTAIN":
            return await self._evaluate_ai_rule(rule, context)
            
        return deterministic_result


# ============================================================================
# Custom Reconciliation Workflows
# ============================================================================

@dataclass
class WorkflowStep:
    """Definition of a workflow step"""
    name: str
    step_type: str  # agent, tool, rule_engine, custom
    configuration: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    retry_count: int = 3


@dataclass
class WorkflowDefinition:
    """Definition of a custom reconciliation workflow"""
    name: str
    description: str
    steps: List[WorkflowStep]
    global_config: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"


class WorkflowEngine:
    """Engine for executing custom reconciliation workflows"""
    
    def __init__(self, plugin_registry: PluginRegistry):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._plugin_registry = plugin_registry
        self._step_processors: Dict[str, Callable] = {}
        
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a workflow definition"""
        self._workflows[workflow.name] = workflow
        logger.info(f"Registered workflow: {workflow.name}")
        
    def load_workflows_from_file(self, config_file: str):
        """Load workflow definitions from a file"""
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                    
            for workflow_data in data.get('workflows', []):
                steps = [
                    WorkflowStep(**step) for step in workflow_data.get('steps', [])
                ]
                
                workflow = WorkflowDefinition(
                    name=workflow_data['name'],
                    description=workflow_data.get('description', ''),
                    steps=steps,
                    global_config=workflow_data.get('global_config', {}),
                    version=workflow_data.get('version', '1.0')
                )
                
                self.register_workflow(workflow)
                
        except Exception as e:
            logger.error(f"Failed to load workflows from {config_file}: {e}")
            
    def register_step_processor(self, step_type: str, processor: Callable):
        """Register a processor for a specific step type"""
        self._step_processors[step_type] = processor
        
    async def execute_workflow(
        self, 
        workflow_name: str, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow"""
        if workflow_name not in self._workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
            
        workflow = self._workflows[workflow_name]
        context = {
            'input_data': input_data,
            'global_config': workflow.global_config,
            'step_results': {}
        }
        
        logger.info(f"Starting workflow execution: {workflow_name}")
        
        try:
            for step in workflow.steps:
                # Check dependencies
                if not self._check_dependencies(step, context):
                    raise RuntimeError(f"Dependencies not met for step: {step.name}")
                    
                # Execute step
                step_result = await self._execute_step(step, context)
                context['step_results'][step.name] = step_result
                
                logger.info(f"Completed step: {step.name}")
                
            return {
                'status': 'success',
                'workflow_name': workflow_name,
                'results': context['step_results']
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                'status': 'failed',
                'workflow_name': workflow_name,
                'error': str(e),
                'partial_results': context.get('step_results', {})
            }
    
    def _check_dependencies(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        for dep in step.dependencies:
            if dep not in context['step_results']:
                return False
        return True
    
    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute a single workflow step"""
        if step.step_type in self._step_processors:
            processor = self._step_processors[step.step_type]
            return await processor(step, context)
        else:
            raise ValueError(f"Unknown step type: {step.step_type}")


# ============================================================================
# Global Architecture Manager
# ============================================================================

class ExtensibleArchitectureManager:
    """Main manager for all extensible architecture components"""
    
    def __init__(self):
        self.plugin_registry = plugin_registry
        self.field_mapping_engine = FieldMappingEngine()
        self.rule_engine = RuleEngine()
        self.workflow_engine = WorkflowEngine(self.plugin_registry)
        self._initialized = False
        
    async def initialize(self, config: Dict[str, Any]):
        """Initialize the extensible architecture"""
        try:
            # Add plugin paths
            for path in config.get('plugin_paths', []):
                self.plugin_registry.add_plugin_path(path)
                
            # Discover plugins
            self.plugin_registry.discover_plugins()
            
            # Load field mapping configurations
            for config_file in config.get('field_mapping_configs', []):
                self.field_mapping_engine.load_format_configs_from_file(config_file)
                
            # Load workflow definitions
            for workflow_file in config.get('workflow_configs', []):
                self.workflow_engine.load_workflows_from_file(workflow_file)
                
            # Register built-in step processors
            self._register_builtin_step_processors()
            
            self._initialized = True
            logger.info("Extensible architecture initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize extensible architecture: {e}")
            raise
    
    def _register_builtin_step_processors(self):
        """Register built-in step processors"""
        async def agent_processor(step: WorkflowStep, context: Dict[str, Any]):
            # This would integrate with the Strands agent system
            logger.info(f"Executing agent step: {step.name}")
            return {"status": "completed", "step_type": "agent"}
            
        async def tool_processor(step: WorkflowStep, context: Dict[str, Any]):
            # This would execute Strands tools
            logger.info(f"Executing tool step: {step.name}")
            return {"status": "completed", "step_type": "tool"}
            
        async def rule_engine_processor(step: WorkflowStep, context: Dict[str, Any]):
            # Execute rule engine
            results = await self.rule_engine.evaluate_rules(context)
            return {"status": "completed", "step_type": "rule_engine", "results": results}
            
        self.workflow_engine.register_step_processor("agent", agent_processor)
        self.workflow_engine.register_step_processor("tool", tool_processor)
        self.workflow_engine.register_step_processor("rule_engine", rule_engine_processor)
    
    async def cleanup(self):
        """Cleanup all components"""
        await self.plugin_registry.cleanup_all()
        self._initialized = False
        logger.info("Extensible architecture cleaned up")
    
    def is_initialized(self) -> bool:
        """Check if the architecture is initialized"""
        return self._initialized


# Global architecture manager instance
architecture_manager = ExtensibleArchitectureManager()