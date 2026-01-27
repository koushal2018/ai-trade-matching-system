import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment Configuration
    environment: str = "development"  # development, staging, production
    disable_auth: bool = True  # Disable authentication in development

    # AWS Configuration
    aws_region: str = "us-east-1"

    # Production DynamoDB Tables
    dynamodb_bank_table: str = "BankTradeData"
    dynamodb_counterparty_table: str = "CounterpartyTradeData"
    dynamodb_matched_table: str = "TradeMatches"
    dynamodb_exceptions_table: str = "ExceptionsTable"
    dynamodb_audit_table: str = "AuditTrail"
    dynamodb_agent_registry_table: str = "trade-matching-system-agent-registry-production"
    dynamodb_hitl_table: str = "HITLReviews"
    dynamodb_processing_status_table: str = "trade-matching-system-processing-status"

    # Production S3 Bucket
    s3_bucket: str = "trade-matching-system-agentcore-production"

    # SQS Queues
    hitl_queue_url: str = ""

    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
