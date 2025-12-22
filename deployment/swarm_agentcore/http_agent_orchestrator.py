"""
HTTP Agent Orchestrator - Calls deployed AgentCore agents via HTTP

This orchestrator invokes agents that are already deployed to AgentCore Runtime.
Each agent runs in its own AgentCore instance and is called via the AgentCore API.

Workflow:
1. PDF Adapter Agent - Extract text from PDF
2. Trade Extraction Agent - Extract structured trade data
3. Trade Matching Agent - Match trades across tables
4. Exception Management Agent - Handle any exceptions
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import quote

# Environment variables are set by AgentCore runtime
# No need for dotenv when running in AgentCore container

import httpx
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.config import Config

from idempotency import IdempotencyCache

logger = logging.getLogger(__name__)

# Configure structured logging for observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")

# Agent Runtime ARNs (hardcoded since environment variables are not being passed through)
PDF_ADAPTER_ARN = os.getenv("PDF_ADAPTER_AGENT_ARN", "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ")
TRADE_EXTRACTION_ARN = os.getenv("TRADE_EXTRACTION_AGENT_ARN", "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/agent_matching_ai-KrY5QeCyXe")
TRADE_MATCHING_ARN = os.getenv("TRADE_MATCHING_AGENT_ARN", "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_ai-r8eaGb4u7B")
EXCEPTION_MANAGEMENT_ARN = os.getenv("EXCEPTION_MANAGEMENT_AGENT_ARN", "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/exception_manager-uliBS5DsX3")

# Timeouts and Retry Configuration
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "300"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Per-agent timeout configuration (in seconds)
# Trade matching can be very slow due to fuzzy matching algorithms
AGENT_TIMEOUTS = {
    "pdf_adapter": 120,        # 2 minutes - PDF text extraction
    "trade_extraction": 60,    # 1 minute - LLM extraction
    "trade_matching": 600,     # 10 minutes - Fuzzy matching can be slow
    "exception_management": 60  # 1 minute - Exception routing
}

DEFAULT_TIMEOUT = 300  # 5 minutes fallback


class AgentCoreClient:
    """Client for invoking deployed AgentCore agents with SigV4 authentication."""
    
    def __init__(self, region: str = REGION):
        self.region = region
        self.session = boto3.Session()
        self.endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com"
        logger.info(f"AgentCore client initialized for region: {region}")
        logger.info(f"Endpoint: {self.endpoint}")
    
    def _sign_request(self, method: str, url: str, headers: Dict[str, str], body: bytes) -> Dict[str, str]:
        """Sign request with SigV4 for AgentCore authentication."""
        credentials = self.session.get_credentials()
        if not credentials:
            raise RuntimeError("No AWS credentials found")
        
        request = AWSRequest(method=method, url=url, headers=headers, data=body)
        SigV4Auth(credentials.get_frozen_credentials(), "bedrock-agentcore", self.region).add_auth(request)
        
        return dict(request.headers)
    
    async def invoke_agent(
        self,
        runtime_arn: str,
        payload: Dict[str, Any],
        session_id: Optional[str] = None,
        timeout: int = AGENT_TIMEOUT_SECONDS,
        retries: int = MAX_RETRIES
    ) -> Dict[str, Any]:
        """
        Invoke a deployed AgentCore agent via HTTP with SigV4 signing.
        """
        if not runtime_arn:
            logger.error("ERROR: Agent runtime ARN is required but not provided")
            raise ValueError("Agent runtime ARN is required")
        
        # Build URL - URL encode the ARN
        encoded_arn = quote(runtime_arn, safe="")
        url = f"{self.endpoint}/runtimes/{encoded_arn}/invocations"
        
        # Extract correlation_id for logging context
        correlation_id = payload.get("correlation_id", "unknown")
        agent_name = runtime_arn.split("/")[-1] if "/" in runtime_arn else "unknown"
        
        logger.info(f"[{correlation_id}] INFO: Invoking agent '{agent_name}'")
        logger.info(f"[{correlation_id}] INFO: Agent ARN: ...{runtime_arn[-40:]}")
        logger.info(f"[{correlation_id}] INFO: Endpoint: {self.endpoint}")
        logger.info(f"[{correlation_id}] INFO: Timeout: {timeout}s, Max retries: {retries}")
        logger.debug(f"[{correlation_id}] DEBUG: Payload: {json.dumps(payload)[:200]}...")
        
        # Prepare request body
        body = json.dumps(payload).encode("utf-8")
        body_size_kb = len(body) / 1024
        logger.debug(f"[{correlation_id}] DEBUG: Request body size: {body_size_kb:.2f} KB")
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if session_id:
            headers["X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"] = session_id
            logger.debug(f"[{correlation_id}] DEBUG: Session ID: {session_id}")
        
        # Sign the request
        request_start = datetime.now(timezone.utc)
        logger.debug(f"[{correlation_id}] DEBUG: Signing request with SigV4")
        signed_headers = self._sign_request("POST", url, headers, body)
        signing_time_ms = (datetime.now(timezone.utc) - request_start).total_seconds() * 1000
        logger.debug(f"[{correlation_id}] DEBUG: Request signed in {signing_time_ms:.2f}ms")
        
        # Make HTTP request with retries
        last_error = None
        for attempt in range(retries):
            attempt_start = datetime.now(timezone.utc)
            
            try:
                logger.info(f"[{correlation_id}] INFO: Attempt {attempt + 1}/{retries} - calling agent")
                logger.debug(f"[{correlation_id}] DEBUG: URL: {url[:80]}...")
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        url,
                        headers=signed_headers,
                        content=body
                    )
                
                attempt_time_ms = (datetime.now(timezone.utc) - attempt_start).total_seconds() * 1000
                response_size_kb = len(response.content) / 1024
                
                logger.info(f"[{correlation_id}] INFO: Response status: {response.status_code}")
                logger.info(f"[{correlation_id}] INFO: Response time: {attempt_time_ms:.2f}ms")
                logger.debug(f"[{correlation_id}] DEBUG: Response size: {response_size_kb:.2f} KB")
                
                if response.status_code == 200:
                    result = response.json()
                    result["success"] = result.get("success", True)
                    result["http_status_code"] = response.status_code
                    result["response_time_ms"] = attempt_time_ms
                    
                    logger.info(f"[{correlation_id}] INFO: Agent returned success={result.get('success')}")
                    logger.debug(f"[{correlation_id}] DEBUG: Response keys: {list(result.keys())}")
                    
                    return result
                
                # Log error response with details
                error_text = response.text[:500]
                logger.error(f"[{correlation_id}] ERROR: Agent returned {response.status_code}")
                logger.error(f"[{correlation_id}] ERROR: Response: {error_text}")
                logger.error(f"[{correlation_id}] ERROR: Attempt {attempt + 1}/{retries} failed")
                
                # Retry on 5xx errors
                if response.status_code >= 500 and attempt < retries - 1:
                    # Exponential backoff: 1.0 * (2 ** attempt)
                    backoff_seconds = min(1.0 * (2 ** attempt), 60.0)
                    logger.warning(f"[{correlation_id}] WARN: Retrying after {backoff_seconds}s backoff")
                    await asyncio.sleep(backoff_seconds)
                    
                    # Re-sign for retry (credentials might have refreshed)
                    logger.debug(f"[{correlation_id}] DEBUG: Re-signing request for retry")
                    signed_headers = self._sign_request("POST", url, headers, body)
                    continue
                
                logger.error(f"[{correlation_id}] ERROR: No more retries, returning error")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_text}",
                    "status_code": response.status_code,
                    "attempt": attempt + 1,
                    "response_time_ms": attempt_time_ms
                }
                
            except httpx.TimeoutException as e:
                attempt_time_ms = (datetime.now(timezone.utc) - attempt_start).total_seconds() * 1000
                last_error = f"Timeout after {timeout}s"
                
                logger.error(f"[{correlation_id}] ERROR: Timeout on attempt {attempt + 1}/{retries}")
                logger.error(f"[{correlation_id}] ERROR: Elapsed time: {attempt_time_ms:.2f}ms")
                logger.error(f"[{correlation_id}] ERROR: Timeout threshold: {timeout}s")
                
                if attempt < retries - 1:
                    # Exponential backoff: 1.0 * (2 ** attempt)
                    backoff_seconds = min(1.0 * (2 ** attempt), 60.0)
                    logger.warning(f"[{correlation_id}] WARN: Retrying after {backoff_seconds}s backoff")
                    await asyncio.sleep(backoff_seconds)
                    signed_headers = self._sign_request("POST", url, headers, body)
                    continue
                    
            except Exception as e:
                attempt_time_ms = (datetime.now(timezone.utc) - attempt_start).total_seconds() * 1000
                last_error = str(e)
                
                logger.error(f"[{correlation_id}] ERROR: Request failed on attempt {attempt + 1}/{retries}")
                logger.error(f"[{correlation_id}] ERROR: Exception type: {type(e).__name__}")
                logger.error(f"[{correlation_id}] ERROR: Exception message: {e}")
                logger.error(f"[{correlation_id}] ERROR: Elapsed time: {attempt_time_ms:.2f}ms")
                
                if attempt < retries - 1:
                    # Exponential backoff: 1.0 * (2 ** attempt)
                    backoff_seconds = min(1.0 * (2 ** attempt), 60.0)
                    logger.warning(f"[{correlation_id}] WARN: Retrying after {backoff_seconds}s backoff")
                    await asyncio.sleep(backoff_seconds)
                    signed_headers = self._sign_request("POST", url, headers, body)
                    continue
        
        logger.error(f"[{correlation_id}] ERROR: All {retries} attempts exhausted")
        logger.error(f"[{correlation_id}] ERROR: Final error: {last_error}")
        
        return {
            "success": False,
            "error": last_error or "Max retries exceeded",
            "attempts": retries,
            "agent_name": agent_name
        }


class TradeMatchingHTTPOrchestrator:
    """
    Orchestrates trade matching workflow by calling deployed AgentCore agents.
    
    This is a sequential workflow orchestrator that:
    1. Calls PDF Adapter to extract text
    2. Calls Trade Extraction to get structured data
    3. Calls Trade Matching to find matches
    4. Calls Exception Management if issues found
    """
    
    def __init__(self):
        self.client = AgentCoreClient()
        self.agent_arns = {
            "pdf_adapter": PDF_ADAPTER_ARN,
            "trade_extraction": TRADE_EXTRACTION_ARN,
            "trade_matching": TRADE_MATCHING_ARN,
            "exception_management": EXCEPTION_MANAGEMENT_ARN
        }
        
        # Initialize idempotency cache
        # TTL of 300 seconds (5 minutes) prevents duplicate processing of recent workflows
        self.idempotency_cache = IdempotencyCache(
            table_name=os.getenv("IDEMPOTENCY_TABLE_NAME", "WorkflowIdempotency"),
            ttl_seconds=int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "300"))
        )
        
        # Validate configuration
        missing = [k for k, v in self.agent_arns.items() if not v]
        if missing:
            logger.warning(f"Missing agent ARNs: {missing}. Set environment variables.")
    
    async def process_trade_confirmation(
        self,
        document_path: str,
        source_type: str,
        document_id: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Process a trade confirmation through the full workflow.
        
        Args:
            document_path: S3 path to the PDF document
            source_type: BANK or COUNTERPARTY
            document_id: Unique document identifier
            correlation_id: Correlation ID for tracing
            
        Returns:
            Complete workflow result with all agent responses
        """
        start_time = datetime.now(timezone.utc)
        workflow_steps = {}
        current_step = None
        
        logger.info(f"[{correlation_id}] ========================================")
        logger.info(f"[{correlation_id}] INFO: Starting trade confirmation workflow")
        logger.info(f"[{correlation_id}] INFO: Document ID: {document_id}")
        logger.info(f"[{correlation_id}] INFO: Source Type: {source_type}")
        logger.info(f"[{correlation_id}] INFO: Document Path: {document_path}")
        logger.info(f"[{correlation_id}] ========================================")
        
        # Check idempotency cache - prevent duplicate workflow execution
        payload = {
            "document_path": document_path,
            "source_type": source_type,
            "document_id": document_id,
            "correlation_id": correlation_id
        }
        
        cached_result = self.idempotency_cache.check_and_set(correlation_id, payload)
        if cached_result is not None:
            logger.info(f"[{correlation_id}] INFO: Returning cached result (idempotency)")
            logger.info(f"[{correlation_id}] INFO: Workflow was already processed recently")
            cached_result["from_cache"] = True
            return cached_result
        
        try:
            # Step 1: PDF Adapter - Extract text from PDF
            current_step = "pdf_adapter"
            step_start = datetime.now(timezone.utc)
            logger.info(f"[{correlation_id}] INFO: Step 1/4: PDF Adapter Agent")
            logger.info(f"[{correlation_id}] INFO: Extracting text from PDF document")
            
            pdf_result = await self._invoke_pdf_adapter(
                document_path=document_path,
                source_type=source_type,
                document_id=document_id,
                correlation_id=correlation_id
            )
            
            step_time_ms = (datetime.now(timezone.utc) - step_start).total_seconds() * 1000
            workflow_steps["pdf_adapter"] = pdf_result
            
            logger.info(f"[{correlation_id}] INFO: PDF Adapter completed in {step_time_ms:.2f}ms")
            logger.info(f"[{correlation_id}] INFO: PDF Adapter success: {pdf_result.get('success')}")
            
            if not pdf_result.get("success"):
                logger.error(f"[{correlation_id}] ERROR: PDF extraction failed")
                logger.error(f"[{correlation_id}] ERROR: Error: {pdf_result.get('error')}")
                return self._build_error_response(
                    step=current_step,
                    error=pdf_result.get("error", "PDF extraction failed"),
                    workflow_steps=workflow_steps,
                    document_id=document_id,
                    correlation_id=correlation_id,
                    start_time=start_time
                )
            
            # Step 2: Trade Extraction - Extract structured data
            current_step = "trade_extraction"
            step_start = datetime.now(timezone.utc)
            logger.info(f"[{correlation_id}] INFO: Step 2/4: Trade Extraction Agent")
            logger.info(f"[{correlation_id}] INFO: Extracting structured trade data")
            
            # Extract canonical_output_location from PDF Adapter response
            canonical_output_location = self._extract_canonical_location(
                pdf_result, source_type, document_id
            )
            logger.debug(f"[{correlation_id}] DEBUG: Canonical location: {canonical_output_location}")
            
            extraction_result = await self._invoke_trade_extraction(
                document_id=document_id,
                source_type=source_type,
                correlation_id=correlation_id,
                canonical_output_location=canonical_output_location
            )
            
            step_time_ms = (datetime.now(timezone.utc) - step_start).total_seconds() * 1000
            workflow_steps["trade_extraction"] = extraction_result
            
            logger.info(f"[{correlation_id}] INFO: Trade Extraction completed in {step_time_ms:.2f}ms")
            logger.info(f"[{correlation_id}] INFO: Trade Extraction success: {extraction_result.get('success')}")
            
            if not extraction_result.get("success"):
                logger.error(f"[{correlation_id}] ERROR: Trade extraction failed")
                logger.error(f"[{correlation_id}] ERROR: Error: {extraction_result.get('error')}")
                logger.info(f"[{correlation_id}] INFO: Routing to Exception Management")
                
                # Route to exception management
                await self._handle_exception(
                    event_type="EXTRACTION_FAILED",
                    trade_id=document_id,
                    error_message=extraction_result.get("error"),
                    correlation_id=correlation_id,
                    workflow_steps=workflow_steps
                )
                return self._build_error_response(
                    step=current_step,
                    error=extraction_result.get("error", "Trade extraction failed"),
                    workflow_steps=workflow_steps,
                    document_id=document_id,
                    correlation_id=correlation_id,
                    start_time=start_time
                )
            
            # Extract trade_id from extraction result
            trade_id = self._extract_trade_id(extraction_result, document_id)
            logger.info(f"[{correlation_id}] INFO: Extracted trade_id: {trade_id}")
            if trade_id != document_id:
                logger.info(f"[{correlation_id}] INFO: Trade ID differs from document ID")
                logger.debug(f"[{correlation_id}] DEBUG: Document ID: {document_id}")
                logger.debug(f"[{correlation_id}] DEBUG: Trade ID: {trade_id}")
            
            # Step 3: Trade Matching - Find matching trades
            current_step = "trade_matching"
            step_start = datetime.now(timezone.utc)
            logger.info(f"[{correlation_id}] INFO: Step 3/4: Trade Matching Agent")
            logger.info(f"[{correlation_id}] INFO: Searching for matching trades")
            logger.info(f"[{correlation_id}] INFO: Primary search key: {trade_id}")
            
            matching_result = await self._invoke_trade_matching(
                trade_id=trade_id,
                source_type=source_type,
                correlation_id=correlation_id,
                document_id=document_id  # Pass original document_id as fallback
            )
            
            step_time_ms = (datetime.now(timezone.utc) - step_start).total_seconds() * 1000
            workflow_steps["trade_matching"] = matching_result
            
            logger.info(f"[{correlation_id}] INFO: Trade Matching completed in {step_time_ms:.2f}ms")
            logger.info(f"[{correlation_id}] INFO: Trade Matching success: {matching_result.get('success')}")
            
            # Check if exception handling needed based on match result
            classification = matching_result.get("match_classification", "UNKNOWN")
            
            # If classification is UNKNOWN, try to extract from agent_response text
            if classification == "UNKNOWN":
                classification = self._extract_classification(matching_result)
                logger.info(f"[{correlation_id}] INFO: Extracted classification from response: {classification}")
            
            confidence_score = matching_result.get("confidence_score", 0)
            logger.info(f"[{correlation_id}] INFO: Match classification: {classification}")
            logger.info(f"[{correlation_id}] INFO: Confidence score: {confidence_score}%")
            
            if classification in ["REVIEW_REQUIRED", "BREAK"]:
                current_step = "exception_management"
                step_start = datetime.now(timezone.utc)
                logger.info(f"[{correlation_id}] INFO: Step 4/4: Exception Management Agent")
                logger.info(f"[{correlation_id}] INFO: Classification requires exception handling: {classification}")
                
                reason_codes = self._extract_reason_codes(matching_result)
                logger.info(f"[{correlation_id}] INFO: Reason codes: {reason_codes}")
                
                exception_result = await self._handle_exception(
                    event_type="MATCHING_EXCEPTION",
                    trade_id=trade_id,
                    match_score=confidence_score / 100.0,
                    reason_codes=reason_codes,
                    correlation_id=correlation_id,
                    workflow_steps=workflow_steps
                )
                
                step_time_ms = (datetime.now(timezone.utc) - step_start).total_seconds() * 1000
                workflow_steps["exception_management"] = exception_result
                
                logger.info(f"[{correlation_id}] INFO: Exception Management completed in {step_time_ms:.2f}ms")
                logger.info(f"[{correlation_id}] INFO: Exception Management success: {exception_result.get('success')}")
            else:
                logger.info(f"[{correlation_id}] INFO: No exception handling needed for classification: {classification}")
            
            # Build success response
            processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            logger.info(f"[{correlation_id}] ========================================")
            logger.info(f"[{correlation_id}] INFO: Workflow completed successfully")
            logger.info(f"[{correlation_id}] INFO: Total processing time: {processing_time_ms:.2f}ms")
            logger.info(f"[{correlation_id}] INFO: Steps executed: {len(workflow_steps)}")
            logger.info(f"[{correlation_id}] INFO: Final classification: {classification}")
            logger.info(f"[{correlation_id}] ========================================")
            
            result = {
                "success": True,
                "document_id": document_id,
                "trade_id": trade_id,
                "source_type": source_type,
                "correlation_id": correlation_id,
                "match_classification": classification,
                "confidence_score": confidence_score,
                "workflow_steps": workflow_steps,
                "processing_time_ms": processing_time_ms,
                "execution_mode": "HTTP Orchestrator"
            }
            
            # Cache the result for idempotency
            self.idempotency_cache.set_result(correlation_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"[{correlation_id}] ========================================")
            logger.error(f"[{correlation_id}] ERROR: Workflow failed at step: {current_step}")
            logger.error(f"[{correlation_id}] ERROR: Exception type: {type(e).__name__}")
            logger.error(f"[{correlation_id}] ERROR: Exception message: {e}")
            logger.error(f"[{correlation_id}] ========================================", exc_info=True)
            
            error_result = self._build_error_response(
                step=current_step or "initialization",
                error=str(e),
                workflow_steps=workflow_steps,
                document_id=document_id,
                correlation_id=correlation_id,
                start_time=start_time
            )
            
            # Cache the error result for idempotency
            self.idempotency_cache.set_result(correlation_id, error_result)
            
            return error_result
    
    async def _invoke_pdf_adapter(
        self,
        document_path: str,
        source_type: str,
        document_id: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Invoke the PDF Adapter agent."""
        if not self.agent_arns["pdf_adapter"]:
            return {"success": False, "error": "PDF_ADAPTER_AGENT_ARN not configured"}
        
        return await self.client.invoke_agent(
            runtime_arn=self.agent_arns["pdf_adapter"],
            payload={
                "document_path": document_path,
                "source_type": source_type,
                "document_id": document_id,
                "correlation_id": correlation_id
            },
            timeout=AGENT_TIMEOUTS.get("pdf_adapter", DEFAULT_TIMEOUT)
        )
    
    async def _invoke_trade_extraction(
        self,
        document_id: str,
        source_type: str,
        correlation_id: str,
        canonical_output_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke the Trade Extraction agent."""
        if not self.agent_arns["trade_extraction"]:
            return {"success": False, "error": "TRADE_EXTRACTION_AGENT_ARN not configured"}
        
        payload = {
            "document_id": document_id,
            "source_type": source_type,
            "correlation_id": correlation_id
        }
        
        # Include canonical_output_location if provided by PDF Adapter
        if canonical_output_location:
            payload["canonical_output_location"] = canonical_output_location
        
        return await self.client.invoke_agent(
            runtime_arn=self.agent_arns["trade_extraction"],
            payload=payload,
            timeout=AGENT_TIMEOUTS.get("trade_extraction", DEFAULT_TIMEOUT)
        )
    
    async def _invoke_trade_matching(
        self,
        trade_id: str,
        source_type: str,
        correlation_id: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke the Trade Matching agent."""
        if not self.agent_arns["trade_matching"]:
            return {"success": False, "error": "TRADE_MATCHING_AGENT_ARN not configured"}
        
        payload = {
            "trade_id": trade_id,
            "source_type": source_type,
            "correlation_id": correlation_id
        }
        
        # Include document_id as fallback search key if different from trade_id
        if document_id and document_id != trade_id:
            payload["document_id"] = document_id
            payload["search_keys"] = [trade_id, document_id]
        
        return await self.client.invoke_agent(
            runtime_arn=self.agent_arns["trade_matching"],
            payload=payload,
            timeout=AGENT_TIMEOUTS.get("trade_matching", DEFAULT_TIMEOUT)
        )
    
    async def _handle_exception(
        self,
        event_type: str,
        trade_id: str,
        correlation_id: str,
        workflow_steps: Dict,
        match_score: Optional[float] = None,
        reason_codes: Optional[list] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke the Exception Management agent."""
        if not self.agent_arns["exception_management"]:
            logger.warning("EXCEPTION_MANAGEMENT_AGENT_ARN not configured - skipping")
            return {"success": False, "error": "Agent not configured", "skipped": True}
        
        return await self.client.invoke_agent(
            runtime_arn=self.agent_arns["exception_management"],
            payload={
                "event_type": event_type,
                "trade_id": trade_id,
                "match_score": match_score,
                "reason_codes": reason_codes or [],
                "error_message": error_message,
                "correlation_id": correlation_id
            },
            timeout=AGENT_TIMEOUTS.get("exception_management", DEFAULT_TIMEOUT)
        )
    
    def _extract_trade_id(self, extraction_result: Dict, fallback: str) -> str:
        """Extract trade_id from extraction result.
        
        The extraction agent stores the actual Trade_ID from the document,
        which may differ from the document_id. For example:
        - document_id: "FAB_26933659" (filename-based)
        - Trade_ID: "26933659" (extracted from document content)
        
        We try multiple strategies to find the actual stored trade_id.
        """
        import re
        
        # Strategy 1: Direct trade_id field in response
        if "trade_id" in extraction_result:
            return extraction_result["trade_id"]
        
        # Strategy 2: Check for extracted_trade_id field
        if "extracted_trade_id" in extraction_result:
            return extraction_result["extracted_trade_id"]
        
        # Strategy 3: Parse agent_response for trade_id patterns
        # Prioritize numeric-only Trade_IDs which are the actual DynamoDB keys
        response_text = extraction_result.get("agent_response", "")
        if response_text:
            # Look for Trade_ID patterns - prioritize numeric IDs
            patterns = [
                # DynamoDB format: "Trade_ID": {"S": "26933659"}
                r'"Trade_ID":\s*\{"S":\s*"(\d+)"',
                r'"trade_id":\s*\{"S":\s*"(\d+)"',
                # Simple format: Trade_ID: 26933659 or Trade_ID = "26933659"
                r'["\']?Trade_ID["\']?\s*[:=]\s*["\']?(\d+)["\']?',
                r'["\']?trade_id["\']?\s*[:=]\s*["\']?(\d+)["\']?',
                # Stored trade ID pattern
                r'stored.*[Tt]rade.*ID[:\s]+["\']?(\d+)["\']?',
                # fab_ref which contains the actual trade ID
                r'["\']?fab_ref["\']?\s*[:=]\s*["\']?(\d+)["\']?',
            ]
            for pattern in patterns:
                match = re.search(pattern, response_text)
                if match:
                    extracted_id = match.group(1)
                    # Validate it looks like a trade ID (numeric, reasonable length)
                    if extracted_id.isdigit() and 5 <= len(extracted_id) <= 15:
                        logger.info(f"Extracted trade_id '{extracted_id}' from agent response using pattern")
                        return extracted_id
        
        # Strategy 4: Strip common prefixes from document_id
        # e.g., "FAB_26933659" -> "26933659"
        if fallback:
            # Try stripping common prefixes
            for prefix in ["FAB_", "GCS_", "BANK_", "CP_"]:
                if fallback.upper().startswith(prefix):
                    stripped = fallback[len(prefix):]
                    # Only use if the stripped value is numeric
                    if stripped.isdigit():
                        logger.info(f"Stripped prefix from document_id: {fallback} -> {stripped}")
                        return stripped
        
        # Strategy 5: Extract numeric portion from document_id
        if fallback:
            numeric_match = re.search(r'(\d{6,15})', fallback)
            if numeric_match:
                extracted = numeric_match.group(1)
                logger.info(f"Extracted numeric trade_id '{extracted}' from document_id: {fallback}")
                return extracted
        
        return fallback
    
    def _extract_classification(self, matching_result: Dict) -> str:
        """Extract match classification from matching result agent_response.
        
        Parses the agent's response text to determine the classification
        when it's not explicitly returned in the structured response.
        """
        response = matching_result.get("agent_response", "").upper()
        
        # Check for explicit classification mentions
        if "REVIEW_REQUIRED" in response or "REVIEW REQUIRED" in response:
            return "REVIEW_REQUIRED"
        if "PROBABLE_MATCH" in response or "PROBABLE MATCH" in response:
            return "PROBABLE_MATCH"
        if "BREAK" in response and ("CLASSIFICATION" in response or "NO MATCH" in response):
            return "BREAK"
        
        # Check for implicit indicators
        if "FURTHER REVIEW" in response or "REQUIRES REVIEW" in response:
            return "REVIEW_REQUIRED"
        if "POTENTIAL MATCH" in response or "LIKELY MATCH" in response:
            return "PROBABLE_MATCH"
        if "MATCHED" in response and "NO" not in response.split("MATCHED")[0][-20:]:
            # Check if "MATCHED" is not preceded by "NO" within 20 chars
            return "MATCHED"
        if "NO MATCH" in response or "NOT FOUND" in response:
            return "BREAK"
        
        return "UNKNOWN"
    
    def _extract_canonical_location(
        self, 
        pdf_result: Dict, 
        source_type: str, 
        document_id: str
    ) -> str:
        """Extract canonical output location from PDF Adapter response.
        
        The PDF adapter agent returns the location in its agent_response text.
        We parse it out or construct the standard path.
        """
        import re
        
        # Strategy 1: Look for explicit canonical_output_location in response
        response_text = pdf_result.get("agent_response", "")
        if response_text:
            # Look for S3 path pattern
            match = re.search(
                r's3://[a-z0-9\-]+/extracted/(?:BANK|COUNTERPARTY)/[^"\s]+\.json',
                response_text
            )
            if match:
                return match.group(0)
        
        # Strategy 2: Construct standard path
        return f"s3://trade-matching-system-agentcore-production/extracted/{source_type}/{document_id}.json"
    
    def _extract_reason_codes(self, matching_result: Dict) -> list:
        """Extract reason codes from matching result."""
        codes = []
        response = matching_result.get("agent_response", "").upper()
        
        if "NOTIONAL" in response and ("MISMATCH" in response or "DIFFERENCE" in response):
            codes.append("NOTIONAL_MISMATCH")
        if "DATE" in response and ("MISMATCH" in response or "DIFFERENCE" in response):
            codes.append("DATE_MISMATCH")
        if "COUNTERPARTY" in response and ("MISMATCH" in response or "DIFFERENCE" in response):
            codes.append("COUNTERPARTY_MISMATCH")
        if "CURRENCY" in response and ("MISMATCH" in response or "DIFFERENCE" in response):
            codes.append("CURRENCY_MISMATCH")
        
        return codes if codes else ["UNKNOWN_MISMATCH"]
    
    def _build_error_response(
        self,
        step: str,
        error: str,
        workflow_steps: Dict,
        document_id: str,
        correlation_id: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Build standardized error response."""
        processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return {
            "success": False,
            "error": error,
            "failed_step": step,
            "document_id": document_id,
            "correlation_id": correlation_id,
            "workflow_steps": workflow_steps,
            "processing_time_ms": processing_time_ms,
            "execution_mode": "HTTP Orchestrator"
        }
