"""
Matching Result Models

This module defines models for trade matching results, including
classification enums, match scores, and detailed difference tracking.

Requirements: 7.1, 7.2, 7.3
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class MatchClassification(str, Enum):
    """
    Classification of matching results.
    
    Requirements:
        - 7.2: Classify results based on match scores and reason codes
    """
    MATCHED = "MATCHED"  # Perfect or near-perfect match (score >= 0.85)
    PROBABLE_MATCH = "PROBABLE_MATCH"  # Likely match with minor differences (score 0.70-0.84)
    REVIEW_REQUIRED = "REVIEW_REQUIRED"  # Requires human review (score 0.50-0.69)
    BREAK = "BREAK"  # Significant mismatch (score < 0.50)
    DATA_ERROR = "DATA_ERROR"  # Data integrity issue (e.g., misplaced trade)


class DecisionStatus(str, Enum):
    """
    Decision status for match results.
    
    Determines the next action in the workflow:
    - AUTO_MATCH: Automatically confirm the match
    - ESCALATE: Send to HITL for human review
    - EXCEPTION: Send to exception handling
    """
    AUTO_MATCH = "AUTO_MATCH"  # Score >= 0.85
    ESCALATE = "ESCALATE"  # Score 0.70-0.84
    EXCEPTION = "EXCEPTION"  # Score < 0.70


class FieldDifference(BaseModel):
    """
    Represents a difference between two trade fields.
    
    Attributes:
        field_name: Name of the field with a difference
        bank_value: Value from the bank trade
        counterparty_value: Value from the counterparty trade
        difference_type: Type of difference (EXACT_MISMATCH, TOLERANCE_EXCEEDED, MISSING)
        tolerance_applied: Whether a tolerance was applied
        within_tolerance: Whether the difference is within tolerance
    """
    field_name: str = Field(
        ...,
        description="Name of the field with a difference"
    )
    
    bank_value: Optional[Any] = Field(
        None,
        description="Value from the bank trade"
    )
    
    counterparty_value: Optional[Any] = Field(
        None,
        description="Value from the counterparty trade"
    )
    
    difference_type: str = Field(
        ...,
        description="Type of difference (EXACT_MISMATCH, TOLERANCE_EXCEEDED, MISSING, FUZZY_MISMATCH)"
    )
    
    tolerance_applied: bool = Field(
        default=False,
        description="Whether a tolerance was applied to this field"
    )
    
    within_tolerance: bool = Field(
        default=False,
        description="Whether the difference is within the allowed tolerance"
    )
    
    percentage_difference: Optional[float] = Field(
        None,
        description="Percentage difference for numeric fields",
        ge=0.0
    )


class MatchingResult(BaseModel):
    """
    Complete matching result for a trade pair.
    
    This model contains all information about a matching operation including
    the classification, match score, differences, and decision status.
    
    Requirements:
        - 7.1: Perform fuzzy matching with tolerances
        - 7.2: Classify results with match scores
        - 7.3: Generate detailed reports
    
    Attributes:
        trade_id: Unique identifier for the trade
        classification: Match classification enum
        match_score: Computed match score (0.0 to 1.0)
        decision_status: Decision status for workflow routing
        reason_codes: List of reason codes explaining the result
        bank_trade: Bank trade data (if available)
        counterparty_trade: Counterparty trade data (if available)
        differences: List of field differences
        confidence_score: Overall confidence in the matching result
        requires_hitl: Whether human review is required
        report_path: S3 path to the detailed matching report
    """
    
    trade_id: str = Field(
        ...,
        description="Unique identifier for the trade",
        min_length=1
    )
    
    classification: MatchClassification = Field(
        ...,
        description="Match classification enum"
    )
    
    match_score: float = Field(
        ...,
        description="Computed match score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    decision_status: DecisionStatus = Field(
        ...,
        description="Decision status for workflow routing"
    )
    
    reason_codes: List[str] = Field(
        default_factory=list,
        description="List of reason codes explaining the result"
    )
    
    bank_trade: Optional[Dict[str, Any]] = Field(
        None,
        description="Bank trade data (if available)"
    )
    
    counterparty_trade: Optional[Dict[str, Any]] = Field(
        None,
        description="Counterparty trade data (if available)"
    )
    
    differences: List[FieldDifference] = Field(
        default_factory=list,
        description="List of field differences between trades"
    )
    
    confidence_score: float = Field(
        default=1.0,
        description="Overall confidence in the matching result (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    requires_hitl: bool = Field(
        default=False,
        description="Whether human review is required"
    )
    
    report_path: Optional[str] = Field(
        None,
        description="S3 path to the detailed matching report"
    )
    
    matching_timestamp: Optional[str] = Field(
        None,
        description="ISO timestamp when matching was performed"
    )
    
    @field_validator("decision_status", mode="after")
    @classmethod
    def validate_decision_status_matches_score(cls, v: DecisionStatus, info) -> DecisionStatus:
        """
        Validate that decision status aligns with match score.
        
        Requirements:
            - Score >= 0.85: AUTO_MATCH
            - Score 0.70-0.84: ESCALATE
            - Score < 0.70: EXCEPTION
        """
        if info.data:
            match_score = info.data.get('match_score')
            if match_score is not None:
                if match_score >= 0.85 and v != DecisionStatus.AUTO_MATCH:
                    raise ValueError(
                        f"Match score {match_score} >= 0.85 should have decision_status AUTO_MATCH"
                    )
                elif 0.70 <= match_score < 0.85 and v != DecisionStatus.ESCALATE:
                    raise ValueError(
                        f"Match score {match_score} in [0.70, 0.85) should have decision_status ESCALATE"
                    )
                elif match_score < 0.70 and v != DecisionStatus.EXCEPTION:
                    raise ValueError(
                        f"Match score {match_score} < 0.70 should have decision_status EXCEPTION"
                    )
        return v
    
    @field_validator("requires_hitl", mode="after")
    @classmethod
    def validate_hitl_requirement(cls, v: bool, info) -> bool:
        """
        Validate that HITL requirement aligns with decision status.
        
        ESCALATE status should require HITL.
        """
        if info.data:
            decision_status = info.data.get('decision_status')
            if decision_status == DecisionStatus.ESCALATE and not v:
                raise ValueError("ESCALATE decision_status requires requires_hitl=True")
        return v
    
    def get_summary(self) -> str:
        """
        Get a human-readable summary of the matching result.
        
        Returns:
            String summary of the result
        """
        summary_parts = [
            f"Trade ID: {self.trade_id}",
            f"Classification: {self.classification.value}",
            f"Match Score: {self.match_score:.2f}",
            f"Decision: {self.decision_status.value}",
        ]
        
        if self.reason_codes:
            summary_parts.append(f"Reason Codes: {', '.join(self.reason_codes)}")
        
        if self.differences:
            summary_parts.append(f"Differences Found: {len(self.differences)}")
        
        return " | ".join(summary_parts)
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "trade_id": "GCS382857",
                    "classification": "MATCHED",
                    "match_score": 0.95,
                    "decision_status": "AUTO_MATCH",
                    "reason_codes": [],
                    "bank_trade": {
                        "Trade_ID": "GCS382857",
                        "notional": 1000000.00,
                        "trade_date": "2024-10-15"
                    },
                    "counterparty_trade": {
                        "Trade_ID": "GCS382857",
                        "notional": 1000000.00,
                        "trade_date": "2024-10-15"
                    },
                    "differences": [],
                    "confidence_score": 0.98,
                    "requires_hitl": False,
                    "report_path": "s3://bucket/reports/matching_report_GCS382857.md"
                },
                {
                    "trade_id": "FAB26933659",
                    "classification": "PROBABLE_MATCH",
                    "match_score": 0.78,
                    "decision_status": "ESCALATE",
                    "reason_codes": ["DATE_MISMATCH"],
                    "bank_trade": {
                        "Trade_ID": "FAB26933659",
                        "notional": 500000.00,
                        "trade_date": "2024-10-16"
                    },
                    "counterparty_trade": {
                        "Trade_ID": "FAB26933659",
                        "notional": 500000.00,
                        "trade_date": "2024-10-17"
                    },
                    "differences": [
                        {
                            "field_name": "trade_date",
                            "bank_value": "2024-10-16",
                            "counterparty_value": "2024-10-17",
                            "difference_type": "TOLERANCE_EXCEEDED",
                            "tolerance_applied": True,
                            "within_tolerance": True
                        }
                    ],
                    "confidence_score": 0.85,
                    "requires_hitl": True,
                    "report_path": "s3://bucket/reports/matching_report_FAB26933659.md"
                }
            ]
        }
