"""
AgentCore Policy Integration for Trade Extraction Agent

This integrates with your existing policy engine to enforce:
- Data integrity validation (TRADE_SOURCE matches table)
- Trade amount limits and approval workflows
- Source classification validation
- Compliance controls
"""

from src.latest_trade_matching_agent.policy.trade_matching_policies import PolicyEngine
import json
from typing import Dict, Any

class TradeExtractionPolicyEnforcement:
    """Policy enforcement for trade extraction operations."""
    
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.gateway_url = "https://gateway.bedrock-agentcore.us-east-1.amazonaws.com/trade-extraction"
    
    def validate_extraction_request(self, 
                                  user_token: str,
                                  trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate trade extraction request against policies.
        
        Args:
            user_token: JWT token for the requesting user
            trade_data: Extracted trade data to validate
            
        Returns:
            Policy decision with allow/deny and reasoning
        """
        try:
            # Create policy test case for this extraction
            test_case = {
                'name': f'Trade extraction validation for {trade_data.get("Trade_ID", "unknown")}',
                'token': user_token,
                'tool': 'TradeExtractionTarget___extract_trade_data',
                'arguments': {
                    'trade_source': trade_data.get('TRADE_SOURCE'),
                    'notional': trade_data.get('notional', 0),
                    'counterparty': trade_data.get('counterparty', ''),
                    'document_id': trade_data.get('document_id', '')
                },
                'expected_result': 'ALLOW'  # We'll check the actual result
            }
            
            # Test against policies
            results = self.policy_engine.test_policy_decisions(
                self.gateway_url, 
                [test_case]
            )
            
            if results and len(results) > 0:
                result = results[0]
                return {
                    "allowed": result.get('passed', False),
                    "decision": result.get('actual', 'DENY'),
                    "reasoning": result.get('reasoning', 'Policy evaluation failed'),
                    "policy_decision": result.get('policy_decision', {})
                }
            else:
                return {
                    "allowed": False,
                    "decision": "DENY",
                    "reasoning": "Policy evaluation failed - no results returned"
                }
                
        except Exception as e:
            return {
                "allowed": False,
                "decision": "DENY",
                "reasoning": f"Policy validation error: {str(e)}"
            }
    
    def validate_data_integrity(self, trade_data: Dict[str, Any], target_table: str) -> Dict[str, Any]:
        """
        Validate data integrity rules from your policy engine.
        
        This enforces the critical business rule that TRADE_SOURCE must match the target table.
        """
        trade_source = trade_data.get('TRADE_SOURCE', '')
        
        # Apply data integrity policy
        if trade_source == 'BANK' and target_table == 'BankTradeData':
            return {"valid": True, "reason": "BANK trade correctly routed to BankTradeData"}
        elif trade_source == 'COUNTERPARTY' and target_table == 'CounterpartyTradeData':
            return {"valid": True, "reason": "COUNTERPARTY trade correctly routed to CounterpartyTradeData"}
        else:
            return {
                "valid": False, 
                "reason": f"Data integrity violation: {trade_source} trade cannot be stored in {target_table}"
            }
    
    def check_trade_amount_limits(self, 
                                user_role: str, 
                                notional_amount: float) -> Dict[str, Any]:
        """
        Check trade amount limits based on user role and your policy rules.
        
        From your policy engine:
        - Standard operators: < $100M
        - Senior operators: < $1B  
        - Admins: No limit
        """
        if user_role == "admin":
            return {"approved": True, "reason": "Admin override - no amount limit"}
        elif user_role == "senior_operator" and notional_amount < 1_000_000_000:
            return {"approved": True, "reason": "Senior operator approved for amount < $1B"}
        elif user_role == "operator" and notional_amount < 100_000_000:
            return {"approved": True, "reason": "Standard operator approved for amount < $100M"}
        else:
            return {
                "approved": False, 
                "reason": f"Amount ${notional_amount:,.0f} exceeds limit for role {user_role}"
            }

# Enhanced tool with policy enforcement
@tool
def validate_trade_extraction_with_policy(trade_data: dict, 
                                        target_table: str,
                                        user_token: str = "",
                                        user_role: str = "operator") -> str:
    """
    Validate trade extraction against AgentCore policies before storing.
    
    This integrates with your existing policy engine to enforce:
    - Data integrity rules
    - Trade amount limits  
    - Source classification validation
    - User authorization
    
    Args:
        trade_data: Extracted trade data
        target_table: Target DynamoDB table
        user_token: JWT token for authorization
        user_role: User role (operator, senior_operator, admin)
        
    Returns:
        JSON string with validation results
    """
    policy_enforcer = TradeExtractionPolicyEnforcement()
    
    try:
        # 1. Validate data integrity
        integrity_check = policy_enforcer.validate_data_integrity(trade_data, target_table)
        if not integrity_check["valid"]:
            return json.dumps({
                "success": False,
                "validation_failed": "data_integrity",
                "reason": integrity_check["reason"],
                "policy_enforced": True
            })
        
        # 2. Check trade amount limits
        notional = float(trade_data.get('notional', 0))
        amount_check = policy_enforcer.check_trade_amount_limits(user_role, notional)
        if not amount_check["approved"]:
            return json.dumps({
                "success": False,
                "validation_failed": "amount_limit",
                "reason": amount_check["reason"],
                "requires_escalation": True,
                "policy_enforced": True
            })
        
        # 3. Validate against full policy engine (if token provided)
        if user_token:
            policy_result = policy_enforcer.validate_extraction_request(user_token, trade_data)
            if not policy_result["allowed"]:
                return json.dumps({
                    "success": False,
                    "validation_failed": "policy_denied",
                    "reason": policy_result["reasoning"],
                    "policy_decision": policy_result["policy_decision"],
                    "policy_enforced": True
                })
        
        # All validations passed
        return json.dumps({
            "success": True,
            "validation_passed": True,
            "data_integrity": "valid",
            "amount_approved": True,
            "policy_compliant": True,
            "target_table": target_table,
            "trade_source": trade_data.get('TRADE_SOURCE')
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "validation_failed": "system_error",
            "reason": f"Policy validation error: {str(e)}",
            "policy_enforced": False
        })

# Integration example for your agent
POLICY_INTEGRATION_EXAMPLE = """
# Before storing trade data, validate against policies:

validation_result = validate_trade_extraction_with_policy(
    trade_data=extracted_trade_data,
    target_table="BankTradeData",
    user_token=context.get("user_token", ""),
    user_role=context.get("user_role", "operator")
)

# Parse the validation result
validation = json.loads(validation_result)

if validation["success"]:
    # Proceed with storing the trade data
    store_result = use_dynamodb_gateway("PutItem", {
        "TableName": validation["target_table"],
        "Item": trade_data_dynamodb_format
    })
else:
    # Handle policy violation
    if validation.get("requires_escalation"):
        # Route to senior operator or admin for approval
        escalate_for_approval(trade_data, validation["reason"])
    else:
        # Log policy violation and reject
        log_policy_violation(trade_data, validation["reason"])
"""