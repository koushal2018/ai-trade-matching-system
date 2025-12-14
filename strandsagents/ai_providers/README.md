# AI Provider Abstraction Layer

This module provides a unified interface for different AI providers including AWS Bedrock, Sagemaker AI Jumpstart, and Huggingface models for the Enhanced Trade Reconciliation System.

## Overview

The AI Provider Abstraction Layer implements a factory pattern to create and manage different AI providers with consistent interfaces. This allows the trade reconciliation system to work with multiple AI services while maintaining the same API.

## Architecture

```
ai_providers/
├── __init__.py              # Package initialization and exports
├── base.py                  # Abstract base class and data structures
├── bedrock_adapter.py       # AWS Bedrock implementation
├── sagemaker_adapter.py     # AWS Sagemaker implementation
├── huggingface_adapter.py   # Hugging Face implementation
├── factory.py               # Factory pattern for provider creation
├── exceptions.py            # Custom exception classes
└── README.md               # This documentation
```

## Supported Providers

### 1. AWS Bedrock (`BedrockAdapter`)
- **Use Case**: Primary choice for regions where Bedrock is available
- **Models**: Claude 3 Sonnet (default), other Bedrock foundation models
- **Configuration**: Requires AWS region and optional model ID
- **Features**: High-quality responses, enterprise-grade security

### 2. AWS Sagemaker (`SagemakerAdapter`)
- **Use Case**: UAE region compatibility where Bedrock may not be available
- **Models**: Any deployed Sagemaker endpoint with foundation models
- **Configuration**: Requires AWS region and endpoint name
- **Features**: Custom model deployments, regional flexibility

### 3. Hugging Face (`HuggingfaceAdapter`)
- **Use Case**: Fallback option for environments without AWS AI services
- **Models**: Any Hugging Face model (API or local)
- **Configuration**: Model name, optional API token
- **Features**: Local deployment option, wide model selection

## Core Components

### AIProviderAdapter (Base Class)

Abstract base class defining the interface all providers must implement:

```python
class AIProviderAdapter(ABC):
    async def initialize(self, config: Dict[str, Any]) -> bool
    async def analyze_document_context(self, document_data: Dict[str, Any]) -> DocumentAnalysisResult
    async def semantic_field_matching(self, field1: str, field2: str, context: str) -> SemanticMatchResult
    async def intelligent_trade_matching(self, trade1: Dict[str, Any], trade2: Dict[str, Any]) -> IntelligentMatchResult
    async def explain_mismatch(self, field_name: str, value1: Any, value2: Any, context: str) -> str
    async def health_check(self) -> Dict[str, Any]
```

### Data Structures

#### DocumentAnalysisResult
```python
@dataclass
class DocumentAnalysisResult:
    transaction_type: str           # e.g., "commodity_swap", "fx_forward"
    critical_fields: List[str]      # Essential fields for reconciliation
    field_mappings: Dict[str, str]  # Semantic field mappings
    confidence: float               # Analysis confidence (0.0-1.0)
    context_metadata: Dict[str, Any] # Additional context information
```

#### SemanticMatchResult
```python
@dataclass
class SemanticMatchResult:
    similarity_score: float  # Semantic similarity (0.0-1.0)
    is_match: bool          # Whether fields are semantically equivalent
    reasoning: str          # Human-readable explanation
    confidence: float       # Confidence in the result (0.0-1.0)
```

#### IntelligentMatchResult
```python
@dataclass
class IntelligentMatchResult:
    match_confidence: float              # Overall match confidence
    field_comparisons: Dict[str, Any]    # Field-by-field comparison results
    overall_status: str                  # "MATCHED", "MISMATCHED", "UNCERTAIN"
    reasoning: str                       # Explanation of the decision
    method_used: str                     # Method used for matching
```

### Factory Pattern

The `AIProviderFactory` class provides convenient methods for creating and initializing providers:

```python
# Create and initialize a provider
provider = await AIProviderFactory.create_and_initialize_provider(
    provider_type='bedrock',
    config={'region': 'us-east-1'},
    fallback_providers=['sagemaker', 'huggingface']
)

# Validate configuration
validation = AIProviderFactory.validate_config('bedrock', config)
```

## Usage Examples

### Basic Usage

```python
from ai_providers import AIProviderFactory

# Create and initialize Bedrock provider
provider = await AIProviderFactory.create_and_initialize_provider(
    'bedrock', 
    {'region': 'us-east-1'}
)

# Analyze a trade document
document_data = {
    'trade_date': '2024-01-15',
    'commodity_type': 'crude_oil',
    'notional': 1000000,
    'currency': 'USD'
}

analysis = await provider.analyze_document_context(document_data)
print(f"Transaction type: {analysis.transaction_type}")
print(f"Critical fields: {analysis.critical_fields}")
```

