from pydantic import BaseModel


class ProcessingMetrics(BaseModel):
    totalProcessed: int
    matchedCount: int
    breakCount: int
    pendingReview: int
    avgProcessingTimeMs: int
    throughputPerHour: int
    errorCount: int = 0  # Count of exceptions with severity=CRITICAL or ERROR
    # Trade breakdown counts
    bankTradeCount: int = 0  # Count of trades from bank side
    counterpartyTradeCount: int = 0  # Count of trades from counterparty side
    # Legacy fields for frontend compatibility (deprecated)
    unmatchedCount: int = 0  # Alias for breakCount
    pendingCount: int = 0  # Alias for pendingReview
