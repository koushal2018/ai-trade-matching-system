# Enhanced Strands Tools for AI-Powered Trade Reconciliation

## Overview

This module provides enhanced Strands tools that integrate AI capabilities with the existing trade reconciliation system. The tools support three operational modes:

- **Deterministic**: Uses rule-based logic and exact matching
- **LLM**: Uses AI providers for intelligent analysis and semantic understanding
- **Hybrid**: Combines deterministic and AI approaches for optimal results

## Available Tools

### 1. `ai_analyze_trade_context`

Analyzes trade documents to understand context and extract relevant fields.

**Parameters:**
- `trade_data` (Dict): Trade information to analyze
- `ai_provider` (Optional[AIProviderAdapter]): AI provider instance (required for LLM/hybrid modes)
- `mode` (str): Analysis mode ("deterministic", "llm", or "hybrid")

**Returns:**
```python
{
    "transaction_type": str,        # e.g., "commodity_trade", "fx_forward"
    "critical_fields": List[str],   # Fields essential for reconciliation
    "field_mappings": Dict[str, str], # Semantic field equivalents
    "confidence": float,            # Confidence score (0.0-1.0)
    "method": str,                  # Method used ("deterministic", "llm", "hybrid")
    "context_metadata": Dict        # Additional context information
}
```

**Example Usage:**
```python
@tool
async def analyze_trade(trade_data: Dict[str, Any]) -> Dict[str, Any]:
    result = await ai_analyze_trade_context(
        trade_data=trade_data,
        ai_provider=bedrock_provider,
        mode="hybrid"
    )
    return result
```

### 2. `semantic_field_match`

Compares fields using semantic understanding or exact matching.

**Parameters:**
- `field1_name` (str): First field name
- `field1_value` (Any): First field value
- `field2_name` (str): Second field name
- `field2_value` (Any): Second field value
- `ai_provider` (Optional[AIProviderAdapter]): AI provider instance
- `mode` (str): Matching mode ("deterministic", "llm", or "hybrid")
- `context` (str): Optional context information

**Returns:**
```python
{
    "match_status": str,           # "MATCHED", "MISMATCHED", "MISSING", "SEMANTIC_MISMATCH"
    "confidence": float,           # Confidence score (0.0-1.0)
    "reasoning": str,              # Human-readable explanation
    "field_name_similarity": float, # Semantic similarity of field names
    "method": str                  # Method used
}
```

**Example Usage:**
```python
@tool
async def compare_fields(bank_field: str, bank_value: Any, 
                        cpty_field: str, cpty_value: Any) -> Dict[str, Any]:
    result = await semantic_field_match(
        field1_name=bank_field,
        field1_value=bank_value,
        field2_name=cpty_field,
        field2_value=cpty_value,
        ai_provider=ai_provider,
        mode="llm",
        context="commodity_trade"
    )
    return result
```

### 3. `intelligent_trade_matching`

Performs comprehensive trade matching combining traditional and AI-based approaches.

**Parameters:**
- `trade1` (Dict): First trade data dictionary
- `trade2` (Dict): Second trade data dictionary
- `ai_provider` (Optional[AIProviderAdapter]): AI provider instance
- `mode` (str): Matching mode ("deterministic", "llm", or "hybrid")
- `weights` (Optional[Dict[str, float]]): Field weights for deterministic matching

**Returns:**
```python
{
    "match_confidence": float,      # Overall match confidence (0.0-1.0)
    "field_comparisons": Dict,      # Field-by-field comparison results
    "overall_status": str,          # "MATCHED", "PARTIAL_MATCH", "MISMATCHED"
    "reasoning": str,               # Explanation of matching decision
    "method": str                   # Method used
}
```

**Example Usage:**
```python
@tool
async def match_trades(bank_trade: Dict[str, Any], 
                      cpty_trade: Dict[str, Any]) -> Dict[str, Any]:
    result = await intelligent_trade_matching(
        trade1=bank_trade,
        trade2=cpty_trade,
        ai_provider=ai_provider,
        mode="hybrid",
        weights={
            "trade_date": 0.30,
            "total_notional_quantity": 0.25,
            "currency": 0.15,
            "counterparty": 0.20,
            "commodity_type": 0.10
        }
    )
    return result
```

