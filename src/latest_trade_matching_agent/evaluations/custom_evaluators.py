"""
Custom Evaluators for AgentCore Trade Matching System

**Feature: agentcore-migration, Tasks 33.1-33.4**
**Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5**
"""

import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..models.trade import CanonicalTradeModel
from ..models.adapter import CanonicalAdapterOutput


class EvaluationScore(Enum):
    """Evaluation scoring scale (1-5)."""
    POOR = 1
    BELOW_AVERAGE = 2
    AVERAGE = 3
    GOOD = 4
    EXCELLENT = 5


@dataclass
class EvaluationResult:
    """Result of an evaluation."""
    evaluator_name: str
    score: EvaluationScore
    confidence: float  # 0.0 to 1.0
    reasoning: str
    metadata: Dict[str, Any]
    timestamp: datetime


class TradeExtractionAccuracyEvaluator:
    """
    Evaluates the accuracy of trade data extraction using LLM-as-Judge.
    
    **Validates: Requirements 19.1, 19.2**
    """
    
    def __init__(self, bedrock_client=None):
        self.bedrock_client = bedrock_client or boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    
    def evaluate(self, 
                 original_pdf_text: str, 
                 extracted_trade: CanonicalTradeModel,
                 ground_truth: Optional[Dict[str, Any]] = None) -> EvaluationResult:
        """
        Evaluate trade extraction accuracy using LLM-as-Judge.
        
        Args:
            original_pdf_text: The original extracted text from PDF
            extracted_trade: The structured trade data extracted by the agent
            ground_truth: Optional ground truth data for comparison
            
        Returns:
            EvaluationResult with score and reasoning
        """
        
        # Prepare evaluation prompt
        evaluation_prompt = f"""
You are an expert financial trade analyst evaluating the accuracy of automated trade data extraction.

ORIGINAL PDF TEXT:
{original_pdf_text[:2000]}...

EXTRACTED TRADE DATA:
{json.dumps(extracted_trade.dict(), indent=2)}

EVALUATION CRITERIA:
1. Completeness: Are all critical trade fields extracted?
2. Accuracy: Do the extracted values match the source document?
3. Format: Are the values in the correct format and data types?
4. Consistency: Are related fields logically consistent?

Required Fields: Trade_ID, trade_date, notional, currency, counterparty, product_type, TRADE_SOURCE

Rate the extraction quality on a scale of 1-5:
1 = Poor (major errors, missing critical fields)
2 = Below Average (some errors, minor missing fields)
3 = Average (mostly correct, minor formatting issues)
4 = Good (accurate with minimal issues)
5 = Excellent (perfect extraction)

Provide your evaluation in this JSON format:
{{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "missing_fields": ["<list of missing required fields>"],
    "accuracy_issues": ["<list of accuracy concerns>"],
    "format_issues": ["<list of format problems>"]
}}
"""
        
        try:
            # Call Bedrock for LLM-as-Judge evaluation
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": evaluation_prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            evaluation_text = response_body['content'][0]['text']
            
            # Parse the JSON response
            evaluation_data = json.loads(evaluation_text)
            
            return EvaluationResult(
                evaluator_name="TradeExtractionAccuracy",
                score=EvaluationScore(evaluation_data["score"]),
                confidence=evaluation_data["confidence"],
                reasoning=evaluation_data["reasoning"],
                metadata={
                    "missing_fields": evaluation_data.get("missing_fields", []),
                    "accuracy_issues": evaluation_data.get("accuracy_issues", []),
                    "format_issues": evaluation_data.get("format_issues", []),
                    "extracted_fields_count": len(extracted_trade.dict()),
                    "trade_source": extracted_trade.TRADE_SOURCE
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            # Fallback evaluation if LLM fails
            return self._fallback_evaluation(extracted_trade, str(e))
    
    def _fallback_evaluation(self, extracted_trade: CanonicalTradeModel, error: str) -> EvaluationResult:
        """Fallback rule-based evaluation if LLM fails."""
        required_fields = ["Trade_ID", "trade_date", "notional", "currency", "counterparty", "TRADE_SOURCE"]
        trade_dict = extracted_trade.dict()
        
        missing_fields = [field for field in required_fields if not trade_dict.get(field)]
        completeness_score = max(1, 5 - len(missing_fields))
        
        return EvaluationResult(
            evaluator_name="TradeExtractionAccuracy",
            score=EvaluationScore(completeness_score),
            confidence=0.7,  # Lower confidence for rule-based
            reasoning=f"Fallback evaluation due to LLM error: {error}. Based on field completeness.",
            metadata={
                "missing_fields": missing_fields,
                "fallback_used": True,
                "error": error
            },
            timestamp=datetime.utcnow()
        )


class MatchingQualityEvaluator:
    """
    Evaluates the quality of trade matching decisions.
    
    **Validates: Requirements 19.1, 19.2**
    """
    
    def __init__(self, bedrock_client=None):
        self.bedrock_client = bedrock_client or boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    
    def evaluate(self, 
                 bank_trade: Dict[str, Any],
                 counterparty_trade: Dict[str, Any],
                 match_result: Dict[str, Any],
                 match_score: float) -> EvaluationResult:
        """
        Evaluate matching decision quality using LLM-as-Judge.
        
        Args:
            bank_trade: Bank trade data
            counterparty_trade: Counterparty trade data  
            match_result: The matching result from the agent
            match_score: Computed match score (0.0-1.0)
            
        Returns:
            EvaluationResult with quality assessment
        """
        
        evaluation_prompt = f"""
You are an expert trade settlement analyst evaluating automated trade matching quality.

BANK TRADE:
{json.dumps(bank_trade, indent=2)}

COUNTERPARTY TRADE:
{json.dumps(counterparty_trade, indent=2)}

MATCHING RESULT:
{json.dumps(match_result, indent=2)}

MATCH SCORE: {match_score}

EVALUATION CRITERIA:
1. Accuracy: Is the matching decision correct based on trade attributes?
2. Reasoning: Are the reason codes appropriate and complete?
3. Risk Assessment: Does the decision appropriately manage settlement risk?
4. Threshold Application: Are the classification thresholds applied correctly?

Classification Thresholds:
- MATCHED: 85%+ (auto-settle)
- PROBABLE_MATCH: 70-84% (senior review)
- REVIEW_REQUIRED: 50-69% (ops review)
- BREAK: <50% (investigate)

Matching Tolerances:
- Currency: Exact match required
- Notional: ±2% tolerance
- Dates: ±2 business days
- Counterparty: Fuzzy string matching

Rate the matching quality on a scale of 1-5:
1 = Poor (incorrect decision, high settlement risk)
2 = Below Average (questionable decision, some risk)
3 = Average (reasonable decision, standard risk)
4 = Good (sound decision, low risk)
5 = Excellent (optimal decision, minimal risk)

Provide your evaluation in JSON format:
{{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "decision_correctness": "<correct|questionable|incorrect>",
    "risk_level": "<low|medium|high>",
    "threshold_applied_correctly": <true|false>
}}
"""
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": evaluation_prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            evaluation_text = response_body['content'][0]['text']
            evaluation_data = json.loads(evaluation_text)
            
            return EvaluationResult(
                evaluator_name="MatchingQuality",
                score=EvaluationScore(evaluation_data["score"]),
                confidence=evaluation_data["confidence"],
                reasoning=evaluation_data["reasoning"],
                metadata={
                    "decision_correctness": evaluation_data.get("decision_correctness"),
                    "risk_level": evaluation_data.get("risk_level"),
                    "threshold_applied_correctly": evaluation_data.get("threshold_applied_correctly"),
                    "match_score": match_score,
                    "classification": match_result.get("classification")
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return self._fallback_matching_evaluation(match_score, str(e))
    
    def _fallback_matching_evaluation(self, match_score: float, error: str) -> EvaluationResult:
        """Fallback rule-based matching evaluation."""
        # Simple rule-based evaluation
        if match_score >= 0.85:
            score = EvaluationScore.EXCELLENT
        elif match_score >= 0.70:
            score = EvaluationScore.GOOD
        elif match_score >= 0.50:
            score = EvaluationScore.AVERAGE
        else:
            score = EvaluationScore.BELOW_AVERAGE
        
        return EvaluationResult(
            evaluator_name="MatchingQuality",
            score=score,
            confidence=0.6,
            reasoning=f"Fallback evaluation based on match score: {match_score}. LLM error: {error}",
            metadata={
                "fallback_used": True,
                "match_score": match_score,
                "error": error
            },
            timestamp=datetime.utcnow()
        )


class OCRQualityEvaluator:
    """
    Evaluates OCR text extraction quality.
    
    **Validates: Requirements 19.1, 19.2**
    """
    
    def __init__(self, bedrock_client=None):
        self.bedrock_client = bedrock_client or boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    
    def evaluate(self, 
                 extracted_text: str,
                 pdf_metadata: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate OCR extraction quality.
        
        Args:
            extracted_text: Text extracted from PDF
            pdf_metadata: Metadata about the PDF (pages, size, etc.)
            
        Returns:
            EvaluationResult with OCR quality assessment
        """
        
        # Basic quality checks
        text_length = len(extracted_text)
        word_count = len(extracted_text.split())
        has_trade_keywords = any(keyword in extracted_text.upper() for keyword in 
                               ["TRADE", "NOTIONAL", "CURRENCY", "COUNTERPARTY", "SWAP", "OPTION"])
        
        # Rule-based scoring
        if text_length < 100:
            score = EvaluationScore.POOR
            reasoning = "Extracted text too short, likely OCR failure"
        elif word_count < 20:
            score = EvaluationScore.BELOW_AVERAGE
            reasoning = "Very few words extracted, possible OCR issues"
        elif not has_trade_keywords:
            score = EvaluationScore.AVERAGE
            reasoning = "Text extracted but no trade-related keywords found"
        elif text_length > 500 and has_trade_keywords:
            score = EvaluationScore.EXCELLENT
            reasoning = "Good text extraction with trade-related content"
        else:
            score = EvaluationScore.GOOD
            reasoning = "Adequate text extraction"
        
        return EvaluationResult(
            evaluator_name="OCRQuality",
            score=score,
            confidence=0.8,
            reasoning=reasoning,
            metadata={
                "text_length": text_length,
                "word_count": word_count,
                "has_trade_keywords": has_trade_keywords,
                "pdf_pages": pdf_metadata.get("pages", 0),
                "pdf_size": pdf_metadata.get("size", 0)
            },
            timestamp=datetime.utcnow()
        )


class ExceptionHandlingQualityEvaluator:
    """
    Evaluates exception handling and triage quality.
    
    **Validates: Requirements 19.1, 19.2**
    """
    
    def evaluate(self, 
                 exception_data: Dict[str, Any],
                 triage_result: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate exception handling quality.
        
        Args:
            exception_data: The exception that occurred
            triage_result: How the exception was triaged
            
        Returns:
            EvaluationResult with exception handling assessment
        """
        
        severity = triage_result.get("severity", "UNKNOWN")
        routing = triage_result.get("routing", "UNKNOWN")
        sla_hours = triage_result.get("sla_hours", 0)
        
        # Rule-based evaluation of triage decisions
        if severity == "CRITICAL" and sla_hours <= 4 and routing in ["ENGINEERING", "SENIOR_OPS"]:
            score = EvaluationScore.EXCELLENT
            reasoning = "Critical exception properly escalated with tight SLA"
        elif severity == "HIGH" and sla_hours <= 24 and routing in ["SENIOR_OPS", "COMPLIANCE"]:
            score = EvaluationScore.GOOD
            reasoning = "High severity exception appropriately handled"
        elif severity == "MEDIUM" and sla_hours <= 72 and routing == "OPS_DESK":
            score = EvaluationScore.GOOD
            reasoning = "Medium severity exception routed correctly"
        elif severity == "LOW" and routing == "AUTO_RESOLVE":
            score = EvaluationScore.EXCELLENT
            reasoning = "Low severity exception auto-resolved appropriately"
        else:
            score = EvaluationScore.AVERAGE
            reasoning = "Exception handling follows standard procedures"
        
        return EvaluationResult(
            evaluator_name="ExceptionHandlingQuality",
            score=score,
            confidence=0.9,
            reasoning=reasoning,
            metadata={
                "severity": severity,
                "routing": routing,
                "sla_hours": sla_hours,
                "exception_type": exception_data.get("type", "UNKNOWN")
            },
            timestamp=datetime.utcnow()
        )


class EvaluationOrchestrator:
    """
    Orchestrates evaluation execution and result aggregation.
    
    **Validates: Requirements 19.3, 19.4, 19.5**
    """
    
    def __init__(self):
        self.evaluators = {
            "trade_extraction": TradeExtractionAccuracyEvaluator(),
            "matching_quality": MatchingQualityEvaluator(),
            "ocr_quality": OCRQualityEvaluator(),
            "exception_handling": ExceptionHandlingQualityEvaluator()
        }
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    
    def evaluate_agent_interaction(self, 
                                   agent_name: str,
                                   interaction_data: Dict[str, Any]) -> List[EvaluationResult]:
        """
        Evaluate a complete agent interaction.
        
        Args:
            agent_name: Name of the agent being evaluated
            interaction_data: Data from the agent interaction
            
        Returns:
            List of evaluation results
        """
        results = []
        
        # Route to appropriate evaluators based on agent type
        if agent_name == "pdf_adapter":
            if "extracted_text" in interaction_data:
                result = self.evaluators["ocr_quality"].evaluate(
                    interaction_data["extracted_text"],
                    interaction_data.get("pdf_metadata", {})
                )
                results.append(result)
        
        elif agent_name == "trade_extractor":
            if "extracted_trade" in interaction_data and "original_text" in interaction_data:
                result = self.evaluators["trade_extraction"].evaluate(
                    interaction_data["original_text"],
                    interaction_data["extracted_trade"]
                )
                results.append(result)
        
        elif agent_name == "trade_matcher":
            if "match_result" in interaction_data:
                result = self.evaluators["matching_quality"].evaluate(
                    interaction_data.get("bank_trade", {}),
                    interaction_data.get("counterparty_trade", {}),
                    interaction_data["match_result"],
                    interaction_data.get("match_score", 0.0)
                )
                results.append(result)
        
        elif agent_name == "exception_handler":
            if "triage_result" in interaction_data:
                result = self.evaluators["exception_handling"].evaluate(
                    interaction_data.get("exception_data", {}),
                    interaction_data["triage_result"]
                )
                results.append(result)
        
        # Send metrics to CloudWatch
        for result in results:
            self._send_metrics_to_cloudwatch(agent_name, result)
        
        return results
    
    def _send_metrics_to_cloudwatch(self, agent_name: str, result: EvaluationResult):
        """Send evaluation metrics to CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='AgentCore/Evaluations',
                MetricData=[
                    {
                        'MetricName': 'QualityScore',
                        'Dimensions': [
                            {
                                'Name': 'AgentName',
                                'Value': agent_name
                            },
                            {
                                'Name': 'EvaluatorName',
                                'Value': result.evaluator_name
                            }
                        ],
                        'Value': result.score.value,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'Confidence',
                        'Dimensions': [
                            {
                                'Name': 'AgentName',
                                'Value': agent_name
                            },
                            {
                                'Name': 'EvaluatorName',
                                'Value': result.evaluator_name
                            }
                        ],
                        'Value': result.confidence,
                        'Unit': 'Percent'
                    }
                ]
            )
        except Exception as e:
            print(f"Failed to send metrics to CloudWatch: {e}")