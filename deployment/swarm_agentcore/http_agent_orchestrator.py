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

import httpx
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.config import Config

from status_tracker import StatusTracker

logger = logging.getLogger(__name__)

# Configure structured logging for observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)

# Configuration
REGION = os.getenv("AWS_REGION", "us-east-1")

# Agent Runtime ARNs - hardcoded for deployed agents
PDF_ADAPTER_ARN = os.getenv(
    "PDF_ADAPTER_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ"
)
TRADE_EXTRACTION_ARN = os.getenv(
    "TRADE_EXTRACTION_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/agent_matching_ai-KrY5QeCyXe"
)
TRADE_MATCHING_ARN = os.getenv(
    "TRADE_MATCHING_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/trade_matching_ai-r8eaGb4u7B"
)
EXCEPTION_MANAGEMENT_ARN = os.getenv(
    "EXCEPTION_MANAGEMENT_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/exception_manager-uliBS5DsX3"
)

# Timeouts and Retry Configuration
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "300"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))


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
            raise ValueError("Agent runtime ARN is required")
        
        # Build URL - URL encode the ARN
        encoded_arn = quote(runtime_arn, safe="")
        url = f"{self.endpoint}/runtimes/{encoded_arn}/invocations"
        
        logger.info(f"Invoking agent ARN: ...{runtime_arn[-40:]}")
        logger.info(f"Payload: {json.dumps(payload)[:200]}...")
        
        # Prepare request body
        body = json.dumps(payload).encode("utf-8")
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if session_id:
            headers["X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"] = session_id
        
        # Sign the request
        signed_headers = self._sign_request("POST", url, headers, body)
        
        # Make HTTP request with retries
        last_error = None
        for attempt in range(retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{retries} - calling {url[:80]}...")
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        url,
                        headers=signed_headers,
                        content=body
                    )
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    result["success"] = result.get("success", True)
                    logger.info(f"Agent returned success={result.get('success')}")
                    return result
                
                # Log error response
                logger.error(f"Agent error: {response.status_code} - {response.text[:500]}")
                
                # Retry on 5xx errors
                if response.status_code >= 500 and attempt < retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    # Re-sign for retry (credentials might have refreshed)
                    signed_headers = self._sign_request("POST", url, headers, body)
                    continue
                
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:500]}",
                    "status_code": response.status_code
                }
                
            except httpx.TimeoutException:
                last_error = f"Timeout after {timeout}s"
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    signed_headers = self._sign_request("POST", url, headers, body)
                    continue
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Request error: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    signed_headers = self._sign_request("POST", url, headers, body)
                    continue
        
        return {"success": False, "error": last_error or "Max retries exceeded"}


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
        self.status_tracker = StatusTracker()
        self.agent_arns = {
            "pdf_adapter": PDF_ADAPTER_ARN,
            "trade_extraction": TRADE_EXTRACTION_ARN,
            "trade_matching": TRADE_MATCHING_ARN,
            "exception_management": EXCEPTION_MANAGEMENT_ARN
        }

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

        # Initialize status tracking for UI
        self.status_tracker.initialize_status(
            session_id=correlation_id,
            correlation_id=correlation_id,
            document_id=document_id,
            source_type=source_type
        )

        try:
            # Step 1: PDF Adapter - Extract text from PDF
            current_step = "pdf_adapter"
            logger.info(f"[{correlation_id}] Step 1: Invoking PDF Adapter Agent")
            step_start = datetime.now(timezone.utc).isoformat()
            self.status_tracker.update_agent_status(
                session_id=correlation_id,
                correlation_id=correlation_id,
                agent_key="pdfAdapter",
                status="in-progress"
            )

            pdf_result = await self._invoke_pdf_adapter(
                document_path=document_path,
                source_type=source_type,
                document_id=document_id,
                correlation_id=correlation_id
            )
            workflow_steps["pdf_adapter"] = pdf_result

            if not pdf_result.get("success"):
                self.status_tracker.update_agent_status(
                    session_id=correlation_id,
                    correlation_id=correlation_id,
                    agent_key="pdfAdapter",
                    status="error",
                    agent_response=pdf_result,
                    started_at=step_start
                )
                self.status_tracker.finalize_status(correlation_id, correlation_id, "failed")
                return self._build_error_response(
                    step=current_step,
                    error=pdf_result.get("error", "PDF extraction failed"),
                    workflow_steps=workflow_steps,
                    document_id=document_id,
                    correlation_id=correlation_id,
                    start_time=start_time
                )

            self.status_tracker.update_agent_status(
                session_id=correlation_id,
                correlation_id=correlation_id,
                agent_key="pdfAdapter",
                status="success",
                agent_response=pdf_result,
                started_at=step_start
            )
            
            # Step 2: Trade Extraction - Extract structured data
            current_step = "trade_extraction"
            logger.info(f"[{correlation_id}] Step 2: Invoking Trade Extraction Agent")
            step_start = datetime.now(timezone.utc).isoformat()
            self.status_tracker.update_agent_status(
                session_id=correlation_id,
                correlation_id=correlation_id,
                agent_key="tradeExtraction",
                status="in-progress"
            )

            # Pass canonical_output_location from PDF Adapter to Trade Extraction
            canonical_output_location = pdf_result.get("canonical_output_location")

            extraction_result = await self._invoke_trade_extraction(
                document_id=document_id,
                source_type=source_type,
                correlation_id=correlation_id,
                canonical_output_location=canonical_output_location
            )
            workflow_steps["trade_extraction"] = extraction_result

            if not extraction_result.get("success"):
                self.status_tracker.update_agent_status(
                    session_id=correlation_id,
                    correlation_id=correlation_id,
                    agent_key="tradeExtraction",
                    status="error",
                    agent_response=extraction_result,
                    started_at=step_start
                )
                # Route to exception management
                await self._handle_exception(
                    event_type="EXTRACTION_FAILED",
                    trade_id=document_id,
                    error_message=extraction_result.get("error"),
                    correlation_id=correlation_id,
                    workflow_steps=workflow_steps
                )
                self.status_tracker.finalize_status(correlation_id, correlation_id, "failed")
                return self._build_error_response(
                    step=current_step,
                    error=extraction_result.get("error", "Trade extraction failed"),
                    workflow_steps=workflow_steps,
                    document_id=document_id,
                    correlation_id=correlation_id,
                    start_time=start_time
                )

            self.status_tracker.update_agent_status(
                session_id=correlation_id,
                correlation_id=correlation_id,
                agent_key="tradeExtraction",
                status="success",
                agent_response=extraction_result,
                started_at=step_start
            )
            
            # Extract trade_id from extraction result
            # The extraction agent stores the actual Trade_ID from the document,
            # which may differ from the document_id (e.g., "26933659" vs "FAB_26933659")
            trade_id = self._extract_trade_id(extraction_result, document_id)
            logger.info(f"[{correlation_id}] Extracted trade_id: {trade_id} (document_id: {document_id})")
            
            # Step 3: Trade Matching - Find matching trades
            # Pass both trade_id and document_id so the agent can search for either
            current_step = "trade_matching"
            logger.info(f"[{correlation_id}] Step 3: Invoking Trade Matching Agent")
            step_start = datetime.now(timezone.utc).isoformat()
            self.status_tracker.update_agent_status(
                session_id=correlation_id,
                correlation_id=correlation_id,
                agent_key="tradeMatching",
                status="in-progress"
            )

            matching_result = await self._invoke_trade_matching(
                trade_id=trade_id,
                source_type=source_type,
                correlation_id=correlation_id,
                document_id=document_id  # Pass original document_id as fallback
            )
            workflow_steps["trade_matching"] = matching_result

            self.status_tracker.update_agent_status(
                session_id=correlation_id,
                correlation_id=correlation_id,
                agent_key="tradeMatching",
                status="success" if matching_result.get("success") else "error",
                agent_response=matching_result,
                started_at=step_start
            )

            # Check if exception handling needed based on match result
            classification = matching_result.get("match_classification", "UNKNOWN")

            # If classification is UNKNOWN, try to extract from agent_response text
            if classification == "UNKNOWN":
                classification = self._extract_classification(matching_result)
                logger.info(f"[{correlation_id}] Extracted classification from response: {classification}")

            if classification in ["REVIEW_REQUIRED", "BREAK"]:
                current_step = "exception_management"
                logger.info(f"[{correlation_id}] Step 4: Invoking Exception Management (classification: {classification})")
                step_start = datetime.now(timezone.utc).isoformat()
                self.status_tracker.update_agent_status(
                    session_id=correlation_id,
                    correlation_id=correlation_id,
                    agent_key="exceptionManagement",
                    status="in-progress"
                )

                exception_result = await self._handle_exception(
                    event_type="MATCHING_EXCEPTION",
                    trade_id=trade_id,
                    match_score=matching_result.get("confidence_score", 0) / 100.0,
                    reason_codes=self._extract_reason_codes(matching_result),
                    correlation_id=correlation_id,
                    workflow_steps=workflow_steps
                )
                workflow_steps["exception_management"] = exception_result

                self.status_tracker.update_agent_status(
                    session_id=correlation_id,
                    correlation_id=correlation_id,
                    agent_key="exceptionManagement",
                    status="success" if exception_result.get("success") else "error",
                    agent_response=exception_result,
                    started_at=step_start
                )

            # Finalize workflow status
            self.status_tracker.finalize_status(correlation_id, correlation_id, "completed")

            # Build success response
            processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            return {
                "success": True,
                "document_id": document_id,
                "trade_id": trade_id,
                "source_type": source_type,
                "correlation_id": correlation_id,
                "match_classification": classification,
                "confidence_score": matching_result.get("confidence_score", 0),
                "workflow_steps": workflow_steps,
                "processing_time_ms": processing_time_ms,
                "execution_mode": "HTTP Orchestrator"
            }

        except Exception as e:
            logger.error(f"[{correlation_id}] Workflow failed at {current_step}: {e}", exc_info=True)
            self.status_tracker.finalize_status(correlation_id, correlation_id, "failed")
            return self._build_error_response(
                step=current_step or "initialization",
                error=str(e),
                workflow_steps=workflow_steps,
                document_id=document_id,
                correlation_id=correlation_id,
                start_time=start_time
            )
    
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
            }
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
            payload=payload
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
            payload=payload
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
            }
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
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
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


