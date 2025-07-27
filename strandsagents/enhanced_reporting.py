"""
Enhanced Reporting Module for AI-Powered Trade Reconciliation

This module provides comprehensive reporting capabilities with AI decision explanations,
confidence scores, structured output formats, and intuitive visualizations.
"""

import json
import logging
import uuid
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from decimal import Decimal
import csv
import io
from pathlib import Path

from strands import tool

try:
    from .enhanced_config import EnhancedReportConfig
    from .models import TradeMatch, ReconciliationResult, FieldComparisonResult
except ImportError:
    from enhanced_config import EnhancedReportConfig
    from models import TradeMatch, ReconciliationResult, FieldComparisonResult

logger = logging.getLogger(__name__)


@dataclass
class AIDecisionExplanation:
    """Structured explanation of AI decision-making process"""
    decision_type: str  # "matching", "reconciliation", "field_comparison"
    confidence_score: float
    reasoning: str
    context_analysis: Dict[str, Any]
    method_used: str  # "deterministic", "llm", "hybrid"
    processing_time_ms: float
    fallback_used: bool = False
    fallback_reason: Optional[str] = None


@dataclass
class EnhancedReconciliationReport:
    """Comprehensive reconciliation report with AI insights"""
    report_id: str
    generation_timestamp: str
    processing_summary: Dict[str, Any]
    ai_insights: Dict[str, Any]
    detailed_results: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    visualization_data: Dict[str, Any]
    recommendations: List[str]
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv", "pdf"])


