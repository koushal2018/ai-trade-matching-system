# Security Policy

## Supported Versions

We actively support the following versions of the AI Trade Matching System:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Create Public Issues

**Please do not report security vulnerabilities through public GitHub issues.** This could expose the vulnerability to malicious actors.

### 2. Report Privately

Send security reports to the project maintainers through one of these methods:

- **GitHub Security Advisories**: Use the "Report a vulnerability" button in the Security tab
- **Direct Contact**: Contact maintainers directly through GitHub with "SECURITY" in the subject line

### 3. Include Detailed Information

When reporting a vulnerability, please include:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** and attack scenarios
- **Affected versions** of the software
- **Suggested fix** (if you have one)
- **Your contact information** for follow-up questions

### 4. Response Timeline

We will acknowledge receipt of your vulnerability report within **48 hours** and provide a detailed response within **7 days** indicating:

- Confirmation of the vulnerability
- Our assessment of the impact
- Timeline for a fix
- Any workarounds or mitigations

## Security Considerations

### AWS Security

This system processes financial documents and requires careful security configuration:

#### IAM Permissions

- **Principle of Least Privilege**: Grant only necessary permissions
- **Role-Based Access**: Use IAM roles instead of access keys when possible
- **Regular Audits**: Review and rotate credentials regularly
- **AgentCore Runtime Roles**: Use separate execution roles for agent runtime

