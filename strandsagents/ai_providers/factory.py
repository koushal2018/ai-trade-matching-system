"""
Factory pattern for creating AI provider adapters
"""

import logging
from typing import Dict, Any, Optional, Type
from .base import AIProviderAdapter
from .bedrock_adapter import BedrockAdapter
from .sagemaker_adapter import SagemakerAdapter
from .huggingface_adapter import HuggingfaceAdapter
from .exceptions import AIProviderConfigurationError, AIProviderError

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """
    Factory class for creating AI provider adapters based on configuration.
    
    Supports provider selection, fallback mechanisms, and configuration validation.
    """
    
    # Registry of available providers
    _providers: Dict[str, Type[AIProviderAdapter]] = {
        'bedrock': BedrockAdapter,
        'sagemaker': SagemakerAdapter,
        'huggingface': HuggingfaceAdapter
    }
    
    @classmethod
    def create_provider(
        self, 
        provider_type: str, 
        config: Dict[str, Any],
        fallback_providers: Optional[list] = None
    ) -> AIProviderAdapter:
        """
        Create an AI provider adapter instance.
        
        Args:
            provider_type: Type of provider ('bedrock', 'sagemaker', 'huggingface')
            config: Configuration dictionary for the provider
            fallback_providers: Optional list of fallback provider types
            
        Returns:
            Initialized AI provider adapter
            
        Raises:
            AIProviderConfigurationError: If provider type is invalid
            AIProviderError: If provider creation fails
        """
        provider_type = provider_type.lower()
        
        if provider_type not in self._providers:
            available_providers = ', '.join(self._providers.keys())
            raise AIProviderConfigurationError(
                "AIProviderFactory",
                "provider_type",
                f"Unknown provider type '{provider_type}'. Available: {available_providers}"
            )
        
        try:
            # Create primary provider
            provider_class = self._providers[provider_type]
            provider = provider_class()
            
            logger.info(f"Created {provider_type} provider adapter")
            return provider
            
        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {e}")
            
            # Try fallback providers if specified
            if fallback_providers:
                for fallback_type in fallback_providers:
                    try:
                        logger.info(f"Attempting fallback to {fallback_type} provider")
                        return self.create_provider(fallback_type, config)
                    except Exception as fallback_error:
                        logger.warning(f"Fallback to {fallback_type} also failed: {fallback_error}")
                        continue
            
            raise AIProviderError(f"Failed to create any provider. Primary error: {str(e)}")
    
    @classmethod
    async def create_and_initialize_provider(
        self,
        provider_type: str,
        config: Dict[str, Any],
        fallback_providers: Optional[list] = None
    ) -> AIProviderAdapter:
        """
        Create and initialize an AI provider adapter.
        
        Args:
            provider_type: Type of provider ('bedrock', 'sagemaker', 'huggingface')
            config: Configuration dictionary for the provider
            fallback_providers: Optional list of fallback provider types
            
        Returns:
            Initialized and ready-to-use AI provider adapter
            
        Raises:
            AIProviderConfigurationError: If provider type is invalid
            AIProviderError: If provider creation or initialization fails
        """
        provider = self.create_provider(provider_type, config, fallback_providers)
        
        try:
            # Initialize the provider
            success = await provider.initialize(config)
            if not success:
                raise AIProviderError(f"Provider {provider_type} initialization returned False")
            
            logger.info(f"Successfully initialized {provider_type} provider")
            return provider
            
        except Exception as e:
            logger.error(f"Failed to initialize {provider_type} provider: {e}")
            
            # Try fallback providers if specified
            if fallback_providers:
                for fallback_type in fallback_providers:
                    try:
                        logger.info(f"Attempting fallback initialization with {fallback_type}")
                        fallback_config = self._adapt_config_for_provider(config, fallback_type)
                        return await self.create_and_initialize_provider(
                            fallback_type, 
                            fallback_config
                        )
                    except Exception as fallback_error:
                        logger.warning(f"Fallback initialization with {fallback_type} failed: {fallback_error}")
                        continue
            
            raise AIProviderError(f"Failed to initialize any provider. Primary error: {str(e)}")
    
    @classmethod
    def _adapt_config_for_provider(self, config: Dict[str, Any], provider_type: str) -> Dict[str, Any]:
        """
        Adapt configuration for different provider types.
        
        Args:
            config: Original configuration
            provider_type: Target provider type
            
        Returns:
            Adapted configuration dictionary
        """
        adapted_config = config.copy()
        
        if provider_type == 'bedrock':
            # Ensure Bedrock-specific config
            if 'model_id' not in adapted_config:
                adapted_config['model_id'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
                
        elif provider_type == 'sagemaker':
            # Ensure Sagemaker-specific config
            if 'endpoint_name' not in adapted_config:
                # Try to derive from model name or use default
                model_name = adapted_config.get('model_name', 'huggingface-text-generation')
                adapted_config['endpoint_name'] = f"{model_name}-endpoint"
                
        elif provider_type == 'huggingface':
            # Ensure Huggingface-specific config
            if 'model_name' not in adapted_config:
                adapted_config['model_name'] = 'microsoft/DialoGPT-medium'
            # Default to API mode if not specified
            if 'use_local' not in adapted_config:
                adapted_config['use_local'] = False
        
        return adapted_config
    
    @classmethod
    def get_available_providers(self) -> list:
        """
        Get list of available provider types.
        
        Returns:
            List of available provider type strings
        """
        return list(self._providers.keys())
    
    @classmethod
    def register_provider(self, provider_type: str, provider_class: Type[AIProviderAdapter]):
        """
        Register a new provider type.
        
        Args:
            provider_type: String identifier for the provider
            provider_class: Provider adapter class
        """
        if not issubclass(provider_class, AIProviderAdapter):
            raise ValueError(f"Provider class must inherit from AIProviderAdapter")
        
        self._providers[provider_type.lower()] = provider_class
        logger.info(f"Registered new provider type: {provider_type}")
    
    @classmethod
    def validate_config(self, provider_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration for a specific provider type.
        
        Args:
            provider_type: Type of provider to validate for
            config: Configuration dictionary to validate
            
        Returns:
            Dictionary with validation results
            
        Example return:
        {
            "valid": True,
            "missing_required": [],
            "warnings": [],
            "adapted_config": {...}
        }
        """
        provider_type = provider_type.lower()
        result = {
            "valid": True,
            "missing_required": [],
            "warnings": [],
            "adapted_config": config.copy()
        }
        
        if provider_type == 'bedrock':
            # Validate Bedrock config
            if not config.get('region'):
                result["missing_required"].append('region')
                result["valid"] = False
            
            if not config.get('model_id'):
                result["warnings"].append('model_id not specified, will use default Claude 3 Sonnet')
                result["adapted_config"]['model_id'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
                
        elif provider_type == 'sagemaker':
            # Validate Sagemaker config
            if not config.get('region'):
                result["missing_required"].append('region')
                result["valid"] = False
                
            if not config.get('endpoint_name'):
                result["missing_required"].append('endpoint_name')
                result["valid"] = False
                
        elif provider_type == 'huggingface':
            # Validate Huggingface config
            if not config.get('model_name'):
                result["warnings"].append('model_name not specified, will use default DialoGPT')
                result["adapted_config"]['model_name'] = 'microsoft/DialoGPT-medium'
            
            use_local = config.get('use_local', False)
            if use_local and not config.get('api_token'):
                result["warnings"].append('Local model usage specified but may require API token for some models')
        else:
            result["valid"] = False
            result["missing_required"].append(f"Unknown provider type: {provider_type}")
        
        return result


# Convenience functions for common use cases
async def create_bedrock_provider(region: str, model_id: str = None) -> BedrockAdapter:
    """
    Convenience function to create and initialize a Bedrock provider.
    
    Args:
        region: AWS region
        model_id: Optional Bedrock model ID
        
    Returns:
        Initialized Bedrock adapter
    """
    config = {'region': region}
    if model_id:
        config['model_id'] = model_id
    
    return await AIProviderFactory.create_and_initialize_provider('bedrock', config)


async def create_sagemaker_provider(region: str, endpoint_name: str) -> SagemakerAdapter:
    """
    Convenience function to create and initialize a Sagemaker provider.
    
    Args:
        region: AWS region
        endpoint_name: Sagemaker endpoint name
        
    Returns:
        Initialized Sagemaker adapter
    """
    config = {
        'region': region,
        'endpoint_name': endpoint_name
    }
    
    return await AIProviderFactory.create_and_initialize_provider('sagemaker', config)


async def create_huggingface_provider(
    model_name: str, 
    api_token: str = None, 
    use_local: bool = False
) -> HuggingfaceAdapter:
    """
    Convenience function to create and initialize a Hugging Face provider.
    
    Args:
        model_name: Hugging Face model name
        api_token: Optional API token
        use_local: Whether to use local transformers
        
    Returns:
        Initialized Hugging Face adapter
    """
    config = {
        'model_name': model_name,
        'use_local': use_local
    }
    if api_token:
        config['api_token'] = api_token
    
    return await AIProviderFactory.create_and_initialize_provider('huggingface', config)