"""
Financial Domain Intelligence Features for Enhanced AI Trade Reconciliation

This module provides specialized financial domain knowledge and intelligence capabilities
for OTC trade reconciliation, including:
- Domain-specific prompts and context for OTC trade terminology
- Commodity-specific field recognition and semantic mapping
- Non-standardized market terminology normalization
- Asset class detection and context-aware field prioritization
- Learning mechanisms for new terminology through usage patterns
- Specialized handling for different trading contexts
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class AssetClass(Enum):
    """Enumeration of supported asset classes"""
    COMMODITIES = "commodities"
    FX = "fx"
    RATES = "rates"
    EQUITIES = "equities"
    CREDIT = "credit"
    DERIVATIVES = "derivatives"
    UNKNOWN = "unknown"


class TradingContext(Enum):
    """Enumeration of trading contexts"""
    SPOT = "spot"
    FORWARD = "forward"
    SWAP = "swap"
    OPTION = "option"
    FUTURE = "future"
    STRUCTURED = "structured"
    UNKNOWN = "unknown"


@dataclass
class TerminologyMapping:
    """Represents a terminology mapping with confidence and context"""
    standard_term: str
    alternative_terms: List[str]
    asset_class: AssetClass
    trading_context: Optional[TradingContext] = None
    confidence: float = 1.0
    usage_count: int = 0
    last_used: Optional[datetime] = None
    source: str = "predefined"  # predefined, learned, user_defined


@dataclass
class FieldPriority:
    """Represents field priority for different contexts"""
    field_name: str
    asset_class: AssetClass
    trading_context: TradingContext
    priority_score: float
    criticality: str  # CRITICAL, IMPORTANT, OPTIONAL
    validation_rules: List[str] = field(default_factory=list)


@dataclass
class DomainContext:
    """Represents domain-specific context for trade analysis"""
    asset_class: AssetClass
    trading_context: TradingContext
    market_conventions: Dict[str, Any]
    terminology_mappings: Dict[str, TerminologyMapping]
    field_priorities: List[FieldPriority]
    validation_rules: Dict[str, List[str]]


class FinancialDomainIntelligence:
    """
    Core class providing financial domain intelligence capabilities
    """
    
    def __init__(self):
        self.terminology_mappings: Dict[str, TerminologyMapping] = {}
        self.field_priorities: Dict[str, List[FieldPriority]] = defaultdict(list)
        self.asset_class_patterns: Dict[AssetClass, List[str]] = {}
        self.trading_context_patterns: Dict[TradingContext, List[str]] = {}
        self.usage_statistics: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.learning_enabled = True
        
        # Initialize with predefined domain knowledge
        self._initialize_predefined_mappings()
        self._initialize_asset_class_patterns()
        self._initialize_field_priorities()
    
    def _initialize_predefined_mappings(self):
        """Initialize predefined terminology mappings for OTC trades"""
        
        # Commodities terminology
        commodities_mappings = [
            TerminologyMapping(
                standard_term="settlement_date",
                alternative_terms=["delivery_date", "maturity_date", "expiry_date", "termination_date"],
                asset_class=AssetClass.COMMODITIES,
                trading_context=TradingContext.FORWARD
            ),
            TerminologyMapping(
                standard_term="notional_quantity",
                alternative_terms=["volume", "amount", "size", "total_quantity", "contract_size"],
                asset_class=AssetClass.COMMODITIES
            ),
            TerminologyMapping(
                standard_term="commodity_type",
                alternative_terms=["underlying", "product", "commodity", "asset", "instrument"],
                asset_class=AssetClass.COMMODITIES
            ),
            TerminologyMapping(
                standard_term="fixed_price",
                alternative_terms=["strike_price", "contract_price", "agreed_price", "settlement_price"],
                asset_class=AssetClass.COMMODITIES
            ),
            TerminologyMapping(
                standard_term="counterparty",
                alternative_terms=["buyer", "seller", "client", "customer", "party", "entity"],
                asset_class=AssetClass.COMMODITIES
            ),
        ]
        
        # FX terminology
        fx_mappings = [
            TerminologyMapping(
                standard_term="currency_pair",
                alternative_terms=["ccypair", "ccy_pair", "fx_pair", "pair"],
                asset_class=AssetClass.FX
            ),
            TerminologyMapping(
                standard_term="exchange_rate",
                alternative_terms=["rate", "fx_rate", "spot_rate", "forward_rate"],
                asset_class=AssetClass.FX
            ),
            TerminologyMapping(
                standard_term="base_currency",
                alternative_terms=["base_ccy", "primary_currency", "from_currency"],
                asset_class=AssetClass.FX
            ),
            TerminologyMapping(
                standard_term="quote_currency",
                alternative_terms=["quote_ccy", "counter_currency", "to_currency"],
                asset_class=AssetClass.FX
            ),
        ]
        
        # Rates terminology
        rates_mappings = [
            TerminologyMapping(
                standard_term="interest_rate",
                alternative_terms=["rate", "fixed_rate", "floating_rate", "coupon_rate"],
                asset_class=AssetClass.RATES
            ),
            TerminologyMapping(
                standard_term="day_count_convention",
                alternative_terms=["day_count", "dcc", "accrual_basis", "day_basis"],
                asset_class=AssetClass.RATES
            ),
            TerminologyMapping(
                standard_term="payment_frequency",
                alternative_terms=["frequency", "payment_period", "coupon_frequency"],
                asset_class=AssetClass.RATES
            ),
        ]
        
        # Derivatives terminology
        derivatives_mappings = [
            TerminologyMapping(
                standard_term="underlying_asset",
                alternative_terms=["underlying", "reference_asset", "base_asset"],
                asset_class=AssetClass.DERIVATIVES
            ),
            TerminologyMapping(
                standard_term="option_type",
                alternative_terms=["call_put", "option_style", "exercise_type"],
                asset_class=AssetClass.DERIVATIVES,
                trading_context=TradingContext.OPTION
            ),
            TerminologyMapping(
                standard_term="strike_price",
                alternative_terms=["strike", "exercise_price", "barrier_level"],
                asset_class=AssetClass.DERIVATIVES,
                trading_context=TradingContext.OPTION
            ),
        ]
        
        # Store all mappings
        all_mappings = commodities_mappings + fx_mappings + rates_mappings + derivatives_mappings
        
        for mapping in all_mappings:
            # Store by standard term
            self.terminology_mappings[mapping.standard_term] = mapping
            
            # Store by alternative terms for reverse lookup
            for alt_term in mapping.alternative_terms:
                self.terminology_mappings[alt_term] = mapping
    
    def _initialize_asset_class_patterns(self):
        """Initialize patterns for asset class detection"""
        self.asset_class_patterns = {
            AssetClass.COMMODITIES: [
                r'\b(oil|crude|brent|wti|gas|gold|silver|copper|aluminum|wheat|corn|soy)\b',
                r'\b(commodity|physical|delivery|warehouse|storage)\b',
                r'\b(barrel|bbl|mt|metric.ton|bushel|ounce|oz)\b'
            ],
            AssetClass.FX: [
                r'\b(usd|eur|gbp|jpy|chf|cad|aud|nzd)\b',
                r'\b(fx|foreign.exchange|currency|spot|forward)\b',
                r'\b[A-Z]{3}[A-Z]{3}\b',  # Currency pair pattern
                r'\b(exchange.rate|fx.rate|cross.rate)\b'
            ],
            AssetClass.RATES: [
                r'\b(libor|sofr|euribor|sonia|ois|swap)\b',
                r'\b(interest.rate|fixed.rate|floating.rate)\b',
                r'\b(basis.point|bp|yield|coupon)\b',
                r'\b(irs|interest.rate.swap|bond)\b'
            ],
            AssetClass.DERIVATIVES: [
                r'\b(option|call|put|strike|barrier)\b',
                r'\b(future|forward|swap|derivative)\b',
                r'\b(underlying|exercise|expiry|maturity)\b',
                r'\b(volatility|delta|gamma|theta|vega)\b'
            ],
            AssetClass.EQUITIES: [
                r'\b(stock|equity|share|dividend)\b',
                r'\b(ticker|symbol|cusip|isin)\b',
                r'\b(market.cap|pe.ratio|earnings)\b'
            ],
            AssetClass.CREDIT: [
                r'\b(bond|credit|spread|yield)\b',
                r'\b(rating|default|recovery)\b',
                r'\b(cds|credit.default.swap)\b'
            ]
        }
    
    def _initialize_field_priorities(self):
        """Initialize field priorities for different asset classes and contexts"""
        
        # Commodities field priorities
        commodities_priorities = [
            FieldPriority("trade_date", AssetClass.COMMODITIES, TradingContext.FORWARD, 0.95, "CRITICAL"),
            FieldPriority("settlement_date", AssetClass.COMMODITIES, TradingContext.FORWARD, 0.90, "CRITICAL"),
            FieldPriority("commodity_type", AssetClass.COMMODITIES, TradingContext.FORWARD, 0.85, "CRITICAL"),
            FieldPriority("notional_quantity", AssetClass.COMMODITIES, TradingContext.FORWARD, 0.80, "CRITICAL"),
            FieldPriority("fixed_price", AssetClass.COMMODITIES, TradingContext.FORWARD, 0.75, "IMPORTANT"),
            FieldPriority("counterparty", AssetClass.COMMODITIES, TradingContext.FORWARD, 0.70, "IMPORTANT"),
            FieldPriority("settlement_type", AssetClass.COMMODITIES, TradingContext.FORWARD, 0.60, "IMPORTANT"),
            FieldPriority("unit_of_measure", AssetClass.COMMODITIES, TradingContext.FORWARD, 0.55, "OPTIONAL"),
        ]
        
        # FX field priorities
        fx_priorities = [
            FieldPriority("trade_date", AssetClass.FX, TradingContext.SPOT, 0.95, "CRITICAL"),
            FieldPriority("currency_pair", AssetClass.FX, TradingContext.SPOT, 0.90, "CRITICAL"),
            FieldPriority("exchange_rate", AssetClass.FX, TradingContext.SPOT, 0.85, "CRITICAL"),
            FieldPriority("notional_amount", AssetClass.FX, TradingContext.SPOT, 0.80, "CRITICAL"),
            FieldPriority("settlement_date", AssetClass.FX, TradingContext.FORWARD, 0.85, "CRITICAL"),
            FieldPriority("counterparty", AssetClass.FX, TradingContext.SPOT, 0.70, "IMPORTANT"),
        ]
        
        # Rates field priorities
        rates_priorities = [
            FieldPriority("trade_date", AssetClass.RATES, TradingContext.SWAP, 0.95, "CRITICAL"),
            FieldPriority("effective_date", AssetClass.RATES, TradingContext.SWAP, 0.90, "CRITICAL"),
            FieldPriority("termination_date", AssetClass.RATES, TradingContext.SWAP, 0.90, "CRITICAL"),
            FieldPriority("notional_amount", AssetClass.RATES, TradingContext.SWAP, 0.85, "CRITICAL"),
            FieldPriority("fixed_rate", AssetClass.RATES, TradingContext.SWAP, 0.80, "CRITICAL"),
            FieldPriority("floating_rate_index", AssetClass.RATES, TradingContext.SWAP, 0.75, "IMPORTANT"),
            FieldPriority("payment_frequency", AssetClass.RATES, TradingContext.SWAP, 0.70, "IMPORTANT"),
        ]
        
        # Store priorities by asset class
        for priority in commodities_priorities + fx_priorities + rates_priorities:
            key = f"{priority.asset_class.value}:{priority.trading_context.value}"
            self.field_priorities[key].append(priority)
    
    def detect_asset_class(self, trade_data: Dict[str, Any]) -> Tuple[AssetClass, float]:
        """
        Detect asset class from trade data using pattern matching and field analysis.
        
        Args:
            trade_data: Trade data dictionary
            
        Returns:
            Tuple of (AssetClass, confidence_score)
        """
        scores = defaultdict(float)
        
        # Convert all values to lowercase string for pattern matching
        text_content = " ".join([
            str(v).lower() for v in trade_data.values() 
            if v is not None
        ])
        
        # Score based on pattern matching
        for asset_class, patterns in self.asset_class_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_content, re.IGNORECASE))
                scores[asset_class] += matches * 0.2
        
        # Score based on field presence
        field_indicators = {
            AssetClass.COMMODITIES: [
                "commodity_type", "settlement_type", "unit_of_measure", 
                "fixed_price", "delivery_date"
            ],
            AssetClass.FX: [
                "currency_pair", "exchange_rate", "base_currency", 
                "quote_currency", "spot_rate"
            ],
            AssetClass.RATES: [
                "interest_rate", "floating_rate_index", "day_count_convention",
                "payment_frequency", "fixed_rate"
            ],
            AssetClass.DERIVATIVES: [
                "underlying_asset", "option_type", "strike_price",
                "expiry_date", "exercise_type"
            ],
            AssetClass.EQUITIES: [
                "ticker_symbol", "cusip", "isin", "dividend_rate",
                "market_cap"
            ],
            AssetClass.CREDIT: [
                "credit_rating", "spread", "recovery_rate",
                "default_probability", "bond_type"
            ]
        }
        
        for asset_class, indicator_fields in field_indicators.items():
            field_matches = sum(1 for field in indicator_fields if field in trade_data)
            scores[asset_class] += field_matches * 0.3
        
        # Find best match
        if not scores:
            return AssetClass.UNKNOWN, 0.0
        
        best_class = max(scores.keys(), key=lambda k: scores[k])
        max_score = scores[best_class]
        
        # Normalize confidence score
        confidence = min(max_score / 2.0, 1.0)  # Divide by 2 since max theoretical score is ~2.0
        
        return best_class, confidence
    
    def detect_trading_context(self, trade_data: Dict[str, Any], asset_class: AssetClass) -> Tuple[TradingContext, float]:
        """
        Detect trading context (spot, forward, swap, etc.) from trade data.
        
        Args:
            trade_data: Trade data dictionary
            asset_class: Detected asset class
            
        Returns:
            Tuple of (TradingContext, confidence_score)
        """
        text_content = " ".join([
            str(v).lower() for v in trade_data.values() 
            if v is not None
        ])
        
        context_patterns = {
            TradingContext.SPOT: [
                r'\bspot\b', r'\bimmediate\b', r'\bT\+[0-2]\b'
            ],
            TradingContext.FORWARD: [
                r'\bforward\b', r'\bfuture\b', r'\bdelivery\b', r'\bmaturity\b'
            ],
            TradingContext.SWAP: [
                r'\bswap\b', r'\bexchange\b', r'\bfloating\b', r'\bfixed\b'
            ],
            TradingContext.OPTION: [
                r'\boption\b', r'\bcall\b', r'\bput\b', r'\bstrike\b', r'\bexercise\b'
            ],
            TradingContext.FUTURE: [
                r'\bfuture\b', r'\bcontract\b', r'\bexpiry\b'
            ],
            TradingContext.STRUCTURED: [
                r'\bstructured\b', r'\bcomplex\b', r'\bbarrier\b', r'\bknock\b'
            ]
        }
        
        scores = defaultdict(float)
        
        # Pattern-based scoring
        for context, patterns in context_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_content, re.IGNORECASE))
                scores[context] += matches * 0.4
        
        # Field-based scoring
        field_indicators = {
            TradingContext.SPOT: ["spot_rate", "immediate_settlement"],
            TradingContext.FORWARD: ["forward_rate", "settlement_date", "delivery_date"],
            TradingContext.SWAP: ["floating_rate_index", "payment_frequency", "reset_date"],
            TradingContext.OPTION: ["strike_price", "option_type", "expiry_date", "premium"],
            TradingContext.FUTURE: ["contract_month", "delivery_month", "margin"],
            TradingContext.STRUCTURED: ["barrier_level", "knock_in", "knock_out"]
        }
        
        for context, indicator_fields in field_indicators.items():
            field_matches = sum(1 for field in indicator_fields if field in trade_data)
            scores[context] += field_matches * 0.3
        
        # Asset class specific adjustments
        if asset_class == AssetClass.COMMODITIES:
            if "settlement_date" in trade_data or "delivery_date" in trade_data:
                scores[TradingContext.FORWARD] += 0.2
        elif asset_class == AssetClass.FX:
            if "settlement_date" in trade_data:
                scores[TradingContext.FORWARD] += 0.2
            else:
                scores[TradingContext.SPOT] += 0.2
        elif asset_class == AssetClass.RATES:
            scores[TradingContext.SWAP] += 0.3  # Most rates products are swaps
        
        if not scores:
            return TradingContext.UNKNOWN, 0.0
        
        best_context = max(scores.keys(), key=lambda k: scores[k])
        confidence = min(scores[best_context] / 1.5, 1.0)
        
        return best_context, confidence
    
    def normalize_field_name(self, field_name: str, asset_class: AssetClass, 
                           trading_context: TradingContext = None) -> Tuple[str, float]:
        """
        Normalize field name to standard terminology.
        
        Args:
            field_name: Original field name
            asset_class: Asset class context
            trading_context: Trading context (optional)
            
        Returns:
            Tuple of (normalized_name, confidence_score)
        """
        field_lower = field_name.lower().strip()
        
        # Direct lookup in terminology mappings
        if field_lower in self.terminology_mappings:
            mapping = self.terminology_mappings[field_lower]
            
            # Check if mapping is appropriate for context
            if (mapping.asset_class == asset_class or mapping.asset_class == AssetClass.UNKNOWN):
                if (trading_context is None or 
                    mapping.trading_context is None or 
                    mapping.trading_context == trading_context):
                    
                    # Update usage statistics
                    if self.learning_enabled:
                        self._update_usage_statistics(field_lower, mapping.standard_term)
                    
                    return mapping.standard_term, mapping.confidence
        
        # Fuzzy matching for similar terms
        best_match = None
        best_score = 0.0
        
        for term, mapping in self.terminology_mappings.items():
            if (mapping.asset_class == asset_class or mapping.asset_class == AssetClass.UNKNOWN):
                # Calculate similarity score
                similarity = self._calculate_field_similarity(field_lower, term)
                
                if similarity > 0.7 and similarity > best_score:
                    best_match = mapping.standard_term
                    best_score = similarity
        
        if best_match:
            if self.learning_enabled:
                self._update_usage_statistics(field_lower, best_match)
            return best_match, best_score
        
        # No match found - return original with low confidence
        return field_name, 0.1
    
    def get_field_priorities(self, asset_class: AssetClass, 
                           trading_context: TradingContext) -> List[FieldPriority]:
        """
        Get field priorities for given asset class and trading context.
        
        Args:
            asset_class: Asset class
            trading_context: Trading context
            
        Returns:
            List of FieldPriority objects sorted by priority score
        """
        key = f"{asset_class.value}:{trading_context.value}"
        priorities = self.field_priorities.get(key, [])
        
        # Also include general priorities for the asset class
        general_key = f"{asset_class.value}:unknown"
        general_priorities = self.field_priorities.get(general_key, [])
        
        all_priorities = priorities + general_priorities
        
        # Sort by priority score (descending)
        return sorted(all_priorities, key=lambda p: p.priority_score, reverse=True)
    
    def learn_terminology(self, original_term: str, standard_term: str, 
                         asset_class: AssetClass, trading_context: TradingContext = None,
                         confidence: float = 0.8):
        """
        Learn new terminology mapping from usage patterns.
        
        Args:
            original_term: Original field name or term
            standard_term: Standard/normalized term
            asset_class: Asset class context
            trading_context: Trading context (optional)
            confidence: Confidence in the mapping
        """
        if not self.learning_enabled:
            return
        
        original_lower = original_term.lower().strip()
        
        # Check if mapping already exists
        if original_lower in self.terminology_mappings:
            existing = self.terminology_mappings[original_lower]
            existing.usage_count += 1
            existing.last_used = datetime.now()
            existing.confidence = min(existing.confidence + 0.1, 1.0)
        else:
            # Create new mapping
            new_mapping = TerminologyMapping(
                standard_term=standard_term,
                alternative_terms=[original_lower],
                asset_class=asset_class,
                trading_context=trading_context,
                confidence=confidence,
                usage_count=1,
                last_used=datetime.now(),
                source="learned"
            )
            
            self.terminology_mappings[original_lower] = new_mapping
        
        logger.info(f"Learned terminology mapping: {original_term} -> {standard_term} "
                   f"(asset_class: {asset_class.value}, confidence: {confidence})")
    
    def get_domain_context(self, trade_data: Dict[str, Any]) -> DomainContext:
        """
        Get comprehensive domain context for trade data.
        
        Args:
            trade_data: Trade data dictionary
            
        Returns:
            DomainContext object with asset class, trading context, and relevant mappings
        """
        # Detect asset class and trading context
        asset_class, ac_confidence = self.detect_asset_class(trade_data)
        trading_context, tc_confidence = self.detect_trading_context(trade_data, asset_class)
        
        # Get relevant terminology mappings
        relevant_mappings = {
            term: mapping for term, mapping in self.terminology_mappings.items()
            if (mapping.asset_class == asset_class or mapping.asset_class == AssetClass.UNKNOWN)
        }
        
        # Get field priorities
        field_priorities = self.get_field_priorities(asset_class, trading_context)
        
        # Get market conventions (placeholder for future implementation)
        market_conventions = self._get_market_conventions(asset_class, trading_context)
        
        # Get validation rules
        validation_rules = self._get_validation_rules(asset_class, trading_context)
        
        return DomainContext(
            asset_class=asset_class,
            trading_context=trading_context,
            market_conventions=market_conventions,
            terminology_mappings=relevant_mappings,
            field_priorities=field_priorities,
            validation_rules=validation_rules
        )
    
    def _calculate_field_similarity(self, field1: str, field2: str) -> float:
        """Calculate similarity between two field names"""
        from difflib import SequenceMatcher
        
        # Basic string similarity
        basic_similarity = SequenceMatcher(None, field1, field2).ratio()
        
        # Token-based similarity (split on underscores, spaces, etc.)
        tokens1 = set(re.split(r'[_\s\-\.]+', field1.lower()))
        tokens2 = set(re.split(r'[_\s\-\.]+', field2.lower()))
        
        if tokens1 and tokens2:
            token_similarity = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))
        else:
            token_similarity = 0.0
        
        # Weighted combination
        return 0.6 * basic_similarity + 0.4 * token_similarity
    
    def _update_usage_statistics(self, original_term: str, standard_term: str):
        """Update usage statistics for learning"""
        self.usage_statistics[original_term][standard_term] += 1
    
    def _get_market_conventions(self, asset_class: AssetClass, 
                              trading_context: TradingContext) -> Dict[str, Any]:
        """Get market conventions for asset class and trading context"""
        conventions = {}
        
        if asset_class == AssetClass.COMMODITIES:
            conventions.update({
                "settlement_cycle": "T+2",
                "price_precision": 4,
                "quantity_units": ["MT", "BBL", "OZ", "BUSHEL"],
                "common_currencies": ["USD", "EUR", "GBP"]
            })
        elif asset_class == AssetClass.FX:
            conventions.update({
                "settlement_cycle": "T+2",
                "rate_precision": 6,
                "major_pairs": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"],
                "quotation_convention": "base/quote"
            })
        elif asset_class == AssetClass.RATES:
            conventions.update({
                "day_count_conventions": ["ACT/360", "ACT/365", "30/360"],
                "payment_frequencies": ["QUARTERLY", "SEMI_ANNUAL", "ANNUAL"],
                "rate_precision": 6
            })
        
        return conventions
    
    def _get_validation_rules(self, asset_class: AssetClass, 
                            trading_context: TradingContext) -> Dict[str, List[str]]:
        """Get validation rules for asset class and trading context"""
        rules = {}
        
        if asset_class == AssetClass.COMMODITIES:
            rules.update({
                "trade_date": ["required", "date_format", "not_future"],
                "settlement_date": ["required", "date_format", "after_trade_date"],
                "commodity_type": ["required", "valid_commodity"],
                "notional_quantity": ["required", "positive_number"],
                "fixed_price": ["required", "positive_number"]
            })
        elif asset_class == AssetClass.FX:
            rules.update({
                "trade_date": ["required", "date_format", "not_future"],
                "currency_pair": ["required", "valid_currency_pair"],
                "exchange_rate": ["required", "positive_number"],
                "notional_amount": ["required", "positive_number"]
            })
        
        return rules
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for monitoring and analysis"""
        return {
            "terminology_mappings_count": len(self.terminology_mappings),
            "learned_mappings_count": len([
                m for m in self.terminology_mappings.values() 
                if m.source == "learned"
            ]),
            "usage_statistics": dict(self.usage_statistics),
            "most_used_mappings": self._get_most_used_mappings(),
            "asset_class_distribution": self._get_asset_class_distribution()
        }
    
    def _get_most_used_mappings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently used terminology mappings"""
        mappings_with_usage = [
            {
                "standard_term": mapping.standard_term,
                "usage_count": mapping.usage_count,
                "asset_class": mapping.asset_class.value,
                "confidence": mapping.confidence,
                "source": mapping.source
            }
            for mapping in self.terminology_mappings.values()
            if mapping.usage_count > 0
        ]
        
        return sorted(mappings_with_usage, key=lambda x: x["usage_count"], reverse=True)[:limit]
    
    def _get_asset_class_distribution(self) -> Dict[str, int]:
        """Get distribution of mappings by asset class"""
        distribution = defaultdict(int)
        for mapping in self.terminology_mappings.values():
            distribution[mapping.asset_class.value] += 1
        return dict(distribution)


# Global instance for use across the application
financial_domain_intelligence = FinancialDomainIntelligence()


def get_domain_intelligence() -> FinancialDomainIntelligence:
    """Get the global financial domain intelligence instance"""
    return financial_domain_intelligence


def reset_domain_intelligence():
    """Reset the global domain intelligence instance (useful for testing)"""
    global financial_domain_intelligence
    financial_domain_intelligence = FinancialDomainIntelligence()