"""
Enhanced AI-Powered Trade Reconciliation Workflow

This module demonstrates the complete enhanced workflow using the AI-powered Strands agents
with configurable decision modes and AI providers.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from .enhanced_agents import (
    create_enhanced_trade_matcher_agent,
    create_enhanced_trade_reconciler_agent, 
    create_enhanced_report_generator_agent,
    create_enhanced_agents,
    run_enhanced_trade_matching,
    run_enhanced_trade_reconciliation,
    run_enhanced_report_generation
)
from .enhanced_config import (
    EnhancedMatcherConfig,
    EnhancedReconcilerConfig,
    EnhancedReportConfig,
    DecisionMode,
    AIProviderType
)

logger = logging.getLogger(__name__)


class EnhancedReconciliationWorkflow:
    """
    Enhanced reconciliation workflow that orchestrates the AI-powered agents.
    """
    
    def __init__(self, 
                 matcher_config: Optional[EnhancedMatcherConfig] = None,
                 reconciler_config: Optional[EnhancedReconcilerConfig] = None,
                 report_config: Optional[EnhancedReportConfig] = None):
        """Initialize the enhanced workflow with configurations."""
        self.matcher_config = matcher_config or EnhancedMatcherConfig.from_environment()
        self.reconciler_config = reconciler_config or EnhancedReconcilerConfig.from_environment()
        self.report_config = report_config or EnhancedReportConfig.from_environment()
        
        self.matcher_agent = None
        self.reconciler_agent = None
        self.report_agent = None
        
        logger.info("Enhanced Reconciliation Workflow initialized")
    
    async def initialize_agents(self) -> bool:
        """Initialize all enhanced agents."""
        try:
            self.matcher_agent = create_enhanced_trade_matcher_agent(self.matcher_config)
            self.reconciler_agent = create_enhanced_trade_reconciler_agent(self.reconciler_config)
            self.report_agent = create_enhanced_report_generator_agent(self.report_config)
            
            logger.info("Agents initialized successfully using Strands SDK")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            return False
    
    async def run_complete_workflow(self, 
                                  source: str = "BANK",
                                  matching_limit: int = 100,
                                  reconciliation_limit: int = 100,
                                  report_limit: int = 1000) -> Dict[str, Any]:
        """
        Run the complete enhanced reconciliation workflow.
        
        Args:
            source: Source to start matching from ("BANK" or "COUNTERPARTY")
            matching_limit: Maximum trades to process in matching phase
            reconciliation_limit: Maximum matches to process in reconciliation phase
            report_limit: Maximum results to include in report
            
        Returns:
            Dictionary with complete workflow results
        """
        workflow_start = datetime.now()
        logger.info("Starting enhanced reconciliation workflow")
        
        # Initialize agents if not already done
        if not self.matcher_agent:
            await self.initialize_agents()
        
        workflow_results = {
            "workflow_id": f"enhanced-workflow-{workflow_start.strftime('%Y%m%d-%H%M%S')}",
            "start_time": workflow_start.isoformat(),
            "configuration": {
                "matcher_mode": self.matcher_config.decision_mode_config.mode,
                "reconciler_mode": self.reconciler_config.decision_mode_config.mode,
                "ai_provider": self.matcher_config.ai_provider_config.provider_type,
                "ai_region": self.matcher_config.ai_provider_config.region
            },
            "phases": {}
        }
        
        try:
            # Phase 1: Enhanced Trade Matching
            logger.info("Phase 1: Starting enhanced trade matching")
            phase1_start = datetime.now()
            
            matching_results = await run_enhanced_trade_matching(
                source=source,
                limit=matching_limit
            )
            
            phase1_duration = (datetime.now() - phase1_start).total_seconds()
            workflow_results["phases"]["matching"] = {
                "duration_seconds": phase1_duration,
                "results": matching_results,
                "status": "completed"
            }
            
            logger.info(f"Phase 1 completed in {phase1_duration:.2f}s - "
                       f"Status: {matching_results.get('status', 'unknown')}")
            
            # Phase 2: Enhanced Trade Reconciliation
            logger.info("Phase 2: Starting enhanced trade reconciliation")
            phase2_start = datetime.now()
            
            reconciliation_results = await run_enhanced_trade_reconciliation(
                limit=reconciliation_limit
            )
            
            phase2_duration = (datetime.now() - phase2_start).total_seconds()
            workflow_results["phases"]["reconciliation"] = {
                "duration_seconds": phase2_duration,
                "results": reconciliation_results,
                "status": "completed"
            }
            
            logger.info(f"Phase 2 completed in {phase2_duration:.2f}s - "
                       f"Status: {reconciliation_results.get('status', 'unknown')}")
            
            # Phase 3: Enhanced Report Generation
            logger.info("Phase 3: Starting enhanced report generation")
            phase3_start = datetime.now()
            
            report_results = await run_enhanced_report_generation(
                status_filter=None,
                limit=report_limit
            )
            
            phase3_duration = (datetime.now() - phase3_start).total_seconds()
            workflow_results["phases"]["reporting"] = {
                "duration_seconds": phase3_duration,
                "results": report_results,
                "status": "completed"
            }
            
            logger.info(f"Phase 3 completed in {phase3_duration:.2f}s - "
                       f"Status: {report_results.get('status', 'unknown')}")
            
            # Calculate total workflow metrics
            total_duration = (datetime.now() - workflow_start).total_seconds()
            workflow_results.update({
                "end_time": datetime.now().isoformat(),
                "total_duration_seconds": total_duration,
                "status": "completed",
                "summary": {
                    "matching_status": matching_results.get("status", "unknown"),
                    "reconciliation_status": reconciliation_results.get("status", "unknown"),
                    "report_status": report_results.get("status", "unknown"),
                    "total_processing_time": f"{total_duration:.2f}s"
                }
            })
            
            logger.info(f"Enhanced workflow completed successfully in {total_duration:.2f}s")
            return workflow_results
            
        except Exception as e:
            logger.error(f"Enhanced workflow failed: {e}")
            workflow_results.update({
                "end_time": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            })
            raise
    
    async def run_matching_only(self, source: str = "BANK", limit: int = 100) -> Dict[str, Any]:
        """Run only the enhanced matching phase."""
        return await run_enhanced_trade_matching(source, limit)
    
    async def run_reconciliation_only(self, limit: int = 100) -> Dict[str, Any]:
        """Run only the enhanced reconciliation phase."""
        return await run_enhanced_trade_reconciliation(limit)
    
    async def run_reporting_only(self, status_filter: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
        """Run only the enhanced reporting phase."""
        return await run_enhanced_report_generation(status_filter, limit)
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "matcher_configuration": {
                "decision_mode": self.matcher_config.decision_mode_config.mode,
                "ai_provider": self.matcher_config.ai_provider_config.provider_type,
                "region": self.matcher_config.ai_provider_config.region,
                "semantic_threshold": self.matcher_config.semantic_threshold,
                "context_analysis_enabled": self.matcher_config.context_analysis_enabled,
                "weights": self.matcher_config.weights
            },
            "reconciler_configuration": {
                "decision_mode": self.reconciler_config.decision_mode_config.mode,
                "ai_provider": self.reconciler_config.ai_provider_config.provider_type,
                "region": self.reconciler_config.ai_provider_config.region,
                "semantic_field_matching": self.reconciler_config.semantic_field_matching,
                "ai_explanation_enabled": self.reconciler_config.ai_explanation_enabled,
                "context_aware_tolerances": self.reconciler_config.context_aware_tolerances,
                "critical_fields": self.reconciler_config.critical_fields
            },
            "report_configuration": {
                "ai_provider": self.report_config.ai_provider_config.provider_type,
                "include_ai_explanations": self.report_config.include_ai_explanations,
                "include_confidence_scores": self.report_config.include_confidence_scores,
                "include_decision_rationale": self.report_config.include_decision_rationale,
                "export_formats": self.report_config.export_formats
            }
        }


# Convenience functions for different workflow scenarios

async def run_deterministic_workflow(matching_limit: int = 100, 
                                   reconciliation_limit: int = 100,
                                   report_limit: int = 1000) -> Dict[str, Any]:
    """Run workflow in pure deterministic mode."""
    from .enhanced_config import AIProviderConfig, DecisionModeConfig
    
    # Create deterministic configurations
    decision_config = DecisionModeConfig(mode=DecisionMode.DETERMINISTIC.value)
    ai_config = AIProviderConfig.from_environment()  # Will be ignored in deterministic mode
    
    matcher_config = EnhancedMatcherConfig(
        decision_mode_config=decision_config,
        ai_provider_config=ai_config
    )
    reconciler_config = EnhancedReconcilerConfig(
        decision_mode_config=decision_config,
        ai_provider_config=ai_config
    )
    report_config = EnhancedReportConfig(ai_provider_config=ai_config)
    
    workflow = EnhancedReconciliationWorkflow(matcher_config, reconciler_config, report_config)
    return await workflow.run_complete_workflow(
        matching_limit=matching_limit,
        reconciliation_limit=reconciliation_limit,
        report_limit=report_limit
    )


async def run_llm_workflow(ai_provider_type: str = "bedrock",
                          region: str = "us-east-1",
                          matching_limit: int = 100,
                          reconciliation_limit: int = 100,
                          report_limit: int = 1000) -> Dict[str, Any]:
    """Run workflow in pure LLM mode."""
    from .enhanced_config import AIProviderConfig, DecisionModeConfig
    
    # Create LLM configurations
    decision_config = DecisionModeConfig(mode=DecisionMode.LLM.value)
    ai_config = AIProviderConfig(
        provider_type=ai_provider_type,
        region=region,
        model_config={}  # Will be populated from environment
    )
    
    matcher_config = EnhancedMatcherConfig(
        decision_mode_config=decision_config,
        ai_provider_config=ai_config
    )
    reconciler_config = EnhancedReconcilerConfig(
        decision_mode_config=decision_config,
        ai_provider_config=ai_config
    )
    report_config = EnhancedReportConfig(ai_provider_config=ai_config)
    
    workflow = EnhancedReconciliationWorkflow(matcher_config, reconciler_config, report_config)
    return await workflow.run_complete_workflow(
        matching_limit=matching_limit,
        reconciliation_limit=reconciliation_limit,
        report_limit=report_limit
    )


async def run_hybrid_workflow(ai_provider_type: str = "bedrock",
                             region: str = "us-east-1",
                             matching_limit: int = 100,
                             reconciliation_limit: int = 100,
                             report_limit: int = 1000) -> Dict[str, Any]:
    """Run workflow in hybrid mode."""
    from .enhanced_config import AIProviderConfig, DecisionModeConfig
    
    # Create hybrid configurations
    decision_config = DecisionModeConfig(mode=DecisionMode.HYBRID.value)
    ai_config = AIProviderConfig(
        provider_type=ai_provider_type,
        region=region,
        model_config={}  # Will be populated from environment
    )
    
    matcher_config = EnhancedMatcherConfig(
        decision_mode_config=decision_config,
        ai_provider_config=ai_config
    )
    reconciler_config = EnhancedReconcilerConfig(
        decision_mode_config=decision_config,
        ai_provider_config=ai_config
    )
    report_config = EnhancedReportConfig(ai_provider_config=ai_config)
    
    workflow = EnhancedReconciliationWorkflow(matcher_config, reconciler_config, report_config)
    return await workflow.run_complete_workflow(
        matching_limit=matching_limit,
        reconciliation_limit=reconciliation_limit,
        report_limit=report_limit
    )


# Main execution function for testing
async def main():
    """Main function for testing the enhanced workflow."""
    import os
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration from environment
    decision_mode = os.getenv('DECISION_MODE', 'deterministic')
    ai_provider = os.getenv('AI_PROVIDER_TYPE', 'bedrock')
    region = os.getenv('AI_PROVIDER_REGION', 'us-east-1')
    
    logger.info(f"Running enhanced workflow in {decision_mode} mode with {ai_provider} provider")
    
    try:
        if decision_mode == 'deterministic':
            results = await run_deterministic_workflow()
        elif decision_mode == 'llm':
            results = await run_llm_workflow(ai_provider, region)
        elif decision_mode == 'hybrid':
            results = await run_hybrid_workflow(ai_provider, region)
        else:
            raise ValueError(f"Invalid decision mode: {decision_mode}")
        
        # Print results summary
        print("\n" + "="*80)
        print("ENHANCED WORKFLOW RESULTS SUMMARY")
        print("="*80)
        print(f"Workflow ID: {results['workflow_id']}")
        print(f"Total Duration: {results['total_duration_seconds']:.2f} seconds")
        print(f"Status: {results['status']}")
        print(f"Configuration: {results['configuration']}")
        print("\nPhase Results:")
        for phase_name, phase_data in results['phases'].items():
            print(f"  {phase_name.title()}: {phase_data['status']} ({phase_data['duration_seconds']:.2f}s)")
        
        print(f"\nSummary:")
        for key, value in results['summary'].items():
            print(f"  {key}: {value}")
        
        return results
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())