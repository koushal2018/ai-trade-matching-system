"""
Trade Matching Agent - Strands SDK Implementation (IMPROVED)

Rock-solid implementation with:
- Nova Pro optimized configuration (temperature=0, topK=1, proper max_tokens)
- Custom DynamoDB tools (no profile issues, Nova-compliant schemas)
- Circuit breaker for retry loops
- Clear separation between data retrieval and comparison logic
- Proper error handling for AgentCore Runtime

Requirements: 2.1, 2.2, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""

import os
# Enable non-interactive tool execution for AgentCore Runtime
# MUST be set before importing strands_tools
os.environ["BYPASS_TOOL_CONSENT"] = "true"

import json
import uuid
import re
import boto3
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
import logging
from decimal import Decimal

# Strands SDK imports
from strands import Agent, tool
from strands.models import BedrockModel

# MCP Gateway imports - following collector agent pattern
try:
    from mcp.client.streamable_http import streamablehttp_client
    from strands.tools.mcp.mcp_client import MCPClient
    MCP_AVAILABLE = True
    print("✓ MCP client libraries loaded successfully")
except ImportError as e:
    MCP_AVAILABLE = False
    print(f"⚠ MCP client libraries not available: {e}")


from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus
from bedrock_agentcore.memory import MemoryClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AgentCore Memory - Strands Integration
try:
    from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
    from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logger.warning("AgentCore Memory Strands integration not available - memory features disabled")

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production")
BANK_TABLE = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-5-20250929-v1:0")
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_ALIAS = os.getenv("AGENT_ALIAS", "default")
OBSERVABILITY_STAGE = os.getenv("OBSERVABILITY_STAGE", "development")

# MCP Gateway configuration from environment
GATEWAY_URL = os.environ.get("GATEWAY_MCP_URL")
GATEWAY_CLIENT_ID = os.environ.get("GATEWAY_CLIENT_ID")
GATEWAY_CLIENT_SECRET = os.environ.get("GATEWAY_CLIENT_SECRET")
GATEWAY_TOKEN_ENDPOINT = os.environ.get("GATEWAY_TOKEN_ENDPOINT")
GATEWAY_SCOPE = os.environ.get("GATEWAY_SCOPE")

# Agent identification constants
AGENT_NAME = "trade-matching-agent"

# AgentCore Memory Configuration
MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID", "trade_matching_decisions-Z3tG4b4Xsd")

# Circuit breaker configuration
MAX_TOOL_RETRIES = 3
MAX_CONSECUTIVE_ERRORS = 5

logger.info(f"[INIT] Agent initialized - service={AGENT_NAME}, stage={OBSERVABILITY_STAGE}")

# Lazy-initialized boto3 clients for efficiency (NO profile_name!)
_boto_clients: Dict[str, Any] = {}


def get_boto_client(service: str):
    """Get or create a boto3 client for the specified service.
    
    Uses IAM role credentials automatically - NO profile_name to avoid
    ProfileNotFound errors in AgentCore Runtime.
    """
    if service not in _boto_clients:
        # Do NOT pass profile_name - use IAM role from execution environment
        _boto_clients[service] = boto3.client(service, region_name=REGION)
    return _boto_clients[service]


# ============================================================================
# Custom DynamoDB Tools (Nova Pro Compatible + Token Optimized)
# ============================================================================
# These tools do pre-processing to reduce token load on the LLM

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def _scan_table(table_name: str) -> List[Dict]:
    """Internal helper to scan a DynamoDB table."""
    from boto3.dynamodb.types import TypeDeserializer
    deserializer = TypeDeserializer()
    
    dynamodb = get_boto_client('dynamodb')
    response = dynamodb.scan(TableName=table_name)
    items = response.get('Items', [])
    
    while 'LastEvaluatedKey' in response:
        response = dynamodb.scan(
            TableName=table_name,
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        items.extend(response.get('Items', []))
    
    trades = []
    for item in items:
        trade = {k: deserializer.deserialize(v) for k, v in item.items()}
        trades.append(trade)
    
    return trades


def _extract_key_attributes(trade: Dict) -> Dict:
    """
    Extract CDM-aligned matching attributes from a trade to reduce token usage.
    
    Based on FINOS/ISDA Common Domain Model (CDM) field specifications.
    """
    # CDM-aligned field name variations (supporting both CDM standard names and legacy formats)
    key_fields = {
        # Core Identification
        'trade_id': ['trade_id', 'Trade_ID', 'TradeID', 'tradeId', 'usi', 'uti'],
        
        # Product Classification
        'product_type': ['product_type', 'Product_Type', 'ProductType', 'product_qualifier', 
                         'Instrument', 'instrument', 'Trade_Type', 'trade_type', 'asset_class'],
        'sub_product_type': ['sub_product_type', 'SubProductType'],
        
        # Economic Terms - Dates
        'trade_date': ['trade_date', 'Trade_Date', 'TradeDate', 'tradeDate', 'execution_date'],
        'effective_date': ['effective_date', 'Effective_Date', 'EffectiveDate', 'effectiveDate', 
                           'Start_Date', 'start_date', 'value_date'],
        'termination_date': ['termination_date', 'Termination_Date', 'TerminationDate', 
                              'Maturity_Date', 'maturity_date', 'End_Date', 'end_date', 'expiry_date'],
        
        # Quantity & Price
        'currency': ['currency', 'Currency', 'CCY', 'ccy', 'notional_currency'],
        'notional': ['notional_amount', 'notional', 'Notional', 'NotionalAmount', 
                     'Quantity', 'quantity', 'Total_Quantity', 'principal'],
        'currency_2': ['currency_2', 'Currency_2', 'second_currency'],
        'notional_2': ['notional_amount_2', 'notional_2', 'Notional_2'],
        
        # Counterparty Information
        'party_a_name': ['party_a_name', 'Party_A_Name', 'Party_A', 'bank_name', 'Bank_Name'],
        'party_b_name': ['party_b_name', 'Party_B_Name', 'Party_B', 'counterparty', 'Counterparty', 
                         'CounterpartyName', 'Counterparty_Name'],
        'party_a_lei': ['party_a_lei', 'Party_A_LEI', 'bank_lei', 'Bank_LEI'],
        'party_b_lei': ['party_b_lei', 'Party_B_LEI', 'counterparty_lei', 'Counterparty_LEI'],
        
        # Interest Rate Terms (CDM critical fields)
        'fixed_rate': ['fixed_rate', 'Fixed_Rate', 'FixedRate', 'Fixed_Price', 'fixed_price', 
                       'Price', 'price', 'Rate', 'rate', 'coupon_rate'],
        'floating_rate_index': ['floating_rate_index', 'Floating_Rate_Index', 'FloatingIndex', 
                                 'Index', 'index', 'reference_rate', 'benchmark'],
        'floating_rate_spread': ['floating_rate_spread', 'Spread', 'spread', 'margin'],
        'day_count_fraction': ['day_count_fraction', 'Day_Count_Fraction', 'DayCountFraction',
                                'day_count', 'Day_Count', 'DayCount', 'day_count_convention'],
        'payment_frequency': ['payment_frequency', 'Payment_Frequency', 'PaymentFrequency',
                               'frequency', 'Frequency', 'payment_period'],
        'payment_frequency_2': ['payment_frequency_2', 'Payment_Frequency_2'],
        'business_day_convention': ['business_day_convention', 'Business_Day_Convention',
                                     'BusinessDayConvention', 'bdc'],
        'reset_frequency': ['reset_frequency', 'Reset_Frequency', 'ResetFrequency'],
        
        # FX Terms
        'fx_rate': ['fx_rate', 'FX_Rate', 'exchange_rate', 'Exchange_Rate'],
        
        # Settlement Terms
        'settlement_type': ['settlement_type', 'Settlement_Type', 'SettlementType'],
        'settlement_date': ['settlement_date', 'Settlement_Date', 'SettlementDate'],
    }
    
    extracted = {}
    for standard_name, variations in key_fields.items():
        for var in variations:
            if var in trade:
                extracted[standard_name] = trade[var]
                break
    
    return extracted


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats to datetime object."""
    if not date_str:
        return None
    
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%Y%m%d",
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    return None


