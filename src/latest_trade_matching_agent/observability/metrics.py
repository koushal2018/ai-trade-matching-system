"""Metrics collection for AgentCore Observability."""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import defaultdict
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and publishes metrics to CloudWatch."""
    
    def __init__(self, namespace: str = "TradeMatching/Agents", region: str = "us-east-1"):
        self.namespace = namespace
        self.region = region
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self._metrics_buffer: List[Dict[str, Any]] = []
        self._buffer_size = 20  # Batch size for CloudWatch
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record a metric value."""
        metric_data = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Timestamp": datetime.utcnow(),
            "Dimensions": [
                {"Name": k, "Value": v}
                for k, v in (dimensions or {}).items()
            ]
        }
        
        self._metrics_buffer.append(metric_data)
        
        if len(self._metrics_buffer) >= self._buffer_size:
            self._flush_metrics()
    
    def _flush_metrics(self):
        """Flush metrics buffer to CloudWatch."""
        if not self._metrics_buffer:
            return
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=self._metrics_buffer
            )
            logger.debug(f"Flushed {len(self._metrics_buffer)} metrics to CloudWatch")
        except ClientError as e:
            logger.warning(f"Failed to publish metrics: {e}")
        finally:
            self._metrics_buffer = []
    
    def record_latency(self, agent_name: str, operation: str, latency_ms: float):
        """Record operation latency."""
        self.record_metric(
            metric_name="Latency",
            value=latency_ms,
            unit="Milliseconds",
            dimensions={"Agent": agent_name, "Operation": operation}
        )
    
    def record_throughput(self, agent_name: str, count: int = 1):
        """Record throughput (items processed)."""
        self.record_metric(
            metric_name="Throughput",
            value=count,
            unit="Count",
            dimensions={"Agent": agent_name}
        )
    
    def record_error(self, agent_name: str, error_type: str):
        """Record an error occurrence."""
        self.record_metric(
            metric_name="Errors",
            value=1,
            unit="Count",
            dimensions={"Agent": agent_name, "ErrorType": error_type}
        )
    
    def record_match_score(self, score: float, classification: str):
        """Record a match score."""
        self.record_metric(
            metric_name="MatchScore",
            value=score,
            unit="None",
            dimensions={"Classification": classification}
        )
    
    def flush(self):
        """Force flush all buffered metrics."""
        self._flush_metrics()


# Global metrics collector
_collector: Optional[MetricsCollector] = None


def get_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


# Convenience functions
def record_latency(agent_name: str, operation: str, latency_ms: float):
    """Record operation latency."""
    get_collector().record_latency(agent_name, operation, latency_ms)


def record_throughput(agent_name: str, count: int = 1):
    """Record throughput."""
    get_collector().record_throughput(agent_name, count)


def record_error(agent_name: str, error_type: str):
    """Record an error."""
    get_collector().record_error(agent_name, error_type)


def get_metrics_summary(agent_name: str) -> Dict[str, Any]:
    """Get metrics summary for an agent (from CloudWatch)."""
    collector = get_collector()
    
    try:
        # Get latency statistics
        latency_response = collector.cloudwatch.get_metric_statistics(
            Namespace=collector.namespace,
            MetricName="Latency",
            Dimensions=[{"Name": "Agent", "Value": agent_name}],
            StartTime=datetime.utcnow().replace(hour=0, minute=0, second=0),
            EndTime=datetime.utcnow(),
            Period=3600,
            Statistics=["Average", "Maximum", "Minimum"]
        )
        
        # Get error count
        error_response = collector.cloudwatch.get_metric_statistics(
            Namespace=collector.namespace,
            MetricName="Errors",
            Dimensions=[{"Name": "Agent", "Value": agent_name}],
            StartTime=datetime.utcnow().replace(hour=0, minute=0, second=0),
            EndTime=datetime.utcnow(),
            Period=3600,
            Statistics=["Sum"]
        )
        
        # Get throughput
        throughput_response = collector.cloudwatch.get_metric_statistics(
            Namespace=collector.namespace,
            MetricName="Throughput",
            Dimensions=[{"Name": "Agent", "Value": agent_name}],
            StartTime=datetime.utcnow().replace(hour=0, minute=0, second=0),
            EndTime=datetime.utcnow(),
            Period=3600,
            Statistics=["Sum"]
        )
        
        latency_data = latency_response.get("Datapoints", [{}])
        error_data = error_response.get("Datapoints", [{}])
        throughput_data = throughput_response.get("Datapoints", [{}])
        
        return {
            "agent": agent_name,
            "latency": {
                "avg_ms": latency_data[0].get("Average", 0) if latency_data else 0,
                "max_ms": latency_data[0].get("Maximum", 0) if latency_data else 0,
                "min_ms": latency_data[0].get("Minimum", 0) if latency_data else 0
            },
            "errors": sum(d.get("Sum", 0) for d in error_data),
            "throughput": sum(d.get("Sum", 0) for d in throughput_data),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except ClientError as e:
        logger.warning(f"Failed to get metrics summary: {e}")
        return {
            "agent": agent_name,
            "latency": {"avg_ms": 0, "max_ms": 0, "min_ms": 0},
            "errors": 0,
            "throughput": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
