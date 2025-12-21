"""
Enhanced AgentCore Observability for Trade Extraction Agent

This builds on your existing observability implementation to add:
- Advanced distributed tracing
- Custom metrics for trade extraction quality
- Anomaly detection for extraction patterns
- Performance optimization insights
"""

from bedrock_agentcore.observability import Observability
import json
from typing import Dict, Any
from datetime import datetime
import re

class EnhancedTradeExtractionObservability:
    """Enhanced observability for trade extraction with PII redaction and advanced metrics."""
    
    def __init__(self, stage: str = "production"):
        self.observability = Observability(
            service_name="trade-extraction-agent",
            stage=stage,
            verbosity="high" if stage == "development" else "medium"
        )
        
        # PII patterns for financial data redaction
        self.pii_patterns = {
            "trade_id": r"(trade_id[\"']?\s*[:=]\s*[\"']?)([^\"',}\s]+)",
            "counterparty": r"(counterparty[\"']?\s*[:=]\s*[\"']?)([^\"',}\s]+)",
            "notional": r"(notional[\"']?\s*[:=]\s*[\"']?)(\d+\.?\d*)",
            "account_number": r"(account[\"']?\s*[:=]\s*[\"']?)(\d{8,})",
            "swift_code": r"([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?)",
        }
    
    def redact_pii(self, text: str) -> str:
        """Redact PII from text before logging."""
        redacted_text = text
        for pattern_name, pattern in self.pii_patterns.items():
            redacted_text = re.sub(pattern, r'\1[REDACTED]', redacted_text)
        return redacted_text
    
    def start_extraction_span(self, 
                            document_id: str,
                            source_type: str,
                            correlation_id: str) -> Any:
        """Start a distributed tracing span for trade extraction."""
        span = self.observability.start_span("extract_trade_data")
        
        # Set standard attributes
        span.set_attribute("agent_name", "trade_extraction_agent")
        span.set_attribute("document_id", document_id)
        span.set_attribute("source_type", source_type)
        span.set_attribute("correlation_id", correlation_id)
        span.set_attribute("operation", "trade_extraction")
        span.set_attribute("timestamp", datetime.utcnow().isoformat())
        
        return span
    
    def record_extraction_metrics(self, 
                                span: Any,
                                extraction_result: Dict[str, Any],
                                processing_time_ms: float,
                                token_usage: Dict[str, int]) -> None:
        """Record detailed extraction metrics."""
        try:
            # Basic performance metrics
            span.set_attribute("processing_time_ms", processing_time_ms)
            span.set_attribute("input_tokens", token_usage.get("input_tokens", 0))
            span.set_attribute("output_tokens", token_usage.get("output_tokens", 0))
            span.set_attribute("total_tokens", token_usage.get("total_tokens", 0))
            
            # Success/failure tracking
            span.set_attribute("success", extraction_result.get("success", False))
            
            if extraction_result.get("success"):
                # Quality metrics for successful extractions
                trade_data = extraction_result.get("trade_data", {})
                
                # Count extracted fields
                extracted_fields = len([v for v in trade_data.values() if v is not None and v != ""])
                span.set_attribute("extracted_fields_count", extracted_fields)
                
                # Track field completeness (using lowercase trade_id to match actual DynamoDB schema)
                required_fields = ["trade_id", "internal_reference", "TRADE_SOURCE", "notional", "currency", "counterparty"]
                complete_fields = sum(1 for field in required_fields if trade_data.get(field))
                completeness_ratio = complete_fields / len(required_fields)
                span.set_attribute("field_completeness_ratio", completeness_ratio)
                
                # Track extraction confidence if available
                confidence = extraction_result.get("extraction_confidence", 0.0)
                span.set_attribute("extraction_confidence", confidence)
                
                # Track data quality indicators
                if trade_data.get("notional"):
                    try:
                        notional_value = float(trade_data["notional"])
                        span.set_attribute("notional_amount", notional_value)
                        # Flag unusual amounts for anomaly detection
                        if notional_value > 1_000_000_000:  # > $1B
                            span.set_attribute("high_value_trade", True)
                    except (ValueError, TypeError):
                        span.set_attribute("notional_parsing_error", True)
                
                # Track source classification accuracy
                source_type = extraction_result.get("source_type", "")
                trade_source = trade_data.get("TRADE_SOURCE", "")
                if source_type and trade_source:
                    source_match = source_type.upper() == trade_source.upper()
                    span.set_attribute("source_classification_accurate", source_match)
                
            else:
                # Error tracking
                error_type = extraction_result.get("error_type", "unknown")
                span.set_attribute("error_type", error_type)
                
                # Redact PII from error messages
                error_message = extraction_result.get("error", "")
                redacted_error = self.redact_pii(error_message)
                span.set_attribute("error_message", redacted_error[:500])  # Truncate long errors
                
                # Categorize errors for better analysis
                if "DynamoDB" in error_message or "dynamodb" in error_message:
                    span.set_attribute("error_category", "database")
                elif "S3" in error_message or "s3" in error_message:
                    span.set_attribute("error_category", "storage")
                elif "Bedrock" in error_message or "bedrock" in error_message:
                    span.set_attribute("error_category", "model")
                elif "validation" in error_message.lower():
                    span.set_attribute("error_category", "validation")
                else:
                    span.set_attribute("error_category", "unknown")
            
            # Cost estimation (approximate Nova Pro pricing)
            input_cost = token_usage.get("input_tokens", 0) * 0.0008 / 1000
            output_cost = token_usage.get("output_tokens", 0) * 0.0032 / 1000
            total_cost = input_cost + output_cost
            span.set_attribute("estimated_cost_usd", round(total_cost, 6))
            
        except Exception as e:
            # Don't let observability errors break the main flow
            span.set_attribute("observability_error", str(e)[:200])
    
    def record_memory_interaction(self, 
                                span: Any,
                                memory_operation: str,
                                patterns_found: int = 0,
                                confidence_boost: float = 0.0) -> None:
        """Record memory interaction metrics."""
        try:
            span.set_attribute("memory_operation", memory_operation)
            span.set_attribute("similar_patterns_found", patterns_found)
            span.set_attribute("confidence_boost_applied", confidence_boost)
            span.set_attribute("memory_enabled", True)
        except Exception:
            pass
    
    def record_policy_validation(self, 
                               span: Any,
                               policy_result: Dict[str, Any]) -> None:
        """Record policy validation metrics."""
        try:
            span.set_attribute("policy_validation_enabled", True)
            span.set_attribute("policy_compliant", policy_result.get("success", False))
            
            if not policy_result.get("success"):
                validation_failed = policy_result.get("validation_failed", "unknown")
                span.set_attribute("policy_violation_type", validation_failed)
                
                if policy_result.get("requires_escalation"):
                    span.set_attribute("requires_escalation", True)
        except Exception:
            pass
    
    def create_custom_metrics(self, extraction_results: Dict[str, Any]) -> None:
        """Create custom CloudWatch metrics for extraction quality."""
        try:
            # This would integrate with CloudWatch to create custom metrics
            # for monitoring extraction quality over time
            
            metrics_data = []
            
            if extraction_results.get("success"):
                # Success rate metric
                metrics_data.append({
                    'MetricName': 'ExtractionSuccessRate',
                    'Value': 1.0,
                    'Unit': 'Count'
                })
                
                # Field completeness metric
                completeness = extraction_results.get("field_completeness_ratio", 0.0)
                metrics_data.append({
                    'MetricName': 'FieldCompletenessRatio',
                    'Value': completeness,
                    'Unit': 'Percent'
                })
                
                # Extraction confidence metric
                confidence = extraction_results.get("extraction_confidence", 0.0)
                metrics_data.append({
                    'MetricName': 'ExtractionConfidence',
                    'Value': confidence,
                    'Unit': 'Percent'
                })
            else:
                # Failure rate metric
                metrics_data.append({
                    'MetricName': 'ExtractionSuccessRate',
                    'Value': 0.0,
                    'Unit': 'Count'
                })
            
            # Processing time metric
            processing_time = extraction_results.get("processing_time_ms", 0)
            metrics_data.append({
                'MetricName': 'ProcessingTimeMs',
                'Value': processing_time,
                'Unit': 'Milliseconds'
            })
            
            # Token usage metrics
            token_usage = extraction_results.get("token_usage", {})
            if token_usage:
                metrics_data.append({
                    'MetricName': 'TokenUsage',
                    'Value': token_usage.get("total_tokens", 0),
                    'Unit': 'Count'
                })
            
            # Send metrics to CloudWatch (implementation would depend on your setup)
            # self.observability.put_metric_data(
            #     Namespace='AgentCore/TradeExtraction',
            #     MetricData=metrics_data
            # )
            
        except Exception as e:
            print(f"Failed to create custom metrics: {e}")

