#!/usr/bin/env python3
"""
Generate test data for E2E testing of the AI Trade Matching System.

This script creates:
1. Sample PDF trade confirmations (Bank and Counterparty)
2. Seeds DynamoDB tables with test trade data
3. Populates agent registry with mock agent status
"""

import os
import sys
import json
import uuid
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
BANK_DIR = DATA_DIR / "BANK"
COUNTERPARTY_DIR = DATA_DIR / "COUNTERPARTY"


class TradeConfirmationGenerator:
    """Generates realistic trade confirmation PDFs."""

    COUNTERPARTIES = [
        "Goldman Sachs International",
        "JP Morgan Securities LLC",
        "Morgan Stanley Capital Services",
        "Citibank N.A.",
        "Bank of America Merrill Lynch",
        "Deutsche Bank AG",
        "Barclays Bank PLC",
        "HSBC Bank USA"
    ]

    CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF"]

    PRODUCT_TYPES = [
        ("Interest Rate Swap", "IRS"),
        ("FX Forward", "FXF"),
        ("Commodity Swap", "CMS"),
        ("Credit Default Swap", "CDS"),
    ]

    def __init__(self, seed=None):
        if seed:
            random.seed(seed)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            'TradeHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkblue
        ))
        self.styles.add(ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.darkblue
        ))
        self.styles.add(ParagraphStyle(
            'FieldLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.gray
        ))

    def generate_trade_data(self, trade_id=None):
        """Generate random trade data."""
        if not trade_id:
            product = random.choice(self.PRODUCT_TYPES)
            trade_id = f"{product[1]}-{random.randint(10000000, 99999999)}"

        trade_date = datetime.now() - timedelta(days=random.randint(1, 30))
        effective_date = trade_date + timedelta(days=random.randint(2, 5))
        maturity_date = effective_date + timedelta(days=random.randint(90, 730))

        notional = round(random.uniform(1000000, 50000000), 2)
        currency = random.choice(self.CURRENCIES)
        counterparty = random.choice(self.COUNTERPARTIES)
        product_type = random.choice(self.PRODUCT_TYPES)[0]

        # Generate rates based on product type
        if "Interest Rate" in product_type:
            fixed_rate = round(random.uniform(2.0, 6.0), 4)
            floating_rate = f"SOFR + {round(random.uniform(0.1, 1.0), 2)}%"
        else:
            fixed_rate = None
            floating_rate = None

        return {
            "trade_id": trade_id,
            "trade_date": trade_date.strftime("%Y-%m-%d"),
            "effective_date": effective_date.strftime("%Y-%m-%d"),
            "maturity_date": maturity_date.strftime("%Y-%m-%d"),
            "notional": notional,
            "currency": currency,
            "counterparty": counterparty,
            "product_type": product_type,
            "fixed_rate": fixed_rate,
            "floating_rate": floating_rate,
            "settlement_type": random.choice(["Cash", "Physical"]),
            "payment_frequency": random.choice(["Monthly", "Quarterly", "Semi-Annual"]),
        }

    def create_bank_confirmation_pdf(self, trade_data, output_path):
        """Create a bank-style trade confirmation PDF."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        story = []

        # Header
        story.append(Paragraph("FIRST NATIONAL BANK", self.styles['TradeHeader']))
        story.append(Paragraph("Trade Confirmation", self.styles['Heading2']))
        story.append(Spacer(1, 20))

        # Confirmation details
        story.append(Paragraph("CONFIRMATION DETAILS", self.styles['SectionHeader']))

        details_data = [
            ["Trade ID:", trade_data["trade_id"]],
            ["Trade Date:", trade_data["trade_date"]],
            ["Product Type:", trade_data["product_type"]],
            ["Counterparty:", trade_data["counterparty"]],
        ]

        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 20))

        # Economic Terms
        story.append(Paragraph("ECONOMIC TERMS", self.styles['SectionHeader']))

        terms_data = [
            ["Notional Amount:", f"{trade_data['currency']} {trade_data['notional']:,.2f}"],
            ["Effective Date:", trade_data["effective_date"]],
            ["Maturity Date:", trade_data["maturity_date"]],
            ["Settlement Type:", trade_data["settlement_type"]],
            ["Payment Frequency:", trade_data["payment_frequency"]],
        ]

        if trade_data.get("fixed_rate"):
            terms_data.append(["Fixed Rate:", f"{trade_data['fixed_rate']}%"])
        if trade_data.get("floating_rate"):
            terms_data.append(["Floating Rate:", trade_data["floating_rate"]])

        terms_table = Table(terms_data, colWidths=[2*inch, 4*inch])
        terms_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(terms_table)
        story.append(Spacer(1, 30))

        # Footer
        story.append(Paragraph(
            "This confirmation is subject to the terms of the ISDA Master Agreement.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['FieldLabel']
        ))

        doc.build(story)
        return output_path

    def create_counterparty_confirmation_pdf(self, trade_data, output_path, introduce_variance=False):
        """Create a counterparty-style trade confirmation PDF."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        story = []

        # Use counterparty name as header
        story.append(Paragraph(trade_data["counterparty"].upper(), self.styles['TradeHeader']))
        story.append(Paragraph("Derivative Trade Confirmation", self.styles['Heading2']))
        story.append(Spacer(1, 20))

        # Reference Information
        story.append(Paragraph("REFERENCE INFORMATION", self.styles['SectionHeader']))

        # Optionally introduce small variance for testing breaks
        display_notional = trade_data["notional"]
        if introduce_variance:
            # Small variance that should still match
            variance_type = random.choice(["none", "rounding", "break"])
            if variance_type == "rounding":
                display_notional = round(trade_data["notional"], 0)  # Round to whole number
            elif variance_type == "break":
                display_notional = trade_data["notional"] * 1.05  # 5% difference - will be a break

        ref_data = [
            ["Our Reference:", trade_data["trade_id"]],
            ["Your Reference:", f"FNB-{trade_data['trade_id']}"],
            ["Trade Date:", trade_data["trade_date"]],
            ["Transaction Type:", trade_data["product_type"]],
        ]

        ref_table = Table(ref_data, colWidths=[2*inch, 4*inch])
        ref_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(ref_table)
        story.append(Spacer(1, 20))

        # Trade Economics
        story.append(Paragraph("TRADE ECONOMICS", self.styles['SectionHeader']))

        econ_data = [
            ["Notional Principal:", f"{trade_data['currency']} {display_notional:,.2f}"],
            ["Start Date:", trade_data["effective_date"]],
            ["End Date:", trade_data["maturity_date"]],
            ["Settlement:", trade_data["settlement_type"]],
            ["Payment Schedule:", trade_data["payment_frequency"]],
        ]

        if trade_data.get("fixed_rate"):
            econ_data.append(["Fixed Rate:", f"{trade_data['fixed_rate']}% per annum"])
        if trade_data.get("floating_rate"):
            econ_data.append(["Floating Rate:", trade_data["floating_rate"]])

        econ_table = Table(econ_data, colWidths=[2*inch, 4*inch])
        econ_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(econ_table)
        story.append(Spacer(1, 30))

        # Legal text
        story.append(Paragraph(
            "Please confirm your agreement to the above terms by signing and returning this confirmation.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            f"Document ID: CP-{uuid.uuid4().hex[:8].upper()}",
            self.styles['FieldLabel']
        ))

        doc.build(story)
        return output_path