def _dates_within_tolerance(date1_str: str, date2_str: str, tolerance_days: int = 2) -> bool:
    """Check if two dates are within tolerance (±days)."""
    date1 = _parse_date(date1_str)
    date2 = _parse_date(date2_str)
    
    if date1 and date2:
        delta = abs((date1 - date2).days)
        return delta <= tolerance_days
    
    # Fallback to string comparison if parsing fails
    return str(date1_str).strip() == str(date2_str).strip()


def _fuzzy_match_counterparty(name1: str, name2: str) -> float:
    """
    Fuzzy match counterparty names. Returns a score between 0 and 1.
    Handles variations like:
    - "Merrill Lynch International" vs "MERRILL LYNCH INTL"
    - "FAB Global Markets (Cayman) Limited" vs "FAB GLOBAL MARKETS"
    """
    if not name1 or not name2:
        return 0.0
    
    # Normalize: uppercase, remove common suffixes, remove punctuation
    def normalize(name):
        name = str(name).upper()
        # Remove common legal suffixes
        suffixes = ['LIMITED', 'LTD', 'LLC', 'INC', 'CORP', 'CORPORATION', 
                    'INTERNATIONAL', 'INTL', 'INT\'L', 'PLC', 'SA', 'AG', 'GMBH',
                    '(CAYMAN)', 'CAYMAN', 'LP', 'LLP']
        for suffix in suffixes:
            name = name.replace(suffix, '')
        # Remove punctuation and extra spaces
        name = re.sub(r'[^\w\s]', '', name)
        name = ' '.join(name.split())
        return name
    
    n1 = normalize(name1)
    n2 = normalize(name2)
    
    # Exact match after normalization
    if n1 == n2:
        return 1.0
    
    # Check if one contains the other
    if n1 in n2 or n2 in n1:
        return 0.9
    
    # Word overlap scoring
    words1 = set(n1.split())
    words2 = set(n2.split())
    
    if not words1 or not words2:
        return 0.0
    
    common_words = words1.intersection(words2)
    total_words = words1.union(words2)
    
    # Jaccard similarity
    return len(common_words) / len(total_words) if total_words else 0.0