# Enhanced observability integration for your agent
def create_enhanced_observability_wrapper(original_invoke_function):
    """
    Wrapper to enhance your existing invoke function with advanced observability.
    
    This preserves your existing implementation while adding enhanced tracking.
    """
    def enhanced_invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        # Initialize enhanced observability
        obs = EnhancedTradeExtractionObservability(
            stage=os.getenv("OBSERVABILITY_STAGE", "production")
        )
        
        # Extract key information
        document_id = payload.get("document_id", "unknown")
        source_type = payload.get("source_type", "unknown")
        correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
        
        # Start enhanced tracing span
        span = obs.start_extraction_span(document_id, source_type, correlation_id)
        
        try:
            # Call your original invoke function
            result = original_invoke_function(payload, context)
            
            # Record enhanced metrics
            processing_time = result.get("processing_time_ms", 0)
            token_usage = result.get("token_usage", {})
            
            obs.record_extraction_metrics(span, result, processing_time, token_usage)
            
            # Record memory interactions if present
            if result.get("memory_patterns_used"):
                obs.record_memory_interaction(
                    span, 
                    "pattern_retrieval",
                    patterns_found=result.get("patterns_found", 0),
                    confidence_boost=result.get("confidence_boost", 0.0)
                )
            
            # Record policy validation if present
            if result.get("policy_validation"):
                obs.record_policy_validation(span, result["policy_validation"])
            
            # Create custom metrics
            obs.create_custom_metrics(result)
            
            return result
            
        except Exception as e:
            # Record error in span
            span.set_attribute("success", False)
            span.set_attribute("error_type", type(e).__name__)
            span.set_attribute("error_message", obs.redact_pii(str(e))[:500])
            raise
            
        finally:
            # Close span
            span.__exit__(None, None, None)
    
    return enhanced_invoke

# Usage example:
# Your existing invoke function would be wrapped like this:
# invoke = create_enhanced_observability_wrapper(invoke)