"""AgentCore Policy integration module for fine-grained authorization."""

from .client import PolicyClient
from .policies import (
    TRADE_AMOUNT_LIMIT_POLICY,
    SENIOR_OPERATOR_APPROVAL_POLICY,
    OPERATOR_APPROVAL_POLICY,
    COMPLIANCE_BLOCK_POLICY,
    EMERGENCY_SHUTDOWN_POLICY,
    create_all_policies,
)
from .config import (
    POLICY_MODES,
    set_policy_mode,
    get_policy_engine_config,
)

__all__ = [
    "PolicyClient",
    "TRADE_AMOUNT_LIMIT_POLICY",
    "SENIOR_OPERATOR_APPROVAL_POLICY",
    "OPERATOR_APPROVAL_POLICY",
    "COMPLIANCE_BLOCK_POLICY",
    "EMERGENCY_SHUTDOWN_POLICY",
    "create_all_policies",
    "POLICY_MODES",
    "set_policy_mode",
    "get_policy_engine_config",
]
