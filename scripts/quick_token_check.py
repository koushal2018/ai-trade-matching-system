#!/usr/bin/env python3
"""
Quick Token Usage Check
Simple script for rapid token usage monitoring during development.
"""

import sys
import os
from datetime import datetime

# Add scripts path for imports
sys.path.append(os.path.dirname(__file__))

from analyze_token_usage import TokenUsageAnalyzer


def quick_check(hours: int = 1) -> None:
    """Run a quick token usage check and display key metrics."""
    
    print(f"🔍 Quick Token Check - Last {hours} hour(s)")
    print("=" * 50)
    
    try:
        analyzer = TokenUsageAnalyzer()
        report = analyzer.generate_report(hours_back=hours)
        
        summary = report['summary']
        
        # Key metrics
        print(f"📊 SUMMARY:")
        print(f"   Total Tokens: {summary['total_tokens']:,}")
        print(f"   Input Tokens: {summary['total_input_tokens']:,}")
        print(f"   Output Tokens: {summary['total_output_tokens']:,}")
        print(f"   Invocations: {summary['total_invocations']}")
        
        if summary['total_invocations'] > 0:
            print(f"   Avg/Invocation: {summary['avg_tokens_per_invocation']:,.1f}")
        
        # Cost estimate
        if report.get('cost_analysis'):
            cost = report['cost_analysis']['total_estimated_cost']
            print(f"   Estimated Cost: ${cost:.4f}")
        
        # Agent breakdown (top 3)
        if report['agent_breakdown']:
            print(f"\n🤖 TOP AGENTS:")
            agents = []
            for agent, metrics in report['agent_breakdown'].items():
                total = metrics.get('total_tokens_sum', 0)
                count = metrics.get('input_tokens_count', 0)
                agents.append((agent, total, count))
            
            # Sort by total tokens and show top 3
            agents.sort(key=lambda x: x[1], reverse=True)
            for agent, total, count in agents[:3]:
                print(f"   {agent}: {total:,} tokens ({count} calls)")
        
        # Recent activity indicator
        if summary['total_tokens'] > 0:
            print(f"\n✅ System is active - {summary['total_tokens']:,} tokens used")
        else:
            print(f"\n💤 No recent activity detected")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick token usage check')
    parser.add_argument('--hours', type=int, default=1, help='Hours back to check (default: 1)')
    
    args = parser.parse_args()
    quick_check(args.hours)