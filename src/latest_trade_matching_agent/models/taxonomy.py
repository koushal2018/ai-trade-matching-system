"""
Workflow and Event Taxonomy System

This module provides hierarchical taxonomy structures for workflows,
events, and reason codes used throughout the system.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import boto3


class WorkflowNode(BaseModel):
    """
    A node in the workflow taxonomy hierarchy.
    
    Validates: Requirements 3.1
    """
    id: str = Field(..., description="Unique identifier for the workflow node")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description of the workflow step")
    parent_id: Optional[str] = Field(default=None, description="Parent node ID")
    children: List[str] = Field(default_factory=list, description="Child node IDs")
    agent_type: Optional[str] = Field(default=None, description="Agent type responsible for this workflow")
    event_triggers: List[str] = Field(default_factory=list, description="Events that trigger this workflow")
    event_outputs: List[str] = Field(default_factory=list, description="Events produced by this workflow")
    sla_target_seconds: Optional[int] = Field(default=None, description="SLA target in seconds")


class WorkflowTaxonomy(BaseModel):
    """
    Complete hierarchical workflow taxonomy.
    
    Validates: Requirements 3.1
    """
    version: str = Field(default="1.0.0", description="Taxonomy version")
    last_updated: str = Field(..., description="Last update timestamp")
    workflows: Dict[str, WorkflowNode] = Field(default_factory=dict, description="All workflow nodes by ID")
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowNode]:
        """Get a workflow node by ID."""
        return self.workflows.get(workflow_id)
    
    def get_children(self, workflow_id: str) -> List[WorkflowNode]:
        """Get all child workflows of a given workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return []
        
        return [self.workflows[child_id] for child_id in workflow.children if child_id in self.workflows]
    
    def get_root_workflows(self) -> List[WorkflowNode]:
        """Get all root-level workflows (no parent)."""
        return [wf for wf in self.workflows.values() if wf.parent_id is None]


