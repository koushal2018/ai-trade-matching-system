"""
Custom exceptions for AI Provider operations
"""


class AIProviderError(Exception):
    """Base exception for AI provider errors"""
    pass


class AIProviderUnavailableError(AIProviderError):
    """Raised when AI provider is unavailable or unreachable"""
    
    def __init__(self, provider_name: str, message: str = None):
        self.provider_name = provider_name
        if message is None:
            message = f"AI provider '{provider_name}' is unavailable"
        super().__init__(message)


class AIProviderConfigurationError(AIProviderError):
    """Raised when AI provider configuration is invalid or incomplete"""
    
    def __init__(self, provider_name: str, missing_config: str = None, message: str = None):
        self.provider_name = provider_name
        self.missing_config = missing_config
        if message is None:
            if missing_config:
                message = f"AI provider '{provider_name}' missing required configuration: {missing_config}"
            else:
                message = f"AI provider '{provider_name}' has invalid configuration"
        super().__init__(message)


class AIProviderTimeoutError(AIProviderError):
    """Raised when AI provider operation times out"""
    
    def __init__(self, provider_name: str, operation: str, timeout_seconds: int):
        self.provider_name = provider_name
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        message = f"AI provider '{provider_name}' operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(message)


class AIProviderRateLimitError(AIProviderError):
    """Raised when AI provider rate limit is exceeded"""
    
    def __init__(self, provider_name: str, retry_after: int = None):
        self.provider_name = provider_name
        self.retry_after = retry_after
        message = f"AI provider '{provider_name}' rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(message)