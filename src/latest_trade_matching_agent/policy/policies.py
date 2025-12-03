"""Cedar policies for trade matching authorization."""

import os
from .client import policy_client

# Get account and region for policy ARNs
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "123456789012")
GATEWAY_ARN = f"arn:aws:bedrock-agentcore:{REGION}:{ACCOUNT_ID}:gateway/trade-gateway"
HITL_GATEWAY_ARN = f"arn:aws:bedrock-agentcore:{REGION}:{ACCOUNT_ID}:gateway/hitl-gateway"

# Trade amount limit policy - restrict processing to amounts under $100M
TRADE_AMOUNT_LIMIT_POLICY = f'''
permit(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"TradeTarget___store_trade",
  resource == AgentCore::Gateway::"{GATEWAY_ARN}"
)
when {{
  principal.hasTag("role") &&
  ["operator", "admin", "senior_operator"].contains(principal.getTag("role")) &&
  context.input.notional < 100000000
}};
'''

# Senior operator approval policy - can approve high-value matches
SENIOR_OPERATOR_APPROVAL_POLICY = f'''
permit(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"HITLTarget___approve_match",
  resource == AgentCore::Gateway::"{HITL_GATEWAY_ARN}"
)
when {{
  principal.hasTag("role") &&
  principal.getTag("role") == "senior_operator" &&
  context.input.match_score >= 0.70
}};
'''

# Regular operator approval policy - can only approve low-risk matches
OPERATOR_APPROVAL_POLICY = f'''
permit(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"HITLTarget___approve_match",
  resource == AgentCore::Gateway::"{HITL_GATEWAY_ARN}"
)
when {{
  principal.hasTag("role") &&
  principal.getTag("role") == "operator" &&
  context.input.match_score >= 0.85
}};
'''

# Compliance block policy - block restricted counterparties
COMPLIANCE_BLOCK_POLICY = f'''
forbid(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"TradeTarget___store_trade",
  resource == AgentCore::Gateway::"{GATEWAY_ARN}"
)
when {{
  context.input has counterparty &&
  ["RESTRICTED_ENTITY_1", "RESTRICTED_ENTITY_2", "SANCTIONED_CORP"].contains(context.input.counterparty)
}};
'''

# Emergency shutdown policy - block all trade processing (disabled by default)
EMERGENCY_SHUTDOWN_POLICY = f'''
forbid(
  principal,
  action == AgentCore::Action::"TradeTarget___store_trade",
  resource == AgentCore::Gateway::"{GATEWAY_ARN}"
);
'''

# Admin override policy - admins can bypass amount limits
ADMIN_OVERRIDE_POLICY = f'''
permit(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"TradeTarget___store_trade",
  resource == AgentCore::Gateway::"{GATEWAY_ARN}"
)
when {{
  principal.hasTag("role") &&
  principal.getTag("role") == "admin"
}};
'''

# Audit access policy - auditors can only read, not modify
AUDITOR_READ_ONLY_POLICY = f'''
permit(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"AuditTarget___query_audit",
  resource == AgentCore::Gateway::"{GATEWAY_ARN}"
)
when {{
  principal.hasTag("role") &&
  principal.getTag("role") == "auditor"
}};

forbid(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"TradeTarget___store_trade",
  resource == AgentCore::Gateway::"{GATEWAY_ARN}"
)
when {{
  principal.hasTag("role") &&
  principal.getTag("role") == "auditor"
}};
'''

