"""
Trade Source Classification Logic

This module provides logic to classify trades as BANK or COUNTERPARTY based
on indicators in the text. It uses pattern matching and LLM for ambiguous cases.

Requirements: 6.2
"""

import json
import logging
import re
from typing import Dict, Any, Optional, Literal
import boto3
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeSourceClassifier:
    """
    Classifier for determining trade source (BANK or COUNTERPARTY).
    
    This classifier:
    1. Identifies BANK vs COUNTERPARTY indicators in text
    2. Uses pattern matching for clear cases
    3. Uses LLM for ambiguous cases
    4. Validates classification result
    
    Validates: Requirements 6.2
    """
    
    # Indicators for BANK source
    BANK_INDICATORS = [
        r'\bbank\b',
        r'\bfirst abu dhabi bank\b',
        r'\bfab\b',
        r'\bour\s+(?:trade|confirmation|deal)\b',
        r'\bwe\s+(?:confirm|agree|execute)\b',
        r'\binternal\s+(?:trade|confirmation)\b',
        r'\bseller:\s*(?:bank|fab)\b',
        r'\bbuyer:\s*(?:bank|fab)\b',
        r'\bfrom:\s*(?:bank|fab)\b',
        r'\bour\s+reference\b',
        r'\bour\s+trade\s+id\b'
    ]
    
    # Indicators for COUNTERPARTY source
    COUNTERPARTY_INDICATORS = [
        r'\bcounterparty\b',
        r'\bgoldman\s+sachs\b',
        r'\bgcs\b',
        r'\bmorgan\s+stanley\b',
        r'\bjp\s*morgan\b',
        r'\bcitibank\b',
        r'\btheir\s+(?:trade|confirmation|deal)\b',
        r'\bthey\s+(?:confirm|agree|execute)\b',
        r'\bexternal\s+(?:trade|confirmation)\b',
        r'\breceived\s+from\b',
        r'\btheir\s+reference\b',
        r'\btheir\s+trade\s+id\b',
        r'\bclient\s+confirmation\b'
    ]
    
    def __init__(
        self,
        model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name: str = "us-east-1",
        confidence_threshold: float = 0.7
    ):
        """
        Initialize Trade Source Classifier.
        
        Args:
            model_id: AWS Bedrock model ID for ambiguous cases
            region_name: AWS region
            confidence_threshold: Minimum confidence for pattern-based classification
        """
        self.model_id = model_id
        self.region_name = region_name
        self.confidence_threshold = confidence_threshold
        
        # Initialize Bedrock client for ambiguous cases
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=region_name
        )
        
        logger.info("Trade Source Classifier initialized")
    
    def classify_trade_source(
        self,
        extracted_text: str,
        document_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify trade source as BANK or COUNTERPARTY.
        
        Args:
            extracted_text: Text to analyze
            document_path: Optional S3 path for additional context
        
        Returns:
            dict: Classification result with source_type and confidence
            
        Validates: Requirements 6.2
        """
        try:
            logger.info("Classifying trade source")
            
            # Step 1: Try pattern-based classification
            pattern_result = self._classify_by_patterns(extracted_text, document_path)
            
            if pattern_result["confidence"] >= self.confidence_threshold:
                logger.info(
                    f"Pattern-based classification: {pattern_result['source_type']} "
                    f"(confidence: {pattern_result['confidence']})"
                )
                return {
                    "success": True,
                    "source_type": pattern_result["source_type"],
                    "confidence": pattern_result["confidence"],
                    "method": "pattern_matching",
                    "indicators": pattern_result["indicators"]
                }
            
            # Step 2: Use LLM for ambiguous cases
            logger.info(
                f"Pattern confidence too low ({pattern_result['confidence']}), "
                "using LLM for classification"
            )
            llm_result = self._classify_by_llm(extracted_text, document_path)
            
            if llm_result["success"]:
                logger.info(
                    f"LLM classification: {llm_result['source_type']} "
                    f"(confidence: {llm_result['confidence']})"
                )
                return llm_result
            else:
                # Fallback to pattern result even if confidence is low
                logger.warning(
                    f"LLM classification failed, using pattern result: "
                    f"{pattern_result['source_type']}"
                )
                return {
                    "success": True,
                    "source_type": pattern_result["source_type"],
                    "confidence": pattern_result["confidence"],
                    "method": "pattern_matching_fallback",
                    "indicators": pattern_result["indicators"],
                    "warning": "Low confidence classification"
                }
        
        except Exception as e:
            logger.error(f"Error classifying trade source: {e}")
            return {
                "success": False,
                "error": str(e),
                "source_type": None
            }
    
    def _classify_by_patterns(
        self,
        extracted_text: str,
        document_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify trade source using pattern matching.
        
        Args:
            extracted_text: Text to analyze
            document_path: Optional S3 path for additional context
        
        Returns:
            dict: Classification result with confidence and indicators
        """
        text_lower = extracted_text.lower()
        
        # Check for BANK indicators
        bank_matches = []
        for pattern in self.BANK_INDICATORS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                bank_matches.extend(matches)
        
        # Check for COUNTERPARTY indicators
        counterparty_matches = []
        for pattern in self.COUNTERPARTY_INDICATORS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                counterparty_matches.extend(matches)
        
        # Check document path for additional context
        path_score = 0.0
        if document_path:
            path_lower = document_path.lower()
            if '/bank/' in path_lower or 'bank_' in path_lower:
                path_score = 0.3
                bank_matches.append("path_indicator")
            elif '/counterparty/' in path_lower or 'counterparty_' in path_lower:
                path_score = 0.3
                counterparty_matches.append("path_indicator")
        
        # Compute confidence scores
        bank_score = len(bank_matches) * 0.1 + path_score
        counterparty_score = len(counterparty_matches) * 0.1 + path_score
        
        # Normalize to 0-1 range
        total_score = bank_score + counterparty_score
        if total_score > 0:
            bank_confidence = bank_score / total_score
            counterparty_confidence = counterparty_score / total_score
        else:
            bank_confidence = 0.5
            counterparty_confidence = 0.5
        
        # Determine classification
        if bank_confidence > counterparty_confidence:
            source_type = "BANK"
            confidence = bank_confidence
            indicators = bank_matches
        else:
            source_type = "COUNTERPARTY"
            confidence = counterparty_confidence
            indicators = counterparty_matches
        
        return {
            "source_type": source_type,
            "confidence": round(confidence, 2),
            "indicators": indicators[:5],  # Limit to first 5 indicators
            "bank_score": round(bank_score, 2),
            "counterparty_score": round(counterparty_score, 2)
        }
    
    def _classify_by_llm(
        self,
        extracted_text: str,
        document_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify trade source using LLM for ambiguous cases.
        
        Args:
            extracted_text: Text to analyze
            document_path: Optional S3 path for additional context
        
        Returns:
            dict: Classification result with confidence and reasoning
        """
        try:
            # Build classification prompt
            prompt = self._build_classification_prompt(extracted_text, document_path)
            
            # Prepare request body for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "temperature": 0.0,  # Deterministic classification
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Invoke Bedrock model
            logger.info(f"Invoking Bedrock model for classification: {self.model_id}")
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text from response
            if 'content' in response_body and len(response_body['content']) > 0:
                classification_text = response_body['content'][0]['text']
            else:
                raise ValueError("No content in Bedrock response")
            
            # Parse JSON from LLM response
            classification_text = classification_text.strip()
            if classification_text.startswith("```json"):
                classification_text = classification_text[7:]
            if classification_text.startswith("```"):
                classification_text = classification_text[3:]
            if classification_text.endswith("```"):
                classification_text = classification_text[:-3]
            classification_text = classification_text.strip()
            
            classification_data = json.loads(classification_text)
            
            # Validate classification
            source_type = classification_data.get("source_type")
            if source_type not in ["BANK", "COUNTERPARTY"]:
                raise ValueError(f"Invalid source_type from LLM: {source_type}")
            
            confidence = classification_data.get("confidence", 0.8)
            reasoning = classification_data.get("reasoning", "")
            
            return {
                "success": True,
                "source_type": source_type,
                "confidence": confidence,
                "method": "llm_classification",
                "reasoning": reasoning
            }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock API error: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"Bedrock API error: {error_code}",
                "error_message": error_message
            }
        
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_classification_prompt(
        self,
        extracted_text: str,
        document_path: Optional[str] = None
    ) -> str:
        """
        Build the classification prompt for the LLM.
        
        Args:
            extracted_text: Text to analyze
            document_path: Optional S3 path for additional context
        
        Returns:
            str: Formatted prompt for LLM
        """
        path_context = ""
        if document_path:
            path_context = f"\n\nDOCUMENT PATH: {document_path}"
        
        prompt = f"""You are a trade confirmation classifier. Determine whether this trade confirmation is from the BANK's perspective or the COUNTERPARTY's perspective.

TEXT TO ANALYZE:
{extracted_text[:2000]}  # Limit to first 2000 chars for efficiency
{path_context}

CLASSIFICATION RULES:
1. BANK perspective indicators:
   - References to "our trade", "our confirmation", "we confirm"
   - Internal trade references
   - Bank name (e.g., First Abu Dhabi Bank, FAB) as the originator
   - Document path contains "BANK" or "bank"

2. COUNTERPARTY perspective indicators:
   - References to "their trade", "received from", "client confirmation"
   - External trade references
   - Counterparty name (e.g., Goldman Sachs, Morgan Stanley) as the originator
   - Document path contains "COUNTERPARTY" or "counterparty"

RESPONSE FORMAT:
Return ONLY a JSON object with the following structure:
{{
    "source_type": "BANK" or "COUNTERPARTY",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of the classification"
}}

Do not include any markdown formatting or explanations outside the JSON object.
"""
        return prompt
    
    def _run(
        self,
        extracted_text: str,
        document_path: Optional[str] = None
    ) -> str:
        """
        Run the tool (CrewAI-compatible interface).
        
        Args:
            extracted_text: Text to analyze
            document_path: Optional S3 path for additional context
        
        Returns:
            str: JSON string with classification result
        """
        result = self.classify_trade_source(extracted_text, document_path)
        return json.dumps(result, indent=2)


# Convenience function for direct usage
def classify_trade_source(
    extracted_text: str,
    document_path: Optional[str] = None,
    model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name: str = "us-east-1"
) -> Literal["BANK", "COUNTERPARTY"]:
    """
    Classify trade source and return the source type.
    
    Args:
        extracted_text: Text to analyze
        document_path: Optional S3 path for additional context
        model_id: AWS Bedrock model ID
        region_name: AWS region
    
    Returns:
        str: "BANK" or "COUNTERPARTY"
    
    Raises:
        ValueError: If classification fails
    """
    classifier = TradeSourceClassifier(model_id=model_id, region_name=region_name)
    result = classifier.classify_trade_source(extracted_text, document_path)
    
    if result["success"]:
        return result["source_type"]
    else:
        raise ValueError(f"Classification failed: {result.get('error')}")
