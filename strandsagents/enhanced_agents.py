"""
Enhanced Strands Agents with AI Capabilities

This module provides enhanced versions of the trade reconciliation agents that support
configurable AI providers and decision-making approaches while maintaining backward
compatibility with existing deterministic workflows.

Following Strands SDK best practices:
- Tools are defined using @tool decorator
- Agents are created with Agent(model, tools, system_prompt)
- Agents are invoked with agent(message)
"""

import json
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from decimal import Decimal

from strands import Agent, tool

try:
    from .enhanced_config import (
        EnhancedMatcherConfig, 
        EnhancedReconcilerConfig, 
        EnhancedReportConfig,
        DecisionMode,
        load_enhanced_configurations
    )
    # Import actual AI-powered tools from enhanced_tools
    from .enhanced_tools import (
        ai_analyze_trade_context,
        semantic_field_match,
        intelligent_trade_matching,
        explain_mismatch,
        context_aware_field_extraction
    )
    # Import actual AWS-powered tools from agents
    from .agents import (
        fetch_unmatched_trades,
        find_potential_matches,
        compute_similarity,
        update_match_status,
        mark_as_unmatched,
        fetch_matched_trades,
        get_trade_pair,
        compare_fields,
        determine_overall_status,
        update_reconciliation_status,
        generate_reconciliation_report,
        store_report,
        fetch_reconciliation_results
    )
except ImportError:
    # Handle standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from enhanced_config import (
        EnhancedMatcherConfig, 
        EnhancedReconcilerConfig, 
        EnhancedReportConfig,
        DecisionMode,
        load_enhanced_configurations
    )
    # Import actual AI-powered tools from enhanced_tools
    from enhanced_tools import (
        ai_analyze_trade_context,
        semantic_field_match,
        intelligent_trade_matching,
        explain_mismatch,
        context_aware_field_extraction
    )
    # Import actual AWS-powered tools from agents
    from agents import (
        fetch_unmatched_trades,
        find_potential_matches,
        compute_similarity,
        update_match_status,
        mark_as_unmatched,
        fetch_matched_trades,
        get_trade_pair,
        compare_fields,
        determine_overall_status,
        update_reconciliation_status,
        generate_reconciliation_report,
        store_report,
        fetch_reconciliation_results
    )

logger = logging.getLogger(__name__)


# All tools are imported from their respective modules:
# - Basic AWS-powered tools from agents.py (fetch_unmatched_trades, compute_similarity, etc.)
# - AI-enhanced tools from enhanced_tools.py (ai_analyze_trade_context, semantic_field_match, etc.)
# Enhanced AI tools are imported from enhanced_tools.py
# These provide actual AI-powered implementations with support for:
# - ai_analyze_trade_context: AI-powered trade context analysis
# - semantic_field_match: Semantic field comparison using AI
# - intelligent_trade_matching: AI-enhanced trade matching
# - explain_mismatch: AI-generated mismatch explanations  
# - context_aware_field_extraction: Context-aware field extraction














