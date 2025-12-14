"""
Enhanced Configuration Management for AI-Powered Trade Reconciliation

This module provides configuration classes for managing AI provider settings,
decision-making modes, and enhanced reconciliation configurations with
deployment flexibility support.
"""

import os
import json
import yaml
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import logging
from pathlib import Path

try:
    from .models import MatcherConfig, ReconcilerConfig, ReportConfig
    from .deployment_flexibility import (
        DeploymentConfigManager, 
        get_deployment_config,
        adapt_config_for_environment
    )
except ImportError:
    from models import MatcherConfig, ReconcilerConfig, ReportConfig
    from deployment_flexibility import (
        DeploymentConfigManager, 
        get_deployment_config,
        adapt_config_for_environment
    )

logger = logging.getLogger(__name__)


class AIProviderType(Enum):
    """Supported AI provider types."""
    BEDROCK = "bedrock"
    SAGEMAKER = "sagemaker"
    HUGGINGFACE = "huggingface"


class DecisionMode(Enum):
    """Decision-making approaches for reconciliation."""
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    HYBRID = "hybrid"


@dataclass
class AIProviderConfig:
    """Configuration for AI provider selection and settings."""
    provider_type: str
    region: str
    model_config: Dict[str, Any] = field(default_factory=dict)
    fallback_provider: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider_type not in [e.value for e in AIProviderType]:
            raise ValueError(f"Invalid provider_type: {self.provider_type}")
        
        if self.fallback_provider and self.fallback_provider not in [e.value for e in AIProviderType]:
            raise ValueError(f"Invalid fallback_provider: {self.fallback_provider}")
    
    @classmethod
    def from_environment(cls) -> 'AIProviderConfig':
        """Load configuration from environment variables with sensible defaults."""
        provider_type = os.getenv('AI_PROVIDER_TYPE', AIProviderType.BEDROCK.value)
        region = os.getenv('AI_PROVIDER_REGION', 'us-east-1')
        
        # Load model-specific configuration
        model_config = {}
        if provider_type == AIProviderType.BEDROCK.value:
            model_config = {
                'model_id': os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                'max_tokens': int(os.getenv('BEDROCK_MAX_TOKENS', '4096')),
                'temperature': float(os.getenv('BEDROCK_TEMPERATURE', '0.1')),
                'top_p': float(os.getenv('BEDROCK_TOP_P', '0.9'))
            }
        elif provider_type == AIProviderType.SAGEMAKER.value:
            model_config = {
                'endpoint_name': os.getenv('SAGEMAKER_ENDPOINT_NAME', ''),
                'instance_type': os.getenv('SAGEMAKER_INSTANCE_TYPE', 'ml.m5.large'),
                'initial_instance_count': int(os.getenv('SAGEMAKER_INITIAL_INSTANCE_COUNT', '1')),
                'content_type': os.getenv('SAGEMAKER_CONTENT_TYPE', 'application/json')
            }
        elif provider_type == AIProviderType.HUGGINGFACE.value:
            model_config = {
                'model_name': os.getenv('HUGGINGFACE_MODEL_NAME', 'microsoft/DialoGPT-medium'),
                'api_token': os.getenv('HUGGINGFACE_API_TOKEN', ''),
                'use_auth_token': bool(os.getenv('HUGGINGFACE_USE_AUTH_TOKEN', 'True')),
                'max_length': int(os.getenv('HUGGINGFACE_MAX_LENGTH', '512'))
            }
        
        return cls(
            provider_type=provider_type,
            region=region,
            model_config=model_config,
            fallback_provider=os.getenv('AI_FALLBACK_PROVIDER'),
            timeout_seconds=int(os.getenv('AI_TIMEOUT_SECONDS', '30')),
            max_retries=int(os.getenv('AI_MAX_RETRIES', '3'))
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of validation errors."""
        errors = []
        
        # Provider-specific validation
        if self.provider_type == AIProviderType.BEDROCK.value:
            if not self.model_config.get('model_id'):
                errors.append("Bedrock model_id is required")
        
        elif self.provider_type == AIProviderType.SAGEMAKER.value:
            if not self.model_config.get('endpoint_name'):
                errors.append("Sagemaker endpoint_name is required")
        
        elif self.provider_type == AIProviderType.HUGGINGFACE.value:
            if not self.model_config.get('model_name'):
                errors.append("Huggingface model_name is required")
        
        # General validation
        if self.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")
        
        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIProviderConfig':
        """Create configuration from dictionary."""
        return cls(**data)


@dataclass
class DecisionModeConfig:
    """Configuration for decision-making approach."""
    mode: str
    confidence_threshold: float = 0.8
    hybrid_fallback_threshold: float = 0.6
    semantic_similarity_threshold: float = 0.85
    context_analysis_enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.mode not in [e.value for e in DecisionMode]:
            raise ValueError(f"Invalid mode: {self.mode}")
        
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        
        if not 0.0 <= self.hybrid_fallback_threshold <= 1.0:
            raise ValueError("hybrid_fallback_threshold must be between 0.0 and 1.0")
        
        if not 0.0 <= self.semantic_similarity_threshold <= 1.0:
            raise ValueError("semantic_similarity_threshold must be between 0.0 and 1.0")
    
    @classmethod
    def from_environment(cls) -> 'DecisionModeConfig':
        """Load configuration from environment variables with sensible defaults."""
        return cls(
            mode=os.getenv('DECISION_MODE', DecisionMode.DETERMINISTIC.value),
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '0.8')),
            hybrid_fallback_threshold=float(os.getenv('HYBRID_FALLBACK_THRESHOLD', '0.6')),
            semantic_similarity_threshold=float(os.getenv('SEMANTIC_SIMILARITY_THRESHOLD', '0.85')),
            context_analysis_enabled=os.getenv('CONTEXT_ANALYSIS_ENABLED', 'True').lower() == 'true'
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of validation errors."""
        errors = []
        
        if self.confidence_threshold < self.hybrid_fallback_threshold:
            errors.append("confidence_threshold should be >= hybrid_fallback_threshold")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionModeConfig':
        """Create configuration from dictionary."""
        return cls(**data)


@dataclass
class EnhancedMatcherConfig(MatcherConfig):
    """Extended matcher configuration with AI capabilities."""
    ai_provider_config: AIProviderConfig = field(default_factory=AIProviderConfig.from_environment)
    decision_mode_config: DecisionModeConfig = field(default_factory=DecisionModeConfig.from_environment)
    semantic_threshold: float = 0.85
    context_analysis_enabled: bool = True
    batch_processing_enabled: bool = True
    max_batch_size: int = 100
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__() if hasattr(super(), '__post_init__') else None
        
        if not 0.0 <= self.semantic_threshold <= 1.0:
            raise ValueError("semantic_threshold must be between 0.0 and 1.0")
        
        if self.max_batch_size <= 0:
            raise ValueError("max_batch_size must be positive")
    
    @classmethod
    def from_environment(cls) -> 'EnhancedMatcherConfig':
        """Load configuration from environment variables."""
        base_config = MatcherConfig()
        
        # Override weights from environment if provided
        weights = {}
        for field_name in base_config.weights.keys():
            env_key = f'MATCHER_WEIGHT_{field_name.upper()}'
            if os.getenv(env_key):
                weights[field_name] = float(os.getenv(env_key))
        
        if weights:
            base_config.weights.update(weights)
        
        return cls(
            weights=base_config.weights,
            threshold=float(os.getenv('MATCHER_THRESHOLD', str(base_config.threshold))),
            conflict_band=float(os.getenv('MATCHER_CONFLICT_BAND', str(base_config.conflict_band))),
            ai_provider_config=AIProviderConfig.from_environment(),
            decision_mode_config=DecisionModeConfig.from_environment(),
            semantic_threshold=float(os.getenv('MATCHER_SEMANTIC_THRESHOLD', '0.85')),
            context_analysis_enabled=os.getenv('MATCHER_CONTEXT_ANALYSIS_ENABLED', 'True').lower() == 'true',
            batch_processing_enabled=os.getenv('MATCHER_BATCH_PROCESSING_ENABLED', 'True').lower() == 'true',
            max_batch_size=int(os.getenv('MATCHER_MAX_BATCH_SIZE', '100'))
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of validation errors."""
        errors = []
        
        # Validate AI provider config
        errors.extend(self.ai_provider_config.validate())
        
        # Validate decision mode config
        errors.extend(self.decision_mode_config.validate())
        
        # Validate matcher-specific settings
        if self.semantic_threshold < self.decision_mode_config.semantic_similarity_threshold:
            errors.append("semantic_threshold should be >= decision_mode_config.semantic_similarity_threshold")
        
        return errors


@dataclass
class EnhancedReconcilerConfig(ReconcilerConfig):
    """Extended reconciler configuration with AI capabilities."""
    ai_provider_config: AIProviderConfig = field(default_factory=AIProviderConfig.from_environment)
    decision_mode_config: DecisionModeConfig = field(default_factory=DecisionModeConfig.from_environment)
    semantic_field_matching: bool = True
    ai_explanation_enabled: bool = True
    context_aware_tolerances: bool = True
    field_priority_weights: Dict[str, float] = field(default_factory=lambda: {
        "critical": 1.0,
        "important": 0.7,
        "optional": 0.3
    })
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__() if hasattr(super(), '__post_init__') else None
        
        # Validate field priority weights
        for priority, weight in self.field_priority_weights.items():
            if not 0.0 <= weight <= 1.0:
                raise ValueError(f"field_priority_weights[{priority}] must be between 0.0 and 1.0")
    
    @classmethod
    def from_environment(cls) -> 'EnhancedReconcilerConfig':
        """Load configuration from environment variables."""
        base_config = ReconcilerConfig()
        
        # Override numeric tolerances from environment if provided
        numeric_tolerance = {}
        for field_name in base_config.numeric_tolerance.keys():
            env_key = f'RECONCILER_TOLERANCE_{field_name.upper()}'
            if os.getenv(env_key):
                numeric_tolerance[field_name] = float(os.getenv(env_key))
        
        if numeric_tolerance:
            base_config.numeric_tolerance.update(numeric_tolerance)
        
        # Override critical fields from environment if provided
        critical_fields = base_config.critical_fields
        if os.getenv('RECONCILER_CRITICAL_FIELDS'):
            critical_fields = os.getenv('RECONCILER_CRITICAL_FIELDS').split(',')
        
        return cls(
            numeric_tolerance=base_config.numeric_tolerance,
            critical_fields=critical_fields,
            string_similarity_threshold=float(os.getenv('RECONCILER_STRING_SIMILARITY_THRESHOLD', 
                                                       str(base_config.string_similarity_threshold))),
            ai_provider_config=AIProviderConfig.from_environment(),
            decision_mode_config=DecisionModeConfig.from_environment(),
            semantic_field_matching=os.getenv('RECONCILER_SEMANTIC_FIELD_MATCHING', 'True').lower() == 'true',
            ai_explanation_enabled=os.getenv('RECONCILER_AI_EXPLANATION_ENABLED', 'True').lower() == 'true',
            context_aware_tolerances=os.getenv('RECONCILER_CONTEXT_AWARE_TOLERANCES', 'True').lower() == 'true'
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of validation errors."""
        errors = []
        
        # Validate AI provider config
        errors.extend(self.ai_provider_config.validate())
        
        # Validate decision mode config
        errors.extend(self.decision_mode_config.validate())
        
        # Validate reconciler-specific settings
        if not self.critical_fields:
            errors.append("critical_fields cannot be empty")
        
        return errors


@dataclass
class EnhancedReportConfig(ReportConfig):
    """Extended report configuration with AI capabilities."""
    ai_provider_config: AIProviderConfig = field(default_factory=AIProviderConfig.from_environment)
    include_ai_explanations: bool = True
    include_confidence_scores: bool = True
    include_decision_rationale: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv", "pdf"])
    
    @classmethod
    def from_environment(cls) -> 'EnhancedReportConfig':
        """Load configuration from environment variables."""
        base_config = ReportConfig()
        
        export_formats = ["json", "csv", "pdf"]
        if os.getenv('REPORT_EXPORT_FORMATS'):
            export_formats = os.getenv('REPORT_EXPORT_FORMATS').split(',')
        
        return cls(
            report_bucket=os.getenv('REPORT_BUCKET', base_config.report_bucket),
            include_summary_stats=os.getenv('REPORT_INCLUDE_SUMMARY_STATS', 'True').lower() == 'true',
            include_field_details=os.getenv('REPORT_INCLUDE_FIELD_DETAILS', 'True').lower() == 'true',
            ai_provider_config=AIProviderConfig.from_environment(),
            include_ai_explanations=os.getenv('REPORT_INCLUDE_AI_EXPLANATIONS', 'True').lower() == 'true',
            include_confidence_scores=os.getenv('REPORT_INCLUDE_CONFIDENCE_SCORES', 'True').lower() == 'true',
            include_decision_rationale=os.getenv('REPORT_INCLUDE_DECISION_RATIONALE', 'True').lower() == 'true',
            export_formats=export_formats
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of validation errors."""
        errors = []
        
        # Validate AI provider config
        errors.extend(self.ai_provider_config.validate())
        
        # Validate export formats
        valid_formats = ["json", "csv", "pdf", "xlsx"]
        for fmt in self.export_formats:
            if fmt not in valid_formats:
                errors.append(f"Invalid export format: {fmt}")
        
        return errors


class ConfigurationManager:
    """Manages configuration loading, validation, and persistence with deployment flexibility."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config"
        self.config_dir.mkdir(exist_ok=True)
        self.deployment_manager = DeploymentConfigManager()
        self.deployment_config = None
    
    def save_configuration(self, config: Union[EnhancedMatcherConfig, EnhancedReconcilerConfig, EnhancedReportConfig], 
                          filename: str) -> None:
        """Save configuration to file."""
        try:
            config_path = self.config_dir / f"{filename}.json"
            
            # Convert to dictionary for serialization
            if hasattr(config, '__dict__'):
                config_dict = self._serialize_config(config)
            else:
                config_dict = asdict(config)
            
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            logger.info(f"Configuration saved to {config_path}")
        
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def load_configuration(self, config_class: type, filename: str):
        """Load configuration from file."""
        try:
            config_path = self.config_dir / f"{filename}.json"
            
            if not config_path.exists():
                logger.warning(f"Configuration file {config_path} not found, using defaults")
                return config_class.from_environment()
            
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            
            return self._deserialize_config(config_class, config_dict)
        
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _serialize_config(self, config) -> Dict[str, Any]:
        """Serialize configuration object to dictionary."""
        result = {}
        
        for key, value in config.__dict__.items():
            if hasattr(value, '__dict__'):
                # Nested configuration object
                result[key] = self._serialize_config(value)
            elif hasattr(value, 'to_dict'):
                # Object with to_dict method
                result[key] = value.to_dict()
            else:
                # Simple value
                result[key] = value
        
        return result
    
    def _deserialize_config(self, config_class: type, config_dict: Dict[str, Any]):
        """Deserialize dictionary to configuration object."""
        # Handle nested configurations
        if 'ai_provider_config' in config_dict and isinstance(config_dict['ai_provider_config'], dict):
            config_dict['ai_provider_config'] = AIProviderConfig.from_dict(config_dict['ai_provider_config'])
        
        if 'decision_mode_config' in config_dict and isinstance(config_dict['decision_mode_config'], dict):
            config_dict['decision_mode_config'] = DecisionModeConfig.from_dict(config_dict['decision_mode_config'])
        
        return config_class(**config_dict)
    
    def load_deployment_specific_config(self, config_filename: str) -> Dict[str, Any]:
        """Load deployment-specific configuration file (YAML)."""
        try:
            if not self.deployment_config:
                self.deployment_config = self.deployment_manager.load_or_detect_config()
            
            # Try deployment-specific config first
            deployment_config_path = self.config_dir / f"{self.deployment_config.environment_type}_deployment.yaml"
            
            if deployment_config_path.exists():
                with open(deployment_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                logger.info(f"Loaded deployment-specific config: {deployment_config_path}")
                return config_data
            
            # Fallback to generic config
            generic_config_path = self.config_dir / f"{config_filename}.yaml"
            if generic_config_path.exists():
                with open(generic_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                logger.info(f"Loaded generic config: {generic_config_path}")
                return config_data
            
            logger.warning(f"No deployment config found for {config_filename}")
            return {}
        
        except Exception as e:
            logger.error(f"Failed to load deployment config: {e}")
            return {}
    
    def adapt_ai_provider_config(self, base_config: AIProviderConfig) -> AIProviderConfig:
        """Adapt AI provider configuration for current deployment environment."""
        if not self.deployment_config:
            self.deployment_config = self.deployment_manager.load_or_detect_config()
        
        # Get deployment-specific adaptations
        adapted_dict = adapt_config_for_environment(base_config.to_dict())
        
        # Apply deployment-specific overrides
        if self.deployment_config.environment_type == "vdi":
            adapted_dict.update({
                "provider_type": "huggingface",
                "timeout_seconds": min(adapted_dict.get("timeout_seconds", 30), 30),
                "max_retries": min(adapted_dict.get("max_retries", 3), 2)
            })
        elif self.deployment_config.environment_type == "standalone":
            adapted_dict.update({
                "provider_type": self.deployment_config.ai_provider_fallback,
                "fallback_provider": "huggingface"
            })
        elif self.deployment_config.environment_type == "laptop":
            # Use AWS services if available, otherwise fallback
            if self.deployment_config.ai_provider_fallback == "bedrock":
                adapted_dict["provider_type"] = "bedrock"
            else:
                adapted_dict["provider_type"] = "huggingface"
        
        return AIProviderConfig.from_dict(adapted_dict)
    
    def get_resource_constrained_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply resource constraints based on deployment environment."""
        if not self.deployment_config:
            self.deployment_config = self.deployment_manager.load_or_detect_config()
        
        constraints = self.deployment_config.resource_constraints
        adapted_config = base_config.copy()
        
        # Apply resource constraints
        adapted_config.update({
            "max_batch_size": min(adapted_config.get("max_batch_size", 100), 
                                constraints.get("batch_size_limit", 25)),
            "max_concurrent_operations": constraints.get("max_concurrent_operations", 4),
            "cache_size_mb": constraints.get("cache_size_mb", 512),
            "memory_limit_mb": constraints.get("max_memory_mb", 4096)
        })
        
        return adapted_config
    
    def validate_all_configurations(self, matcher_config: EnhancedMatcherConfig,
                                  reconciler_config: EnhancedReconcilerConfig,
                                  report_config: EnhancedReportConfig) -> List[str]:
        """Validate all configurations and return combined error list."""
        all_errors = []
        
        all_errors.extend([f"Matcher: {error}" for error in matcher_config.validate()])
        all_errors.extend([f"Reconciler: {error}" for error in reconciler_config.validate()])
        all_errors.extend([f"Report: {error}" for error in report_config.validate()])
        
        # Add deployment-specific validation
        if not self.deployment_config:
            self.deployment_config = self.deployment_manager.load_or_detect_config()
        
        # Validate deployment compatibility
        if (self.deployment_config.environment_type == "vdi" and 
            matcher_config.ai_provider_config.provider_type == "bedrock"):
            all_errors.append("Deployment: Bedrock not recommended for VDI environments")
        
        if (self.deployment_config.local_resources_only and 
            not self.deployment_config.network_restrictions and
            matcher_config.ai_provider_config.provider_type not in ["huggingface", "local"]):
            all_errors.append("Deployment: Non-local AI provider selected for local-only environment")
        
        return all_errors


def load_enhanced_configurations() -> tuple[EnhancedMatcherConfig, EnhancedReconcilerConfig, EnhancedReportConfig]:
    """Load all enhanced configurations with deployment flexibility support."""
    config_manager = ConfigurationManager()
    
    # Load base configurations from environment
    matcher_config = EnhancedMatcherConfig.from_environment()
    reconciler_config = EnhancedReconcilerConfig.from_environment()
    report_config = EnhancedReportConfig.from_environment()
    
    # Apply deployment-specific adaptations
    matcher_config.ai_provider_config = config_manager.adapt_ai_provider_config(matcher_config.ai_provider_config)
    reconciler_config.ai_provider_config = config_manager.adapt_ai_provider_config(reconciler_config.ai_provider_config)
    report_config.ai_provider_config = config_manager.adapt_ai_provider_config(report_config.ai_provider_config)
    
    # Apply resource constraints
    matcher_dict = config_manager.get_resource_constrained_config(asdict(matcher_config))
    matcher_config = EnhancedMatcherConfig(**matcher_dict)
    
    # Load deployment-specific configuration overrides
    deployment_config = config_manager.load_deployment_specific_config("enhanced_config")
    if deployment_config:
        # Apply deployment-specific overrides to configurations
        if "matcher" in deployment_config:
            matcher_overrides = deployment_config["matcher"]
            for key, value in matcher_overrides.items():
                if hasattr(matcher_config, key):
                    setattr(matcher_config, key, value)
        
        if "reconciler" in deployment_config:
            reconciler_overrides = deployment_config["reconciler"]
            for key, value in reconciler_overrides.items():
                if hasattr(reconciler_config, key):
                    setattr(reconciler_config, key, value)
        
        if "report" in deployment_config:
            report_overrides = deployment_config["report"]
            for key, value in report_overrides.items():
                if hasattr(report_config, key):
                    setattr(report_config, key, value)
    
    # Validate all configurations
    errors = config_manager.validate_all_configurations(matcher_config, reconciler_config, report_config)
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    deployment_env = get_deployment_config()
    logger.info(f"Enhanced configurations loaded for {deployment_env.environment_type} environment")
    return matcher_config, reconciler_config, report_config

@dataclass
class EnhancedConfig:
    """Main enhanced configuration class that combines all configuration components."""
    matcher_config: EnhancedMatcherConfig = field(default_factory=EnhancedMatcherConfig.from_environment)
    reconciler_config: EnhancedReconcilerConfig = field(default_factory=EnhancedReconcilerConfig.from_environment)
    report_config: EnhancedReportConfig = field(default_factory=EnhancedReportConfig.from_environment)
    deployment_environment: str = field(default_factory=lambda: os.getenv('DEPLOYMENT_ENVIRONMENT', 'aws'))
    
    @classmethod
    def from_environment(cls) -> 'EnhancedConfig':
        """Load complete enhanced configuration from environment."""
        matcher_config, reconciler_config, report_config = load_enhanced_configurations()
        
        return cls(
            matcher_config=matcher_config,
            reconciler_config=reconciler_config,
            report_config=report_config,
            deployment_environment=os.getenv('DEPLOYMENT_ENVIRONMENT', 'aws')
        )
    
    def validate(self) -> List[str]:
        """Validate all configuration components."""
        errors = []
        errors.extend([f"Matcher: {error}" for error in self.matcher_config.validate()])
        errors.extend([f"Reconciler: {error}" for error in self.reconciler_config.validate()])
        errors.extend([f"Report: {error}" for error in self.report_config.validate()])
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'matcher_config': asdict(self.matcher_config),
            'reconciler_config': asdict(self.reconciler_config),
            'report_config': asdict(self.report_config),
            'deployment_environment': self.deployment_environment
        }


def load_deployment_aware_config(config_type: str = "enhanced") -> Dict[str, Any]:
    """Load deployment-aware configuration for current environment."""
    config_manager = ConfigurationManager()
    deployment_config = config_manager.load_deployment_specific_config(config_type)
    
    # Apply environment-specific adaptations
    adapted_config = adapt_config_for_environment(deployment_config)
    
    return adapted_config