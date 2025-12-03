"""
Tests for Exception Handling Module

This module tests the exception classification, scoring, triage, delegation,
and RL components.
"""

import pytest
from datetime import datetime
from ..models.exception import (
    ExceptionRecord,
    ExceptionType,
    TriageClassification,
    SeverityLevel,
    RoutingDestination,
    ResolutionOutcome
)
from ..models.taxonomy import ReasonCodeTaxonomy
from .classifier import classify_exception, get_classification_description
from .scorer import (
    compute_severity_score,
    get_severity_level,
    get_severity_description,
    compute_severity_breakdown
)
from .triage import triage_exception, get_triage_summary
from .rl_handler import RLExceptionHandler, create_default_rl_handler


class TestExceptionClassifier:
    """Tests for exception classification."""
    
    def test_classify_matching_exception(self):
        """Test classification of matching exceptions."""
        exception = ExceptionRecord(
            exception_id="exc_test_001",
            exception_type=ExceptionType.MATCHING_EXCEPTION,
            event_type="MATCHING_EXCEPTION",
            agent_id="trade_matching_agent",
            reason_codes=[ReasonCodeTaxonomy.NOTIONAL_MISMATCH],
            error_message="Notional mismatch detected",
            match_score=0.65
        )
        
        classification = classify_exception(exception)
        assert classification == TriageClassification.OPERATIONAL_ISSUE
    
    def test_classify_data_integrity_error(self):
        """Test classification of data integrity errors."""
        exception = ExceptionRecord(
            exception_id="exc_test_002",
            exception_type=ExceptionType.DATA_INTEGRITY_ERROR,
            event_type="DATA_ERROR",
            agent_id="trade_extraction_agent",
            reason_codes=[ReasonCodeTaxonomy.MISPLACED_TRADE],
            error_message="Trade in wrong table"
        )
        
        classification = classify_exception(exception)
        assert classification == TriageClassification.DATA_QUALITY_ISSUE
    
    def test_classify_system_error(self):
        """Test classification of system errors."""
        exception = ExceptionRecord(
            exception_id="exc_test_003",
            exception_type=ExceptionType.SERVICE_ERROR,
            event_type="SERVICE_ERROR",
            agent_id="pdf_adapter_agent",
            reason_codes=[ReasonCodeTaxonomy.SERVICE_UNAVAILABLE],
            error_message="Bedrock service unavailable"
        )
        
        classification = classify_exception(exception)
        assert classification == TriageClassification.SYSTEM_ISSUE
    
    def test_classify_compliance_issue(self):
        """Test classification of compliance issues."""
        exception = ExceptionRecord(
            exception_id="exc_test_004",
            exception_type=ExceptionType.SERVICE_ERROR,
            event_type="AUTH_ERROR",
            agent_id="api_gateway",
            reason_codes=[ReasonCodeTaxonomy.AUTHENTICATION_FAILED],
            error_message="Authentication failed"
        )
        
        classification = classify_exception(exception)
        assert classification == TriageClassification.COMPLIANCE_ISSUE
    
    def test_get_classification_description(self):
        """Test getting classification descriptions."""
        desc = get_classification_description(TriageClassification.OPERATIONAL_ISSUE)
        assert "operational review" in desc.lower()


class TestSeverityScorer:
    """Tests for severity scoring."""
    
    def test_compute_severity_score_high(self):
        """Test computing high severity score."""
        exception = ExceptionRecord(
            exception_id="exc_test_005",
            exception_type=ExceptionType.MATCHING_EXCEPTION,
            event_type="MATCHING_EXCEPTION",
            agent_id="trade_matching_agent",
            reason_codes=[ReasonCodeTaxonomy.NOTIONAL_MISMATCH],
            error_message="Notional mismatch",
            match_score=0.50  # Low match score
        )
        
        score = compute_severity_score(exception)
        assert 0.0 <= score <= 1.0
        assert score >= 0.6  # Should be high severity
    
    def test_compute_severity_score_low(self):
        """Test computing low severity score."""
        exception = ExceptionRecord(
            exception_id="exc_test_006",
            exception_type=ExceptionType.PROCESSING_ERROR,
            event_type="PROCESSING_ERROR",
            agent_id="pdf_adapter_agent",
            reason_codes=[ReasonCodeTaxonomy.RATE_LIMIT_EXCEEDED],
            error_message="Rate limit exceeded"
        )
        
        score = compute_severity_score(exception)
        assert 0.0 <= score <= 1.0
        assert score < 0.3  # Should be low severity
    
    def test_get_severity_level(self):
        """Test converting score to severity level."""
        assert get_severity_level(0.1) == SeverityLevel.LOW
        assert get_severity_level(0.4) == SeverityLevel.MEDIUM
        assert get_severity_level(0.7) == SeverityLevel.HIGH
        assert get_severity_level(0.9) == SeverityLevel.CRITICAL
    
    def test_get_severity_description(self):
        """Test getting severity descriptions."""
        desc = get_severity_description(SeverityLevel.CRITICAL)
        assert "critical" in desc.lower()
        assert "immediate" in desc.lower()
    
    def test_compute_severity_breakdown(self):
        """Test computing detailed severity breakdown."""
        exception = ExceptionRecord(
            exception_id="exc_test_007",
            exception_type=ExceptionType.MATCHING_EXCEPTION,
            event_type="MATCHING_EXCEPTION",
            agent_id="trade_matching_agent",
            reason_codes=[ReasonCodeTaxonomy.NOTIONAL_MISMATCH],
            error_message="Notional mismatch",
            match_score=0.65,
            retry_count=2
        )
        
        breakdown = compute_severity_breakdown(exception)
        assert "exception_id" in breakdown
        assert "final_score" in breakdown
        assert "severity_level" in breakdown
        assert "breakdown" in breakdown
        assert "factors" in breakdown


