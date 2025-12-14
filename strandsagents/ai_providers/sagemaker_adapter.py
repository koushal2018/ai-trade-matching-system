"""
AWS Sagemaker AI Jumpstart implementation of AI provider adapter
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

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


class SagemakerAdapter(AIProviderAdapter):
    """
    AWS Sagemaker AI Jumpstart implementation of AI provider adapter.
    
    Supports deployed Sagemaker endpoints with foundation models.
    Particularly useful for UAE region where Bedrock may not be available.
    """
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.endpoint_name = None
        self.region = None
        self.model_type = None
        self.content_type = 'application/json'
        self.accept_type = 'application/json'
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize Sagemaker client with configuration.
        
        Expected config keys:
        - region: AWS region (required)
        - endpoint_name: Sagemaker endpoint name (required)
        - model_type: Type of model (optional, helps with request formatting)
        - content_type: Request content type (optional)
        - accept_type: Response accept type (optional)
        """
        try:
            self.region = config.get('region')
            if not self.region:
                raise AIProviderConfigurationError(
                    "SagemakerAdapter", 
                    "region", 
                    "AWS region is required for Sagemaker"
                )
            
            self.endpoint_name = config.get('endpoint_name')
            if not self.endpoint_name:
                raise AIProviderConfigurationError(
                    "SagemakerAdapter",
                    "endpoint_name",
                    "Sagemaker endpoint name is required"
                )
            
            self.model_type = config.get('model_type', 'huggingface')
            self.content_type = config.get('content_type', 'application/json')
            self.accept_type = config.get('accept_type', 'application/json')
            
            # Initialize Sagemaker runtime client
            self.client = boto3.client(
                'sagemaker-runtime',
                region_name=self.region
            )
            
            # Test connectivity
            await self._test_connectivity()
            
            self.is_initialized = True
            self.logger.info(f"Sagemaker adapter initialized successfully with endpoint {self.endpoint_name}")
            return True
            
        except (AIProviderConfigurationError, AIProviderUnavailableError):
            # Re-raise our custom exceptions without wrapping
            raise
        except NoCredentialsError:
            raise AIProviderConfigurationError(
                "SagemakerAdapter",
                "credentials",
                "AWS credentials not found or invalid"
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'ValidationException':
                raise AIProviderConfigurationError(
                    "SagemakerAdapter",
                    "endpoint",
                    f"Sagemaker endpoint '{self.endpoint_name}' not found or invalid"
                )
            else:
                raise AIProviderUnavailableError(
                    "SagemakerAdapter",
                    f"AWS Sagemaker unavailable: {str(e)}"
                )
        except Exception as e:
            self.logger.error(f"Failed to initialize Sagemaker adapter: {e}")
            raise AIProviderError(f"Sagemaker initialization failed: {str(e)}")
    
    async def _test_connectivity(self):
        """Test basic connectivity to Sagemaker endpoint"""
        try:
            # Simple test prompt
            test_prompt = "Hello, please respond with 'OK' to confirm connectivity."
            await self._invoke_endpoint(test_prompt)
        except Exception as e:
            raise AIProviderUnavailableError(
                "SagemakerAdapter",
                f"Connectivity test failed: {str(e)}"
            )
    
    async def _invoke_endpoint(self, prompt: str, system_prompt: str = None) -> str:
        """
        Invoke Sagemaker endpoint with prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Model response text
        """
        self._validate_initialization()
        
        try:
            # Prepare request payload based on model type
            if self.model_type.lower() == 'huggingface':
                # Standard Hugging Face format
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 1024,
                        "temperature": 0.1,
                        "do_sample": True,
                        "return_full_text": False
                    }
                }
                if system_prompt:
                    payload["inputs"] = f"System: {system_prompt}\n\nUser: {prompt}"
                    
            elif self.model_type.lower() == 'llama':
                # Llama format
                if system_prompt:
                    formatted_prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
                else:
                    formatted_prompt = f"<s>[INST] {prompt} [/INST]"
                
                payload = {
                    "inputs": formatted_prompt,
                    "parameters": {
                        "max_new_tokens": 1024,
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            else:
                # Generic format
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 1024,
                        "temperature": 0.1
                    }
                }
                if system_prompt:
                    payload["system"] = system_prompt
            
            # Invoke endpoint
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.invoke_endpoint(
                    EndpointName=self.endpoint_name,
                    ContentType=self.content_type,
                    Accept=self.accept_type,
                    Body=json.dumps(payload)
                )
            )
            
            # Parse response
            response_body = json.loads(response['Body'].read().decode())
            
            # Extract text based on response format
            if isinstance(response_body, list) and len(response_body) > 0:
                if 'generated_text' in response_body[0]:
                    return response_body[0]['generated_text']
                elif 'text' in response_body[0]:
                    return response_body[0]['text']
            elif isinstance(response_body, dict):
                if 'generated_text' in response_body:
                    return response_body['generated_text']
                elif 'outputs' in response_body:
                    return response_body['outputs']
                elif 'text' in response_body:
                    return response_body['text']
            
            # Fallback - return string representation
            return str(response_body)
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'ModelError':
                raise AIProviderError(f"Sagemaker model error: {str(e)}")
            elif error_code == 'ThrottlingException':
                raise AIProviderRateLimitError("SagemakerAdapter")
            else:
                raise AIProviderError(f"Sagemaker API error: {str(e)}")
        except asyncio.TimeoutError:
            raise AIProviderTimeoutError("SagemakerAdapter", "endpoint_invocation", 30)
        except Exception as e:
            raise AIProviderError(f"Unexpected error invoking Sagemaker endpoint: {str(e)}")
    
    async def analyze_document_context(self, document_data: Dict[str, Any]) -> DocumentAnalysisResult:
        """Analyze document context using Sagemaker"""
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
            response = await self._invoke_endpoint(prompt, system_prompt)
            
            # Clean response and extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
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
            self.logger.error(f"Failed to parse Sagemaker response as JSON: {e}")
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
        """Perform semantic field matching using Sagemaker"""
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
            response = await self._invoke_endpoint(prompt, system_prompt)
            
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
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
        """Perform intelligent trade matching using Sagemaker"""
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
            response = await self._invoke_endpoint(prompt, system_prompt)
            
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
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
        """Generate explanation for field mismatches using Sagemaker"""
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
            response = await self._invoke_endpoint(prompt, system_prompt)
            return response.strip()
            
        except Exception as e:
            # Fallback explanation
            return f"Field '{field_name}' mismatch: '{value1}' vs '{value2}'. Manual review required."
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this AI provider adapter."""
        return {
            'provider_type': 'sagemaker',
            'provider_name': 'AWS SageMaker',
            'endpoint_name': self.endpoint_name,
            'region': self.region,
            'instance_type': self.instance_type,
            'capabilities': [
                'document_analysis',
                'semantic_matching',
                'intelligent_matching',
                'mismatch_explanation'
            ],
            'supported_models': [
                'huggingface-text-generation',
                'custom-trained-models'
            ]
        }