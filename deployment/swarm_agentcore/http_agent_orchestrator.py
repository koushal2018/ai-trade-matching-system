#!/usr/bin/env python3
"""
HTTP Agent Orchestrator for Trade Matching System

This orchestrator communicates with deployed AgentCore agents using standard HTTP calls
via the `agentcore invoke` CLI, which is simpler than A2A protocol and works with
your existing deployed agents.
"""

import asyncio
import json
import logging
import os
import subprocess
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent directories for invoking via CLI
AGENT_CONFIGS = {
    "pdf_adapter": {
        "directory": "/Users/koushald/ai-trade-matching-system-2/deployment/pdf_adapter",
        "name": "pdf_adapter_agent",
        "description": "Downloads PDFs from S3, extracts text via Bedrock multimodal, saves canonical output"
    },
    "trade_extractor": {
        "directory": "/Users/koushald/ai-trade-matching-system-2/deployment/trade_extraction", 
        "name": "trade_extraction_agent",
        "description": "Reads canonical output, parses trade fields, stores in DynamoDB"
    },
    "trade_matcher": {
        "directory": "/Users/koushald/ai-trade-matching-system-2/deployment/trade_matching",
        "name": "trade_matching_agent",
        "description": "Scans both tables, matches by attributes (NOT Trade_ID), generates reports"
    },
    "exception_handler": {
        "directory": "/Users/koushald/ai-trade-matching-system-2/deployment/exception_management",
        "name": "exception_manager",
        "description": "Analyzes breaks, calculates SLA deadlines, stores exception records"
    }
}


class AgentCoreHTTPClient:
    """
    HTTP client for communicating with deployed AgentCore agents via CLI.
    """
    
    def __init__(self, agent_name: str, agent_directory: str, timeout: int = 300):
        """
        Initialize HTTP client for a specific agent.
        
        Args:
            agent_name: Name of the AgentCore agent
            agent_directory: Directory containing the agent's agentcore.yaml
            timeout: Request timeout in seconds
        """
        self.agent_name = agent_name
        self.agent_directory = agent_directory
        self.timeout = timeout
        
        logger.info(f"Initialized HTTP client for {agent_name} in {agent_directory}")
    
    async def invoke_agent(self, payload: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke the AgentCore agent with a payload.
        
        Args:
            payload: JSON payload to send to the agent
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            Agent response as dictionary
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Ensure session ID meets AgentCore minimum length requirement (33+ chars)
        if len(session_id) < 33:
            session_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
        
        # Prepare the payload
        payload_str = json.dumps(payload)
        
        # Build agentcore invoke command for dev mode
        cmd = [
            "agentcore", "invoke",
            "--dev", "--port", "8082",
            payload_str
        ]
        
        try:
            logger.info(f"Invoking {self.agent_name} with session {session_id}")
            logger.debug(f"Payload: {payload}")
            
            # Change to agent directory and run command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.agent_directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            if process.returncode == 0:
                # Parse JSON response
                try:
                    raw_output = stdout.decode()
                    
                    # Check if this is dev server format
                    if "Response from dev server:" in raw_output:
                        # Extract the response part after "Response from dev server:"
                        response_section = raw_output.split("Response from dev server:")[-1].strip()
                        # Parse the outer response
                        outer_response = json.loads(response_section)
                        # Parse the inner response string
                        if 'response' in outer_response and isinstance(outer_response['response'], str):
                            inner_response = json.loads(outer_response['response'])
                            return {
                                "success": True,
                                "response": inner_response,
                                "session_id": session_id,
                                "agent_name": self.agent_name
                            }
                        else:
                            return {
                                "success": True,
                                "response": outer_response,
                                "session_id": session_id,
                                "agent_name": self.agent_name
                            }
                    else:
                        # Regular AgentCore format
                        response = json.loads(raw_output)
                        return {
                            "success": True,
                            "response": response,
                            "session_id": session_id,
                            "agent_name": self.agent_name
                        }
                except json.JSONDecodeError as e:
                    raw_output = stdout.decode()
                    logger.debug(f"Parsing AgentCore output from {self.agent_name}")
                    
                    # AgentCore includes formatting, look for the JSON in "Response:" section
                    if "Response:" in raw_output:
                        response_section = raw_output.split("Response:")[-1].strip()
                        # Handle multi-line JSON (AgentCore may wrap long lines)
                        json_lines = []
                        for line in response_section.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('│') and not line.startswith('╭') and not line.startswith('╰'):
                                json_lines.append(line)
                        
                        json_text = ''.join(json_lines)
                        try:
                            response = json.loads(json_text)
                            logger.info(f"Successfully parsed AgentCore response from {self.agent_name}")
                            return {
                                "success": True,
                                "response": response,
                                "session_id": session_id,
                                "agent_name": self.agent_name
                            }
                        except json.JSONDecodeError as parse_error:
                            logger.error(f"Failed to parse extracted JSON: {json_text}")
                    
                    # Fallback: Try to extract JSON from any line
                    lines = raw_output.strip().split('\n')
                    for line in reversed(lines):
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                response = json.loads(line)
                                return {
                                    "success": True,
                                    "response": response,
                                    "session_id": session_id,
                                    "agent_name": self.agent_name
                                }
                            except json.JSONDecodeError:
                                continue
                    
                    return {
                        "success": False,
                        "error": f"Invalid JSON response: {e}",
                        "raw_stdout": raw_output,
                        "session_id": session_id,
                        "agent_name": self.agent_name
                    }
            else:
                return {
                    "success": False,
                    "error": f"Agent invocation failed (exit code {process.returncode})",
                    "stderr": stderr.decode(),
                    "stdout": stdout.decode(),
                    "session_id": session_id,
                    "agent_name": self.agent_name
                }
                
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Agent invocation timed out after {self.timeout} seconds",
                "session_id": session_id,
                "agent_name": self.agent_name
            }
        except Exception as e:
            logger.error(f"Agent invocation failed for {self.agent_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "agent_name": self.agent_name
            }


