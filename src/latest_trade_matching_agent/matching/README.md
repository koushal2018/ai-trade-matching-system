# Trade Matching Module

This module provides fuzzy matching, scoring, classification, and reporting capabilities for trade confirmation matching.

## Quick Start

```python
from latest_trade_matching_agent.matching import (
    fuzzy_match,
    compute_match_score,
    classify_match,
    generate_report
)

# 1. Perform fuzzy matching
bank_trade = {
    "Trade_ID": {"S": "ABC123"},
    "trade_date": {"S": "2024-10-15"},
    "notional": {"N": "1000000.00"},
    "counterparty": {"S": "Goldman Sachs"},
    "currency": {"S": "USD"}
}

counterparty_trade = {
    "Trade_ID": {"S": "ABC123"},
    "trade_date": {"S": "2024-10-16"},  # 1 day difference
    "notional": {"N": "1000050.00"},  # 0.005% difference
    "counterparty": {"S": "Goldman Sachs"},
    "currency": {"S": "USD"}
}

match_result = fuzzy_match(bank_trade, counterparty_trade)

# 2. Compute match score
match_score = compute_match_score(match_result)
print(f"Match score: {match_score:.2f}")  # e.g., 0.92

# 3. Classify result
classification, decision, reason_codes = classify_match(
    match_score=match_score,
    match_result=match_result,
    trade_id="ABC123",
    bank_trade=bank_trade,
    counterparty_trade=counterparty_trade
)

print(f"Classification: {classification.value}")  # e.g., PROBABLE_MATCH
print(f"Decision: {decision.value}")  # e.g., ESCALATE
print(f"Reason codes: {reason_codes}")  # e.g., ['WITHIN_DATE_TOLERANCE']
```

## Modules

### fuzzy_matcher.py

Performs fuzzy matching with tolerances:

**Tolerances**:
- Trade_ID: Exact match required
- Trade_Date: ±1 business day
- Notional: ±0.01%
- Counterparty: Fuzzy string match (similarity >= 0.8)
- Currency: Exact match

**Functions**:
- `fuzzy_match(bank_trade, counterparty_trade) -> MatchResult`

**Returns**: `MatchResult` with:
- `trade_id_match`: bool
- `date_diff_days`: int
- `notional_diff_pct`: float
- `counterparty_similarity`: float (0.0 to 1.0)
- `currency_match`: bool
- `differences`: List of field differences

### scorer.py

Computes weighted match scores:

**Field Weights**:
- Trade_ID: 30%
- Notional: 25%
- Trade_Date: 20%
- Counterparty: 15%
- Currency: 10%

**Functions**:
- `compute_match_score(match_result) -> float`
- `compute_match_score_with_confidence(match_result) -> Tuple[float, float]`

**Returns**: Score from 0.0 (no match) to 1.0 (perfect match)

### classifier.py

Classifies matches and determines decision status:

**Classification Thresholds**:
- Score >= 0.85: MATCHED → AUTO_MATCH
- Score 0.70-0.84: PROBABLE_MATCH → ESCALATE (HITL)
- Score 0.50-0.69: REVIEW_REQUIRED → EXCEPTION
- Score < 0.50: BREAK → EXCEPTION

**Functions**:
- `classify_match(match_score, match_result, trade_id, bank_trade, counterparty_trade) -> Tuple[MatchClassification, DecisionStatus, List[str]]`
- `create_matching_result(...) -> MatchingResult`
- `check_data_integrity(bank_trade, counterparty_trade) -> Tuple[bool, List[str]]`

**Reason Codes**:
- `NOTIONAL_MISMATCH`: Notional exceeds tolerance
- `DATE_MISMATCH`: Date exceeds tolerance
- `COUNTERPARTY_MISMATCH`: Counterparty doesn't match
- `CURRENCY_MISMATCH`: Currency doesn't match
- `WITHIN_DATE_TOLERANCE`: Date within tolerance
- `WITHIN_NOTIONAL_TOLERANCE`: Notional within tolerance
- `FUZZY_COUNTERPARTY_MATCH`: Counterparty fuzzy match
- `DATA_ERROR`: Data integrity issue

### report_generator.py

Generates markdown reports:

**Functions**:
- `generate_report(matching_result, s3_bucket, s3_prefix) -> str`
- `generate_batch_report(matching_results, s3_bucket, s3_prefix, batch_id) -> str`

**Report Sections**:
1. Summary (classification, score, decision)
2. Reason codes
3. Trade details (bank and counterparty)
4. Field comparison table
5. Next actions

**Returns**: S3 URI of saved report

## Complete Example

```python
from latest_trade_matching_agent.matching.classifier import create_matching_result
from latest_trade_matching_agent.matching import (
    fuzzy_match,
    compute_match_score,
    generate_report
)

# Perform matching
match_result = fuzzy_match(bank_trade, counterparty_trade)
match_score = compute_match_score(match_result)

# Create complete result
matching_result = create_matching_result(
    trade_id="ABC123",
    match_score=match_score,
    match_result=match_result,
    bank_trade=bank_trade,
    counterparty_trade=counterparty_trade,
    matching_timestamp="2025-01-15T10:00:00Z"
)

# Generate report
report_path = generate_report(
    matching_result,
    s3_bucket="my-bucket",
    s3_prefix="reports"
)

print(f"Report saved to: {report_path}")
print(f"Classification: {matching_result.classification.value}")
print(f"Decision: {matching_result.decision_status.value}")
print(f"Requires HITL: {matching_result.requires_hitl}")
```

## Testing

Run tests:

```bash
pytest src/latest_trade_matching_agent/matching/test_matching.py -v
```

## Integration with Trade Matching Agent

The Trade Matching Agent (`agents/trade_matching_agent.py`) uses this module to:

1. Subscribe to `matching-events` SQS queue
2. Retrieve trades from DynamoDB
3. Perform fuzzy matching and scoring
4. Classify results
5. Generate reports
6. Publish to appropriate queues based on decision

See `agents/trade_matching_agent.py` for the complete event-driven implementation.

## Requirements

- Python 3.11+
- boto3 (for S3 operations)
- pydantic (for data models)

## License

Part of the AI Trade Matching System - AgentCore Migration
