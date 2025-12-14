"""
AI Service Monitoring and Alerting Module

This module provides comprehensive monitoring and alerting capabilities for AI service
failures and fallback usage patterns in the enhanced trade reconciliation system.
"""

import json
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AIServiceAlert:
    """AI service alert data structure"""
    timestamp: float
    provider_name: str
    operation: str
    severity: AlertSeverity
    message: str
    error_type: Optional[str] = None
    failure_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class AIServiceAlerting:
    """AI service alerting system with configurable thresholds"""
    
    def __init__(self):
        self.alerts = []
        self.alert_thresholds = {
            'failure_rate_threshold': 0.5,  # 50% failure rate
            'consecutive_failures_threshold': 5,
            'fallback_rate_threshold': 0.3,  # 30% fallback rate
            'response_time_threshold_ms': 10000,  # 10 seconds
            'health_check_failure_threshold': 3
        }
        self.consecutive_failures = {}
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between similar alerts
        
    def configure_thresholds(self, thresholds: Dict[str, Any]):
        """Configure alert thresholds"""
        self.alert_thresholds.update(thresholds)
        logger.info(f"Alert thresholds updated: {self.alert_thresholds}")
        
    def check_failure_rate_alert(self, provider_name: str, operation: str, 
                                failure_count: int, total_count: int) -> Optional[AIServiceAlert]:
        """Check if failure rate exceeds threshold"""
        if total_count == 0:
            return None
            
        failure_rate = failure_count / total_count
        threshold = self.alert_thresholds['failure_rate_threshold']
        
        if failure_rate >= threshold:
            alert_key = f"{provider_name}:{operation}:failure_rate"
            if self._should_send_alert(alert_key):
                return AIServiceAlert(
                    timestamp=time.time(),
                    provider_name=provider_name,
                    operation=operation,
                    severity=AlertSeverity.ERROR,
                    message=f"High failure rate: {failure_rate:.2%} (threshold: {threshold:.2%})",
                    error_type="high_failure_rate",
                    failure_count=failure_count,
                    metadata={"failure_rate": failure_rate, "total_count": total_count}
                )
        return None
        
    def check_consecutive_failures_alert(self, provider_name: str, operation: str) -> Optional[AIServiceAlert]:
        """Check for consecutive failures"""
        key = f"{provider_name}:{operation}"
        if key not in self.consecutive_failures:
            self.consecutive_failures[key] = 0
            
        self.consecutive_failures[key] += 1
        threshold = self.alert_thresholds['consecutive_failures_threshold']
        
        if self.consecutive_failures[key] >= threshold:
            alert_key = f"{key}:consecutive_failures"
            if self._should_send_alert(alert_key):
                return AIServiceAlert(
                    timestamp=time.time(),
                    provider_name=provider_name,
                    operation=operation,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Consecutive failures: {self.consecutive_failures[key]} (threshold: {threshold})",
                    error_type="consecutive_failures",
                    failure_count=self.consecutive_failures[key]
                )
        return None
        
    def reset_consecutive_failures(self, provider_name: str, operation: str):
        """Reset consecutive failure count on success"""
        key = f"{provider_name}:{operation}"
        if key in self.consecutive_failures:
            self.consecutive_failures[key] = 0
            
    def check_fallback_rate_alert(self, provider_name: str, operation: str,
                                fallback_count: int, total_count: int) -> Optional[AIServiceAlert]:
        """Check if fallback usage rate exceeds threshold"""
        if total_count == 0:
            return None
            
        fallback_rate = fallback_count / total_count
        threshold = self.alert_thresholds['fallback_rate_threshold']
        
        if fallback_rate >= threshold:
            alert_key = f"{provider_name}:{operation}:fallback_rate"
            if self._should_send_alert(alert_key):
                return AIServiceAlert(
                    timestamp=time.time(),
                    provider_name=provider_name,
                    operation=operation,
                    severity=AlertSeverity.WARNING,
                    message=f"High fallback rate: {fallback_rate:.2%} (threshold: {threshold:.2%})",
                    error_type="high_fallback_rate",
                    failure_count=fallback_count,
                    metadata={"fallback_rate": fallback_rate, "total_count": total_count}
                )
        return None
        
    def check_response_time_alert(self, provider_name: str, operation: str,
                                avg_response_time_ms: float) -> Optional[AIServiceAlert]:
        """Check if average response time exceeds threshold"""
        threshold = self.alert_thresholds['response_time_threshold_ms']
        
        if avg_response_time_ms >= threshold:
            alert_key = f"{provider_name}:{operation}:response_time"
            if self._should_send_alert(alert_key):
                return AIServiceAlert(
                    timestamp=time.time(),
                    provider_name=provider_name,
                    operation=operation,
                    severity=AlertSeverity.WARNING,
                    message=f"Slow response time: {avg_response_time_ms:.0f}ms (threshold: {threshold}ms)",
                    error_type="slow_response",
                    metadata={"avg_response_time_ms": avg_response_time_ms}
                )
        return None
        
    def check_health_status_alert(self, provider_name: str, health_status: Dict[str, Any]) -> Optional[AIServiceAlert]:
        """Check health status and generate alerts"""
        status = health_status.get('status', 'unknown')
        
        if status in ['unhealthy', 'timeout', 'error']:
            alert_key = f"{provider_name}:health_check"
            if self._should_send_alert(alert_key):
                severity = AlertSeverity.CRITICAL if status == 'unhealthy' else AlertSeverity.ERROR
                return AIServiceAlert(
                    timestamp=time.time(),
                    provider_name=provider_name,
                    operation="health_check",
                    severity=severity,
                    message=f"Health check failed: {status}",
                    error_type="health_check_failure",
                    metadata=health_status
                )
        return None
        
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent based on cooldown period"""
        current_time = time.time()
        if alert_key in self.last_alert_time:
            time_since_last = current_time - self.last_alert_time[alert_key]
            if time_since_last < self.alert_cooldown:
                return False
                
        self.last_alert_time[alert_key] = current_time
        return True
        
    def add_alert(self, alert: AIServiceAlert):
        """Add alert to the alert list"""
        self.alerts.append(alert)
        logger.warning(f"AI Service Alert: {alert.severity.value.upper()} - {alert.message}")
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = time.time() - 86400  # 24 hours
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
        
    def get_recent_alerts(self, hours: int = 24) -> List[AIServiceAlert]:
        """Get alerts from the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        return [alert for alert in self.alerts if alert.timestamp > cutoff_time]
        
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of recent alerts"""
        recent_alerts = self.get_recent_alerts()
        
        summary = {
            "total_alerts": len(recent_alerts),
            "alerts_by_severity": {},
            "alerts_by_provider": {},
            "alerts_by_error_type": {},
            "most_recent_alert": None
        }
        
        for alert in recent_alerts:
            # Count by severity
            severity = alert.severity.value
            summary["alerts_by_severity"][severity] = summary["alerts_by_severity"].get(severity, 0) + 1
            
            # Count by provider
            provider = alert.provider_name
            summary["alerts_by_provider"][provider] = summary["alerts_by_provider"].get(provider, 0) + 1
            
            # Count by error type
            if alert.error_type:
                error_type = alert.error_type
                summary["alerts_by_error_type"][error_type] = summary["alerts_by_error_type"].get(error_type, 0) + 1
        
        if recent_alerts:
            most_recent = max(recent_alerts, key=lambda x: x.timestamp)
            summary["most_recent_alert"] = {
                "timestamp": most_recent.timestamp,
                "provider": most_recent.provider_name,
                "severity": most_recent.severity.value,
                "message": most_recent.message
            }
            
        return summary


class AIServiceMonitoringDashboard:
    """Dashboard for AI service monitoring with metrics aggregation"""
    
    def __init__(self, alerting_system: AIServiceAlerting):
        self.alerting = alerting_system
        
    def generate_monitoring_report(self, ai_monitor_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        report = {
            "timestamp": time.time(),
            "report_generated_at": datetime.now().isoformat(),
            "ai_service_health": {},
            "performance_metrics": {},
            "failure_analysis": {},
            "fallback_usage": {},
            "alerts_summary": self.alerting.get_alert_summary(),
            "recommendations": []
        }
        
        # Process health status
        health_status = ai_monitor_stats.get('health_status', {})
        for provider, status in health_status.items():
            report["ai_service_health"][provider] = {
                "status": status.get('status', 'unknown'),
                "last_check": status.get('timestamp', 0),
                "response_time_ms": status.get('response_time_ms', 0)
            }
            
            # Check for health alerts
            alert = self.alerting.check_health_status_alert(provider, status)
            if alert:
                self.alerting.add_alert(alert)
        
        # Process operation metrics
        operation_metrics = ai_monitor_stats.get('operation_metrics', {})
        for operation_key, metrics in operation_metrics.items():
            provider, operation = operation_key.split(':', 1)
            
            success_rate = metrics['successful_calls'] / metrics['total_calls'] if metrics['total_calls'] > 0 else 0
            failure_count = metrics['total_calls'] - metrics['successful_calls']
            
            report["performance_metrics"][operation_key] = {
                "total_calls": metrics['total_calls'],
                "successful_calls": metrics['successful_calls'],
                "success_rate": success_rate,
                "avg_duration_ms": metrics['avg_duration_ms']
            }
            
            # Check for performance alerts
            failure_alert = self.alerting.check_failure_rate_alert(
                provider, operation, failure_count, metrics['total_calls']
            )
            if failure_alert:
                self.alerting.add_alert(failure_alert)
                
            response_time_alert = self.alerting.check_response_time_alert(
                provider, operation, metrics['avg_duration_ms']
            )
            if response_time_alert:
                self.alerting.add_alert(response_time_alert)
        
        # Process failure counts
        failure_counts = ai_monitor_stats.get('failure_counts', {})
        for operation_key, failures in failure_counts.items():
            provider, operation = operation_key.split(':', 1)
            total_failures = sum(failures.values())
            
            report["failure_analysis"][operation_key] = {
                "total_failures": total_failures,
                "failure_breakdown": failures
            }
        
        # Process fallback usage
        fallback_counts = ai_monitor_stats.get('fallback_counts', {})
        for operation_key, fallbacks in fallback_counts.items():
            provider, operation = operation_key.split(':', 1)
            total_fallbacks = sum(fallbacks.values()) if isinstance(fallbacks, dict) else fallbacks
            
            report["fallback_usage"][operation_key] = {
                "total_fallbacks": total_fallbacks,
                "fallback_reasons": fallbacks if isinstance(fallbacks, dict) else {"unknown": fallbacks}
            }
            
            # Check for fallback rate alerts
            total_calls = operation_metrics.get(operation_key, {}).get('total_calls', 0)
            if total_calls > 0:
                fallback_alert = self.alerting.check_fallback_rate_alert(
                    provider, operation, total_fallbacks, total_calls
                )
                if fallback_alert:
                    self.alerting.add_alert(fallback_alert)
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        return report
        
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on monitoring data"""
        recommendations = []
        
        # Check for unhealthy services
        for provider, health in report["ai_service_health"].items():
            if health["status"] != "healthy":
                recommendations.append(f"Investigate {provider} service health - status: {health['status']}")
        
        # Check for high failure rates
        for operation_key, metrics in report["performance_metrics"].items():
            if metrics["success_rate"] < 0.8:  # Less than 80% success rate
                recommendations.append(f"High failure rate for {operation_key}: {metrics['success_rate']:.1%}")
        
        # Check for high fallback usage
        for operation_key, fallback_data in report["fallback_usage"].items():
            total_calls = report["performance_metrics"].get(operation_key, {}).get("total_calls", 0)
            if total_calls > 0:
                fallback_rate = fallback_data["total_fallbacks"] / total_calls
                if fallback_rate > 0.2:  # More than 20% fallback rate
                    recommendations.append(f"High fallback usage for {operation_key}: {fallback_rate:.1%}")
        
        # Check for slow response times
        for operation_key, metrics in report["performance_metrics"].items():
            if metrics["avg_duration_ms"] > 5000:  # Slower than 5 seconds
                recommendations.append(f"Slow response time for {operation_key}: {metrics['avg_duration_ms']:.0f}ms")
        
        return recommendations


# Global alerting system instance
ai_alerting = AIServiceAlerting()
ai_dashboard = AIServiceMonitoringDashboard(ai_alerting)


def configure_ai_monitoring(thresholds: Dict[str, Any] = None, cooldown: int = None):
    """Configure AI monitoring system"""
    if thresholds:
        ai_alerting.configure_thresholds(thresholds)
    if cooldown:
        ai_alerting.alert_cooldown = cooldown


def get_ai_monitoring_report(ai_monitor_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Get comprehensive AI monitoring report"""
    return ai_dashboard.generate_monitoring_report(ai_monitor_stats)


def get_ai_alerts(hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent AI service alerts"""
    alerts = ai_alerting.get_recent_alerts(hours)
    return [asdict(alert) for alert in alerts]