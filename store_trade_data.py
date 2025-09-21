#!/usr/bin/env python3
import json
import os
from datetime import datetime
from tinydb import TinyDB, Query

# Create storage directory if it doesn't exist
storage_dir = './storage'
os.makedirs(storage_dir, exist_ok=True)

# Trade data from the context
trade_data = {
  "document_metadata": {
    "source_document": "GCS381315_V1.pdf",
    "extraction_timestamp": "2024-12-12T15:30:00Z",
    "extraction_method": "OCR",
    "pages_processed": 3,
    "document_version": "V1",
    "data_integrity_hash": "GCS381315_V1_EXTRACTED",
    "extraction_confidence": "HIGH"
  },
  "trade_identification": {
    "trade_id": "GCS381315-V1",
    "gsi_reference": "GCS381315-V1",
    "client_reference": "FAB-DRV-2024-26933659",
    "deal_date": "15 September 2024",
    "trade_date": "15-Sep-2024",
    "effective_date": "17-Sep-2024",
    "termination_date": "17-Sep-2029",
    "product_type": "Interest Rate Swap",
    "asset_class": "OTC Derivatives"
  },
  "counterparty_details": {
    "dealer": {
      "entity_name": "Goldman Sachs International",
      "entity_type": "Dealer",
      "lei_code": "549300IYTZEDU5LF4J88",
      "swift_code": "SPGBGB2L",
      "business_address": "25 Cabot Square, Canary Wharf London E14 4QA United Kingdom",
      "operational_contact": {
        "email": "gs-derivatives-ops@gs.com",
        "phone": "+44-207-774-4000"
      },
      "credit_line": "Internal Allocation"
    },
    "client": {
      "entity_name": "First Abu Dhabi Bank PJSC",
      "entity_type": "Client",
      "lei_code": "2549000O1WT2BXINQTE68",
      "swift_code": "FABKAEAA",
      "business_address": "Khalifa Business Park Abu Dhabi United Arab Emirates",
      "operational_contact": {
        "email": "derivatives@bankfab.com",
        "phone": "+971-2-611-1999"
      },
      "credit_line": "USD 100,000,000"
    }
  },
  "economic_terms": {
    "notional_principal": {
      "amount": 50000000.00,
      "currency": "USD",
      "formatted_amount": "USD 50,000,000.00"
    },
    "trade_currency": "United States Dollar (USD)",
    "calculation_agent": "Goldman Sachs International",
    "business_day_centers": ["New York", "London"],
    "business_day_convention": "Modified Following"
  },
  "fixed_leg_details": {
    "payer": "First Abu Dhabi Bank PJSC",
    "receiver": "Goldman Sachs International",
    "fixed_rate": {
      "rate_percentage": 3.75000,
      "rate_decimal": 0.0375,
      "formatted_rate": "3.75000% per annum"
    },
    "day_count_fraction": "30/360",
    "payment_frequency": "Semi-Annual",
    "payment_schedule": {
      "payment_dates": "17-Mar and 17-Sep of each year starting 17-Mar-2025",
      "first_payment_date": "17-Mar-2025",
      "last_regular_payment_date": "17-Sep-2029",
      "stub_period": "None",
      "compounding": "Not Applicable"
    }
  },
  "floating_leg_details": {
    "payer": "Goldman Sachs International",
    "receiver": "First Abu Dhabi Bank PJSC",
    "floating_rate_option": "USD-SOFR-OIS Compound",
    "floating_rate_index": "USD-SOFR-OIS Compound",
    "index_source": "Federal Reserve Bank of New York",
    "spread": {
      "basis_points": 25,
      "decimal": 0.0025,
      "formatted_spread": "+25 basis points (+0.25%)"
    },
    "day_count_fraction": "ACT/360",
    "payment_frequency": "Quarterly",
    "reset_frequency": "Daily",
    "payment_schedule": {
      "payment_dates": "17th day of each calendar quarter",
      "quarterly_dates": "17-Dec, 17-Mar, 17-Jun, 17-Sep of each year starting 17-Dec-2024",
      "first_payment_date": "17-Dec-2024",
      "final_payment_date": "17-Sep-2029"
    },
    "rate_cut_off": "2 New York Business Days",
    "compounding_method": "OIS Compounding",
    "reset_dates": "Each New York Business Day"
  },
  "settlement_instructions": {
    "payment_method": "Electronic Transfer",
    "payment_currency": "USD",
    "netting_arrangements": "ISDA Payment Netting",
    "settlement_date_convention": "Payment Date + 0 Business Days",
    "gsi_account_details": {
      "bank_name": "Citibank N.A. London Branch",
      "account_number": "40012345",
      "swift_code": "CITIGB2L",
      "iban": "GB29CITI18500840012345"
    },
    "fab_account_details": {
      "bank_name": "JPMorgan Chase Bank N.A.",
      "account_number": "001-234-567890",
      "swift_code": "CHASUS33",
      "aba_routing": "021000021"
    }
  },
  "documentation_and_legal": {
    "master_agreement": {
      "type": "ISDA 2002 Master Agreement",
      "date": "15 March 2019"
    },
    "credit_support_document": "ISDA 2016 Credit Support Annex",
    "csa_thresholds": {
      "gsi_threshold": {
        "amount": 25000000.00,
        "currency": "USD",
        "formatted": "USD 25,000,000"
      },
      "fab_threshold": {
        "amount": 15000000.00,
        "currency": "USD",
        "formatted": "USD 15,000,000"
      }
    },
    "governing_law": "English Law",
    "jurisdiction": "English Courts",
    "process_agent_fab": "CT Corporation System London, United Kingdom"
  },
  "confirmations_and_signatures": {
    "gsi_signatory": {
      "name": "Marcus Richardson",
      "title": "Executive Director, Fixed Income Division",
      "signature_date": "15 September 2024",
      "entity": "Goldman Sachs International"
    },
    "fab_signatory": {
      "name": "[TO BE COMPLETED]",
      "title": "[TO BE COMPLETED]",
      "signature_date": "[TO BE COMPLETED]",
      "entity": "First Abu Dhabi Bank PJSC",
      "status": "PENDING_SIGNATURE"
    }
  },
  "regulatory_and_compliance": {
    "trade_capacity": "Principal",
    "confirmation_requirement": "Execute acknowledgment and return within one business day",
    "submission_methods": ["fax", "email"],
    "master_agreement_reference": "ISDA Master Agreement dated 15 March 2019 between Goldman Sachs International and First Abu Dhabi Bank PJSC"
  },
  "payment_calculations": {
    "fixed_leg_annual_amount": {
      "calculation": "50,000,000 * 3.75% = 1,875,000 USD per annum",
      "semi_annual_payment": 937500.00
    },
    "floating_leg_reference": "USD-SOFR-OIS Compound + 25bp quarterly payments"
  },
  "data_extraction_notes": {
    "extracted_fields_count": 45,
    "critical_fields_verified": True,
    "decimal_precision_maintained": True,
    "date_formats_preserved": True,
    "counterparty_identifiers_complete": True,
    "settlement_instructions_complete": True,
    "regulatory_fields_captured": True,
    "data_quality_score": "EXCELLENT",
    "source_pages": [
      "Page 1: Trade identification and counterparty details",
      "Page 2: Economic terms and settlement instructions", 
      "Page 3: Documentation and legal framework"
    ]
  }
}

# Determine database based on content - this is counterparty trade data
# (contains both dealer and client information)
db_path = os.path.join(storage_dir, 'counterparty_trade_data.db')
db = TinyDB(db_path)

# Use Trade_ID as primary key
trade_id = trade_data['trade_identification']['trade_id']
Trade = Query()

# Check if record exists
existing_record = db.search(Trade.trade_identification.trade_id == trade_id)

# Add metadata for storage tracking
storage_metadata = {
    'storage_timestamp': datetime.now().isoformat(),
    'storage_action': 'update' if existing_record else 'insert'
}
trade_data['storage_metadata'] = storage_metadata

# Perform idempotent operation
if existing_record:
    # Update existing record
    db.update(trade_data, Trade.trade_identification.trade_id == trade_id)
    action = 'updated'
else:
    # Insert new record
    db.insert(trade_data)
    action = 'inserted'

# Get record count
record_count = len(db.all())

# Print confirmation
print(f"Stored trade {trade_id} in counterparty_trade_data.db")
print(f"Action: {action}")
print(f"Database record count: {record_count}")

# Close database
db.close()