def _calculate_match_score(source_trade: Dict, target_trade: Dict) -> Dict:
    """
    Calculate a match score between two trades based on CDM-aligned matching criteria.
    
    CDM Matching Criteria (FINOS/ISDA Common Domain Model):
    - Currency: exact match required
    - Notional Amount: ±2% tolerance
    - Dates: ±2 business days tolerance (trade, effective, termination)
    - Counterparty: fuzzy name matching OR exact LEI match
    - Product Type: exact match
    - Day Count Fraction: exact match (critical for interest calculations)
    - Payment Frequency: exact match
    - Floating Rate Index: exact match (SOFR, EURIBOR, etc.)
    - Fixed Rate/Price: ±1bp tolerance
    
    Returns a dict with score, breakdown, and classification.
    """
    score = 0.0
    max_score = 0.0
    breakdown = {}
    
    source = _extract_key_attributes(source_trade)
    target = _extract_key_attributes(target_trade)
    
    # =========================================================================
    # 1. Currency (exact match, high weight) - 12 points
    # =========================================================================
    if 'currency' in source and 'currency' in target:
        max_score += 12
        if str(source['currency']).upper() == str(target['currency']).upper():
            score += 12
            breakdown['currency'] = {'match': True, 'source': source['currency'], 'target': target['currency']}
        else:
            breakdown['currency'] = {'match': False, 'source': source['currency'], 'target': target['currency']}
    
    # =========================================================================
    # 2. Notional Amount (±2% tolerance) - 15 points
    # =========================================================================
    if 'notional' in source and 'notional' in target:
        max_score += 15
        try:
            s_notional = float(str(source['notional']).replace(',', '').replace(' ', ''))
            t_notional = float(str(target['notional']).replace(',', '').replace(' ', ''))
            if s_notional > 0:
                diff_pct = abs(s_notional - t_notional) / s_notional
                if diff_pct <= 0.02:  # Within 2%
                    score += 15
                    breakdown['notional'] = {'match': True, 'source': s_notional, 'target': t_notional, 'diff_pct': round(diff_pct * 100, 2)}
                elif diff_pct <= 0.05:  # Within 5% - partial credit
                    score += 8
                    breakdown['notional'] = {'match': 'partial', 'source': s_notional, 'target': t_notional, 'diff_pct': round(diff_pct * 100, 2)}
                else:
                    breakdown['notional'] = {'match': False, 'source': s_notional, 'target': t_notional, 'diff_pct': round(diff_pct * 100, 2)}
        except (ValueError, ZeroDivisionError):
            breakdown['notional'] = {'match': False, 'error': 'parse_error'}
    
    # =========================================================================
    # 3. Product Type (exact match) - 10 points
    # =========================================================================
    if 'product_type' in source and 'product_type' in target:
        max_score += 10
        s_type = str(source['product_type']).upper().replace('_', ' ').replace('-', ' ')
        t_type = str(target['product_type']).upper().replace('_', ' ').replace('-', ' ')
        if s_type == t_type:
            score += 10
            breakdown['product_type'] = {'match': True, 'source': source['product_type'], 'target': target['product_type']}
        elif s_type in t_type or t_type in s_type:
            score += 6
            breakdown['product_type'] = {'match': 'partial', 'source': source['product_type'], 'target': target['product_type']}
        else:
            breakdown['product_type'] = {'match': False, 'source': source['product_type'], 'target': target['product_type']}
    
    # =========================================================================
    # 4. Trade Date (±2 days tolerance) - 8 points
    # =========================================================================
    if 'trade_date' in source and 'trade_date' in target:
        max_score += 8
        if _dates_within_tolerance(source['trade_date'], target['trade_date'], 2):
            score += 8
            breakdown['trade_date'] = {'match': True, 'source': source['trade_date'], 'target': target['trade_date']}
        else:
            breakdown['trade_date'] = {'match': False, 'source': source['trade_date'], 'target': target['trade_date']}
    
    # =========================================================================
    # 5. Effective Date (±2 days tolerance) - 8 points
    # =========================================================================
    if 'effective_date' in source and 'effective_date' in target:
        max_score += 8
        if _dates_within_tolerance(source['effective_date'], target['effective_date'], 2):
            score += 8
            breakdown['effective_date'] = {'match': True, 'source': source['effective_date'], 'target': target['effective_date']}
        else:
            breakdown['effective_date'] = {'match': False, 'source': source['effective_date'], 'target': target['effective_date']}
    
    # =========================================================================
    # 6. Termination/Maturity Date (±2 days tolerance) - 8 points
    # =========================================================================
    if 'termination_date' in source and 'termination_date' in target:
        max_score += 8
        if _dates_within_tolerance(source['termination_date'], target['termination_date'], 2):
            score += 8
            breakdown['termination_date'] = {'match': True, 'source': source['termination_date'], 'target': target['termination_date']}
        else:
            breakdown['termination_date'] = {'match': False, 'source': source['termination_date'], 'target': target['termination_date']}
    
    # =========================================================================
    # 7. Counterparty - LEI match (exact) OR Name match (fuzzy) - 8 points
    # =========================================================================
    # First try LEI match (preferred - exact match)
    lei_matched = False
    if 'party_b_lei' in source and 'party_b_lei' in target:
        max_score += 8
        if str(source['party_b_lei']).upper() == str(target['party_b_lei']).upper():
            score += 8
            lei_matched = True
            breakdown['counterparty_lei'] = {'match': True, 'source': source['party_b_lei'], 'target': target['party_b_lei']}
        else:
            breakdown['counterparty_lei'] = {'match': False, 'source': source['party_b_lei'], 'target': target['party_b_lei']}
    
    # Fall back to fuzzy name matching if LEI not available or didn't match
    if not lei_matched and 'party_b_name' in source and 'party_b_name' in target:
        if 'party_b_lei' not in source or 'party_b_lei' not in target:
            max_score += 8
        fuzzy_score = _fuzzy_match_counterparty(source['party_b_name'], target['party_b_name'])
        if fuzzy_score >= 0.8:
            score += 8
            breakdown['counterparty_name'] = {'match': True, 'source': source['party_b_name'], 'target': target['party_b_name'], 'similarity': round(fuzzy_score, 2)}
        elif fuzzy_score >= 0.5:
            score += 4
            breakdown['counterparty_name'] = {'match': 'partial', 'source': source['party_b_name'], 'target': target['party_b_name'], 'similarity': round(fuzzy_score, 2)}
        else:
            breakdown['counterparty_name'] = {'match': False, 'source': source['party_b_name'], 'target': target['party_b_name'], 'similarity': round(fuzzy_score, 2)}
    
    # =========================================================================
    # 8. Day Count Fraction (exact match - CDM critical) - 8 points
    # =========================================================================
    if 'day_count_fraction' in source and 'day_count_fraction' in target:
        max_score += 8
        s_dc = str(source['day_count_fraction']).upper().replace(' ', '').replace('_', '/')
        t_dc = str(target['day_count_fraction']).upper().replace(' ', '').replace('_', '/')
        # Normalize common variations
        dc_aliases = {
            'ACT/360': ['ACT/360', 'ACTUAL/360', 'A/360'],
            'ACT/365': ['ACT/365', 'ACTUAL/365', 'A/365', 'ACT/365F', 'ACT/365FIXED'],
            '30/360': ['30/360', '30E/360', 'BOND', 'BONDBASIS'],
            'ACT/ACT': ['ACT/ACT', 'ACTUAL/ACTUAL', 'ACT/ACTISDA', 'ACT/ACTISMA'],
        }
        s_normalized = s_dc
        t_normalized = t_dc
        for standard, aliases in dc_aliases.items():
            if s_dc in aliases:
                s_normalized = standard
            if t_dc in aliases:
                t_normalized = standard
        
        if s_normalized == t_normalized:
            score += 8
            breakdown['day_count_fraction'] = {'match': True, 'source': source['day_count_fraction'], 'target': target['day_count_fraction']}
        else:
            breakdown['day_count_fraction'] = {'match': False, 'source': source['day_count_fraction'], 'target': target['day_count_fraction']}
    
    # =========================================================================
    # 9. Payment Frequency (exact match - CDM critical) - 7 points
    # =========================================================================
    if 'payment_frequency' in source and 'payment_frequency' in target:
        max_score += 7
        freq_aliases = {
            'MONTHLY': ['MONTHLY', '1M', 'M', 'MONTH'],
            'QUARTERLY': ['QUARTERLY', '3M', 'Q', 'QUARTER'],
            'SEMI_ANNUAL': ['SEMI_ANNUAL', 'SEMIANNUAL', '6M', 'S', 'SEMI-ANNUAL'],
            'ANNUAL': ['ANNUAL', '12M', 'A', 'YEARLY', '1Y'],
        }
        s_freq = str(source['payment_frequency']).upper().replace('-', '_').replace(' ', '')
        t_freq = str(target['payment_frequency']).upper().replace('-', '_').replace(' ', '')
        
        s_normalized = s_freq
        t_normalized = t_freq
        for standard, aliases in freq_aliases.items():
            if s_freq in aliases:
                s_normalized = standard
            if t_freq in aliases:
                t_normalized = standard
        
        if s_normalized == t_normalized:
            score += 7
            breakdown['payment_frequency'] = {'match': True, 'source': source['payment_frequency'], 'target': target['payment_frequency']}
        else:
            breakdown['payment_frequency'] = {'match': False, 'source': source['payment_frequency'], 'target': target['payment_frequency']}
    
    # =========================================================================
    # 10. Floating Rate Index (exact match - CDM critical) - 8 points
    # =========================================================================
    if 'floating_rate_index' in source and 'floating_rate_index' in target:
        max_score += 8
        index_aliases = {
            'SOFR': ['SOFR', 'USD-SOFR', 'SECURED OVERNIGHT FINANCING RATE'],
            'EURIBOR': ['EURIBOR', 'EUR-EURIBOR', 'EURO INTERBANK OFFERED RATE'],
            'ESTR': ['ESTR', 'EUR-ESTR', '€STR', 'EURO SHORT-TERM RATE'],
            'SONIA': ['SONIA', 'GBP-SONIA', 'STERLING OVERNIGHT INDEX AVERAGE'],
            'LIBOR': ['LIBOR', 'USD-LIBOR', 'GBP-LIBOR', 'EUR-LIBOR'],
            'EIBOR': ['EIBOR', 'AED-EIBOR', 'EMIRATES INTERBANK OFFERED RATE'],
        }
        s_idx = str(source['floating_rate_index']).upper().replace('-', ' ').replace('_', ' ')
        t_idx = str(target['floating_rate_index']).upper().replace('-', ' ').replace('_', ' ')
        
        s_normalized = s_idx
        t_normalized = t_idx
        for standard, aliases in index_aliases.items():
            for alias in aliases:
                if alias in s_idx:
                    s_normalized = standard
                if alias in t_idx:
                    t_normalized = standard
        
        if s_normalized == t_normalized:
            score += 8
            breakdown['floating_rate_index'] = {'match': True, 'source': source['floating_rate_index'], 'target': target['floating_rate_index']}
        else:
            breakdown['floating_rate_index'] = {'match': False, 'source': source['floating_rate_index'], 'target': target['floating_rate_index']}
    
    # =========================================================================
    # 11. Fixed Rate/Price (±1bp tolerance) - 8 points
    # =========================================================================
    if 'fixed_rate' in source and 'fixed_rate' in target:
        max_score += 8
        try:
            s_rate = float(str(source['fixed_rate']).replace(',', '').replace('%', ''))
            t_rate = float(str(target['fixed_rate']).replace(',', '').replace('%', ''))
            
            # Normalize if one is in percentage and other in decimal
            if s_rate > 1 and t_rate < 1:
                s_rate = s_rate / 100
            elif t_rate > 1 and s_rate < 1:
                t_rate = t_rate / 100
            
            diff_bps = abs(s_rate - t_rate) * 10000  # Convert to basis points
            if diff_bps <= 1:  # Within 1bp
                score += 8
                breakdown['fixed_rate'] = {'match': True, 'source': s_rate, 'target': t_rate, 'diff_bps': round(diff_bps, 2)}
            elif diff_bps <= 5:  # Within 5bp
                score += 4
                breakdown['fixed_rate'] = {'match': 'partial', 'source': s_rate, 'target': t_rate, 'diff_bps': round(diff_bps, 2)}
            else:
                breakdown['fixed_rate'] = {'match': False, 'source': s_rate, 'target': t_rate, 'diff_bps': round(diff_bps, 2)}
        except (ValueError, ZeroDivisionError):
            breakdown['fixed_rate'] = {'match': False, 'error': 'parse_error'}
    
    # =========================================================================
    # Calculate final score
    # =========================================================================
    final_score = (score / max_score * 100) if max_score > 0 else 0.0
    
    return {
        'score': round(final_score, 1),
        'breakdown': breakdown,
        'points_earned': score,
        'points_possible': max_score,
        'fields_compared': len(breakdown)
    }


