"""
User Feedback System for AI Model Performance Improvement

This module provides mechanisms for users to provide feedback on AI decisions,
track model performance over time, and implement continuous learning capabilities.
"""

import json
import logging
import uuid
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import sqlite3
from pathlib import Path

from strands import tool

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback users can provide"""
    CORRECT_DECISION = "correct_decision"
    INCORRECT_DECISION = "incorrect_decision"
    CONFIDENCE_TOO_HIGH = "confidence_too_high"
    CONFIDENCE_TOO_LOW = "confidence_too_low"
    MISSING_CONTEXT = "missing_context"
    FIELD_MAPPING_ERROR = "field_mapping_error"
    SEMANTIC_MATCHING_ERROR = "semantic_matching_error"
    EXPLANATION_UNCLEAR = "explanation_unclear"


class FeedbackSeverity(Enum):
    """Severity levels for feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UserFeedback:
    """Structured user feedback on AI decisions"""
    feedback_id: str
    user_id: str
    timestamp: str
    trade_pair_id: str
    decision_type: str  # "matching", "reconciliation", "field_comparison"
    feedback_type: FeedbackType
    severity: FeedbackSeverity
    original_decision: Dict[str, Any]
    user_correction: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    model_version: Optional[str] = None


@dataclass
class FeedbackAnalysis:
    """Analysis of feedback patterns and trends"""
    analysis_id: str
    analysis_timestamp: str
    feedback_count: int
    feedback_by_type: Dict[str, int]
    feedback_by_severity: Dict[str, int]
    common_issues: List[Dict[str, Any]]
    improvement_suggestions: List[str]
    model_performance_trends: Dict[str, Any]