### 4. `explain_mismatch`

Generates human-readable explanations for field mismatches.

**Parameters:**
- `field_name` (str): Name of the mismatched field
- `value1` (Any): First value
- `value2` (Any): Second value
- `ai_provider` (Optional[AIProviderAdapter]): AI provider instance
- `context` (str): Optional context information
- `mode` (str): Explanation mode ("deterministic", "llm", or "hybrid")

**Returns:**
- `str`: Human-readable explanation of the mismatch

**Example Usage:**
```python
@tool
async def get_mismatch_explanation(field: str, val1: Any, val2: Any) -> str:
    explanation = await explain_mismatch(
        field_name=field,
        value1=val1,
        value2=val2,
        ai_provider=ai_provider,
        mode="llm",
        context="commodity_swap"
    )
    return explanation
```

### 5. `context_aware_field_extraction`

Identifies relevant fields for comparison based on transaction type.

**Parameters:**
- `trade_data` (Dict): Trade data dictionary
- `transaction_type` (str): Type of transaction
- `ai_provider` (Optional[AIProviderAdapter]): AI provider instance
- `mode` (str): Extraction mode ("deterministic", "llm", or "hybrid")

**Returns:**
```python
{
    "extracted_fields": List[str],   # Fields relevant for this transaction type
    "field_priorities": Dict,        # Field importance categories
    "field_mappings": Dict[str, str], # Standard field mappings
    "transaction_type": str,         # Transaction type
    "method": str                    # Method used
}
```

**Example Usage:**
```python
@tool
async def extract_relevant_fields(trade: Dict[str, Any], 
                                 tx_type: str) -> Dict[str, Any]:
    result = await context_aware_field_extraction(
        trade_data=trade,
        transaction_type=tx_type,
        ai_provider=ai_provider,
        mode="hybrid"
    )
    return result
```

## Error Handling and Fallback Mechanisms

All tools implement robust error handling with automatic fallback to deterministic methods:

### `robust_ai_operation` Function

This utility function provides:
- **Retry Logic**: Exponential backoff for transient failures
- **Timeout Handling**: Graceful handling of AI service timeouts
- **Automatic Fallback**: Falls back to deterministic methods when AI fails
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

### Exception Types Handled

- `AIProviderTimeoutError`: AI service timeout
- `AIProviderUnavailableError`: AI service unavailable
- `AIProviderError`: General AI service errors
- `Exception`: Unexpected errors

### Fallback Behavior

When AI operations fail, the system automatically:
1. Logs the failure with appropriate severity
2. Calls the deterministic fallback function
3. Returns results with method indicator showing fallback was used
4. Maintains system availability and functionality

## Integration with Strands Agents

### Enhanced Agent Configuration

The tools integrate with enhanced configuration classes:

```python
from enhanced_config import EnhancedMatcherConfig, EnhancedReconcilerConfig

# Load enhanced configuration
matcher_config = EnhancedMatcherConfig.from_environment()
reconciler_config = EnhancedReconcilerConfig.from_environment()

# Initialize AI provider
ai_provider = await initialize_ai_provider_from_config(matcher_config)
```

### Agent System Prompts

Enhanced agents should include AI configuration in their system prompts:

```python
ENHANCED_TRADE_MATCHER_PROMPT = """
You are an enhanced trade matching agent with configurable AI capabilities.

Your configuration:
- AI Provider: {ai_provider_type}
- Decision Mode: {decision_mode}
- Matching Threshold: {threshold}

Enhanced Tasks:
1. Use ai_analyze_trade_context tool to understand trade types
2. Apply semantic_field_match for intelligent field comparison
3. Use intelligent_trade_matching for comprehensive matching
4. Generate detailed explanations using explain_mismatch tool
"""
```

## Performance Considerations

### Batching and Caching

- **Intelligent Batching**: Group similar operations to reduce API calls
- **Result Caching**: Cache AI analysis results to avoid redundant processing
- **Parallel Processing**: Use asyncio for concurrent operations

### Monitoring and Metrics

- **Response Times**: Track AI vs deterministic processing times
- **Fallback Rates**: Monitor frequency of fallback usage
- **Confidence Scores**: Track AI confidence levels over time
- **Error Rates**: Monitor AI service availability and error patterns

