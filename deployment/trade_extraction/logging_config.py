"""
Centralized logging configuration for Trade Extraction Agent.

This module provides standardized logging setup and utilities for consistent
logging across all components of the Trade Extraction Agent.
"""

import logging
import structlog
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone


def setup_structured_logging(
    service_name: str = "trade-extraction-agent",
    log_level: str = "INFO",
    correlation_id: Optional[str] = None
) -> None:
    """
    Set up structured logging with consistent format.
    
    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        correlation_id: Optional correlation ID for request tracing
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Add service context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        service=service_name,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    if correlation_id:
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def log_operation_metrics(
    operation_name: str,
    duration_ms: float,
    success: bool,
    additional_metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log operation metrics in a standardized format.
    
    Args:
        operation_name: Name of the operation
        duration_ms: Operation duration in milliseconds
        success: Whether the operation succeeded
        additional_metrics: Additional metrics to log
    """
    logger = get_logger("metrics")
    
    metrics = {
        "operation": operation_name,
        "duration_ms": duration_ms,
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if additional_metrics:
        metrics.update(additional_metrics)
    
    if success:
        logger.info("OPERATION_METRICS", **metrics)
    else:
        logger.error("OPERATION_METRICS_FAILED", **metrics)


def log_aws_operation(
    service: str,
    operation: str,
    duration_ms: float,
    success: bool,
    request_params: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    """
    Log AWS operation with standardized format.
    
    Args:
        service: AWS service name
        operation: Operation name
        duration_ms: Operation duration
        success: Success status
        request_params: Request parameters (sanitized)
        response_data: Response data (sanitized)
        error: Error message if failed
    """
    logger = get_logger("aws_operations")
    
    log_data = {
        "aws_service": service,
        "aws_operation": operation,
        "duration_ms": duration_ms,
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if request_params:
        # Sanitize sensitive data
        sanitized_params = {k: v for k, v in request_params.items() 
                          if k not in ['AccessKeyId', 'SecretAccessKey', 'SessionToken']}
        log_data["request_params"] = sanitized_params
    
    if response_data:
        log_data["response_keys"] = list(response_data.keys()) if isinstance(response_data, dict) else []
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info("AWS_OPERATION_SUCCESS", **log_data)
    else:
        logger.error("AWS_OPERATION_FAILED", **log_data)


def log_validation_result(
    validation_type: str,
    input_data: Any,
    is_valid: bool,
    errors: Optional[list] = None,
    warnings: Optional[list] = None
) -> None:
    """
    Log validation results with standardized format.
    
    Args:
        validation_type: Type of validation performed
        input_data: Input data being validated (sanitized)
        is_valid: Validation result
        errors: List of validation errors
        warnings: List of validation warnings
    """
    logger = get_logger("validation")
    
    log_data = {
        "validation_type": validation_type,
        "is_valid": is_valid,
        "input_type": type(input_data).__name__,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Sanitize input data for logging
    if isinstance(input_data, str) and len(input_data) > 100:
        log_data["input_preview"] = input_data[:100] + "..."
    elif isinstance(input_data, dict):
        log_data["input_keys"] = list(input_data.keys())
    else:
        log_data["input_value"] = str(input_data)
    
    if errors:
        log_data["errors"] = errors
        log_data["error_count"] = len(errors)
    
    if warnings:
        log_data["warnings"] = warnings
        log_data["warning_count"] = len(warnings)
    
    if is_valid:
        logger.info("VALIDATION_SUCCESS", **log_data)
    else:
        logger.warning("VALIDATION_FAILED", **log_data)