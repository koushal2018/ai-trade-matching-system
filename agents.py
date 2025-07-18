import json
import uuid
import boto3
import logging
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher

from strands import Agent, tool
from models import (
    Trade, TradeMatch, FieldComparisonResult, ReconciliationResult,
    MatcherConfig, ReconcilerConfig, ReportConfig
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Helper for DynamoDB JSON serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


@tool
def fetch_unmatched_trades(source: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch unmatched trades from the specified source (BANK or COUNTERPARTY).
    
    Args:
        source (str): The source to fetch trades from ('BANK' or 'COUNTERPARTY')
        limit (int): Maximum number of trades to fetch
        
    Returns:
        List[Dict[str, Any]]: List of unmatched trade records
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('BankTradeData' if source == 'BANK' else 'CounterpartyTradeData')
    
    response = table.scan(
        FilterExpression="matched_status = :status",
        ExpressionAttributeValues={":status": "PENDING"},
        Limit=limit
    )
    
    trades = response.get('Items', [])
    logger.info(f"Fetched {len(trades)} unmatched trades from {source}")
    return trades


@tool
def find_potential_matches(trade: Dict[str, Any], opposite_source: str) -> List[Dict[str, Any]]:
    """
    Find potential matches for a trade in the opposite source.
    
    Args:
        trade (Dict[str, Any]): The trade to find matches for
        opposite_source (str): The source to search in ('BANK' or 'COUNTERPARTY')
        
    Returns:
        List[Dict[str, Any]]: List of potential matching trades
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('BankTradeData' if opposite_source == 'BANK' else 'CounterpartyTradeData')
    
    # Generate composite key components for filtering
    composite_key_components = []
    if trade.get('trade_date'):
        composite_key_components.append(trade['trade_date'])
    if trade.get('currency'):
        composite_key_components.append(trade['currency'])
    if trade.get('total_notional_quantity'):
        # Bucket notional into ranges for fuzzy matching
        notional = float(trade['total_notional_quantity'])
        notional_bucket = f"N{int(notional / 1000)}K"
        composite_key_components.append(notional_bucket)
    if trade.get('commodity_type'):
        composite_key_components.append(trade['commodity_type'])
    
    composite_key = "#".join(composite_key_components) if composite_key_components else "UNKNOWN"
    
    # Use composite key for efficient filtering if available
    if composite_key != "UNKNOWN":
        # Query by composite key components for more flexible matching
        components = composite_key.split('#')
        filter_expressions = []
        expression_values = {}
        
        for i, component in enumerate(components):
            if component:
                attr_name = f":val{i}"
                # For each component, check if it's contained in the composite key
                filter_expressions.append(f"contains(composite_key, {attr_name})")
                expression_values[attr_name] = component
        
        filter_expression = " AND ".join(filter_expressions)
        
        response = table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_values,
            Limit=20  # Limit potential matches for performance
        )
    else:
        # Fallback to scanning for unmatched trades
        response = table.scan(
            FilterExpression="matched_status = :status",
            ExpressionAttributeValues={":status": "PENDING"},
            Limit=50
        )
    
    potential_matches = response.get('Items', [])
    logger.info(f"Found {len(potential_matches)} potential matches for trade {trade.get('trade_id')}")
    return potential_matches


@tool
def compute_similarity(bank_trade: Dict[str, Any], counterparty_trade: Dict[str, Any], weights: Dict[str, float]) -> float:
    """
    Compute similarity score between two trades.
    
    Args:
        bank_trade (Dict[str, Any]): The bank trade record
        counterparty_trade (Dict[str, Any]): The counterparty trade record
        weights (Dict[str, float]): Weights for different attributes
        
    Returns:
        float: Similarity score between 0 and 1
    """
    score = 0.0
    
    # Trade date comparison (exact match)
    if bank_trade.get('trade_date') and counterparty_trade.get('trade_date'):
        if bank_trade['trade_date'] == counterparty_trade['trade_date']:
            score += weights.get("trade_date", 0.3)
    
    # Counterparty name comparison (fuzzy match)
    bank_entity = bank_trade.get('buyer_legal_entity') or bank_trade.get('seller_legal_entity')
    cpty_entity = counterparty_trade.get('buyer_legal_entity') or counterparty_trade.get('seller_legal_entity')
    
    if bank_entity and cpty_entity:
        name_similarity = SequenceMatcher(None, bank_entity, cpty_entity).ratio()
        score += weights.get("counterparty_name", 0.2) * name_similarity
    
    # Notional comparison (with tolerance)
    bank_notional = bank_trade.get('total_notional_quantity')
    cpty_notional = counterparty_trade.get('total_notional_quantity')
    
    if bank_notional and cpty_notional:
        bank_notional_float = float(bank_notional)
        cpty_notional_float = float(cpty_notional)
        
        notional_diff = abs(bank_notional_float - cpty_notional_float)
        notional_pct_diff = notional_diff / bank_notional_float if bank_notional_float > 0 else 1.0
        
        # Full score if within 0.1%, scaled down as difference increases
        if notional_pct_diff <= 0.001:
            notional_score = 1.0
        elif notional_pct_diff <= 0.01:
            notional_score = 0.9
        elif notional_pct_diff <= 0.05:
            notional_score = 0.5
        else:
            notional_score = max(0, 1 - notional_pct_diff)
        
        score += weights.get("notional", 0.25) * notional_score
    
    # Currency comparison (exact match)
    if bank_trade.get('currency') and counterparty_trade.get('currency'):
        if bank_trade['currency'].upper() == counterparty_trade['currency'].upper():
            score += weights.get("currency", 0.15)
    
    # Product type comparison (fuzzy match)
    if bank_trade.get('commodity_type') and counterparty_trade.get('commodity_type'):
        product_similarity = SequenceMatcher(None, bank_trade['commodity_type'], counterparty_trade['commodity_type']).ratio()
        score += weights.get("product_type", 0.1) * product_similarity
    
    return score


@tool
def update_match_status(bank_trade: Dict[str, Any], counterparty_trade: Dict[str, Any], score: float) -> str:
    """
    Update the match status for both trades and create a match record.
    
    Args:
        bank_trade (Dict[str, Any]): The bank trade record
        counterparty_trade (Dict[str, Any]): The counterparty trade record
        score (float): The similarity score
        
    Returns:
        str: The match ID
    """
    dynamodb = boto3.resource('dynamodb')
    bank_table = dynamodb.Table('BankTradeData')
    counterparty_table = dynamodb.Table('CounterpartyTradeData')
    matches_table = dynamodb.Table('TradeMatches')
    
    match_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Update both trades with match information - using correct composite keys
    # Bank table has composite key of trade_id and internal_reference
    bank_table.update_item(
        Key={
            "trade_id": bank_trade["trade_id"],
            "internal_reference": bank_trade["internal_reference"]
        },
        UpdateExpression="SET matched_status = :status, match_id = :match_id, last_updated = :timestamp",
        ExpressionAttributeValues={
            ":status": "MATCHED",
            ":match_id": match_id,
            ":timestamp": timestamp
        }
    )
    
    # Counterparty table has the same schema
    counterparty_table.update_item(
        Key={
            "trade_id": counterparty_trade["trade_id"],
            "internal_reference": counterparty_trade["internal_reference"]
        },
        UpdateExpression="SET matched_status = :status, match_id = :match_id, last_updated = :timestamp",
        ExpressionAttributeValues={
            ":status": "MATCHED",
            ":match_id": match_id,
            ":timestamp": timestamp
        }
    )
    
    # Create match record in TradeMatches table
    matches_table.put_item(
        Item={
            "match_id": match_id,
            "bank_trade_id": bank_trade["trade_id"],
            "counterparty_trade_id": counterparty_trade["trade_id"],
            "similarity_score": Decimal(str(score)),
            "reconciliation_status": "PENDING",
            "last_updated": timestamp
        }
    )
    
    logger.info(f"Created match {match_id} between bank trade {bank_trade['trade_id']} and counterparty trade {counterparty_trade['trade_id']} with score {score}")
    return match_id


@tool
def mark_as_unmatched(trade: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark a trade as unmatched.
    
    Args:
        trade (Dict[str, Any]): The trade to mark as unmatched
        
    Returns:
        Dict[str, Any]: The update result
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = 'BankTradeData' if trade['source'] == 'BANK' else 'CounterpartyTradeData'
    table = dynamodb.Table(table_name)
    
    response = table.update_item(
        Key={"trade_id": trade["trade_id"]},
        UpdateExpression="SET matched_status = :status, last_updated = :timestamp",
        ExpressionAttributeValues={
            ":status": "UNMATCHED",
            ":timestamp": datetime.now().isoformat()
        },
        ReturnValues="ALL_NEW"
    )
    
    logger.info(f"Marked trade {trade['trade_id']} as UNMATCHED")
    return response.get('Attributes', {})


@tool
def fetch_matched_trades(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch matched trades that need reconciliation.
    
    Args:
        limit (int): Maximum number of trades to fetch
        
    Returns:
        List[Dict[str, Any]]: List of matched trade records
    """
    dynamodb = boto3.resource('dynamodb')
    matches_table = dynamodb.Table('TradeMatches')
    
    response = matches_table.scan(
        FilterExpression="reconciliation_status = :status",
        ExpressionAttributeValues={":status": "PENDING"},
        Limit=limit
    )
    
    matches = response.get('Items', [])
    logger.info(f"Fetched {len(matches)} matched trades for reconciliation")
    return matches


@tool
def get_trade_pair(match: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get the bank and counterparty trade details for a match.
    
    Args:
        match (Dict[str, Any]): The match record
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary with bank_trade and counterparty_trade
    """
    dynamodb = boto3.resource('dynamodb')
    bank_table = dynamodb.Table('BankTradeData')
    counterparty_table = dynamodb.Table('CounterpartyTradeData')
    
    bank_trade = bank_table.get_item(
        Key={"trade_id": match["bank_trade_id"]}
    ).get('Item', {})
    
    counterparty_trade = counterparty_table.get_item(
        Key={"trade_id": match["counterparty_trade_id"]}
    ).get('Item', {})
    
    return {
        "bank_trade": bank_trade,
        "counterparty_trade": counterparty_trade
    }


@tool
def compare_fields(bank_trade: Dict[str, Any], counterparty_trade: Dict[str, Any], 
                  numeric_tolerance: Dict[str, float], string_similarity_threshold: float) -> Dict[str, Dict[str, Any]]:
    """
    Compare fields between bank and counterparty trades.
    
    Args:
        bank_trade (Dict[str, Any]): The bank trade record
        counterparty_trade (Dict[str, Any]): The counterparty trade record
        numeric_tolerance (Dict[str, float]): Tolerance thresholds for numeric fields
        string_similarity_threshold (float): Threshold for string field similarity
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of field comparison results
    """
    field_results = {}
    
    # Fields to compare based on trade_attributes.json
    fields_to_compare = [
        "trade_date", "effective_date", "termination_date",
        "total_notional_quantity", "unit_of_measure",
        "fixed_price", "currency", "price_unit",
        "commodity_type", "settlement_type", "business_days_convention"
    ]
    
    for field in fields_to_compare:
        bank_value = bank_trade.get(field)
        counterparty_value = counterparty_trade.get(field)
        
        # Skip if both values are missing
        if bank_value is None and counterparty_value is None:
            continue
        
        # Handle missing values
        if bank_value is None or counterparty_value is None:
            field_results[field] = {
                "field_name": field,
                "bank_value": bank_value,
                "counterparty_value": counterparty_value,
                "status": "MISSING",
                "reason": "Field missing in one source"
            }
            continue
        
        # Handle numeric fields with tolerance
        if isinstance(bank_value, (int, float, Decimal)) or (isinstance(bank_value, str) and bank_value.replace('.', '', 1).isdigit()):
            # Convert to float for comparison
            bank_num = float(bank_value) if isinstance(bank_value, (int, float, Decimal)) else float(bank_value)
            counterparty_num = float(counterparty_value) if isinstance(counterparty_value, (int, float, Decimal)) else float(counterparty_value)
            
            # Get tolerance for this field or use default
            tolerance = numeric_tolerance.get(field, 0.001)
            
            # Calculate percentage difference
            if bank_num != 0:
                pct_diff = abs(bank_num - counterparty_num) / abs(bank_num)
                
                if pct_diff <= tolerance:
                    status = "MATCHED"
                    reason = None
                else:
                    status = "MISMATCHED"
                    reason = f"Difference of {pct_diff:.4%} exceeds tolerance of {tolerance:.4%}"
            else:
                # Handle division by zero
                if counterparty_num == 0:
                    status = "MATCHED"
                    reason = None
                else:
                    status = "MISMATCHED"
                    reason = "Values differ and bank value is zero"
        
        # Handle string fields with fuzzy matching
        elif isinstance(bank_value, str) and isinstance(counterparty_value, str):
            # Exact match for dates and codes
            if field in ["trade_date", "effective_date", "termination_date", "currency"]:
                if bank_value == counterparty_value:
                    status = "MATCHED"
                    reason = None
                else:
                    status = "MISMATCHED"
                    reason = "Values do not match exactly"
            else:
                # Fuzzy match for other string fields
                similarity = SequenceMatcher(None, bank_value, counterparty_value).ratio()
                
                if similarity >= string_similarity_threshold:
                    status = "MATCHED"
                    reason = None
                else:
                    status = "MISMATCHED"
                    reason = f"String similarity {similarity:.2%} below threshold {string_similarity_threshold:.2%}"
        
        # Handle other types
        else:
            if str(bank_value) == str(counterparty_value):
                status = "MATCHED"
                reason = None
            else:
                status = "MISMATCHED"
                reason = "Values do not match"
        
        field_results[field] = {
            "field_name": field,
            "bank_value": bank_value if not isinstance(bank_value, Decimal) else float(bank_value),
            "counterparty_value": counterparty_value if not isinstance(counterparty_value, Decimal) else float(counterparty_value),
            "status": status,
            "reason": reason
        }
    
    return field_results


@tool
def determine_overall_status(field_results: Dict[str, Dict[str, Any]], critical_fields: List[str]) -> str:
    """
    Determine the overall reconciliation status based on field results.
    
    Args:
        field_results (Dict[str, Dict[str, Any]]): Dictionary of field comparison results
        critical_fields (List[str]): List of fields considered critical
        
    Returns:
        str: Overall status (FULLY_MATCHED, PARTIALLY_MATCHED, or CRITICAL_MISMATCH)
    """
    # Check if any critical fields are mismatched
    critical_mismatches = [
        field for field, result in field_results.items()
        if field in critical_fields and result["status"] in ["MISMATCHED", "MISSING"]
    ]
    
    if critical_mismatches:
        return "CRITICAL_MISMATCH"
    
    # Check if any fields are mismatched
    any_mismatches = any(
        result["status"] in ["MISMATCHED", "MISSING"]
        for result in field_results.values()
    )
    
    if any_mismatches:
        return "PARTIALLY_MATCHED"
    
    return "FULLY_MATCHED"


@tool
def update_reconciliation_status(match_id: str, field_results: Dict[str, Dict[str, Any]], overall_status: str) -> Dict[str, Any]:
    """
    Update the reconciliation status in the TradeMatches table.
    
    Args:
        match_id (str): The match ID
        field_results (Dict[str, Dict[str, Any]]): Dictionary of field comparison results
        overall_status (str): Overall reconciliation status
        
    Returns:
        Dict[str, Any]: The update result
    """
    dynamodb = boto3.resource('dynamodb')
    matches_table = dynamodb.Table('TradeMatches')
    
    # Update the match record
    response = matches_table.update_item(
        Key={"match_id": match_id},
        UpdateExpression="SET reconciliation_status = :status, field_results = :results, last_updated = :timestamp",
        ExpressionAttributeValues={
            ":status": overall_status,
            ":results": field_results,
            ":timestamp": datetime.now().isoformat()
        },
        ReturnValues="ALL_NEW"
    )
    
    logger.info(f"Updated reconciliation status for match {match_id} to {overall_status}")
    return response.get('Attributes', {})


@tool
def generate_reconciliation_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a reconciliation report from the results.
    
    Args:
        results (List[Dict[str, Any]]): List of reconciliation results
        
    Returns:
        Dict[str, Any]: The generated report
    """
    report_id = f"recon-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    timestamp = datetime.now().isoformat()
    
    # Generate summary statistics
    summary = {
        "total_matches": len(results),
        "fully_matched": sum(1 for r in results if r.get("reconciliation_status") == "FULLY_MATCHED"),
        "partially_matched": sum(1 for r in results if r.get("reconciliation_status") == "PARTIALLY_MATCHED"),
        "critical_mismatch": sum(1 for r in results if r.get("reconciliation_status") == "CRITICAL_MISMATCH"),
        "match_confidence_avg": sum(float(r.get("similarity_score", 0)) for r in results) / len(results) if results else 0
    }
    
    # Generate detailed results
    detailed_results = []
    for match in results:
        match_result = {
            "trade_pair_id": match.get("match_id"),
            "bank_trade_id": match.get("bank_trade_id"),
            "counterparty_trade_id": match.get("counterparty_trade_id"),
            "match_confidence": float(match.get("similarity_score", 0)),
            "overall_status": match.get("reconciliation_status"),
            "last_updated": match.get("last_updated")
        }
        
        # Include field-level details if available
        if "field_results" in match:
            match_result["field_results"] = match["field_results"]
        
        detailed_results.append(match_result)
    
    # Construct the full report
    report = {
        "report_id": report_id,
        "timestamp": timestamp,
        "summary": summary,
        "detailed_results": detailed_results
    }
    
    return report


@tool
def store_report(report: Dict[str, Any], bucket: str) -> str:
    """
    Store the report in S3.
    
    Args:
        report (Dict[str, Any]): The report to store
        bucket (str): The S3 bucket name
        
    Returns:
        str: The S3 URI of the stored report
    """
    s3 = boto3.client('s3')
    report_id = report["report_id"]
    report_key = f"reports/{report_id}.json"
    
    # Convert to JSON with custom encoder for Decimal
    report_json = json.dumps(report, cls=DecimalEncoder, indent=2)
    
    # Store in S3
    s3.put_object(
        Bucket=bucket,
        Key=report_key,
        Body=report_json,
        ContentType="application/json",
        Metadata={
            "report-type": "trade-reconciliation",
            "timestamp": report["timestamp"],
            "total-matches": str(report["summary"]["total_matches"])
        }
    )
    
    logger.info(f"Stored report {report_id} in S3 bucket {bucket}")
    return f"s3://{bucket}/{report_key}"


@tool
def fetch_reconciliation_results(status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch reconciliation results, optionally filtered by status.
    
    Args:
        status (Optional[str]): Filter by reconciliation status
        limit (int): Maximum number of results to fetch
        
    Returns:
        List[Dict[str, Any]]: List of reconciliation results
    """
    dynamodb = boto3.resource('dynamodb')
    matches_table = dynamodb.Table('TradeMatches')
    
    filter_expression = "reconciliation_status <> :pending"
    expression_values = {":pending": "PENDING"}
    
    if status:
        filter_expression += " AND reconciliation_status = :status"
        expression_values[":status"] = status
    
    response = matches_table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_values,
        Limit=limit
    )
    
    results = response.get('Items', [])
    logger.info(f"Fetched {len(results)} reconciliation results")
    return results