def create_default_taxonomy() -> WorkflowTaxonomy:
    """
    Create the default workflow taxonomy for the trade matching system.
    
    Returns:
        WorkflowTaxonomy: Complete taxonomy structure
        
    Validates: Requirements 3.1
    """
    workflows = {
        # Root workflow
        "trade_processing": WorkflowNode(
            id="trade_processing",
            name="Trade Processing Workflow",
            description="Complete end-to-end trade confirmation processing",
            parent_id=None,
            children=["document_ingestion", "data_extraction", "trade_matching", "exception_handling"],
            agent_type="ORCHESTRATOR",
            event_triggers=["DOCUMENT_UPLOADED"],
            event_outputs=["WORKFLOW_COMPLETED"],
            sla_target_seconds=90
        ),
        
        # Document Ingestion
        "document_ingestion": WorkflowNode(
            id="document_ingestion",
            name="Document Ingestion",
            description="Ingest and process trade confirmation documents",
            parent_id="trade_processing",
            children=["pdf_upload", "chat_message", "email_receipt", "voice_transcription"],
            agent_type="ADAPTER",
            event_triggers=["DOCUMENT_UPLOADED"],
            event_outputs=["PDF_PROCESSED", "CHAT_PROCESSED", "EMAIL_PROCESSED", "VOICE_PROCESSED"],
            sla_target_seconds=15
        ),
        
        "pdf_upload": WorkflowNode(
            id="pdf_upload",
            name="PDF Upload",
            description="Process PDF trade confirmations",
            parent_id="document_ingestion",
            children=[],
            agent_type="ADAPTER",
            event_triggers=["DOCUMENT_UPLOADED"],
            event_outputs=["PDF_PROCESSED"],
            sla_target_seconds=10
        ),
        
        "chat_message": WorkflowNode(
            id="chat_message",
            name="Chat Message",
            description="Process trade confirmations from chat messages",
            parent_id="document_ingestion",
            children=[],
            agent_type="ADAPTER",
            event_triggers=["CHAT_MESSAGE_RECEIVED"],
            event_outputs=["CHAT_PROCESSED"],
            sla_target_seconds=5
        ),
        
        "email_receipt": WorkflowNode(
            id="email_receipt",
            name="Email Receipt",
            description="Process trade confirmations from email",
            parent_id="document_ingestion",
            children=[],
            agent_type="ADAPTER",
            event_triggers=["EMAIL_RECEIVED"],
            event_outputs=["EMAIL_PROCESSED"],
            sla_target_seconds=10
        ),
        
        "voice_transcription": WorkflowNode(
            id="voice_transcription",
            name="Voice Transcription",
            description="Process trade confirmations from voice recordings",
            parent_id="document_ingestion",
            children=[],
            agent_type="ADAPTER",
            event_triggers=["VOICE_RECORDING_RECEIVED"],
            event_outputs=["VOICE_PROCESSED"],
            sla_target_seconds=20
        ),
        
        # Data Extraction
        "data_extraction": WorkflowNode(
            id="data_extraction",
            name="Data Extraction",
            description="Extract structured trade data from unstructured sources",
            parent_id="trade_processing",
            children=["ocr_processing", "llm_extraction", "field_validation"],
            agent_type="EXTRACTOR",
            event_triggers=["PDF_PROCESSED", "CHAT_PROCESSED", "EMAIL_PROCESSED", "VOICE_PROCESSED"],
            event_outputs=["TRADE_EXTRACTED"],
            sla_target_seconds=30
        ),
        
        "ocr_processing": WorkflowNode(
            id="ocr_processing",
            name="OCR Processing",
            description="Optical character recognition from images",
            parent_id="data_extraction",
            children=[],
            agent_type="EXTRACTOR",
            event_triggers=["PDF_PROCESSED"],
            event_outputs=["OCR_COMPLETED"],
            sla_target_seconds=15
        ),
        
        "llm_extraction": WorkflowNode(
            id="llm_extraction",
            name="LLM Extraction",
            description="Extract trade fields using LLM",
            parent_id="data_extraction",
            children=[],
            agent_type="EXTRACTOR",
            event_triggers=["OCR_COMPLETED"],
            event_outputs=["EXTRACTION_COMPLETED"],
            sla_target_seconds=10
        ),
        
        "field_validation": WorkflowNode(
            id="field_validation",
            name="Field Validation",
            description="Validate extracted trade fields",
            parent_id="data_extraction",
            children=[],
            agent_type="EXTRACTOR",
            event_triggers=["EXTRACTION_COMPLETED"],
            event_outputs=["TRADE_EXTRACTED"],
            sla_target_seconds=5
        ),
        
        # Trade Matching
        "trade_matching": WorkflowNode(
            id="trade_matching",
            name="Trade Matching",
            description="Match bank and counterparty trades",
            parent_id="trade_processing",
            children=["fuzzy_matching", "score_computation", "classification"],
            agent_type="MATCHER",
            event_triggers=["TRADE_EXTRACTED"],
            event_outputs=["MATCH_COMPLETED", "MATCHING_EXCEPTION"],
            sla_target_seconds=30
        ),
        
        "fuzzy_matching": WorkflowNode(
            id="fuzzy_matching",
            name="Fuzzy Matching",
            description="Perform fuzzy matching with tolerances",
            parent_id="trade_matching",
            children=[],
            agent_type="MATCHER",
            event_triggers=["TRADE_EXTRACTED"],
            event_outputs=["MATCHING_STARTED"],
            sla_target_seconds=10
        ),
        
        "score_computation": WorkflowNode(
            id="score_computation",
            name="Score Computation",
            description="Compute match scores",
            parent_id="trade_matching",
            children=[],
            agent_type="MATCHER",
            event_triggers=["MATCHING_STARTED"],
            event_outputs=["SCORE_COMPUTED"],
            sla_target_seconds=5
        ),
        
        "classification": WorkflowNode(
            id="classification",
            name="Classification",
            description="Classify match results",
            parent_id="trade_matching",
            children=[],
            agent_type="MATCHER",
            event_triggers=["SCORE_COMPUTED"],
            event_outputs=["MATCH_COMPLETED"],
            sla_target_seconds=5
        ),
        
        # Exception Handling
        "exception_handling": WorkflowNode(
            id="exception_handling",
            name="Exception Handling",
            description="Handle exceptions and errors",
            parent_id="trade_processing",
            children=["triage", "delegation", "resolution_tracking"],
            agent_type="EXCEPTION_HANDLER",
            event_triggers=["EXCEPTION_RAISED", "MATCHING_EXCEPTION"],
            event_outputs=["EXCEPTION_TRIAGED", "EXCEPTION_RESOLVED"],
            sla_target_seconds=300
        ),
        
        "triage": WorkflowNode(
            id="triage",
            name="Triage",
            description="Classify and prioritize exceptions",
            parent_id="exception_handling",
            children=[],
            agent_type="EXCEPTION_HANDLER",
            event_triggers=["EXCEPTION_RAISED"],
            event_outputs=["EXCEPTION_TRIAGED"],
            sla_target_seconds=60
        ),
        
        "delegation": WorkflowNode(
            id="delegation",
            name="Delegation",
            description="Delegate exceptions to appropriate handlers",
            parent_id="exception_handling",
            children=[],
            agent_type="EXCEPTION_HANDLER",
            event_triggers=["EXCEPTION_TRIAGED"],
            event_outputs=["EXCEPTION_DELEGATED"],
            sla_target_seconds=30
        ),
        
        "resolution_tracking": WorkflowNode(
            id="resolution_tracking",
            name="Resolution Tracking",
            description="Track exception resolution",
            parent_id="exception_handling",
            children=[],
            agent_type="EXCEPTION_HANDLER",
            event_triggers=["EXCEPTION_DELEGATED"],
            event_outputs=["EXCEPTION_RESOLVED"],
            sla_target_seconds=14400  # 4 hours
        )
    }
    
    from datetime import datetime
    return WorkflowTaxonomy(
        version="1.0.0",
        last_updated=datetime.utcnow().isoformat(),
        workflows=workflows
    )


