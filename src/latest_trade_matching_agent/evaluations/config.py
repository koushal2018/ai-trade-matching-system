"""Evaluation configuration for trade matching system."""

from typing import Optional
from .client import evaluations_client
from .evaluators import BUILTIN_EVALUATORS

# Evaluation metrics configuration
EVALUATION_METRICS = {
    "TradeExtractionScore": {
        "namespace": "TradeMatching/Evaluations",
        "dimensions": ["AgentId", "EvaluatorId"],
        "alarm_threshold": 3.5,
        "description": "Average trade extraction quality score"
    },
    "MatchingQualityScore": {
        "namespace": "TradeMatching/Evaluations",
        "dimensions": ["AgentId", "EvaluatorId"],
        "alarm_threshold": 4.0,
        "description": "Average matching decision quality score"
    },
    "OCRQualityScore": {
        "namespace": "TradeMatching/Evaluations",
        "dimensions": ["AgentId", "EvaluatorId"],
        "alarm_threshold": 3.5,
        "description": "Average OCR extraction quality score"
    },
    "ExceptionHandlingScore": {
        "namespace": "TradeMatching/Evaluations",
        "dimensions": ["AgentId", "EvaluatorId"],
        "alarm_threshold": 3.5,
        "description": "Average exception handling quality score"
    }
}


def create_online_evaluation_config(
    trade_extraction_evaluator_arn: str,
    matching_quality_evaluator_arn: str,
    log_group: str = "/aws/agentcore/trade-matching",
    sampling_rate: float = 0.1,
    metrics_namespace: str = "TradeMatching/Evaluations",
    output_log_group: str = "/aws/agentcore/evaluations"
) -> dict:
    """
    Create online evaluation configuration for continuous monitoring.
    
    Args:
        trade_extraction_evaluator_arn: ARN of trade extraction evaluator
        matching_quality_evaluator_arn: ARN of matching quality evaluator
        log_group: CloudWatch log group for agent traces
        sampling_rate: Fraction of traffic to evaluate (0.0-1.0)
        metrics_namespace: CloudWatch metrics namespace
        output_log_group: Log group for evaluation results
    
    Returns:
        Online evaluation configuration
    """
    return evaluations_client.create_online_evaluation(
        name="TradeMatchingOnlineEval",
        description="Continuous quality monitoring for trade matching agents",
        data_source={
            "cloudwatch_log_group": log_group,
            "sampling_rate": sampling_rate
        },
        evaluators=[
            {
                "evaluator_arn": trade_extraction_evaluator_arn,
                "target_agents": ["pdf_adapter_agent", "trade_extraction_agent"]
            },
            {
                "evaluator_arn": matching_quality_evaluator_arn,
                "target_agents": ["trade_matching_agent"]
            },
            {
                "evaluator_arn": BUILTIN_EVALUATORS["accuracy"],
                "target_agents": ["*"]
            }
        ],
        output_config={
            "cloudwatch_metrics_namespace": metrics_namespace,
            "cloudwatch_log_group": output_log_group
        }
    )


def create_evaluation_alarms(
    sns_topic_arn: str,
    metrics_namespace: str = "TradeMatching/Evaluations"
) -> list[dict]:
    """
    Create CloudWatch alarms for evaluation metrics.
    
    Args:
        sns_topic_arn: SNS topic ARN for alarm notifications
        metrics_namespace: CloudWatch metrics namespace
    
    Returns:
        List of created alarm configurations
    """
    alarms = []
    
    for metric_name, config in EVALUATION_METRICS.items():
        alarm = evaluations_client.create_evaluation_alarm(
            alarm_name=f"LowQuality_{metric_name}",
            metric_name=metric_name,
            namespace=metrics_namespace,
            threshold=config["alarm_threshold"],
            alarm_action_arn=sns_topic_arn
        )
        alarms.append(alarm)
    
    return alarms


def get_evaluation_dashboard_config() -> dict:
    """
    Get CloudWatch dashboard configuration for evaluations.
    
    Returns:
        Dashboard widget configuration
    """
    return {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "title": "Trade Extraction Quality",
                    "metrics": [
                        ["TradeMatching/Evaluations", "TradeExtractionScore"]
                    ],
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "title": "Matching Quality",
                    "metrics": [
                        ["TradeMatching/Evaluations", "MatchingQualityScore"]
                    ],
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "title": "OCR Quality",
                    "metrics": [
                        ["TradeMatching/Evaluations", "OCRQualityScore"]
                    ],
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "title": "Exception Handling Quality",
                    "metrics": [
                        ["TradeMatching/Evaluations", "ExceptionHandlingScore"]
                    ],
                    "period": 300,
                    "stat": "Average"
                }
            }
        ]
    }
