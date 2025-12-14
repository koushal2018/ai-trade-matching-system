"""
Domain-Specific Prompts and Context for OTC Trade Reconciliation

This module provides specialized prompts and context templates for different
asset classes and trading contexts to improve AI understanding of financial
terminology and trade reconciliation requirements.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

from financial_domain_intelligence import AssetClass, TradingContext, DomainContext


@dataclass
class PromptTemplate:
    """Template for domain-specific prompts"""
    name: str
    asset_class: AssetClass
    trading_context: Optional[TradingContext]
    system_prompt: str
    user_prompt_template: str
    examples: List[Dict[str, Any]]
    validation_instructions: str


class DomainPromptGenerator:
    """
    Generates domain-specific prompts for AI providers based on asset class
    and trading context to improve understanding of OTC trade terminology.
    """
    
    def __init__(self):
        self.prompt_templates = {}
        self._initialize_prompt_templates()
    
    def _initialize_prompt_templates(self):
        """Initialize domain-specific prompt templates"""
        
        # Commodities prompts
        self.prompt_templates["commodities_analysis"] = PromptTemplate(
            name="commodities_analysis",
            asset_class=AssetClass.COMMODITIES,
            trading_context=None,
            system_prompt=self._get_commodities_system_prompt(),
            user_prompt_template=self._get_commodities_user_prompt(),
            examples=self._get_commodities_examples(),
            validation_instructions=self._get_commodities_validation()
        )
        
        # FX prompts
        self.prompt_templates["fx_analysis"] = PromptTemplate(
            name="fx_analysis",
            asset_class=AssetClass.FX,
            trading_context=None,
            system_prompt=self._get_fx_system_prompt(),
            user_prompt_template=self._get_fx_user_prompt(),
            examples=self._get_fx_examples(),
            validation_instructions=self._get_fx_validation()
        )
        
        # Rates prompts
        self.prompt_templates["rates_analysis"] = PromptTemplate(
            name="rates_analysis",
            asset_class=AssetClass.RATES,
            trading_context=TradingContext.SWAP,
            system_prompt=self._get_rates_system_prompt(),
            user_prompt_template=self._get_rates_user_prompt(),
            examples=self._get_rates_examples(),
            validation_instructions=self._get_rates_validation()
        )
        
        # Derivatives prompts
        self.prompt_templates["derivatives_analysis"] = PromptTemplate(
            name="derivatives_analysis",
            asset_class=AssetClass.DERIVATIVES,
            trading_context=None,
            system_prompt=self._get_derivatives_system_prompt(),
            user_prompt_template=self._get_derivatives_user_prompt(),
            examples=self._get_derivatives_examples(),
            validation_instructions=self._get_derivatives_validation()
        )
    
    def _get_commodities_system_prompt(self) -> str:
        return """You are an expert in commodities trading and OTC trade reconciliation. You have deep knowledge of:

COMMODITIES EXPERTISE:
- Physical commodity markets (oil, gas, metals, agriculture)
- Commodity trading terminology and conventions
- Settlement and delivery mechanisms
- Price discovery and risk management
- Regional market differences and terminology variations

KEY TERMINOLOGY UNDERSTANDING:
- Settlement Date = Delivery Date = Maturity Date = Termination Date
- Notional Quantity = Volume = Amount = Size = Total Quantity
- Fixed Price = Strike Price = Contract Price = Agreed Price
- Commodity Type = Underlying = Product = Asset = Instrument
- Counterparty = Buyer = Seller = Client = Customer = Party

MARKET CONVENTIONS:
- Oil: Priced in USD per barrel (BBL), settled T+2
- Gas: Priced in USD per MMBtu, various delivery points
- Metals: Priced in USD per troy ounce (precious) or per metric ton (base)
- Agriculture: Priced in USD per bushel, seasonal delivery patterns

RECONCILIATION FOCUS:
- Prioritize quantity, price, delivery date, and commodity specification
- Understand that terminology varies significantly between counterparties
- Recognize that settlement terms can be physical or financial
- Account for location-specific delivery terms and quality specifications

