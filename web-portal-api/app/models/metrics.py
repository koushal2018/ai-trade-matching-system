from pydantic import BaseModel


class ProcessingMetrics(BaseModel):
    totalProcessed: int
    matchedCount: int
    breakCount: int
    pendingReview: int
    avgProcessingTimeMs: int
    throughputPerHour: int
