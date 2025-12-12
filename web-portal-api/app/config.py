import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AWS Configuration
    aws_region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    dynamodb_bank_table: str = os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData")
    dynamodb_counterparty_table: str = os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData")
    dynamodb_exceptions_table: str = os.getenv("DYNAMODB_EXCEPTIONS_TABLE", "ExceptionsTable")
    dynamodb_audit_table: str = os.getenv("DYNAMODB_AUDIT_TABLE", "AuditTrail")
    dynamodb_agent_registry_table: str = os.getenv("DYNAMODB_AGENT_REGISTRY_TABLE", "AgentRegistry")
    dynamodb_hitl_table: str = os.getenv("DYNAMODB_HITL_TABLE", "HITLReviews")
    s3_bucket: str = os.getenv("S3_BUCKET_NAME", "trade-matching-us-east-1")
    
    # SQS Queues
    hitl_queue_url: str = os.getenv("HITL_QUEUE_URL", "")
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"


settings = Settings()
