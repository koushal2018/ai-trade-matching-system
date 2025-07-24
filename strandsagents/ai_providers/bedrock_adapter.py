"""
AWS Bedrock implementation of AI provider adapter
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

from .base import (
    AIProviderAdapter, 
    DocumentAnalysisResult, 
    SemanticMatchResult, 
    IntelligentMatchResult
)
from .exceptions import (
    AIProviderError,
    AIProviderUnavailableError,
    AIProviderConfigurationError,
    AIProviderTimeoutError,
    AIProviderRateLimitError
)

logger = logging.getLogger(__name__)


class BedrockAdapter(AIProviderAdapter):
    """
    AWS Bedrock implementation of AI provider adapter.
    
    Supports Claude 3 models and other foundation models available in Bedrock.
    """
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.model_id = None
        self.region = None
        self.max_tokens = 4096
        self.temperature = 0.1
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize Bedrock client with configuration.
        
        Expected config keys:
        - region: AWS region (required)
        - model_id: Bedrock model ID (optional, defaults to Claude 3 Sonnet)
        - max_tokens: Maximum tokens for responses (optional)
        - temperature: Model temperature (optional)
        """
        try:
            self.region = config.get('region')
            if not self.region:
                raise AIProviderConfigurationError(
                    "BedrockAdapter", 
                    "region", 
                    "AWS region is required for Bedrock"
                )
            
            self.model_id = config.get(
                'model_id', 
                'anthropic.claude-3-sonnet-20240229-v1:0'
            )
            self.max_tokens = config.get('max_tokens', 4096)
            self.temperature = config.get('temperature', 0.1)
            
            # Initialize Bedrock client
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=self.region
            )
            
            # Test connectivity
            await self._test_connectivity()
            
            self.is_initialized = True
            self.logger.info(f"Bedrock adapter initialized successfully in region {self.region}")
            return True
            
        except (AIProviderConfigurationError, AIProviderUnavailableError):
            # Re-raise our custom exceptions without wrapping
            raise
        except NoCredentialsError:
            raise AIProviderConfigurationError(
                "BedrockAdapter",
                "credentials",
                "AWS credentials not found or invalid"
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'UnauthorizedOperation':
                raise AIProviderConfigurationError(
                    "BedrockAdapter",
                    "permissions",
                    f"Insufficient permissions for Bedrock in region {self.region}"
                )
            else:
                raise AIProviderUnavailableError(
                    "BedrockAdapter",
                    f"AWS Bedrock unavailable: {str(e)}"
                )
        except Exception as e:
            self.logger.error(f"Failed to initialize Bedrock adapter: {e}")
            raise AIProviderError(f"Bedrock initialization failed: {str(e)}")
    
    async def _test_connectivity(self):
        """Test basic connectivity to Bedrock"""
        try:
            # Simple test prompt
            test_prompt = "Hello, please respond with 'OK' to confirm connectivity."
            await self._invoke_model(test_prompt)
        except Exception as e:
            raise AIProviderUnavailableError(
                "BedrockAdapter",
                f"Connectivity test failed: {str(e)}"
            )
    
    async def _invoke_model(self, prompt: str, system_prompt: str = None) -> str:
        """
        Invoke Bedrock model with prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Model response text
        """
        self._validate_initialization()
        
        try:
            # Prepare request body based on model type
            if 'claude' in self.model_id.lower():
                messages = [{"role": "user", "content": prompt}]
                if system_prompt:
                    body = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                        "system": system_prompt,
                        "messages": messages
                    }
                else:
                    body = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                        "messages": messages
                    }
            else:
                # Generic format for other models
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": self.max_tokens,
                        "temperature": self.temperature
                    }
                }
            
            # Invoke model
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.invoke_model(
                    body=json.dumps(body),
                    modelId=self.model_id,
                    accept='application/json',
                    contentType='application/json'
                )
            )
            
            # Parse response
            response_body = json.loads(response.get('body').read())
            
            if 'claude' in self.model_id.lower():
                return response_body['content'][0]['text']
            else:
                return response_body.get('results', [{}])[0].get('outputText', '')
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'ThrottlingException':
                raise AIProviderRateLimitError("BedrockAdapter")
            elif error_code == 'ValidationException':
                raise AIProviderError(f"Invalid request to Bedrock: {str(e)}")
            else:
                raise AIProviderError(f"Bedrock API error: {str(e)}")
        except asyncio.TimeoutError:
            raise AIProviderTimeoutError("BedrockAdapter", "model_invocation", 30)
        except Exception as e:
            raise AIProviderError(f"Unexpected error invoking Bedrock model: {str(e)}")
    
    async def analyze_document_context(self, document_data: Dict[str, Any]) -> DocumentAnalysisResult:
        """Analyze document context using Bedrock"""
        system_prompt = """You are a financial trade analysis expert. Analyze trade documents to identify transaction types, critical fields, and field mappings for reconciliation purposes."""
        
        prompt = f"""
        Analyze this trade document and provide a structured analysis:

        Document data: {json.dumps(document_data, indent=2, default=str)}

        Please identify:
        1. Transaction type (e.g., commodity_swap, fx_forward, interest_rate_swap, etc.)
        2. Critical fields that are essential for reconciliation
        3. Field mappings and semantic equivalents
        4. Your confidence level (0.0 to 1.0)

        Respond with valid JSON in this exact format:
        {{
            "transaction_type": "string",
            "critical_fields": ["field1", "field2", "field3"],
            "field_mappings": {{"original_field": "standard_field"}},
            "confidence": 0.95,
            "context_metadata": {{"reasoning": "explanation", "asset_class": "commodities"}}
        }}
        """
        
        try:
            response = await self._invoke_model(prompt, system_prompt)
            
            # Parse JSON response
            result_data = json.loads(response.strip())
            
            return DocumentAnalysisResult(
                transaction_type=result_data.get('transaction_type', 'unknown'),
                critical_fields=result_data.get('critical_fields', []),
                field_mappings=result_data.get('field_mappings', {}),
                confidence=result_data.get('confidence', 0.5),
                context_metadata=result_data.get('context_metadata', {})
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Bedrock response as JSON: {e}")
            # Fallback analysis
            return DocumentAnalysisResult(
                transaction_type='unknown',
                critical_fields=['trade_date', 'notional', 'currency'],
                field_mappings={},
                confidence=0.3,
                context_metadata={'error': 'Failed to parse AI response', 'fallback': True}
            )
        except Exception as e:
            raise AIProviderError(f"Document analysis failed: {str(e)}")
    
    async def semantic_field_matching(
        self, 
        field1: str, 
        field2: str, 
        context: str = ""
    ) -> SemanticMatchResult:
        """Perform semantic field matching using Bedrock"""
        system_prompt = """You are a financial terminology expert. Compare field names to determine if they refer to the same concept in trade reconciliation."""
        
        prompt = f"""
        Compare these two field names in the context of financial trade reconciliation:

        Field 1: "{field1}"
        Field 2: "{field2}"
        Context: {context if context else "General trade reconciliation"}

        Determine if these fields refer to the same concept. Consider:
        - Semantic equivalence (e.g., "settlement_date" vs "maturity_date")
        - Common financial terminology variations
        - Context-specific meanings

        Respond with valid JSON in this exact format:
        {{
            "similarity_score": 0.95,
            "is_match": true,
            "reasoning": "Both fields refer to the date when the trade settles",
            "confidence": 0.90
        }}
        """
        
        try:
            response = await self._invoke_model(prompt, system_prompt)
            result_data = json.loads(response.strip())
            
            return SemanticMatchResult(
                similarity_score=result_data.get('similarity_score', 0.0),
                is_match=result_data.get('is_match', False),
                reasoning=result_data.get('reasoning', 'No reasoning provided'),
                confidence=result_data.get('confidence', 0.5)
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse semantic matching response: {e}")
            # Simple fallback - exact string match
            is_exact_match = field1.lower() == field2.lower()
            return SemanticMatchResult(
                similarity_score=1.0 if is_exact_match else 0.0,
                is_match=is_exact_match,
                reasoning="Fallback to exact string matching due to parsing error",
                confidence=0.3
            )
        except Exception as e:
            raise AIProviderError(f"Semantic field matching failed: {str(e)}")
    
    async def intelligent_trade_matching(
        self, 
        trade1: Dict[str, Any], 
        trade2: Dict[str, Any]
    ) -> IntelligentMatchResult:
        """Perform intelligent trade matching using Bedrock"""
        system_prompt = """You are a trade reconciliation expert. Compare two trades to determine if they represent the same transaction, considering variations in formatting, terminology, and data representation."""
        
        prompt = f"""
        Compare these two trades to determine if they represent the same transaction:

        Trade 1: {json.dumps(trade1, indent=2, default=str)}

        Trade 2: {json.dumps(trade2, indent=2, default=str)}

        Analyze:
        1. Key identifying fields (dates, amounts, counterparties)
        2. Semantic equivalence of field values
        3. Acceptable variations in formatting
        4. Overall likelihood these are the same trade

        Respond with valid JSON in this exact format:
        {{
            "match_confidence": 0.95,
            "field_comparisons": {{
                "trade_date": {{"status": "MATCHED", "reasoning": "Both dates are 2024-01-15"}},
                "notional": {{"status": "MATCHED", "reasoning": "Both amounts are 1,000,000 USD"}}
            }},
            "overall_status": "MATCHED",
            "reasoning": "High confidence match based on key fields",
            "method_used": "ai_semantic_analysis"
        }}
        """
        
        try:
            response = await self._invoke_model(prompt, system_prompt)
            result_data = json.loads(response.strip())
            
            return IntelligentMatchResult(
                match_confidence=result_data.get('match_confidence', 0.0),
                field_comparisons=result_data.get('field_comparisons', {}),
                overall_status=result_data.get('overall_status', 'UNCERTAIN'),
                reasoning=result_data.get('reasoning', 'No reasoning provided'),
                method_used=result_data.get('method_used', 'ai_analysis')
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse trade matching response: {e}")
            return IntelligentMatchResult(
                match_confidence=0.0,
                field_comparisons={},
                overall_status='UNCERTAIN',
                reasoning='Failed to parse AI response',
                method_used='fallback'
            )
        except Exception as e:
            raise AIProviderError(f"Intelligent trade matching failed: {str(e)}")
    
    async def explain_mismatch(
        self, 
        field_name: str, 
        value1: Any, 
        value2: Any, 
        context: str = ""
    ) -> str:
        """Generate explanation for field mismatches using Bedrock"""
        system_prompt = """You are a trade reconciliation expert. Provide clear, concise explanations for why field values don't match in trade reconciliation."""
        
        prompt = f"""
        Explain why these field values don't match in trade reconciliation:

        Field: {field_name}
        Value 1: {value1}
        Value 2: {value2}
        Context: {context if context else "Trade reconciliation"}

        Provide a clear, business-friendly explanation that helps operations staff understand:
        1. What the difference is
        2. Potential reasons for the difference
        3. Whether this is likely a critical issue or acceptable variation

        Keep the explanation concise and actionable.
        """
        
        try:
            response = await self._invoke_model(prompt, system_prompt)
            return response.strip()
            
        except Exception as e:
            # Fallback explanation
            return f"Field '{field_name}' mismatch: '{value1}' vs '{value2}'. Manual review required."