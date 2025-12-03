#!/usr/bin/env python3
"""
Data Import Script - Import data to us-east-1 region.

This script imports DynamoDB tables and S3 objects to the target region
after transformation.

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

# Target configuration
TARGET_REGION = os.getenv("TARGET_REGION", "us-east-1")
TARGET_BUCKET = os.getenv("TARGET_BUCKET", "trade-matching-us-east-1")
BANK_TABLE = os.getenv("BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("COUNTERPARTY_TABLE", "CounterpartyTradeData")

# Import directory
IMPORT_DIR = os.getenv("IMPORT_DIR", "/tmp/migration_export")


def transform_trade_data(item: Dict[str, Any], source_bucket: str, target_bucket: str) -> Dict[str, Any]:
    """Transform trade data for the new region."""
    transformed = item.copy()
    
    # Update S3 references
    for key, value in transformed.items():
        if isinstance(value, str) and source_bucket in value:
            transformed[key] = value.replace(source_bucket, target_bucket)
    
    # Add migration metadata
    transformed["_migration_timestamp"] = datetime.utcnow().isoformat() + "Z"
    transformed["_source_region"] = "me-central-1"
    
    return transformed


def import_dynamodb_table(table_name: str, region: str, input_file: str, source_bucket: str, target_bucket: str) -> int:
    """Import items to a DynamoDB table from JSON file."""
    logger.info(f"Importing to table {table_name} in {region}...")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return 0
    
    with open(input_file, "r") as f:
        items = json.load(f)
    
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    
    imported_count = 0
    
    with table.batch_writer() as batch:
        for item in items:
            transformed = transform_trade_data(item, source_bucket, target_bucket)
            batch.put_item(Item=transformed)
            imported_count += 1
    
    logger.info(f"Imported {imported_count} items to {table_name}")
    return imported_count


def import_s3_objects(bucket: str, region: str, input_dir: str) -> int:
    """Import S3 objects from local directory."""
    logger.info(f"Importing S3 objects to {bucket} in {region}...")
    
    s3 = boto3.client("s3", region_name=region)
    s3_dir = os.path.join(input_dir, "s3")
    
    if not os.path.exists(s3_dir):
        logger.warning(f"S3 export directory not found: {s3_dir}")
        return 0
    
    imported_count = 0
    
    for root, dirs, files in os.walk(s3_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            # Calculate S3 key from local path
            key = os.path.relpath(local_path, s3_dir)
            
            try:
                s3.upload_file(local_path, bucket, key)
                imported_count += 1
            except Exception as e:
                logger.warning(f"Failed to upload {key}: {e}")
    
    logger.info(f"Imported {imported_count} S3 objects to {bucket}")
    return imported_count


def verify_import(region: str, bucket: str) -> Dict[str, Any]:
    """Verify the imported data."""
    logger.info("Verifying imported data...")
    
    verification = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "region": region,
        "tables": {},
        "s3_objects": 0,
        "status": "SUCCESS"
    }
    
    dynamodb = boto3.resource("dynamodb", region_name=region)
    s3 = boto3.client("s3", region_name=region)
    
    # Verify DynamoDB tables
    for table_name in [BANK_TABLE, COUNTERPARTY_TABLE]:
        try:
            table = dynamodb.Table(table_name)
            response = table.scan(Select="COUNT")
            verification["tables"][table_name] = {"count": response.get("Count", 0)}
        except Exception as e:
            verification["tables"][table_name] = {"error": str(e)}
            verification["status"] = "PARTIAL"
    
    # Count S3 objects
    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            verification["s3_objects"] += len(page.get("Contents", []))
    except Exception as e:
        verification["s3_error"] = str(e)
        verification["status"] = "PARTIAL"
    
    return verification


def main():
    """Main import function."""
    source_bucket = os.getenv("SOURCE_BUCKET", "otc-menat-2025")
    
    logger.info(f"Starting data import to {TARGET_REGION}")
    logger.info(f"Import directory: {IMPORT_DIR}")
    
    # Import DynamoDB tables
    bank_count = import_dynamodb_table(
        BANK_TABLE, TARGET_REGION,
        os.path.join(IMPORT_DIR, f"{BANK_TABLE}.json"),
        source_bucket, TARGET_BUCKET
    )
    
    cp_count = import_dynamodb_table(
        COUNTERPARTY_TABLE, TARGET_REGION,
        os.path.join(IMPORT_DIR, f"{COUNTERPARTY_TABLE}.json"),
        source_bucket, TARGET_BUCKET
    )
    
    # Import S3 objects
    s3_count = import_s3_objects(TARGET_BUCKET, TARGET_REGION, IMPORT_DIR)
    
    # Verify import
    verification = verify_import(TARGET_REGION, TARGET_BUCKET)
    
    # Save verification report
    report_file = os.path.join(IMPORT_DIR, "import_verification.json")
    with open(report_file, "w") as f:
        json.dump(verification, f, indent=2)
    
    logger.info(f"Import complete. Verification report: {report_file}")
    logger.info(f"Summary: {bank_count} bank trades, {cp_count} counterparty trades, {s3_count} S3 objects")
    
    return verification


if __name__ == "__main__":
    main()
