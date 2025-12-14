from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime


@dataclass
class Trade:
    """Represents a trade record from either bank or counterparty source."""
    trade_id: str
    source: str  # BANK or COUNTERPARTY
    internal_reference: Optional[str] = None
    trade_date: str = None
    notional: Decimal = None
    currency: str = None
    product_type: str = None
    matched_status: str = "PENDING"  # PENDING, MATCHED, UNMATCHED
    match_id: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Additional fields from trade_attributes.json
    global_uti: Optional[str] = None
    effective_date: Optional[str] = None
    termination_date: Optional[str] = None
    total_notional_quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    fixed_price: Optional[Decimal] = None
    price_unit: Optional[str] = None
    commodity_type: Optional[str] = None
    settlement_type: Optional[str] = None
    business_days_convention: Optional[str] = None
    buyer_legal_entity: Optional[str] = None
    seller_legal_entity: Optional[str] = None
    
    @property
    def composite_key(self) -> str:
        """Generate a composite key for efficient matching."""
        components = []
        if self.trade_date:
            components.append(self.trade_date)
        if self.currency:
            components.append(self.currency)
        if self.notional:
            # Bucket notional into ranges for fuzzy matching
            notional_bucket = f"N{int(self.notional / 1000)}K"
            components.append(notional_bucket)
        if self.product_type:
            components.append(self.product_type)
        
        return "#".join(components) if components else "UNKNOWN"


@dataclass
class TradeMatch:
    """Represents a match between bank and counterparty trades."""
    match_id: str
    bank_trade_id: str
    counterparty_trade_id: str
    similarity_score: float
    reconciliation_status: str = "PENDING"  # PENDING, FULLY_MATCHED, PARTIALLY_MATCHED, CRITICAL_MISMATCH
    field_results: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FieldComparisonResult:
    """Represents the comparison result for a single field."""
    field_name: str
    bank_value: Any
    counterparty_value: Any
    status: str  # MATCHED, MISMATCHED, MISSING
    reason: Optional[str] = None


@dataclass
class ReconciliationResult:
    """Represents the overall reconciliation result for a trade pair."""
    trade_pair_id: str
    match_confidence: float
    field_results: Dict[str, FieldComparisonResult]
    overall_status: str  # FULLY_MATCHED, PARTIALLY_MATCHED, CRITICAL_MISMATCH


@dataclass
class MatcherConfig:
    """Configuration for the trade matcher."""
    weights: Dict[str, float] = field(default_factory=lambda: {
        "trade_date": 0.30,
        "counterparty_name": 0.20,
        "notional": 0.25,
        "currency": 0.15,
        "product_type": 0.10
    })
    threshold: float = 0.90  # Minimum score to consider a match
    conflict_band: float = 0.02  # Band for flagging multiple close matches


@dataclass
class ReconcilerConfig:
    """Configuration for the field reconciler."""
    numeric_tolerance: Dict[str, float] = field(default_factory=lambda: {
        "notional": 0.001,  # 0.1% tolerance
        "fixed_price": 0.0001  # 0.01% tolerance
    })
    critical_fields: List[str] = field(default_factory=lambda: [
        "trade_date", "notional", "currency"
    ])
    string_similarity_threshold: float = 0.85


@dataclass
class TableConfig:
    """Configuration for DynamoDB table names."""
    bank_trades_table: str = "BankTradeData"
    counterparty_trades_table: str = "CounterpartyTradeData" 
    trade_matches_table: str = "TradeMatches"
    
    @classmethod
    def from_environment(cls):
        """Create configuration from environment variables."""
        import os
        return cls(
            bank_trades_table=os.getenv('BANK_TRADES_TABLE', 'BankTradeData'),
            counterparty_trades_table=os.getenv('COUNTERPARTY_TRADES_TABLE', 'CounterpartyTradeData'),
            trade_matches_table=os.getenv('TRADE_MATCHES_TABLE', 'TradeMatches')
        )


@dataclass
class ReportConfig:
    """Configuration for the report generator."""
    report_bucket: str = "trade-reconciliation-reports"
    include_summary_stats: bool = True
    include_field_details: bool = True
