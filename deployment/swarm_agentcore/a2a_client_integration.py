"""
A2A Client Integration for Trade Matching Swarm

This module provides A2A (Agent-to-Agent) communication capabilities to interact
with deployed AgentCore agents instead of running local Strands agents.

The A2A orchestrator can communicate with:
- pdf_adapter_agent: arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ
- trade_extraction_agent: arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_extraction_agent-KnAx4O4ezw  
- trade_matching_agent: arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_agent-3aAvK64dQz
- exception_manager: arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/exception_manager-uliBS5DsX3
"""

import asyncio
import logging
import os
import json
import httpx
from uuid import uuid4
from typing import Dict, Any, Optional, List
from urllib.parse import quote

# A2A client imports
try:
    from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
    from a2a.types import Message, Part, Role, TextPart
except ImportError:
    # Fallback to python_a2a package
    from python_a2a import A2AClient as BaseA2AClient, AgentCard, Message, TextContent
    
    # Create compatibility wrappers for the different API
    class A2ACardResolver:
        def __init__(self, httpx_client=None, base_url=None):
            self.httpx_client = httpx_client
            self.base_url = base_url
        
        async def get_agent_card(self):
            # Use httpx client to get agent card directly
            if self.base_url and self.httpx_client:
                response = await self.httpx_client.get(f"{self.base_url}/.well-known/agent-card.json")
                response.raise_for_status()
                return AgentCard(**response.json())
            raise Exception("Unable to fetch agent card")
    
    class ClientConfig:
        def __init__(self, httpx_client=None, streaming=False):
            self.httpx_client = httpx_client
            self.streaming = streaming
    
    class ClientFactory:
        def __init__(self, config):
            self.config = config
        
        def create(self, agent_card):
            # Return a wrapper that uses httpx directly for A2A communication
            return A2AClientWrapper(self.config.httpx_client, agent_card)
    
    class A2AClientWrapper:
        def __init__(self, httpx_client, agent_card):
            self.httpx_client = httpx_client
            self.agent_card = agent_card
        
        async def send_message(self, message):
            # Direct HTTP call to agent using A2A protocol
            payload = {
                "jsonrpc": "2.0",
                "id": "req-001", 
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": message.parts[0].text}],
                        "messageId": message.message_id
                    }
                }
            }
            
            response = await self.httpx_client.post("/", json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Convert response back to Message format
            if "result" in result:
                response_message = Message(
                    kind="message",
                    role="assistant",
                    parts=[TextContent(kind="text", text=result["result"])],
                    message_id=result.get("id", "response-001")
                )
                yield response_message
    
    # Create compatibility types
    class Role:
        user = "user"
        assistant = "assistant"
    
    class Part:
        def __init__(self, content):
            if hasattr(content, 'text'):
                self.text = content.text
            else:
                self.text = str(content)
    
    class TextPart:
        def __init__(self, kind="text", text=""):
            self.kind = kind
            self.text = text

# Set up logging
logger = logging.getLogger(__name__)

# AgentCore agent configurations
AGENT_CONFIGS = {
    "pdf_adapter": {
        "arn": "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ",
        "name": "PDF Adapter Agent",
        "description": "Downloads PDFs from S3, extracts text via Bedrock multimodal, saves canonical output"
    },
    "trade_extractor": {
        "arn": "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_extraction_agent-KnAx4O4ezw",
        "name": "Trade Extraction Agent", 
        "description": "Reads canonical output, parses trade fields, stores in DynamoDB"
    },
    "trade_matcher": {
        "arn": "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_agent-3aAvK64dQz",
        "name": "Trade Matching Agent",
        "description": "Scans both tables, matches by attributes (NOT Trade_ID), generates reports"
    },
    "exception_handler": {
        "arn": "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/exception_manager-uliBS5DsX3",
        "name": "Exception Management Agent",
        "description": "Analyzes breaks, calculates SLA deadlines, stores exception records"
    }
}

# Default configuration
DEFAULT_TIMEOUT = 300  # 5 minutes
DEFAULT_REGION = "us-east-1"
AGENTCORE_BASE_URL = f"https://bedrock-agentcore.{DEFAULT_REGION}.amazonaws.com"


class A2AAgentClient:
    """
    A2A client for communicating with a single deployed AgentCore agent.
    """
    
    def __init__(
        self,
        agent_arn: str,
        bearer_token: str,
        region: str = DEFAULT_REGION,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize A2A client for a specific agent.
        
        Args:
            agent_arn: AgentCore agent ARN
            bearer_token: OAuth bearer token for authentication
            region: AWS region
            timeout: Request timeout in seconds
        """
        self.agent_arn = agent_arn
        self.bearer_token = bearer_token
        self.region = region
        self.timeout = timeout
        
        # Construct runtime URL
        escaped_arn = quote(agent_arn, safe='')
        self.runtime_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_arn}/invocations/"
        
        logger.info(f"Initialized A2A client for {agent_arn}")
        logger.debug(f"Runtime URL: {self.runtime_url}")
    
    async def send_message(self, message_text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to the AgentCore agent via A2A.
        
        Args:
            message_text: Message to send to the agent
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            Agent response as dictionary
        """
        if session_id is None:
            session_id = str(uuid4())
        
        # Create authentication headers
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as httpx_client:
                # Get agent card from the runtime URL
                resolver = A2ACardResolver(httpx_client=httpx_client, base_url=self.runtime_url)
                agent_card = await resolver.get_agent_card()
                
                # Create client using factory
                config = ClientConfig(
                    httpx_client=httpx_client,
                    streaming=False,  # Use non-streaming mode for sync response
                )
                factory = ClientFactory(config)
                client = factory.create(agent_card)
                
                # Create and send message
                msg = Message(
                    kind="message",
                    role=Role.user,
                    parts=[Part(TextPart(kind="text", text=message_text))],
                    message_id=uuid4().hex,
                )
                
                # Send message and collect response
                response_data = None
                async for event in client.send_message(msg):
                    if isinstance(event, Message):
                        # Extract text content from message parts
                        response_text = ""
                        for part in event.parts:
                            if hasattr(part, 'text'):
                                response_text += part.text
                        
                        response_data = {
                            "success": True,
                            "message_id": event.message_id,
                            "response": response_text,
                            "session_id": session_id
                        }
                        break
                    elif isinstance(event, tuple) and len(event) == 2:
                        # (Task, UpdateEvent) tuple
                        task, update_event = event
                        response_data = {
                            "success": True,
                            "task": task.model_dump(exclude_none=True) if hasattr(task, 'model_dump') else str(task),
                            "update_event": update_event.model_dump(exclude_none=True) if hasattr(update_event, 'model_dump') else str(update_event),
                            "session_id": session_id
                        }
                        break
                    else:
                        # Fallback for other response types
                        response_data = {
                            "success": True,
                            "response": str(event),
                            "session_id": session_id
                        }
                        break
                
                return response_data or {
                    "success": False,
                    "error": "No response received from agent",
                    "session_id": session_id
                }
                
        except Exception as e:
            logger.error(f"A2A communication failed for {self.agent_arn}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_arn": self.agent_arn,
                "session_id": session_id
            }


class TradeMatchingA2AOrchestrator:
    """
    A2A orchestrator for the Trade Matching workflow using deployed AgentCore agents.
    
    This orchestrator replaces the Strands Swarm with A2A communication to coordinate
    between your four deployed AgentCore agents.
    """
    
    def __init__(self, bearer_token: str, region: str = DEFAULT_REGION):
        """
        Initialize the A2A orchestrator.
        
        Args:
            bearer_token: OAuth bearer token for authentication
            region: AWS region
        """
        self.bearer_token = bearer_token
        self.region = region
        
        # Create A2A clients for each agent
        self.agents = {}
        for agent_name, config in AGENT_CONFIGS.items():
            self.agents[agent_name] = A2AAgentClient(
                agent_arn=config["arn"],
                bearer_token=bearer_token,
                region=region
            )
        
        logger.info("Initialized Trade Matching A2A Orchestrator")
        logger.info(f"Configured agents: {list(self.agents.keys())}")
    
    async def process_trade_confirmation(
        self,
        document_path: str,
        source_type: str,
        document_id: str,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a trade confirmation using A2A agent communication.
        
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
            correlation_id = f"corr_{uuid4().hex[:12]}"
        
        session_id = f"trade_{document_id}_{uuid4().hex[:8]}"
        
        try:
            # Step 1: PDF Adapter - Download and extract text
            logger.info(f"Step 1: PDF Adapter processing for {document_id}")
            
            pdf_task = f"""Process this trade confirmation PDF and extract the text content.

## Document Details
- Document ID: {document_id}
- S3 Location: {document_path}
- Source Type: {source_type}
- Correlation ID: {correlation_id}

## Instructions
1. Download the PDF from the specified S3 location
2. Extract all text content using Bedrock's multimodal capabilities
3. Save the canonical output to S3 in the standardized format
4. Return the canonical_output_location so the next agent can process the data

Focus on accurate text extraction and proper canonical format. Extract all trade details including trade IDs, dates, counterparty information, notional amounts, currencies, product types, and settlement information."""

            pdf_result = await self.agents["pdf_adapter"].send_message(pdf_task, session_id)
            
            if not pdf_result.get("success"):
                return {
                    "success": False,
                    "step": "pdf_adapter",
                    "error": pdf_result.get("error"),
                    "document_id": document_id,
                    "correlation_id": correlation_id
                }
            
            # Step 2: Trade Extraction - Parse and store data
            logger.info(f"Step 2: Trade Extraction processing for {document_id}")
            
            extraction_task = f"""Extract trade data from the canonical output and store it in DynamoDB.

## Document Details
- Document ID: {document_id}
- Source Type: {source_type}
- Correlation ID: {correlation_id}

## Previous Step Result
The PDF Adapter has processed the document and saved canonical output. You need to:
1. Read the canonical output from S3 (extracted/{source_type}/{document_id}.json)
2. Parse the extracted text to identify key trade fields
3. Structure the data appropriately for DynamoDB storage
4. Store the trade data in the correct table based on source type

## Key Fields to Extract
- trade_id / Trade_ID (REQUIRED)
- trade_date, effective_date, maturity_date
- notional, currency
- counterparty, buyer, seller
- product_type (SWAP, OPTION, FORWARD)
- fixed_rate, floating_rate_index

Route the trade to:
- BankTradeData table if source_type is BANK
- CounterpartyTradeData table if source_type is COUNTERPARTY

Ensure the TRADE_SOURCE field matches the table it's stored in."""

            extraction_result = await self.agents["trade_extractor"].send_message(extraction_task, session_id)
            
            if not extraction_result.get("success"):
                return {
                    "success": False,
                    "step": "trade_extraction",
                    "error": extraction_result.get("error"),
                    "document_id": document_id,
                    "correlation_id": correlation_id,
                    "pdf_result": pdf_result
                }
            
            # Step 3: Trade Matching - Analyze matches
            logger.info(f"Step 3: Trade Matching processing for {document_id}")
            
            matching_task = f"""Analyze trade matches between bank and counterparty systems.

## Document Details
- Document ID: {document_id}
- Source Type: {source_type}
- Correlation ID: {correlation_id}

## Previous Steps Completed
1. PDF text extraction completed successfully
2. Trade data extracted and stored in DynamoDB

## Your Task
Perform trade matching analysis by:
1. Scanning both BankTradeData and CounterpartyTradeData tables
2. Matching trades by ATTRIBUTES, NOT by Trade_ID (systems use different IDs for same trade)
3. Applying matching criteria with appropriate tolerances:
   - Currency (exact match)
   - Notional (within 2% tolerance)
   - Maturity/Termination Date (within 2 days)
   - Trade Date (within 2 days)
   - Counterparty names (fuzzy match)
   - Product Type

## Classification Guidelines
- MATCHED (85%+): All key attributes align well
- PROBABLE_MATCH (70-84%): Most attributes match with minor discrepancies
- REVIEW_REQUIRED (50-69%): Some significant discrepancies need review
- BREAK (<50%): Likely not the same trade

Generate a comprehensive matching report and save it to S3. Include your confidence score and reasoning for the classification."""

            matching_result = await self.agents["trade_matcher"].send_message(matching_task, session_id)
            
            if not matching_result.get("success"):
                return {
                    "success": False,
                    "step": "trade_matching",
                    "error": matching_result.get("error"),
                    "document_id": document_id,
                    "correlation_id": correlation_id,
                    "pdf_result": pdf_result,
                    "extraction_result": extraction_result
                }
            
            # Step 4: Exception Management (if needed)
            # Check if the matching result indicates issues that need exception handling
            matching_response = matching_result.get("response", "")
            needs_exception_handling = any(term in matching_response.lower() for term in [
                "review_required", "break", "exception", "error", "discrepancy", "mismatch"
            ])
            
            exception_result = None
            if needs_exception_handling:
                logger.info(f"Step 4: Exception Management processing for {document_id}")
                
                exception_task = f"""Analyze and process trade matching exceptions.

## Document Details
- Document ID: {document_id}
- Source Type: {source_type}
- Correlation ID: {correlation_id}

## Previous Steps Completed
1. PDF text extraction completed
2. Trade data extracted and stored
3. Trade matching analysis completed

## Matching Analysis Result
{matching_response}

## Your Task
Based on the matching analysis, determine if any exceptions need to be recorded:
1. First call get_severity_guidelines() to understand classification rules
2. Analyze the matching results for any issues or discrepancies
3. If exceptions are identified, determine appropriate severity level:
   - CRITICAL: Counterparty mismatches, regulatory risks
   - HIGH: Notional or currency discrepancies
   - MEDIUM: Date mismatches, missing non-critical fields
   - LOW: Processing delays, minor issues
4. Calculate SLA hours based on severity
5. Store exception records with your determined severity and reasoning

Only create exceptions if there are actual issues that require attention. If the trade matched successfully, no exception handling is needed."""

                exception_result = await self.agents["exception_handler"].send_message(exception_task, session_id)
            
            # Compile final result
            result = {
                "success": True,
                "document_id": document_id,
                "correlation_id": correlation_id,
                "session_id": session_id,
                "workflow_steps": {
                    "pdf_adapter": pdf_result,
                    "trade_extraction": extraction_result,
                    "trade_matching": matching_result
                }
            }
            
            if exception_result:
                result["workflow_steps"]["exception_management"] = exception_result
            
            logger.info(f"A2A workflow completed successfully for {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"A2A orchestration failed for {document_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "document_id": document_id,
                "correlation_id": correlation_id
            }


def get_bearer_token_from_env() -> str:
    """
    Get bearer token from environment variable.
    
    Returns:
        Bearer token for AgentCore authentication
        
    Raises:
        ValueError: If bearer token is not found in environment
    """
    token = os.environ.get("AGENTCORE_BEARER_TOKEN")
    if not token:
        raise ValueError(
            "AGENTCORE_BEARER_TOKEN environment variable not set. "
            "Run: export AGENTCORE_BEARER_TOKEN=\"your-token-here\""
        )
    return token


async def process_trade_with_a2a(
    document_path: str,
    source_type: str,
    document_id: str,
    correlation_id: Optional[str] = None,
    bearer_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a trade confirmation using A2A orchestration.
    
    Args:
        document_path: S3 path to the PDF
        source_type: BANK or COUNTERPARTY
        document_id: Unique document identifier
        correlation_id: Optional correlation ID for tracing
        bearer_token: Optional bearer token (from environment if not provided)
        
    Returns:
        Processing result with status and details
    """
    if bearer_token is None:
        bearer_token = get_bearer_token_from_env()
    
    orchestrator = TradeMatchingA2AOrchestrator(bearer_token)
    
    return await orchestrator.process_trade_confirmation(
        document_path=document_path,
        source_type=source_type,
        document_id=document_id,
        correlation_id=correlation_id
    )


# ============================================================================
# CLI Entry Point for A2A Mode
# ============================================================================

def main_a2a():
    """CLI entrypoint for A2A mode of the Trade Matching system."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Trade Matching A2A Orchestrator - Process trade confirmations using deployed AgentCore agents"
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
        "--bearer-token", "-t",
        help="Bearer token for AgentCore authentication (uses AGENTCORE_BEARER_TOKEN env var if not provided)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)
    
    async def run_processing():
        result = await process_trade_with_a2a(
            document_path=args.document_path,
            source_type=args.source_type,
            document_id=args.document_id,
            correlation_id=args.correlation_id,
            bearer_token=args.bearer_token
        )
        
        print(json.dumps(result, indent=2, default=str))
        return result.get("success", False)
    
    # Run the async function
    success = asyncio.run(run_processing())
    return 0 if success else 1


if __name__ == "__main__":
    exit(main_a2a())