When analyzing trades, focus on semantic equivalence rather than exact field name matching."""
    
    def _get_commodities_user_prompt(self) -> str:
        return """Analyze this commodities trade data for reconciliation:

Trade Data: {trade_data}

Please provide:
1. Transaction Type: Identify the specific commodity and trade structure
2. Critical Fields: List the most important fields for reconciliation
3. Field Mappings: Map non-standard field names to standard terminology
4. Context Analysis: Explain the trading context and any special considerations
5. Validation Rules: Specify validation rules specific to this commodity type

Focus on understanding the economic substance of the trade rather than exact field names.
Consider regional terminology variations and market-specific conventions."""
    
    def _get_commodities_examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "product": "Crude Oil WTI",
                    "volume": "1000",
                    "unit": "BBL",
                    "delivery_date": "2024-03-15",
                    "agreed_price": "75.50",
                    "seller": "ABC Trading LLC"
                },
                "output": {
                    "transaction_type": "crude_oil_forward",
                    "critical_fields": ["delivery_date", "volume", "agreed_price", "product"],
                    "field_mappings": {
                        "volume": "notional_quantity",
                        "agreed_price": "fixed_price",
                        "delivery_date": "settlement_date",
                        "product": "commodity_type",
                        "seller": "counterparty"
                    }
                }
            }
        ]
    
    def _get_commodities_validation(self) -> str:
        return """COMMODITIES VALIDATION RULES:
- Delivery date must be future date and align with market conventions
- Quantity must be positive and in standard units (BBL, MT, OZ, BUSHEL)
- Price must be positive and in appropriate currency (typically USD)
- Commodity type must be specific and recognizable
- Settlement type (physical/financial) must be specified
- Location/delivery point should be included for physical settlement"""
    
    def _get_fx_system_prompt(self) -> str:
        return """You are an expert in foreign exchange (FX) trading and OTC trade reconciliation. You have deep knowledge of:

FX EXPERTISE:
- Spot and forward FX markets
- Currency pair conventions and quotation methods
- Settlement cycles and market practices
- Cross-currency transactions and triangulation
- Regional FX market differences

KEY TERMINOLOGY UNDERSTANDING:
- Currency Pair = CCY Pair = FX Pair = Pair
- Exchange Rate = Rate = FX Rate = Spot Rate = Forward Rate
- Base Currency = Base CCY = Primary Currency = From Currency
- Quote Currency = Quote CCY = Counter Currency = To Currency
- Notional Amount = Amount = Size = Principal

MARKET CONVENTIONS:
- Major pairs: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD
- Standard settlement: T+2 for spot, custom for forwards
- Quotation: Base currency per quote currency (e.g., EUR/USD = 1.1000)
- Precision: Typically 4-6 decimal places depending on currency pair

RECONCILIATION FOCUS:
- Currency pair direction is critical (EUR/USD vs USD/EUR)
- Rate precision and rounding conventions
- Settlement date calculations and business day adjustments
- Notional amounts in both base and quote currencies

When analyzing FX trades, pay special attention to currency pair direction and rate quotation conventions."""
    
    def _get_fx_user_prompt(self) -> str:
        return """Analyze this FX trade data for reconciliation:

Trade Data: {trade_data}

Please provide:
1. Transaction Type: Identify spot, forward, or other FX structure
2. Critical Fields: List the most important fields for FX reconciliation
3. Field Mappings: Map non-standard field names to standard FX terminology
4. Currency Analysis: Analyze currency pair direction and rate quotation
5. Settlement Analysis: Determine settlement date and business day conventions

Pay special attention to currency pair conventions and rate quotation methods.
Consider that different systems may quote rates in opposite directions."""
    
    def _get_fx_examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "ccypair": "EURUSD",
                    "rate": "1.1050",
                    "amount": "1000000",
                    "base_ccy": "EUR",
                    "settlement": "2024-01-17"
                },
                "output": {
                    "transaction_type": "fx_spot",
                    "critical_fields": ["ccypair", "rate", "amount", "settlement"],
                    "field_mappings": {
                        "ccypair": "currency_pair",
                        "rate": "exchange_rate",
                        "amount": "notional_amount",
                        "settlement": "settlement_date"
                    }
                }
            }
        ]
    
    def _get_fx_validation(self) -> str:
        return """FX VALIDATION RULES:
