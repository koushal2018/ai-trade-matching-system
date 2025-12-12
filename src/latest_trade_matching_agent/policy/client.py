"""AgentCore Policy client for Cedar policy management."""

import os
from typing import Optional, Any
import boto3
from botocore.exceptions import ClientError


class PolicyClient:
    """Client for Amazon Bedrock AgentCore Policy."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.account_id = self._get_account_id()
        self.bedrock_agent = boto3.client("bedrock-agent", region_name=region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
    
    def _get_account_id(self) -> str:
        """Get AWS account ID."""
        try:
            sts = boto3.client("sts")
            return sts.get_caller_identity()["Account"]
        except Exception:
            return os.getenv("AWS_ACCOUNT_ID", "123456789012")
    
    def create_or_get_policy_engine(
        self,
        name: str,
        description: str = ""
    ) -> dict:
        """
        Create or get existing policy engine.
        
        Args:
            name: Policy engine name
            description: Description of the policy engine
        
        Returns:
            Policy engine configuration with ARN
        """
        try:
            # Try to create new policy engine
            response = self.bedrock_agent.create_policy_engine(
                name=name,
                description=description
            )
            return {
                "policyEngineId": response.get("policyEngineId"),
                "policyEngineArn": response.get("policyEngineArn"),
                "name": name,
                "status": "CREATED"
            }
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceAlreadyExistsException":
                # Get existing policy engine
                return self.get_policy_engine(name)
            # Return placeholder for development
            return {
                "policyEngineId": f"pe_{name.lower().replace(' ', '_')}",
                "policyEngineArn": f"arn:aws:bedrock-agentcore:{self.region}:{self.account_id}:policy-engine/{name}",
                "name": name,
                "status": "PLACEHOLDER",
                "error": str(e)
            }
    
    def get_policy_engine(self, name: str) -> dict:
        """Get policy engine by name."""
        try:
            response = self.bedrock_agent.list_policy_engines()
            for engine in response.get("policyEngines", []):
                if engine.get("name") == name:
                    return {
                        "policyEngineId": engine.get("policyEngineId"),
                        "policyEngineArn": engine.get("policyEngineArn"),
                        "name": name,
                        "status": "ACTIVE"
                    }
            return {"name": name, "status": "NOT_FOUND"}
        except ClientError as e:
            return {"name": name, "status": "ERROR", "error": str(e)}
    
    def create_policy(
        self,
        policy_engine_id: str,
        name: str,
        cedar_statement: str,
        description: str = "",
        validation_mode: str = "FAIL_ON_ANY_FINDINGS"
    ) -> dict:
        """
        Create a Cedar policy in the policy engine.
        
        Args:
            policy_engine_id: ID of the policy engine
            name: Policy name (must match ^[A-Za-z][A-Za-z0-9_]*$)
            cedar_statement: Cedar policy statement
            description: Policy description
            validation_mode: Validation mode (FAIL_ON_ANY_FINDINGS or WARN)
        
        Returns:
            Policy configuration
        """
        try:
            response = self.bedrock_agent.create_policy(
                policyEngineId=policy_engine_id,
                name=name,
                definition={
                    "cedar": {
                        "statement": cedar_statement
                    }
                },
                description=description,
                validationMode=validation_mode
            )
            return {
                "policyId": response.get("policyId"),
                "name": name,
                "status": "CREATED"
            }
        except ClientError as e:
            return {
                "policyId": f"policy_{name.lower()}",
                "name": name,
                "status": "PLACEHOLDER",
                "error": str(e)
            }
    
    def delete_policy(
        self,
        policy_engine_id: str,
        policy_id: str
    ) -> dict:
        """Delete a policy from the policy engine."""
        try:
            self.bedrock_agent.delete_policy(
                policyEngineId=policy_engine_id,
                policyId=policy_id
            )
            return {"policyId": policy_id, "status": "DELETED"}
        except ClientError as e:
            return {"policyId": policy_id, "status": "ERROR", "error": str(e)}
    
    def list_policies(self, policy_engine_id: str) -> list[dict]:
        """List all policies in a policy engine."""
        try:
            response = self.bedrock_agent.list_policies(
                policyEngineId=policy_engine_id
            )
            return response.get("policies", [])
        except ClientError:
            return []
    
    def update_gateway_policy_engine(
        self,
        gateway_id: str,
        policy_engine_arn: str,
        mode: str = "ENFORCE"
    ) -> dict:
        """
        Attach policy engine to a Gateway.
        
        Args:
            gateway_id: Gateway identifier
            policy_engine_arn: Policy engine ARN
            mode: Enforcement mode (ENFORCE or LOG_ONLY)
        
        Returns:
            Update result
        """
        try:
            response = self.bedrock_agent.update_gateway(
                gatewayId=gateway_id,
                policyEngineConfig={
                    "policyEngineArn": policy_engine_arn,
                    "mode": mode
                }
            )
            return {
                "gatewayId": gateway_id,
                "policyEngineArn": policy_engine_arn,
                "mode": mode,
                "status": "ATTACHED"
            }
        except ClientError as e:
            return {
                "gatewayId": gateway_id,
                "status": "ERROR",
                "error": str(e)
            }
    
    def create_policy_denial_alarm(
        self,
        alarm_name: str,
        threshold: int,
        sns_topic_arn: str,
        namespace: str = "TradeMatching/Policy"
    ) -> dict:
        """
        Create alarm for policy denials.
        
        Args:
            alarm_name: Name of the alarm
            threshold: Number of denials to trigger alarm
            sns_topic_arn: SNS topic for notifications
            namespace: CloudWatch namespace
        
        Returns:
            Alarm configuration
        """
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                MetricName="PolicyDenied",
                Namespace=namespace,
                Threshold=threshold,
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=3,
                Period=60,
                Statistic="Sum",
                AlarmActions=[sns_topic_arn]
            )
            return {"alarmName": alarm_name, "status": "CREATED"}
        except ClientError as e:
            return {"alarmName": alarm_name, "status": "ERROR", "error": str(e)}


# Global client instance
policy_client = PolicyClient()
