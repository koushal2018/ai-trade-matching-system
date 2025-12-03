"""
Data models for the AgentCore Trade Matching System.

This module contains all Pydantic models used across the system including:
- Canonical adapter outputs
- Trade data models
- Matching results
- Exception and triage models
- Audit trail models
- Event message schemas
- Agent registry
- Workflow and event taxonomy
- Reason code taxonomy
"""

from .adapter import CanonicalAdapterOutput
from .trade import CanonicalTradeModel
from .matching import MatchingResult, MatchClassification
from .exception import ExceptionRecord, TriageResult, TriageClassification
from .audit import AuditRecord
from .events import StandardEventMessage, EventTaxonomy
from .registry import AgentRegistryEntry, AgentRegistry, ScalingConfig
from .taxonomy import (
    WorkflowNode,
    WorkflowTaxonomy,
    ReasonCodeTaxonomy,
    TaxonomyLoader,
    create_default_taxonomy,
    classify_reason_codes,
    get_recommended_routing
)

__all__ = [
    "CanonicalAdapterOutput",
    "CanonicalTradeModel",
    "MatchingResult",
    "MatchClassification",
    "ExceptionRecord",
    "TriageResult",
    "TriageClassification",
    "AuditRecord",
    "StandardEventMessage",
    "EventTaxonomy",
    "AgentRegistryEntry",
    "AgentRegistry",
    "ScalingConfig",
    "WorkflowNode",
    "WorkflowTaxonomy",
    "ReasonCodeTaxonomy",
    "TaxonomyLoader",
    "create_default_taxonomy",
    "classify_reason_codes",
    "get_recommended_routing",
]
