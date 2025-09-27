#!/usr/bin/env python3
"""
Comprehensive test suite for Trade Matching System
Combines unit tests, integration tests, security tests, and performance tests
"""

import pytest
import asyncio
import subprocess
import sys
import os
import json
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradeMatchingTestSuite:
    def __init__(self):
        self.test_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests': {},
            'summary': {}
        }
        self.base_dir = Path(__file__).parent

    def run_unit_tests(self):
        """Run unit tests using pytest"""
        logger.info("🧪 Running unit tests...")

        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                'tests/', '-v', '--tb=short', '--json-report', '--json-report-file=test-results/unit-tests.json'
            ], capture_output=True, text=True, timeout=300)

            success = result.returncode == 0
            self.test_results['tests']['unit_tests'] = {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }

            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"Unit Tests: {status}")
            return success

        except subprocess.TimeoutExpired:
            logger.error("❌ Unit tests timed out")
            self.test_results['tests']['unit_tests'] = {
                'success': False,
                'error': 'Timeout after 300 seconds'
            }
            return False
        except Exception as e:
            logger.error(f"❌ Unit tests failed: {e}")
            self.test_results['tests']['unit_tests'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def run_integration_tests(self):
        """Run integration tests"""
        logger.info("🔗 Running integration tests...")

        try:
            # Check if API is running
            import requests
            health_response = requests.get("http://localhost:8080/health", timeout=10)
            if health_response.status_code != 200:
                logger.error("❌ API not available for integration tests")
                self.test_results['tests']['integration_tests'] = {
                    'success': False,
                    'error': 'API not available'
                }
                return False

            # Run integration tests
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                'tests/integration/', '-v', '--tb=short'
            ], capture_output=True, text=True, timeout=600)

            success = result.returncode == 0
            self.test_results['tests']['integration_tests'] = {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }

            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"Integration Tests: {status}")
            return success

        except subprocess.TimeoutExpired:
            logger.error("❌ Integration tests timed out")
            self.test_results['tests']['integration_tests'] = {
                'success': False,
                'error': 'Timeout after 600 seconds'
            }
            return False
        except Exception as e:
            logger.error(f"❌ Integration tests failed: {e}")
            self.test_results['tests']['integration_tests'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def run_security_audit(self):
        """Run security audit"""
        logger.info("🔒 Running security audit...")

        try:
            result = subprocess.run([
                sys.executable, 'security/security_audit.py'
            ], capture_output=True, text=True, timeout=300)

            # Parse security results
            success = True
            try:
                with open('security/security_audit_results.json', 'r') as f:
                    security_data = json.load(f)
                    high_severity = security_data['summary']['high_severity']
                    overall_score = security_data['summary']['overall_score']

                    # Consider success if score > 60 and no high severity issues
                    success = overall_score > 60 and high_severity == 0

                    self.test_results['tests']['security_audit'] = {
                        'success': success,
                        'score': overall_score,
                        'high_severity_issues': high_severity,
                        'total_findings': security_data['summary']['total_findings']
                    }
            except FileNotFoundError:
                success = False
                self.test_results['tests']['security_audit'] = {
                    'success': False,
                    'error': 'Security audit results file not found'
                }

            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"Security Audit: {status}")
            return success

        except subprocess.TimeoutExpired:
            logger.error("❌ Security audit timed out")
            self.test_results['tests']['security_audit'] = {
                'success': False,
                'error': 'Timeout after 300 seconds'
            }
            return False
        except Exception as e:
            logger.error(f"❌ Security audit failed: {e}")
            self.test_results['tests']['security_audit'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def run_performance_tests(self):
        """Run performance tests"""
        logger.info("📊 Running performance tests...")

        try:
            result = subprocess.run([
                sys.executable, 'performance/load_test.py', '--quick'
            ], capture_output=True, text=True, timeout=600)

            # Parse performance results
            success = True
            try:
                with open('performance/load_test_results.json', 'r') as f:
                    perf_data = json.load(f)

                    # Calculate overall performance score
                    total_requests = 0
                    successful_requests = 0
                    avg_response_times = []

                    for test_name, test_data in perf_data['tests'].items():
                        if 'analysis' in test_data and test_data['analysis']:
                            analysis = test_data['analysis']
                            total_requests += analysis['total_requests']
                            successful_requests += analysis['successful_requests']
                            avg_response_times.append(analysis['response_times']['avg'])

                    if total_requests > 0:
                        success_rate = (successful_requests / total_requests) * 100
                        avg_response_time = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0

                        # Consider success if >95% success rate and <1s avg response time
                        success = success_rate > 95 and avg_response_time < 1.0

                        self.test_results['tests']['performance_tests'] = {
                            'success': success,
                            'success_rate': success_rate,
                            'avg_response_time': avg_response_time,
                            'total_requests': total_requests
                        }
                    else:
                        success = False
                        self.test_results['tests']['performance_tests'] = {
                            'success': False,
                            'error': 'No performance data available'
                        }

            except FileNotFoundError:
                success = False
                self.test_results['tests']['performance_tests'] = {
                    'success': False,
                    'error': 'Performance test results file not found'
                }

            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"Performance Tests: {status}")
            return success

        except subprocess.TimeoutExpired:
            logger.error("❌ Performance tests timed out")
            self.test_results['tests']['performance_tests'] = {
                'success': False,
                'error': 'Timeout after 600 seconds'
            }
            return False
        except Exception as e:
            logger.error(f"❌ Performance tests failed: {e}")
            self.test_results['tests']['performance_tests'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def run_health_check(self):
        """Run system health check"""
        logger.info("💚 Running system health check...")

        try:
            result = subprocess.run([
                sys.executable, 'monitoring/health_check.py'
            ], capture_output=True, text=True, timeout=180)

            # Parse health check results
            success = True
            try:
                with open('monitoring/health_check_results.json', 'r') as f:
                    health_data = json.load(f)
                    overall_healthy = health_data.get('overall_healthy', False)

                    self.test_results['tests']['health_check'] = {
                        'success': overall_healthy,
                        'checks': health_data.get('checks', {}),
                        'overall_healthy': overall_healthy
                    }
                    success = overall_healthy

            except FileNotFoundError:
                success = False
                self.test_results['tests']['health_check'] = {
                    'success': False,
                    'error': 'Health check results file not found'
                }

            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"Health Check: {status}")
            return success

        except subprocess.TimeoutExpired:
            logger.error("❌ Health check timed out")
            self.test_results['tests']['health_check'] = {
                'success': False,
                'error': 'Timeout after 180 seconds'
            }
            return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            self.test_results['tests']['health_check'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def run_comprehensive_suite(self):
        """Run all tests in the comprehensive suite"""
        logger.info("🚀 Starting Comprehensive Test Suite")
        logger.info("="*80)

        # Create test results directory
        os.makedirs('test-results', exist_ok=True)

        start_time = time.time()

        # Test sequence
        test_functions = [
            ('Health Check', self.run_health_check),
            ('Unit Tests', self.run_unit_tests),
            ('Integration Tests', self.run_integration_tests),
            ('Security Audit', self.run_security_audit),
            ('Performance Tests', self.run_performance_tests),
        ]

        passed_tests = 0
        total_tests = len(test_functions)

        for test_name, test_function in test_functions:
            logger.info(f"\n▶️  Running {test_name}...")
            try:
                success = test_function()
                if success:
                    passed_tests += 1
            except Exception as e:
                logger.error(f"❌ {test_name} encountered an error: {e}")

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate summary
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests) * 100,
            'total_time': total_time,
            'overall_success': passed_tests == total_tests
        }

        # Save comprehensive results
        with open('test-results/comprehensive_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)

        # Print summary
        self.print_test_summary()

        return self.test_results['summary']['overall_success']

    def print_test_summary(self):
        """Print comprehensive test summary"""
        summary = self.test_results['summary']

        print("\n" + "="*80)
        print("🧪 COMPREHENSIVE TEST SUITE SUMMARY")
        print("="*80)
        print(f"📊 Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Total Time: {summary['total_time']:.1f} seconds")

        # Individual test results
        print(f"\n📋 Test Results:")
        for test_name, test_data in self.test_results['tests'].items():
            status = "✅ PASSED" if test_data['success'] else "❌ FAILED"
            print(f"   • {test_name.replace('_', ' ').title()}: {status}")

            if not test_data['success'] and 'error' in test_data:
                print(f"     Error: {test_data['error']}")

        # Overall status
        if summary['overall_success']:
            overall_status = "🟢 ALL TESTS PASSED"
            print(f"\n🎉 {overall_status}")
            print("✅ Your Trade Matching System is ready for production!")
        else:
            overall_status = "🔴 SOME TESTS FAILED"
            print(f"\n⚠️  {overall_status}")
            print("❌ Please review and fix failing tests before production deployment")

        print("="*80)

def main():
    """Main entry point"""
    test_suite = TradeMatchingTestSuite()
    success = test_suite.run_comprehensive_suite()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()