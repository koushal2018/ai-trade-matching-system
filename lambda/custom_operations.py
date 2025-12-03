"""
Custom Operations Lambda Function for AgentCore Gateway

This Lambda function provides custom business logic operations that can be
invoked by agents through the AgentCore Gateway MCP interface.

Operations:
- validate_trade: Validate trade data against business rules
- compute_match_score: Compute match score between two trades
- classify_exception: Classify exception severity and routing
- apply_tolerances: Apply matching tolerances to trade fields
- generate_trade_id: Generate unique trade identifiers
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


def lambda_handler(event, context):
    """
    Main Lambda handler for custom operations.
    
    Args:
        event: Lambda event containing operation and parameters
        context: Lambda context
    
    Returns:
        dict: Operation result with statusCode and body
    """
    try:
        # Parse operation from event
        operation = event.get('operation')
        
        if not operation:
            return error_response(400, "Missing 'operation' parameter")
        
        # Route to appropriate handler
        handlers = {
            'validate_trade': validate_trade,
            'compute_match_score': compute_match_score,
            'classify_exception': classify_exception,
            'apply_tolerances': apply_tolerances,
            'generate_trade_id': generate_trade_id
        }
        
        handler = handlers.get(operation)
        if not handler:
            return error_response(400, f"Unknown operation: {operation}")
        
        # Execute handler
        result = handler(event)
        return success_response(result)
        
    except Exception as e:
        return error_response(500, f"Internal error: {str(e)}")


def validate_trade(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate trade data against business rules.
    
    Args:
        event: Event containing trade_data
    
    Returns:
        dict: Validation result with valid flag and errors list
    """
    trade_data = event.get('trade_data', {})
    errors = []
    
    # Required fields
    required_fields = [
        'Trade_ID', 'TRADE_SOURCE', 'trade_date', 
        'notional', 'currency', 'counterparty', 'product_type'
    ]
    
    for field in required_fields:
        if field not in trade_data or not trade_data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate TRADE_SOURCE
    if trade_data.get('TRADE_SOURCE') not in ['BANK', 'COUNTERPARTY']:
        errors.append("TRADE_SOURCE must be 'BANK' or 'COUNTERPARTY'")
    
    # Validate notional is positive
    try:
        notional = float(trade_data.get('notional', 0))
        if notional <= 0:
            errors.append("Notional must be positive")
    except (ValueError, TypeError):
        errors.append("Notional must be a valid number")
    
    # Validate currency code (3 characters)
    currency = trade_data.get('currency', '')
    if len(currency) != 3:
        errors.append("Currency must be a 3-character ISO code")
    
    # Validate date format (YYYY-MM-DD)
    trade_date = trade_data.get('trade_date', '')
    try:
        datetime.strptime(trade_date, '%Y-%m-%d')
    except ValueError:
        errors.append("trade_date must be in YYYY-MM-DD format")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'trade_id': trade_data.get('Trade_ID')
    }


