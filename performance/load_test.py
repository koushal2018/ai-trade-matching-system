#!/usr/bin/env python3
"""
Load testing script for Trade Matching System
Tests API performance under various load conditions
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
import argparse
import statistics
from typing import List, Dict
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = []

    async def health_check_test(self, session: aiohttp.ClientSession):
        """Simple health check test"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/health") as response:
                end_time = time.time()
                return {
                    'endpoint': '/health',
                    'status_code': response.status,
                    'response_time': end_time - start_time,
                    'success': response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                'endpoint': '/health',
                'status_code': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e)
            }

    async def process_document_test(self, session: aiohttp.ClientSession):
        """Test document processing endpoint"""
        start_time = time.time()
        payload = {
            "s3_bucket": "fab-otc-reconciliation-deployment",
            "s3_key": "BANK/FAB_26933659.pdf",
            "source_type": "BANK",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "unique_identifier": f"LOAD_TEST_{uuid.uuid4().hex[:8]}"
        }

        try:
            async with session.post(
                f"{self.base_url}/process",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                response_data = await response.json() if response.content_type == 'application/json' else {}

                return {
                    'endpoint': '/process',
                    'status_code': response.status,
                    'response_time': end_time - start_time,
                    'success': response.status == 200,
                    'processing_id': response_data.get('processing_id')
                }
        except asyncio.TimeoutError:
            end_time = time.time()
            return {
                'endpoint': '/process',
                'status_code': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': 'Timeout'
            }
        except Exception as e:
            end_time = time.time()
            return {
                'endpoint': '/process',
                'status_code': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e)
            }

    async def status_check_test(self, session: aiohttp.ClientSession, processing_id: str):
        """Test status check endpoint"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/status/{processing_id}") as response:
                end_time = time.time()
                return {
                    'endpoint': '/status',
                    'status_code': response.status,
                    'response_time': end_time - start_time,
                    'success': response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                'endpoint': '/status',
                'status_code': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e)
            }

    async def run_concurrent_requests(self, num_requests: int, test_type: str = 'health'):
        """Run concurrent requests for load testing"""
        logger.info(f"Starting {num_requests} concurrent {test_type} requests...")

        async with aiohttp.ClientSession() as session:
            if test_type == 'health':
                tasks = [self.health_check_test(session) for _ in range(num_requests)]
            elif test_type == 'process':
                tasks = [self.process_document_test(session) for _ in range(num_requests)]
            else:
                # Status tests need processing IDs
                test_id = f"TEST_{uuid.uuid4().hex[:8]}"
                tasks = [self.status_check_test(session, test_id) for _ in range(num_requests)]

            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Filter out exceptions and process results
            valid_results = [r for r in results if isinstance(r, dict)]

            return {
                'test_type': test_type,
                'total_requests': num_requests,
                'successful_requests': len([r for r in valid_results if r['success']]),
                'failed_requests': len([r for r in valid_results if not r['success']]),
                'total_time': end_time - start_time,
                'results': valid_results
            }

    def analyze_performance(self, test_results: Dict):
        """Analyze performance metrics"""
        results = test_results['results']
        if not results:
            return {}

        response_times = [r['response_time'] for r in results if 'response_time' in r]
        successful_requests = [r for r in results if r['success']]

        if not response_times:
            return {}

        analysis = {
            'total_requests': test_results['total_requests'],
            'successful_requests': test_results['successful_requests'],
            'failed_requests': test_results['failed_requests'],
            'success_rate': (test_results['successful_requests'] / test_results['total_requests']) * 100,
            'total_time': test_results['total_time'],
            'requests_per_second': test_results['total_requests'] / test_results['total_time'],
            'response_times': {
                'min': min(response_times),
                'max': max(response_times),
                'avg': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else response_times[0],
                'p99': statistics.quantiles(response_times, n=100)[98] if len(response_times) > 1 else response_times[0]
            }
        }

        return analysis

    async def run_load_test_suite(self,
                                  light_load: int = 10,
                                  medium_load: int = 50,
                                  heavy_load: int = 100):
        """Run comprehensive load test suite"""
        logger.info("🚀 Starting Load Test Suite...")

        test_suite_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'base_url': self.base_url,
            'tests': {}
        }

        # Test scenarios
        scenarios = [
            ('light_health_check', light_load, 'health'),
            ('medium_health_check', medium_load, 'health'),
            ('heavy_health_check', heavy_load, 'health'),
            ('light_status_check', light_load // 2, 'status'),
            ('medium_status_check', medium_load // 2, 'status'),
            # Process endpoint tests (fewer due to resource intensity)
            ('light_process', min(light_load // 5, 3), 'process'),
            ('medium_process', min(medium_load // 10, 5), 'process'),
        ]

        for scenario_name, num_requests, test_type in scenarios:
            logger.info(f"Running {scenario_name}: {num_requests} {test_type} requests")

            try:
                test_results = await self.run_concurrent_requests(num_requests, test_type)
                analysis = self.analyze_performance(test_results)

                test_suite_results['tests'][scenario_name] = {
                    'raw_results': test_results,
                    'analysis': analysis
                }

                # Log summary
                if analysis:
                    logger.info(f"✅ {scenario_name}: "
                              f"{analysis['success_rate']:.1f}% success rate, "
                              f"{analysis['requests_per_second']:.1f} req/s, "
                              f"avg response: {analysis['response_times']['avg']:.3f}s")
                else:
                    logger.error(f"❌ {scenario_name}: No valid results")

                # Brief pause between scenarios
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"❌ {scenario_name} failed: {e}")
                test_suite_results['tests'][scenario_name] = {
                    'error': str(e)
                }

        # Save results
        with open('performance/load_test_results.json', 'w') as f:
            json.dump(test_suite_results, f, indent=2)

        # Generate performance summary
        self.generate_performance_summary(test_suite_results)

        return test_suite_results

    def generate_performance_summary(self, results: Dict):
        """Generate human-readable performance summary"""
        print("\n" + "="*80)
        print("📊 LOAD TEST PERFORMANCE SUMMARY")
        print("="*80)

        overall_stats = {
            'total_tests': 0,
            'total_requests': 0,
            'total_successful': 0,
            'avg_response_times': []
        }

        for scenario_name, scenario_data in results['tests'].items():
            if 'analysis' in scenario_data and scenario_data['analysis']:
                analysis = scenario_data['analysis']

                print(f"\n📋 {scenario_name.replace('_', ' ').title()}:")
                print(f"   • Requests: {analysis['total_requests']}")
                print(f"   • Success Rate: {analysis['success_rate']:.1f}%")
                print(f"   • Throughput: {analysis['requests_per_second']:.1f} req/s")
                print(f"   • Avg Response Time: {analysis['response_times']['avg']:.3f}s")
                print(f"   • P95 Response Time: {analysis['response_times']['p95']:.3f}s")

                # Collect overall stats
                overall_stats['total_tests'] += 1
                overall_stats['total_requests'] += analysis['total_requests']
                overall_stats['total_successful'] += analysis['successful_requests']
                overall_stats['avg_response_times'].append(analysis['response_times']['avg'])

        # Overall summary
        if overall_stats['total_tests'] > 0:
            overall_success_rate = (overall_stats['total_successful'] / overall_stats['total_requests']) * 100
            overall_avg_response = statistics.mean(overall_stats['avg_response_times'])

            print(f"\n🏆 OVERALL PERFORMANCE:")
            print(f"   • Total Tests: {overall_stats['total_tests']}")
            print(f"   • Total Requests: {overall_stats['total_requests']}")
            print(f"   • Overall Success Rate: {overall_success_rate:.1f}%")
            print(f"   • Average Response Time: {overall_avg_response:.3f}s")

            # Performance rating
            if overall_success_rate >= 99 and overall_avg_response < 0.2:
                rating = "🟢 EXCELLENT"
            elif overall_success_rate >= 95 and overall_avg_response < 0.5:
                rating = "🟡 GOOD"
            elif overall_success_rate >= 90 and overall_avg_response < 1.0:
                rating = "🟠 ACCEPTABLE"
            else:
                rating = "🔴 NEEDS IMPROVEMENT"

            print(f"   • Performance Rating: {rating}")

        print("="*80)

async def main():
    parser = argparse.ArgumentParser(description='Trade Matching System Load Tester')
    parser.add_argument('--url', default='http://localhost:8080', help='API base URL')
    parser.add_argument('--light', type=int, default=10, help='Light load request count')
    parser.add_argument('--medium', type=int, default=50, help='Medium load request count')
    parser.add_argument('--heavy', type=int, default=100, help='Heavy load request count')
    parser.add_argument('--quick', action='store_true', help='Quick test with minimal load')

    args = parser.parse_args()

    # Create performance directory
    import os
    os.makedirs('performance', exist_ok=True)

    if args.quick:
        # Quick test for development
        light, medium, heavy = 5, 10, 20
    else:
        light, medium, heavy = args.light, args.medium, args.heavy

    tester = LoadTester(args.url)
    await tester.run_load_test_suite(light, medium, heavy)

if __name__ == "__main__":
    asyncio.run(main())