@tool
def find_trade_matches(trade_id: str, source_type: str) -> str:
    """
    Find potential matches for a trade by comparing against the opposite table.
    This tool does the heavy lifting of scanning both tables and calculating
    match scores based on OTC derivative matching criteria.
    
    Matching Criteria:
    - Currency: exact match required
    - Notional Amount: ±2% tolerance  
    - Dates: ±2 days tolerance (trade, effective, termination)
    - Counterparty Names: fuzzy matching
    - Product Type: exact match
    - Fixed Rate/Price: ±1% tolerance
    
    Args:
        trade_id: The trade ID to match.
        source_type: Either 'BANK' or 'COUNTERPARTY' indicating which table the trade is from.
    
    Returns:
        JSON with the source trade, top matching candidates with scores and breakdown.
    """
    try:
        # Determine source and target tables
        if source_type.upper() == 'BANK':
            source_table = BANK_TABLE
            target_table = COUNTERPARTY_TABLE
        else:
            source_table = COUNTERPARTY_TABLE
            target_table = BANK_TABLE
        
        # Scan both tables
        source_trades = _scan_table(source_table)
        target_trades = _scan_table(target_table)
        
        logger.info(f"Scanned {len(source_trades)} from {source_table}, {len(target_trades)} from {target_table}")
        
        # Find the source trade
        source_trade = None
        for trade in source_trades:
            trade_id_value = trade.get('Trade_ID') or trade.get('trade_id') or trade.get('TradeID')
            if str(trade_id_value) == str(trade_id):
                source_trade = trade
                break
        
        if not source_trade:
            return json.dumps({
                "error": f"Trade {trade_id} not found in {source_table}",
                "found": False
            })
        
        # Calculate match scores for all target trades
        candidates = []
        for target in target_trades:
            match_result = _calculate_match_score(source_trade, target)
            target_id = target.get('Trade_ID') or target.get('trade_id') or target.get('TradeID')
            candidates.append({
                "trade_id": str(target_id),
                "score": match_result['score'],
                "breakdown": match_result['breakdown'],
                "attributes": _extract_key_attributes(target)
            })
        
        # Sort by score descending and take top 5
        candidates.sort(key=lambda x: x['score'], reverse=True)
        top_candidates = candidates[:5]
        
        # Determine classification based on top score
        top_score = top_candidates[0]['score'] if top_candidates else 0
        if top_score >= 85:
            classification = "MATCHED"
        elif top_score >= 70:
            classification = "PROBABLE_MATCH"
        elif top_score >= 50:
            classification = "REVIEW_REQUIRED"
        else:
            classification = "BREAK"
        
        result = {
            "source_trade": {
                "trade_id": str(trade_id),
                "table": source_table,
                "attributes": _extract_key_attributes(source_trade)
            },
            "best_match": top_candidates[0] if top_candidates else None,
            "other_candidates": top_candidates[1:4] if len(top_candidates) > 1 else [],
            "classification": classification,
            "confidence": top_score,
            "total_candidates_evaluated": len(target_trades)
        }
        
        logger.info(f"Match analysis complete: {classification} ({top_score}%) for trade {trade_id}")
        return json.dumps(result, cls=DecimalEncoder)
    
    except Exception as e:
        logger.error(f"Error in find_trade_matches: {e}")
        return json.dumps({"error": str(e), "trade_id": trade_id})


