#!/usr/bin/env python3
"""
Health monitoring script for Trade Matching System
Monitors system health, processes, and AWS resources
"""

import requests
import json
import time
import boto3
from datetime import datetime
import logging
import os
import subprocess
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring/health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradeMatchingHealthMonitor:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')

        # Initialize AWS clients
        try:
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
            self.dynamodb_client = boto3.client('dynamodb', region_name=self.aws_region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=self.aws_region)
            logger.info("AWS clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            self.s3_client = None
            self.dynamodb_client = None
            self.cloudwatch = None

    def check_api_health(self):
        """Check API health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ API Health: {health_data['status']}")
                return True, health_data
            else:
                logger.error(f"❌ API Health Check Failed: {response.status_code}")
                return False, None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API Health Check Failed: {e}")
            return False, None

    def check_s3_bucket(self, bucket_name="fab-otc-reconciliation-deployment"):
        """Check S3 bucket accessibility"""
        if not self.s3_client:
            return False, "S3 client not initialized"

        try:
            response = self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"✅ S3 Bucket '{bucket_name}' accessible")

            # Check recent objects
            objects = self.s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            object_count = objects.get('KeyCount', 0)
            logger.info(f"📄 Recent objects in bucket: {object_count}")

            return True, f"Bucket accessible, {object_count} recent objects"
        except Exception as e:
            logger.error(f"❌ S3 Bucket Check Failed: {e}")
            return False, str(e)

    def check_dynamodb_tables(self):
        """Check DynamoDB tables"""
        if not self.dynamodb_client:
            return False, "DynamoDB client not initialized"

        tables = ['BankTradeData', 'CounterpartyTradeData']
        results = {}

        for table_name in tables:
            try:
                response = self.dynamodb_client.describe_table(TableName=table_name)
                status = response['Table']['TableStatus']
                item_count = response['Table'].get('ItemCount', 0)

                logger.info(f"✅ DynamoDB Table '{table_name}': {status}, Items: {item_count}")
                results[table_name] = {'status': status, 'item_count': item_count}
            except Exception as e:
                logger.error(f"❌ DynamoDB Table '{table_name}' Check Failed: {e}")
                results[table_name] = {'status': 'ERROR', 'error': str(e)}

        return True, results

    def check_system_resources(self):
        """Check system resources"""
        try:
            # Check disk usage
            disk_usage = subprocess.check_output(['df', '-h', '/'], encoding='utf-8').strip().split('\n')[1]
            logger.info(f"💾 Disk Usage: {disk_usage}")

            # Check memory usage
            memory_info = subprocess.check_output(['vm_stat'], encoding='utf-8')
            logger.info("🧠 Memory usage checked")

            # Check Docker containers (if available)
            try:
                docker_ps = subprocess.check_output(['docker', 'ps', '--format', 'table {{.Names}}\\t{{.Status}}'], encoding='utf-8')
                logger.info(f"🐳 Docker containers:\n{docker_ps}")
            except subprocess.CalledProcessError:
                logger.warning("Docker not available or no containers running")

            return True, "System resources checked"
        except Exception as e:
            logger.error(f"❌ System Resource Check Failed: {e}")
            return False, str(e)

    def run_end_to_end_test(self):
        """Run a simple end-to-end test"""
        try:
            # Test processing endpoint with a simple request
            test_payload = {
                "s3_bucket": "fab-otc-reconciliation-deployment",
                "s3_key": "BANK/FAB_26933659.pdf",
                "source_type": "BANK",
                "event_time": datetime.utcnow().isoformat() + "Z",
                "unique_identifier": f"HEALTH_CHECK_{int(time.time())}"
            }

            response = requests.post(f"{self.api_url}/process", json=test_payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                processing_id = result.get('processing_id')
                logger.info(f"✅ End-to-end test initiated: {processing_id}")

                # Check status after a brief wait
                time.sleep(5)
                status_response = requests.get(f"{self.api_url}/status/{processing_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    logger.info(f"📊 Test Status: {status_data.get('status')}")
                    return True, f"E2E test successful: {status_data.get('status')}"
                else:
                    return False, "Status check failed"
            else:
                logger.error(f"❌ End-to-end test failed: {response.status_code}")
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            logger.error(f"❌ End-to-end test failed: {e}")
            return False, str(e)

    def send_cloudwatch_metrics(self, metrics_data):
        """Send custom metrics to CloudWatch"""
        if not self.cloudwatch:
            logger.warning("CloudWatch client not available")
            return

        try:
            # Send API health metric
            api_health = 1 if metrics_data.get('api_healthy') else 0
            self.cloudwatch.put_metric_data(
                Namespace='TradeMatching/Health',
                MetricData=[
                    {
                        'MetricName': 'APIHealth',
                        'Value': api_health,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    },
                ]
            )

            # Send S3 accessibility metric
            s3_health = 1 if metrics_data.get('s3_healthy') else 0
            self.cloudwatch.put_metric_data(
                Namespace='TradeMatching/Health',
                MetricData=[
                    {
                        'MetricName': 'S3Health',
                        'Value': s3_health,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    },
                ]
            )

            logger.info("📊 CloudWatch metrics sent successfully")
        except Exception as e:
            logger.error(f"❌ Failed to send CloudWatch metrics: {e}")

    def run_full_health_check(self, include_e2e=False):
        """Run complete health check"""
        logger.info("🚀 Starting comprehensive health check...")

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }

        # API Health Check
        api_healthy, api_data = self.check_api_health()
        results['checks']['api'] = {'healthy': api_healthy, 'data': api_data}

        # S3 Health Check
        s3_healthy, s3_data = self.check_s3_bucket()
        results['checks']['s3'] = {'healthy': s3_healthy, 'data': s3_data}

        # DynamoDB Health Check
        db_healthy, db_data = self.check_dynamodb_tables()
        results['checks']['dynamodb'] = {'healthy': db_healthy, 'data': db_data}

        # System Resources Check
        sys_healthy, sys_data = self.check_system_resources()
        results['checks']['system'] = {'healthy': sys_healthy, 'data': sys_data}

        # Optional End-to-End Test
        if include_e2e:
            e2e_healthy, e2e_data = self.run_end_to_end_test()
            results['checks']['e2e_test'] = {'healthy': e2e_healthy, 'data': e2e_data}

        # Calculate overall health
        all_checks = [api_healthy, s3_healthy, db_healthy, sys_healthy]
        if include_e2e:
            all_checks.append(e2e_healthy)

        overall_healthy = all(all_checks)
        results['overall_healthy'] = overall_healthy

        # Send metrics to CloudWatch
        metrics_data = {
            'api_healthy': api_healthy,
            's3_healthy': s3_healthy,
            'overall_healthy': overall_healthy
        }
        self.send_cloudwatch_metrics(metrics_data)

        # Summary
        status_emoji = "✅" if overall_healthy else "❌"
        logger.info(f"{status_emoji} Overall System Health: {'HEALTHY' if overall_healthy else 'UNHEALTHY'}")

        # Save results to file
        with open('monitoring/health_check_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        return results

def main():
    parser = argparse.ArgumentParser(description='Trade Matching System Health Monitor')
    parser.add_argument('--api-url', default='http://localhost:8080', help='API base URL')
    parser.add_argument('--include-e2e', action='store_true', help='Include end-to-end test')
    parser.add_argument('--continuous', action='store_true', help='Run continuously every 60 seconds')

    args = parser.parse_args()

    monitor = TradeMatchingHealthMonitor(api_url=args.api_url)

    if args.continuous:
        logger.info("Starting continuous monitoring (every 60 seconds)...")
        while True:
            try:
                monitor.run_full_health_check(include_e2e=args.include_e2e)
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                time.sleep(10)
    else:
        results = monitor.run_full_health_check(include_e2e=args.include_e2e)
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()