def generate_sample_pdfs(num_pairs=5, seed=42):
    """Generate sample PDF pairs for testing."""
    generator = TradeConfirmationGenerator(seed=seed)

    # Ensure directories exist
    BANK_DIR.mkdir(parents=True, exist_ok=True)
    COUNTERPARTY_DIR.mkdir(parents=True, exist_ok=True)

    generated_trades = []

    print(f"Generating {num_pairs} trade confirmation pairs...")
    print(f"  Bank PDFs: {BANK_DIR}")
    print(f"  Counterparty PDFs: {COUNTERPARTY_DIR}")
    print()

    for i in range(num_pairs):
        # Generate trade data
        trade_data = generator.generate_trade_data()
        trade_id = trade_data["trade_id"]

        # Decide if this should be a matching pair, probable match, or break
        scenario = random.choices(
            ["match", "probable", "break"],
            weights=[0.6, 0.2, 0.2],
            k=1
        )[0]

        # Create bank confirmation
        bank_filename = f"BANK_{trade_id}.pdf"
        bank_path = BANK_DIR / bank_filename
        generator.create_bank_confirmation_pdf(trade_data, bank_path)

        # Create counterparty confirmation (with potential variance)
        cp_filename = f"CP_{trade_id}.pdf"
        cp_path = COUNTERPARTY_DIR / cp_filename
        introduce_variance = scenario == "break"
        generator.create_counterparty_confirmation_pdf(trade_data, cp_path, introduce_variance)

        status_emoji = {"match": "✓", "probable": "~", "break": "✗"}[scenario]
        print(f"  [{status_emoji}] {trade_id}: {trade_data['product_type']} - {trade_data['currency']} {trade_data['notional']:,.0f}")

        generated_trades.append({
            "trade_id": trade_id,
            "bank_file": str(bank_path),
            "counterparty_file": str(cp_path),
            "trade_data": trade_data,
            "expected_scenario": scenario
        })

    # Save manifest
    manifest_path = DATA_DIR / "test_trades_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(generated_trades, f, indent=2, default=str)

    print()
    print(f"Generated {num_pairs} trade pairs")
    print(f"Manifest saved to: {manifest_path}")

    return generated_trades


