"""
Canonical Adapter Output Schema

This module defines the standardized output format for all adapter agents
(PDF, Chat, Email, Voice). All adapters must produce output conforming to
this canonical schema to ensure interoperability.

Requirements: 3.2, 5.1, 5.2, 5.3
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class CanonicalAdapterOutput(BaseModel):
    """
    Canonical output schema for all adapter agents.
    
    This schema ensures that all adapters (PDF, Chat, Email, Voice) produce
    standardized output that can be consumed by downstream agents without
    modification.
    
    Attributes:
        adapter_type: Type of adapter that produced this output
        document_id: Unique identifier for the document/message
        source_type: Classification of the trade source (BANK or COUNTERPARTY)
        extracted_text: The extracted text content from the source
        metadata: Extensible metadata fields specific to the adapter type
        s3_location: S3 URI where the canonical output is stored
        processing_timestamp: When the adapter processed this document
        correlation_id: Optional correlation ID for distributed tracing
    """
    
    adapter_type: Literal["PDF", "CHAT", "EMAIL", "VOICE"] = Field(
        ...,
        description="Type of adapter that produced this output"
    )
    
    document_id: str = Field(
        ...,
        description="Unique identifier for the document or message",
        min_length=1
    )
    
    source_type: Literal["BANK", "COUNTERPARTY"] = Field(
        ...,
        description="Classification of the trade source"
    )
    
    extracted_text: str = Field(
        ...,
        description="The extracted text content from the source",
        min_length=1
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible metadata fields specific to the adapter type"
    )
    
    s3_location: str = Field(
        ...,
        description="S3 URI where the canonical output is stored",
        pattern=r"^s3://[a-z0-9\-\.]+/.+"
    )
    
    processing_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the adapter processed this document"
    )
    
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for distributed tracing across agents"
    )
    
    @field_validator("extracted_text")
    @classmethod
    def validate_extracted_text(cls, v: str) -> str:
        """Ensure extracted text is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("extracted_text cannot be empty or whitespace only")
        return v
    
    @field_validator("metadata", mode="after")
    @classmethod
    def validate_metadata_for_pdf(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        """
        Validate that PDF adapters include required metadata fields.
        
        For PDF adapters, the following fields are required:
        - page_count: Number of pages in the PDF
        - dpi: Resolution of the converted images
        """
        # Access adapter_type from the validation context
        if info.data and info.data.get('adapter_type') == 'PDF':
            required_fields = ['page_count', 'dpi']
            missing_fields = [f for f in required_fields if f not in v]
            if missing_fields:
                raise ValueError(
                    f"PDF adapter output must include metadata fields: {missing_fields}"
                )
            
            # Validate page_count is positive integer
            if not isinstance(v.get('page_count'), int) or v['page_count'] <= 0:
                raise ValueError("page_count must be a positive integer")
            
            # Validate DPI is 300 (requirement 5.1, 18.1)
            if v.get('dpi') != 300:
                raise ValueError("PDF conversion must use 300 DPI (requirement 5.1)")
        
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "adapter_type": "PDF",
                    "document_id": "doc_456",
                    "source_type": "COUNTERPARTY",
                    "extracted_text": "Trade Confirmation\nTrade ID: GCS382857\n...",
                    "metadata": {
                        "page_count": 5,
                        "dpi": 300,
                        "ocr_confidence": 0.95,
                        "file_size_bytes": 245678
                    },
                    "s3_location": "s3://trade-matching-bucket/extracted/COUNTERPARTY/doc_456.json",
                    "processing_timestamp": "2025-01-15T10:31:30Z",
                    "correlation_id": "corr_abc"
                },
                {
                    "adapter_type": "CHAT",
                    "document_id": "msg_789",
                    "source_type": "BANK",
                    "extracted_text": "Trade details: ID=FAB26933659, Notional=1000000 USD...",
                    "metadata": {
                        "chat_platform": "slack",
                        "user_id": "U123456",
                        "channel_id": "C789012"
                    },
                    "s3_location": "s3://trade-matching-bucket/extracted/BANK/msg_789.json",
                    "processing_timestamp": "2025-01-15T11:00:00Z",
                    "correlation_id": "corr_def"
                }
            ]
        }
