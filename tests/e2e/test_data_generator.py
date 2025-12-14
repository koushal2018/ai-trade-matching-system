"""Test data generator for end-to-end integration tests."""

import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TradeData:
    """Generated trade data for testing."""
    trade_id: str
    bank_trade: Dict[str, Any]
    counterparty_trade: Dict[str, Any]
    expected_match: bool
    expected_classification: str
    mismatch_fields: List[str]


class TestDataGenerator:
    """Generates synthetic trade data for testing."""
    
    COUNTERPARTIES = [
        "Goldman Sachs", "JP Morgan", "Morgan Stanley", "Citibank",
        "Bank of America", "Deutsche Bank", "Barclays", "HSBC"
    ]
    
    CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD"]
    
    PRODUCT_TYPES = [
        "Interest Rate Swap", "FX Forward", "Commodity Swap",
        "Credit Default Swap", "Equity Option", "FX Option"
    ]
    
    COMMODITY_TYPES = ["Crude Oil", "Natural Gas", "Gold", "Silver", "Copper"]
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
    
    def generate_trade_id(self) -> str:
        """Generate a unique trade ID."""
        prefix = random.choice(["TRD", "SWP", "FWD", "OPT"])
        number = "".join(random.choices(string.digits, k=8))
        return f"{prefix}{number}"
    
    def generate_base_trade(self, trade_id: str, source_type: str) -> Dict[str, Any]:
        """Generate a base trade with all fields."""
        trade_date = datetime.now() - timedelta(days=random.randint(0, 30))
        effective_date = trade_date + timedelta(days=random.randint(1, 5))
        maturity_date = effective_date + timedelta(days=random.randint(30, 365))
        
        return {
            "Trade_ID": trade_id,
            "TRADE_SOURCE": source_type,
            "trade_date": trade_date.strftime("%Y-%m-%d"),
            "effective_date": effective_date.strftime("%Y-%m-%d"),
            "maturity_date": maturity_date.strftime("%Y-%m-%d"),
            "notional": round(random.uniform(100000, 10000000), 2),
            "currency": random.choice(self.CURRENCIES),
            "counterparty": random.choice(self.COUNTERPARTIES),
            "product_type": random.choice(self.PRODUCT_TYPES),
            "commodity_type": random.choice(self.COMMODITY_TYPES) if random.random() > 0.5 else None,
            "settlement_type": random.choice(["Physical", "Cash"]),
        }
    
    def generate_matching_pair(self, trade_id: Optional[str] = None) -> TradeData:
        """Generate a perfectly matching trade pair."""
        trade_id = trade_id or self.generate_trade_id()
        bank_trade = self.generate_base_trade(trade_id, "BANK")
        counterparty_trade = bank_trade.copy()
        counterparty_trade["TRADE_SOURCE"] = "COUNTERPARTY"
        
        return TradeData(
            trade_id=trade_id,
            bank_trade=bank_trade,
            counterparty_trade=counterparty_trade,
            expected_match=True,
            expected_classification="MATCHED",
            mismatch_fields=[]
        )

    
    def generate_probable_match_pair(self, trade_id: Optional[str] = None) -> TradeData:
        """Generate a trade pair with minor differences (probable match)."""
        trade_id = trade_id or self.generate_trade_id()
        bank_trade = self.generate_base_trade(trade_id, "BANK")
        counterparty_trade = bank_trade.copy()
        counterparty_trade["TRADE_SOURCE"] = "COUNTERPARTY"
        
        mismatch_fields = []
        
        # Introduce minor date difference (within tolerance)
        if random.random() > 0.5:
            original_date = datetime.strptime(bank_trade["trade_date"], "%Y-%m-%d")
            new_date = original_date + timedelta(days=1)
            counterparty_trade["trade_date"] = new_date.strftime("%Y-%m-%d")
            mismatch_fields.append("trade_date")
        
        return TradeData(
            trade_id=trade_id,
            bank_trade=bank_trade,
            counterparty_trade=counterparty_trade,
            expected_match=True,
            expected_classification="PROBABLE_MATCH",
            mismatch_fields=mismatch_fields
        )
    
    def generate_break_pair(self, trade_id: Optional[str] = None) -> TradeData:
        """Generate a trade pair with significant differences (break)."""
        trade_id = trade_id or self.generate_trade_id()
        bank_trade = self.generate_base_trade(trade_id, "BANK")
        counterparty_trade = bank_trade.copy()
        counterparty_trade["TRADE_SOURCE"] = "COUNTERPARTY"
        
        mismatch_fields = []
        
        # Introduce significant notional difference
        counterparty_trade["notional"] = bank_trade["notional"] * 1.1  # 10% difference
        mismatch_fields.append("notional")
        
        # Different counterparty name
        counterparty_trade["counterparty"] = random.choice(
            [c for c in self.COUNTERPARTIES if c != bank_trade["counterparty"]]
        )
        mismatch_fields.append("counterparty")
        
        return TradeData(
            trade_id=trade_id,
            bank_trade=bank_trade,
            counterparty_trade=counterparty_trade,
            expected_match=False,
            expected_classification="BREAK",
            mismatch_fields=mismatch_fields
        )
    
    def generate_data_error_pair(self, trade_id: Optional[str] = None) -> TradeData:
        """Generate a trade pair with data quality issues."""
        trade_id = trade_id or self.generate_trade_id()
        bank_trade = self.generate_base_trade(trade_id, "BANK")
        counterparty_trade = bank_trade.copy()
        counterparty_trade["TRADE_SOURCE"] = "COUNTERPARTY"
        
        # Remove required field
        del counterparty_trade["notional"]
        
        return TradeData(
            trade_id=trade_id,
            bank_trade=bank_trade,
            counterparty_trade=counterparty_trade,
            expected_match=False,
            expected_classification="DATA_ERROR",
            mismatch_fields=["notional"]
        )
    
    def generate_test_dataset(
        self,
        matched_count: int = 5,
        probable_count: int = 3,
        break_count: int = 2,
        error_count: int = 1
    ) -> List[TradeData]:
        """Generate a complete test dataset with various scenarios."""
        dataset = []
        
        for _ in range(matched_count):
            dataset.append(self.generate_matching_pair())
        
        for _ in range(probable_count):
            dataset.append(self.generate_probable_match_pair())
        
        for _ in range(break_count):
            dataset.append(self.generate_break_pair())
        
        for _ in range(error_count):
            dataset.append(self.generate_data_error_pair())
        
        random.shuffle(dataset)
        return dataset
    
    def export_to_json(self, dataset: List[TradeData], output_dir: str) -> Tuple[str, str]:
        """Export dataset to JSON files for bank and counterparty trades."""
        bank_trades = [td.bank_trade for td in dataset]
        cp_trades = [td.counterparty_trade for td in dataset]
        
        bank_file = f"{output_dir}/bank_trades.json"
        cp_file = f"{output_dir}/counterparty_trades.json"
        
        with open(bank_file, "w") as f:
            json.dump(bank_trades, f, indent=2)
        
        with open(cp_file, "w") as f:
            json.dump(cp_trades, f, indent=2)
        
        return bank_file, cp_file


# Convenience function
def generate_test_data(seed: int = 42) -> List[TradeData]:
    """Generate a standard test dataset."""
    generator = TestDataGenerator(seed=seed)
    return generator.generate_test_dataset()