def seed_dynamodb_test_data(trades, use_aws=True):
    """Seed DynamoDB tables with test trade data."""
    if not use_aws:
        print("Skipping DynamoDB seeding (use_aws=False)")
        return

    try:
        import boto3
        from botocore.exceptions import ClientError

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Table names from config
        bank_table = dynamodb.Table('BankTradeData')
        cp_table = dynamodb.Table('CounterpartyTradeData')

        print("Seeding DynamoDB tables with test data...")

        for trade in trades:
            trade_data = trade["trade_data"]
            trade_id = trade_data["trade_id"]

            # Convert float to Decimal for DynamoDB
            def to_decimal(obj):
                if isinstance(obj, float):
                    return Decimal(str(obj))
                return obj

            # Bank trade record
            bank_item = {
                "Trade_ID": trade_id,
                "TRADE_SOURCE": "BANK",
                "trade_date": trade_data["trade_date"],
                "effective_date": trade_data["effective_date"],
                "maturity_date": trade_data["maturity_date"],
                "notional": to_decimal(trade_data["notional"]),
                "currency": trade_data["currency"],
                "counterparty": trade_data["counterparty"],
                "product_type": trade_data["product_type"],
                "settlement_type": trade_data["settlement_type"],
                "payment_frequency": trade_data["payment_frequency"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            if trade_data.get("fixed_rate"):
                bank_item["fixed_rate"] = to_decimal(trade_data["fixed_rate"])

            # Counterparty trade record (may have variance)
            cp_item = bank_item.copy()
            cp_item["TRADE_SOURCE"] = "COUNTERPARTY"

            if trade["expected_scenario"] == "break":
                # Introduce variance for break scenarios
                cp_item["notional"] = to_decimal(float(trade_data["notional"]) * 1.05)

            try:
                bank_table.put_item(Item=bank_item)
                cp_table.put_item(Item=cp_item)
                print(f"  Seeded: {trade_id}")
            except ClientError as e:
                print(f"  Error seeding {trade_id}: {e}")

        print("DynamoDB seeding complete!")

    except Exception as e:
        print(f"DynamoDB seeding failed: {e}")
        print("Make sure AWS credentials are configured.")


def seed_agent_registry():
    """Populate agent registry with mock data."""
    try:
        import boto3
        from decimal import Decimal

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('AgentRegistry')

        agents = [
            {
                "agent_id": "pdf_adapter_agent",
                "agent_type": "PDF_ADAPTER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "description": "Extracts text from PDF trade confirmations",
                "avg_latency_ms": 15000,
                "throughput_per_hour": 25,
                "error_rate": Decimal("0.015"),
                "success_rate": Decimal("0.985"),
            },
            {
                "agent_id": "trade_extraction_agent",
                "agent_type": "TRADE_EXTRACTOR",
                "deployment_status": "ACTIVE",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "description": "Extracts structured trade data",
                "avg_latency_ms": 8000,
                "throughput_per_hour": 45,
                "error_rate": Decimal("0.008"),
                "success_rate": Decimal("0.992"),
            },
            {
                "agent_id": "trade_matching_agent",
                "agent_type": "TRADE_MATCHER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "description": "Matches trades across counterparties",
                "avg_latency_ms": 12000,
                "throughput_per_hour": 35,
                "error_rate": Decimal("0.012"),
                "success_rate": Decimal("0.988"),
            },
            {
                "agent_id": "exception_manager",
                "agent_type": "EXCEPTION_HANDLER",
                "deployment_status": "ACTIVE",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "description": "Handles trade exceptions",
                "avg_latency_ms": 3000,
                "throughput_per_hour": 60,
                "error_rate": Decimal("0.005"),
                "success_rate": Decimal("0.995"),
            },
        ]

        print("Seeding Agent Registry...")
        for agent in agents:
            table.put_item(Item=agent)
            print(f"  Registered: {agent['agent_id']}")

        print("Agent registry seeding complete!")

    except Exception as e:
        print(f"Agent registry seeding failed: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate test data for AI Trade Matching System")
    parser.add_argument("--pairs", type=int, default=5, help="Number of trade pairs to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--no-aws", action="store_true", help="Skip AWS DynamoDB seeding")
    parser.add_argument("--agents-only", action="store_true", help="Only seed agent registry")

    args = parser.parse_args()

    print("=" * 60)
    print("AI Trade Matching System - Test Data Generator")
    print("=" * 60)
    print()

    if args.agents_only:
        seed_agent_registry()
        return

    # Generate PDFs
    trades = generate_sample_pdfs(num_pairs=args.pairs, seed=args.seed)
    print()

    # Seed DynamoDB
    if not args.no_aws:
        seed_dynamodb_test_data(trades, use_aws=True)
        print()
        seed_agent_registry()
    else:
        print("Skipping AWS seeding (--no-aws flag set)")

    print()
    print("=" * 60)
    print("Test data generation complete!")
    print()
    print("Next steps:")
    print("  1. Upload PDFs via the web portal at http://localhost:3000")
    print("  2. Or use the API: POST /api/upload with a PDF file")
    print(f"  3. Sample PDFs are in: {DATA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
