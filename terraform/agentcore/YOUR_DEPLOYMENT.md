# Your AgentCore Deployment - Ready to Go! 🚀

## Configuration Summary

✅ **Email Configured**: koushald@amazon.ae
✅ **Monthly Budget**: $500 USD
✅ **Region**: us-east-1
✅ **Environment**: production

## What You'll Receive

### Email Alerts

You'll receive emails at **koushald@amazon.ae** for:

#### 1. Operational Alerts
- Agent errors (error rate > 5%)
- Performance issues (latency > 30s)
- System anomalies

#### 2. Billing Alerts
- **Warning**: When costs reach $400 (80% of budget)
- **Critical**: When costs exceed $500 (your budget)
- **Daily**: When daily costs exceed ~$17/day
- **Per-Service**: S3 > $100, DynamoDB > $200, Bedrock > $300, CloudWatch > $100

### Expected Costs

**Idle (not processing trades)**:
- $8-34/month
- Just S3 storage, Cognito, CloudWatch alarms, KMS

**Active (processing trades)**:
- $220-490/month
- Includes DynamoDB, Bedrock, SQS, CloudWatch logs

## Deploy Now

### Step 1: Review the Plan

```bash
cd terraform/agentcore
terraform plan
```

**Expected**: 126 resources to be created

### Step 2: Deploy

```bash
terraform apply
```

Type `yes` when prompted.

**Time**: ~5-10 minutes

### Step 3: Confirm Email Subscriptions

After deployment:
1. Check your inbox: **koushald@amazon.ae**
2. You'll receive **2 confirmation emails**:
   - ✉️ Operational Alerts (agent monitoring)
   - ✉️ Billing Alerts (cost monitoring)
3. Click "Confirm subscription" in each email

**Important**: You won't receive alerts until you confirm!

## What Gets Created

### Storage & Databases
- ✅ 2 S3 buckets (documents + logs)
- ✅ 4 DynamoDB tables (trades, exceptions, registry)
- ✅ KMS encryption keys

### Messaging & Events
- ✅ 10+ SQS queues (event-driven architecture)
- ✅ 2 SNS topics (operational + billing alerts)

### Security & Access
- ✅ 10+ IAM roles (least-privilege access)
- ✅ Cognito user pool (authentication)
- ✅ 3 user groups (Admin, Operator, Auditor)

### Monitoring & Alerts
- ✅ 5 CloudWatch log groups
- ✅ 7+ CloudWatch alarms
- ✅ 1 CloudWatch dashboard
- ✅ X-Ray tracing configuration
- ✅ AWS Budget with forecasting

### Cost Monitoring
- ✅ Total monthly budget alarm ($500)
- ✅ Warning alarm at 80% ($400)
- ✅ Daily spending alarm (~$17/day)
- ✅ Per-service alarms (S3, DynamoDB, Bedrock, CloudWatch)

## After Deployment

### Verify Everything Works

```bash
# Check S3 bucket
terraform output s3_bucket_name

# Check DynamoDB tables
terraform output bank_trade_table_name
terraform output counterparty_trade_table_name

# Check billing configuration
terraform output billing_alarm_threshold
terraform output billing_alerts_topic_arn

# View all outputs
terraform output
```

### View Your Costs

```bash
# Open AWS Cost Explorer
open https://console.aws.amazon.com/cost-management/home

# Or use CLI
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost
```

### View Your Dashboard

```bash
# Get dashboard name
DASHBOARD=$(terraform output -raw dashboard_name)

# Open in browser
open "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=$DASHBOARD"
```

## Cost Control

### If You Want to Stop Charges

**Option 1: Destroy Everything** (recommended for dev/testing)
```bash
terraform destroy
```
This removes ALL resources and stops ALL charges.

**Option 2: Scale Down** (for production)
- Reduce log retention
- Delete old S3 data
- Disable non-critical alarms

### Monitor Your Spending

**Weekly Check** (recommended):
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost
```

## Troubleshooting

### Not Receiving Emails?

1. **Check spam folder** for AWS SNS emails
2. **Verify email** in terraform.tfvars: `koushald@amazon.ae`
3. **Reconfirm subscription**:
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn $(terraform output -raw billing_alerts_topic_arn)
   ```

### Costs Higher Than Expected?

1. **Check Cost Explorer**: https://console.aws.amazon.com/cost-management/home
2. **Filter by tag**: Component = AgentCore
3. **View by service** to identify high costs
4. **Common culprits**:
   - Bedrock: High token usage
   - DynamoDB: Excessive read/write operations
   - S3: Large data storage
   - CloudWatch: Excessive logging

### Want to Adjust Budget?

Edit `terraform.tfvars`:
```hcl
billing_alarm_threshold = 1000  # Increase to $1000
```

Then apply:
```bash
terraform apply
```

## Next Steps

After infrastructure is deployed:

### 1. Deploy AgentCore Services
```bash
cd scripts
./deploy_agentcore_memory.sh
./deploy_agentcore_gateway.sh
```

### 2. Create Users
```bash
USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username koushald@amazon.ae \
  --user-attributes Name=email,Value=koushald@amazon.ae Name=name,Value="Koushal" \
  --temporary-password "TempPass123!" \
  --region us-east-1

aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username koushald@amazon.ae \
  --group-name Admin \
  --region us-east-1
```

### 3. Deploy Agents
See tasks 14.1-14.6 in `.kiro/specs/agentcore-migration/tasks.md`

### 4. Deploy Web Portal
See tasks 16.1-16.11 in `.kiro/specs/agentcore-migration/tasks.md`

## Documentation

- 📖 **Quick Start**: `QUICK_START.md`
- 💰 **Cost Summary**: `COST_SUMMARY.md`
- 📊 **Billing Guide**: `BILLING_GUIDE.md`
- 🚀 **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- 📚 **Full README**: `README.md`

## Important Reminders

1. ✅ **Confirm email subscriptions** after deployment
2. ✅ **Monitor costs weekly** in Cost Explorer
3. ✅ **Review billing alerts** when received
4. ✅ **Destroy resources** when not needed (dev/testing)
5. ✅ **Enable MFA** for Cognito admin users

## Support

- **Email**: koushald@amazon.ae (that's you!)
- **AWS Console**: https://console.aws.amazon.com
- **Cost Explorer**: https://console.aws.amazon.com/cost-management/home
- **Documentation**: See files in this directory

---

## Ready to Deploy?

Run this command:

```bash
cd terraform/agentcore
terraform apply
```

Then check your email (**koushald@amazon.ae**) to confirm subscriptions!

Good luck! 🎉