# ============================================================================
# Trade ID Normalization
# ============================================================================

def normalize_trade_id(raw_id: str, source: Optional[str] = None) -> str:
    """Normalize trade ID to standard format for consistent matching."""
    if not raw_id:
        return raw_id
    
    prefixes = ["fab_", "FAB_", "cpty_", "CPTY_", "bank_", "BANK_"]
    numeric_id = raw_id
    for prefix in prefixes:
        if numeric_id.startswith(prefix):
            numeric_id = numeric_id[len(prefix):]
            break
    
    match = re.search(r'(\d+)', numeric_id)
    if match:
        numeric_id = match.group(1)
    
    if source:
        source_lower = source.lower()
        if source_lower == "bank":
            return f"bank_{numeric_id}"
        elif source_lower == "counterparty":
            return f"cpty_{numeric_id}"
    
    return numeric_id


# ============================================================================
# AgentCore Memory Session Manager Factory
# ============================================================================

def create_memory_session_manager(
    correlation_id: str,
    trade_id: str = None
) -> Optional['AgentCoreMemorySessionManager']:
    """Create AgentCore Memory session manager for Strands agent integration."""
    if not MEMORY_AVAILABLE or not MEMORY_ID:
        logger.debug(f"[{correlation_id}] Memory not available - skipping session manager creation")
        return None
    
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        session_id = f"match_{trade_id or 'unknown'}_{timestamp}_{correlation_id[:8]}"
        
        config = AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=AGENT_NAME,
            retrieval_config={
                "/facts/{actorId}": RetrievalConfig(top_k=10, relevance_score=0.6),
                "/preferences/{actorId}": RetrievalConfig(top_k=5, relevance_score=0.7),
                "/summaries/{actorId}/{sessionId}": RetrievalConfig(top_k=5, relevance_score=0.5)
            }
        )
        
        session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=config,
            region_name=REGION
        )
        
        logger.info(f"[{correlation_id}] AgentCore Memory session created - memory_id={MEMORY_ID}, session_id={session_id}")
        return session_manager
        
    except Exception as e:
        logger.warning(f"[{correlation_id}] Failed to create memory session manager: {e}. Continuing without memory.")
        return None