class ReportVisualizationGenerator:
    """Generates visualization data for reconciliation reports"""
    
    def __init__(self):
        self.chart_colors = {
            "matched": "#10B981",      # Green
            "mismatched": "#EF4444",   # Red
            "partial": "#F59E0B",      # Amber
            "pending": "#6B7280",      # Gray
            "ai_enhanced": "#3B82F6",  # Blue
            "deterministic": "#8B5CF6" # Purple
        }
    
    def generate_status_distribution_chart(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate data for status distribution pie chart"""
        status_counts = {}
        for result in results:
            status = result.get('overall_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "type": "pie",
            "title": "Reconciliation Status Distribution",
            "data": {
                "labels": list(status_counts.keys()),
                "datasets": [{
                    "data": list(status_counts.values()),
                    "backgroundColor": [
                        self.chart_colors.get(status.lower(), "#6B7280") 
                        for status in status_counts.keys()
                    ]
                }]
            }
        }
    
    def generate_confidence_score_histogram(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate confidence score distribution histogram"""
        confidence_scores = []
        for result in results:
            if 'ai_explanation' in result and 'confidence_score' in result['ai_explanation']:
                confidence_scores.append(result['ai_explanation']['confidence_score'])
        
        # Create histogram bins
        bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        bin_counts = [0] * (len(bins) - 1)
        
        for score in confidence_scores:
            for i in range(len(bins) - 1):
                if bins[i] <= score < bins[i + 1]:
                    bin_counts[i] += 1
                    break
        
        return {
            "type": "bar",
            "title": "AI Confidence Score Distribution",
            "data": {
                "labels": [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)],
                "datasets": [{
                    "label": "Number of Trades",
                    "data": bin_counts,
                    "backgroundColor": self.chart_colors["ai_enhanced"]
                }]
            }
        }    

    def generate_method_comparison_chart(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comparison chart between AI and deterministic methods"""
        method_stats = {
            "deterministic": {"count": 0, "avg_confidence": 0, "success_rate": 0},
            "llm": {"count": 0, "avg_confidence": 0, "success_rate": 0},
            "hybrid": {"count": 0, "avg_confidence": 0, "success_rate": 0}
        }
        
        for result in results:
            method = result.get('ai_explanation', {}).get('method_used', 'deterministic')
            if method in method_stats:
                method_stats[method]["count"] += 1
                confidence = result.get('ai_explanation', {}).get('confidence_score', 0.8)
                method_stats[method]["avg_confidence"] += confidence
                
                # Consider successful if status is FULLY_MATCHED or PARTIALLY_MATCHED
                status = result.get('overall_status', '')
                if status in ['FULLY_MATCHED', 'PARTIALLY_MATCHED']:
                    method_stats[method]["success_rate"] += 1
        
        # Calculate averages
        for method, stats in method_stats.items():
            if stats["count"] > 0:
                stats["avg_confidence"] /= stats["count"]
                stats["success_rate"] = stats["success_rate"] / stats["count"] * 100
        
        return {
            "type": "grouped_bar",
            "title": "Method Performance Comparison",
            "data": {
                "labels": list(method_stats.keys()),
                "datasets": [
                    {
                        "label": "Average Confidence",
                        "data": [stats["avg_confidence"] for stats in method_stats.values()],
                        "backgroundColor": self.chart_colors["ai_enhanced"]
                    },
                    {
                        "label": "Success Rate (%)",
                        "data": [stats["success_rate"] for stats in method_stats.values()],
                        "backgroundColor": self.chart_colors["matched"]
                    }
                ]
            }
        }
    
    def generate_processing_time_chart(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate processing time comparison chart"""
        time_data = performance_metrics.get('processing_times', {})
        
        return {
            "type": "bar",
            "title": "Processing Time by Component (ms)",
            "data": {
                "labels": list(time_data.keys()),
                "datasets": [{
                    "label": "Processing Time (ms)",
                    "data": list(time_data.values()),
                    "backgroundColor": [
                        self.chart_colors["ai_enhanced"] if "ai" in label.lower() 
                        else self.chart_colors["deterministic"]
                        for label in time_data.keys()
                    ]
                }]
            }
        }
    
    def generate_field_mismatch_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate field-level mismatch analysis chart"""
        field_mismatches = {}
        
        for result in results:
            field_results = result.get('field_results', {})
            for field_name, field_result in field_results.items():
                if isinstance(field_result, dict) and field_result.get('status') == 'MISMATCHED':
                    field_mismatches[field_name] = field_mismatches.get(field_name, 0) + 1
        
        # Sort by frequency
        sorted_fields = sorted(field_mismatches.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "type": "horizontal_bar",
            "title": "Most Common Field Mismatches",
            "data": {
                "labels": [field for field, count in sorted_fields[:10]],  # Top 10
                "datasets": [{
                    "label": "Mismatch Count",
                    "data": [count for field, count in sorted_fields[:10]],
                    "backgroundColor": self.chart_colors["mismatched"]
                }]
            }
        }


class AIInsightsAnalyzer:
    """Analyzes AI decision patterns and generates insights"""
    
    def __init__(self):
        self.insight_patterns = {
            "high_confidence_pattern": lambda results: self._analyze_high_confidence_pattern(results),
            "fallback_usage_pattern": lambda results: self._analyze_fallback_usage(results),
            "semantic_matching_effectiveness": lambda results: self._analyze_semantic_matching(results),
            "context_analysis_impact": lambda results: self._analyze_context_impact(results)
        }
    
    def generate_ai_insights(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive AI insights from reconciliation results"""
        insights = {}
        
        for pattern_name, analyzer in self.insight_patterns.items():
            try:
                insights[pattern_name] = analyzer(results)
            except Exception as e:
                logger.warning(f"Failed to analyze pattern {pattern_name}: {e}")
                insights[pattern_name] = {"error": str(e)}
        
        return insights
    
    def _analyze_high_confidence_pattern(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in high-confidence AI decisions"""
        high_confidence_results = [
            r for r in results 
            if r.get('ai_explanation', {}).get('confidence_score', 0) >= 0.9
        ]
        
        if not high_confidence_results:
            return {"message": "No high-confidence AI decisions found"}
        
        # Analyze transaction types in high-confidence decisions
        transaction_types = {}
        for result in high_confidence_results:
            tx_type = result.get('ai_explanation', {}).get('context_analysis', {}).get('transaction_type', 'unknown')
            transaction_types[tx_type] = transaction_types.get(tx_type, 0) + 1
        
        return {
            "total_high_confidence": len(high_confidence_results),
            "percentage_of_total": len(high_confidence_results) / len(results) * 100,
            "common_transaction_types": dict(sorted(transaction_types.items(), key=lambda x: x[1], reverse=True)),
            "recommendation": "High-confidence decisions show strong AI performance in these transaction types"
        }
    
    def _analyze_fallback_usage(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze AI fallback usage patterns"""
        fallback_results = [
            r for r in results 
            if r.get('ai_explanation', {}).get('fallback_used', False)
        ]
        
        if not fallback_results:
            return {"message": "No AI fallback usage detected"}
        
        # Analyze fallback reasons
        fallback_reasons = {}
        for result in fallback_results:
            reason = result.get('ai_explanation', {}).get('fallback_reason', 'unknown')
            fallback_reasons[reason] = fallback_reasons.get(reason, 0) + 1
        
        return {
            "total_fallbacks": len(fallback_results),
            "fallback_rate": len(fallback_results) / len(results) * 100,
            "common_reasons": dict(sorted(fallback_reasons.items(), key=lambda x: x[1], reverse=True)),
            "recommendation": "Monitor AI service health to reduce fallback usage"
        }
    
    def _analyze_semantic_matching(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze semantic matching effectiveness"""
        semantic_results = [
            r for r in results 
            if r.get('ai_explanation', {}).get('method_used') in ['llm', 'hybrid']
        ]
        
        if not semantic_results:
            return {"message": "No semantic matching results found"}
        
        # Calculate semantic matching success rate
        successful_semantic = [
            r for r in semantic_results 
            if r.get('overall_status') in ['FULLY_MATCHED', 'PARTIALLY_MATCHED']
        ]
        
        success_rate = len(successful_semantic) / len(semantic_results) * 100
        
        return {
            "total_semantic_matches": len(semantic_results),
            "success_rate": success_rate,
            "avg_confidence": sum(r.get('ai_explanation', {}).get('confidence_score', 0) for r in semantic_results) / len(semantic_results),
            "recommendation": f"Semantic matching shows {success_rate:.1f}% success rate"
        }
    
    def _analyze_context_impact(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze impact of context analysis on matching accuracy"""
        context_enabled_results = [
            r for r in results 
            if r.get('ai_explanation', {}).get('context_analysis', {}).get('transaction_type') != 'unknown'
        ]
        
        if not context_enabled_results:
            return {"message": "No context analysis data found"}
        
        # Compare success rates with and without context
        context_success = [
            r for r in context_enabled_results 
            if r.get('overall_status') in ['FULLY_MATCHED', 'PARTIALLY_MATCHED']
        ]
        
        context_success_rate = len(context_success) / len(context_enabled_results) * 100
        
        return {
            "context_enabled_trades": len(context_enabled_results),
            "context_success_rate": context_success_rate,
            "recommendation": f"Context analysis improves matching accuracy to {context_success_rate:.1f}%"
        }


class UserFriendlyExplanationGenerator:
    """Generates user-friendly explanations for AI decisions"""
    
    def __init__(self):
        self.explanation_templates = {
            "matching_decision": self._generate_matching_explanation,
            "field_comparison": self._generate_field_explanation,
            "mismatch_reason": self._generate_mismatch_explanation,
            "confidence_assessment": self._generate_confidence_explanation
        }
    
    def generate_explanation(self, explanation_type: str, data: Dict[str, Any]) -> str:
        """Generate user-friendly explanation for given type and data"""
        if explanation_type in self.explanation_templates:
            return self.explanation_templates[explanation_type](data)
        else:
            return f"No explanation template available for {explanation_type}"
    
    def _generate_matching_explanation(self, data: Dict[str, Any]) -> str:
        """Generate explanation for trade matching decision"""
        confidence = data.get('confidence_score', 0)
        method = data.get('method_used', 'deterministic')
        transaction_type = data.get('context_analysis', {}).get('transaction_type', 'trade')
        
        if confidence >= 0.9:
            confidence_desc = "very high confidence"
        elif confidence >= 0.8:
            confidence_desc = "high confidence"
        elif confidence >= 0.6:
            confidence_desc = "moderate confidence"
        else:
            confidence_desc = "low confidence"
        
        method_desc = {
            'deterministic': 'rule-based analysis',
            'llm': 'AI semantic analysis',
            'hybrid': 'combined AI and rule-based analysis'
        }.get(method, method)
        
        return f"This {transaction_type} was matched with {confidence_desc} ({confidence:.1%}) using {method_desc}. " \
               f"The system analyzed key fields and found sufficient similarity to establish a match."
    
    def _generate_field_explanation(self, data: Dict[str, Any]) -> str:
        """Generate explanation for field comparison result"""
        field_name = data.get('field_name', 'field')
        status = data.get('status', 'unknown')
        confidence = data.get('confidence', 0)
        reasoning = data.get('reasoning', '')
        
        status_desc = {
            'MATCHED': 'matched successfully',
            'MISMATCHED': 'did not match',
            'MISSING': 'was missing from one document'
        }.get(status, status)
        
        return f"The {field_name} field {status_desc} with {confidence:.1%} confidence. {reasoning}"
    
    def _generate_mismatch_explanation(self, data: Dict[str, Any]) -> str:
        """Generate explanation for field mismatch"""
        field_name = data.get('field_name', 'field')
        bank_value = data.get('bank_value', 'N/A')
        counterparty_value = data.get('counterparty_value', 'N/A')
        reason = data.get('reason', 'Values differ')
        
        return f"The {field_name} field shows a mismatch: Bank document shows '{bank_value}' " \
               f"while counterparty document shows '{counterparty_value}'. {reason}"
    
    def _generate_confidence_explanation(self, data: Dict[str, Any]) -> str:
        """Generate explanation for confidence score"""
        confidence = data.get('confidence_score', 0)
        factors = data.get('confidence_factors', [])
        
        if confidence >= 0.9:
            explanation = "Very high confidence - all critical fields matched with strong semantic similarity."
        elif confidence >= 0.8:
            explanation = "High confidence - most critical fields matched with good semantic similarity."
        elif confidence >= 0.6:
            explanation = "Moderate confidence - some fields matched but with notable differences."
        else:
            explanation = "Low confidence - significant differences found in critical fields."
        
        if factors:
            factor_text = ", ".join(factors)
            explanation += f" Key factors: {factor_text}."
        
        return explanation


@tool
async def generate_enhanced_reconciliation_report(
    results: List[Dict[str, Any]],
    config: Optional[EnhancedReportConfig] = None,
    include_visualizations: bool = True
) -> Dict[str, Any]:
    """
    Generate comprehensive reconciliation report with AI insights and visualizations.
    
    Args:
        results: List of reconciliation results
        config: Report configuration
        include_visualizations: Whether to include visualization data
        
    Returns:
        Enhanced reconciliation report with AI explanations and insights
    """
    if config is None:
        config = EnhancedReportConfig.from_environment()
    
    start_time = time.time()
    report_id = str(uuid.uuid4())
    
    logger.info(f"Generating enhanced reconciliation report {report_id} for {len(results)} results")
    
    # Initialize components
    viz_generator = ReportVisualizationGenerator()
    insights_analyzer = AIInsightsAnalyzer()
    explanation_generator = UserFriendlyExplanationGenerator()
    
    # Generate processing summary
    processing_summary = _generate_processing_summary(results)
    
    # Generate AI insights
    ai_insights = {}
    if config.include_ai_explanations:
        ai_insights = insights_analyzer.generate_ai_insights(results)
    
    # Enhance results with user-friendly explanations
    enhanced_results = []
    for result in results:
        enhanced_result = result.copy()
        
        if config.include_ai_explanations and 'ai_explanation' in result:
            # Add user-friendly explanations
            enhanced_result['user_friendly_explanation'] = explanation_generator.generate_explanation(
                'matching_decision', result['ai_explanation']
            )
            
            # Add field-level explanations
            if 'field_results' in result:
                for field_name, field_result in result['field_results'].items():
                    if isinstance(field_result, dict):
                        field_result['user_explanation'] = explanation_generator.generate_explanation(
                            'field_comparison', {**field_result, 'field_name': field_name}
                        )
        
        enhanced_results.append(enhanced_result)
    
    # Generate performance metrics
    performance_metrics = _generate_performance_metrics(results, start_time)
    
    # Generate visualization data
    visualization_data = {}
    if include_visualizations:
        visualization_data = {
            'status_distribution': viz_generator.generate_status_distribution_chart(results),
            'confidence_histogram': viz_generator.generate_confidence_score_histogram(results),
            'method_comparison': viz_generator.generate_method_comparison_chart(results),
            'processing_times': viz_generator.generate_processing_time_chart(performance_metrics),
            'field_mismatches': viz_generator.generate_field_mismatch_analysis(results)
        }
    
    # Generate recommendations
    recommendations = _generate_recommendations(results, ai_insights, performance_metrics)
    
    # Create comprehensive report
    report = EnhancedReconciliationReport(
        report_id=report_id,
        generation_timestamp=datetime.now().isoformat(),
        processing_summary=processing_summary,
        ai_insights=ai_insights,
        detailed_results=enhanced_results,
        performance_metrics=performance_metrics,
        visualization_data=visualization_data,
        recommendations=recommendations,
        export_formats=config.export_formats
    )
    
    generation_time = (time.time() - start_time) * 1000
    logger.info(f"Enhanced report {report_id} generated in {generation_time:.2f}ms")
    
    return asdict(report)


def _generate_processing_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate high-level processing summary"""
    total_trades = len(results)
    
    status_counts = {}
    method_counts = {}
    confidence_sum = 0
    confidence_count = 0
    
    for result in results:
        # Count statuses
        status = result.get('overall_status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count methods
        method = result.get('ai_explanation', {}).get('method_used', 'deterministic')
        method_counts[method] = method_counts.get(method, 0) + 1
        
        # Sum confidence scores
        confidence = result.get('ai_explanation', {}).get('confidence_score')
        if confidence is not None:
            confidence_sum += confidence
            confidence_count += 1
    
    avg_confidence = confidence_sum / confidence_count if confidence_count > 0 else 0
    
    return {
        'total_trades_processed': total_trades,
        'status_breakdown': status_counts,
        'method_breakdown': method_counts,
        'average_confidence_score': avg_confidence,
        'success_rate': (status_counts.get('FULLY_MATCHED', 0) + status_counts.get('PARTIALLY_MATCHED', 0)) / total_trades * 100 if total_trades > 0 else 0
    }


def _generate_performance_metrics(results: List[Dict[str, Any]], start_time: float) -> Dict[str, Any]:
    """Generate performance metrics"""
    processing_times = {}
    
    # Calculate average processing times by method
    method_times = {}
    for result in results:
        method = result.get('ai_explanation', {}).get('method_used', 'deterministic')
        proc_time = result.get('ai_explanation', {}).get('processing_time_ms', 0)
        
        if method not in method_times:
            method_times[method] = []
        method_times[method].append(proc_time)
    
    for method, times in method_times.items():
        if times:
            processing_times[f"{method}_avg_ms"] = sum(times) / len(times)
            processing_times[f"{method}_max_ms"] = max(times)
            processing_times[f"{method}_min_ms"] = min(times)
    
    total_generation_time = (time.time() - start_time) * 1000
    
    return {
        'processing_times': processing_times,
        'report_generation_time_ms': total_generation_time,
        'trades_per_second': len(results) / (total_generation_time / 1000) if total_generation_time > 0 else 0
    }


def _generate_recommendations(results: List[Dict[str, Any]], ai_insights: Dict[str, Any], 
                            performance_metrics: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on analysis"""
    recommendations = []
    
    # Analyze success rates
    total_trades = len(results)
    successful_trades = sum(1 for r in results if r.get('overall_status') in ['FULLY_MATCHED', 'PARTIALLY_MATCHED'])
    success_rate = successful_trades / total_trades * 100 if total_trades > 0 else 0
    
    if success_rate < 80:
        recommendations.append(f"Success rate is {success_rate:.1f}%. Consider reviewing matching thresholds or enabling AI semantic matching.")
    
    # Analyze AI fallback usage
    fallback_insight = ai_insights.get('fallback_usage_pattern', {})
    if fallback_insight.get('fallback_rate', 0) > 10:
        recommendations.append(f"AI fallback rate is {fallback_insight['fallback_rate']:.1f}%. Check AI service health and configuration.")
    
    # Analyze confidence scores
    low_confidence_trades = sum(1 for r in results if r.get('ai_explanation', {}).get('confidence_score', 1) < 0.6)
    if low_confidence_trades > total_trades * 0.2:
        recommendations.append(f"{low_confidence_trades} trades have low confidence scores. Consider manual review or threshold adjustment.")
    
    # Performance recommendations
    avg_processing_time = performance_metrics.get('processing_times', {}).get('llm_avg_ms', 0)
    if avg_processing_time > 5000:  # 5 seconds
        recommendations.append(f"AI processing time is high ({avg_processing_time:.0f}ms). Consider optimizing prompts or using hybrid mode.")
    
    # Field-specific recommendations
    field_mismatches = {}
    for result in results:
        field_results = result.get('field_results', {})
        for field_name, field_result in field_results.items():
            if isinstance(field_result, dict) and field_result.get('status') == 'MISMATCHED':
                field_mismatches[field_name] = field_mismatches.get(field_name, 0) + 1
    
    if field_mismatches:
        most_problematic_field = max(field_mismatches.items(), key=lambda x: x[1])
        if most_problematic_field[1] > total_trades * 0.3:
            recommendations.append(f"Field '{most_problematic_field[0]}' has high mismatch rate ({most_problematic_field[1]} trades). Review field mapping or tolerance settings.")
    
    if not recommendations:
        recommendations.append("System is performing well. Continue monitoring for any changes in data patterns.")
    
    return recommendations