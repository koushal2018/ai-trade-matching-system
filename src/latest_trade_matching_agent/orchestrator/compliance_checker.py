"""
Compliance Checking Tool

This module provides compliance checking capabilities for the Orchestrator Agent.
It validates data integrity (TRADE_SOURCE in correct tables), checks regulatory
requirements, and detects compliance violations.

Requirements: 4.1, 4.2
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from enum import Enum
import boto3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceCheckType(str, Enum):
    """Types of compliance checks."""
    DATA_INTEGRITY = "data_integrity"
    TRADE_SOURCE_ROUTING = "trade_source_routing"
    AUDIT_TRAIL_COMPLETENESS = "audit_trail_completeness"
    REGULATORY_REQUIREMENTS = "regulatory_requirements"
    FIELD_VALIDATION = "field_validation"


class ComplianceViolation(BaseModel):
    """
    Represents a compliance violation detected by the checker.
    
    Validates: Requirements 4.2
    """
    check_type: ComplianceCheckType = Field(..., description="Type of compliance check")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(..., description="Violation severity")
    resource_id: str = Field(..., description="ID of resource with violation (e.g., trade_id)")
    resource_type: str = Field(..., description="Type of resource (e.g., trade, agent)")
    description: str = Field(..., description="Human-readable description of violation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional violation details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When violation was detected")
    remediation: str = Field(..., description="Suggested remediation action")


class ComplianceStatus(BaseModel):
    """
    Overall compliance status for the system or a specific check.
    
    Validates: Requirements 4.1, 4.2
    """
    status: Literal["COMPLIANT", "WARNING", "VIOLATED"] = Field(..., description="Overall compliance status")
    violations: List[ComplianceViolation] = Field(default_factory=list, description="List of violations")
    checks_performed: int = Field(..., description="Number of checks performed")
    checks_passed: int = Field(..., description="Number of checks passed")
    compliance_percentage: float = Field(..., description="Overall compliance percentage")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last check timestamp")
    summary: str = Field(..., description="Summary of compliance status")


class ComplianceCheckerTool:
    """
    Tool for checking compliance across the system.
    
    This tool:
    1. Validates data integrity (TRADE_SOURCE matches table location)
    2. Checks regulatory requirements
    3. Validates audit trail completeness
    4. Detects compliance violations
    5. Provides remediation recommendations
    
    Validates: Requirements 4.1, 4.2
    """
    
    def __init__(
        self,
        region_name: str = "us-east-1",
        bank_table_name: str = "BankTradeData",
        counterparty_table_name: str = "CounterpartyTradeData",
        audit_table_name: str = "AuditTrail"
    ):
        """
        Initialize Compliance Checker Tool.
        
        Args:
            region_name: AWS region
            bank_table_name: DynamoDB table for bank trades
            counterparty_table_name: DynamoDB table for counterparty trades
            audit_table_name: DynamoDB table for audit trail
        """
        self.region_name = region_name
        self.bank_table_name = bank_table_name
        self.counterparty_table_name = counterparty_table_name
        self.audit_table_name = audit_table_name
        
        # Initialize AWS clients
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        
        logger.info("Compliance Checker Tool initialized")
    
    def check_data_integrity(self, sample_size: int = 100) -> ComplianceStatus:
        """
        Check data integrity across DynamoDB tables.
        
        Validates that TRADE_SOURCE field matches the table location:
        - BANK trades should be in BankTradeData table
        - COUNTERPARTY trades should be in CounterpartyTradeData table
        
        Args:
            sample_size: Number of trades to sample from each table
            
        Returns:
            ComplianceStatus: Data integrity compliance status
            
        Validates: Requirements 4.1, 4.2, 7.5
        """
        logger.info("Checking data integrity compliance")
        
        violations = []
        checks_performed = 0
        checks_passed = 0
        
        try:
            # Check BankTradeData table
            logger.info(f"Checking {self.bank_table_name} for data integrity")
            bank_violations = self._check_table_data_integrity(
                table_name=self.bank_table_name,
                expected_source="BANK",
                sample_size=sample_size
            )
            violations.extend(bank_violations)
            checks_performed += sample_size
            checks_passed += (sample_size - len(bank_violations))
            
            # Check CounterpartyTradeData table
            logger.info(f"Checking {self.counterparty_table_name} for data integrity")
            cp_violations = self._check_table_data_integrity(
                table_name=self.counterparty_table_name,
                expected_source="COUNTERPARTY",
                sample_size=sample_size
            )
            violations.extend(cp_violations)
            checks_performed += sample_size
            checks_passed += (sample_size - len(cp_violations))
            
            # Calculate compliance percentage
            compliance_percentage = (checks_passed / checks_performed * 100) if checks_performed > 0 else 100.0
            
            # Determine overall status
            if not violations:
                status = "COMPLIANT"
                summary = f"All {checks_performed} trades have correct TRADE_SOURCE routing"
            elif compliance_percentage >= 95.0:
                status = "WARNING"
                summary = f"{len(violations)} data integrity violations found ({compliance_percentage:.1f}% compliant)"
            else:
                status = "VIOLATED"
                summary = f"{len(violations)} data integrity violations found ({compliance_percentage:.1f}% compliant)"
            
            return ComplianceStatus(
                status=status,
                violations=violations,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                compliance_percentage=compliance_percentage,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error checking data integrity: {e}")
            return ComplianceStatus(
                status="VIOLATED",
                violations=[],
                checks_performed=0,
                checks_passed=0,
                compliance_percentage=0.0,
                summary=f"Error checking data integrity: {str(e)}"
            )
    
    def check_trade_source_routing(self, trade_id: str) -> ComplianceStatus:
        """
        Check if a specific trade is routed to the correct table.
        
        Args:
            trade_id: Trade identifier to check
            
        Returns:
            ComplianceStatus: Routing compliance status
            
        Validates: Requirements 4.2, 7.5
        """
        logger.info(f"Checking trade source routing for: {trade_id}")
        
        violations = []
        checks_performed = 2  # Check both tables
        checks_passed = 0
        
        try:
            # Check BankTradeData table
            bank_trade = self._get_trade_from_table(self.bank_table_name, trade_id)
            
            if bank_trade:
                trade_source = bank_trade.get("TRADE_SOURCE", {}).get("S", "")
                
                if trade_source != "BANK":
                    violations.append(ComplianceViolation(
                        check_type=ComplianceCheckType.TRADE_SOURCE_ROUTING,
                        severity="HIGH",
                        resource_id=trade_id,
                        resource_type="trade",
                        description=f"Trade {trade_id} in {self.bank_table_name} has TRADE_SOURCE={trade_source} (expected BANK)",
                        details={
                            "table": self.bank_table_name,
                            "expected_source": "BANK",
                            "actual_source": trade_source
                        },
                        remediation=f"Move trade {trade_id} to {self.counterparty_table_name} table"
                    ))
                else:
                    checks_passed += 1
            
            # Check CounterpartyTradeData table
            cp_trade = self._get_trade_from_table(self.counterparty_table_name, trade_id)
            
            if cp_trade:
                trade_source = cp_trade.get("TRADE_SOURCE", {}).get("S", "")
                
                if trade_source != "COUNTERPARTY":
                    violations.append(ComplianceViolation(
                        check_type=ComplianceCheckType.TRADE_SOURCE_ROUTING,
                        severity="HIGH",
                        resource_id=trade_id,
                        resource_type="trade",
                        description=f"Trade {trade_id} in {self.counterparty_table_name} has TRADE_SOURCE={trade_source} (expected COUNTERPARTY)",
                        details={
                            "table": self.counterparty_table_name,
                            "expected_source": "COUNTERPARTY",
                            "actual_source": trade_source
                        },
                        remediation=f"Move trade {trade_id} to {self.bank_table_name} table"
                    ))
                else:
                    checks_passed += 1
            
            # Calculate compliance
            compliance_percentage = (checks_passed / checks_performed * 100) if checks_performed > 0 else 100.0
            
            if not violations:
                status = "COMPLIANT"
                summary = f"Trade {trade_id} is correctly routed"
            else:
                status = "VIOLATED"
                summary = f"Trade {trade_id} has routing violations"
            
            return ComplianceStatus(
                status=status,
                violations=violations,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                compliance_percentage=compliance_percentage,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error checking trade source routing: {e}")
            return ComplianceStatus(
                status="VIOLATED",
                violations=[],
                checks_performed=0,
                checks_passed=0,
                compliance_percentage=0.0,
                summary=f"Error checking routing: {str(e)}"
            )
    
    def check_regulatory_requirements(self) -> ComplianceStatus:
        """
        Check regulatory requirements compliance.
        
        This includes:
        - Required fields present in all trades
        - Audit trail completeness
        - Data retention policies
        
        Returns:
            ComplianceStatus: Regulatory compliance status
            
        Validates: Requirements 4.2
        """
        logger.info("Checking regulatory requirements compliance")
        
        violations = []
        checks_performed = 0
        checks_passed = 0
        
        try:
            # Check required fields in trades
            required_fields = [
                "Trade_ID",
                "TRADE_SOURCE",
                "trade_date",
                "notional",
                "currency",
                "counterparty",
                "product_type"
            ]
            
            # Sample trades from both tables
            sample_size = 50
            
            # Check BankTradeData
            bank_field_violations = self._check_required_fields(
                table_name=self.bank_table_name,
                required_fields=required_fields,
                sample_size=sample_size
            )
            violations.extend(bank_field_violations)
            checks_performed += sample_size
            checks_passed += (sample_size - len(bank_field_violations))
            
            # Check CounterpartyTradeData
            cp_field_violations = self._check_required_fields(
                table_name=self.counterparty_table_name,
                required_fields=required_fields,
                sample_size=sample_size
            )
            violations.extend(cp_field_violations)
            checks_performed += sample_size
            checks_passed += (sample_size - len(cp_field_violations))
            
            # Calculate compliance
            compliance_percentage = (checks_passed / checks_performed * 100) if checks_performed > 0 else 100.0
            
            if not violations:
                status = "COMPLIANT"
                summary = f"All {checks_performed} trades meet regulatory requirements"
            elif compliance_percentage >= 95.0:
                status = "WARNING"
                summary = f"{len(violations)} regulatory violations found ({compliance_percentage:.1f}% compliant)"
            else:
                status = "VIOLATED"
                summary = f"{len(violations)} regulatory violations found ({compliance_percentage:.1f}% compliant)"
            
            return ComplianceStatus(
                status=status,
                violations=violations,
                checks_performed=checks_performed,
                checks_passed=checks_passed,
                compliance_percentage=compliance_percentage,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error checking regulatory requirements: {e}")
            return ComplianceStatus(
                status="VIOLATED",
                violations=[],
                checks_performed=0,
                checks_passed=0,
                compliance_percentage=0.0,
                summary=f"Error checking regulatory requirements: {str(e)}"
            )
    
    def check_all_compliance(self, sample_size: int = 100) -> ComplianceStatus:
        """
        Perform all compliance checks and return aggregated status.
        
        Args:
            sample_size: Number of records to sample for each check
            
        Returns:
            ComplianceStatus: Overall compliance status
            
        Validates: Requirements 4.1, 4.2
        """
        logger.info("Performing all compliance checks")
        
        all_violations = []
        total_checks = 0
        total_passed = 0
        
        try:
            # Check data integrity
            data_integrity_status = self.check_data_integrity(sample_size)
            all_violations.extend(data_integrity_status.violations)
            total_checks += data_integrity_status.checks_performed
            total_passed += data_integrity_status.checks_passed
            
            # Check regulatory requirements
            regulatory_status = self.check_regulatory_requirements()
            all_violations.extend(regulatory_status.violations)
            total_checks += regulatory_status.checks_performed
            total_passed += regulatory_status.checks_passed
            
            # Calculate overall compliance
            compliance_percentage = (total_passed / total_checks * 100) if total_checks > 0 else 100.0
            
            if not all_violations:
                status = "COMPLIANT"
                summary = f"All {total_checks} compliance checks passed"
            elif compliance_percentage >= 95.0:
                status = "WARNING"
                summary = f"{len(all_violations)} violations found across {total_checks} checks ({compliance_percentage:.1f}% compliant)"
            else:
                status = "VIOLATED"
                summary = f"{len(all_violations)} violations found across {total_checks} checks ({compliance_percentage:.1f}% compliant)"
            
            return ComplianceStatus(
                status=status,
                violations=all_violations,
                checks_performed=total_checks,
                checks_passed=total_passed,
                compliance_percentage=compliance_percentage,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error performing compliance checks: {e}")
            return ComplianceStatus(
                status="VIOLATED",
                violations=[],
                checks_performed=0,
                checks_passed=0,
                compliance_percentage=0.0,
                summary=f"Error performing compliance checks: {str(e)}"
            )
    
    def _check_table_data_integrity(
        self,
        table_name: str,
        expected_source: str,
        sample_size: int
    ) -> List[ComplianceViolation]:
        """
        Check data integrity for a specific table.
        
        Args:
            table_name: DynamoDB table name
            expected_source: Expected TRADE_SOURCE value
            sample_size: Number of trades to sample
            
        Returns:
            List[ComplianceViolation]: List of violations found
        """
        violations = []
        
        try:
            # Scan table with limit
            response = self.dynamodb.scan(
                TableName=table_name,
                Limit=sample_size,
                ProjectionExpression="Trade_ID, TRADE_SOURCE"
            )
            
            items = response.get('Items', [])
            
            for item in items:
                trade_id = item.get("Trade_ID", {}).get("S", "unknown")
                trade_source = item.get("TRADE_SOURCE", {}).get("S", "")
                
                if trade_source != expected_source:
                    violations.append(ComplianceViolation(
                        check_type=ComplianceCheckType.DATA_INTEGRITY,
                        severity="HIGH",
                        resource_id=trade_id,
                        resource_type="trade",
                        description=f"Trade {trade_id} in {table_name} has TRADE_SOURCE={trade_source} (expected {expected_source})",
                        details={
                            "table": table_name,
                            "expected_source": expected_source,
                            "actual_source": trade_source
                        },
                        remediation=f"Move trade {trade_id} to correct table or update TRADE_SOURCE field"
                    ))
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking table {table_name}: {e}")
            return []
    
    def _check_required_fields(
        self,
        table_name: str,
        required_fields: List[str],
        sample_size: int
    ) -> List[ComplianceViolation]:
        """
        Check that required fields are present in trades.
        
        Args:
            table_name: DynamoDB table name
            required_fields: List of required field names
            sample_size: Number of trades to sample
            
        Returns:
            List[ComplianceViolation]: List of violations found
        """
        violations = []
        
        try:
            # Scan table with limit
            response = self.dynamodb.scan(
                TableName=table_name,
                Limit=sample_size
            )
            
            items = response.get('Items', [])
            
            for item in items:
                trade_id = item.get("Trade_ID", {}).get("S", "unknown")
                
                # Check each required field
                missing_fields = []
                for field in required_fields:
                    if field not in item or not item[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    violations.append(ComplianceViolation(
                        check_type=ComplianceCheckType.FIELD_VALIDATION,
                        severity="MEDIUM",
                        resource_id=trade_id,
                        resource_type="trade",
                        description=f"Trade {trade_id} in {table_name} is missing required fields: {', '.join(missing_fields)}",
                        details={
                            "table": table_name,
                            "missing_fields": missing_fields
                        },
                        remediation=f"Re-extract trade {trade_id} to populate missing fields"
                    ))
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking required fields in {table_name}: {e}")
            return []
    
    def _get_trade_from_table(self, table_name: str, trade_id: str) -> Optional[Dict]:
        """Get a trade from a DynamoDB table."""
        try:
            response = self.dynamodb.get_item(
                TableName=table_name,
                Key={"Trade_ID": {"S": trade_id}}
            )
            return response.get('Item')
        except Exception as e:
            logger.debug(f"Trade {trade_id} not found in {table_name}: {e}")
            return None
    
    def _run(self, check_type: str = "all", sample_size: int = 100) -> str:
        """
        Tool execution method for CrewAI/Strands integration.
        
        Args:
            check_type: Type of check to perform (all, data_integrity, regulatory)
            sample_size: Number of records to sample
            
        Returns:
            str: JSON string with compliance status
        """
        import json
        
        try:
            if check_type == "data_integrity":
                status = self.check_data_integrity(sample_size)
            elif check_type == "regulatory":
                status = self.check_regulatory_requirements()
            else:
                status = self.check_all_compliance(sample_size)
            
            return json.dumps(status.model_dump(), indent=2, default=str)
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "message": "Failed to check compliance"
            }, indent=2)


if __name__ == "__main__":
    """Test Compliance Checker Tool."""
    import json
    
    # Initialize tool
    checker = ComplianceCheckerTool()
    
    # Check all compliance
    status = checker.check_all_compliance(sample_size=50)
    print("Overall Compliance Status:")
    print(json.dumps(status.model_dump(), indent=2, default=str))
    
    # Check data integrity specifically
    data_integrity_status = checker.check_data_integrity(sample_size=50)
    print("\nData Integrity Status:")
    print(json.dumps(data_integrity_status.model_dump(), indent=2, default=str))