**Trade Matching System Permissions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockModelAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
      ]
    },
    {
      "Sid": "S3TradeDocumentAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::trade-matching-system-agentcore-production/BANK/*",
        "arn:aws:s3:::trade-matching-system-agentcore-production/COUNTERPARTY/*",
        "arn:aws:s3:::trade-matching-system-agentcore-production/extracted/*",
        "arn:aws:s3:::trade-matching-system-agentcore-production/reports/*"
      ]
    },
    {
      "Sid": "DynamoDBTradeDataAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/BankTradeData",
        "arn:aws:dynamodb:us-east-1:*:table/CounterpartyTradeData",
        "arn:aws:dynamodb:us-east-1:*:table/ExceptionsTable",
        "arn:aws:dynamodb:us-east-1:*:table/AgentRegistry",
        "arn:aws:dynamodb:us-east-1:*:table/HITLReviews",
        "arn:aws:dynamodb:us-east-1:*:table/AuditTrail"
      ]
    },
    {
      "Sid": "AgentCoreRuntimeAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgent",
        "bedrock-agentcore:GetAgentRuntime",
        "bedrock-agentcore:ListAgentRuntimes"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-east-1:*:agent-runtime/pdf-adapter-*",
        "arn:aws:bedrock-agentcore:us-east-1:*:agent-runtime/trade-extraction-*",
        "arn:aws:bedrock-agentcore:us-east-1:*:agent-runtime/trade-matching-*",
        "arn:aws:bedrock-agentcore:us-east-1:*:agent-runtime/exception-management-*",
        "arn:aws:bedrock-agentcore:us-east-1:*:agent-runtime/orchestrator-*"
      ]
    }
  ]
}
```

**AgentCore VPC Security Conditions:**

```json
{
  "Sid": "EnforceVPCAgentCore",
  "Action": [
    "bedrock-agentcore:CreateAgentRuntime",
    "bedrock-agentcore:UpdateAgentRuntime"
  ],
  "Effect": "Deny",
  "Resource": "*",
  "Condition": {
    "Null": {
      "bedrock-agentcore:Subnets": "true",
      "bedrock-agentcore:SecurityGroups": "true"
    }
  }
}
```

#### Data Encryption

- **S3 Encryption**: Enable server-side encryption (SSE-S3 or SSE-KMS)
- **DynamoDB Encryption**: Enable encryption at rest
- **Transit Encryption**: All AWS API calls use HTTPS/TLS

#### Network Security

- **VPC Configuration**: Deploy AgentCore Runtime in private subnets when possible
- **Security Groups**: Restrict access to necessary ports only
- **NAT Gateway**: Use NAT Gateway for outbound internet access
- **AgentCore VPC Isolation**: Use VPC condition keys to enforce network isolation
- **Agent Communication**: Secure inter-agent communication within VPC boundaries

### Data Privacy

#### Sensitive Data Handling

- **PII Redaction**: Automatically redact personally identifiable information
- **Data Retention**: Implement data retention policies
- **Access Logging**: Log all data access for audit trails

#### Financial Data Security

- **Trade Data**: Treat all trade information as confidential
- **Counterparty Information**: Protect counterparty identities
- **Audit Trails**: Maintain comprehensive audit logs
- **Agent Processing**: Ensure agents process financial data in secure, isolated environments
- **Data Classification**: Classify BANK vs COUNTERPARTY data with appropriate access controls
- **Matching Integrity**: Protect trade matching algorithms from manipulation

### Application Security

#### Input Validation

- **PDF Validation**: Validate PDF files before processing
- **Parameter Sanitization**: Sanitize all input parameters
- **File Size Limits**: Enforce reasonable file size limits

#### Authentication & Authorization

- **API Authentication**: Implement proper API authentication
- **Role-Based Access Control**: Implement RBAC for different user types
- **Session Management**: Secure session handling for web interface

#### Secure Coding Practices

- **Dependency Management**: Keep dependencies updated
- **Error Handling**: Don't expose sensitive information in errors
- **Logging**: Log security events without exposing sensitive data

### Infrastructure Security

#### Terraform Security

- **State File Security**: Secure Terraform state files
- **Variable Management**: Use secure variable management
- **Resource Tagging**: Tag resources for security tracking

#### Monitoring & Alerting

- **CloudWatch Alarms**: Set up security-related alarms
- **AWS CloudTrail**: Enable CloudTrail for API logging
- **VPC Flow Logs**: Monitor network traffic
- **AgentCore Observability**: Enable comprehensive agent monitoring and tracing
- **Agent Health Monitoring**: Track agent performance and security metrics
- **Anomaly Detection**: Monitor for unusual agent behavior or processing patterns

## Security Best Practices

### For Developers

1. **Code Reviews**: All code changes require security review
2. **Dependency Scanning**: Regularly scan dependencies for vulnerabilities
3. **Static Analysis**: Use static analysis tools (bandit, semgrep)
4. **Secrets Management**: Never commit secrets to version control

### For Operators

1. **Regular Updates**: Keep all components updated
2. **Access Reviews**: Regularly review user access
3. **Backup Security**: Secure backup procedures
4. **Incident Response**: Have an incident response plan

### For Users

1. **Credential Security**: Protect AWS credentials
2. **Network Security**: Use secure networks for access
3. **Data Classification**: Properly classify and handle data
4. **Reporting**: Report suspicious activity immediately

## Vulnerability Disclosure Process

### Internal Process

1. **Triage**: Security team triages the report within 24 hours
2. **Investigation**: Technical investigation and impact assessment
3. **Fix Development**: Develop and test security fix
4. **Coordinated Disclosure**: Coordinate with reporter on disclosure timeline
5. **Release**: Release security update with advisory

### Public Disclosure

- **Security Advisories**: Published through GitHub Security Advisories
- **CVE Assignment**: Request CVE for significant vulnerabilities
- **Release Notes**: Include security fixes in release notes
- **Documentation**: Update security documentation as needed

## Security Tools and Resources

### Recommended Tools

- **AWS Security Hub**: Centralized security findings
- **AWS Config**: Configuration compliance monitoring
- **AWS GuardDuty**: Threat detection service
- **AWS Inspector**: Application security assessment

### Security Scanning

```bash
# Dependency vulnerability scanning
pip-audit

# Static code analysis
bandit -r src/

# Container scanning (if using containers)
docker scan your-image:tag

# Infrastructure scanning
checkov -f terraform/
```

### Security Testing

```bash
# Run security tests
pytest tests/security/ -v

# Check for secrets in code
detect-secrets scan --all-files

# License compliance
pip-licenses --format=table
```

## Compliance

### Standards

This project aims to comply with:

- **SOC 2 Type II**: Security, availability, and confidentiality
- **ISO 27001**: Information security management
- **PCI DSS**: Payment card industry standards (where applicable)

### Audit Support

We maintain documentation and logs to support security audits:

- **Access Logs**: All system access is logged
- **Change Logs**: All configuration changes are tracked
- **Security Controls**: Documentation of implemented controls

## Contact Information

For security-related questions or concerns:

- **Security Issues**: Use GitHub Security Advisories
- **General Security Questions**: Create a GitHub Discussion with "security" tag
- **Urgent Security Matters**: Contact maintainers directly

## Acknowledgments

We appreciate security researchers and the community for helping keep this project secure. Security contributors will be acknowledged in our security advisories (with permission).

---

**Remember**: Security is everyone's responsibility. When in doubt, err on the side of caution and report potential issues.