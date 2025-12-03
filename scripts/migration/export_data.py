#!/usr/bin/env python3
"""
Data Export Script - Export data from me-central-1 region.

This script exports DynamoDB tables and S3 objects from the source region
for migration to us-east-1.

Requirements: 14.3
"""

import os
import json
import boto3
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Source configuration
SOURCE_REGION = os.getenv("SOURCE_REGION", "me-central-1")
SOURCE_BUCKET = os.getenv("SOURCE_BUCKET", "otc-menat-2025")
BANK_TABLE = os.getenv("BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("COUNTERPARTY_TABLE", "CounterpartyTradeData")

# Export directory
EXPORT_DIR = os.getenv("EXPORT_DIR", "/tmp/migration_export")


def export_dynamodb_table(table_name: str, region: str, output_file: str) -> int:
    """Export all items from a DynamoDB table to JSON file."""
    logger.info(f"Exporting table {table_name} from {region}...")
    
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    
    items = []
    scan_kwargs = {}
    
    while True:
        response = table.scan(**scan_kwargs)
        items.extend(response.get("Items", []))
        
        if "LastEvaluatedKey" not in response:
            break
        scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
    
    # Write to file
    with open(output_file, "w") as f:
        json.dump(items, f, indent=2, default=str)
    
    logger.info(f"Exported {len(items)} items from {table_name} to {output_file}")
    return len(items)


def export_s3_objects(bucket: str, region: str, output_dir: str, prefixes: List[str] = None) -> int:
    """Export S3 objects to local directory."""
    logger.info(f"Exporting S3 objects from {bucket} in {region}...")
    
    s3 = boto3.client("s3", region_name=region)
    
    if prefixes is None:
        prefixes = ["BANK/", "COUNTERPARTY/", "extracted/", "reports/"]
    
    total_objects = 0
    
    for prefix in prefixes:
        paginator = s3.get_paginator("list_objects_v2")
        
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                local_path = os.path.join(output_dir, "s3", key)
                
                # Create directory structure
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Download object
                try:
                    s3.download_file(bucket, key, local_path)
                    total_objects += 1
                except Exception as e:
                    logger.warning(f"Failed to download {key}: {e}")
    
    logger.info(f"Exported {total_objects} S3 objects to {output_dir}/s3")
    return total_objects


def verify_export(export_dir: str) -> Dict[str, Any]:
    """Verify the exported data integrity."""
    logger.info("Verifying exported data...")
    
    verification = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tables": {},
        "s3_objects": 0,
        "status": "SUCCESS"
    }
    
    # Verify DynamoDB exports
    for table_name in [BANK_TABLE, COUNTERPARTY_TABLE]:
        export_file = os.path.join(export_dir, f"{table_name}.json")
        if os.path.exists(export_file):
            with open(export_file, "r") as f:
                items = json.load(f)
            verification["tables"][table_name] = {
                "count": len(items),
                "file": export_file
            }
        else:
            verification["tables"][table_name] = {"count": 0, "error": "File not found"}
            verification["status"] = "PARTIAL"
    
    # Count S3 objects
    s3_dir = os.path.join(export_dir, "s3")
    if os.path.exists(s3_dir):
        for root, dirs, files in os.walk(s3_dir):
            verification["s3_objects"] += len(files)
    
    return verification


def main():
    """Main export function."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    logger.info(f"Starting data export from {SOURCE_REGION}")
    logger.info(f"Export directory: {EXPORT_DIR}")
    
    # Export DynamoDB tables
    bank_count = export_dynamodb_table(
        BANK_TABLE, SOURCE_REGION,
        os.path.join(EXPORT_DIR, f"{BANK_TABLE}.json")
    )
    
    cp_count = export_dynamodb_table(
        COUNTERPARTY_TABLE, SOURCE_REGION,
        os.path.join(EXPORT_DIR, f"{COUNTERPARTY_TABLE}.json")
    )
    
    # Export S3 objects
    s3_count = export_s3_objects(SOURCE_BUCKET, SOURCE_REGION, EXPORT_DIR)
    
    # Verify export
    verification = verify_export(EXPORT_DIR)
    
    # Save verification report
    report_file = os.path.join(EXPORT_DIR, "export_verification.json")
    with open(report_file, "w") as f:
        json.dump(verification, f, indent=2)
    
    logger.info(f"Export complete. Verification report: {report_file}")
    logger.info(f"Summary: {bank_count} bank trades, {cp_count} counterparty trades, {s3_count} S3 objects")
    
    return verification


if __name__ == "__main__":
    main()
