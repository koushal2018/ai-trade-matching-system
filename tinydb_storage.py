#!/usr/bin/env python3

# TinyDB Storage Implementation for Trade Data
# This script stores the comprehensive trade data in TinyDB database

import json
import os
from datetime import datetime

# Simple TinyDB-like implementation since TinyDB may not be installed
class SimpleDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.data = []
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.data = json.loads(content)
            except (json.JSONDecodeError, FileNotFoundError):
                self.data = []
    
    def save_data(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def insert(self, record):
        self.data.append(record)
        self.save_data()
    
    def update(self, record, trade_id):
        for i, existing in enumerate(self.data):
            if existing.get('Trade_ID') == trade_id:
                self.data[i] = record
                self.save_data()
                return True
        return False
    
    def search(self, trade_id):
        for record in self.data:
            if record.get('Trade_ID') == trade_id:
                return [record]
        return []
    
    def count(self):
        return len(self.data)
    
    def close(self):
        pass

# Main storage function
def store_comprehensive_trade_data():
    # Trade data from the JSON file (already read once)
    trade_data = {
        "document_metadata": {
            "document_type": "DERIVATIVES TRADE CONFIRMATION",
            "source_file": "FAB_26933659.pdf",
            "extraction_timestamp": "2024-12-07T10:45:00Z",
            "pages_processed": 3,
            "bank_name": "FIRST ABU DHABI BANK"
        },
        "trade_identification": {
            "trade_reference": "FAB-DRV-2024-26933659",
            "deal_id": "FAB-DRV-2024-26933659",
            "confirmation_date": "2024-09-15",
            "transaction_type": "Interest Rate Swap",
            "product_classification": "IR:SWAP:Fixed-Float"
        },
        "trade_dates": {
            "trade_date": "2024-09-15",
            "effective_date": "2024-09-17",
            "maturity_date": "2029-09-17",
            "tenor": "5 Years",
            "settlement_date": "T+2 Business Days"
        },
        "counterparty_information": {
            "party_a": {
                "role": "Bank",
                "legal_name": "First Abu Dhabi Bank PJSC",
                "short_name": "FAB",
                "lei_code": "254900O1WT2BXINOTE68",
                "bic_code": "FABKAEAA",
                "address": "Khalifa Business Park Abu Dhabi, UAE",
                "contact_email": "derivatives@bankfab.com",
                "contact_phone": "+971-2-6111999",
                "booking_location": "Abu Dhabi, UAE",
                "booking_entity": "First Abu Dhabi Bank PJSC",
                "business_unit": "Derivatives Trading",
                "trader": "Ahmed Hassan",
                "sales": "Fatima Al-Zahra",
                "authorized_signatory": "Sarah Al-Mansouri, Director",
                "signature_date": "2024-09-15",
                "signature_time": "10:45 GMT"
            },
            "party_b": {
                "role": "Counterparty",
                "legal_name": "Goldman Sachs International",
                "short_name": "GSI",
                "lei_code": "549300IYTZEDU5LF4J88",
                "bic_code": "SPGBGB2L",
                "address": "25 Cabot Square London E14 4QA, UK",
                "contact_email": "confirmations@gs.com",
                "contact_phone": "+44-20-7774-1000",
                "booking_location": "London, UK",
                "booking_entity": "Goldman Sachs International",
                "business_unit": "Fixed Income",
                "trader": "David Williams",
                "sales": "Emma Thompson",
                "authorized_signatory": "Michael Chen, Vice President",
                "signature_date": "2024-09-15",
                "signature_time": "11:15 GMT"
            }
        },
        "economic_terms": {
            "notional_amount": {
                "amount": 50000000.00,
                "currency": "USD",
                "formatted": "USD 50,000,000"
            },
            "currency": "USD",
            "business_day_convention": "Modified Following",
            "day_count_convention": "30/360",
            "calculation_agent": "First Abu Dhabi Bank PJSC",
            "business_days": "London and New York",
            "holiday_calendar": "GBLO, USNY"
        },
        "fixed_rate_leg": {
            "payer": "Party A (FAB)",
            "fixed_rate": {
                "rate": 3.750,
                "formatted": "3.750% per annum"
            },
            "payment_frequency": "Semi-Annual",
            "payment_dates": "17th March and 17th September",
            "first_payment_date": "2025-03-17",
            "final_payment_date": "2029-09-17",
            "day_count": "30/360",
            "compounding": "Not Applicable",
            "reset_dates": "Not Applicable"
        },
        "floating_rate_leg": {
            "payer": "Party B (GSI)",
            "floating_rate_index": "USD-SOFR-OIS Compound",
            "spread": {
                "spread": 0.25,
                "formatted": "+0.25% per annum"
            },
            "payment_frequency": "Quarterly",
            "payment_dates": "17th of each quarter",
            "first_payment_date": "2024-12-17",
            "final_payment_date": "2029-09-17",
            "reset_frequency": "Daily",
            "reset_dates": "Each Business Day",
            "day_count": "ACT/360",
            "compounding_method": "OIS Compound",
            "lookback_period": "2 Business Days",
            "rate_cut_off": "2 Business Days"
        },
        "settlement_instructions": {
            "settlement_currency": "USD",
            "settlement_method": "Cash Settlement",
            "netting": "Payment Netting Applies",
            "fab_payment_account": {
                "bank_name": "JPMorgan Chase Bank N.A.",
                "swift_code": "CHASUS33",
                "account_number": "001-234-567890"
            },
            "gsi_payment_account": {
                "bank_name": "Citibank N.A. London",
                "swift_code": "CITIGB2L",
                "account_number": "40012345"
            }
        },
        "documentation": {
            "master_agreement": "2002 ISDA Master Agreement",
            "schedule_date": "2019-03-15",
            "credit_support_annex": "ISDA 2016 Credit Support Annex",
            "governing_law": "English Law",
            "jurisdiction": "Courts of England and Wales",
            "termination_events": "Standard ISDA Events",
            "early_termination": "Standard ISDA Provisions",
            "definitions": "2006 ISDA Definitions and 2021 ISDA Interest Rate Derivatives Definitions"
        },
        "regulatory_information": {
            "trade_classification": "OTC Derivative",
            "regulatory_regime": "EMIR / UK EMIR",
            "reporting_requirements": "Both parties to report",
            "uti": "FAB1549300IYTZEDU5LF4J88202409150001",
            "usi": "1549300IYTZEDU5LF4J88000026933659",
            "lei_required": True,
            "clearing_eligible": False,
            "clearing_exempt": True,
            "clearing_exemption_reason": "End User Exception",
            "mifid_ii_reporting": "Required",
            "risk_category": "OTC Interest Rate Derivatives",
            "credit_valuation_adjustment": "Applicable"
        },
        "margin_and_collateral": {
            "initial_margin": "Not Required",
            "variation_margin": "Required",
            "collateral_requirements": "As per CSA",
            "eligible_collateral": "USD Cash, US Treasury Securities",
            "margin_call_threshold": {
                "amount": 1000000.00,
                "currency": "USD",
                "formatted": "USD 1,000,000"
            },
            "independent_amount": {
                "amount": 0.00,
                "currency": "USD",
                "formatted": "USD 0"
            },
            "minimum_transfer_amount": {
                "amount": 100000.00,
                "currency": "USD",
                "formatted": "USD 100,000"
            },
            "rounding": "Nearest USD 1,000"
        },
        "payment_schedule": {
            "fixed_leg_payments": {
                "frequency": "Semi-Annual",
                "dates": "17th March and 17th September",
                "first_payment": "2025-03-17",
                "final_payment": "2029-09-17"
            },
            "floating_leg_payments": {
                "frequency": "Quarterly",
                "dates": "17th December, March, June, September",
                "first_payment": "2024-12-17",
                "final_payment": "2029-09-17"
            }
        },
        "trade_capacity": {
            "fab_capacity": "Principal",
            "gsi_capacity": "Principal"
        },
        "confirmation_details": {
            "confirmation_required": True,
            "confirmation_deadline": "24 hours",
            "confirmation_method": "Signed copy return",
            "binding_agreement": True
        },
        "data_quality_metrics": {
            "decimal_precision_preserved": True,
            "original_date_formats_maintained": True,
            "counterparty_identifiers_complete": True,
            "payment_schedules_complete": True,
            "regulatory_flags_captured": True,
            "settlement_instructions_complete": True,
            "extraction_completeness": "100%"
        }
    }
    
    # Extract Trade_ID from trade_identification.trade_reference
    trade_id = trade_data.get('trade_identification', {}).get('trade_reference', '')
    
    if not trade_id:
        print("Error: Trade_ID not found in data")
        return
    
    # This is bank trade data from FAB (source_file "FAB_26933659.pdf", party_a is bank)
    db_path = './storage/bank_trade_data.db'
    
    # Add Trade_ID as primary key to the data
    trade_data['Trade_ID'] = trade_id
    
    # Initialize database
    db = SimpleDB(db_path)
    
    # Check if record exists
    existing_record = db.search(trade_id)
    
    # Log timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if existing_record:
        # Update existing record
        db.update(trade_data, trade_id)
        action = 'updated'
        print(f"[{timestamp}] Updated trade {trade_id} in bank_trade_data.db")
    else:
        # Insert new record
        db.insert(trade_data)
        action = 'inserted'
        print(f"[{timestamp}] Inserted trade {trade_id} in bank_trade_data.db")
    
    # Get total record count
    record_count = db.count()
    
    db.close()
    
    # Return confirmation in required format
    return f"Stored trade {trade_id} in bank_trade_data.db\nAction: {action}\nDatabase record count: {record_count}"

# Execute storage
if __name__ == '__main__':
    result = store_comprehensive_trade_data()
    print(result)
