---
inclusion: fileMatch
fileMatchPattern: "**/test*.py"
---

# Testing Standards

## Test Categories
- `tests/unit/` - Fast, isolated tests with mocked dependencies
- `tests/integration/` - Tests with real AWS services (use test data)
- `tests/e2e/` - Complete workflow tests with sample PDFs
- `tests/property_based/` - Hypothesis-based property tests

## Property-Based Testing with Hypothesis
This project uses Hypothesis for property-based testing. Key patterns:

```python
from hypothesis import given, strategies as st, settings, assume
import pytest

# Define strategies for test data generation
pdf_filename_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=100
).map(lambda s: s + ".pdf")

source_type_strategy = st.sampled_from(["BANK", "COUNTERPARTY"])

@given(
    source_type=source_type_strategy,
    filename=pdf_filename_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_source_type_inference(source_type: str, filename: str):
    """
    **Feature: feature-name, Property N: Property Description**
    **Validates: Requirements X.Y**
    
    Property description here.
    """
    s3_key = f"{source_type}/{filename}"
    result = infer_source_type(s3_key)
    assert result == source_type
```

## Test Docstring Format
Always include feature reference and requirement traceability:
```python
"""
**Feature: s3-event-automation, Property 1: Source Type Inference**
**Validates: Requirements 1.1, 1.2**

Description of what the test validates.
"""
```

## Running Tests
```bash
pytest tests/ -v                           # All tests
pytest tests/property_based/ -v            # Property tests only
pytest tests/ --cov=src --cov-report=html  # With coverage
```

## Test Data Guidelines
- Use sanitized data - no real financial information
- Create reusable fixtures in `conftest.py`
- Mock AWS services in unit tests using `moto` or `unittest.mock`
- Clean up test resources after execution
