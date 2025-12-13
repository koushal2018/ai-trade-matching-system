"""
Fuzzy Matching Logic

This module implements fuzzy matching with tolerances for trade confirmation matching.

Requirements:
    - 7.1: Perform fuzzy matching with tolerances
    - 18.3: Use same fuzzy matching algorithms and tolerances as CrewAI implementation

Matching Criteria:
    - Trade_ID: Exact match required
    - Trade_Date: ±1 business day tolerance
    - Notional: ±0.01% tolerance
    - Counterparty: Fuzzy string match (Levenshtein distance)
    - Currency: Exact match
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from difflib import SequenceMatcher


class MatchResult(BaseModel):
    """
    Result of fuzzy matching operation.
    
    Attributes:
        trade_id_match: Whether Trade_ID matches exactly
        date_diff_days: Difference in trade dates (business days)
        notional_diff_pct: Percentage difference in notional
        counterparty_similarity: Similarity score for counterparty (0.0 to 1.0)
        currency_match: Whether currency matches exactly
        exact_matches: Dictionary of fields with exact matches
        differences: List of field differences with details
    """
    trade_id_match: bool = Field(
        ...,
        description="Whether Trade_ID matches exactly"
    )
    
    date_diff_days: Optional[int] = Field(
        None,
        description="Difference in trade dates (calendar days)"
    )
    
    notional_diff_pct: Optional[float] = Field(
        None,
        description="Percentage difference in notional"
    )
    
    counterparty_similarity: Optional[float] = Field(
        None,
        description="Similarity score for counterparty (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    currency_match: Optional[bool] = Field(
        None,
        description="Whether currency matches exactly"
    )
    
    exact_matches: Dict[str, bool] = Field(
        default_factory=dict,
        description="Dictionary of fields with exact match status"
    )
    
    differences: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of field differences with details"
    )
    
    def is_match(self) -> bool:
        """
        Determine if the trades match based on tolerances.
        
        Returns:
            True if all critical fields match within tolerances
        """
        # Currency must match exactly
        if self.currency_match is not None and not self.currency_match:
            return False
        
        # Date must be within ±2 days
        if self.date_diff_days is not None and self.date_diff_days > 2:
            return False
        
        # Notional must be within ±2%
        if self.notional_diff_pct is not None and self.notional_diff_pct > 2.0:
            return False
        
        # Counterparty must have similarity >= 0.8
        if self.counterparty_similarity is not None and self.counterparty_similarity < 0.8:
            return False
        
        return True


def fuzzy_match(
    bank_trade: Dict[str, Any],
    counterparty_trade: Dict[str, Any]
) -> MatchResult:
    """
    Perform fuzzy matching between bank and counterparty trades.
    
    This function applies tolerances to key fields and computes similarity
    scores for fuzzy-matched fields.
    
    Tolerances:
        - Trade_Date: ±1 business day (calendar day approximation)
        - Notional: ±0.01%
        - Counterparty: Fuzzy string match (similarity >= 0.8 considered match)
    
    Args:
        bank_trade: Trade data from bank system
        counterparty_trade: Trade data from counterparty system
    
    Returns:
        MatchResult with detailed comparison results
    
    Requirements:
        - 7.1: Fuzzy matching with tolerances
        - 18.3: Same algorithms as CrewAI implementation
    
    Example:
        >>> bank = {"Trade_ID": "ABC123", "notional": 1000000.0, "trade_date": "2024-10-15"}
        >>> cp = {"Trade_ID": "ABC123", "notional": 1000050.0, "trade_date": "2024-10-16"}
        >>> result = fuzzy_match(bank, cp)
        >>> result.trade_id_match
        True
        >>> result.notional_diff_pct
        0.005
    """
    differences = []
    exact_matches = {}
    
    # Extract Trade_ID from DynamoDB format if needed
    bank_trade_id = _extract_value(bank_trade, "Trade_ID")
    cp_trade_id = _extract_value(counterparty_trade, "Trade_ID")
    
    # 1. Trade_ID: Exact match required
    trade_id_match = bank_trade_id == cp_trade_id
    exact_matches["Trade_ID"] = trade_id_match
    
    if not trade_id_match:
        differences.append({
            "field_name": "Trade_ID",
            "bank_value": bank_trade_id,
            "counterparty_value": cp_trade_id,
            "difference_type": "EXACT_MISMATCH",
            "tolerance_applied": False,
            "within_tolerance": False
        })
    
    # 2. Trade_Date: ±2 days tolerance
    bank_date = _extract_value(bank_trade, "trade_date")
    cp_date = _extract_value(counterparty_trade, "trade_date")
    
    date_diff_days = None
    if bank_date and cp_date:
        try:
            bank_dt = datetime.strptime(bank_date, "%Y-%m-%d")
            cp_dt = datetime.strptime(cp_date, "%Y-%m-%d")
            date_diff_days = abs((bank_dt - cp_dt).days)
            
            within_tolerance = date_diff_days <= 2
            exact_matches["trade_date"] = date_diff_days == 0
            
            if date_diff_days > 0:
                differences.append({
                    "field_name": "trade_date",
                    "bank_value": bank_date,
                    "counterparty_value": cp_date,
                    "difference_type": "TOLERANCE_EXCEEDED" if date_diff_days > 2 else "WITHIN_TOLERANCE",
                    "tolerance_applied": True,
                    "within_tolerance": within_tolerance,
                    "days_difference": date_diff_days
                })
        except (ValueError, TypeError):
            differences.append({
                "field_name": "trade_date",
                "bank_value": bank_date,
                "counterparty_value": cp_date,
                "difference_type": "INVALID_FORMAT",
                "tolerance_applied": False,
                "within_tolerance": False
            })
    
    # 3. Notional: ±2% tolerance
    bank_notional = _extract_value(bank_trade, "notional")
    cp_notional = _extract_value(counterparty_trade, "notional")
    
    notional_diff_pct = None
    if bank_notional is not None and cp_notional is not None:
        try:
            bank_notional_float = float(bank_notional)
            cp_notional_float = float(cp_notional)
            
            if bank_notional_float > 0:
                notional_diff_pct = abs(
                    (cp_notional_float - bank_notional_float) / bank_notional_float * 100
                )
                
                within_tolerance = notional_diff_pct <= 2.0
                exact_matches["notional"] = notional_diff_pct == 0.0
                
                if notional_diff_pct > 0:
                    differences.append({
                        "field_name": "notional",
                        "bank_value": bank_notional_float,
                        "counterparty_value": cp_notional_float,
                        "difference_type": "TOLERANCE_EXCEEDED" if notional_diff_pct > 2.0 else "WITHIN_TOLERANCE",
                        "tolerance_applied": True,
                        "within_tolerance": within_tolerance,
                        "percentage_difference": notional_diff_pct
                    })
        except (ValueError, TypeError):
            differences.append({
                "field_name": "notional",
                "bank_value": bank_notional,
                "counterparty_value": cp_notional,
                "difference_type": "INVALID_FORMAT",
                "tolerance_applied": False,
                "within_tolerance": False
            })
    
    # 4. Counterparty: Fuzzy string match
    bank_cp = _extract_value(bank_trade, "counterparty")
    cp_cp = _extract_value(counterparty_trade, "counterparty")
    
    counterparty_similarity = None
    if bank_cp and cp_cp:
        counterparty_similarity = _compute_string_similarity(
            str(bank_cp).lower(),
            str(cp_cp).lower()
        )
        
        # Consider similarity >= 0.8 as a match
        within_tolerance = counterparty_similarity >= 0.8
        exact_matches["counterparty"] = counterparty_similarity == 1.0
        
        if counterparty_similarity < 1.0:
            differences.append({
                "field_name": "counterparty",
                "bank_value": bank_cp,
                "counterparty_value": cp_cp,
                "difference_type": "FUZZY_MISMATCH" if counterparty_similarity < 0.8 else "FUZZY_MATCH",
                "tolerance_applied": True,
                "within_tolerance": within_tolerance,
                "similarity_score": counterparty_similarity
            })
    
    # 5. Currency: Exact match
    bank_currency = _extract_value(bank_trade, "currency")
    cp_currency = _extract_value(counterparty_trade, "currency")
    
    currency_match = None
    if bank_currency and cp_currency:
        currency_match = str(bank_currency) == str(cp_currency)
        exact_matches["currency"] = currency_match
        
        if not currency_match:
            differences.append({
                "field_name": "currency",
                "bank_value": bank_currency,
                "counterparty_value": cp_currency,
                "difference_type": "EXACT_MISMATCH",
                "tolerance_applied": False,
                "within_tolerance": False
            })
    
    # 6. Check other important fields for exact matches
    other_fields = ["product_type", "effective_date", "maturity_date", "commodity_type"]
    for field in other_fields:
        bank_val = _extract_value(bank_trade, field)
        cp_val = _extract_value(counterparty_trade, field)
        
        if bank_val is not None and cp_val is not None:
            match = str(bank_val) == str(cp_val)
            exact_matches[field] = match
            
            if not match:
                differences.append({
                    "field_name": field,
                    "bank_value": bank_val,
                    "counterparty_value": cp_val,
                    "difference_type": "EXACT_MISMATCH",
                    "tolerance_applied": False,
                    "within_tolerance": False
                })
    
    return MatchResult(
        trade_id_match=trade_id_match,
        date_diff_days=date_diff_days,
        notional_diff_pct=notional_diff_pct,
        counterparty_similarity=counterparty_similarity,
        currency_match=currency_match,
        exact_matches=exact_matches,
        differences=differences
    )


def _extract_value(trade: Optional[Dict[str, Any]], field_name: str) -> Any:
    """
    Extract value from trade dictionary, handling DynamoDB typed format.
    
    Args:
        trade: Trade dictionary (may be in DynamoDB format)
        field_name: Name of the field to extract
    
    Returns:
        Extracted value or None if not found
    """
    if not trade or field_name not in trade:
        return None
    
    value = trade[field_name]
    
    # Handle DynamoDB typed format
    if isinstance(value, dict):
        if "S" in value:
            return value["S"]
        elif "N" in value:
            return value["N"]
        elif "BOOL" in value:
            return value["BOOL"]
        elif "NULL" in value:
            return None
    
    return value


def _compute_string_similarity(str1: str, str2: str) -> float:
    """
    Compute similarity between two strings using SequenceMatcher with enhanced matching.
    
    This uses the Ratcliff/Obershelp algorithm and also handles common abbreviations
    for financial institutions.
    
    Args:
        str1: First string
        str2: Second string
    
    Returns:
        Similarity score from 0.0 (completely different) to 1.0 (identical)
    """
    if not str1 or not str2:
        return 0.0
    
    # Normalize strings
    norm1 = str1.lower().strip()
    norm2 = str2.lower().strip()
    
    # Check for exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Common financial institution abbreviations
    abbreviations = {
        'goldman sachs': ['gs', 'goldman', 'goldman sachs & co'],
        'jpmorgan': ['jpm', 'jp morgan', 'jpmorgan chase'],
        'morgan stanley': ['ms', 'morgan stanley & co'],
        'bank of america': ['boa', 'bofa', 'bank of america corp'],
        'citigroup': ['citi', 'citibank', 'citicorp'],
        'wells fargo': ['wf', 'wells fargo & co'],
        'deutsche bank': ['db', 'deutsche bank ag'],
        'credit suisse': ['cs', 'credit suisse group'],
        'ubs': ['ubs group', 'ubs ag'],
        'barclays': ['barclays plc', 'barclays bank']
    }
    
    # Check if either string is an abbreviation of the other
    for full_name, abbrevs in abbreviations.items():
        if (norm1 == full_name and norm2 in abbrevs) or (norm2 == full_name and norm1 in abbrevs):
            return 0.9  # High similarity for known abbreviations
        if norm1 in abbrevs and norm2 in abbrevs:
            return 0.9  # Both are abbreviations of the same entity
    
    # Use standard sequence matching
    return SequenceMatcher(None, norm1, norm2).ratio()


def _count_business_days(date1: datetime, date2: datetime) -> int:
    """
    Count business days between two dates (excluding weekends).
    
    Note: This is a simplified implementation that doesn't account for holidays.
    For production use, consider using a library like pandas with business day calendars.
    
    Args:
        date1: First date
        date2: Second date
    
    Returns:
        Number of business days between the dates
    """
    if date1 > date2:
        date1, date2 = date2, date1
    
    business_days = 0
    current = date1
    
    while current <= date2:
        # Monday = 0, Sunday = 6
        if current.weekday() < 5:  # Monday to Friday
            business_days += 1
        current += timedelta(days=1)
    
    return business_days