class TestTriageSystem:
    """Tests for triage system."""
    
    def test_triage_high_severity_matching(self):
        """Test triaging high severity matching exception."""
        exception = ExceptionRecord(
            exception_id="exc_test_008",
            exception_type=ExceptionType.MATCHING_EXCEPTION,
            event_type="MATCHING_EXCEPTION",
            agent_id="trade_matching_agent",
            reason_codes=[ReasonCodeTaxonomy.NOTIONAL_MISMATCH],
            error_message="Notional mismatch",
            match_score=0.60
        )
        
        triage_result = triage_exception(exception)
        
        assert triage_result.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        # NOTIONAL_MISMATCH has high base severity (0.8), which can result in CRITICAL severity
        # CRITICAL severity routes to SENIOR_OPS
        assert triage_result.routing in [RoutingDestination.OPS_DESK, RoutingDestination.SENIOR_OPS]
        assert 1 <= triage_result.priority <= 2
        assert triage_result.sla_hours <= 4
    
    def test_triage_compliance_issue(self):
        """Test triaging compliance issue."""
        exception = ExceptionRecord(
            exception_id="exc_test_009",
            exception_type=ExceptionType.SERVICE_ERROR,
            event_type="AUTH_ERROR",
            agent_id="api_gateway",
            reason_codes=[ReasonCodeTaxonomy.AUTHENTICATION_FAILED],
            error_message="Authentication failed"
        )
        
        triage_result = triage_exception(exception)
        
        assert triage_result.severity == SeverityLevel.CRITICAL
        assert triage_result.routing in [RoutingDestination.SENIOR_OPS, RoutingDestination.COMPLIANCE]
        assert triage_result.priority == 1
        assert triage_result.sla_hours == 2
    
    def test_triage_low_severity(self):
        """Test triaging low severity exception."""
        exception = ExceptionRecord(
            exception_id="exc_test_010",
            exception_type=ExceptionType.PROCESSING_ERROR,
            event_type="PROCESSING_ERROR",
            agent_id="pdf_adapter_agent",
            reason_codes=[ReasonCodeTaxonomy.RATE_LIMIT_EXCEEDED],
            error_message="Rate limit exceeded"
        )
        
        triage_result = triage_exception(exception)
        
        assert triage_result.severity == SeverityLevel.LOW
        # PROCESSING_ERROR with SYSTEM category routes to ENGINEERING
        # But low severity can also be AUTO_RESOLVE
        assert triage_result.routing in [RoutingDestination.AUTO_RESOLVE, RoutingDestination.ENGINEERING]
        assert triage_result.priority >= 4
    
    def test_get_triage_summary(self):
        """Test getting triage summary."""
        exception = ExceptionRecord(
            exception_id="exc_test_011",
            exception_type=ExceptionType.MATCHING_EXCEPTION,
            event_type="MATCHING_EXCEPTION",
            agent_id="trade_matching_agent",
            reason_codes=[ReasonCodeTaxonomy.DATE_MISMATCH],
            error_message="Date mismatch"
        )
        
        triage_result = triage_exception(exception)
        summary = get_triage_summary(triage_result)
        
        assert "exception_id" in summary
        assert "severity" in summary
        assert "routing" in summary
        assert "priority" in summary
        assert "sla" in summary