- Currency pair must follow standard conventions (e.g., EURUSD not USDEUR for majors)
- Exchange rate must be positive and within reasonable market ranges
- Settlement date must account for currency-specific holidays
- Notional amount must be positive
- Both base and quote currency amounts should be calculable
- Rate precision should match market conventions for the currency pair"""
    
    def _get_rates_system_prompt(self) -> str:
        return """You are an expert in interest rate derivatives and OTC trade reconciliation. You have deep knowledge of:

RATES EXPERTISE:
- Interest rate swaps (IRS), basis swaps, overnight index swaps (OIS)
- Day count conventions and accrual calculations
- Payment frequencies and reset mechanisms
- Yield curve construction and rate interpolation
- Credit risk and collateral management

KEY TERMINOLOGY UNDERSTANDING:
- Interest Rate = Rate = Fixed Rate = Floating Rate = Coupon Rate
- Day Count Convention = Day Count = DCC = Accrual Basis = Day Basis
- Payment Frequency = Frequency = Payment Period = Coupon Frequency
- Notional Amount = Notional = Principal = Amount
- Effective Date = Start Date = Value Date
- Termination Date = Maturity Date = End Date

MARKET CONVENTIONS:
- USD: ACT/360, Quarterly payments, SOFR/LIBOR reference
- EUR: ACT/360, Annual payments, EURIBOR reference
- GBP: ACT/365, Semi-annual payments, SONIA reference
- Standard settlement: T+2 for spot starting swaps

RECONCILIATION FOCUS:
- Rate precision and rounding (typically 4-6 decimal places)
- Day count convention consistency
- Payment frequency alignment
- Reset and payment date calculations
- Notional amount and currency

When analyzing rates trades, focus on the economic terms and calculation methodologies."""
    
    def _get_rates_user_prompt(self) -> str:
        return """Analyze this interest rates trade data for reconciliation:

Trade Data: {trade_data}

Please provide:
1. Transaction Type: Identify the specific rates product (IRS, basis swap, OIS, etc.)
2. Critical Fields: List the most important fields for rates reconciliation
3. Field Mappings: Map non-standard field names to standard rates terminology
4. Rate Analysis: Analyze fixed/floating rate specifications and conventions
5. Schedule Analysis: Determine payment frequencies and calculation periods

Focus on the calculation methodology and market conventions for the specific rates product.
Consider that different systems may use different day count conventions or reference rates."""
    
    def _get_rates_examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "fixed_rate": "2.5000",
                    "floating_index": "USD-SOFR",
                    "notional": "10000000",
                    "start_date": "2024-01-15",
                    "maturity": "2029-01-15",
                    "pay_freq": "QUARTERLY"
                },
                "output": {
                    "transaction_type": "interest_rate_swap",
                    "critical_fields": ["fixed_rate", "floating_index", "notional", "start_date", "maturity"],
                    "field_mappings": {
                        "start_date": "effective_date",
                        "maturity": "termination_date",
                        "pay_freq": "payment_frequency",
                        "floating_index": "floating_rate_index"
                    }
                }
            }
        ]
    
    def _get_rates_validation(self) -> str:
        return """RATES VALIDATION RULES:
- Fixed rate must be positive and within reasonable market ranges
- Floating rate index must be valid and market-standard
- Effective date must be valid business date
- Termination date must be after effective date
- Payment frequency must align with market conventions
- Day count convention must be specified and appropriate for currency
- Notional amount must be positive"""
    
    def _get_derivatives_system_prompt(self) -> str:
        return """You are an expert in derivatives trading and OTC trade reconciliation. You have deep knowledge of:

DERIVATIVES EXPERTISE:
- Options (vanilla and exotic), futures, forwards, swaps
- Underlying asset specifications and market conventions
- Option pricing models and Greeks
- Exercise and settlement mechanisms
- Structured products and complex derivatives