def create_enhanced_trade_matcher_agent(config: Optional[EnhancedMatcherConfig] = None) -> Agent:
    """
    Create an enhanced trade matching agent with configurable AI capabilities.
    
    Args:
        config: Enhanced matcher configuration
        
    Returns:
        Configured Strands Agent for trade matching
    """
    if config is None:
        config = EnhancedMatcherConfig.from_environment()
    
    decision_mode = config.decision_mode_config.mode
    
    # Build enhanced system prompt with AI provider configuration and decision mode options
    system_prompt = f"""You are an enhanced trade matching agent with configurable AI capabilities and intelligent decision-making.

## Configuration:
- **Decision Mode**: {decision_mode}
- **AI Provider**: {config.ai_provider_config.provider_type}
- **Region**: {config.ai_provider_config.region}
- **Matching Threshold**: {config.threshold}
- **Semantic Threshold**: {config.semantic_threshold}
- **Context Analysis**: {config.context_analysis_enabled}
- **Batch Processing**: {config.batch_processing_enabled}
- **Max Batch Size**: {config.max_batch_size}

## AI Provider Settings:
- **Model Config**: {json.dumps(config.ai_provider_config.model_config, indent=2)}
- **Timeout**: {config.ai_provider_config.timeout_seconds}s
- **Max Retries**: {config.ai_provider_config.max_retries}
- **Fallback Provider**: {config.ai_provider_config.fallback_provider or 'None'}

## Decision Mode Behavior:
### DETERMINISTIC Mode:
- Use traditional rule-based matching with exact field comparisons
- Apply weighted similarity scoring with predefined weights: {json.dumps(config.weights)}
- Use compute_similarity for trade comparison
- Rely on exact string matching and numeric tolerances

### LLM Mode:
- Use AI-powered context analysis with ai_analyze_trade_context tool
- Apply semantic field matching with semantic_field_match tool
- Use intelligent_trade_matching for AI-enhanced similarity scoring
- Leverage context-aware field extraction for transaction-type specific matching
- Generate AI explanations for matching decisions

### HYBRID Mode:
- Start with deterministic matching for high-confidence cases
- Fall back to AI analysis for uncertain or complex cases
- Combine confidence scores from both approaches
- Use AI insights to enhance deterministic results

## Enhanced Workflow:
1. **Context Analysis**: Use ai_analyze_trade_context to understand transaction types and identify critical fields
2. **Intelligent Matching**: Apply semantic_field_match for field-level comparison when in LLM/HYBRID mode
3. **Similarity Scoring**: Use intelligent_trade_matching for AI-enhanced scoring or compute_similarity for deterministic
4. **Decision Making**: Combine confidence scores and reasoning from multiple approaches
5. **Status Updates**: Update match status with detailed reasoning and confidence metrics

## Tools Available by Mode:
### Always Available (All Modes):
- fetch_unmatched_trades: Get unmatched trades from specified source
- find_potential_matches: Find candidate matches in opposite source
- update_match_status: Create match records with confidence scores
- mark_as_unmatched: Mark trades that couldn't be matched

### AI-Enhanced Tools (LLM/HYBRID Modes):
- ai_analyze_trade_context: Analyze trade context and identify transaction type
- semantic_field_match: Compare fields using semantic understanding
- intelligent_trade_matching: AI-powered trade similarity scoring
- context_aware_field_extraction: Extract relevant fields based on transaction type

### Traditional Tools (DETERMINISTIC Mode):
- compute_similarity: Traditional weighted similarity scoring

## Output Requirements:
- Always include confidence scores and reasoning for all matching decisions
- Provide transaction type analysis when using AI tools
- Include field-level comparison details
- Maintain audit trail of decision-making approach used
- Handle regional terminology variations intelligently in LLM mode
- Ensure backward compatibility with existing deterministic workflows

## Error Handling:
- Gracefully handle AI service unavailability by falling back to deterministic methods
- Log all AI failures and fallback usage for monitoring
- Maintain processing continuity even when AI services are down
- Provide clear error messages and recovery suggestions"""
    
    # Select tools based on decision mode - always include base tools for backward compatibility
    tools = [
        fetch_unmatched_trades,
        find_potential_matches,
        update_match_status,
        mark_as_unmatched
    ]
    
    # Add mode-specific tools
    if decision_mode == DecisionMode.DETERMINISTIC.value:
        # Traditional deterministic tools
        tools.append(compute_similarity)
    
    elif decision_mode in [DecisionMode.LLM.value, DecisionMode.HYBRID.value]:
        # AI-enhanced tools for LLM and hybrid modes
        tools.extend([
            ai_analyze_trade_context,
            semantic_field_match,
            intelligent_trade_matching,
            context_aware_field_extraction
        ])
        
        # Include traditional tools for hybrid mode fallback
        if decision_mode == DecisionMode.HYBRID.value:
            tools.append(compute_similarity)
    
    # Create agent with configurable model
    model_id = config.ai_provider_config.model_config.get(
        'model_id', 
        'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    )
    
    agent = Agent(
        model=model_id,
        tools=tools,
        system_prompt=system_prompt
    )
    
    # Store configuration for reference
    agent._enhanced_config = config
    agent._decision_mode = decision_mode
    
    logger.info(f"Enhanced Trade Matcher Agent created in {decision_mode} mode with model {model_id}")
    return agent


def create_enhanced_trade_reconciler_agent(config: Optional[EnhancedReconcilerConfig] = None) -> Agent:
    """
    Create an enhanced trade reconciliation agent with AI-powered field comparison and intelligent analysis.
    
    Args:
        config: Enhanced reconciler configuration
        
    Returns:
        Configured Strands Agent for trade reconciliation
    """
    if config is None:
        config = EnhancedReconcilerConfig.from_environment()
    
    decision_mode = config.decision_mode_config.mode
    
    # Build enhanced system prompt with AI capabilities
    system_prompt = f"""You are an enhanced trade reconciliation agent with AI-powered field comparison and intelligent contextual analysis.

## Configuration:
- **Decision Mode**: {decision_mode}
- **AI Provider**: {config.ai_provider_config.provider_type}
- **Region**: {config.ai_provider_config.region}
- **Critical Fields**: {config.critical_fields}
- **AI Explanations**: {config.ai_explanation_enabled}
- **Semantic Field Matching**: {config.semantic_field_matching}
- **Context-Aware Tolerances**: {config.context_aware_tolerances}

## Numeric Tolerances:
{json.dumps({k: float(v) for k, v in config.numeric_tolerance.items()}, indent=2)}

## Field Priority Weights:
{json.dumps(config.field_priority_weights, indent=2)}

## AI Provider Settings:
- **Model Config**: {json.dumps(config.ai_provider_config.model_config, indent=2)}
- **Timeout**: {config.ai_provider_config.timeout_seconds}s
- **Max Retries**: {config.ai_provider_config.max_retries}
- **Fallback Provider**: {config.ai_provider_config.fallback_provider or 'None'}

## Decision Mode Behavior:
### DETERMINISTIC Mode:
- Use traditional exact field comparison with predefined tolerances
- Apply rule-based field matching with string similarity thresholds
- Use compare_fields tool for systematic field-by-field analysis
- Generate standard mismatch explanations

### LLM Mode:
- Use semantic_field_match for intelligent field comparison
- Apply context-aware analysis based on transaction type
- Generate AI-powered explanations using explain_mismatch tool
- Handle non-standardized terminology in commodities trading
- Adapt field comparison based on transaction context

### HYBRID Mode:
- Start with deterministic comparison for exact-match fields (dates, IDs)
- Use AI semantic comparison for descriptive fields (counterparty names, product descriptions)
- Apply context-aware tolerances based on transaction type
- Combine confidence scores from both approaches

## Enhanced Workflow:
1. **Context Analysis**: Use ai_analyze_trade_context to understand transaction type and critical fields
2. **Trade Pair Retrieval**: Get detailed bank and counterparty trade information
3. **Intelligent Field Comparison**: 
   - Use semantic_field_match for field-level semantic analysis in LLM/HYBRID mode
   - Use compare_fields for traditional comparison in DETERMINISTIC mode
4. **Mismatch Explanation**: Generate AI-powered explanations using explain_mismatch tool
5. **Status Determination**: Apply context-aware logic to determine overall reconciliation status
6. **Results Update**: Store detailed reconciliation results with reasoning and confidence scores

## Tools Available by Mode:
### Always Available (All Modes):
- fetch_matched_trades: Get matched trades needing reconciliation
- get_trade_pair: Retrieve bank and counterparty trade details
- determine_overall_status: Determine reconciliation status based on field results
- update_reconciliation_status: Store reconciliation results

### AI-Enhanced Tools (LLM/HYBRID Modes):
- ai_analyze_trade_context: Analyze trade context for intelligent comparison
- semantic_field_match: Compare fields using semantic understanding
- explain_mismatch: Generate AI-powered explanations for field mismatches
- context_aware_field_extraction: Extract relevant fields based on transaction type

### Traditional Tools (DETERMINISTIC Mode):
- compare_fields: Traditional field comparison with tolerances

## Field Comparison Strategy:
### Exact-Match Fields (All Modes):
- Trade dates, settlement dates, currencies, reference IDs
- Use exact string matching with minimal tolerance

### Numeric Fields (Context-Aware):
- Apply transaction-type specific tolerances
- Use percentage-based comparison for notional amounts
- Consider market conventions for price tolerances

### Descriptive Fields (AI-Enhanced in LLM Mode):
- Counterparty names: Use semantic matching for entity recognition
- Product descriptions: Handle terminology variations intelligently
- Settlement instructions: Understand equivalent terms

## Output Requirements:
- Provide detailed field-by-field analysis with explanations
- Include confidence scores for each field comparison
- Generate human-readable explanations for all mismatches
- Maintain audit trail of comparison methods used
- Handle regional and market-specific terminology variations
- Ensure backward compatibility with existing deterministic workflows

## Error Handling:
- Gracefully handle AI service unavailability by falling back to deterministic methods
- Log all AI failures and fallback usage for monitoring
- Maintain processing continuity even when AI services are down
- Provide clear error messages and recovery suggestions

## Financial Domain Intelligence:
- Understand OTC trade terminology and conventions
- Handle commodity-specific field recognition and semantic mapping
- Support non-standardized market terminology through AI normalization
- Detect asset class and apply context-aware field prioritization
- Learn from usage patterns to improve terminology recognition"""
    
    # Select tools based on decision mode - always include base tools for backward compatibility
    tools = [
        fetch_matched_trades,
        get_trade_pair,
        determine_overall_status,
        update_reconciliation_status
    ]
    
    # Add mode-specific tools
    if decision_mode == DecisionMode.DETERMINISTIC.value:
        # Traditional deterministic tools
        tools.append(compare_fields)
    
    elif decision_mode in [DecisionMode.LLM.value, DecisionMode.HYBRID.value]:
        # AI-enhanced tools for LLM and hybrid modes
        tools.extend([
            ai_analyze_trade_context,
            semantic_field_match,
            explain_mismatch,
            context_aware_field_extraction
        ])
        
        # Include traditional tools for hybrid mode fallback
        if decision_mode == DecisionMode.HYBRID.value:
            tools.append(compare_fields)
    
    # Create agent with configurable model
    model_id = config.ai_provider_config.model_config.get(
        'model_id', 
        'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    )
    
    agent = Agent(
        model=model_id,
        tools=tools,
        system_prompt=system_prompt
    )
    
    # Store configuration for reference
    agent._enhanced_config = config
    agent._decision_mode = decision_mode
    
    logger.info(f"Enhanced Trade Reconciler Agent created in {decision_mode} mode with model {model_id}")
    return agent


def create_enhanced_report_generator_agent(config: Optional[EnhancedReportConfig] = None) -> Agent:
    """
    Create an enhanced report generation agent with AI decision rationale and comprehensive insights.
    
    Args:
        config: Enhanced report configuration
        
    Returns:
        Configured Strands Agent for report generation
    """
    if config is None:
        config = EnhancedReportConfig.from_environment()
    
    # Build enhanced system prompt with AI decision rationale capabilities
    system_prompt = f"""You are an enhanced report generation agent that creates comprehensive reconciliation reports with AI decision rationale and confidence scoring.

## Configuration:
- **AI Provider**: {config.ai_provider_config.provider_type}
- **Region**: {config.ai_provider_config.region}
- **Report Bucket**: {config.report_bucket}
- **Include AI Explanations**: {config.include_ai_explanations}
- **Include Confidence Scores**: {config.include_confidence_scores}
- **Include Decision Rationale**: {config.include_decision_rationale}
- **Export Formats**: {config.export_formats}
- **Include Summary Stats**: {config.include_summary_stats}
- **Include Field Details**: {config.include_field_details}

## AI Provider Settings:
- **Model Config**: {json.dumps(config.ai_provider_config.model_config, indent=2)}
- **Timeout**: {config.ai_provider_config.timeout_seconds}s
- **Max Retries**: {config.ai_provider_config.max_retries}

## Enhanced Reporting Capabilities:
### AI Decision Rationale:
- Include detailed explanations of AI-powered matching decisions
- Document confidence scores for each trade pair and field comparison
- Provide reasoning for semantic field matching results
- Explain context-aware analysis outcomes

### Comprehensive Analysis:
- Executive summary with key insights and recommendations
- Detailed reconciliation statistics with trend analysis
- Field-level mismatch analysis with AI explanations
- Performance metrics comparing AI vs deterministic approaches

### Multi-Format Output:
- JSON: Structured data for system integration
- CSV: Tabular data for spreadsheet analysis
- PDF: Human-readable reports for stakeholders

## Report Structure:
### Executive Summary:
- Overall reconciliation status and key metrics
- AI vs deterministic processing statistics
- Critical issues requiring attention
- Recommendations for process improvements

### Detailed Analysis:
- Trade-by-trade reconciliation results
- Field comparison details with confidence scores
- AI decision explanations and rationale
- Context analysis insights

### Technical Metadata:
- Processing timestamps and duration
- AI provider configuration used
- Decision mode statistics
- Error logs and fallback usage

### Performance Metrics:
- Processing speed comparisons
- Accuracy improvements from AI
- Confidence score distributions
- System health indicators

## Enhanced Workflow:
1. **Data Collection**: Fetch reconciliation results with all metadata
2. **AI Insights Analysis**: Extract AI decision rationale and confidence scores
3. **Statistical Analysis**: Generate comprehensive statistics and trends
4. **Report Generation**: Create structured reports with AI explanations
5. **Multi-Format Export**: Generate reports in all configured formats
6. **Storage & Distribution**: Store reports with proper metadata

## Tools Available:
- fetch_reconciliation_results: Get reconciliation data with AI metadata
- generate_reconciliation_report: Create comprehensive reports with AI insights
- store_report: Save reports with proper categorization and metadata

## Output Requirements:
### When AI Explanations Enabled:
- Include detailed AI decision reasoning for each trade pair
- Document semantic field matching explanations
- Provide context analysis insights
- Show confidence score breakdowns

### When Confidence Scores Enabled:
- Include match confidence percentages
- Show field-level confidence metrics
- Provide uncertainty indicators
- Document confidence thresholds used

### When Decision Rationale Enabled:
- Explain why specific decision modes were used
- Document fallback scenarios and reasons
- Show hybrid mode decision logic
- Include performance impact analysis

## Report Quality Standards:
- Clear, actionable insights for operations teams
- Technical depth appropriate for different audiences
- Consistent formatting across all export formats
- Comprehensive audit trail for compliance
- User-friendly visualizations and summaries

## Error Handling:
- Handle missing AI metadata gracefully
- Provide fallback reporting when AI insights unavailable
- Log report generation issues for troubleshooting
- Ensure report completeness even with partial data

## Backward Compatibility:
- Support reports from deterministic-only processing
- Handle mixed AI/deterministic result sets
- Maintain existing report format compatibility
- Provide migration guidance for legacy reports"""
    
    tools = [
        fetch_reconciliation_results,
        generate_reconciliation_report,
        store_report
    ]
    
    # Create agent with configurable model
    model_id = config.ai_provider_config.model_config.get(
        'model_id', 
        'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    )
    
    agent = Agent(
        model=model_id,
        tools=tools,
        system_prompt=system_prompt
    )
    
    # Store configuration for reference
    agent._enhanced_config = config
    
    logger.info(f"Enhanced Report Generator Agent created with model {model_id}")
    return agent


# Convenience functions for running enhanced agents with AI capabilities
def run_enhanced_trade_matching(source: str = "BANK", limit: int = 100, config: Optional[EnhancedMatcherConfig] = None) -> str:
    """Run enhanced trade matching with AI capabilities and backward compatibility."""
    agent = create_enhanced_trade_matcher_agent(config)
    decision_mode = agent._decision_mode
    
    query = f"""Process enhanced trade matching for {source} source with limit {limit} using {decision_mode} mode.

## Enhanced Workflow Instructions:

### Step 1: Context Analysis (LLM/HYBRID modes)
{f"- Use ai_analyze_trade_context to understand transaction types and identify critical fields" if decision_mode in ['llm', 'hybrid'] else "- Skip AI context analysis in deterministic mode"}

### Step 2: Trade Retrieval
- Fetch unmatched trades from the {source} source using fetch_unmatched_trades
- For each trade, find potential matches using find_potential_matches

### Step 3: Intelligent Matching
{f'''- Use ai_analyze_trade_context for each trade to understand transaction type
- Apply semantic_field_match for field-level semantic comparison
- Use intelligent_trade_matching for AI-enhanced similarity scoring
- Leverage context_aware_field_extraction for transaction-specific matching''' if decision_mode == 'llm' else ''}
{f'''- Start with compute_similarity for high-confidence deterministic matches
- Fall back to AI tools (ai_analyze_trade_context, intelligent_trade_matching) for uncertain cases
- Combine confidence scores from both approaches''' if decision_mode == 'hybrid' else ''}
{f"- Use compute_similarity with predefined weights for traditional matching" if decision_mode == 'deterministic' else ''}

### Step 4: Decision Making & Status Updates
- Evaluate matches using the configured threshold and decision mode
- Update match status for successful matches with detailed reasoning
- Mark unmatched trades appropriately with confidence scores

### Step 5: Comprehensive Results
- Return detailed statistics including:
  - Total trades processed and matched
  - Average confidence scores by decision method
  - Transaction type breakdown (if AI analysis used)
  - Field-level matching insights
  - Performance metrics and processing time
  - Any AI fallback usage or errors

Ensure backward compatibility while leveraging enhanced AI capabilities based on configuration."""
    
    result = agent(query)
    return result.message


def run_enhanced_trade_reconciliation(limit: int = 100, config: Optional[EnhancedReconcilerConfig] = None) -> str:
    """Run enhanced trade reconciliation with AI-powered field comparison and intelligent analysis."""
    agent = create_enhanced_trade_reconciler_agent(config)
    decision_mode = agent._decision_mode
    
    query = f"""Process enhanced trade reconciliation for up to {limit} matched trades using {decision_mode} mode.

## Enhanced Reconciliation Workflow:

### Step 1: Context Analysis (LLM/HYBRID modes)
{f"- Use ai_analyze_trade_context to understand transaction types and critical fields for each trade pair" if decision_mode in ['llm', 'hybrid'] else "- Skip AI context analysis in deterministic mode"}

### Step 2: Trade Pair Retrieval
- Fetch matched trades that need reconciliation using fetch_matched_trades
- Get detailed trade pair information using get_trade_pair

### Step 3: Intelligent Field Comparison
{f'''- Use semantic_field_match for intelligent field-level comparison
- Apply context-aware analysis based on transaction type
- Handle non-standardized terminology in commodities trading
- Use explain_mismatch to generate AI-powered explanations for mismatches''' if decision_mode == 'llm' else ''}
{f'''- Use compare_fields for exact-match fields (dates, IDs, currencies)
- Apply semantic_field_match for descriptive fields (counterparty names, product descriptions)
- Use context-aware tolerances based on transaction type
- Generate AI explanations for complex mismatches using explain_mismatch''' if decision_mode == 'hybrid' else ''}
{f"- Use compare_fields with predefined tolerances for traditional field comparison" if decision_mode == 'deterministic' else ''}

### Step 4: Mismatch Analysis & Explanation
- Generate detailed explanations for all field mismatches
{f"- Use explain_mismatch tool for AI-powered, human-readable explanations" if decision_mode in ['llm', 'hybrid'] else "- Provide standard deterministic explanations"}
- Include confidence scores and reasoning for each field comparison

### Step 5: Status Determination & Updates
- Use determine_overall_status with context-aware logic
- Apply field priority weights based on transaction type
- Update reconciliation status with comprehensive results using update_reconciliation_status

### Step 6: Comprehensive Results
- Return detailed statistics including:
  - Field-by-field analysis with explanations and confidence scores
  - Overall reconciliation status breakdown
  - AI decision rationale and reasoning (if applicable)
  - Transaction type analysis and critical field identification
  - Performance metrics and processing efficiency
  - Error handling and fallback usage statistics

Ensure all field comparisons include detailed reasoning and maintain backward compatibility."""
    
    result = agent(query)
    return result.message


def run_enhanced_report_generation(status_filter: Optional[str] = None, limit: int = 1000, config: Optional[EnhancedReportConfig] = None) -> str:
    """Run enhanced report generation with AI decision rationale and comprehensive insights."""
    agent = create_enhanced_report_generator_agent(config)
    
    filter_clause = f" with status filter '{status_filter}'" if status_filter else ""
    query = f"""Generate an enhanced reconciliation report for up to {limit} results{filter_clause} with AI decision rationale and confidence scoring.

## Enhanced Report Generation Workflow:

### Step 1: Data Collection with AI Metadata
- Fetch reconciliation results using fetch_reconciliation_results
- Include all AI decision metadata, confidence scores, and reasoning
- Collect performance metrics from AI vs deterministic processing

### Step 2: AI Insights Analysis
{f'''- Extract AI decision rationale for each trade pair
- Analyze confidence score distributions and patterns
- Document semantic field matching explanations
- Compile context analysis insights''' if config and config.include_ai_explanations else '- Skip AI insights analysis (disabled in configuration)'}

### Step 3: Comprehensive Report Generation
- Use generate_reconciliation_report to create structured analysis
- Include the following enhanced sections:

#### Executive Summary:
- Overall reconciliation status with key performance indicators
- AI vs deterministic processing statistics and efficiency gains
- Critical issues requiring immediate attention
- Strategic recommendations for process improvements

#### Detailed Analysis:
{f'''- Trade-by-trade reconciliation results with AI explanations
- Field comparison details with confidence scores and reasoning
- Context analysis insights showing transaction type identification
- Semantic matching results and terminology handling''' if config and config.include_ai_explanations else '- Standard reconciliation results without AI explanations'}

#### Performance Metrics:
{f'''- Processing speed comparisons between AI and deterministic methods
- Accuracy improvements achieved through AI analysis
- Confidence score distributions and reliability metrics
- System health indicators and AI service availability''' if config and config.include_confidence_scores else '- Basic performance metrics without confidence analysis'}

#### Technical Metadata:
{f'''- AI provider configuration and model settings used
- Decision mode statistics and fallback usage patterns
- Error logs and recovery scenarios
- Processing timestamps and duration analysis''' if config and config.include_decision_rationale else '- Standard technical metadata without decision rationale'}

### Step 4: Multi-Format Export
- Generate reports in configured formats: {config.export_formats if config else ['json', 'csv', 'pdf']}
- Ensure consistent formatting across all export types
- Include appropriate visualizations for each format

### Step 5: Storage & Distribution
- Store reports using store_report with proper categorization
- Include comprehensive metadata for searchability
- Ensure reports are accessible for stakeholder review

### Output Requirements:
- Clear, actionable insights for operations teams
- Technical depth appropriate for different audiences
- Comprehensive audit trail for compliance requirements
- User-friendly summaries with detailed technical appendices
- Backward compatibility with existing report consumers

Generate a comprehensive report that demonstrates the value of AI-enhanced reconciliation while maintaining full backward compatibility."""
    
    result = agent(query)
    return result.message


# Factory function for creating all agents
async def create_enhanced_agents() -> tuple[Agent, Agent, Agent]:
    """Create and initialize all enhanced agents with proper configuration."""
    try:
        matcher_config, reconciler_config, report_config = load_enhanced_configurations()
        
        matcher_agent = create_enhanced_trade_matcher_agent(matcher_config)
        reconciler_agent = create_enhanced_trade_reconciler_agent(reconciler_config)
        report_agent = create_enhanced_report_generator_agent(report_config)
        
        logger.info("All enhanced agents created successfully using Strands SDK")
        return matcher_agent, reconciler_agent, report_agent
        
    except Exception as e:
        logger.error(f"Error creating enhanced agents: {e}")
        raise