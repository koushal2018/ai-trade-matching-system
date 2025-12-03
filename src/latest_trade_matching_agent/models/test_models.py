"""
Test suite for data models.

This test file validates that all models work correctly with proper
validation, serialization, and business logic.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from models.adapter import CanonicalAdapterOutput
from models.trade import CanonicalTradeModel
from models.matching import MatchingResult, MatchClassification, DecisionStatus, FieldDifference
from models.exception import ExceptionRecord, TriageResult, SeverityLevel, RoutingDestination, TriageClassification, ExceptionType
from models.audit import AuditRecord, ActionType, ActionOutcome
from models.events import StandardEventMessage, EventTaxonomy, EventFactory


def test_canonical_adapter_output():
    """Test CanonicalAdapterOutput model."""
    print("Testing CanonicalAdapterOutput...")
    
    # Test PDF adapter output
    pdf_output = CanonicalAdapterOutput(
        adapter_type="PDF",
        document_id="doc_123",
        source_type="BANK",
        extracted_text="Trade confirmation text...",
        metadata={
            "page_count": 3,
            "dpi": 300,
            "ocr_confidence": 0.95
        },
        s3_location="s3://bucket/extracted/BANK/doc_123.json",
        correlation_id="corr_abc"
    )
    
    assert pdf_output.adapter_type == "PDF"
    assert pdf_output.metadata["dpi"] == 300
    print("✓ PDF adapter output validated")
    
    # Test validation - DPI must be 300
    try:
        bad_output = CanonicalAdapterOutput(
            adapter_type="PDF",
            document_id="doc_456",
            source_type="COUNTERPARTY",
            extracted_text="Text...",
            metadata={"page_count": 2, "dpi": 200},  # Wrong DPI
            s3_location="s3://bucket/test.json"
        )
        assert False, "Should have raised validation error for wrong DPI"
    except ValueError as e:
        assert "300 DPI" in str(e)
        print("✓ DPI validation works correctly")


def test_canonical_trade_model():
    """Test CanonicalTradeModel."""
    print("\nTesting CanonicalTradeModel...")
    
    trade = CanonicalTradeModel(
        Trade_ID="GCS382857",
        TRADE_SOURCE="COUNTERPARTY",
        trade_date="2024-10-15",
        notional=1000000.00,
        currency="USD",
        counterparty="Goldman Sachs",
        product_type="SWAP",
        effective_date="2024-10-17",
        maturity_date="2025-10-17",
        commodity_type="CRUDE_OIL"
    )
    
    assert trade.Trade_ID == "GCS382857"
    assert trade.TRADE_SOURCE == "COUNTERPARTY"
    assert trade.currency == "USD"
    print("✓ Trade model created successfully")
    
    # Test DynamoDB conversion
    dynamodb_format = trade.to_dynamodb_format()
    assert dynamodb_format["Trade_ID"]["S"] == "GCS382857"
    assert dynamodb_format["notional"]["N"] == "1000000.0"
    assert dynamodb_format["TRADE_SOURCE"]["S"] == "COUNTERPARTY"
    print("✓ DynamoDB format conversion works")
    
    # Test round-trip conversion
    trade_back = CanonicalTradeModel.from_dynamodb_format(dynamodb_format)
    assert trade_back.Trade_ID == trade.Trade_ID
    assert trade_back.notional == trade.notional
    print("✓ Round-trip DynamoDB conversion works")


def test_matching_result():
    """Test MatchingResult model."""
    print("\nTesting MatchingResult...")
    
    # Test AUTO_MATCH scenario
    match_result = MatchingResult(
        trade_id="GCS382857",
        classification=MatchClassification.MATCHED,
        match_score=0.95,
        decision_status=DecisionStatus.AUTO_MATCH,
        reason_codes=[],
        differences=[],
        requires_hitl=False
    )
    
    assert match_result.decision_status == DecisionStatus.AUTO_MATCH
    assert not match_result.requires_hitl
    print("✓ AUTO_MATCH result validated")
    
    # Test ESCALATE scenario
    escalate_result = MatchingResult(
        trade_id="FAB26933659",
        classification=MatchClassification.PROBABLE_MATCH,
        match_score=0.78,
        decision_status=DecisionStatus.ESCALATE,
        reason_codes=["DATE_MISMATCH"],
        differences=[
            FieldDifference(
                field_name="trade_date",
                bank_value="2024-10-16",
                counterparty_value="2024-10-17",
                difference_type="TOLERANCE_EXCEEDED",
                tolerance_applied=True,
                within_tolerance=True
            )
        ],
        requires_hitl=True
    )
    
    assert escalate_result.decision_status == DecisionStatus.ESCALATE
    assert escalate_result.requires_hitl
    assert len(escalate_result.differences) == 1
    print("✓ ESCALATE result validated")
    
    # Test summary
    summary = match_result.get_summary()
    assert "GCS382857" in summary
    assert "0.95" in summary
    print("✓ Summary generation works")


def test_exception_record():
    """Test ExceptionRecord model."""
    print("\nTesting ExceptionRecord...")
    
    exception = ExceptionRecord(
        exception_id="exc_123",
        exception_type=ExceptionType.MATCHING_EXCEPTION,
        event_type="MATCHING_EXCEPTION",
        trade_id="GCS382857",
        agent_id="trade_matching_agent",
        match_score=0.45,
        reason_codes=["NOTIONAL_MISMATCH", "DATE_MISMATCH"],
        error_message="Trade matching failed due to significant mismatches",
        context={"notional_diff": 50000, "date_diff_days": 2},
        correlation_id="corr_abc"
    )
    
    assert exception.exception_type == ExceptionType.MATCHING_EXCEPTION
    assert len(exception.reason_codes) == 2
    print("✓ Exception record created")
    
    # Test state vector for RL
    state_vector = exception.to_state_vector()
    assert state_vector["exception_type"] == "MATCHING_EXCEPTION"
    assert state_vector["match_score"] == 0.45
    print("✓ State vector generation works")


def test_triage_result():
    """Test TriageResult model."""
    print("\nTesting TriageResult...")
    
    triage = TriageResult(
        exception_id="exc_123",
        severity=SeverityLevel.HIGH,
        severity_score=0.75,
        routing=RoutingDestination.OPS_DESK,
        priority=2,
        sla_hours=4,
        classification=TriageClassification.OPERATIONAL_ISSUE,
        recommended_action="Review and correct notional mismatch"
    )
    
    assert triage.severity == SeverityLevel.HIGH
    assert triage.routing == RoutingDestination.OPS_DESK
    assert triage.priority == 2
    print("✓ Triage result validated")
    
    # Test validation - severity must match score
    try:
        bad_triage = TriageResult(
            exception_id="exc_456",
            severity=SeverityLevel.LOW,  # Wrong severity for score
            severity_score=0.85,  # Should be CRITICAL
            routing=RoutingDestination.AUTO_RESOLVE,
            priority=1,
            sla_hours=24,
            classification=TriageClassification.AUTO_RESOLVABLE
        )
        assert False, "Should have raised validation error"
    except ValueError as e:
        assert "CRITICAL" in str(e)
        print("✓ Severity validation works")


def test_audit_record():
    """Test AuditRecord model."""
    print("\nTesting AuditRecord...")
    
    audit = AuditRecord(
        record_id="audit_001",
        agent_id="pdf_adapter_agent",
        action_type=ActionType.PDF_PROCESSED,
        resource_id="doc_456",
        outcome=ActionOutcome.SUCCESS,
        details={
            "page_count": 5,
            "processing_time_ms": 8500,
            "dpi": 300
        },
        correlation_id="corr_abc"
    )
    
    # Finalize to compute hash
    audit.finalize()
    
    assert audit.immutable_hash != ""
    assert len(audit.immutable_hash) == 64  # SHA-256 produces 64 hex chars
    print("✓ Audit record created with hash")
    
    # Test hash verification
    assert audit.verify_hash()
    print("✓ Hash verification works")
    
    # Test tamper detection
    audit.details["tampered"] = True
    assert not audit.verify_hash()
    print("✓ Tamper detection works")
    
    # Test export formats
    json_export = audit.to_json()
    assert "audit_001" in json_export
    print("✓ JSON export works")
    
    csv_row = audit.to_csv_row()
    assert len(csv_row) == 11
    print("✓ CSV export works")
    
    xml_export = audit.to_xml()
    assert "<AuditRecord>" in xml_export
    print("✓ XML export works")


def test_standard_event_message():
    """Test StandardEventMessage model."""
    print("\nTesting StandardEventMessage...")
    
    event = StandardEventMessage(
        event_id="evt_123",
        event_type=EventTaxonomy.PDF_PROCESSED,
        source_agent="pdf_adapter_agent",
        correlation_id="corr_abc",
        payload={
            "document_id": "doc_456",
            "canonical_output_location": "s3://bucket/extracted/doc_456.json",
            "page_count": 5
        },
        metadata={
            "dpi": 300,
            "ocr_confidence": 0.95
        }
    )
    
    assert event.event_type == EventTaxonomy.PDF_PROCESSED
    assert event.payload["page_count"] == 5
    print("✓ Event message created")
    
    # Test SQS serialization
    sqs_message = event.to_sqs_message()
    assert "evt_123" in sqs_message
    print("✓ SQS serialization works")
    
    # Test SQS deserialization
    event_back = StandardEventMessage.from_sqs_message(sqs_message)
    assert event_back.event_id == event.event_id
    assert event_back.correlation_id == event.correlation_id
    print("✓ SQS deserialization works")
    
    # Test event validation
    try:
        bad_event = StandardEventMessage(
            event_id="evt_456",
            event_type="INVALID_EVENT",  # Not in taxonomy
            source_agent="test_agent",
            correlation_id="corr_def",
            payload={}
        )
        assert False, "Should have raised validation error"
    except ValueError as e:
        assert "Invalid event_type" in str(e)
        print("✓ Event type validation works")


def test_event_factory():
    """Test EventFactory."""
    print("\nTesting EventFactory...")
    
    # Test creating specific event types
    pdf_event = EventFactory.create_event(
        event_type=EventTaxonomy.PDF_PROCESSED,
        event_id="evt_789",
        source_agent="pdf_adapter_agent",
        correlation_id="corr_xyz",
        payload={"document_id": "doc_789"}
    )
    
    assert pdf_event.event_type == EventTaxonomy.PDF_PROCESSED
    print("✓ Event factory creates events")
    
    # Test from SQS message
    sqs_body = pdf_event.to_sqs_message()
    event_back = EventFactory.from_sqs_message(sqs_body)
    assert event_back.event_id == "evt_789"
    print("✓ Event factory deserializes from SQS")


def run_all_tests():
    """Run all model tests."""
    print("=" * 60)
    print("Running Data Model Tests")
    print("=" * 60)
    
    test_canonical_adapter_output()
    test_canonical_trade_model()
    test_matching_result()
    test_exception_record()
    test_triage_result()
    test_audit_record()
    test_standard_event_message()
    test_event_factory()
    
    print("\n" + "=" * 60)
    print("✓ All tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