# All policy configurations
POLICY_CONFIGS = {
    "TradeAmountLimit": {
        "name": "TradeAmountLimit",
        "description": "Limit trade processing to amounts under $100M",
        "cedar": TRADE_AMOUNT_LIMIT_POLICY,
        "enabled": True
    },
    "SeniorOperatorApproval": {
        "name": "SeniorOperatorApproval",
        "description": "Senior operators can approve high-value matches (score >= 0.70)",
        "cedar": SENIOR_OPERATOR_APPROVAL_POLICY,
        "enabled": True
    },
    "OperatorApproval": {
        "name": "OperatorApproval",
        "description": "Regular operators can only approve low-risk matches (score >= 0.85)",
        "cedar": OPERATOR_APPROVAL_POLICY,
        "enabled": True
    },
    "ComplianceBlock": {
        "name": "ComplianceBlock",
        "description": "Block trades with restricted counterparties",
        "cedar": COMPLIANCE_BLOCK_POLICY,
        "enabled": True
    },
    "AdminOverride": {
        "name": "AdminOverride",
        "description": "Admins can bypass amount limits",
        "cedar": ADMIN_OVERRIDE_POLICY,
        "enabled": True
    },
    "AuditorReadOnly": {
        "name": "AuditorReadOnly",
        "description": "Auditors can only read audit data",
        "cedar": AUDITOR_READ_ONLY_POLICY,
        "enabled": True
    },
    "EmergencyShutdown": {
        "name": "EmergencyShutdown",
        "description": "Emergency: Block all trade processing",
        "cedar": EMERGENCY_SHUTDOWN_POLICY,
        "enabled": False  # Disabled by default
    }
}


def create_all_policies(
    policy_engine_id: str,
    include_emergency: bool = False
) -> dict[str, dict]:
    """
    Create all policies in the policy engine.
    
    Args:
        policy_engine_id: ID of the policy engine
        include_emergency: Whether to include emergency shutdown policy
    
    Returns:
        Dictionary of created policies
    """
    results = {}
    
    for policy_name, config in POLICY_CONFIGS.items():
        # Skip emergency policy unless explicitly requested
        if policy_name == "EmergencyShutdown" and not include_emergency:
            continue
        
        # Skip disabled policies
        if not config.get("enabled", True):
            continue
        
        result = policy_client.create_policy(
            policy_engine_id=policy_engine_id,
            name=config["name"],
            cedar_statement=config["cedar"],
            description=config["description"]
        )
        results[policy_name] = result
    
    return results


def enable_emergency_shutdown(policy_engine_id: str) -> dict:
    """Enable emergency shutdown policy."""
    config = POLICY_CONFIGS["EmergencyShutdown"]
    return policy_client.create_policy(
        policy_engine_id=policy_engine_id,
        name=config["name"],
        cedar_statement=config["cedar"],
        description=config["description"]
    )


def disable_emergency_shutdown(policy_engine_id: str, policy_id: str) -> dict:
    """Disable emergency shutdown policy by deleting it."""
    return policy_client.delete_policy(
        policy_engine_id=policy_engine_id,
        policy_id=policy_id
    )


def update_restricted_counterparties(
    policy_engine_id: str,
    counterparties: list[str]
) -> dict:
    """
    Update the list of restricted counterparties.
    
    Args:
        policy_engine_id: Policy engine ID
        counterparties: List of restricted counterparty names
    
    Returns:
        Updated policy result
    """
    counterparty_list = ", ".join([f'"{c}"' for c in counterparties])
    
    updated_policy = f'''
forbid(
  principal is AgentCore::OAuthUser,
  action == AgentCore::Action::"TradeTarget___store_trade",
  resource == AgentCore::Gateway::"{GATEWAY_ARN}"
)
when {{
  context.input has counterparty &&
  [{counterparty_list}].contains(context.input.counterparty)
}};
'''
    
    # Delete existing policy first, then create new one
    existing_policies = policy_client.list_policies(policy_engine_id)
    for policy in existing_policies:
        if policy.get("name") == "ComplianceBlock":
            policy_client.delete_policy(policy_engine_id, policy.get("policyId"))
            break
    
    return policy_client.create_policy(
        policy_engine_id=policy_engine_id,
        name="ComplianceBlock",
        cedar_statement=updated_policy,
        description=f"Block trades with restricted counterparties: {', '.join(counterparties)}"
    )
