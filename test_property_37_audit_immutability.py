#!/usr/bin/env python3
"""
Property Test for Property 37: Audit records are immutable

**Feature: agentcore-migration, Property 37: Audit records are immutable**
**Validates: Requirements 10.4**
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import json
import hashlib
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

# Import the audit models
from src.latest_trade_matching_agent.models.audit import (
    AuditRecord, ActionType, ActionOutcome
)


@composite
def audit_record_strategy(draw):
    """Generate test audit records with random but valid data."""
    
    # Generate random but realistic data
    record_id = f"audit_{draw(st.integers(min_value=1000, max_value=9999))}"
    
    # Generate timestamp within reasonable range (last 30 days)
    base_time = datetime.utcnow()
    time_offset = draw(st.integers(min_value=0, max_value=30*24*3600))  # 30 days in seconds
    timestamp = base_time - timedelta(seconds=time_offset)
    
    agent_id = draw(st.sampled_from([
        "pdf_adapter_agent", "trade_extraction_agent", "trade_matching_agent",
        "exception_management_agent", "orchestrator_agent", "web_portal"
    ]))
    
    action_type = draw(st.sampled_from(list(ActionType)))
    outcome = draw(st.sampled_from(list(ActionOutcome)))
    
    # Optional fields
    resource_id = draw(st.one_of(
        st.none(),
        st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
    ))
    
    user_id = draw(st.one_of(
        st.none(),
        st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    ))
    
    correlation_id = draw(st.one_of(
        st.none(),
        st.text(min_size=8, max_size=16, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    ))
    
    previous_hash = draw(st.one_of(
        st.none(),
        st.text(min_size=64, max_size=64, alphabet='0123456789abcdef')  # Valid hex hash
    ))
    
    # Generate realistic details dictionary
    details_options = [
        {},
        {"page_count": draw(st.integers(min_value=1, max_value=50))},
        {"processing_time_ms": draw(st.integers(min_value=100, max_value=30000))},
        {"match_score": draw(st.floats(min_value=0.0, max_value=1.0))},
        {"error_code": draw(st.text(min_size=3, max_size=10))},
        {
            "page_count": draw(st.integers(min_value=1, max_value=50)),
            "dpi": 300,
            "processing_time_ms": draw(st.integers(min_value=100, max_value=30000))
        }
    ]
    details = draw(st.sampled_from(details_options))
    
    return {
        "record_id": record_id,
        "timestamp": timestamp,
        "agent_id": agent_id,
        "action_type": action_type,
        "resource_id": resource_id,
        "outcome": outcome,
        "user_id": user_id,
        "details": details,
        "previous_hash": previous_hash,
        "correlation_id": correlation_id
    }


def test_property_37_audit_records_are_immutable():
    """
    **Feature: agentcore-migration, Property 37: Audit records are immutable**
    **Validates: Requirements 10.4**
    
    Property: For any audit record, its immutable_hash should be SHA-256 of the record fields,
    and any modification should be detectable by hash mismatch.
    
    This test verifies:
    1. Hash computation is deterministic and correct
    2. Hash verification works for unmodified records
    3. Any field modification is detected by hash mismatch
    4. Hash computation is consistent across multiple calls
    """
    print("Running Property 37: Audit records are immutable")
    print("Testing 100 random audit records...")
    
    success_count = 0
    
    for i in range(100):
        try:
            # Generate random audit record data
            from hypothesis import strategies as st
            audit_data = audit_record_strategy().example()
            
            # Create audit record (without hash initially)
            audit = AuditRecord(**audit_data)
            
            # Test 1: Hash computation should be deterministic
            hash1 = audit.compute_hash()
            hash2 = audit.compute_hash()
            assert hash1 == hash2, f"Hash computation not deterministic: {hash1} != {hash2}"
            
            # Test 2: Hash should be valid SHA-256 (64 hex characters)
            assert len(hash1) == 64, f"Hash length incorrect: {len(hash1)} != 64"
            assert all(c in '0123456789abcdef' for c in hash1), f"Hash contains invalid characters: {hash1}"
            
            # Test 3: Finalize should set the hash correctly
            audit.finalize()
            assert audit.immutable_hash == hash1, f"Finalize didn't set hash correctly"
            
            # Test 4: Verification should pass for unmodified record
            assert audit.verify_hash(), f"Hash verification failed for unmodified record"
            
            # Test 5: Modification detection - modify each field and verify detection
            original_audit = AuditRecord(**audit_data)
            original_audit.finalize()
            
            # Test modification of record_id
            modified_audit = AuditRecord(**audit_data)
            modified_audit.record_id = "modified_id"
            modified_audit.immutable_hash = original_audit.immutable_hash  # Use original hash
            assert not modified_audit.verify_hash(), f"Failed to detect record_id modification"
            
            # Test modification of agent_id
            modified_audit = AuditRecord(**audit_data)
            modified_audit.agent_id = "modified_agent"
            modified_audit.immutable_hash = original_audit.immutable_hash
            assert not modified_audit.verify_hash(), f"Failed to detect agent_id modification"
            
            # Test modification of action_type
            modified_audit = AuditRecord(**audit_data)
            modified_audit.action_type = ActionType.SYSTEM_ALERT if audit.action_type != ActionType.SYSTEM_ALERT else ActionType.USER_LOGIN
            modified_audit.immutable_hash = original_audit.immutable_hash
            assert not modified_audit.verify_hash(), f"Failed to detect action_type modification"
            
            # Test modification of outcome
            modified_audit = AuditRecord(**audit_data)
            modified_audit.outcome = ActionOutcome.FAILURE if audit.outcome != ActionOutcome.FAILURE else ActionOutcome.SUCCESS
            modified_audit.immutable_hash = original_audit.immutable_hash
            assert not modified_audit.verify_hash(), f"Failed to detect outcome modification"
            
            # Test modification of details
            modified_audit = AuditRecord(**audit_data)
            modified_audit.details = {"tampered": True}
            modified_audit.immutable_hash = original_audit.immutable_hash
            assert not modified_audit.verify_hash(), f"Failed to detect details modification"
            
            # Test modification of timestamp
            modified_audit = AuditRecord(**audit_data)
            modified_audit.timestamp = datetime.utcnow()
            modified_audit.immutable_hash = original_audit.immutable_hash
            assert not modified_audit.verify_hash(), f"Failed to detect timestamp modification"
            
            # Test 6: Hash should be different for different records
            other_data = audit_record_strategy().example()
            other_audit = AuditRecord(**other_data)
            other_hash = other_audit.compute_hash()
            
            # Only assert different if the records are actually different
            if audit_data != other_data:
                assert hash1 != other_hash, f"Different records produced same hash"
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ Test case {i+1} failed: {e}")
            raise
    
    print(f"✅ All {success_count} test cases passed!")
    return True


@settings(max_examples=50, deadline=30000)
@given(audit_record_strategy())
def test_property_37_hypothesis(audit_data):
    """
    **Feature: agentcore-migration, Property 37: Audit records are immutable**
    **Validates: Requirements 10.4**
    
    Hypothesis-based test for audit record immutability with random inputs.
    """
    # Create audit record
    audit = AuditRecord(**audit_data)
    
    # Hash computation should be deterministic
    hash1 = audit.compute_hash()
    hash2 = audit.compute_hash()
    assert hash1 == hash2, "Hash computation not deterministic"
    
    # Hash should be valid SHA-256
    assert len(hash1) == 64, f"Hash length incorrect: {len(hash1)}"
    assert all(c in '0123456789abcdef' for c in hash1), f"Hash contains invalid characters"
    
    # Finalize and verify
    audit.finalize()
    assert audit.verify_hash(), "Hash verification failed for unmodified record"
    
    # Test tamper detection by modifying details
    original_hash = audit.immutable_hash
    audit.details = {"tampered": True}
    assert not audit.verify_hash(), "Failed to detect tampering"
    
    # Restore and verify again
    audit.details = audit_data["details"]
    audit.immutable_hash = original_hash
    assert audit.verify_hash(), "Hash verification failed after restoration"


def test_hash_computation_correctness():
    """
    Test that hash computation follows the expected algorithm.
    
    This ensures the hash is computed correctly according to the specification.
    """
    print("Testing hash computation correctness...")
    
    # Create a known audit record
    audit = AuditRecord(
        record_id="test_001",
        timestamp=datetime(2025, 1, 15, 10, 30, 0),
        agent_id="test_agent",
        action_type=ActionType.PDF_PROCESSED,
        resource_id="doc_123",
        outcome=ActionOutcome.SUCCESS,
        user_id="user_456",
        details={"test": "value"},
        previous_hash="abcd1234",
        correlation_id="corr_789"
    )
    
    # Compute expected hash manually
    hash_data = {
        "record_id": "test_001",
        "timestamp": "2025-01-15T10:30:00",
        "agent_id": "test_agent",
        "action_type": "PDF_PROCESSED",
        "resource_id": "doc_123",
        "outcome": "SUCCESS",
        "user_id": "user_456",
        "details": {"test": "value"},
        "previous_hash": "abcd1234",
        "correlation_id": "corr_789",
    }
    
    json_str = json.dumps(hash_data, sort_keys=True, default=str)
    expected_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    # Compare with audit record's computed hash
    computed_hash = audit.compute_hash()
    assert computed_hash == expected_hash, f"Hash computation incorrect: {computed_hash} != {expected_hash}"
    
    print("✅ Hash computation correctness verified")


def test_blockchain_style_linking():
    """
    Test that audit records can be linked in blockchain style using previous_hash.
    
    This ensures the integrity of the audit trail chain.
    """
    print("Testing blockchain-style linking...")
    
    # Create first audit record
    audit1 = AuditRecord(
        record_id="audit_001",
        agent_id="test_agent",
        action_type=ActionType.PDF_PROCESSED,
        outcome=ActionOutcome.SUCCESS,
        details={"step": 1}
    )
    audit1.finalize()
    
    # Create second audit record linked to first
    audit2 = AuditRecord(
        record_id="audit_002",
        agent_id="test_agent",
        action_type=ActionType.TRADE_EXTRACTED,
        outcome=ActionOutcome.SUCCESS,
        details={"step": 2},
        previous_hash=audit1.immutable_hash
    )
    audit2.finalize()
    
    # Verify both records are valid
    assert audit1.verify_hash(), "First audit record hash invalid"
    assert audit2.verify_hash(), "Second audit record hash invalid"
    
    # Verify linking
    assert audit2.previous_hash == audit1.immutable_hash, "Blockchain linking broken"
    
    # Test that breaking the chain is detectable
    audit2.previous_hash = "tampered_hash"
    assert not audit2.verify_hash(), "Failed to detect broken chain"
    
    print("✅ Blockchain-style linking verified")


def main():
    """Run all property tests for audit trail immutability."""
    print("=" * 80)
    print("Property-Based Test for Audit Trail Immutability")
    print("Property 37: Audit records are immutable")
    print("Validates: Requirements 10.4")
    print("=" * 80)
    
    all_passed = True
    
    # Run main property test
    try:
        if not test_property_37_audit_records_are_immutable():
            all_passed = False
    except Exception as e:
        print(f"❌ Property test failed: {e}")
        all_passed = False
    
    # Run hash computation correctness test
    try:
        test_hash_computation_correctness()
    except Exception as e:
        print(f"❌ Hash computation test failed: {e}")
        all_passed = False
    
    # Run blockchain linking test
    try:
        test_blockchain_style_linking()
    except Exception as e:
        print(f"❌ Blockchain linking test failed: {e}")
        all_passed = False
    
    # Run hypothesis test
    try:
        test_property_37_hypothesis()
        print("✅ Hypothesis-based testing passed!")
    except Exception as e:
        print(f"❌ Hypothesis testing failed: {e}")
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL PROPERTY TESTS PASSED!")
        print("🎯 Property 37: Audit records are immutable - VALIDATED")
        print("📋 Requirements 10.4: Ensure immutability and tamper-evidence - SATISFIED")
        print("✅ The audit trail correctly maintains immutability and detects tampering")
    else:
        print("❌ SOME PROPERTY TESTS FAILED!")
        print("🚨 Property 37 validation incomplete")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)