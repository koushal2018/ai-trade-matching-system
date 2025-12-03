"""Distributed tracing for AgentCore Observability."""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Any, Dict
from contextlib import contextmanager
from functools import wraps
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class Span:
    """Represents a single span in a distributed trace."""
    
    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.attributes = attributes or {}
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.status = "OK"
        self.events: list[Dict[str, Any]] = []
    
    def set_attribute(self, key: str, value: Any):
        """Set a span attribute."""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "attributes": attributes or {}
        })
    
    def set_status(self, status: str, description: Optional[str] = None):
        """Set span status (OK, ERROR)."""
        self.status = status
        if description:
            self.attributes["status_description"] = description
    
    def end(self):
        """End the span."""
        self.end_time = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for export."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time.isoformat() + "Z",
            "end_time": self.end_time.isoformat() + "Z" if self.end_time else None,
            "duration_ms": (self.end_time - self.start_time).total_seconds() * 1000 if self.end_time else None,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events
        }


class Tracer:
    """Distributed tracer for AgentCore Observability."""
    
    _current_trace_id: Optional[str] = None
    _current_span_id: Optional[str] = None
    _spans: list[Span] = []
    
    def __init__(self, service_name: str, region: str = "us-east-1"):
        self.service_name = service_name
        self.region = region
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.logs = boto3.client("logs", region_name=region)
        self.log_group = os.getenv("OBSERVABILITY_LOG_GROUP", "/agentcore/trade-matching")
    
    def start_trace(self, name: str, correlation_id: Optional[str] = None) -> Span:
        """Start a new trace."""
        trace_id = correlation_id or f"trace_{uuid.uuid4().hex}"
        span_id = f"span_{uuid.uuid4().hex[:16]}"
        
        Tracer._current_trace_id = trace_id
        Tracer._current_span_id = span_id
        
        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=span_id,
            attributes={"service.name": self.service_name}
        )
        Tracer._spans.append(span)
        return span
    
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new span within the current trace."""
        if not Tracer._current_trace_id:
            return self.start_trace(name)
        
        span_id = f"span_{uuid.uuid4().hex[:16]}"
        parent_span_id = Tracer._current_span_id
        
        span = Span(
            name=name,
            trace_id=Tracer._current_trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            attributes={**(attributes or {}), "service.name": self.service_name}
        )
        
        Tracer._current_span_id = span_id
        Tracer._spans.append(span)
        return span
    
    def end_span(self, span: Span):
        """End a span and export it."""
        span.end()
        Tracer._current_span_id = span.parent_span_id
        self._export_span(span)
    
    def _export_span(self, span: Span):
        """Export span to CloudWatch Logs."""
        try:
            log_stream = f"{self.service_name}/{datetime.utcnow().strftime('%Y/%m/%d')}"
            
            # Ensure log stream exists
            try:
                self.logs.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=log_stream
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
            
            # Put log event
            self.logs.put_log_events(
                logGroupName=self.log_group,
                logStreamName=log_stream,
                logEvents=[{
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "message": json.dumps(span.to_dict())
                }]
            )
        except Exception as e:
            logger.warning(f"Failed to export span: {e}")
    
    @staticmethod
    def get_current_trace_id() -> Optional[str]:
        """Get the current trace ID."""
        return Tracer._current_trace_id
    
    @staticmethod
    def get_trace_context() -> Dict[str, str]:
        """Get trace context for propagation."""
        return {
            "trace_id": Tracer._current_trace_id or "",
            "span_id": Tracer._current_span_id or ""
        }


# Global tracer instances per service
_tracers: Dict[str, Tracer] = {}


def get_tracer(service_name: str) -> Tracer:
    """Get or create a tracer for a service."""
    if service_name not in _tracers:
        _tracers[service_name] = Tracer(service_name)
    return _tracers[service_name]


@contextmanager
def create_span(service_name: str, span_name: str, attributes: Optional[Dict[str, Any]] = None):
    """Context manager for creating spans."""
    tracer = get_tracer(service_name)
    span = tracer.start_span(span_name, attributes)
    try:
        yield span
    except Exception as e:
        span.set_status("ERROR", str(e))
        raise
    finally:
        tracer.end_span(span)


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID."""
    return Tracer.get_current_trace_id()


def propagate_trace_context(event: Dict[str, Any]) -> Dict[str, Any]:
    """Add trace context to an event for propagation."""
    context = Tracer.get_trace_context()
    event["trace_context"] = context
    return event