class TestRLHandler:
    """Tests for RL exception handler."""
    
    def test_create_rl_handler(self):
        """Test creating RL handler."""
        handler = create_default_rl_handler()
        assert handler is not None
        assert handler.learning_rate == 0.1
        assert handler.discount_factor == 0.9
    
    def test_record_episode(self):
        """Test recording episode."""
        handler = RLExceptionHandler()
        
        state = {
            "exception_type": "MATCHING_EXCEPTION",
            "reason_codes": ["NOTIONAL_MISMATCH"],
            "match_score": 0.65
        }
        
        handler.record_episode("exc_test_012", state, "OPS_DESK", {})
        
        assert "exc_test_012" in handler.pending_episodes
        assert handler.pending_episodes["exc_test_012"]["action"] == "OPS_DESK"
    
    def test_compute_reward(self):
        """Test computing reward."""
        handler = RLExceptionHandler()
        
        # Test positive reward (within SLA, correct routing)
        outcome1 = ResolutionOutcome(
            exception_id="exc_test_013",
            resolved_at=datetime.utcnow(),
            resolution_time_hours=2.0,
            resolved_within_sla=True,
            routing_was_correct=True
        )
        reward1 = handler.compute_reward(outcome1)
        assert reward1 == 1.0
        
        # Test negative reward (late, incorrect routing)
        outcome2 = ResolutionOutcome(
            exception_id="exc_test_014",
            resolved_at=datetime.utcnow(),
            resolution_time_hours=10.0,
            resolved_within_sla=False,
            routing_was_correct=False
        )
        reward2 = handler.compute_reward(outcome2)
        assert reward2 == -1.0
    
    def test_predict(self):
        """Test predicting action."""
        handler = RLExceptionHandler()
        
        state = {
            "exception_type": "MATCHING_EXCEPTION",
            "reason_codes": ["NOTIONAL_MISMATCH"],
            "match_score": 0.65
        }
        
        action = handler.predict(state)
        assert action in handler.actions
    
    def test_supervised_update(self):
        """Test supervised learning update."""
        handler = RLExceptionHandler()
        
        state = {
            "exception_type": "MATCHING_EXCEPTION",
            "reason_codes": ["COUNTERPARTY_MISMATCH"],
            "match_score": 0.50
        }
        
        # Perform supervised update
        handler.supervised_update(state, "SENIOR_OPS")
        
        # Q-value should be updated
        state_hash = handler._hash_state(state)
        q_value = handler.q_table.get((state_hash, "SENIOR_OPS"), 0.0)
        assert q_value > 0.0
    
    def test_update_with_resolution(self):
        """Test updating with resolution."""
        handler = RLExceptionHandler()
        
        # Record episode
        state = {
            "exception_type": "MATCHING_EXCEPTION",
            "reason_codes": ["NOTIONAL_MISMATCH"],
            "match_score": 0.65
        }
        handler.record_episode("exc_test_015", state, "OPS_DESK", {})
        
        # Update with resolution
        outcome = ResolutionOutcome(
            exception_id="exc_test_015",
            resolved_at=datetime.utcnow(),
            resolution_time_hours=3.0,
            resolved_within_sla=True,
            routing_was_correct=True
        )
        handler.update_with_resolution("exc_test_015", outcome)
        
        # Episode should be removed from pending
        assert "exc_test_015" not in handler.pending_episodes
        
        # Replay buffer should have the episode
        assert len(handler.replay_buffer) > 0
    
    def test_get_statistics(self):
        """Test getting statistics."""
        handler = RLExceptionHandler()
        stats = handler.get_statistics()
        
        assert "q_table_size" in stats
        assert "replay_buffer_size" in stats
        assert "learning_rate" in stats


class TestIntegration:
    """Integration tests for complete workflow."""
    
    def test_complete_exception_workflow(self):
        """Test complete exception handling workflow."""
        # 1. Create exception
        exception = ExceptionRecord(
            exception_id="exc_test_016",
            exception_type=ExceptionType.MATCHING_EXCEPTION,
            event_type="MATCHING_EXCEPTION",
            agent_id="trade_matching_agent",
            reason_codes=[ReasonCodeTaxonomy.NOTIONAL_MISMATCH],
            error_message="Notional mismatch detected",
            match_score=0.65,
            trade_id="GCS382857"
        )
        
        # 2. Classify
        classification = classify_exception(exception)
        assert classification is not None
        
        # 3. Score
        severity_score = compute_severity_score(exception)
        assert 0.0 <= severity_score <= 1.0
        
        # 4. Triage
        triage_result = triage_exception(exception, severity_score)
        assert triage_result is not None
        assert triage_result.severity is not None
        assert triage_result.routing is not None
        
        # 5. RL recording
        rl_handler = RLExceptionHandler()
        rl_handler.record_episode(
            exception.exception_id,
            exception.to_state_vector(),
            triage_result.routing.value,
            {}
        )
        assert exception.exception_id in rl_handler.pending_episodes
        
        # 6. Resolution update
        outcome = ResolutionOutcome(
            exception_id=exception.exception_id,
            resolved_at=datetime.utcnow(),
            resolution_time_hours=2.5,
            resolved_within_sla=True,
            routing_was_correct=True
        )
        rl_handler.update_with_resolution(exception.exception_id, outcome)
        assert exception.exception_id not in rl_handler.pending_episodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
