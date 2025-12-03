"""
Report Generation

This module generates detailed markdown reports for trade matching results.

Requirements:
    - 7.3: Include summary statistics, matched trades, breaks, data errors
    - 7.4: Save reports to S3
    - 18.4: Include all existing report sections
"""

from datetime import datetime
from typing import Dict, List, Optional
import boto3
from ..models.matching import MatchingResult, MatchClassification


def generate_report(
    matching_result: MatchingResult,
    s3_bucket: str,
    s3_prefix: str = "reports"
) -> str:
    """
    Generate a detailed markdown report for a matching result.
    
    The report includes:
    - Summary statistics
    - Match classification and score
    - Trade details (bank and counterparty)
    - Field-by-field comparison
    - Differences and reason codes
    - Decision status and next actions
    
    Args:
        matching_result: Complete matching result
        s3_bucket: S3 bucket name for report storage
        s3_prefix: S3 prefix/folder for reports (default: "reports")
    
    Returns:
        S3 URI of the saved report
    
    Requirements:
        - 7.3: Complete report with all sections
        - 7.4: Save to S3
        - 18.4: Maintain functional parity
    
    Example:
        >>> result = MatchingResult(...)
        >>> report_path = generate_report(result, "my-bucket")
        >>> report_path.startswith("s3://my-bucket/reports/")
        True
    """
    # Generate report content
    report_content = _generate_report_content(matching_result)
    
    # Generate S3 key
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    s3_key = f"{s3_prefix}/matching_report_{matching_result.trade_id}_{timestamp}.md"
    
    # Upload to S3
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=s3_key,
        Body=report_content.encode('utf-8'),
        ContentType='text/markdown'
    )
    
    s3_uri = f"s3://{s3_bucket}/{s3_key}"
    return s3_uri


def generate_batch_report(
    matching_results: List[MatchingResult],
    s3_bucket: str,
    s3_prefix: str = "reports",
    batch_id: str = None
) -> str:
    """
    Generate a batch report summarizing multiple matching results.
    
    This report provides aggregate statistics across all trades in the batch.
    
    Args:
        matching_results: List of matching results
        s3_bucket: S3 bucket name
        s3_prefix: S3 prefix/folder for reports
        batch_id: Optional batch identifier
    
    Returns:
        S3 URI of the saved batch report
    
    Requirements:
        - 7.3: Summary statistics for batch processing
    """
    # Generate batch report content
    report_content = _generate_batch_report_content(matching_results, batch_id)
    
    # Generate S3 key
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    batch_id_str = f"_{batch_id}" if batch_id else ""
    s3_key = f"{s3_prefix}/batch_matching_report{batch_id_str}_{timestamp}.md"
    
    # Upload to S3
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=s3_key,
        Body=report_content.encode('utf-8'),
        ContentType='text/markdown'
    )
    
    s3_uri = f"s3://{s3_bucket}/{s3_key}"
    return s3_uri


def _generate_report_content(result: MatchingResult) -> str:
    """
    Generate the markdown content for a single matching result.
    
    Args:
        result: Matching result
    
    Returns:
        Markdown formatted report
    """
    lines = []
    
    # Header
    lines.append("# Trade Matching Report")
    lines.append("")
    lines.append(f"**Trade ID:** {result.trade_id}")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    
    # Summary Section
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Classification:** {result.classification.value}")
    lines.append(f"- **Match Score:** {result.match_score:.2f} / 1.00")
    lines.append(f"- **Confidence:** {result.confidence_score:.2f}")
    lines.append(f"- **Decision Status:** {result.decision_status.value}")
    lines.append(f"- **Requires HITL:** {'Yes' if result.requires_hitl else 'No'}")
    lines.append("")
    
    # Reason Codes
    if result.reason_codes:
        lines.append("## Reason Codes")
        lines.append("")
        for code in result.reason_codes:
            lines.append(f"- {code}")
        lines.append("")
    
    # Trade Details
    lines.append("## Trade Details")
    lines.append("")
    
    # Bank Trade
    lines.append("### Bank Trade")
    lines.append("")
    if result.bank_trade:
        lines.extend(_format_trade_details(result.bank_trade))
    else:
        lines.append("*No bank trade found*")
    lines.append("")
    
    # Counterparty Trade
    lines.append("### Counterparty Trade")
    lines.append("")
    if result.counterparty_trade:
        lines.extend(_format_trade_details(result.counterparty_trade))
    else:
        lines.append("*No counterparty trade found*")
    lines.append("")
    
    # Field Comparison
    if result.differences:
        lines.append("## Field Comparison")
        lines.append("")
        lines.append("| Field | Bank Value | Counterparty Value | Difference Type | Within Tolerance |")
        lines.append("|-------|------------|-------------------|-----------------|------------------|")
        
        for diff in result.differences:
            bank_val = _format_value(diff.bank_value)
            cp_val = _format_value(diff.counterparty_value)
            tolerance = "✓" if diff.within_tolerance else "✗"
            
            lines.append(
                f"| {diff.field_name} | {bank_val} | {cp_val} | "
                f"{diff.difference_type} | {tolerance} |"
            )
        lines.append("")
    else:
        lines.append("## Field Comparison")
        lines.append("")
        lines.append("*No differences found - perfect match*")
        lines.append("")
    
    # Next Actions
    lines.append("## Next Actions")
    lines.append("")
    if result.decision_status.value == "AUTO_MATCH":
        lines.append("✓ **Auto-confirm match** - No further action required")
    elif result.decision_status.value == "ESCALATE":
        lines.append("⚠ **Human review required** - Trade sent to HITL queue")
    else:
        lines.append("✗ **Exception handling required** - Trade sent to exception queue")
    lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by Trade Matching Agent*")
    if result.matching_timestamp:
        lines.append(f"*Matching performed at: {result.matching_timestamp}*")
    lines.append("")
    
    return "\n".join(lines)