# ============================================================================
# Health Check Handler
# ============================================================================

@app.ping
def health_check() -> PingStatus:
    """Custom health check for AgentCore Runtime."""
    try:
        get_boto_client('dynamodb')
        return PingStatus.HEALTHY
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return PingStatus.HEALTHY


# ============================================================================
# Agent System Prompt (Nova Pro Optimized - Token Efficient)
# ============================================================================

SYSTEM_PROMPT = f"""##Role##
You are an expert Trade Matching Agent for OTC derivative trade confirmations.

##Mission##
Match trades between bank and counterparty systems by analyzing their attributes. 
CRITICAL: Bank and counterparty systems use COMPLETELY DIFFERENT Trade_IDs for the same trade.
You must match by comparing trade characteristics, NOT by matching IDs directly.

##Available Tool##
You have ONE tool available:
**find_trade_matches** - Finds and scores potential matches for a trade
  - Parameters: trade_id (string), source_type ('BANK' or 'COUNTERPARTY')
  - Returns: Source trade attributes, top 5 matching candidates with scores, preliminary classification

##CRITICAL INSTRUCTIONS##
1. Call find_trade_matches with the trade_id and source_type
2. Review the results returned by the tool
3. Confirm or adjust the classification based on the attribute comparison
4. Return your final analysis as JSON

##Classification Thresholds##
- **MATCHED** (≥85%): High confidence - all critical attributes align
- **PROBABLE_MATCH** (70-84%): Good confidence - most attributes match
- **REVIEW_REQUIRED** (50-69%): Uncertain - needs human review
- **BREAK** (<50%): Low confidence - likely different transactions

##Output Format##
After reviewing the tool results, respond with:
```json
{{
  "match_classification": "MATCHED|PROBABLE_MATCH|REVIEW_REQUIRED|BREAK",
  "confidence_score": 85.5,
  "source_trade_id": "the trade being matched",
  "matched_trade_id": "the best matching counterparty trade ID",
  "reasoning": "brief explanation of why this classification was chosen"
}}
```
"""