# =============================================================================
# BedrockAgentCore Application Setup
# =============================================================================
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.models import PingStatus

# Initialize the AgentCore app
app = BedrockAgentCoreApp()

# Create orchestrator instance
orchestrator = TradeMatchingHTTPOrchestrator()


@app.ping
def handle_ping() -> PingStatus:
    """Health check endpoint."""
    return PingStatus.HEALTHY


@app.entrypoint
def handle_invoke(payload: dict, context: any) -> dict:
    """Handle workflow invocation requests.

    Expected payload format from backend:
    {
        "sessionId": "session-uuid-FAB_12345",
        "s3Uri": "s3://bucket/path/to/file.pdf",
        "action": "process_upload"
    }

    Also supports direct format:
    {
        "session_id": "uuid",
        "document_id": "FAB_12345",
        "source_type": "BANK",
        "s3_bucket": "bucket",
        "s3_key": "path/to/file.pdf"
    }
    """
    logger.info(f"Received invocation request: {json.dumps(payload, default=str)[:500]}")

    try:
        # Handle backend format (sessionId, s3Uri, action)
        if "sessionId" in payload and "s3Uri" in payload:
            session_id = payload.get("sessionId", "")
            s3_uri = payload.get("s3Uri", "")

            # Parse s3Uri to get document_path
            document_path = s3_uri

            # Extract document_id from session_id (format: session-uuid-FAB_12345)
            # or from s3_uri filename
            if "-FAB_" in session_id:
                document_id = "FAB_" + session_id.split("-FAB_")[-1]
            elif "-GCS_" in session_id:
                document_id = "GCS_" + session_id.split("-GCS_")[-1]
            else:
                # Extract from filename in s3_uri
                filename = s3_uri.split("/")[-1].replace(".pdf", "")
                document_id = filename.split("-")[-1] if "-" in filename else filename

            # Determine source_type from s3_uri path
            if "/BANK/" in s3_uri:
                source_type = "BANK"
            elif "/COUNTERPARTY/" in s3_uri:
                source_type = "COUNTERPARTY"
            else:
                source_type = "BANK"  # Default

            correlation_id = session_id

        # Handle direct format (session_id, s3_bucket, s3_key)
        else:
            session_id = payload.get("session_id", "")
            correlation_id = payload.get("correlation_id", session_id)
            document_id = payload.get("document_id", "")
            source_type = payload.get("source_type", "BANK")
            s3_bucket = payload.get("s3_bucket", "")
            s3_key = payload.get("s3_key", "")

            if not all([session_id, document_id, s3_bucket, s3_key]):
                return {
                    "success": False,
                    "error": "Missing required parameters: session_id, document_id, s3_bucket, s3_key"
                }

            document_path = f"s3://{s3_bucket}/{s3_key}"

        logger.info(f"Processing: session_id={session_id}, document_id={document_id}, source_type={source_type}, path={document_path}")

        # Run the workflow synchronously (asyncio.run for async method)
        import asyncio
        result = asyncio.run(orchestrator.process_trade_confirmation(
            document_path=document_path,
            source_type=source_type,
            document_id=document_id,
            correlation_id=correlation_id
        ))

        return result

    except Exception as e:
        logger.exception(f"Error processing request: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    """Let AgentCore Runtime control the execution."""
    app.run()