class TaxonomyLoader:
    """
    Loader for workflow taxonomy from S3.
    
    Validates: Requirements 3.1
    """
    
    def __init__(self, bucket_name: str, region_name: str = "us-east-1"):
        """Initialize the taxonomy loader."""
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.s3 = boto3.client('s3', region_name=region_name)
        self.taxonomy_key = "config/taxonomy.json"
    
    def save_taxonomy(self, taxonomy: WorkflowTaxonomy) -> dict:
        """
        Save taxonomy to S3.
        
        Args:
            taxonomy: WorkflowTaxonomy to save
            
        Returns:
            dict: Response indicating success or failure
        """
        try:
            taxonomy_json = taxonomy.model_dump_json(indent=2)
            
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=self.taxonomy_key,
                Body=taxonomy_json,
                ContentType='application/json'
            )
            
            return {
                "success": True,
                "message": f"Taxonomy saved to s3://{self.bucket_name}/{self.taxonomy_key}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save taxonomy to S3"
            }
    
    def load_taxonomy(self) -> Optional[WorkflowTaxonomy]:
        """
        Load taxonomy from S3.
        
        Returns:
            Optional[WorkflowTaxonomy]: Loaded taxonomy or None if not found
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=self.taxonomy_key
            )
            
            taxonomy_json = response['Body'].read().decode('utf-8')
            taxonomy_dict = json.loads(taxonomy_json)
            
            return WorkflowTaxonomy(**taxonomy_dict)
        except self.s3.exceptions.NoSuchKey:
            print(f"Taxonomy not found at s3://{self.bucket_name}/{self.taxonomy_key}")
            return None
        except Exception as e:
            print(f"Error loading taxonomy: {e}")
            return None
    
    def initialize_default_taxonomy(self) -> dict:
        """
        Create and save the default taxonomy to S3.
        
        Returns:
            dict: Response indicating success or failure
        """
        taxonomy = create_default_taxonomy()
        return self.save_taxonomy(taxonomy)



# ========== Reason Code Taxonomy ==========

class ReasonCodeTaxonomy:
    """
    Standardized reason codes for exceptions and mismatches.
    
    This taxonomy provides consistent reason codes across all agents
    for exception handling, matching analysis, and error reporting.
    
    Validates: Requirements 7.2, 7.5, 8.1
    """
    
    # ========== Matching Reason Codes ==========
    NOTIONAL_MISMATCH = "NOTIONAL_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    COUNTERPARTY_MISMATCH = "COUNTERPARTY_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    PRODUCT_TYPE_MISMATCH = "PRODUCT_TYPE_MISMATCH"
    TRADE_ID_MISMATCH = "TRADE_ID_MISMATCH"
    EFFECTIVE_DATE_MISMATCH = "EFFECTIVE_DATE_MISMATCH"
    MATURITY_DATE_MISMATCH = "MATURITY_DATE_MISMATCH"
    COMMODITY_TYPE_MISMATCH = "COMMODITY_TYPE_MISMATCH"
    STRIKE_PRICE_MISMATCH = "STRIKE_PRICE_MISMATCH"
    SETTLEMENT_TYPE_MISMATCH = "SETTLEMENT_TYPE_MISMATCH"
    
    # ========== Data Error Reason Codes ==========
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_FORMAT = "INVALID_FIELD_FORMAT"
    AMBIGUOUS_FIELD_VALUE = "AMBIGUOUS_FIELD_VALUE"
    DUPLICATE_TRADE_ID = "DUPLICATE_TRADE_ID"
    MISPLACED_TRADE = "MISPLACED_TRADE"  # Trade in wrong table
    INCOMPLETE_TRADE_DATA = "INCOMPLETE_TRADE_DATA"
    
    # ========== Processing Reason Codes ==========
    OCR_QUALITY_LOW = "OCR_QUALITY_LOW"
    PDF_CORRUPTED = "PDF_CORRUPTED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    IMAGE_CONVERSION_FAILED = "IMAGE_CONVERSION_FAILED"
    EXTRACTION_TIMEOUT = "EXTRACTION_TIMEOUT"
    PARSING_ERROR = "PARSING_ERROR"
    
    # ========== System Reason Codes ==========
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    NETWORK_ERROR = "NETWORK_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    S3_ACCESS_ERROR = "S3_ACCESS_ERROR"
    
    # ========== Business Logic Reason Codes ==========
    TRADE_NOT_FOUND = "TRADE_NOT_FOUND"
    COUNTERPARTY_TRADE_MISSING = "COUNTERPARTY_TRADE_MISSING"
    BANK_TRADE_MISSING = "BANK_TRADE_MISSING"
    MULTIPLE_MATCHES_FOUND = "MULTIPLE_MATCHES_FOUND"
    NO_MATCH_FOUND = "NO_MATCH_FOUND"
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    
    @classmethod
    def all_reason_codes(cls) -> list:
        """Get list of all reason codes."""
        return [
            value for name, value in vars(cls).items()
            if not name.startswith('_') and isinstance(value, str)
        ]
    
    @classmethod
    def is_valid_reason_code(cls, reason_code: str) -> bool:
        """Check if a reason code is valid."""
        return reason_code in cls.all_reason_codes()
    
    @classmethod
    def get_reason_code_description(cls, reason_code: str) -> str:
        """
        Get human-readable description for a reason code.
        
        Args:
            reason_code: Reason code to describe
        
        Returns:
            str: Description of the reason code
        """
        descriptions = {
            # Matching Reason Codes
            cls.NOTIONAL_MISMATCH: "Trade notional amounts differ beyond tolerance (±0.01%)",
            cls.DATE_MISMATCH: "Trade dates differ beyond tolerance (±1 business day)",
            cls.COUNTERPARTY_MISMATCH: "Counterparty names do not match",
            cls.CURRENCY_MISMATCH: "Currency codes do not match",
            cls.PRODUCT_TYPE_MISMATCH: "Product types do not match",
            cls.TRADE_ID_MISMATCH: "Trade IDs do not match",
            cls.EFFECTIVE_DATE_MISMATCH: "Effective dates do not match",
            cls.MATURITY_DATE_MISMATCH: "Maturity dates do not match",
            cls.COMMODITY_TYPE_MISMATCH: "Commodity types do not match",
            cls.STRIKE_PRICE_MISMATCH: "Strike prices do not match",
            cls.SETTLEMENT_TYPE_MISMATCH: "Settlement types do not match",
            
            # Data Error Reason Codes
            cls.MISSING_REQUIRED_FIELD: "Required field is missing from trade data",
            cls.INVALID_FIELD_FORMAT: "Field value does not match expected format",
            cls.AMBIGUOUS_FIELD_VALUE: "Field value is ambiguous and requires clarification",
            cls.DUPLICATE_TRADE_ID: "Trade ID already exists in the system",
            cls.MISPLACED_TRADE: "Trade stored in incorrect DynamoDB table (TRADE_SOURCE mismatch)",
            cls.INCOMPLETE_TRADE_DATA: "Trade data is incomplete or missing critical fields",
            
            # Processing Reason Codes
            cls.OCR_QUALITY_LOW: "OCR extraction quality is below acceptable threshold",
            cls.PDF_CORRUPTED: "PDF file is corrupted or cannot be read",
            cls.UNSUPPORTED_FORMAT: "Document format is not supported",
            cls.IMAGE_CONVERSION_FAILED: "Failed to convert PDF to images",
            cls.EXTRACTION_TIMEOUT: "Trade data extraction exceeded timeout limit",
            cls.PARSING_ERROR: "Error parsing extracted text into structured data",
            
            # System Reason Codes
            cls.SERVICE_UNAVAILABLE: "Required service is temporarily unavailable",
            cls.TIMEOUT: "Operation exceeded timeout limit",
            cls.RATE_LIMIT_EXCEEDED: "API rate limit exceeded",
            cls.AUTHENTICATION_FAILED: "Authentication failed",
            cls.AUTHORIZATION_FAILED: "User does not have required permissions",
            cls.NETWORK_ERROR: "Network communication error",
            cls.DATABASE_ERROR: "Database operation failed",
            cls.S3_ACCESS_ERROR: "Failed to access S3 bucket or object",
            
            # Business Logic Reason Codes
            cls.TRADE_NOT_FOUND: "Trade not found in database",
            cls.COUNTERPARTY_TRADE_MISSING: "Counterparty trade not found for matching",
            cls.BANK_TRADE_MISSING: "Bank trade not found for matching",
            cls.MULTIPLE_MATCHES_FOUND: "Multiple potential matches found for trade",
            cls.NO_MATCH_FOUND: "No matching trade found",
            cls.CONFIDENCE_TOO_LOW: "Match confidence score is below threshold"
        }
        
        return descriptions.get(reason_code, f"Unknown reason code: {reason_code}")
    
    @classmethod
    def get_reason_code_category(cls, reason_code: str) -> str:
        """
        Get the category for a reason code.
        
        Args:
            reason_code: Reason code to categorize
        
        Returns:
            str: Category name (MATCHING, DATA_ERROR, PROCESSING, SYSTEM, BUSINESS_LOGIC)
        """
        matching_codes = [
            cls.NOTIONAL_MISMATCH, cls.DATE_MISMATCH, cls.COUNTERPARTY_MISMATCH,
            cls.CURRENCY_MISMATCH, cls.PRODUCT_TYPE_MISMATCH, cls.TRADE_ID_MISMATCH,
            cls.EFFECTIVE_DATE_MISMATCH, cls.MATURITY_DATE_MISMATCH,
            cls.COMMODITY_TYPE_MISMATCH, cls.STRIKE_PRICE_MISMATCH,
            cls.SETTLEMENT_TYPE_MISMATCH
        ]
        
        data_error_codes = [
            cls.MISSING_REQUIRED_FIELD, cls.INVALID_FIELD_FORMAT,
            cls.AMBIGUOUS_FIELD_VALUE, cls.DUPLICATE_TRADE_ID,
            cls.MISPLACED_TRADE, cls.INCOMPLETE_TRADE_DATA
        ]
        
        processing_codes = [
            cls.OCR_QUALITY_LOW, cls.PDF_CORRUPTED, cls.UNSUPPORTED_FORMAT,
            cls.IMAGE_CONVERSION_FAILED, cls.EXTRACTION_TIMEOUT, cls.PARSING_ERROR
        ]
        
        system_codes = [
            cls.SERVICE_UNAVAILABLE, cls.TIMEOUT, cls.RATE_LIMIT_EXCEEDED,
            cls.AUTHENTICATION_FAILED, cls.AUTHORIZATION_FAILED,
            cls.NETWORK_ERROR, cls.DATABASE_ERROR, cls.S3_ACCESS_ERROR
        ]
        
        business_logic_codes = [
            cls.TRADE_NOT_FOUND, cls.COUNTERPARTY_TRADE_MISSING,
            cls.BANK_TRADE_MISSING, cls.MULTIPLE_MATCHES_FOUND,
            cls.NO_MATCH_FOUND, cls.CONFIDENCE_TOO_LOW
        ]
        
        if reason_code in matching_codes:
            return "MATCHING"
        elif reason_code in data_error_codes:
            return "DATA_ERROR"
        elif reason_code in processing_codes:
            return "PROCESSING"
        elif reason_code in system_codes:
            return "SYSTEM"
        elif reason_code in business_logic_codes:
            return "BUSINESS_LOGIC"
        else:
            return "UNKNOWN"
    
    @classmethod
    def get_base_severity_score(cls, reason_code: str) -> float:
        """
        Get the base severity score for a reason code.
        
        Args:
            reason_code: Reason code
        
        Returns:
            float: Base severity score (0.0 to 1.0)
            
        Validates: Requirements 8.1
        """
        severity_scores = {
            # High severity (0.8-1.0)
            cls.NOTIONAL_MISMATCH: 0.8,
            cls.COUNTERPARTY_MISMATCH: 0.9,
            cls.DUPLICATE_TRADE_ID: 0.85,
            cls.MISPLACED_TRADE: 0.9,
            cls.AUTHENTICATION_FAILED: 1.0,
            cls.AUTHORIZATION_FAILED: 0.95,
            
            # Medium-high severity (0.6-0.79)
            cls.DATE_MISMATCH: 0.7,
            cls.CURRENCY_MISMATCH: 0.75,
            cls.PRODUCT_TYPE_MISMATCH: 0.7,
            cls.MISSING_REQUIRED_FIELD: 0.6,
            cls.INCOMPLETE_TRADE_DATA: 0.65,
            cls.DATABASE_ERROR: 0.7,
            
            # Medium severity (0.4-0.59)
            cls.EFFECTIVE_DATE_MISMATCH: 0.5,
            cls.MATURITY_DATE_MISMATCH: 0.5,
            cls.INVALID_FIELD_FORMAT: 0.5,
            cls.AMBIGUOUS_FIELD_VALUE: 0.45,
            cls.OCR_QUALITY_LOW: 0.5,
            cls.PARSING_ERROR: 0.55,
            cls.SERVICE_UNAVAILABLE: 0.5,
            cls.TIMEOUT: 0.4,
            
            # Low severity (0.0-0.39)
            cls.COMMODITY_TYPE_MISMATCH: 0.3,
            cls.STRIKE_PRICE_MISMATCH: 0.35,
            cls.SETTLEMENT_TYPE_MISMATCH: 0.3,
            cls.PDF_CORRUPTED: 0.3,
            cls.UNSUPPORTED_FORMAT: 0.25,
            cls.RATE_LIMIT_EXCEEDED: 0.2,
            cls.NETWORK_ERROR: 0.3,
            cls.CONFIDENCE_TOO_LOW: 0.35,
        }
        
        return severity_scores.get(reason_code, 0.5)  # Default to medium severity


def classify_reason_codes(reason_codes: list) -> dict:
    """
    Classify a list of reason codes by category and compute aggregate severity.
    
    Args:
        reason_codes: List of reason codes
    
    Returns:
        dict: Classification result with categories and severity
        
    Validates: Requirements 7.2, 7.5, 8.1
    """
    if not reason_codes:
        return {
            "categories": [],
            "max_severity": 0.0,
            "avg_severity": 0.0,
            "primary_category": None
        }
    
    # Categorize each reason code
    categories = {}
    severities = []
    
    for code in reason_codes:
        category = ReasonCodeTaxonomy.get_reason_code_category(code)
        severity = ReasonCodeTaxonomy.get_base_severity_score(code)
        
        if category not in categories:
            categories[category] = []
        categories[category].append(code)
        severities.append(severity)
    
    # Determine primary category (most codes)
    primary_category = max(categories.items(), key=lambda x: len(x[1]))[0] if categories else None
    
    return {
        "categories": list(categories.keys()),
        "category_breakdown": categories,
        "max_severity": max(severities) if severities else 0.0,
        "avg_severity": sum(severities) / len(severities) if severities else 0.0,
        "primary_category": primary_category,
        "reason_code_count": len(reason_codes)
    }


def get_recommended_routing(reason_codes: list) -> str:
    """
    Get recommended routing based on reason codes.
    
    Args:
        reason_codes: List of reason codes
    
    Returns:
        str: Recommended routing (OPS_DESK, SENIOR_OPS, COMPLIANCE, ENGINEERING, AUTO_RESOLVE)
        
    Validates: Requirements 8.1
    """
    if not reason_codes:
        return "AUTO_RESOLVE"
    
    classification = classify_reason_codes(reason_codes)
    max_severity = classification["max_severity"]
    primary_category = classification["primary_category"]
    
    # Critical severity or authentication/authorization issues -> SENIOR_OPS
    if max_severity >= 0.9:
        return "SENIOR_OPS"
    
    # High severity matching issues -> OPS_DESK
    if max_severity >= 0.7 and primary_category == "MATCHING":
        return "OPS_DESK"
    
    # Data errors -> OPS_DESK
    if primary_category == "DATA_ERROR":
        return "OPS_DESK"
    
    # System errors -> ENGINEERING
    if primary_category == "SYSTEM":
        return "ENGINEERING"
    
    # Processing errors -> ENGINEERING
    if primary_category == "PROCESSING":
        return "ENGINEERING"
    
    # Medium severity -> OPS_DESK
    if max_severity >= 0.5:
        return "OPS_DESK"
    
    # Low severity -> AUTO_RESOLVE
    return "AUTO_RESOLVE"