class FeedbackDatabase:
    """SQLite database for storing and managing user feedback"""
    
    def __init__(self, db_path: str = "user_feedback.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the feedback database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    trade_pair_id TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    original_decision TEXT NOT NULL,
                    user_correction TEXT,
                    comments TEXT,
                    context_data TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create feedback analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_analysis (
                    analysis_id TEXT PRIMARY KEY,
                    analysis_timestamp TEXT NOT NULL,
                    feedback_count INTEGER NOT NULL,
                    analysis_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create model performance tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    performance_id TEXT PRIMARY KEY,
                    model_version TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    measurement_timestamp TEXT NOT NULL,
                    context_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def store_feedback(self, feedback: UserFeedback) -> bool:
        """Store user feedback in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO feedback (
                        feedback_id, user_id, timestamp, trade_pair_id, decision_type,
                        feedback_type, severity, original_decision, user_correction,
                        comments, context_data, processed, model_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    feedback.feedback_id,
                    feedback.user_id,
                    feedback.timestamp,
                    feedback.trade_pair_id,
                    feedback.decision_type,
                    feedback.feedback_type.value,
                    feedback.severity.value,
                    json.dumps(feedback.original_decision),
                    json.dumps(feedback.user_correction) if feedback.user_correction else None,
                    feedback.comments,
                    json.dumps(feedback.context_data),
                    feedback.processed,
                    feedback.model_version
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")
            return False
    
    def get_feedback(self, limit: int = 100, processed: Optional[bool] = None,
                    feedback_type: Optional[FeedbackType] = None) -> List[UserFeedback]:
        """Retrieve feedback from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM feedback"
                params = []
                conditions = []
                
                if processed is not None:
                    conditions.append("processed = ?")
                    params.append(processed)
                
                if feedback_type is not None:
                    conditions.append("feedback_type = ?")
                    params.append(feedback_type.value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                feedback_list = []
                for row in rows:
                    feedback = UserFeedback(
                        feedback_id=row[0],
                        user_id=row[1],
                        timestamp=row[2],
                        trade_pair_id=row[3],
                        decision_type=row[4],
                        feedback_type=FeedbackType(row[5]),
                        severity=FeedbackSeverity(row[6]),
                        original_decision=json.loads(row[7]),
                        user_correction=json.loads(row[8]) if row[8] else None,
                        comments=row[9],
                        context_data=json.loads(row[10]) if row[10] else {},
                        processed=bool(row[11]),
                        model_version=row[12]
                    )
                    feedback_list.append(feedback)
                
                return feedback_list
                
        except Exception as e:
            logger.error(f"Failed to retrieve feedback: {e}")
            return []
    
    def mark_feedback_processed(self, feedback_id: str) -> bool:
        """Mark feedback as processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE feedback SET processed = TRUE WHERE feedback_id = ?",
                    (feedback_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to mark feedback as processed: {e}")
            return False
    
    def store_performance_metric(self, model_version: str, metric_name: str, 
                               metric_value: float, context_data: Optional[Dict[str, Any]] = None) -> bool:
        """Store model performance metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO model_performance (
                        performance_id, model_version, metric_name, metric_value,
                        measurement_timestamp, context_data
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    model_version,
                    metric_name,
                    metric_value,
                    datetime.now().isoformat(),
                    json.dumps(context_data) if context_data else None
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store performance metric: {e}")
            return False


class FeedbackAnalyzer:
    """Analyzes user feedback to identify patterns and improvement opportunities"""
    
    def __init__(self, db: FeedbackDatabase):
        self.db = db
    
    def analyze_feedback_patterns(self, days_back: int = 30) -> FeedbackAnalysis:
        """Analyze feedback patterns over specified time period"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Get recent feedback
        all_feedback = self.db.get_feedback(limit=1000)
        recent_feedback = [
            f for f in all_feedback 
            if f.timestamp >= cutoff_date
        ]
        
        if not recent_feedback:
            return FeedbackAnalysis(
                analysis_id=str(uuid.uuid4()),
                analysis_timestamp=datetime.now().isoformat(),
                feedback_count=0,
                feedback_by_type={},
                feedback_by_severity={},
                common_issues=[],
                improvement_suggestions=[],
                model_performance_trends={}
            )
        
        # Analyze feedback by type
        feedback_by_type = {}
        for feedback in recent_feedback:
            feedback_type = feedback.feedback_type.value
            feedback_by_type[feedback_type] = feedback_by_type.get(feedback_type, 0) + 1
        
        # Analyze feedback by severity
        feedback_by_severity = {}
        for feedback in recent_feedback:
            severity = feedback.severity.value
            feedback_by_severity[severity] = feedback_by_severity.get(severity, 0) + 1
        
        # Identify common issues
        common_issues = self._identify_common_issues(recent_feedback)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(recent_feedback, common_issues)
        
        # Analyze performance trends
        performance_trends = self._analyze_performance_trends(recent_feedback)
        
        return FeedbackAnalysis(
            analysis_id=str(uuid.uuid4()),
            analysis_timestamp=datetime.now().isoformat(),
            feedback_count=len(recent_feedback),
            feedback_by_type=feedback_by_type,
            feedback_by_severity=feedback_by_severity,
            common_issues=common_issues,
            improvement_suggestions=improvement_suggestions,
            model_performance_trends=performance_trends
        )
    
    def _identify_common_issues(self, feedback_list: List[UserFeedback]) -> List[Dict[str, Any]]:
        """Identify common issues from feedback"""
        issues = []
        
        # Group by decision type and feedback type
        issue_groups = {}
        for feedback in feedback_list:
            key = f"{feedback.decision_type}_{feedback.feedback_type.value}"
            if key not in issue_groups:
                issue_groups[key] = []
            issue_groups[key].append(feedback)
        
        # Identify issues that occur frequently
        for key, group in issue_groups.items():
            if len(group) >= 3:  # At least 3 occurrences
                decision_type, feedback_type = key.split('_', 1)
                
                # Analyze common patterns in this group
                common_contexts = self._find_common_contexts(group)
                
                issues.append({
                    "issue_type": feedback_type,
                    "decision_type": decision_type,
                    "frequency": len(group),
                    "severity_distribution": {
                        severity.value: sum(1 for f in group if f.severity == severity)
                        for severity in FeedbackSeverity
                    },
                    "common_contexts": common_contexts,
                    "sample_comments": [f.comments for f in group[:3] if f.comments]
                })
        
        # Sort by frequency
        issues.sort(key=lambda x: x["frequency"], reverse=True)
        return issues
    
    def _find_common_contexts(self, feedback_group: List[UserFeedback]) -> Dict[str, Any]:
        """Find common contexts in a group of feedback"""
        contexts = {}
        
        for feedback in feedback_group:
            context_data = feedback.context_data
            
            # Look for common transaction types
            if "transaction_type" in context_data:
                tx_type = context_data["transaction_type"]
                contexts.setdefault("transaction_types", {})
                contexts["transaction_types"][tx_type] = contexts["transaction_types"].get(tx_type, 0) + 1
            
            # Look for common field names
            if "field_name" in context_data:
                field_name = context_data["field_name"]
                contexts.setdefault("field_names", {})
                contexts["field_names"][field_name] = contexts["field_names"].get(field_name, 0) + 1
            
            # Look for common model versions
            if feedback.model_version:
                contexts.setdefault("model_versions", {})
                contexts["model_versions"][feedback.model_version] = contexts["model_versions"].get(feedback.model_version, 0) + 1
        
        return contexts
    
    def _generate_improvement_suggestions(self, feedback_list: List[UserFeedback], 
                                        common_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement suggestions based on feedback analysis"""
        suggestions = []
        
        # Analyze high-severity feedback
        high_severity_feedback = [f for f in feedback_list if f.severity in [FeedbackSeverity.HIGH, FeedbackSeverity.CRITICAL]]
        if high_severity_feedback:
            suggestions.append(f"Address {len(high_severity_feedback)} high/critical severity issues immediately")
        
        # Analyze common issue patterns
        for issue in common_issues[:3]:  # Top 3 issues
            issue_type = issue["issue_type"]
            decision_type = issue["decision_type"]
            frequency = issue["frequency"]
            
            if issue_type == "confidence_too_high":
                suggestions.append(f"Review confidence calibration for {decision_type} decisions ({frequency} reports)")
            elif issue_type == "semantic_matching_error":
                suggestions.append(f"Improve semantic matching algorithms for {decision_type} ({frequency} reports)")
            elif issue_type == "field_mapping_error":
                suggestions.append(f"Update field mapping rules for {decision_type} ({frequency} reports)")
            elif issue_type == "explanation_unclear":
                suggestions.append(f"Improve explanation clarity for {decision_type} decisions ({frequency} reports)")
        
        # Analyze feedback trends
        incorrect_decisions = [f for f in feedback_list if f.feedback_type == FeedbackType.INCORRECT_DECISION]
        if len(incorrect_decisions) > len(feedback_list) * 0.2:  # More than 20% incorrect
            suggestions.append("High rate of incorrect decisions detected - consider model retraining")
        
        # Model-specific suggestions
        model_versions = {}
        for feedback in feedback_list:
            if feedback.model_version:
                model_versions[feedback.model_version] = model_versions.get(feedback.model_version, 0) + 1
        
        if model_versions:
            problematic_version = max(model_versions.items(), key=lambda x: x[1])
            if problematic_version[1] > len(feedback_list) * 0.5:
                suggestions.append(f"Model version {problematic_version[0]} has high feedback volume - investigate")
        
        return suggestions
    
    def _analyze_performance_trends(self, feedback_list: List[UserFeedback]) -> Dict[str, Any]:
        """Analyze performance trends from feedback"""
        trends = {}
        
        # Calculate accuracy trend (inverse of incorrect decisions)
        total_feedback = len(feedback_list)
        incorrect_feedback = len([f for f in feedback_list if f.feedback_type == FeedbackType.INCORRECT_DECISION])
        accuracy_rate = (total_feedback - incorrect_feedback) / total_feedback * 100 if total_feedback > 0 else 100
        
        trends["accuracy_rate"] = accuracy_rate
        trends["total_feedback_volume"] = total_feedback
        trends["error_rate"] = incorrect_feedback / total_feedback * 100 if total_feedback > 0 else 0
        
        # Analyze confidence calibration
        confidence_issues = len([
            f for f in feedback_list 
            if f.feedback_type in [FeedbackType.CONFIDENCE_TOO_HIGH, FeedbackType.CONFIDENCE_TOO_LOW]
        ])
        trends["confidence_calibration_issues"] = confidence_issues / total_feedback * 100 if total_feedback > 0 else 0
        
        return trends


class UserTrainingSystem:
    """System for training users on new AI features and best practices"""
    
    def __init__(self):
        self.training_modules = {
            "ai_decision_understanding": self._create_ai_decision_module,
            "feedback_best_practices": self._create_feedback_module,
            "confidence_score_interpretation": self._create_confidence_module,
            "semantic_matching_concepts": self._create_semantic_module
        }
    
    def generate_training_material(self, module_name: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate training material for specified module"""
        if module_name not in self.training_modules:
            return {"error": f"Unknown training module: {module_name}"}
        
        return self.training_modules[module_name](user_context or {})
    
    def _create_ai_decision_module(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create training module for understanding AI decisions"""
        return {
            "title": "Understanding AI-Powered Trade Reconciliation Decisions",
            "sections": [
                {
                    "title": "How AI Enhances Trade Matching",
                    "content": [
                        "AI systems analyze trade context to identify transaction types automatically",
                        "Semantic matching recognizes equivalent terms (e.g., 'settlement date' vs 'maturity date')",
                        "Context-aware analysis adapts to different trading scenarios (commodities, FX, derivatives)",
                        "Confidence scores indicate the system's certainty in its decisions"
                    ]
                },
                {
                    "title": "Decision Modes Explained",
                    "content": [
                        "Deterministic: Uses traditional rule-based matching with exact criteria",
                        "LLM: Leverages AI for intelligent semantic analysis and context understanding",
                        "Hybrid: Combines both approaches for optimal accuracy and reliability"
                    ]
                },
                {
                    "title": "Reading AI Explanations",
                    "content": [
                        "Look for transaction type identification in the explanation",
                        "Check which fields were considered critical for the specific trade type",
                        "Review confidence scores - higher scores indicate more certain decisions",
                        "Pay attention to fallback indicators - these show when AI wasn't available"
                    ]
                }
            ],
            "examples": [
                {
                    "scenario": "Commodity Swap Matching",
                    "explanation": "AI identified this as a commodity swap and focused on notional quantity, commodity type, and settlement terms rather than generic trade fields."
                }
            ],
            "quiz": [
                {
                    "question": "What does a confidence score of 0.95 indicate?",
                    "options": ["Low confidence", "Medium confidence", "High confidence", "Perfect match"],
                    "correct": 2
                }
            ]
        }
    
    def _create_feedback_module(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create training module for effective feedback"""
        return {
            "title": "Providing Effective Feedback on AI Decisions",
            "sections": [
                {
                    "title": "When to Provide Feedback",
                    "content": [
                        "When AI makes an incorrect matching decision",
                        "When confidence scores seem inappropriate for the decision quality",
                        "When explanations are unclear or unhelpful",
                        "When you notice patterns in AI errors"
                    ]
                },
                {
                    "title": "Types of Feedback",
                    "content": [
                        "Correct/Incorrect Decision: Basic accuracy feedback",
                        "Confidence Issues: When confidence doesn't match decision quality",
                        "Missing Context: When AI missed important trade context",
                        "Field Mapping Errors: When AI misunderstood field relationships",
                        "Explanation Clarity: When AI explanations are confusing"
                    ]
                },
                {
                    "title": "Best Practices",
                    "content": [
                        "Be specific in your comments - explain what went wrong",
                        "Provide context about the trade type and market conventions",
                        "Include suggestions for improvement when possible",
                        "Use appropriate severity levels (Critical for major errors)"
                    ]
                }
            ],
            "examples": [
                {
                    "good_feedback": "AI incorrectly matched trades with different commodity types (Oil vs Gas). Should prioritize commodity type in matching algorithm.",
                    "poor_feedback": "This is wrong."
                }
            ]
        }
    
    def _create_confidence_module(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create training module for confidence score interpretation"""
        return {
            "title": "Interpreting AI Confidence Scores",
            "sections": [
                {
                    "title": "Confidence Score Ranges",
                    "content": [
                        "0.9-1.0: Very high confidence - AI is very certain about the decision",
                        "0.8-0.9: High confidence - AI is confident but some uncertainty remains",
                        "0.6-0.8: Moderate confidence - AI has reasonable certainty",
                        "0.0-0.6: Low confidence - AI is uncertain, manual review recommended"
                    ]
                },
                {
                    "title": "Factors Affecting Confidence",
                    "content": [
                        "Field similarity: How well trade fields match between documents",
                        "Context clarity: How clearly the AI understood the transaction type",
                        "Data quality: Completeness and consistency of trade data",
                        "Model familiarity: How similar the trade is to training examples"
                    ]
                },
                {
                    "title": "Acting on Confidence Scores",
                    "content": [
                        "High confidence (>0.8): Generally safe to accept AI decision",
                        "Medium confidence (0.6-0.8): Review AI reasoning before accepting",
                        "Low confidence (<0.6): Always perform manual review",
                        "Consider trade value and risk when making decisions"
                    ]
                }
            ]
        }
    
    def _create_semantic_module(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create training module for semantic matching concepts"""
        return {
            "title": "Understanding Semantic Matching in Trade Reconciliation",
            "sections": [
                {
                    "title": "What is Semantic Matching?",
                    "content": [
                        "Goes beyond exact text matching to understand meaning",
                        "Recognizes that 'settlement date' and 'maturity date' often mean the same thing",
                        "Handles variations in terminology between different trading parties",
                        "Adapts to market-specific conventions and naming patterns"
                    ]
                },
                {
                    "title": "Common Semantic Equivalents",
                    "content": [
                        "Notional/Amount/Principal: Different terms for trade size",
                        "Counterparty/Client/Entity: Different terms for trading partner",
                        "Settlement/Maturity/Expiry: Different terms for end date",
                        "Rate/Price/Level: Different terms for trading price"
                    ]
                },
                {
                    "title": "Benefits and Limitations",
                    "content": [
                        "Benefits: Handles real-world terminology variations automatically",
                        "Benefits: Reduces false mismatches from naming differences",
                        "Limitations: May occasionally over-match dissimilar fields",
                        "Limitations: Requires good training data for accuracy"
                    ]
                }
            ]
        }


@tool
async def submit_user_feedback(
    trade_pair_id: str,
    decision_type: str,
    feedback_type: str,
    severity: str,
    original_decision: Dict[str, Any],
    user_id: str = "system_user",
    user_correction: Optional[Dict[str, Any]] = None,
    comments: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Submit user feedback on AI decision for model improvement.
    
    Args:
        trade_pair_id: ID of the trade pair the feedback relates to
        decision_type: Type of decision ("matching", "reconciliation", "field_comparison")
        feedback_type: Type of feedback (see FeedbackType enum)
        severity: Severity level (see FeedbackSeverity enum)
        original_decision: The original AI decision being reviewed
        user_id: ID of the user providing feedback
        user_correction: Optional correction provided by user
        comments: Optional additional comments
        context_data: Optional additional context information
        
    Returns:
        Dictionary with feedback submission status and ID
    """
    try:
        # Validate inputs
        try:
            feedback_type_enum = FeedbackType(feedback_type)
            severity_enum = FeedbackSeverity(severity)
        except ValueError as e:
            return {"success": False, "error": f"Invalid enum value: {e}"}
        
        # Create feedback object
        feedback = UserFeedback(
            feedback_id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            trade_pair_id=trade_pair_id,
            decision_type=decision_type,
            feedback_type=feedback_type_enum,
            severity=severity_enum,
            original_decision=original_decision,
            user_correction=user_correction,
            comments=comments,
            context_data=context_data or {},
            processed=False,
            model_version="enhanced_v1.0"  # This would be dynamic in production
        )
        
        # Store feedback
        db = FeedbackDatabase()
        success = db.store_feedback(feedback)
        
        if success:
            logger.info(f"User feedback submitted successfully: {feedback.feedback_id}")
            return {
                "success": True,
                "feedback_id": feedback.feedback_id,
                "message": "Feedback submitted successfully and will be used to improve AI performance"
            }
        else:
            return {"success": False, "error": "Failed to store feedback"}
            
    except Exception as e:
        logger.error(f"Failed to submit user feedback: {e}")
        return {"success": False, "error": str(e)}


@tool
async def analyze_user_feedback(days_back: int = 30) -> Dict[str, Any]:
    """
    Analyze user feedback patterns and generate improvement insights.
    
    Args:
        days_back: Number of days to look back for feedback analysis
        
    Returns:
        Dictionary with feedback analysis results and recommendations
    """
    try:
        db = FeedbackDatabase()
        analyzer = FeedbackAnalyzer(db)
        
        analysis = analyzer.analyze_feedback_patterns(days_back)
        
        logger.info(f"Feedback analysis completed: {analysis.feedback_count} feedback items analyzed")
        
        return {
            "success": True,
            "analysis": asdict(analysis),
            "summary": {
                "total_feedback": analysis.feedback_count,
                "most_common_issue": max(analysis.feedback_by_type.items(), key=lambda x: x[1])[0] if analysis.feedback_by_type else "None",
                "improvement_priority": analysis.improvement_suggestions[0] if analysis.improvement_suggestions else "No specific recommendations"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze user feedback: {e}")
        return {"success": False, "error": str(e)}


@tool
async def get_training_material(module_name: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get training material for users on AI features and best practices.
    
    Args:
        module_name: Name of the training module to retrieve
        user_context: Optional context about the user for personalization
        
    Returns:
        Dictionary with training material content
    """
    try:
        training_system = UserTrainingSystem()
        material = training_system.generate_training_material(module_name, user_context)
        
        logger.info(f"Training material generated for module: {module_name}")
        
        return {
            "success": True,
            "module_name": module_name,
            "material": material
        }
        
    except Exception as e:
        logger.error(f"Failed to generate training material: {e}")
        return {"success": False, "error": str(e)}