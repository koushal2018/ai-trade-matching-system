"""Custom evaluators for trade matching quality assessment."""

from .client import evaluations_client

# Built-in evaluator ARNs
BUILTIN_EVALUATORS = {
    "helpfulness": "arn:aws:bedrock-agentcore:::evaluator/Builtin.Helpfulness",
    "accuracy": "arn:aws:bedrock-agentcore:::evaluator/Builtin.Accuracy",
    "coherence": "arn:aws:bedrock-agentcore:::evaluator/Builtin.Coherence"
}

# Trade extraction accuracy evaluation criteria
TRADE_EXTRACTION_CRITERIA = """
Evaluate the trade extraction based on:
1. Field Completeness: Are all mandatory fields extracted? (Trade_ID, trade_date, notional, currency, counterparty)
2. Field Accuracy: Do extracted values match the source document?
3. Format Correctness: Are dates, numbers, and currencies in correct format?
4. Source Classification: Is TRADE_SOURCE correctly identified as BANK or COUNTERPARTY?

Score 1-5 where:
5 = All fields correct, complete, properly formatted
4 = Minor formatting issues, all fields present
3 = 1-2 fields missing or incorrect
2 = Multiple errors or missing mandatory fields
1 = Extraction failed or fundamentally incorrect
"""

# Matching quality evaluation criteria
MATCHING_QUALITY_CRITERIA = """
Evaluate the matching decision based on:
1. Score Accuracy: Does the match score reflect actual similarity?
2. Classification Correctness: Is the classification (MATCHED, BREAK, etc.) appropriate?
3. Reason Code Relevance: Are reason codes accurate and helpful?
4. Tolerance Application: Were matching tolerances correctly applied?
   - Trade_Date: ±1 business day
   - Notional: ±0.01%
   - Counterparty: Fuzzy string match

Score 1-5 where:
5 = Perfect matching decision with accurate scoring
4 = Correct decision with minor scoring variance
3 = Correct decision but inaccurate scoring or reason codes
2 = Questionable decision requiring review
1 = Incorrect matching decision
"""

# OCR quality evaluation criteria
OCR_QUALITY_CRITERIA = """
Evaluate the OCR extraction quality based on:
1. Text Completeness: Is all visible text from the document extracted?
2. Character Accuracy: Are characters correctly recognized?
3. Layout Preservation: Is document structure maintained?
4. Special Characters: Are numbers, dates, and symbols correct?

Score 1-5 where:
5 = Perfect extraction with no errors
4 = Minor errors that don't affect data extraction
3 = Some errors requiring manual review
2 = Significant errors affecting data quality
1 = Extraction failed or unusable
"""

# Exception handling evaluation criteria
EXCEPTION_HANDLING_CRITERIA = """
Evaluate the exception handling based on:
1. Classification Accuracy: Is the exception correctly classified?
2. Severity Assessment: Is the severity score appropriate?
3. Routing Decision: Is the exception routed to the correct handler?
4. SLA Compliance: Is the SLA deadline appropriate for the severity?

Score 1-5 where:
5 = Perfect classification, routing, and SLA assignment
4 = Correct routing with minor severity variance
3 = Correct classification but suboptimal routing
2 = Questionable routing decision
1 = Incorrect classification or routing
"""


def create_trade_extraction_evaluator() -> dict:
    """Create custom evaluator for trade extraction accuracy."""
    return evaluations_client.create_custom_evaluator(
        name="TradeExtractionAccuracy",
        description="Evaluates accuracy of trade field extraction from PDFs",
        evaluation_criteria=TRADE_EXTRACTION_CRITERIA,
        scoring_schema={
            "type": "integer",
            "minimum": 1,
            "maximum": 5
        }
    )


def create_matching_quality_evaluator() -> dict:
    """Create custom evaluator for matching quality."""
    return evaluations_client.create_custom_evaluator(
        name="MatchingQuality",
        description="Evaluates quality of trade matching decisions",
        evaluation_criteria=MATCHING_QUALITY_CRITERIA,
        scoring_schema={
            "type": "integer",
            "minimum": 1,
            "maximum": 5
        }
    )


def create_ocr_quality_evaluator() -> dict:
    """Create custom evaluator for OCR quality."""
    return evaluations_client.create_custom_evaluator(
        name="OCRQuality",
        description="Evaluates quality of OCR text extraction",
        evaluation_criteria=OCR_QUALITY_CRITERIA,
        scoring_schema={
            "type": "integer",
            "minimum": 1,
            "maximum": 5
        }
    )


def create_exception_handling_evaluator() -> dict:
    """Create custom evaluator for exception handling."""
    return evaluations_client.create_custom_evaluator(
        name="ExceptionHandlingQuality",
        description="Evaluates quality of exception classification and routing",
        evaluation_criteria=EXCEPTION_HANDLING_CRITERIA,
        scoring_schema={
            "type": "integer",
            "minimum": 1,
            "maximum": 5
        }
    )


def get_all_custom_evaluators() -> dict[str, dict]:
    """Create and return all custom evaluators."""
    return {
        "trade_extraction": create_trade_extraction_evaluator(),
        "matching_quality": create_matching_quality_evaluator(),
        "ocr_quality": create_ocr_quality_evaluator(),
        "exception_handling": create_exception_handling_evaluator()
    }