## Configuration Examples

### Environment Variables

```bash
# AI Provider Configuration
AI_PROVIDER_TYPE=bedrock
AI_PROVIDER_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Decision Mode Configuration
DECISION_MODE=hybrid
CONFIDENCE_THRESHOLD=0.8
SEMANTIC_SIMILARITY_THRESHOLD=0.85

# Fallback Configuration
AI_FALLBACK_PROVIDER=huggingface
AI_TIMEOUT_SECONDS=30
AI_MAX_RETRIES=3
```

### Programmatic Configuration

```python
from enhanced_config import AIProviderConfig, DecisionModeConfig

# AI Provider Configuration
ai_config = AIProviderConfig(
    provider_type="bedrock",
    region="us-east-1",
    model_config={
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "max_tokens": 4096,
        "temperature": 0.1
    },
    fallback_provider="sagemaker",
    timeout_seconds=30,
    max_retries=3
)

# Decision Mode Configuration
decision_config = DecisionModeConfig(
    mode="hybrid",
    confidence_threshold=0.8,
    hybrid_fallback_threshold=0.6,
    semantic_similarity_threshold=0.85,
    context_analysis_enabled=True
)
```

## Testing and Validation

### Unit Tests

Run the basic functionality tests:

```bash
python strandsagents/test_enhanced_tools_basic.py
```

### Integration Tests

Test with actual AI providers:

```bash
python strandsagents/test_enhanced_tools.py
```

### Performance Tests

Benchmark deterministic vs AI performance:

```python
import time
import asyncio

async def benchmark_modes():
    trade_data = {...}  # Sample trade data
    
    # Test deterministic mode
    start = time.time()
    det_result = await ai_analyze_trade_context(trade_data, mode="deterministic")
    det_time = time.time() - start
    
    # Test AI mode
    start = time.time()
    ai_result = await ai_analyze_trade_context(trade_data, ai_provider, mode="llm")
    ai_time = time.time() - start
    
    print(f"Deterministic: {det_time:.3f}s, AI: {ai_time:.3f}s")
```

## Best Practices

### 1. Mode Selection

- **Deterministic**: Use for high-volume, low-latency scenarios
- **LLM**: Use for complex, ambiguous cases requiring semantic understanding
- **Hybrid**: Use for balanced approach with fallback capabilities

### 2. Error Handling

- Always provide fallback functions for AI operations
- Log AI failures appropriately for monitoring
- Use appropriate timeout values for your environment

### 3. Performance Optimization

- Cache AI results for similar inputs
- Use batch processing for multiple operations
- Monitor and tune confidence thresholds

### 4. Configuration Management

- Use environment variables for deployment flexibility
- Validate configurations before use
- Implement configuration versioning for reproducibility

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and paths are correct
2. **AI Provider Failures**: Check credentials, regions, and service availability
3. **Timeout Issues**: Adjust timeout settings based on your environment
4. **Performance Issues**: Consider using deterministic mode for high-volume scenarios

### Debugging

Enable detailed logging:

```python
import logging
logging.getLogger("strandsagents.enhanced_tools").setLevel(logging.DEBUG)
```

### Health Checks

Monitor AI provider health:

```python
health_status = await ai_provider.health_check()
print(f"Provider status: {health_status['status']}")
```

## Future Enhancements

### Planned Features

1. **Learning Mechanisms**: Improve AI performance through usage patterns
2. **Custom Prompts**: Allow domain-specific prompt customization
3. **Multi-Model Support**: Use different models for different tasks
4. **Advanced Caching**: Implement intelligent caching strategies
5. **Metrics Dashboard**: Real-time monitoring and analytics

### Extension Points

The tools are designed to be extensible:

- Add new AI providers through the factory pattern
- Implement custom fallback strategies
- Add domain-specific semantic mappings
- Integrate with external monitoring systems

## Conclusion

The enhanced Strands tools provide a powerful foundation for AI-powered trade reconciliation while maintaining backward compatibility and robust fallback mechanisms. The three-mode approach (deterministic, LLM, hybrid) allows for flexible deployment across different environments and requirements.

For questions or issues, refer to the test files and configuration examples provided in this documentation.