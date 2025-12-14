"""
Base abstract class for AI Provider Adapters
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentAnalysisResult:
    """Result from document context analysis"""
    transaction_type: str
    critical_fields: List[str]
    field_mappings: Dict[str, str]
    confidence: float
    context_metadata: Dict[str, Any]


@dataclass
class SemanticMatchResult:
    """Result from semantic field matching"""
    similarity_score: float
    is_match: bool
    reasoning: str
    confidence: float


@dataclass
class IntelligentMatchResult:
    """Result from intelligent trade matching"""
    match_confidence: float
    field_comparisons: Dict[str, Any]
    overall_status: str  # MATCHED, MISMATCHED, UNCERTAIN
    reasoning: str
    method_used: str


class AIProviderAdapter(ABC):
    """
    Abstract base class for AI provider adapters.
    
    This class defines the interface that all AI providers must implement
    to support the enhanced trade reconciliation system.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.provider_name = self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.provider_name}")
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the AI provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
            
        Returns:
            bool: True if initialization successful, False otherwise
            
        Raises:
            AIProviderConfigurationError: If configuration is invalid
            AIProviderUnavailableError: If provider cannot be reached
        """
        pass
    
    @abstractmethod
    async def analyze_document_context(self, document_data: Dict[str, Any]) -> DocumentAnalysisResult:
        """
        Analyze document to understand context and extract relevant fields.
        
        Args:
            document_data: Dictionary containing document/trade data
            
        Returns:
            DocumentAnalysisResult: Analysis results including transaction type,
                                  critical fields, and field mappings
                                  
        Raises:
            AIProviderError: If analysis fails
        """
        pass
    
    @abstractmethod
    async def semantic_field_matching(
        self, 
        field1: str, 
        field2: str, 
        context: str = ""
    ) -> SemanticMatchResult:
        """
        Calculate semantic similarity between field names.
        
        Args:
            field1: First field name to compare
            field2: Second field name to compare
            context: Optional context information (e.g., transaction type)
            
        Returns:
            SemanticMatchResult: Similarity score and match determination
            
        Raises:
            AIProviderError: If matching fails
        """
        pass
    
    @abstractmethod
    async def intelligent_trade_matching(
        self, 
        trade1: Dict[str, Any], 
        trade2: Dict[str, Any]
    ) -> IntelligentMatchResult:
        """
        Perform intelligent trade matching using AI.
        
        Args:
            trade1: First trade data dictionary
            trade2: Second trade data dictionary
            
        Returns:
            IntelligentMatchResult: Comprehensive matching result with reasoning
            
        Raises:
            AIProviderError: If matching fails
        """
        pass
    
    @abstractmethod
    async def explain_mismatch(
        self, 
        field_name: str, 
        value1: Any, 
        value2: Any, 
        context: str = ""
    ) -> str:
        """
        Generate human-readable explanation for field mismatches.
        
        Args:
            field_name: Name of the field that mismatched
            value1: First value
            value2: Second value
            context: Optional context information
            
        Returns:
            str: Human-readable explanation of the mismatch
            
        Raises:
            AIProviderError: If explanation generation fails
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the AI provider.
        
        Returns:
            Dict containing health status information
        """
        try:
            # Basic connectivity test - try to analyze a simple document
            test_data = {
                "trade_date": "2024-01-15",
                "currency": "USD",
                "notional": 1000000
            }
            
            start_time = asyncio.get_event_loop().time()
            result = await asyncio.wait_for(
                self.analyze_document_context(test_data),
                timeout=30.0
            )
            end_time = asyncio.get_event_loop().time()
            
            return {
                "status": "healthy",
                "provider": self.provider_name,
                "response_time_ms": int((end_time - start_time) * 1000),
                "last_check": asyncio.get_event_loop().time()
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "provider": self.provider_name,
                "error": "Health check timed out after 30 seconds"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_name,
                "error": str(e)
            }
    
    def _validate_initialization(self):
        """Ensure provider is initialized before operations"""
        if not self.is_initialized:
            raise RuntimeError(f"{self.provider_name} must be initialized before use")
    
    async def cleanup(self):
        """
        Cleanup resources when provider is no longer needed.
        Override in subclasses if cleanup is required.
        """
        self.logger.info(f"Cleaning up {self.provider_name}")
        self.is_initialized = False