KEY TERMINOLOGY UNDERSTANDING:
- Underlying Asset = Underlying = Reference Asset = Base Asset
- Option Type = Call/Put = Option Style = Exercise Type
- Strike Price = Strike = Exercise Price = Barrier Level
- Expiry Date = Expiration Date = Maturity Date = Exercise Date
- Premium = Option Premium = Cost = Price

MARKET CONVENTIONS:
- European vs American exercise styles
- Physical vs cash settlement
- Barrier levels and knock-in/knock-out features
- Volatility quotation conventions

RECONCILIATION FOCUS:
- Underlying asset specification and identification
- Strike price and barrier level precision
- Exercise style and settlement method
- Premium amount and payment date
- Expiry date and exercise provisions

When analyzing derivatives, focus on the specific terms that define the payoff structure."""
    
    def _get_derivatives_user_prompt(self) -> str:
        return """Analyze this derivatives trade data for reconciliation:

Trade Data: {trade_data}

Please provide:
1. Transaction Type: Identify the specific derivative structure
2. Critical Fields: List the most important fields for derivatives reconciliation
3. Field Mappings: Map non-standard field names to standard derivatives terminology
4. Payoff Analysis: Analyze the payoff structure and key terms
5. Settlement Analysis: Determine exercise and settlement provisions

Focus on the terms that define the derivative's payoff structure and exercise provisions.
Consider that derivatives terminology can vary significantly between different product types."""
    
    def _get_derivatives_examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "underlying": "AAPL",
                    "call_put": "CALL",
                    "strike": "150.00",
                    "expiry": "2024-03-15",
                    "premium": "5.25",
                    "style": "AMERICAN"
                },
                "output": {
                    "transaction_type": "equity_option",
                    "critical_fields": ["underlying", "call_put", "strike", "expiry", "premium"],
                    "field_mappings": {
                        "underlying": "underlying_asset",
                        "call_put": "option_type",
                        "strike": "strike_price",
                        "expiry": "expiry_date",
                        "style": "exercise_style"
                    }
                }
            }
        ]
    
    def _get_derivatives_validation(self) -> str:
        return """DERIVATIVES VALIDATION RULES:
- Underlying asset must be valid and identifiable
- Option type (call/put) must be specified for options
- Strike price must be positive for standard options
- Expiry date must be future date and valid business date
- Premium must be positive (for purchased options)
- Exercise style must be specified (European/American/Bermudan)
- Settlement method must be specified (physical/cash)"""
    
    def get_domain_prompt(self, asset_class: AssetClass, 
                         trading_context: Optional[TradingContext] = None,
                         operation: str = "analysis") -> Optional[PromptTemplate]:
        """
        Get domain-specific prompt template for given asset class and context.
        
        Args:
            asset_class: Asset class for the prompt
            trading_context: Trading context (optional)
            operation: Type of operation (analysis, matching, explanation)
            
        Returns:
            PromptTemplate if found, None otherwise
        """
        # Map asset class to prompt template key
        template_key = f"{asset_class.value}_{operation}"
        
        return self.prompt_templates.get(template_key)
    
    def generate_context_prompt(self, domain_context: DomainContext, 
                              trade_data: Dict[str, Any],
                              operation: str = "analysis") -> str:
        """
        Generate a context-aware prompt for AI analysis.
        
        Args:
            domain_context: Domain context information
            trade_data: Trade data to analyze
            operation: Type of operation
            
        Returns:
            Generated prompt string
        """
        template = self.get_domain_prompt(domain_context.asset_class, 
                                        domain_context.trading_context, 
                                        operation)
        
        if not template:
            return self._get_generic_prompt(trade_data, operation)
        
        # Format the user prompt with trade data
        user_prompt = template.user_prompt_template.format(trade_data=trade_data)
        
        # Combine system prompt and user prompt
        full_prompt = f"{template.system_prompt}\n\n{user_prompt}"
        
        # Add validation instructions
        if template.validation_instructions:
            full_prompt += f"\n\nVALIDATION REQUIREMENTS:\n{template.validation_instructions}"
        
        # Add relevant terminology mappings
        if domain_context.terminology_mappings:
            terminology_section = "\n\nRELEVANT TERMINOLOGY MAPPINGS:\n"
            for term, mapping in list(domain_context.terminology_mappings.items())[:10]:
                terminology_section += f"- {term} → {mapping.standard_term}\n"
            full_prompt += terminology_section
        
        # Add field priorities
        if domain_context.field_priorities:
            priority_section = "\n\nFIELD PRIORITIES (HIGH TO LOW):\n"
            for priority in domain_context.field_priorities[:10]:
                priority_section += f"- {priority.field_name} ({priority.criticality}): {priority.priority_score:.2f}\n"
            full_prompt += priority_section
        
        return full_prompt
    
    def _get_generic_prompt(self, trade_data: Dict[str, Any], operation: str) -> str:
        """Generate a generic prompt when no domain-specific template is available"""
        return f"""You are an expert in OTC trade reconciliation. Analyze this trade data:

Trade Data: {trade_data}

Please provide:
1. Transaction Type: Identify the trade structure and asset class
2. Critical Fields: List the most important fields for reconciliation
3. Field Mappings: Map non-standard field names to standard terminology
4. Context Analysis: Explain any special considerations for this trade type

Focus on understanding the economic substance and key reconciliation points."""
    
    def get_semantic_matching_prompt(self, field1: str, field2: str, 
                                   domain_context: DomainContext) -> str:
        """
        Generate prompt for semantic field matching.
        
        Args:
            field1: First field name
            field2: Second field name
            domain_context: Domain context
            
        Returns:
            Semantic matching prompt
        """
        asset_class_context = f"Asset Class: {domain_context.asset_class.value}"
        trading_context_context = f"Trading Context: {domain_context.trading_context.value}"
        
        # Get relevant terminology for this asset class
        relevant_terms = []
        for term, mapping in domain_context.terminology_mappings.items():
            if mapping.asset_class == domain_context.asset_class:
                relevant_terms.append(f"{term} → {mapping.standard_term}")
        
        terminology_context = "\n".join(relevant_terms[:15])  # Limit to avoid prompt bloat
        
        return f"""You are an expert in {domain_context.asset_class.value} trading terminology. 

{asset_class_context}
{trading_context_context}

RELEVANT TERMINOLOGY MAPPINGS:
{terminology_context}

Compare these two field names for semantic equivalence:
Field 1: "{field1}"
Field 2: "{field2}"

Consider:
1. Are these fields semantically equivalent in {domain_context.asset_class.value} trading?
2. Do they refer to the same economic concept or data point?
3. Are there market conventions that make these terms interchangeable?

Provide:
- similarity_score: Float between 0.0 and 1.0
- is_match: Boolean indicating if fields are semantically equivalent
- reasoning: Explanation of your assessment
- confidence: Your confidence in this assessment (0.0 to 1.0)

Focus on the economic meaning rather than exact string matching."""
    
    def get_mismatch_explanation_prompt(self, field_name: str, value1: Any, value2: Any,
                                      domain_context: DomainContext) -> str:
        """
        Generate prompt for explaining field mismatches.
        
        Args:
            field_name: Name of the mismatched field
            value1: First value
            value2: Second value
            domain_context: Domain context
            
        Returns:
            Mismatch explanation prompt
        """
        return f"""You are an expert in {domain_context.asset_class.value} trade reconciliation.

Asset Class: {domain_context.asset_class.value}
Trading Context: {domain_context.trading_context.value}
Field: {field_name}

Values to compare:
Value 1: {value1}
Value 2: {value2}

Provide a clear, business-friendly explanation of why these values don't match.
Consider:
1. Market conventions and tolerances for this field in {domain_context.asset_class.value}
2. Possible reasons for the discrepancy (rounding, timing, data source differences)
3. Whether this is a critical mismatch that requires investigation
4. Suggested next steps for resolution

Format your response as a clear explanation that a trade operations analyst would understand."""


# Global instance
domain_prompt_generator = DomainPromptGenerator()


def get_domain_prompt_generator() -> DomainPromptGenerator:
    """Get the global domain prompt generator instance"""
    return domain_prompt_generator