class TradeMatchingHTTPOrchestrator:
    """
    HTTP orchestrator for the Trade Matching workflow using deployed AgentCore agents.
    
    This orchestrator coordinates between your four deployed AgentCore agents using
    standard HTTP invocation via the agentcore CLI.
    """
    
    def __init__(self):
        """Initialize the HTTP orchestrator."""
        # Create HTTP clients for each agent
        self.agents = {}
        for agent_name, config in AGENT_CONFIGS.items():
            self.agents[agent_name] = AgentCoreHTTPClient(
                agent_name=config["name"],
                agent_directory=config["directory"]
            )
        
        logger.info("Initialized Trade Matching HTTP Orchestrator")
        logger.info(f"Configured agents: {list(self.agents.keys())}")
    
    async def process_trade_confirmation(
        self,
        document_path: str,
        source_type: str,
        document_id: str,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a trade confirmation using HTTP agent communication.
        
        This method orchestrates the workflow:
        1. PDF Adapter: Download and extract text from PDF
        2. Trade Extraction: Parse and store trade data
        3. Trade Matching: Match against existing trades
        4. Exception Management: Handle any issues
        
        Args:
            document_path: S3 path to the PDF
            source_type: BANK or COUNTERPARTY
            document_id: Unique document identifier
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Processing result with status and details
        """
        if correlation_id is None:
            correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
        
        session_id = f"trade_{document_id}_{uuid.uuid4()}"
        
        try:
            # Step 1: PDF Adapter - Download and extract text
            logger.info(f"Step 1: PDF Adapter processing for {document_id}")
            
            pdf_payload = {
                "document_path": document_path,
                "source_type": source_type
            }
            
            pdf_result = await self.agents["pdf_adapter"].invoke_agent(pdf_payload, f"{session_id[:20]}_pdf_{uuid.uuid4().hex[:8]}")
            
            if not pdf_result.get("success"):
                return {
                    "success": False,
                    "step": "pdf_adapter",
                    "error": pdf_result.get("error"),
                    "document_id": document_id,
                    "correlation_id": correlation_id,
                    "execution_mode": "HTTP Orchestrator"
                }
            
            # Step 2: Trade Extraction - Parse and store data
            logger.info(f"Step 2: Trade Extraction processing for {document_id}")
            
            extraction_payload = {
                "document_id": document_id,
                "source_type": source_type
            }
            
            extraction_result = await self.agents["trade_extractor"].invoke_agent(extraction_payload, f"{session_id[:20]}_ext_{uuid.uuid4().hex[:8]}")
            
            if not extraction_result.get("success"):
                return {
                    "success": False,
                    "step": "trade_extraction",
                    "error": extraction_result.get("error"),
                    "document_id": document_id,
                    "correlation_id": correlation_id,
                    "pdf_result": pdf_result,
                    "execution_mode": "HTTP Orchestrator"
                }
            
            # Step 3: Trade Matching - Analyze matches
            logger.info(f"Step 3: Trade Matching processing for {document_id}")
            
            matching_payload = {
                "document_id": document_id,
                "source_type": source_type
            }
            
            matching_result = await self.agents["trade_matcher"].invoke_agent(matching_payload, f"{session_id[:20]}_match_{uuid.uuid4().hex[:8]}")
            
            if not matching_result.get("success"):
                return {
                    "success": False,
                    "step": "trade_matching",
                    "error": matching_result.get("error"),
                    "document_id": document_id,
                    "correlation_id": correlation_id,
                    "pdf_result": pdf_result,
                    "extraction_result": extraction_result,
                    "execution_mode": "HTTP Orchestrator"
                }
            
            # Step 4: Exception Management (if needed)
            # Check if the matching result indicates issues that need exception handling
            matching_response = str(matching_result.get("response", ""))
            needs_exception_handling = any(term in matching_response.lower() for term in [
                "review_required", "break", "exception", "error", "discrepancy", "mismatch"
            ])
            
            exception_result = None
            if needs_exception_handling:
                logger.info(f"Step 4: Exception Management processing for {document_id}")
                
                exception_payload = {
                    "document_id": document_id,
                    "source_type": source_type
                }
                
                exception_result = await self.agents["exception_handler"].invoke_agent(exception_payload, f"{session_id[:20]}_exc_{uuid.uuid4().hex[:8]}")
            
            # Compile final result
            result = {
                "success": True,
                "document_id": document_id,
                "correlation_id": correlation_id,
                "session_id": session_id,
                "execution_mode": "HTTP Orchestrator",
                "workflow_steps": {
                    "pdf_adapter": pdf_result,
                    "trade_extraction": extraction_result,
                    "trade_matching": matching_result
                }
            }
            
            if exception_result:
                result["workflow_steps"]["exception_management"] = exception_result
            
            logger.info(f"HTTP orchestration completed successfully for {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"HTTP orchestration failed for {document_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "document_id": document_id,
                "correlation_id": correlation_id,
                "execution_mode": "HTTP Orchestrator"
            }


async def process_trade_with_http_orchestrator(
    document_path: str,
    source_type: str,
    document_id: str,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a trade confirmation using HTTP orchestration.
    
    Args:
        document_path: S3 path to the PDF
        source_type: BANK or COUNTERPARTY
        document_id: Unique document identifier
        correlation_id: Optional correlation ID for tracing
        
    Returns:
        Processing result with status and details
    """
    orchestrator = TradeMatchingHTTPOrchestrator()
    
    return await orchestrator.process_trade_confirmation(
        document_path=document_path,
        source_type=source_type,
        document_id=document_id,
        correlation_id=correlation_id
    )


# ============================================================================
# CLI Entry Point for HTTP Orchestrator Mode
# ============================================================================

def main_http():
    """CLI entrypoint for HTTP orchestrator mode."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Trade Matching HTTP Orchestrator - Process trade confirmations using deployed AgentCore agents"
    )
    parser.add_argument(
        "document_path",
        help="S3 path to the PDF document"
    )
    parser.add_argument(
        "--source-type", "-s",
        choices=["BANK", "COUNTERPARTY"],
        required=True,
        help="Source type: BANK or COUNTERPARTY"
    )
    parser.add_argument(
        "--document-id", "-d",
        required=True,
        help="Document ID for the trade"
    )
    parser.add_argument(
        "--correlation-id", "-c",
        help="Optional correlation ID for tracing"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async def run_processing():
        result = await process_trade_with_http_orchestrator(
            document_path=args.document_path,
            source_type=args.source_type,
            document_id=args.document_id,
            correlation_id=args.correlation_id
        )
        
        print(json.dumps(result, indent=2, default=str))
        return result.get("success", False)
    
    # Run the async function
    success = asyncio.run(run_processing())
    return 0 if success else 1


if __name__ == "__main__":
    exit(main_http())