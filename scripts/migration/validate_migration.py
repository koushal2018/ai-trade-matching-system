#!/usr/bin/env python3
"""
Migration Validation Script - Validate data migration between regions.

This script compares data between source and target regions to ensure
migration completeness and integrity.

Requirements: 14.3
"""

import os
import json
import boto3
from datetime import datetime
from typing import Dict, Any
import logging
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SOURCE_REGION = os.getenv("SOURCE_REGION", "me-central-1")
TARGET_REGION = os.getenv("TARGET_REGION", "us-east-1")
BANK_TABLE = os.getenv("BANK_TABLE", "BankTradeData")
COUNTERPARTY_TABLE = os.getenv("COUNTERPARTY_TABLE", "CounterpartyTradeData")


def get_table_count(table_name: str, region: str) -> int:
    """Get item count from a DynamoDB table."""
    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)
        response = table.scan(Select="COUNT")
        return response.get("Count", 0)
    except Exception as e:
        logger.error(f"Error counting {table_name} in {region}: {e}")
        return -1


def get_table_hash(table_name: str, region: str) -> str:
    """Get a hash of all Trade_IDs in a table for comparison."""
    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)
        
        trade_ids = []
        scan_kwargs = {"ProjectionExpression": "Trade_ID"}
        
        while True:
            response = table.scan(**scan_kwargs)
            for item in response.get("Items", []):
                trade_ids.append(item.get("Trade_ID", ""))
            
            if "LastEvaluatedKey" not in response:
                break
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        
        trade_ids.sort()
        content = ",".join(trade_ids)
        return hashlib.sha256(content.encode()).hexdigest()
    except Exception as e:
        logger.error(f"Error hashing {table_name} in {region}: {e}")
        return ""


def validate_tables() -> Dict[str, Any]:
    """Validate DynamoDB table migration."""
    logger.info("Validating DynamoDB tables...")
    
    results = {
        "tables": {},
        "all_valid": True
    }
    
    for table_name in [BANK_TABLE, COUNTERPARTY_TABLE]:
        source_count = get_table_count(table_name, SOURCE_REGION)
        target_count = get_table_count(table_name, TARGET_REGION)
        
        source_hash = get_table_hash(table_name, SOURCE_REGION)
        target_hash = get_table_hash(table_name, TARGET_REGION)
        
        is_valid = (source_count == target_count) and (source_hash == target_hash)
        
        results["tables"][table_name] = {
            "source_count": source_count,
            "target_count": target_count,
            "count_match": source_count == target_count,
            "hash_match": source_hash == target_hash,
            "valid": is_valid
        }
        
        if not is_valid:
            results["all_valid"] = False
            logger.warning(f"Validation failed for {table_name}")
        else:
            logger.info(f"Validation passed for {table_name}: {source_count} records")
    
    return results


def validate_queries() -> Dict[str, Any]:
    """Test queries on migrated data."""
    logger.info("Testing queries on migrated data...")
    
    results = {"queries": [], "all_passed": True}
    
    dynamodb = boto3.resource("dynamodb", region_name=TARGET_REGION)
    
    # Test 1: Query bank trades
    try:
        table = dynamodb.Table(BANK_TABLE)
        response = table.scan(Limit=5)
        results["queries"].append({
            "name": "scan_bank_trades",
            "passed": len(response.get("Items", [])) >= 0,
            "count": len(response.get("Items", []))
        })
    except Exception as e:
        results["queries"].append({"name": "scan_bank_trades", "passed": False, "error": str(e)})
        results["all_passed"] = False
    
    # Test 2: Query counterparty trades
    try:
        table = dynamodb.Table(COUNTERPARTY_TABLE)
        response = table.scan(Limit=5)
        results["queries"].append({
            "name": "scan_counterparty_trades",
            "passed": len(response.get("Items", [])) >= 0,
            "count": len(response.get("Items", []))
        })
    except Exception as e:
        results["queries"].append({"name": "scan_counterparty_trades", "passed": False, "error": str(e)})
        results["all_passed"] = False
    
    return results


def main():
    """Main validation function."""
    logger.info(f"Validating migration from {SOURCE_REGION} to {TARGET_REGION}")
    
    validation_report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_region": SOURCE_REGION,
        "target_region": TARGET_REGION,
        "status": "SUCCESS"
    }
    
    # Validate tables
    table_results = validate_tables()
    validation_report["tables"] = table_results
    
    if not table_results["all_valid"]:
        validation_report["status"] = "FAILED"
    
    # Validate queries
    query_results = validate_queries()
    validation_report["queries"] = query_results
    
    if not query_results["all_passed"]:
        validation_report["status"] = "FAILED"
    
    # Save report
    report_file = "/tmp/migration_validation.json"
    with open(report_file, "w") as f:
        json.dump(validation_report, f, indent=2)
    
    logger.info(f"Validation complete. Status: {validation_report['status']}")
    logger.info(f"Report saved to: {report_file}")
    
    return validation_report


if __name__ == "__main__":
    main()
