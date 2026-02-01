"""
Reusable AWS tool resources for the Trade Matching Swarm.

This module provides shared AWS client configurations and resource management
that can be reused across multiple swarm sessions and agent deployments.
"""

import boto3
from botocore.config import Config
from typing import Dict, Any
import os


class AWSResourceManager:
    """Manages reusable AWS resources with proper configuration."""
    
    def __init__(self, region: str = None):
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self._clients: Dict[str, Any] = {}
        self._session = None
    
    @property
    def session(self) -> boto3.Session:
        """Get or create a shared boto3 session."""
        if self._session is None:
            self._session = boto3.Session(region_name=self.region)
        return self._session
    
    def get_client(self, service: str) -> Any:
        """Get or create a configured AWS client."""
        if service not in self._clients:
            # Service-specific configurations
            configs = {
                'bedrock-runtime': Config(
                    read_timeout=300,  # 5 minutes for PDF processing
                    connect_timeout=60,
                    retries={'max_attempts': 3, 'mode': 'adaptive'}
                ),
                's3': Config(
                    read_timeout=120,
                    connect_timeout=30,
                    retries={'max_attempts': 3, 'mode': 'adaptive'}
                ),
                'dynamodb': Config(
                    read_timeout=60,
                    connect_timeout=30,
                    retries={'max_attempts': 3, 'mode': 'adaptive'}
                )
            }
            
            config = configs.get(service, Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            ))
            
            self._clients[service] = self.session.client(service, config=config)
        
        return self._clients[service]
    
    def get_resource_config(self) -> Dict[str, Any]:
        """Get configuration that can be shared across sessions."""
        return {
            "region": self.region,
            "s3_bucket": os.getenv("S3_BUCKET_NAME", "trade-matching-system-agentcore-production"),
            "bank_table": os.getenv("DYNAMODB_BANK_TABLE", "BankTradeData"),
            "counterparty_table": os.getenv("DYNAMODB_COUNTERPARTY_TABLE", "CounterpartyTradeData"),
            "exceptions_table": os.getenv("DYNAMODB_EXCEPTIONS_TABLE", "ExceptionsTable"),
            "bedrock_model_id": os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
        }


# Global resource manager instance
_resource_manager = None

def get_aws_resource_manager() -> AWSResourceManager:
    """Get the global AWS resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = AWSResourceManager()
    return _resource_manager

def get_aws_client(service: str):
    """Get an AWS client using the shared resource manager."""
    return get_aws_resource_manager().get_client(service)

def get_config():
    """Get shared configuration."""
    return get_aws_resource_manager().get_resource_config()