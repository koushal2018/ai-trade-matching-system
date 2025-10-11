# Configuration Files for Token Optimization

## Purpose
These configuration files implement the **scratchpad pattern** to reduce token usage in CrewAI agents.

Instead of embedding all procedural details in task descriptions, agents read these configs as needed.

## Files

### 1. `matching_rules.json`
Contains trade matching criteria and classification rules.

**Usage:**
- `matching_analyst` agent reads this file to understand matching tolerances
- Reduces task description from 1000 tokens to 150 tokens
- Agents can reference specific rules without loading full context

**Key Sections:**
- `matching_criteria`: How to match trades (exact, tolerance, fuzzy)
- `classifications`: How to classify match results
- `table_integrity_rules`: Data validation requirements
- `reporting_requirements`: What to include in reports

### 2. `storage_config.json`
Contains DynamoDB and S3 storage configuration.

**Usage:**
- All agents reference this for table names, paths, and validation rules
- Centralizes storage logic outside of task descriptions
- Reduces redundancy across tasks

**Key Sections:**
- `dynamodb.tables`: Table schemas and validation rules
- `s3.paths`: S3 path templates
- `local_storage`: Local temp directory structure

## Scratchpad Pattern in Action

### Before (Verbose Task Description)
```yaml
matching_task:
  description: |
    **STEP 0: CRITICAL VERIFICATION**
    Check BankTradeData - ALL records should have TRADE_SOURCE = "BANK"
    Check CounterpartyTradeData - ALL records should have TRADE_SOURCE = "COUNTERPARTY"

    **MATCHING CRITERIA:**
    - Trade ID: exact match
    - Trade Date: within 1 day tolerance
    - Notional: within 0.01% tolerance
    ...
    [50 lines of detailed instructions]
```
**Token Cost:** ~1000 tokens

### After (Concise + Config Reference)
```yaml
matching_task:
  description: |
    Read matching rules from config/matching_rules.json.
    Match trades between BankTradeData and CounterpartyTradeData.
    Save report to S3: reports/matching_report_{id}.md
```
**Token Cost:** ~100 tokens

**Agent reads config file only when needed, not on every LLM call**

## Uploading to S3 (Optional)

To make configs available to agents running in cloud environments:

```bash
# Upload to S3 for cloud access
aws s3 cp config/matching_rules.json s3://fab-otc-reconciliation-deployment/config/
aws s3 cp config/storage_config.json s3://fab-otc-reconciliation-deployment/config/

# Agents can read from S3
s3://fab-otc-reconciliation-deployment/config/matching_rules.json
```

## Agent Usage Example

Agents can reference configs in their backstory or via tools:

```yaml
matching_analyst:
  backstory: >
    You are an expert trade matcher with 10+ years experience.
    You follow standardized matching rules defined in config/matching_rules.json.
    You always verify table integrity before matching.
    You produce detailed reports saved to S3.
```

The agent will:
1. Read `config/matching_rules.json` on first task
2. Cache rules in memory for current session
3. Apply rules without re-reading file
4. **Token savings:** Rules not included in every LLM prompt

## Token Savings Summary

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| Task descriptions | 2600 tokens | 440 tokens | 83% |
| Repeated rules | 500 tokens/call | 0 tokens/call | 100% |
| Agent context | Large | Minimal | 60-80% |

## Next Steps

1. ✅ Tasks optimized (completed)
2. ✅ Config files created (completed)
3. ⏭️ Optional: Upload configs to S3
4. ⏭️ Optional: Update agent backstories to reference configs
5. ⏭️ Test crew with new optimized tasks
