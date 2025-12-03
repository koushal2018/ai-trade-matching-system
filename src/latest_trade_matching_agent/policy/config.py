"""Policy configuration for trade matching system."""

import os
from typing import Optional
from .client import policy_client

# Policy enforcement modes by environment
POLICY_MODES = {
    "development": "LOG_ONLY",   # Log decisions without enforcing
    "staging": "LOG_ONLY",       # Test policies before production
    "production": "ENFORCE"      # Full enforcement
}

# Policy log configuration
POLICY_LOG_CONFIG = {
    "log_group": "/aws/agentcore/policy-decisions",
    "metrics_namespace": "TradeMatching/Policy",
    "metrics": [
        "PolicyDecisions",      # Total decisions
        "PolicyAllowed",        # Allowed requests
        "PolicyDenied",         # Denied requests
        "PolicyEvaluationTime"  # Evaluation latency
    ]
}


def get_current_environment() -> str:
    """Get current deployment environment."""
    return os.getenv("ENVIRONMENT", "development")


def get_policy_mode() -> str:
    """Get policy enforcement mode for current environment."""
    env = get_current_environment()
    return POLICY_MODES.get(env, "LOG_ONLY")


def set_policy_mode(
    gateway_id: str,
    policy_engine_arn: str,
    environment: Optional[str] = None
) -> dict:
    """
    Set policy enforcement mode based on environment.
    
    Args:
        gateway_id: Gateway identifier
        policy_engine_arn: Policy engine ARN
        environment: Override environment (uses current if not specified)
    
    Returns:
        Update result
    """
    env = environment or get_current_environment()
    mode = POLICY_MODES.get(env, "LOG_ONLY")
    
    return policy_client.update_gateway_policy_engine(
        gateway_id=gateway_id,
        policy_engine_arn=policy_engine_arn,
        mode=mode
    )


def get_policy_engine_config() -> dict:
    """
    Get policy engine configuration for trade matching.
    
    Returns:
        Policy engine configuration
    """
    return {
        "name": "TradeMatchingPolicyEngine",
        "description": "Policy engine for trade matching agent authorization",
        "enforcement_mode": get_policy_mode(),
        "log_config": POLICY_LOG_CONFIG,
        "policies": [
            {
                "name": "TradeAmountLimit",
                "description": "Limit trade processing to amounts under $100M",
                "enabled": True
            },
            {
                "name": "SeniorOperatorApproval",
                "description": "Senior operators can approve high-value matches",
                "enabled": True
            },
            {
                "name": "OperatorApproval",
                "description": "Regular operators approve low-risk matches only",
                "enabled": True
            },
            {
                "name": "ComplianceBlock",
                "description": "Block restricted counterparties",
                "enabled": True
            },
            {
                "name": "AdminOverride",
                "description": "Admins can bypass amount limits",
                "enabled": True
            },
            {
                "name": "AuditorReadOnly",
                "description": "Auditors can only read audit data",
                "enabled": True
            },
            {
                "name": "EmergencyShutdown",
                "description": "Emergency: Block all trade processing",
                "enabled": False
            }
        ]
    }


def create_policy_alarms(sns_topic_arn: str) -> list[dict]:
    """
    Create CloudWatch alarms for policy monitoring.
    
    Args:
        sns_topic_arn: SNS topic ARN for notifications
    
    Returns:
        List of created alarms
    """
    alarms = []
    
    # High denial rate alarm
    alarms.append(
        policy_client.create_policy_denial_alarm(
            alarm_name="HighPolicyDenialRate",
            threshold=10,  # Alert if >10 denials per minute
            sns_topic_arn=sns_topic_arn
        )
    )
    
    return alarms


def get_policy_dashboard_config() -> dict:
    """
    Get CloudWatch dashboard configuration for policy monitoring.
    
    Returns:
        Dashboard widget configuration
    """
    return {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "title": "Policy Decisions",
                    "metrics": [
                        ["TradeMatching/Policy", "PolicyDecisions"],
                        ["TradeMatching/Policy", "PolicyAllowed"],
                        ["TradeMatching/Policy", "PolicyDenied"]
                    ],
                    "period": 60,
                    "stat": "Sum"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "title": "Policy Evaluation Latency",
                    "metrics": [
                        ["TradeMatching/Policy", "PolicyEvaluationTime"]
                    ],
                    "period": 60,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "title": "Denial Rate",
                    "metrics": [
                        [{
                            "expression": "m2/m1*100",
                            "label": "Denial Rate %",
                            "id": "e1"
                        }],
                        ["TradeMatching/Policy", "PolicyDecisions", {"id": "m1", "visible": False}],
                        ["TradeMatching/Policy", "PolicyDenied", {"id": "m2", "visible": False}]
                    ],
                    "period": 300,
                    "stat": "Sum"
                }
            }
        ]
    }