def _generate_batch_report_content(
    results: List[MatchingResult],
    batch_id: Optional[str]
) -> str:
    """
    Generate markdown content for batch report.
    
    Args:
        results: List of matching results
        batch_id: Optional batch identifier
    
    Returns:
        Markdown formatted batch report
    """
    lines = []
    
    # Header
    lines.append("# Batch Trade Matching Report")
    lines.append("")
    if batch_id:
        lines.append(f"**Batch ID:** {batch_id}")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Total Trades:** {len(results)}")
    lines.append("")
    
    # Summary Statistics
    lines.append("## Summary Statistics")
    lines.append("")
    
    # Count by classification
    classification_counts = {}
    for result in results:
        cls = result.classification.value
        classification_counts[cls] = classification_counts.get(cls, 0) + 1
    
    lines.append("### By Classification")
    lines.append("")
    for cls in MatchClassification:
        count = classification_counts.get(cls.value, 0)
        pct = (count / len(results) * 100) if results else 0
        lines.append(f"- **{cls.value}:** {count} ({pct:.1f}%)")
    lines.append("")
    
    # Count by decision status
    decision_counts = {}
    for result in results:
        dec = result.decision_status.value
        decision_counts[dec] = decision_counts.get(dec, 0) + 1
    
    lines.append("### By Decision Status")
    lines.append("")
    for dec in ["AUTO_MATCH", "ESCALATE", "EXCEPTION"]:
        count = decision_counts.get(dec, 0)
        pct = (count / len(results) * 100) if results else 0
        lines.append(f"- **{dec}:** {count} ({pct:.1f}%)")
    lines.append("")
    
    # Average match score
    if results:
        avg_score = sum(r.match_score for r in results) / len(results)
        lines.append(f"**Average Match Score:** {avg_score:.2f}")
        lines.append("")
    
    # Detailed Results
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| Trade ID | Classification | Score | Decision | Reason Codes |")
    lines.append("|----------|---------------|-------|----------|--------------|")
    
    for result in results:
        codes = ", ".join(result.reason_codes[:3])  # Show first 3 codes
        if len(result.reason_codes) > 3:
            codes += "..."
        
        lines.append(
            f"| {result.trade_id} | {result.classification.value} | "
            f"{result.match_score:.2f} | {result.decision_status.value} | {codes} |"
        )
    lines.append("")
    
    # Breaks and Exceptions
    breaks = [r for r in results if r.classification == MatchClassification.BREAK]
    if breaks:
        lines.append("## Breaks")
        lines.append("")
        lines.append(f"**Total Breaks:** {len(breaks)}")
        lines.append("")
        for result in breaks:
            lines.append(f"- **{result.trade_id}** (Score: {result.match_score:.2f})")
            if result.reason_codes:
                lines.append(f"  - Reasons: {', '.join(result.reason_codes)}")
        lines.append("")
    
    # Data Errors
    data_errors = [r for r in results if r.classification == MatchClassification.DATA_ERROR]
    if data_errors:
        lines.append("## Data Errors")
        lines.append("")
        lines.append(f"**Total Data Errors:** {len(data_errors)}")
        lines.append("")
        for result in data_errors:
            lines.append(f"- **{result.trade_id}**")
            if result.reason_codes:
                lines.append(f"  - Errors: {', '.join(result.reason_codes)}")
        lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*Batch report generated by Trade Matching Agent*")
    lines.append("")
    
    return "\n".join(lines)


def _format_trade_details(trade: Dict) -> List[str]:
    """
    Format trade details for display in report.
    
    Args:
        trade: Trade dictionary
    
    Returns:
        List of formatted lines
    """
    lines = []
    
    # Key fields to display
    key_fields = [
        "Trade_ID",
        "TRADE_SOURCE",
        "trade_date",
        "notional",
        "currency",
        "counterparty",
        "product_type",
        "effective_date",
        "maturity_date",
        "commodity_type"
    ]
    
    for field in key_fields:
        value = _extract_field_value(trade, field)
        if value is not None:
            lines.append(f"- **{field}:** {value}")
    
    return lines


def _extract_field_value(trade: Dict, field_name: str):
    """
    Extract field value from trade, handling DynamoDB format.
    
    Args:
        trade: Trade dictionary
        field_name: Field name to extract
    
    Returns:
        Field value or None
    """
    if field_name not in trade:
        return None
    
    value = trade[field_name]
    
    # Handle DynamoDB typed format
    if isinstance(value, dict):
        if "S" in value:
            return value["S"]
        elif "N" in value:
            return value["N"]
        elif "BOOL" in value:
            return value["BOOL"]
    
    return value


def _format_value(value) -> str:
    """
    Format a value for display in markdown table.
    
    Args:
        value: Value to format
    
    Returns:
        Formatted string
    """
    if value is None:
        return "*N/A*"
    elif isinstance(value, float):
        return f"{value:.2f}"
    else:
        return str(value)
