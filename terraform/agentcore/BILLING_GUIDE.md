# Billing and Cost Monitoring Guide

This guide explains the billing alarms and cost monitoring features configured in the AgentCore infrastructure.

## Overview

The infrastructure includes comprehensive cost monitoring to help you:
- Track AWS spending in real-time
- Get alerts before costs exceed your budget
- Identify cost anomalies and unexpected charges
- Monitor per-service spending

## Billing Alarms Configured

### 1. Total Monthly Charges Alarm

**Threshold**: $500/month (configurable via `billing_alarm_threshold`)

**Triggers when**: Total AWS charges exceed your monthly budget

**Action**: Sends email alert to billing team

**Configuration**:
```hcl
billing_alarm_threshold = 500  # Set your monthly budget
```

### 2. Warning Alarm (80% of Budget)

**Threshold**: $400/month (80% of your budget)

**Triggers when**: Charges reach 80% of your monthly budget

**Action**: Early warning email to take action before hitting limit

**Purpose**: Gives you time to optimize costs or adjust budget

### 3. Daily Charges Alarm

**Threshold**: ~$16.67/day (monthly budget ÷ 30)

**Triggers when**: Daily charges exceed expected daily rate

**Action**: Immediate alert for unusual daily spending

**Purpose**: Catch cost spikes early

### 4. Service-Specific Alarms

Individual alarms for high-cost services:

| Service | Threshold | Purpose |
|---------|-----------|---------|
| S3 | $100/month | Storage costs |
| DynamoDB | $200/month | Database operations |
| Bedrock | $300/month | AI model usage |
| CloudWatch | $100/month | Logging and monitoring |

**Enable/Disable**:
```hcl
enable_service_billing_alarms = true  # Set to false to disable
```

### 5. AWS Budget

**Features**:
- Tracks actual spending vs budget
- Forecasts end-of-month costs
- Sends alerts at 80%, 90%, and 100% of budget
- Filters by AgentCore resources only

**Enable/Disable**:
```hcl
enable_aws_budget = true  # Set to false to disable
```

### 6. Cost Anomaly Detection (Optional)

**Features**:
- Uses ML to detect unusual spending patterns
- Alerts on anomalies > $50
- Daily email summaries
- Requires at least one email address

**Enable**:
```hcl
enable_cost_anomaly_detection = true
billing_alert_emails = ["billing@example.com"]
```

## Setup Instructions

### Step 1: Configure Email Addresses

Edit `terraform.tfvars`:

```hcl
# Billing alerts (separate from operational alerts)
billing_alert_emails = [
  "billing@example.com",
  "finance@example.com",
  "admin@example.com"
]
```

### Step 2: Set Your Budget

```hcl
# Monthly budget in USD
billing_alarm_threshold = 500  # Adjust based on your needs
```

**Recommended Thresholds by Environment**:
- **Development**: $50-100/month
- **Staging**: $100-200/month
- **Production**: $500-1000/month

### Step 3: Enable/Disable Features

```hcl
# Per-service alarms (recommended for production)
enable_service_billing_alarms = true

# AWS Budget (recommended for all environments)
enable_aws_budget = true

# Cost Anomaly Detection (optional, for production)
enable_cost_anomaly_detection = false
```

### Step 4: Apply Configuration

```bash
cd terraform/agentcore
terraform apply
```

### Step 5: Confirm Email Subscriptions

After applying, you'll receive confirmation emails:
1. Check your inbox for AWS SNS subscription confirmations
2. Click "Confirm subscription" in each email
3. Verify subscriptions:
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn $(terraform output -raw billing_alerts_topic_arn)
   ```

## Understanding Billing Alerts

### Alert Email Format

```
Subject: ALARM: "trade-matching-system-total-charges-production" in US East (N. Virginia)

You are receiving this email because your Amazon CloudWatch Alarm 
"trade-matching-system-total-charges-production" in the US East (N. Virginia) 
region has entered the ALARM state.

Alarm Details:
- Alarm Name: trade-matching-system-total-charges-production
- Alarm Description: Alert when total AWS charges exceed $500
- State Change: OK -> ALARM
- Reason: Threshold Crossed: 1 datapoint [523.45] was greater than the threshold (500.0)
- Timestamp: 2025-01-15 10:30:00 UTC
```

### What to Do When You Receive an Alert

1. **Check AWS Cost Explorer**:
   ```bash
   # Open Cost Explorer
   aws ce get-cost-and-usage \
     --time-period Start=2025-01-01,End=2025-01-31 \
     --granularity DAILY \
     --metrics BlendedCost \
     --group-by Type=SERVICE
   ```

2. **Identify High-Cost Services**:
   - Go to AWS Console → Cost Management → Cost Explorer
   - Filter by "Component: AgentCore" tag
   - View by service to see breakdown

3. **Common Cost Culprits**:
   - **Bedrock**: High token usage from AI models
   - **DynamoDB**: Excessive read/write operations
   - **S3**: Large data storage or frequent access
   - **CloudWatch**: Excessive logging

4. **Take Action**:
   - Review and optimize agent prompts (reduce tokens)
   - Check for infinite loops or retry storms
   - Review S3 lifecycle policies
   - Reduce CloudWatch log retention
   - Scale down unused resources

## Cost Monitoring Dashboard

### View Current Costs

```bash
# Get current month's costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://cost-filter.json

