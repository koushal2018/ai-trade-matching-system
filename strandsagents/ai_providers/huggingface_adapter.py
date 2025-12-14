"""
Hugging Face implementation of AI provider adapter
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
import os

# Optional dependency handling
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None

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


class HuggingfaceAdapter(AIProviderAdapter):
    """
    Hugging Face implementation of AI provider adapter.
    
    Supports both Hugging Face Inference API and local transformers.
    Useful as a fallback option for environments without AWS AI services.
    """
    
    def __init__(self):
        super().__init__()
        self.api_token = None
        self.model_name = None
        self.api_url = None
        self.session = None
        self.use_local = False
        self.local_pipeline = None
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize Hugging Face adapter with configuration.
        
        Expected config keys:
        - model_name: Hugging Face model name (required)
        - api_token: Hugging Face API token (optional for public models)
        - use_local: Whether to use local transformers (optional)
        - max_length: Maximum response length (optional)
        """
        try:
            self.model_name = config.get('model_name')
            if not self.model_name:
                raise AIProviderConfigurationError(
                    "HuggingfaceAdapter", 
                    "model_name", 
                    "Hugging Face model name is required"
                )
            
            self.api_token = config.get('api_token') or os.getenv('HUGGINGFACE_API_TOKEN')
            self.use_local = config.get('use_local', False)
            self.max_length = config.get('max_length', 1024)
            
            if self.use_local:
                await self._initialize_local_model()
            else:
                await self._initialize_api_client()
            
            # Test connectivity
            await self._test_connectivity()
            
            self.is_initialized = True
            self.logger.info(f"Hugging Face adapter initialized successfully with model {self.model_name}")
            return True
            
        except (AIProviderConfigurationError, AIProviderUnavailableError):
            # Re-raise our custom exceptions without wrapping
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize Hugging Face adapter: {e}")
            raise AIProviderError(f"Hugging Face initialization failed: {str(e)}")
    
    async def _initialize_local_model(self):
        """Initialize local transformers pipeline"""
        try:
            # Import transformers locally to avoid dependency issues
            from transformers import pipeline
            
            # Initialize pipeline in executor to avoid blocking
            self.local_pipeline = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pipeline(
                    "text-generation",
                    model=self.model_name,
                    device_map="auto" if self._has_gpu() else "cpu"
                )
            )
            
        except ImportError:
            raise AIProviderConfigurationError(
                "HuggingfaceAdapter",
                "transformers",
                "transformers library not installed for local model usage"
            )
        except Exception as e:
            raise AIProviderError(f"Failed to load local model: {str(e)}")
    
    async def _initialize_api_client(self):
        """Initialize API client for Hugging Face Inference API"""
        if not HAS_AIOHTTP:
            raise AIProviderConfigurationError(
                "HuggingfaceAdapter",
                "aiohttp",
                "aiohttp library is required for Hugging Face API usage. Install with: pip install aiohttp"
            )
        
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                "Authorization": f"Bearer {self.api_token}" if self.api_token else None,
                "Content-Type": "application/json"
            }
        )
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def _test_connectivity(self):
        """Test basic connectivity"""
        try:
            test_prompt = "Hello, please respond with 'OK' to confirm connectivity."
            await self._generate_text(test_prompt)
        except Exception as e:
            raise AIProviderUnavailableError(
                "HuggingfaceAdapter",
                f"Connectivity test failed: {str(e)}"
            )
    
    async def _generate_text(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate text using Hugging Face model.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        self._validate_initialization()
        
        try:
            # Combine system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            
            if self.use_local:
                return await self._generate_local(full_prompt)
            else:
                return await self._generate_api(full_prompt)
                
        except Exception as e:
            raise AIProviderError(f"Text generation failed: {str(e)}")
    
    async def _generate_local(self, prompt: str) -> str:
        """Generate text using local model"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.local_pipeline(
                    prompt,
                    max_length=self.max_length,
                    num_return_sequences=1,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.local_pipeline.tokenizer.eos_token_id
                )
            )
            
            generated_text = result[0]['generated_text']
            # Remove the original prompt from the response
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            raise AIProviderError(f"Local model generation failed: {str(e)}")
    
    async def _generate_api(self, prompt: str) -> str:
        """Generate text using Hugging Face API"""
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": self.max_length,
                    "temperature": 0.1,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            async with self.session.post(self.api_url, json=payload) as response:
                if response.status == 429:
                    raise AIProviderRateLimitError("HuggingfaceAdapter")
                elif response.status == 503:
                    raise AIProviderUnavailableError(
                        "HuggingfaceAdapter",
                        "Model is loading, please try again later"
                    )
                elif response.status != 200:
                    error_text = await response.text()
                    raise AIProviderError(f"API request failed: {error_text}")
                
                result = await response.json()
                
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
                elif isinstance(result, dict):
                    return result.get('generated_text', '').strip()
                else:
                    return str(result)
                    
        except aiohttp.ClientError as e:
            raise AIProviderError(f"API request failed: {str(e)}")
        except asyncio.TimeoutError:
            raise AIProviderTimeoutError("HuggingfaceAdapter", "api_request", 60)
    
    async def analyze_document_context(self, document_data: Dict[str, Any]) -> DocumentAnalysisResult:
        """Analyze document context using Hugging Face"""
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
            response = await self._generate_text(prompt, system_prompt)
            
            # Clean response and extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result_data = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No JSON found in response", response, 0)
            
            return DocumentAnalysisResult(
                transaction_type=result_data.get('transaction_type', 'unknown'),
                critical_fields=result_data.get('critical_fields', []),
                field_mappings=result_data.get('field_mappings', {}),
                confidence=result_data.get('confidence', 0.5),
                context_metadata=result_data.get('context_metadata', {})
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Hugging Face response as JSON: {e}")
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
        """Perform semantic field matching using Hugging Face"""
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
            response = await self._generate_text(prompt, system_prompt)
            
            # Clean response and extract JSON
            response = response.strip()
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result_data = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No JSON found in response", response, 0)
            
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
        """Perform intelligent trade matching using Hugging Face"""
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
            response = await self._generate_text(prompt, system_prompt)
            
            # Clean response and extract JSON
            response = response.strip()
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result_data = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No JSON found in response", response, 0)
            
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
        """Generate explanation for field mismatches using Hugging Face"""
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
            response = await self._generate_text(prompt, system_prompt)
            return response.strip()
            
        except Exception as e:
            # Fallback explanation
            return f"Field '{field_name}' mismatch: '{value1}' vs '{value2}'. Manual review required."
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this AI provider adapter."""
        return {
            'provider_type': 'huggingface',
            'provider_name': 'Hugging Face',
            'model_name': self.model_name,
            'api_token_configured': bool(self.api_token),
            'use_auth_token': self.use_auth_token,
            'max_length': self.max_length,
            'capabilities': [
                'document_analysis',
                'semantic_matching',
                'intelligent_matching',
                'mismatch_explanation'
            ],
            'supported_models': [
                'microsoft/DialoGPT-medium',
                'microsoft/DialoGPT-large',
                'gpt2',
                'distilgpt2'
            ]
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await super().cleanup()
        if self.session:
            await self.session.close()
            self.session = None