### Semantic Field Matching

```python
# Compare field names semantically
result = await provider.semantic_field_matching(
    'settlement_date', 
    'maturity_date', 
    'commodity swap'
)

if result.is_match:
    print(f"Fields are semantically equivalent (confidence: {result.confidence})")
    print(f"Reasoning: {result.reasoning}")
```

### Intelligent Trade Matching

```python
trade1 = {'trade_date': '2024-01-15', 'notional': 1000000, 'currency': 'USD'}
trade2 = {'settlement_date': '2024-01-15', 'amount': '1,000,000 USD'}

match_result = await provider.intelligent_trade_matching(trade1, trade2)
print(f"Match confidence: {match_result.match_confidence}")
print(f"Status: {match_result.overall_status}")
```

### Configuration Examples

#### Bedrock Configuration
```python
bedrock_config = {
    'region': 'us-east-1',
    'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0',
    'max_tokens': 4096,
    'temperature': 0.1
}
```

#### Sagemaker Configuration
```python
sagemaker_config = {
    'region': 'me-central-1',
    'endpoint_name': 'huggingface-text-generation-endpoint',
    'model_type': 'huggingface',
    'content_type': 'application/json'
}
```

#### Hugging Face Configuration
```python
huggingface_config = {
    'model_name': 'microsoft/DialoGPT-medium',
    'api_token': 'your_hf_token_here',
    'use_local': False,
    'max_length': 1024
}
```

## Error Handling

The module provides comprehensive error handling with custom exception classes:

- `AIProviderError`: Base exception for all AI provider errors
- `AIProviderConfigurationError`: Invalid or missing configuration
- `AIProviderUnavailableError`: Provider service is unavailable
- `AIProviderTimeoutError`: Operation timed out
- `AIProviderRateLimitError`: Rate limit exceeded

```python
try:
    provider = await AIProviderFactory.create_and_initialize_provider(
        'bedrock', 
        {'region': 'us-east-1'}
    )
except AIProviderConfigurationError as e:
    print(f"Configuration error: {e}")
except AIProviderUnavailableError as e:
    print(f"Service unavailable: {e}")
```

## Testing

The module includes comprehensive tests:

- `test_ai_providers_basic.py`: Basic functionality tests (no external dependencies)
- `test_ai_providers.py`: Full functionality tests

Run tests:
```bash
cd strandsagents
python test_ai_providers_basic.py  # Basic tests
python test_ai_providers.py        # Full tests
```

## Integration with Strands Framework

This AI Provider Abstraction Layer is designed to integrate seamlessly with the Strands agents framework:

1. **Tool Integration**: Each provider method can be wrapped as a Strands tool
2. **Configuration Management**: Providers can be configured through Strands configuration
3. **Error Handling**: Errors are handled gracefully with fallback to deterministic methods
4. **Async Support**: All operations are async-compatible with Strands workflows

## Performance Considerations

- **Caching**: Results can be cached to avoid redundant API calls
- **Batching**: Multiple operations can be batched for efficiency
- **Timeouts**: All operations have configurable timeouts
- **Fallback**: Automatic fallback to alternative providers or deterministic methods

## Security

- **Credentials**: Uses standard AWS credential chain and environment variables
- **Validation**: Input validation and sanitization
- **Logging**: Comprehensive logging without exposing sensitive data
- **Error Handling**: Graceful error handling without information leakage

## Future Extensions

The architecture supports easy extension:

1. **New Providers**: Add new AI providers by implementing `AIProviderAdapter`
2. **Custom Models**: Support for custom or fine-tuned models
3. **Caching Layer**: Add intelligent caching for improved performance
4. **Monitoring**: Add metrics and monitoring capabilities

## Dependencies

- `boto3`: AWS SDK for Bedrock and Sagemaker
- `aiohttp`: HTTP client for Hugging Face API (optional)
- `transformers`: Hugging Face transformers library (optional for local models)

Install dependencies:
```bash
pip install boto3 aiohttp transformers torch
```

## Conclusion

The AI Provider Abstraction Layer provides a robust, flexible foundation for integrating multiple AI services into the Enhanced Trade Reconciliation System. It supports the requirements for configurable AI providers, regional deployment flexibility, and seamless integration with the existing Strands framework.