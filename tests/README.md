# Test Suite

This directory contains the test suite for the AI Trade Matching System.

## Test Categories

### Unit Tests

#### `test_installation.py`
Tests that dependencies and project configuration are properly set up.

```bash
pytest tests/test_installation.py -v
```

#### `test_api_startup.py`
Tests that the FastAPI backend starts up correctly.

```bash
pytest tests/test_api_startup.py -v
```

### End-to-End Tests (`e2e/`)

#### `test_complete_workflow.py`
Tests the complete workflow from PDF processing to trade matching.

```bash
pytest tests/e2e/test_complete_workflow.py -v
```

#### `test_data_generator.py`
Utilities for generating test data for E2E tests.

### Property-Based Tests (`property_based/`)

Property-based tests using [Hypothesis](https://hypothesis.readthedocs.io/) to validate system behavior across various inputs.

#### Memory and Storage Tests
- `test_property_1_memory_storage_consistency.py` - Memory storage consistency
- `test_property_2_memory_retrieval_relevance.py` - Memory retrieval relevance
- `test_property_5_memory_configuration.py` - Memory configuration validation

#### System Integration Tests
- `test_property_3_session_id_format.py` - Session ID format validation
- `test_property_4_functional_parity.py` - Functional parity between components
- `test_property_6_agentcore_runtime_scaling.py` - AgentCore runtime scaling

#### Processing Tests
- `test_property_11_pdf_dpi.py` - PDF processing DPI validation
- `test_property_12_llm_ocr_completeness.py` - LLM OCR completeness
- `test_property_17_simple.py` - Simple property validation

#### Dependency Tests
- `test_property_2_dependency_consistency.py` - Dependency consistency validation

#### Session Management
- `test_session_manager_simple.py` - Session manager functionality

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Categories
```bash
# Unit tests only
pytest tests/test_*.py -v

# End-to-end tests
pytest tests/e2e/ -v

# Property-based tests
pytest tests/property_based/ -v
```

### With Coverage
```bash
pytest tests/ --cov=deployment --cov=web-portal-api --cov-report=html
```

### Property-Based Test Configuration

Property-based tests use Hypothesis with custom settings:

```python
from hypothesis import settings

# Custom settings for longer-running tests
@settings(max_examples=100, deadline=5000)
def test_property_example():
    pass
```

## Test Data

Test data is generated using:
- **Hypothesis strategies** for property-based tests
- **Test data generators** in `e2e/test_data_generator.py`
- **Mock data** for unit tests

## Prerequisites

- Python 3.11+
- All dependencies installed (`pip install -r requirements.txt`)
- AWS credentials configured (for integration tests)
- DynamoDB tables created (for E2E tests)

## Configuration

Tests use environment variables for configuration:

```bash
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=test-bucket
export DYNAMODB_AGENT_REGISTRY_TABLE=test-table
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```bash
# Fast tests (unit tests)
pytest tests/test_*.py --maxfail=1

# Full test suite
pytest tests/ --maxfail=5 --tb=short
```

## Adding New Tests

### Unit Tests
Add new unit tests directly in the `tests/` directory following the naming pattern `test_*.py`.

### Property-Based Tests
Add new property-based tests in `tests/property_based/` following the pattern `test_property_*.py`.

### End-to-End Tests
Add new E2E tests in `tests/e2e/` and update the test data generator as needed.

## Test Guidelines

1. **Isolation**: Each test should be independent and not rely on external state
2. **Deterministic**: Tests should produce consistent results
3. **Fast**: Unit tests should complete quickly (< 1 second each)
4. **Descriptive**: Test names should clearly describe what is being tested
5. **Assertions**: Use clear, specific assertions with helpful error messages