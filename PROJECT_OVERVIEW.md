# AI Trade Matching System

## Description

The AI Trade Matching System is an intelligent, cloud-native platform that automates the complex process of trade reconciliation between financial institutions and their counterparties. Built on AWS infrastructure with advanced AI capabilities, the system processes trade confirmations from multiple sources, extracts structured data using machine learning, and performs intelligent matching to identify discrepancies and exceptions.

The platform leverages Amazon Bedrock's Claude AI models for document processing and natural language understanding, combined with sophisticated matching algorithms to handle the nuances of financial trade data. It features a comprehensive web portal for real-time monitoring, human-in-the-loop (HITL) review workflows, and detailed audit trails to ensure regulatory compliance.

Key components include:
- **AI-Powered Document Processing**: Automated extraction of trade data from PDF confirmations using computer vision and NLP
- **Intelligent Trade Matching**: Advanced algorithms with configurable similarity weights and tolerance thresholds
- **Exception Management**: Automated routing and escalation of unmatched trades with severity classification
- **Real-Time Monitoring**: Interactive dashboard with live metrics, agent health monitoring, and processing status
- **Audit & Compliance**: Comprehensive logging, audit trails, and regulatory reporting capabilities

## Customer Value Description

### Why This Matters for Financial Institutions

**Operational Efficiency & Cost Reduction**
- **Eliminates Manual Processing**: Reduces trade reconciliation time from hours to minutes, freeing up operations teams for higher-value activities
- **Reduces Operational Risk**: Minimizes human errors in trade matching that can lead to settlement failures and regulatory penalties
- **Scales with Volume**: Handles increasing trade volumes without proportional staff increases, supporting business growth

**Enhanced Accuracy & Risk Management**
- **AI-Driven Precision**: Machine learning models continuously improve matching accuracy, reducing false positives and missed exceptions
- **Real-Time Exception Detection**: Immediate identification of trade discrepancies prevents settlement delays and reduces counterparty risk
- **Configurable Tolerance Rules**: Flexible matching criteria accommodate different trade types and counterparty agreements

**Regulatory Compliance & Auditability**
- **Complete Audit Trail**: Every processing step is logged and traceable for regulatory examinations and internal audits
- **Standardized Reporting**: Automated generation of reconciliation reports in formats required by regulators
- **Data Integrity**: Immutable records and encryption ensure data security and compliance with financial regulations

**Business Intelligence & Insights**
- **Performance Analytics**: Real-time dashboards provide visibility into processing metrics, exception trends, and operational efficiency
- **Predictive Capabilities**: Historical data analysis helps predict and prevent common reconciliation issues
- **Counterparty Insights**: Pattern recognition identifies systematic issues with specific counterparties or trade types

**Competitive Advantages**
- **Faster Settlement Cycles**: Reduced reconciliation time enables faster trade settlement and improved cash flow
- **Improved Client Relationships**: Fewer reconciliation disputes and faster resolution enhance counterparty satisfaction
- **Scalable Architecture**: Cloud-native design supports rapid expansion into new markets and asset classes
- **Future-Ready Platform**: AI/ML foundation enables continuous improvement and adaptation to changing market conditions

### Return on Investment

**Quantifiable Benefits:**
- **70-90% reduction** in manual reconciliation effort
- **50-80% faster** exception resolution times
- **95%+ accuracy** in automated trade matching
- **Significant cost savings** through reduced operational overhead
- **Improved SLA performance** with counterparties and regulators

**Strategic Value:**
- Enables digital transformation of trade operations
- Provides foundation for expanding into new financial products
- Supports regulatory compliance in multiple jurisdictions
- Creates competitive differentiation in trade processing capabilities

This system transforms trade reconciliation from a manual, error-prone process into an intelligent, automated workflow that enhances operational efficiency, reduces risk, and provides strategic business value.


---

## Critical Configuration Notes

### DynamoDB Table Names (Dec 24, 2025)

**IMPORTANT:** There have been recurring table name mismatches. Always use these exact names:

#### Status Tracking Table
- **Correct Name:** `trade-matching-system-processing-status`
- **Table ARN:** `arn:aws:dynamodb:us-east-1:401552979575:table/trade-matching-system-processing-status`
- **Used By:** HTTP Agent Orchestrator for real-time workflow status tracking
- **Partition Key:** `processing_id` (String) ⚠️ **CRITICAL - NOT sessionId!**
- **Environment Variable:** `STATUS_TABLE_NAME` (defaults to correct name)

**⚠️ RECURRING ISSUE - READ CAREFULLY:**
The actual deployed table uses `processing_id` as the partition key, NOT `sessionId`.
This has been missed 10-20+ times. Always verify:
```python
# CORRECT - Use processing_id
Key={"processing_id": {"S": session_id}}

# WRONG - Do NOT use sessionId
Key={"sessionId": {"S": session_id}}  # ❌ This will fail!
```

**Common Mistakes:** 
1. Code previously used `ai-trade-matching-processing-status` (wrong table name)
2. Code previously used `sessionId` as partition key (wrong key name - should be `processing_id`)

#### Idempotency Table
- **Status:** DISABLED - Not in design
- **Previous Name:** `WorkflowIdempotency` (table does not exist)
- **Reason:** Idempotency caching is not part of the current architecture
- **Code Behavior:** Orchestrator has `idempotency_cache = None` with null checks

**Files to Check When Debugging:**
- `deployment/swarm_agentcore/http_agent_orchestrator.py` - Orchestrator initialization
- `deployment/swarm_agentcore/status_tracker.py` - Status tracking helper (uses `processing_id` key)
- `deployment/swarm_agentcore/idempotency.py` - Idempotency cache (disabled)

**Deployment Impact:**
After fixing table names, always redeploy the orchestrator:
```bash
cd deployment/swarm_agentcore
agentcore launch --auto-update-on-conflict
```
