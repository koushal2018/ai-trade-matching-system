"""
Property-based tests for S3 Event Processor.

Feature: s3-event-automation
Tests correctness properties defined in the design document.
"""

import sys
import re
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import pytest

# Add deployment path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "deployment" / "s3_event_processor"))

from s3_event_processor import (
    generate_correlation_id,
    extract_document_id,
    infer_source_type,
    is_pdf_file,
    parse_s3_event,
)
from models import EventPayload, ValidationError


# =============================================================================
# Strategies for generating test data
# =============================================================================

# Strategy for valid PDF filenames (alphanumeric with underscores)
pdf_filename_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=100
).map(lambda s: s + ".pdf")

# Strategy for non-PDF filenames
non_pdf_extension_strategy = st.sampled_from([
    ".txt", ".doc", ".docx", ".xlsx", ".csv", ".json", ".xml", ".png", ".jpg", ""
])

non_pdf_filename_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=100
).flatmap(lambda name: non_pdf_extension_strategy.map(lambda ext: name + ext))

# Strategy for source types
source_type_strategy = st.sampled_from(["BANK", "COUNTERPARTY"])

# Strategy for valid S3 keys with PDF files
valid_s3_key_strategy = st.tuples(
    source_type_strategy,
    pdf_filename_strategy
).map(lambda t: f"{t[0]}/{t[1]}")

# Strategy for correlation IDs
correlation_id_strategy = st.text(
    alphabet="0123456789abcdef",
    min_size=12,
    max_size=12
).map(lambda hex_str: f"corr_{hex_str}")


# =============================================================================
# Property 1: Source Type Inference Correctness
# =============================================================================