# cost-filter.json
{
  "Tags": {
    "Key": "Component",
    "Values": ["AgentCore"]
  }
}
```

### View Cost by Service

```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE \
  --filter file://cost-filter.json
```

### View Daily Costs

```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter file://cost-filter.json
```

## Cost Optimization Tips

### 1. Development Environment

**Destroy when not in use**:
```bash
# At end of day
terraform destroy

# Next morning
terraform apply
```

**Estimated savings**: $8-20/month → $0 when destroyed

### 2. S3 Storage

**Already optimized** with lifecycle policies:
- 30 days → Standard-IA (50% cheaper)
- 90 days → Glacier (80% cheaper)
- Auto-delete old data

**Manual optimization**:
```bash
# Delete old test data
aws s3 rm s3://bucket-name/test/ --recursive

# Empty specific folders
aws s3 rm s3://bucket-name/temp/ --recursive
```

### 3. CloudWatch Logs

**Already optimized** with 30-day retention

**Manual optimization**:
```bash
# Reduce retention for dev logs
aws logs put-retention-policy \
  --log-group-name /aws/agentcore/trade-matching-system/pdf-adapter-dev \
  --retention-in-days 7
```

### 4. DynamoDB

**Already optimized** with on-demand billing

**Monitor usage**:
```bash
# Check read/write capacity
aws dynamodb describe-table \
  --table-name BankTradeData-production \
  --query 'Table.BillingModeSummary'
```

### 5. Bedrock

**Optimize token usage**:
- Use shorter prompts
- Cache common responses
- Reduce max_tokens parameter
- Use cheaper models for simple tasks

### 6. Disable Unused Alarms

```bash
# Disable non-critical alarms in dev
aws cloudwatch disable-alarm-actions \
  --alarm-names trade-matching-system-pdf-adapter-latency-dev
```

## Budget Scenarios

### Scenario 1: Development ($50/month)

```hcl
billing_alarm_threshold = 50
enable_service_billing_alarms = false  # Too granular for dev
enable_aws_budget = true
enable_cost_anomaly_detection = false
```

**Expected costs**:
- S3: $5-10
- DynamoDB: $0-5 (minimal usage)
- CloudWatch: $1-5
- Other: $1-5
- **Total**: $7-25/month

### Scenario 2: Staging ($200/month)

```hcl
billing_alarm_threshold = 200
enable_service_billing_alarms = true
enable_aws_budget = true
enable_cost_anomaly_detection = false
```

**Expected costs**:
- S3: $20-40
- DynamoDB: $50-100
- Bedrock: $50-100
- CloudWatch: $20-40
- Other: $10-20
- **Total**: $150-300/month

### Scenario 3: Production ($500/month)

```hcl
billing_alarm_threshold = 500
enable_service_billing_alarms = true
enable_aws_budget = true
enable_cost_anomaly_detection = true
```

**Expected costs**:
- S3: $50-100
- DynamoDB: $100-200
- Bedrock: $200-400
- CloudWatch: $50-100
- Other: $20-50
- **Total**: $420-850/month

## Troubleshooting

### Issue: Not Receiving Billing Alerts

**Check subscription status**:
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn $(terraform output -raw billing_alerts_topic_arn)
```

**Confirm subscription**:
- Check spam folder for confirmation email
- Resend confirmation:
  ```bash
  aws sns subscribe \
    --topic-arn $(terraform output -raw billing_alerts_topic_arn) \
    --protocol email \
    --notification-endpoint your-email@example.com
  ```

### Issue: Billing Metrics Not Available

**Enable billing alerts in AWS**:
1. Go to AWS Console → Billing → Billing Preferences
2. Check "Receive Billing Alerts"
3. Save preferences
4. Wait 24 hours for metrics to populate

### Issue: Alarm in INSUFFICIENT_DATA State

**Cause**: Billing metrics update every 6 hours

**Solution**: Wait 6-24 hours after deployment

### Issue: False Alarms

**Adjust threshold**:
```hcl
billing_alarm_threshold = 1000  # Increase if needed
```

**Or disable specific alarms**:
```bash
aws cloudwatch disable-alarm-actions \
  --alarm-names trade-matching-system-daily-charges-production
```

## Best Practices

1. **Set Realistic Budgets**: Start conservative, adjust based on actual usage
2. **Monitor Weekly**: Review costs every week, not just when alarms trigger
3. **Tag Everything**: Use consistent tags for accurate cost allocation
4. **Use Cost Explorer**: Visualize trends and identify optimization opportunities
5. **Enable Anomaly Detection**: Catch unusual spending patterns early
6. **Document Costs**: Keep notes on what causes cost spikes
7. **Review Monthly**: Analyze monthly bills and optimize accordingly

## Additional Resources

- [AWS Cost Management Console](https://console.aws.amazon.com/cost-management/home)
- [AWS Cost Explorer](https://console.aws.amazon.com/cost-management/home#/cost-explorer)
- [AWS Budgets](https://console.aws.amazon.com/billing/home#/budgets)
- [AWS Cost Anomaly Detection](https://console.aws.amazon.com/cost-management/home#/anomaly-detection)

## Support

For billing questions:
- Review this guide
- Check AWS Cost Explorer
- Contact AWS Support for billing disputes
- Reach out to platform team for optimization help
