"""
Trade Matching Module

This module provides fuzzy matching, scoring, classification, and reporting
capabilities for trade confirmation matching.

Requirements: 7.1, 7.2, 7.3, 7.4, 18.3, 18.4
"""

from .fuzzy_matcher import fuzzy_match, MatchResult
from .scorer import compute_match_score
from .classifier import classify_match
from .report_generator import generate_report

__all__ = [
    "fuzzy_match",
    "MatchResult",
    "compute_match_score",
    "classify_match",
    "generate_report",
]
