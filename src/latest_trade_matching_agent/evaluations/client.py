"""AgentCore Evaluations client for quality assessment."""

import os
import json
from datetime import datetime
from typing import Optional, Any
import boto3
from botocore.exceptions import ClientError


class EvaluationsClient:
    """Client for Amazon Bedrock AgentCore Evaluations."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.bedrock_agent = boto3.client("bedrock-agent", region_name=region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
    
    def create_custom_evaluator(
        self,
        name: str,
        description: str,
        evaluation_criteria: str,
        scoring_schema: dict[str, Any],
        model_id: str = "anthropic.claude-sonnet-4-20250514-v1:0"
    ) -> dict:
        """
        Create a custom evaluator for agent assessment.
        
        Args:
            name: Evaluator name
            description: Description of what the evaluator assesses
            evaluation_criteria: Detailed criteria for evaluation
            scoring_schema: JSON schema for scoring (min, max, type)
            model_id: Bedrock model ID for LLM-as-Judge
        
        Returns:
            Evaluator configuration with ARN
        """
        try:
            # Note: Actual API may differ - this is based on documentation
            response = self.bedrock_agent.create_evaluator(
                name=name,
                description=description,
                evaluatorConfig={
                    "llmAsJudge": {
                        "modelId": model_id,
                        "evaluationCriteria": evaluation_criteria,
                        "scoringSchema": scoring_schema
                    }
                }
            )
            return {
                "evaluatorId": response.get("evaluatorId"),
                "evaluatorArn": response.get("evaluatorArn"),
                "name": name,
                "status": "CREATED"
            }
        except ClientError as e:
            # Return placeholder for development
            return {
                "evaluatorId": f"eval_{name.lower()}",
                "evaluatorArn": f"arn:aws:bedrock-agentcore:{self.region}:evaluator/{name}",
                "name": name,
                "status": "PLACEHOLDER",
                "error": str(e)
            }
    
    def create_online_evaluation(
        self,
        name: str,
        description: str,
        data_source: dict[str, Any],
        evaluators: list[dict],
        output_config: dict[str, str]
    ) -> dict:
        """
        Create online evaluation configuration for continuous monitoring.
        
        Args:
            name: Evaluation configuration name
            description: Description of the evaluation
            data_source: CloudWatch log group and sampling config
            evaluators: List of evaluator configurations
            output_config: Output destination configuration
        
        Returns:
            Online evaluation configuration
        """
        try:
            response = self.bedrock_agent.create_evaluation_configuration(
                name=name,
                description=description,
                evaluationType="ONLINE",
                dataSource={
                    "cloudWatchLogs": {
                        "logGroupName": data_source.get("cloudwatch_log_group"),
                        "samplingRate": data_source.get("sampling_rate", 0.1)
                    }
                },
                evaluators=[
                    {
                        "evaluatorArn": e.get("evaluator_arn"),
                        "targetAgents": e.get("target_agents", ["*"])
                    }
                    for e in evaluators
                ],
                outputConfig={
                    "cloudWatchMetrics": {
                        "namespace": output_config.get("cloudwatch_metrics_namespace")
                    },
                    "cloudWatchLogs": {
                        "logGroupName": output_config.get("cloudwatch_log_group")
                    }
                }
            )
            return {
                "configurationId": response.get("evaluationConfigurationId"),
                "name": name,
                "status": "CREATED"
            }
        except ClientError as e:
            return {
                "configurationId": f"config_{name.lower()}",
                "name": name,
                "status": "PLACEHOLDER",
                "error": str(e)
            }
    
    def run_on_demand_evaluation(
        self,
        evaluator_arn: str,
        traces: list[dict],
        session_id: Optional[str] = None
    ) -> dict:
        """
        Run on-demand evaluation on specific traces.
        
        Args:
            evaluator_arn: ARN of the evaluator to use
            traces: List of agent traces to evaluate
            session_id: Optional session identifier
        
        Returns:
            Evaluation results with scores
        """
        session_id = session_id or f"eval_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        try:
            response = self.bedrock_agent.evaluate(
                evaluatorArn=evaluator_arn,
                sessionId=session_id,
                traces=traces
            )
            return {
                "sessionId": session_id,
                "results": response.get("evaluationResults", []),
                "status": "COMPLETED"
            }
        except ClientError as e:
            return {
                "sessionId": session_id,
                "results": [],
                "status": "FAILED",
                "error": str(e)
            }
    
    def create_evaluation_alarm(
        self,
        alarm_name: str,
        metric_name: str,
        namespace: str,
        threshold: float,
        alarm_action_arn: str,
        dimensions: Optional[list[dict]] = None
    ) -> dict:
        """
        Create CloudWatch alarm for evaluation metrics.
        
        Args:
            alarm_name: Name of the alarm
            metric_name: Metric to monitor
            namespace: CloudWatch namespace
            threshold: Alarm threshold
            alarm_action_arn: SNS topic ARN for notifications
            dimensions: Optional metric dimensions
        
        Returns:
            Alarm configuration
        """
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                MetricName=metric_name,
                Namespace=namespace,
                Threshold=threshold,
                ComparisonOperator="LessThanThreshold",
                EvaluationPeriods=3,
                Period=300,
                Statistic="Average",
                AlarmActions=[alarm_action_arn],
                Dimensions=dimensions or []
            )
            return {"alarmName": alarm_name, "status": "CREATED"}
        except ClientError as e:
            return {"alarmName": alarm_name, "status": "FAILED", "error": str(e)}


# Global client instance
evaluations_client = EvaluationsClient()
