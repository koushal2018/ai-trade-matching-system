#!/usr/bin/env python3
"""
Security audit script for Trade Matching System
Checks security configurations, IAM policies, and compliance requirements
"""

import boto3
import json
import os
import logging
from datetime import datetime
import subprocess
import requests
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security/security_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityAuditor:
    def __init__(self, aws_region='us-east-1'):
        self.aws_region = aws_region
        self.iam_client = boto3.client('iam')
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=aws_region)
        self.sts_client = boto3.client('sts')

    def get_current_identity(self):
        """Get current AWS identity"""
        try:
            identity = self.sts_client.get_caller_identity()
            logger.info(f"🔐 Current AWS Identity: {identity['Arn']}")
            return identity
        except Exception as e:
            logger.error(f"❌ Failed to get AWS identity: {e}")
            return None

    def audit_iam_permissions(self):
        """Audit IAM permissions and policies"""
        findings = []

        try:
            # Get current user/role
            identity = self.get_current_identity()
            if not identity:
                return [{"severity": "HIGH", "finding": "Cannot determine current AWS identity"}]

            # Check if using IAM user vs role
            arn = identity['Arn']
            if ':user/' in arn:
                logger.warning("🚨 Using IAM User instead of IAM Role - consider using roles for better security")
                findings.append({
                    "severity": "MEDIUM",
                    "finding": "Using IAM User instead of IAM Role",
                    "recommendation": "Use IAM Roles with temporary credentials for better security"
                })

            # Check attached policies (if IAM user)
            if ':user/' in arn:
                username = arn.split('/')[-1]
                try:
                    user_policies = self.iam_client.list_attached_user_policies(UserName=username)
                    inline_policies = self.iam_client.list_user_policies(UserName=username)

                    logger.info(f"📋 Attached Policies: {len(user_policies['AttachedPolicies'])}")
                    logger.info(f"📋 Inline Policies: {len(inline_policies['PolicyNames'])}")

                    # Check for overly permissive policies
                    for policy in user_policies['AttachedPolicies']:
                        if 'Admin' in policy['PolicyName'] or 'FullAccess' in policy['PolicyName']:
                            findings.append({
                                "severity": "HIGH",
                                "finding": f"Overly permissive policy attached: {policy['PolicyName']}",
                                "recommendation": "Use least privilege principle - grant only necessary permissions"
                            })

                except Exception as e:
                    logger.error(f"❌ Failed to check IAM policies: {e}")
                    findings.append({
                        "severity": "MEDIUM",
                        "finding": f"Cannot audit IAM policies: {e}"
                    })

            return findings

        except Exception as e:
            logger.error(f"❌ IAM audit failed: {e}")
            return [{"severity": "HIGH", "finding": f"IAM audit failed: {e}"}]

    def audit_s3_security(self, bucket_name='fab-otc-reconciliation-deployment'):
        """Audit S3 bucket security"""
        findings = []

        try:
            # Check bucket policy
            try:
                bucket_policy = self.s3_client.get_bucket_policy(Bucket=bucket_name)
                policy_doc = json.loads(bucket_policy['Policy'])
                logger.info("📋 S3 Bucket has custom policy")

                # Check for public access
                for statement in policy_doc.get('Statement', []):
                    if statement.get('Principal') == '*':
                        findings.append({
                            "severity": "HIGH",
                            "finding": "S3 bucket policy allows public access",
                            "recommendation": "Restrict bucket access to specific principals"
                        })

            except self.s3_client.exceptions.NoSuchBucketPolicy:
                logger.info("📋 S3 Bucket has no custom policy")

            # Check bucket encryption
            try:
                encryption = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
                encryption_config = encryption['ServerSideEncryptionConfiguration']
                logger.info("✅ S3 Bucket encryption is configured")

                # Check encryption type
                for rule in encryption_config.get('Rules', []):
                    sse_config = rule.get('ApplyServerSideEncryptionByDefault', {})
                    if sse_config.get('SSEAlgorithm') == 'AES256':
                        findings.append({
                            "severity": "MEDIUM",
                            "finding": "S3 bucket using AES256 encryption instead of KMS",
                            "recommendation": "Consider using KMS encryption for better key management"
                        })

            except self.s3_client.exceptions.NoSuchBucket:
                findings.append({
                    "severity": "HIGH",
                    "finding": f"S3 bucket {bucket_name} does not exist"
                })
            except Exception as e:
                if 'ServerSideEncryptionConfigurationNotFoundError' in str(e):
                    findings.append({
                        "severity": "HIGH",
                        "finding": "S3 bucket does not have encryption configured",
                        "recommendation": "Enable server-side encryption for data at rest"
                    })
                else:
                    logger.error(f"❌ Failed to check S3 encryption: {e}")

            # Check public access block
            try:
                public_access = self.s3_client.get_public_access_block(Bucket=bucket_name)
                block_config = public_access['PublicAccessBlockConfiguration']

                security_settings = [
                    'BlockPublicAcls',
                    'IgnorePublicAcls',
                    'BlockPublicPolicy',
                    'RestrictPublicBuckets'
                ]

                for setting in security_settings:
                    if not block_config.get(setting, False):
                        findings.append({
                            "severity": "HIGH",
                            "finding": f"S3 public access setting {setting} is not enabled",
                            "recommendation": "Enable all public access block settings"
                        })

            except Exception as e:
                logger.error(f"❌ Failed to check S3 public access block: {e}")
                findings.append({
                    "severity": "MEDIUM",
                    "finding": "Cannot check S3 public access block settings"
                })

            return findings

        except Exception as e:
            logger.error(f"❌ S3 security audit failed: {e}")
            return [{"severity": "HIGH", "finding": f"S3 security audit failed: {e}"}]

    def audit_dynamodb_security(self):
        """Audit DynamoDB security"""
        findings = []
        tables = ['BankTradeData', 'CounterpartyTradeData']

        for table_name in tables:
            try:
                # Check encryption at rest
                table_info = self.dynamodb_client.describe_table(TableName=table_name)
                table_details = table_info['Table']

                sse_description = table_details.get('SSEDescription')
                if sse_description:
                    sse_status = sse_description.get('Status')
                    if sse_status == 'ENABLED':
                        logger.info(f"✅ DynamoDB table {table_name} has encryption enabled")
                    else:
                        findings.append({
                            "severity": "HIGH",
                            "finding": f"DynamoDB table {table_name} encryption is not enabled",
                            "recommendation": "Enable encryption at rest for DynamoDB tables"
                        })
                else:
                    findings.append({
                        "severity": "HIGH",
                        "finding": f"DynamoDB table {table_name} has no encryption configuration",
                        "recommendation": "Enable encryption at rest for DynamoDB tables"
                    })

                # Check point-in-time recovery
                try:
                    pitr = self.dynamodb_client.describe_continuous_backups(TableName=table_name)
                    pitr_status = pitr['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus']

                    if pitr_status == 'ENABLED':
                        logger.info(f"✅ DynamoDB table {table_name} has point-in-time recovery enabled")
                    else:
                        findings.append({
                            "severity": "MEDIUM",
                            "finding": f"DynamoDB table {table_name} does not have point-in-time recovery enabled",
                            "recommendation": "Enable point-in-time recovery for data protection"
                        })

                except Exception as e:
                    logger.error(f"❌ Failed to check PITR for {table_name}: {e}")

            except Exception as e:
                logger.error(f"❌ Failed to audit DynamoDB table {table_name}: {e}")
                findings.append({
                    "severity": "HIGH",
                    "finding": f"Failed to audit DynamoDB table {table_name}: {e}"
                })

        return findings

    def audit_api_security(self, api_url='http://localhost:8080'):
        """Audit API security"""
        findings = []

        try:
            # Check HTTPS
            if api_url.startswith('http://'):
                findings.append({
                    "severity": "HIGH",
                    "finding": "API is not using HTTPS",
                    "recommendation": "Use HTTPS for all API communications"
                })

            # Check for security headers
            try:
                response = requests.get(f"{api_url}/health", timeout=10)
                headers = response.headers

                security_headers = {
                    'X-Frame-Options': 'Clickjacking protection',
                    'X-Content-Type-Options': 'MIME type sniffing protection',
                    'X-XSS-Protection': 'XSS protection',
                    'Strict-Transport-Security': 'HTTPS enforcement',
                    'Content-Security-Policy': 'Content injection protection'
                }

                for header, description in security_headers.items():
                    if header not in headers:
                        findings.append({
                            "severity": "MEDIUM",
                            "finding": f"Missing security header: {header}",
                            "recommendation": f"Add {header} header for {description}"
                        })

                # Check for sensitive information exposure
                response_text = response.text.lower()
                sensitive_patterns = ['password', 'key', 'secret', 'token', 'credential']

                for pattern in sensitive_patterns:
                    if pattern in response_text:
                        findings.append({
                            "severity": "HIGH",
                            "finding": f"Potential sensitive information exposure: {pattern}",
                            "recommendation": "Remove sensitive information from API responses"
                        })

            except Exception as e:
                findings.append({
                    "severity": "MEDIUM",
                    "finding": f"Cannot check API security headers: {e}"
                })

        except Exception as e:
            logger.error(f"❌ API security audit failed: {e}")
            findings.append({
                "severity": "HIGH",
                "finding": f"API security audit failed: {e}"
            })

        return findings

    def check_environment_security(self):
        """Check environment and configuration security"""
        findings = []

        # Check for hardcoded secrets in environment
        env_vars = os.environ
        sensitive_patterns = ['password', 'key', 'secret', 'token', 'credential']

        for var_name, var_value in env_vars.items():
            var_name_lower = var_name.lower()
            for pattern in sensitive_patterns:
                if pattern in var_name_lower and var_value:
                    # Don't log the actual value
                    findings.append({
                        "severity": "HIGH",
                        "finding": f"Potentially sensitive environment variable: {var_name}",
                        "recommendation": "Use secure parameter store or secrets manager for sensitive values"
                    })

        # Check file permissions
        sensitive_files = [
            '~/.aws/credentials',
            '~/.aws/config',
            '.env',
            'terraform/terraform.tfvars'
        ]

        for file_path in sensitive_files:
            expanded_path = os.path.expanduser(file_path)
            if os.path.exists(expanded_path):
                try:
                    stat_info = os.stat(expanded_path)
                    permissions = oct(stat_info.st_mode)[-3:]

                    if permissions != '600':
                        findings.append({
                            "severity": "MEDIUM",
                            "finding": f"File {file_path} has overly permissive permissions: {permissions}",
                            "recommendation": "Set file permissions to 600 for sensitive files"
                        })

                except Exception as e:
                    logger.error(f"❌ Failed to check permissions for {file_path}: {e}")

        return findings

    def generate_compliance_report(self):
        """Generate comprehensive compliance report"""
        logger.info("🔒 Starting comprehensive security audit...")

        audit_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'auditor': 'Trade Matching System Security Auditor',
            'scope': 'Infrastructure, API, and Configuration Security',
            'findings': {
                'iam': self.audit_iam_permissions(),
                's3': self.audit_s3_security(),
                'dynamodb': self.audit_dynamodb_security(),
                'api': self.audit_api_security(),
                'environment': self.check_environment_security()
            }
        }

        # Categorize findings by severity
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        all_findings = []

        for category, findings in audit_results['findings'].items():
            for finding in findings:
                all_findings.append({**finding, 'category': category})
                severity_counts[finding['severity']] += 1

        audit_results['summary'] = {
            'total_findings': len(all_findings),
            'high_severity': severity_counts['HIGH'],
            'medium_severity': severity_counts['MEDIUM'],
            'low_severity': severity_counts['LOW'],
            'overall_score': self.calculate_security_score(severity_counts, len(all_findings))
        }

        # Save results
        with open('security/security_audit_results.json', 'w') as f:
            json.dump(audit_results, f, indent=2)

        # Generate summary
        self.print_security_summary(audit_results)

        return audit_results

    def calculate_security_score(self, severity_counts, total_findings):
        """Calculate security score (0-100)"""
        if total_findings == 0:
            return 100

        # Weight different severities
        penalty = (severity_counts['HIGH'] * 10) + (severity_counts['MEDIUM'] * 5) + (severity_counts['LOW'] * 1)
        max_possible_penalty = total_findings * 10

        score = max(0, 100 - (penalty / max_possible_penalty * 100))
        return round(score, 1)

    def print_security_summary(self, audit_results):
        """Print security audit summary"""
        summary = audit_results['summary']

        print("\n" + "="*80)
        print("🔒 SECURITY AUDIT SUMMARY")
        print("="*80)
        print(f"📊 Overall Security Score: {summary['overall_score']}/100")
        print(f"🔍 Total Findings: {summary['total_findings']}")
        print(f"🚨 High Severity: {summary['high_severity']}")
        print(f"⚠️  Medium Severity: {summary['medium_severity']}")
        print(f"ℹ️  Low Severity: {summary['low_severity']}")

        if summary['high_severity'] > 0:
            print("\n🚨 CRITICAL ISSUES - Immediate Action Required:")
            for category, findings in audit_results['findings'].items():
                for finding in findings:
                    if finding['severity'] == 'HIGH':
                        print(f"   • [{category.upper()}] {finding['finding']}")
                        if 'recommendation' in finding:
                            print(f"     → {finding['recommendation']}")

        score = summary['overall_score']
        if score >= 90:
            status = "🟢 EXCELLENT"
        elif score >= 75:
            status = "🟡 GOOD"
        elif score >= 60:
            status = "🟠 NEEDS IMPROVEMENT"
        else:
            status = "🔴 CRITICAL"

        print(f"\n🏆 Security Status: {status}")
        print("="*80)

def main():
    # Create security directory if it doesn't exist
    os.makedirs('security', exist_ok=True)

    auditor = SecurityAuditor()
    results = auditor.generate_compliance_report()

    return results

if __name__ == "__main__":
    main()