def compute_match_score(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute match score between bank and counterparty trades.
    
    Args:
        event: Event containing bank_trade and counterparty_trade
    
    Returns:
        dict: Match score, classification, and field differences
    """
    bank_trade = event.get('bank_trade', {})
    cp_trade = event.get('counterparty_trade', {})
    
    if not bank_trade or not cp_trade:
        return {
            'match_score': 0.0,
            'classification': 'DATA_ERROR',
            'reason': 'Missing trade data'
        }
    
    # Field weights for scoring
    field_weights = {
        'Trade_ID': 0.30,
        'notional': 0.25,
        'trade_date': 0.20,
        'counterparty': 0.15,
        'currency': 0.10
    }
    
    score = 0.0
    differences = []
    
    # Compare Trade_ID (exact match)
    if bank_trade.get('Trade_ID') == cp_trade.get('Trade_ID'):
        score += field_weights['Trade_ID']
    else:
        differences.append({
            'field': 'Trade_ID',
            'bank_value': bank_trade.get('Trade_ID'),
            'cp_value': cp_trade.get('Trade_ID'),
            'match': False
        })
    
    # Compare notional (±0.01% tolerance)
    bank_notional = float(bank_trade.get('notional', 0))
    cp_notional = float(cp_trade.get('notional', 0))
    notional_diff = abs(bank_notional - cp_notional) / bank_notional if bank_notional > 0 else 1.0
    
    if notional_diff <= 0.0001:  # 0.01% tolerance
        score += field_weights['notional']
    else:
        differences.append({
            'field': 'notional',
            'bank_value': bank_notional,
            'cp_value': cp_notional,
            'difference_pct': notional_diff * 100,
            'match': False
        })
    
    # Compare trade_date (±1 day tolerance)
    try:
        bank_date = datetime.strptime(bank_trade.get('trade_date', ''), '%Y-%m-%d')
        cp_date = datetime.strptime(cp_trade.get('trade_date', ''), '%Y-%m-%d')
        date_diff_days = abs((bank_date - cp_date).days)
        
        if date_diff_days <= 1:
            score += field_weights['trade_date']
        else:
            differences.append({
                'field': 'trade_date',
                'bank_value': bank_trade.get('trade_date'),
                'cp_value': cp_trade.get('trade_date'),
                'difference_days': date_diff_days,
                'match': False
            })
    except ValueError:
        differences.append({
            'field': 'trade_date',
            'bank_value': bank_trade.get('trade_date'),
            'cp_value': cp_trade.get('trade_date'),
            'match': False,
            'error': 'Invalid date format'
        })
    
    # Compare counterparty (fuzzy match)
    bank_cp = bank_trade.get('counterparty', '').lower()
    cp_cp = cp_trade.get('counterparty', '').lower()
    
    if bank_cp == cp_cp:
        score += field_weights['counterparty']
    elif bank_cp in cp_cp or cp_cp in bank_cp:
        score += field_weights['counterparty'] * 0.8  # Partial match
    else:
        differences.append({
            'field': 'counterparty',
            'bank_value': bank_trade.get('counterparty'),
            'cp_value': cp_trade.get('counterparty'),
            'match': False
        })
    
    # Compare currency (exact match)
    if bank_trade.get('currency') == cp_trade.get('currency'):
        score += field_weights['currency']
    else:
        differences.append({
            'field': 'currency',
            'bank_value': bank_trade.get('currency'),
            'cp_value': cp_trade.get('currency'),
            'match': False
        })
    
    # Classify based on score
    if score >= 0.85:
        classification = 'MATCHED'
        decision_status = 'AUTO_MATCH'
    elif score >= 0.70:
        classification = 'PROBABLE_MATCH'
        decision_status = 'ESCALATE'
    else:
        classification = 'BREAK'
        decision_status = 'EXCEPTION'
    
    return {
        'match_score': round(score, 4),
        'classification': classification,
        'decision_status': decision_status,
        'differences': differences,
        'requires_hitl': decision_status == 'ESCALATE'
    }


def classify_exception(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify exception severity and determine routing.
    
    Args:
        event: Event containing exception_data
    
    Returns:
        dict: Severity, routing, priority, and SLA
    """
    exception_data = event.get('exception_data', {})
    reason_codes = exception_data.get('reason_codes', [])
    match_score = exception_data.get('match_score', 0.0)
    
    # Base severity scores for reason codes
    severity_scores = {
        'NOTIONAL_MISMATCH': 0.8,
        'COUNTERPARTY_MISMATCH': 0.9,
        'DUPLICATE_TRADE_ID': 0.85,
        'DATE_MISMATCH': 0.7,
        'CURRENCY_MISMATCH': 0.75,
        'MISSING_REQUIRED_FIELD': 0.6,
        'OCR_QUALITY_LOW': 0.5,
        'CONFIDENCE_TOO_LOW': 0.35
    }
    
    # Compute max severity
    max_severity = 0.0
    for code in reason_codes:
        max_severity = max(max_severity, severity_scores.get(code, 0.5))
    
    # Adjust severity based on match score
    if match_score < 0.5:
        max_severity = max(max_severity, 0.7)
    
    # Determine severity level
    if max_severity >= 0.8:
        severity = 'CRITICAL'
        priority = 1
        sla_hours = 2
    elif max_severity >= 0.6:
        severity = 'HIGH'
        priority = 2
        sla_hours = 4
    elif max_severity >= 0.3:
        severity = 'MEDIUM'
        priority = 3
        sla_hours = 24
    else:
        severity = 'LOW'
        priority = 4
        sla_hours = 72
    
    # Determine routing
    if max_severity >= 0.9:
        routing = 'SENIOR_OPS'
    elif max_severity >= 0.7:
        routing = 'OPS_DESK'
    elif max_severity >= 0.5:
        routing = 'OPS_DESK'
    else:
        routing = 'AUTO_RESOLVE'
    
    return {
        'severity': severity,
        'severity_score': round(max_severity, 4),
        'routing': routing,
        'priority': priority,
        'sla_hours': sla_hours,
        'classification': 'OPERATIONAL_ISSUE' if 'MISMATCH' in str(reason_codes) else 'DATA_QUALITY_ISSUE'
    }


def apply_tolerances(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply matching tolerances to trade fields.
    
    Args:
        event: Event containing field_name, value1, value2
    
    Returns:
        dict: Whether values match within tolerance
    """
    field_name = event.get('field_name')
    value1 = event.get('value1')
    value2 = event.get('value2')
    
    if field_name == 'notional':
        # ±0.01% tolerance
        try:
            v1 = float(value1)
            v2 = float(value2)
            diff_pct = abs(v1 - v2) / v1 if v1 > 0 else 1.0
            within_tolerance = diff_pct <= 0.0001
            
            return {
                'field': field_name,
                'within_tolerance': within_tolerance,
                'difference_pct': round(diff_pct * 100, 4),
                'tolerance_pct': 0.01
            }
        except (ValueError, TypeError):
            return {
                'field': field_name,
                'within_tolerance': False,
                'error': 'Invalid numeric values'
            }
    
    elif field_name == 'trade_date':
        # ±1 business day tolerance
        try:
            date1 = datetime.strptime(value1, '%Y-%m-%d')
            date2 = datetime.strptime(value2, '%Y-%m-%d')
            diff_days = abs((date1 - date2).days)
            within_tolerance = diff_days <= 1
            
            return {
                'field': field_name,
                'within_tolerance': within_tolerance,
                'difference_days': diff_days,
                'tolerance_days': 1
            }
        except ValueError:
            return {
                'field': field_name,
                'within_tolerance': False,
                'error': 'Invalid date format'
            }
    
    else:
        # Exact match for other fields
        return {
            'field': field_name,
            'within_tolerance': value1 == value2,
            'exact_match_required': True
        }


def generate_trade_id(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate unique trade identifier.
    
    Args:
        event: Event containing optional prefix
    
    Returns:
        dict: Generated trade_id
    """
    prefix = event.get('prefix', 'TRD')
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    
    # Generate unique ID
    trade_id = f"{prefix}{timestamp}"
    
    return {
        'trade_id': trade_id,
        'timestamp': timestamp
    }


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create success response."""
    return {
        'statusCode': 200,
        'body': json.dumps(data, default=str)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create error response."""
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'error': message
        })
    }