@given(
    source_type=source_type_strategy,
    filename=pdf_filename_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_1_source_type_inference_correctness(source_type: str, filename: str):
    """
    **Feature: s3-event-automation, Property 1: Source Type Inference Correctness**
    **Validates: Requirements 1.1, 1.2**
    
    For any S3 event with a key path, if the path starts with BANK/ then the 
    resulting message source_type SHALL be "BANK", and if the path starts with 
    COUNTERPARTY/ then the resulting message source_type SHALL be "COUNTERPARTY".
    """
    s3_key = f"{source_type}/{filename}"
    
    inferred_type = infer_source_type(s3_key)
    
    assert inferred_type == source_type, \
        f"Expected source_type '{source_type}' for key '{s3_key}', got '{inferred_type}'"


@given(
    prefix=st.text(min_size=1, max_size=20).filter(
        lambda s: s not in ["BANK", "COUNTERPARTY"] and "/" not in s
    ),
    filename=pdf_filename_strategy
)
@settings(max_examples=50, deadline=None)
def test_property_1_unknown_source_type_returns_none(prefix: str, filename: str):
    """
    **Feature: s3-event-automation, Property 1: Source Type Inference Correctness**
    **Validates: Requirements 1.1, 1.2**
    
    For any S3 key that doesn't start with BANK/ or COUNTERPARTY/, 
    infer_source_type should return None.
    """
    s3_key = f"{prefix}/{filename}"
    
    inferred_type = infer_source_type(s3_key)
    
    assert inferred_type is None, \
        f"Expected None for unknown prefix '{prefix}', got '{inferred_type}'"


# =============================================================================
# Property 3: Non-PDF Filtering
# =============================================================================

@given(
    source_type=source_type_strategy,
    filename=non_pdf_filename_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_3_non_pdf_filtering(source_type: str, filename: str):
    """
    **Feature: s3-event-automation, Property 3: Non-PDF Filtering**
    **Validates: Requirements 1.4**
    
    For any S3 event where the object key does not end with .pdf (case-insensitive),
    the S3_Event_Processor SHALL return None (no message produced).
    """
    # Ensure filename doesn't end with .pdf
    assume(not filename.lower().endswith(".pdf"))
    
    s3_key = f"{source_type}/{filename}"
    
    result = is_pdf_file(s3_key)
    
    assert result is False, \
        f"Expected is_pdf_file to return False for '{s3_key}', got {result}"


@given(
    source_type=source_type_strategy,
    filename=pdf_filename_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_3_pdf_files_accepted(source_type: str, filename: str):
    """
    **Feature: s3-event-automation, Property 3: Non-PDF Filtering**
    **Validates: Requirements 1.4**
    
    For any S3 event where the object key ends with .pdf,
    is_pdf_file should return True.
    """
    s3_key = f"{source_type}/{filename}"
    
    result = is_pdf_file(s3_key)
    
    assert result is True, \
        f"Expected is_pdf_file to return True for '{s3_key}', got {result}"


@given(
    source_type=source_type_strategy,
    base_name=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
        min_size=1,
        max_size=50
    )
)
@settings(max_examples=50, deadline=None)
def test_property_3_pdf_case_insensitive(source_type: str, base_name: str):
    """
    **Feature: s3-event-automation, Property 3: Non-PDF Filtering**
    **Validates: Requirements 1.4**
    
    PDF extension check should be case-insensitive.
    """
    # Test various case combinations
    extensions = [".pdf", ".PDF", ".Pdf", ".pDf"]
    
    for ext in extensions:
        s3_key = f"{source_type}/{base_name}{ext}"
        result = is_pdf_file(s3_key)
        assert result is True, \
            f"Expected is_pdf_file to return True for '{s3_key}' (case-insensitive), got {result}"



# =============================================================================
# Property 5: Correlation ID Format
# =============================================================================

@settings(max_examples=100, deadline=None)
@given(st.integers())  # Just to run multiple times
def test_property_5_correlation_id_format(seed: int):
    """
    **Feature: s3-event-automation, Property 5: Correlation ID Format**
    **Validates: Requirements 4.1**
    
    For any processed S3 event, the generated correlation_id SHALL match 
    the regex pattern ^corr_[a-f0-9]{12}$.
    """
    correlation_id = generate_correlation_id()
    
    pattern = r"^corr_[a-f0-9]{12}$"
    
    assert re.match(pattern, correlation_id), \
        f"Correlation ID '{correlation_id}' does not match pattern '{pattern}'"


@settings(max_examples=50, deadline=None)
@given(st.integers())
def test_property_5_correlation_id_uniqueness(seed: int):
    """
    **Feature: s3-event-automation, Property 5: Correlation ID Format**
    **Validates: Requirements 4.1**
    
    Each generated correlation_id should be unique.
    """
    # Generate multiple correlation IDs
    ids = [generate_correlation_id() for _ in range(10)]
    
    # All should be unique
    assert len(ids) == len(set(ids)), \
        f"Generated duplicate correlation IDs: {ids}"


# =============================================================================
# Property 4: Invalid Event Robustness
# =============================================================================

@given(
    missing_field=st.sampled_from(["bucket", "object", "key", "s3", "Records"])
)
@settings(max_examples=50, deadline=None)
def test_property_4_invalid_event_robustness(missing_field: str):
    """
    **Feature: s3-event-automation, Property 4: Invalid Event Robustness**
    **Validates: Requirements 2.2**
    
    For any malformed S3 event (missing Records, missing s3 object, missing key fields),
    the S3_Event_Processor SHALL not raise an exception and SHALL return None.
    """
    # Build a valid record first
    valid_record = {
        "eventSource": "aws:s3",
        "eventTime": "2024-01-15T10:30:00.000Z",
        "eventName": "ObjectCreated:Put",
        "s3": {
            "bucket": {"name": "test-bucket"},
            "object": {
                "key": "BANK/test.pdf",
                "size": 12345
            }
        }
    }
    
    # Remove the specified field to make it invalid
    if missing_field == "bucket":
        del valid_record["s3"]["bucket"]
    elif missing_field == "object":
        del valid_record["s3"]["object"]
    elif missing_field == "key":
        del valid_record["s3"]["object"]["key"]
    elif missing_field == "s3":
        del valid_record["s3"]
    elif missing_field == "Records":
        # Test with empty record
        valid_record = {}
    
    # Should not raise an exception
    try:
        result = parse_s3_event(valid_record)
        # Result should be None for invalid events
        if missing_field in ["bucket", "key", "s3"]:
            assert result is None, \
                f"Expected None for record missing '{missing_field}', got {result}"
    except Exception as e:
        pytest.fail(f"parse_s3_event raised exception for missing '{missing_field}': {e}")


@given(
    random_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.text(min_size=0, max_size=20),
        max_size=5
    )
)
@settings(max_examples=50, deadline=None)
def test_property_4_random_malformed_events(random_data: dict):
    """
    **Feature: s3-event-automation, Property 4: Invalid Event Robustness**
    **Validates: Requirements 2.2**
    
    For any random malformed data, parse_s3_event should not raise an exception.
    """
    try:
        result = parse_s3_event(random_data)
        # Result should be None for invalid events
        assert result is None, \
            f"Expected None for random malformed data, got {result}"
    except Exception as e:
        pytest.fail(f"parse_s3_event raised exception for random data: {e}")


# =============================================================================
# Property 7: Event Payload Round-Trip Serialization
# =============================================================================

@given(
    document_id=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
        min_size=1,
        max_size=50
    ),
    source_type=source_type_strategy,
    correlation_id=correlation_id_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_7_payload_round_trip_serialization(
    document_id: str, source_type: str, correlation_id: str
):
    """
    **Feature: s3-event-automation, Property 7: Event Payload Round-Trip Serialization**
    **Validates: Requirements 6.1**
    
    For any valid EventPayload object, serializing to JSON and then 
    deserializing SHALL produce an equivalent object.
    """
    document_path = f"s3://test-bucket/{source_type}/{document_id}.pdf"
    
    original = EventPayload(
        document_path=document_path,
        source_type=source_type,
        document_id=document_id,
        correlation_id=correlation_id
    )
    
    # Serialize to JSON
    json_str = original.to_json()
    
    # Deserialize back
    restored = EventPayload.from_json(json_str)
    
    # Should be equivalent
    assert original == restored, \
        f"Round-trip failed: original={original}, restored={restored}"


@given(
    document_id=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
        min_size=1,
        max_size=50
    ),
    source_type=source_type_strategy,
    correlation_id=correlation_id_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_7_payload_dict_round_trip(
    document_id: str, source_type: str, correlation_id: str
):
    """
    **Feature: s3-event-automation, Property 7: Event Payload Round-Trip Serialization**
    **Validates: Requirements 6.1**
    
    For any valid EventPayload object, converting to dict and back 
    SHALL produce an equivalent object.
    """
    document_path = f"s3://test-bucket/{source_type}/{document_id}.pdf"
    
    original = EventPayload(
        document_path=document_path,
        source_type=source_type,
        document_id=document_id,
        correlation_id=correlation_id
    )
    
    # Convert to dict
    data = original.to_dict()
    
    # Convert back
    restored = EventPayload.from_dict(data)
    
    # Should be equivalent
    assert original == restored, \
        f"Dict round-trip failed: original={original}, restored={restored}"



# =============================================================================
# Property 8: Validation Rejects Incomplete Payloads
# =============================================================================

@given(
    missing_field=st.sampled_from(["document_path", "source_type", "document_id", "correlation_id"])
)
@settings(max_examples=50, deadline=None)
def test_property_8_validation_rejects_missing_fields(missing_field: str):
    """
    **Feature: s3-event-automation, Property 8: Validation Rejects Incomplete Payloads**
    **Validates: Requirements 6.2**
    
    For any EventPayload with one or more required fields missing or None,
    validation SHALL fail before serialization.
    """
    # Build a valid payload first
    valid_data = {
        "document_path": "s3://test-bucket/BANK/test.pdf",
        "source_type": "BANK",
        "document_id": "test_doc",
        "correlation_id": "corr_abc123def456"
    }
    
    # Set the specified field to empty string
    valid_data[missing_field] = ""
    
    payload = EventPayload(**valid_data)
    
    # Validation should fail
    with pytest.raises(ValidationError):
        payload.validate()


@given(
    invalid_source_type=st.text(min_size=1, max_size=20).filter(
        lambda s: s not in ["BANK", "COUNTERPARTY"]
    )
)
@settings(max_examples=50, deadline=None)
def test_property_8_validation_rejects_invalid_source_type(invalid_source_type: str):
    """
    **Feature: s3-event-automation, Property 8: Validation Rejects Incomplete Payloads**
    **Validates: Requirements 6.2**
    
    For any EventPayload with invalid source_type, validation SHALL fail.
    """
    payload = EventPayload(
        document_path="s3://test-bucket/BANK/test.pdf",
        source_type=invalid_source_type,
        document_id="test_doc",
        correlation_id="corr_abc123def456"
    )
    
    with pytest.raises(ValidationError):
        payload.validate()


@given(
    invalid_correlation_id=st.text(min_size=1, max_size=30).filter(
        lambda s: not re.match(r"^corr_[a-f0-9]{12}$", s)
    )
)
@settings(max_examples=50, deadline=None)
def test_property_8_validation_rejects_invalid_correlation_id(invalid_correlation_id: str):
    """
    **Feature: s3-event-automation, Property 8: Validation Rejects Incomplete Payloads**
    **Validates: Requirements 6.2**
    
    For any EventPayload with invalid correlation_id format, validation SHALL fail.
    """
    payload = EventPayload(
        document_path="s3://test-bucket/BANK/test.pdf",
        source_type="BANK",
        document_id="test_doc",
        correlation_id=invalid_correlation_id
    )
    
    with pytest.raises(ValidationError):
        payload.validate()


@given(
    invalid_document_path=st.text(min_size=1, max_size=50).filter(
        lambda s: not s.startswith("s3://")
    )
)
@settings(max_examples=50, deadline=None)
def test_property_8_validation_rejects_invalid_document_path(invalid_document_path: str):
    """
    **Feature: s3-event-automation, Property 8: Validation Rejects Incomplete Payloads**
    **Validates: Requirements 6.2**
    
    For any EventPayload with invalid document_path (not S3 URI), validation SHALL fail.
    """
    payload = EventPayload(
        document_path=invalid_document_path,
        source_type="BANK",
        document_id="test_doc",
        correlation_id="corr_abc123def456"
    )
    
    with pytest.raises(ValidationError):
        payload.validate()


@given(
    document_id=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
        min_size=1,
        max_size=50
    ),
    source_type=source_type_strategy,
    correlation_id=correlation_id_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_8_valid_payload_passes_validation(
    document_id: str, source_type: str, correlation_id: str
):
    """
    **Feature: s3-event-automation, Property 8: Validation Rejects Incomplete Payloads**
    **Validates: Requirements 6.2**
    
    For any valid EventPayload, validation SHALL pass.
    """
    document_path = f"s3://test-bucket/{source_type}/{document_id}.pdf"
    
    payload = EventPayload(
        document_path=document_path,
        source_type=source_type,
        document_id=document_id,
        correlation_id=correlation_id
    )
    
    # Should not raise
    payload.validate()


# =============================================================================
# Additional helper tests for document_id extraction
# =============================================================================

@given(
    source_type=source_type_strategy,
    document_id=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
        min_size=1,
        max_size=50
    )
)
@settings(max_examples=100, deadline=None)
def test_document_id_extraction(source_type: str, document_id: str):
    """
    Test that document_id is correctly extracted from S3 key.
    """
    s3_key = f"{source_type}/{document_id}.pdf"
    
    extracted = extract_document_id(s3_key)
    
    assert extracted == document_id, \
        f"Expected document_id '{document_id}' from key '{s3_key}', got '{extracted}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
