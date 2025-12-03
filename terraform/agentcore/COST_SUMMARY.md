# Cost Summary - AgentCore Infrastructure

## Quick Reference

### Monthly Cost Estimates

| Environment | Idle Cost | Active Cost | Notes |
|-------------|-----------|-------------|-------|
| **Development** | $8-20 | $50-100 | Destroy when not in use |
| **Staging** | $20-50 | $150-300 | Moderate usage |
| **Production** | $50-100 | $420-850 | Full usage |

### Cost Breakdown by Service

#### Always Charging (Even When Idle)

| Service | Idle Cost/Month | Notes |
|---------|-----------------|-------|
| S3 Storage | $5-20 | Based on data stored |
| Cognito | $0-10 | Per monthly active user |
| CloudWatch Alarms | $1-2 | $0.10 per alarm |
| KMS Keys | $1 | $1 per key |
| SNS Topics | <$1 | Minimal base cost |
| **TOTAL IDLE** | **$8-34/month** | **Minimum cost when not used** |

#### Usage-Based (Only When Active)

| Service | Cost Model | Estimated Active Cost |
|---------|------------|----------------------|
| DynamoDB | Per request | $100-200/month |
| SQS | Per message | $10-20/month |
| Lambda | Per invocation | $10-20/month |
| Bedrock | Per token | $200-400/month |
| CloudWatch Logs | Per GB | $50-100/month |
| X-Ray | Per trace | $10-20/month |
| **TOTAL ACTIVE** | - | **$380-760/month** |

## Billing Alarms Configured

### 1. Total Monthly Budget
- **Threshold**: $500/month (configurable)
- **Alert**: When total charges exceed budget
- **Email**: Sent to billing team

### 2. Warning Alert (80%)
- **Threshold**: $400/month (80% of budget)
- **Alert**: Early warning before hitting limit
- **Email**: Sent to billing team

### 3. Daily Spending
- **Threshold**: ~$17/day (budget ÷ 30)
- **Alert**: When daily charges exceed expected rate
- **Email**: Immediate notification

### 4. Per-Service Alarms
- **S3**: $100/month
- **DynamoDB**: $200/month
- **Bedrock**: $300/month
- **CloudWatch**: $100/month

### 5. AWS Budget
- Tracks actual vs forecasted spending
- Alerts at 80%, 90%, 100% of budget
- Filters by AgentCore resources only

### 6. Cost Anomaly Detection (Optional)
- ML-based anomaly detection
- Alerts on unusual spending > $50
- Daily email summaries

## Configuration

### Set Your Budget

Edit `terraform.tfvars`:

```hcl
# Your monthly budget
billing_alarm_threshold = 500  # USD

# Email addresses for billing alerts
billing_alert_emails = [
  "billing@example.com",
  "admin@example.com"
]

# Enable/disable features
enable_service_billing_alarms = true
enable_aws_budget = true
enable_cost_anomaly_detection = false
```

### Recommended Budgets

```hcl
# Development
billing_alarm_threshold = 50

# Staging
billing_alarm_threshold = 200

# Production
billing_alarm_threshold = 500
```

## Cost Optimization Strategies

### For Development

1. **Destroy when not in use**:
   ```bash
   terraform destroy  # End of day
   terraform apply    # Next morning
   ```
   **Savings**: $8-20/month → $0

2. **Disable service alarms**:
   ```hcl
   enable_service_billing_alarms = false
   ```

3. **Reduce log retention**:
   - Already set to 30 days
   - Can reduce to 7 days for dev

### For Production

1. **S3 Lifecycle Policies** ✅ Already configured
   - 30 days → Standard-IA
   - 90 days → Glacier
   - Auto-delete old data

2. **DynamoDB On-Demand** ✅ Already configured
   - Only pay for actual usage
   - No idle costs

3. **Monitor and Optimize**:
   - Review Cost Explorer weekly
   - Optimize Bedrock token usage
   - Clean up unused data

## What Happens When You Hit Your Budget?

### Automatic Actions
- ❌ **NO automatic shutdown** (by design)
- ✅ Email alerts sent to billing team
- ✅ Notifications in AWS Console

### Manual Actions Required
1. Review Cost Explorer to identify high costs
2. Optimize or scale down resources
3. Increase budget if needed
4. Contact AWS Support if unexpected

## Viewing Costs

### AWS Console
1. Go to: https://console.aws.amazon.com/cost-management/home
2. Click "Cost Explorer"
3. Filter by tag: `Component = AgentCore`

### AWS CLI
```bash
# Current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost

# By service
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

### Terraform Output
```bash
cd terraform/agentcore
terraform output billing_alarm_threshold
terraform output billing_alerts_topic_arn
```

## Important Notes

### Billing Metrics Delay
- Billing metrics update every **6 hours**
- Alarms may take **6-24 hours** to activate
- Cost Explorer updates **daily**

### First-Time Setup
1. Enable billing alerts in AWS Console:
   - Go to Billing → Billing Preferences
   - Check "Receive Billing Alerts"
   - Save preferences

2. Confirm email subscriptions:
   - Check inbox for SNS confirmation emails
   - Click "Confirm subscription"

3. Wait 24 hours for metrics to populate

### Free Tier
Some services have free tiers:
- **Cognito**: First 50,000 MAUs free
- **Lambda**: 1M requests/month free
- **CloudWatch**: 10 custom metrics free
- **S3**: 5GB storage free (first 12 months)

## FAQ

**Q: Will I be charged if I don't use the infrastructure?**
A: Yes, minimal charges (~$8-34/month) for S3 storage, Cognito, CloudWatch alarms, and KMS keys.

**Q: How do I stop all charges?**
A: Run `terraform destroy` to delete all resources.

**Q: Can I set a hard spending limit?**
A: No, AWS doesn't support automatic spending limits. You must manually stop resources.

**Q: What if I exceed my budget?**
A: You'll receive email alerts, but services will continue running. You must manually scale down or destroy resources.

**Q: How accurate are the cost estimates?**
A: Estimates are based on typical usage. Actual costs may vary based on:
- Number of trades processed
- Bedrock token usage
- Data storage volume
- Log volume

**Q: Can I get a refund for unexpected charges?**
A: Contact AWS Support for billing disputes. They may provide credits for service issues.

## Next Steps

1. **Configure your budget** in `terraform.tfvars`
2. **Add billing email addresses**
3. **Apply the configuration**: `terraform apply`
4. **Confirm email subscriptions**
5. **Monitor costs** in AWS Cost Explorer
6. **Review weekly** and optimize as needed

## Support

- **Billing Guide**: See `BILLING_GUIDE.md` for detailed information
- **AWS Cost Explorer**: https://console.aws.amazon.com/cost-management/home
- **AWS Support**: For billing questions and disputes
- **Platform Team**: For optimization help