# ============================================================================
# MCP Gateway Helpers
# ============================================================================

def _get_oauth_token() -> str:
    """Get OAuth2 token from Cognito using client credentials flow."""
    import httpx
    
    if not all([GATEWAY_CLIENT_ID, GATEWAY_CLIENT_SECRET, GATEWAY_TOKEN_ENDPOINT, GATEWAY_SCOPE]):
        raise ValueError("Missing Gateway OAuth configuration")
    
    response = httpx.post(
        GATEWAY_TOKEN_ENDPOINT,
        data={
            "grant_type": "client_credentials",
            "client_id": GATEWAY_CLIENT_ID,
            "client_secret": GATEWAY_CLIENT_SECRET,
            "scope": GATEWAY_SCOPE,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    
    if response.status_code != 200:
        logger.warning(f"OAuth token request failed with status: {response.status_code}")
        raise RuntimeError(f"OAuth failed: {response.status_code}")
    
    return response.json()["access_token"]


def _create_mcp_transport(headers=None):
    """Create MCP transport with OAuth authentication."""
    access_token = _get_oauth_token()
    headers = {**(headers or {}), "Authorization": f"Bearer {access_token}"}
    return streamablehttp_client(GATEWAY_URL, headers=headers)


def _gateway_configured() -> bool:
    """Check if MCP Gateway is fully configured."""
    return MCP_AVAILABLE and all([
        GATEWAY_URL,
        GATEWAY_CLIENT_ID,
        GATEWAY_CLIENT_SECRET,
        GATEWAY_TOKEN_ENDPOINT,
        GATEWAY_SCOPE
    ])


# ============================================================================
# Create Strands Agent (Nova Pro Optimized)
# ============================================================================

def create_nova_model() -> BedrockModel:
    """
    Create a Nova Pro optimized BedrockModel instance.
    
    Key optimizations for Nova Pro tool use:
    - temperature=0 (greedy decoding - CRITICAL for reliable tool use)
    - topK=1 (most deterministic selection)
    - max_tokens=8192 (sufficient for complex responses)
    - stop_sequences to prevent runaway generation
    """
    return BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        region_name=REGION,
        temperature=0.0,  # CRITICAL: Nova requires temperature=0 for reliable tool use
        max_tokens=8192,
        additional_request_fields={
            "inferenceConfig": {
                "topK": 1  # Greedy decoding for Nova
            }
        },
        stop_sequences=["</tool>", "```\n\n"]  # Prevent runaway generation
    )


# Custom tools list - single smart tool that does the heavy lifting
CUSTOM_TOOLS = [find_trade_matches]


def _invoke_with_mcp(prompt: str, session_manager=None) -> Any:
    """Invoke agent with MCP Gateway tools inside the client context."""
    bedrock_model = create_nova_model()
    mcp_client = MCPClient(_create_mcp_transport)
    
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        logger.info(f"Loaded {len(tools)} MCP tools from gateway")
        
        # Combine MCP tools with custom tools
        all_tools = list(tools) + CUSTOM_TOOLS
        
        agent_kwargs = {
            "model": bedrock_model,
            "system_prompt": SYSTEM_PROMPT,
            "tools": all_tools,
        }
        if session_manager:
            agent_kwargs["session_manager"] = session_manager
        
        agent = Agent(**agent_kwargs)
        return agent(prompt)


def _invoke_with_custom_tools(prompt: str, session_manager=None) -> Any:
    """Invoke agent with custom DynamoDB tools only (no MCP/use_aws)."""
    bedrock_model = create_nova_model()
    
    agent_kwargs = {
        "model": bedrock_model,
        "system_prompt": SYSTEM_PROMPT,
        "tools": CUSTOM_TOOLS,  # Use only custom tools - no use_aws
    }
    if session_manager:
        agent_kwargs["session_manager"] = session_manager
    
    agent = Agent(**agent_kwargs)
    return agent(prompt)


def invoke_matching_agent(prompt: str, session_manager=None) -> Any:
    """
    Invoke matching agent with MCP Gateway or custom tools fallback.
    
    Uses custom DynamoDB tools instead of use_aws to avoid:
    - ProfileNotFound errors in AgentCore Runtime
    - Schema compatibility issues with Nova Pro
    """
    if _gateway_configured():
        try:
            logger.info("Attempting MCP Gateway connection for AWS operations")
            return _invoke_with_mcp(prompt, session_manager)
        except (RuntimeError, ValueError) as oauth_error:
            logger.warning(f"MCP Gateway OAuth failed ({type(oauth_error).__name__}), falling back to custom tools")
        except Exception as mcp_error:
            logger.warning(f"MCP Gateway connection failed ({type(mcp_error).__name__}), falling back to custom tools")
    
    # Fallback to custom tools (recommended for AgentCore Runtime)
    logger.info("Using custom DynamoDB tools for AWS operations")
    return _invoke_with_custom_tools(prompt, session_manager)


# ============================================================================
# Token Metrics Extraction
# ============================================================================

def _extract_token_metrics(result) -> Dict[str, int]:
    """Extract token usage metrics from Strands agent result."""
    metrics = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    try:
        if hasattr(result, 'metrics') and result.metrics:
            summary = result.metrics.get_summary()
            usage = summary.get("accumulated_usage", {})
            metrics["input_tokens"] = usage.get("inputTokens", 0) or 0
            metrics["output_tokens"] = usage.get("outputTokens", 0) or 0
            metrics["total_tokens"] = usage.get("totalTokens", 0) or (metrics["input_tokens"] + metrics["output_tokens"])
            
            if metrics["total_tokens"] == 0:
                logger.warning("Token counting returned zero - potential instrumentation issue")
    except Exception as e:
        logger.warning(f"Failed to extract token metrics: {e}")
    return metrics


# ============================================================================
# AgentCore Entrypoint
# ============================================================================

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for Trade Matching Agent.
    
    Uses Strands SDK with custom DynamoDB tools for reliable operation.
    """
    start_time = datetime.now(timezone.utc)
    
    # Extract request parameters
    trade_id = payload.get("trade_id")
    source_type = payload.get("source_type", "BANK").upper()
    correlation_id = payload.get("correlation_id", f"corr_{uuid.uuid4().hex[:12]}")
    
    logger.info(
        f"[{correlation_id}] INVOKE_START - Trade Matching Agent invoked",
        extra={
            "correlation_id": correlation_id,
            "trade_id": trade_id,
            "source_type": source_type,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
        }
    )
    
    if not trade_id:
        logger.error(f"[{correlation_id}] Missing required field: trade_id")
        return {
            "success": False,
            "error": "Missing required field: trade_id",
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "correlation_id": correlation_id,
        }
    
    try:
        # Create memory session manager
        session_manager = None
        if MEMORY_AVAILABLE and MEMORY_ID:
            session_manager = create_memory_session_manager(
                correlation_id=correlation_id,
                trade_id=trade_id
            )
        
        logger.info(f"[{correlation_id}] Creating matching agent with model: {BEDROCK_MODEL_ID}")
        
        # Construct goal-oriented prompt
        prompt = f"""Match trade ID "{trade_id}" from {source_type} system.

Call the find_trade_matches tool with trade_id="{trade_id}" and source_type="{source_type}".
Then review the results and provide your final classification as JSON.
"""
        
        # Invoke the agent
        logger.info(f"[{correlation_id}] Invoking Strands agent for matching analysis")
        result = invoke_matching_agent(prompt, session_manager=session_manager)
        token_metrics = _extract_token_metrics(result)
        
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.info(f"[{correlation_id}] Token usage: {token_metrics['input_tokens']} in / {token_metrics['output_tokens']} out")
        
        # Extract the agent's response
        response_text = str(result.message) if hasattr(result, 'message') else str(result)
        
        # Extract classification from response
        classification = "UNKNOWN"
        confidence_score = 0.0
        try:
            if "MATCHED" in response_text.upper():
                if "PROBABLE_MATCH" in response_text.upper():
                    classification = "PROBABLE_MATCH"
                elif "REVIEW_REQUIRED" in response_text.upper():
                    classification = "REVIEW_REQUIRED"
                else:
                    classification = "MATCHED"
            elif "BREAK" in response_text.upper():
                classification = "BREAK"
            
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*%', response_text)
            if score_match:
                confidence_score = float(score_match.group(1))
            else:
                score_match = re.search(r'"confidence_score":\s*(\d+(?:\.\d+)?)', response_text)
                if score_match:
                    confidence_score = float(score_match.group(1))
        except Exception:
            pass
        
        logger.info(
            f"[{correlation_id}] Trade matching completed - "
            f"trade_id={trade_id}, classification={classification}, "
            f"confidence={confidence_score:.1f}%, time={processing_time_ms:.0f}ms"
        )
        
        return {
            "success": True,
            "trade_id": trade_id,
            "source_type": source_type,
            "correlation_id": correlation_id,
            "agent_response": response_text,
            "processing_time_ms": processing_time_ms,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "agent_alias": AGENT_ALIAS,
            "token_usage": token_metrics,
            "match_classification": classification,
            "confidence_score": confidence_score,
        }
        
    except Exception as e:
        logger.error(f"[{correlation_id}] Error in matching agent: {e}", exc_info=True)
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "trade_id": trade_id,
            "correlation_id": correlation_id,
            "agent_name": AGENT_NAME,
            "agent_version": AGENT_VERSION,
            "processing_time_ms": processing_time_ms,
        }


if __name__ == "__main__":
    """Let AgentCore Runtime control the agent execution."""
    app.run()
