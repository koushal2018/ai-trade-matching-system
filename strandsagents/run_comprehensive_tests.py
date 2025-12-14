#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner

This script runs all comprehensive tests for the enhanced AI reconciliation system,
providing detailed reporting and coverage analysis.
"""

import sys
import os
import subprocess
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSuiteRunner:
    """Comprehensive test suite runner with reporting."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_test_module(self, module_name: str, description: str) -> Dict[str, Any]:
        """Run a specific test module and capture results."""
        logger.info(f"Running {description}...")
        
        start_time = time.time()
        
        try:
            # Run pytest on the specific module
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                f"{module_name}",
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={self.output_dir}/{module_name.replace('.py', '')}_report.json"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Parse results
            success = result.returncode == 0
            
            # Try to load JSON report if available
            json_report_path = self.output_dir / f"{module_name.replace('.py', '')}_report.json"
            test_details = {}
            
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_report = json.load(f)
                        test_details = {
                            "total_tests": json_report.get("summary", {}).get("total", 0),
                            "passed": json_report.get("summary", {}).get("passed", 0),
                            "failed": json_report.get("summary", {}).get("failed", 0),
                            "skipped": json_report.get("summary", {}).get("skipped", 0),
                            "errors": json_report.get("summary", {}).get("error", 0)
                        }
                except Exception as e:
                    logger.warning(f"Could not parse JSON report for {module_name}: {e}")
            
            return {
                "module": module_name,
                "description": description,
                "success": success,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                **test_details
            }
            
        except Exception as e:
            logger.error(f"Error running {module_name}: {e}")
            return {
                "module": module_name,
                "description": description,
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests."""
        self.start_time = time.time()
        
        # Define test modules in order of execution
        test_modules = [
            ("test_ai_provider_adapters.py", "AI Provider Adapter Unit Tests"),
            ("test_enhanced_tools.py", "Enhanced Tools Unit Tests"),
            ("test_enhanced_agents.py", "Enhanced Agents Unit Tests"),
            ("test_strands_integration.py", "Strands SDK Integration Tests"),
            ("test_strands_workflow_integration.py", "Strands Workflow Integration Tests"),
            ("test_performance_comparison.py", "Performance Comparison Tests"),
            ("test_error_handling_fallback.py", "Error Handling and Fallback Tests"),
            ("test_configuration_validation.py", "Configuration Validation Tests"),
            ("test_end_to_end_reconciliation.py", "End-to-End Reconciliation Tests"),
            ("test_performance_optimization.py", "Performance Optimization Tests"),
            ("test_extensible_architecture.py", "Extensible Architecture Tests")
        ]
        
        logger.info("Starting comprehensive test suite execution...")
        logger.info(f"Running {len(test_modules)} test modules")
        
        # Run each test module
        for module_name, description in test_modules:
            if Path(module_name).exists():
                result = self.run_test_module(module_name, description)
                self.test_results[module_name] = result
                
                # Log immediate results
                if result["success"]:
                    logger.info(f"✓ {description} - PASSED ({result['execution_time']:.2f}s)")
                    if "total_tests" in result:
                        logger.info(f"  Tests: {result['passed']}/{result['total_tests']} passed")
                else:
                    logger.error(f"✗ {description} - FAILED ({result['execution_time']:.2f}s)")
                    if result.get("stderr"):
                        logger.error(f"  Error: {result['stderr'][:200]}...")
            else:
                logger.warning(f"Test module {module_name} not found, skipping...")
        
        self.end_time = time.time()
        
        # Generate summary report
        return self.generate_summary_report()
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report."""
        total_execution_time = self.end_time - self.start_time
        
        # Calculate overall statistics
        total_modules = len(self.test_results)
        passed_modules = sum(1 for result in self.test_results.values() if result["success"])
        failed_modules = total_modules - passed_modules
        
        total_tests = sum(result.get("total_tests", 0) for result in self.test_results.values())
        total_passed = sum(result.get("passed", 0) for result in self.test_results.values())
        total_failed = sum(result.get("failed", 0) for result in self.test_results.values())
        total_skipped = sum(result.get("skipped", 0) for result in self.test_results.values())
        total_errors = sum(result.get("errors", 0) for result in self.test_results.values())
        
        # Create summary
        summary = {
            "execution_summary": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "total_execution_time": total_execution_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time))
            },
            "module_summary": {
                "total_modules": total_modules,
                "passed_modules": passed_modules,
                "failed_modules": failed_modules,
                "success_rate": (passed_modules / total_modules * 100) if total_modules > 0 else 0
            },
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": total_passed,
                "failed_tests": total_failed,
                "skipped_tests": total_skipped,
                "error_tests": total_errors,
                "test_success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
            },
            "module_results": self.test_results,
            "performance_metrics": self.calculate_performance_metrics(),
            "coverage_analysis": self.analyze_test_coverage(),
            "recommendations": self.generate_recommendations()
        }
        
        return summary
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics from test results."""
        execution_times = [result["execution_time"] for result in self.test_results.values()]
        
        if not execution_times:
            return {}
        
        return {
            "fastest_module": min(self.test_results.items(), key=lambda x: x[1]["execution_time"]),
            "slowest_module": max(self.test_results.items(), key=lambda x: x[1]["execution_time"]),
            "average_execution_time": sum(execution_times) / len(execution_times),
            "total_test_time": sum(execution_times)
        }
    
    def analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage across different components."""
        coverage_areas = {
            "ai_provider_adapters": "test_ai_provider_adapters.py" in self.test_results,
            "enhanced_tools": "test_enhanced_tools.py" in self.test_results,
            "enhanced_agents": "test_enhanced_agents.py" in self.test_results,
            "strands_integration": "test_strands_integration.py" in self.test_results,
            "workflow_integration": "test_strands_workflow_integration.py" in self.test_results,
            "performance_testing": "test_performance_comparison.py" in self.test_results,
            "error_handling": "test_error_handling_fallback.py" in self.test_results,
            "configuration_validation": "test_configuration_validation.py" in self.test_results,
            "end_to_end_testing": "test_end_to_end_reconciliation.py" in self.test_results
        }
        
        covered_areas = sum(1 for covered in coverage_areas.values() if covered)
        total_areas = len(coverage_areas)
        
        return {
            "coverage_areas": coverage_areas,
            "covered_areas": covered_areas,
            "total_areas": total_areas,
            "coverage_percentage": (covered_areas / total_areas * 100) if total_areas > 0 else 0
        }
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check for failed modules
        failed_modules = [name for name, result in self.test_results.items() if not result["success"]]
        if failed_modules:
            recommendations.append(f"Address failures in: {', '.join(failed_modules)}")
        
        # Check for slow tests
        slow_modules = [name for name, result in self.test_results.items() 
                       if result["execution_time"] > 30]  # More than 30 seconds
        if slow_modules:
            recommendations.append(f"Optimize performance for slow test modules: {', '.join(slow_modules)}")
        
        # Check test coverage
        coverage = self.analyze_test_coverage()
        if coverage["coverage_percentage"] < 100:
            missing_areas = [area for area, covered in coverage["coverage_areas"].items() if not covered]
            recommendations.append(f"Add missing test coverage for: {', '.join(missing_areas)}")
        
        # Check for skipped tests
        total_skipped = sum(result.get("skipped", 0) for result in self.test_results.values())
        if total_skipped > 0:
            recommendations.append(f"Review and address {total_skipped} skipped tests")
        
        # Performance recommendations
        performance = self.calculate_performance_metrics()
        if performance and performance["total_test_time"] > 300:  # More than 5 minutes
            recommendations.append("Consider parallelizing tests to reduce total execution time")
        
        return recommendations
    
    def save_report(self, summary: Dict[str, Any], filename: str = "comprehensive_test_report.json"):
        """Save the comprehensive test report."""
        report_path = self.output_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Comprehensive test report saved to: {report_path}")
        return report_path
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print a human-readable summary of test results."""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUITE RESULTS")
        print("="*80)
        
        # Execution summary
        exec_summary = summary["execution_summary"]
        print(f"\nExecution Time: {exec_summary['total_execution_time']:.2f} seconds")
        print(f"Completed: {exec_summary['timestamp']}")
        
        # Module summary
        mod_summary = summary["module_summary"]
        print(f"\nModule Results:")
        print(f"  Total Modules: {mod_summary['total_modules']}")
        print(f"  Passed: {mod_summary['passed_modules']}")
        print(f"  Failed: {mod_summary['failed_modules']}")
        print(f"  Success Rate: {mod_summary['success_rate']:.1f}%")
        
        # Test summary
        test_summary = summary["test_summary"]
        print(f"\nTest Results:")
        print(f"  Total Tests: {test_summary['total_tests']}")
        print(f"  Passed: {test_summary['passed_tests']}")
        print(f"  Failed: {test_summary['failed_tests']}")
        print(f"  Skipped: {test_summary['skipped_tests']}")
        print(f"  Errors: {test_summary['error_tests']}")
        print(f"  Success Rate: {test_summary['test_success_rate']:.1f}%")
        
        # Coverage analysis
        coverage = summary["coverage_analysis"]
        print(f"\nTest Coverage:")
        print(f"  Coverage: {coverage['covered_areas']}/{coverage['total_areas']} areas ({coverage['coverage_percentage']:.1f}%)")
        
        # Module details
        print(f"\nModule Details:")
        for module_name, result in summary["module_results"].items():
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            time_str = f"{result['execution_time']:.2f}s"
            test_info = ""
            if "total_tests" in result:
                test_info = f" ({result['passed']}/{result['total_tests']} tests)"
            print(f"  {status} {result['description']} - {time_str}{test_info}")
        
        # Performance metrics
        if "performance_metrics" in summary and summary["performance_metrics"]:
            perf = summary["performance_metrics"]
            print(f"\nPerformance Metrics:")
            print(f"  Fastest Module: {perf['fastest_module'][0]} ({perf['fastest_module'][1]['execution_time']:.2f}s)")
            print(f"  Slowest Module: {perf['slowest_module'][0]} ({perf['slowest_module'][1]['execution_time']:.2f}s)")
            print(f"  Average Time: {perf['average_execution_time']:.2f}s")
        
        # Recommendations
        if summary["recommendations"]:
            print(f"\nRecommendations:")
            for i, rec in enumerate(summary["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        # Overall result
        print(f"\n" + "="*80)
        if mod_summary["failed_modules"] == 0:
            print("🎉 ALL TESTS PASSED! The enhanced AI reconciliation system is ready.")
        else:
            print(f"⚠️  {mod_summary['failed_modules']} module(s) failed. Please review and fix issues.")
        print("="*80)


def main():
    """Main function to run comprehensive tests."""
    parser = argparse.ArgumentParser(description="Run comprehensive test suite for enhanced AI reconciliation")
    parser.add_argument("--output-dir", default="test_results", help="Output directory for test results")
    parser.add_argument("--module", help="Run specific test module only")
    parser.add_argument("--no-report", action="store_true", help="Skip generating detailed report")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Create test runner
    runner = TestSuiteRunner(args.output_dir)
    
    try:
        if args.module:
            # Run specific module
            logger.info(f"Running specific test module: {args.module}")
            result = runner.run_test_module(args.module, f"Specific Test: {args.module}")
            runner.test_results[args.module] = result
            
            # Generate minimal summary
            summary = {
                "module_results": {args.module: result},
                "execution_summary": {
                    "total_execution_time": result["execution_time"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        else:
            # Run all tests
            summary = runner.run_all_tests()
        
        # Print summary
        runner.print_summary(summary)
        
        # Save detailed report
        if not args.no_report:
            report_path = runner.save_report(summary)
            print(f"\nDetailed report saved to: {report_path}")
        
        # Exit with appropriate code
        if args.module:
            sys.exit(0 if result["success"] else 1)
        else:
            failed_modules = summary["module_summary"]["failed_modules"]
            sys.exit(0 if failed_modules == 0 else 1)
            
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error running test suite: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()