#!/usr/bin/env python3
"""
Token Usage Analysis Script for AI Trade Matching System
Collects and analyzes token usage across all agents during end-to-end testing.
"""

import json
import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse


class TokenUsageAnalyzer:
    """Analyzes token usage across all trade matching agents."""
    
    def __init__(self, region: str = "us-east-1"):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        
    def get_bedrock_metrics(self, hours_back: int = 1) -> Dict[str, Any]:
        """Get Bedrock token usage from CloudWatch."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        metrics = {}
        model_ids = [
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "amazon.nova-pro-v1:0"
        ]
        
        for model_id in model_ids:
            for metric_name in ['InputTokenCount', 'OutputTokenCount', 'InvocationCount']:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/Bedrock',
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'ModelId', 'Value': model_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5-minute intervals
                    Statistics=['Sum']
                )
                
                total = sum(point['Sum'] for point in response['Datapoints'])
                metrics[f"{model_id}_{metric_name}"] = total
                
        return metrics
    
    def get_agent_logs_token_usage(self, hours_back: int = 1) -> List[Dict[str, Any]]:
        """Extract token usage from agent CloudWatch logs."""
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = int((datetime.utcnow() - timedelta(hours=hours_back)).timestamp() * 1000)
        
        # AgentCore Runtime log groups (based on actual deployment structure)
        log_groups = [
            "/aws/bedrock/agentcore/pdf_adapter",
            "/aws/bedrock/agentcore/trade_extraction", 
            "/aws/bedrock/agentcore/trade_matching",
            "/aws/bedrock/agentcore/exception_management",
            "/aws/bedrock/agentcore/orchestrator"
        ]
        
        token_data = []
        
        for log_group in log_groups:
            try:
                response = self.logs.filter_log_events(
                    logGroupName=log_group,
                    startTime=start_time,
                    endTime=end_time,
                    filterPattern="Token usage"
                )
                
                for event in response['events']:
                    message = event['message']
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    
                    # Parse token usage from log message
                    # Multiple formats supported:
                    # "Token usage: 1234 in / 567 out"
                    # "Tokens used: input=1234, output=567"
                    # "Processing completed. Tokens: 1234 input, 567 output"
                    if any(phrase in message.lower() for phrase in ["token usage:", "tokens used:", "tokens:"]):
                        try:
                            # Format 1: "Token usage: 1234 in / 567 out"
                            if " in / " in message and " out" in message:
                                parts = message.split("Token usage:")[1].strip()
                                input_tokens = int(parts.split(" in / ")[0])
                                output_tokens = int(parts.split(" in / ")[1].split(" out")[0])
                            
                            # Format 2: "input=1234, output=567"
                            elif "input=" in message and "output=" in message:
                                import re
                                input_match = re.search(r'input=(\d+)', message)
                                output_match = re.search(r'output=(\d+)', message)
                                if input_match and output_match:
                                    input_tokens = int(input_match.group(1))
                                    output_tokens = int(output_match.group(1))
                                else:
                                    continue
                            
                            # Format 3: "1234 input, 567 output"
                            elif " input," in message and " output" in message:
                                import re
                                pattern = r'(\d+)\s+input,\s*(\d+)\s+output'
                                match = re.search(pattern, message)
                                if match:
                                    input_tokens = int(match.group(1))
                                    output_tokens = int(match.group(2))
                                else:
                                    continue
                            else:
                                continue
                                
                            token_data.append({
                                'timestamp': timestamp,
                                'agent': log_group.split('/')[-1],
                                'input_tokens': input_tokens,
                                'output_tokens': output_tokens,
                                'total_tokens': input_tokens + output_tokens,
                                'log_group': log_group
                            })
                            
                        except (ValueError, IndexError) as parse_error:
                            print(f"Failed to parse token data from: {message[:100]}... Error: {parse_error}")
                            continue
                            
            except Exception as e:
                print(f"Error processing log group {log_group}: {e}")
                
        return token_data
    
    def analyze_by_agent(self, token_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Analyze token usage by agent type."""
        df = pd.DataFrame(token_data)
        if df.empty:
            return df
            
        summary = df.groupby('agent').agg({
            'input_tokens': ['sum', 'mean', 'count'],
            'output_tokens': ['sum', 'mean'],
            'total_tokens': ['sum', 'mean']
        }).round(2)
        
        summary.columns = ['_'.join(col).strip() for col in summary.columns]
        return summary
    
    def analyze_by_time(self, token_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Analyze token usage over time."""
        df = pd.DataFrame(token_data)
        if df.empty:
            return df
            
        df['hour'] = df['timestamp'].dt.floor('H')
        hourly = df.groupby('hour').agg({
            'input_tokens': 'sum',
            'output_tokens': 'sum', 
            'total_tokens': 'sum'
        })
        
        return hourly
    
    def calculate_costs(self, token_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate estimated costs based on token usage.
        
        Uses current Bedrock pricing for Claude Sonnet and Nova Pro models.
        """
        # Bedrock pricing (per 1K tokens) - December 2024
        pricing = {
            "claude-3-5-sonnet": {
                "input": 0.003,   # $3 per 1M input tokens
                "output": 0.015   # $15 per 1M output tokens
            },
            "nova-pro": {
                "input": 0.0008,  # $0.80 per 1M input tokens  
                "output": 0.0032  # $3.20 per 1M output tokens
            }
        }
        
        total_input = sum(item['input_tokens'] for item in token_data)
        total_output = sum(item['output_tokens'] for item in token_data)
        
        # Estimate costs assuming 70% Claude Sonnet, 30% Nova Pro usage
        claude_input_cost = (total_input * 0.7 / 1000) * pricing["claude-3-5-sonnet"]["input"]
        claude_output_cost = (total_output * 0.7 / 1000) * pricing["claude-3-5-sonnet"]["output"]
        
        nova_input_cost = (total_input * 0.3 / 1000) * pricing["nova-pro"]["input"]
        nova_output_cost = (total_output * 0.3 / 1000) * pricing["nova-pro"]["output"]
        
        return {
            "total_estimated_cost": claude_input_cost + claude_output_cost + nova_input_cost + nova_output_cost,
            "claude_sonnet_cost": claude_input_cost + claude_output_cost,
            "nova_pro_cost": nova_input_cost + nova_output_cost,
            "cost_per_1k_tokens": (claude_input_cost + claude_output_cost + nova_input_cost + nova_output_cost) / max((total_input + total_output) / 1000, 1)
        }
    
    def generate_report(self, hours_back: int = 1) -> Dict[str, Any]:
        """Generate comprehensive token usage report."""
        print(f"🔍 Analyzing token usage for the last {hours_back} hour(s)...")
        
        # Get data from multiple sources
        bedrock_metrics = self.get_bedrock_metrics(hours_back)
        agent_logs = self.get_agent_logs_token_usage(hours_back)
        
        # Analyze data
        agent_summary = self.analyze_by_agent(agent_logs)
        time_analysis = self.analyze_by_time(agent_logs)
        cost_analysis = self.calculate_costs(agent_logs)
        
        # Calculate totals
        total_input = sum(item['input_tokens'] for item in agent_logs)
        total_output = sum(item['output_tokens'] for item in agent_logs)
        total_invocations = len(agent_logs)
        
        report = {
            'analysis_period': f"{hours_back} hours",
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_input_tokens': total_input,
                'total_output_tokens': total_output,
                'total_tokens': total_input + total_output,
                'total_invocations': total_invocations,
                'avg_tokens_per_invocation': round((total_input + total_output) / max(total_invocations, 1), 2)
            },
            'bedrock_metrics': bedrock_metrics,
            'cost_analysis': cost_analysis,
            'agent_breakdown': agent_summary.to_dict() if not agent_summary.empty else {},
            'hourly_usage': time_analysis.to_dict() if not time_analysis.empty else {},
            'raw_data': agent_logs
        }
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Analyze token usage for AI Trade Matching System')
    parser.add_argument('--hours', type=int, default=1, help='Hours back to analyze (default: 1)')
    parser.add_argument('--output', type=str, help='Output file path (JSON format)')
    parser.add_argument('--region', type=str, default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    analyzer = TokenUsageAnalyzer(region=args.region)
    report = analyzer.generate_report(hours_back=args.hours)
    
    # Print summary
    print("\n📊 TOKEN USAGE SUMMARY")
    print("=" * 50)
    print(f"Analysis Period: {report['summary']['total_tokens']:,} tokens over {args.hours} hour(s)")
    print(f"Total Input Tokens: {report['summary']['total_input_tokens']:,}")
    print(f"Total Output Tokens: {report['summary']['total_output_tokens']:,}")
    print(f"Total Invocations: {report['summary']['total_invocations']}")
    print(f"Avg Tokens/Invocation: {report['summary']['avg_tokens_per_invocation']}")
    
    # Print cost analysis
    if report['cost_analysis']:
        cost = report['cost_analysis']
        print(f"\n💰 COST ANALYSIS:")
        print(f"Estimated Total Cost: ${cost['total_estimated_cost']:.4f}")
        print(f"Claude Sonnet Cost: ${cost['claude_sonnet_cost']:.4f}")
        print(f"Nova Pro Cost: ${cost['nova_pro_cost']:.4f}")
        print(f"Cost per 1K tokens: ${cost['cost_per_1k_tokens']:.4f}")
    
    # Print agent breakdown
    if report['agent_breakdown']:
        print("\n🤖 BY AGENT:")
        for agent, metrics in report['agent_breakdown'].items():
            total = metrics.get('total_tokens_sum', 0)
            count = metrics.get('input_tokens_count', 0)
            print(f"  {agent}: {total:,} tokens ({count} invocations)")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Full report saved to: {args.output}")


if __name__ == "__main__":
    main()