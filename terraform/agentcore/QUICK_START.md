# Quick Start Guide - AgentCore Infrastructure

## 🚀 Deploy in 5 Minutes

### Step 1: Configure Billing Alerts (Important!)

Edit `terraform.tfvars`:

```hcl
# Add your email for billing alerts
billing_alert_emails = [
  "your-email@example.com"
]

# Set your monthly budget (in USD)
billing_alarm_threshold = 500  # Adjust based on your needs
```

**Recommended budgets**:
- Development: $50
- Staging: $200
- Production: $500

### Step 2: Review Configuration

```bash
cd terraform/agentcore
terraform plan
```

**Expected**: ~126 resources to be created

### Step 3: Deploy

```bash
terraform apply
```

Type `yes` when prompted.

**Deployment time**: ~5-10 minutes

### Step 4: Confirm Email Subscriptions

1. Check your inbox for AWS SNS confirmation emails
2. Click "Confirm subscription" in each email
3. You'll receive 2 emails:
   - Operational alerts (agent errors, performance)
   - Billing alerts (cost monitoring)

### Step 5: Verify Deployment

```bash
# Check S3 bucket
terraform output s3_bucket_name

# Check DynamoDB tables
terraform output bank_trade_table_name

# Check billing alarm
terraform output billing_alarm_threshold
```

## 💰 Cost Monitoring

### View Current Costs

```bash
# AWS Console
open https://console.aws.amazon.com/cost-management/home

# Or use CLI
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost
```

### Billing Alarms

You'll receive email alerts when:
- ✅ Total charges exceed your budget ($500)
- ✅ Charges reach 80% of budget ($400)
- ✅ Daily charges exceed expected rate (~$17/day)
- ✅ Individual services exceed thresholds

### Expected Costs

**When NOT in use** (idle):
- $8-34/month (S3 storage, Cognito, CloudWatch alarms, KMS)

**When actively processing trades**:
- $220-490/month (includes DynamoDB, Bedrock, SQS, CloudWatch logs)

## 🛑 Stop All Charges

To completely stop all charges:

```bash
cd terraform/agentcore
terraform destroy
```

Type `yes` when prompted.

**This will delete ALL resources and data!**

## 📚 Documentation

- **Cost Details**: `COST_SUMMARY.md`
- **Billing Setup**: `BILLING_GUIDE.md`
- **Full README**: `README.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`

## ⚙️ Configuration Files

```
terraform/agentcore/
├── terraform.tfvars          # Your configuration (edit this!)
├── terraform.tfvars.example  # Example values
├── QUICK_START.md           # This file
├── COST_SUMMARY.md          # Cost breakdown
├── BILLING_GUIDE.md         # Detailed billing info
└── README.md                # Full documentation
```

## 🔧 Common Tasks

### Update Budget

Edit `terraform.tfvars`:
```hcl
billing_alarm_threshold = 1000  # Increase to $1000
```

Then apply:
```bash
terraform apply
```

### Add Email Address

Edit `terraform.tfvars`:
```hcl
billing_alert_emails = [
  "existing@example.com",
  "new@example.com"  # Add new email
]
```

Then apply:
```bash
terraform apply
```

### Disable Service Alarms

Edit `terraform.tfvars`:
```hcl
enable_service_billing_alarms = false
```

Then apply:
```bash
terraform apply
```

### View All Outputs

```bash
terraform output
```

### View Specific Output

```bash
terraform output s3_bucket_name
terraform output billing_alarm_threshold
terraform output cognito_user_pool_id
```

## 🆘 Troubleshooting

### Issue: Not receiving billing alerts

**Solution**: 
1. Check spam folder for confirmation email
2. Verify email in `terraform.tfvars`
3. Reapply: `terraform apply`

### Issue: Costs higher than expected

**Solution**:
1. Check AWS Cost Explorer
2. Review `BILLING_GUIDE.md`
3. Identify high-cost services
4. Optimize or scale down

### Issue: Terraform state locked

**Solution**:
```bash
terraform force-unlock <LOCK_ID>
```

### Issue: Want to start fresh

**Solution**:
```bash
terraform destroy  # Delete everything
terraform apply    # Recreate
```

## 📞 Support

- **Billing Questions**: See `BILLING_GUIDE.md`
- **Cost Optimization**: See `COST_SUMMARY.md`
- **Technical Issues**: See `README.md`
- **AWS Support**: For billing disputes

## ✅ Checklist

Before deploying:
- [ ] Terraform installed
- [ ] AWS CLI configured
- [ ] Email addresses added to `terraform.tfvars`
- [ ] Budget threshold set in `terraform.tfvars`
- [ ] Reviewed cost estimates in `COST_SUMMARY.md`

After deploying:
- [ ] Confirmed email subscriptions (check inbox)
- [ ] Verified resources created (`terraform output`)
- [ ] Checked AWS Cost Explorer
- [ ] Bookmarked Cost Management Console

## 🎯 Next Steps

After infrastructure is deployed:

1. **Deploy AgentCore Memory** (see `DEPLOYMENT_GUIDE.md`)
2. **Deploy AgentCore Gateway** (see `DEPLOYMENT_GUIDE.md`)
3. **Create Cognito Users** (see `DEPLOYMENT_GUIDE.md`)
4. **Deploy Agents** (Tasks 14.1-14.6 in implementation plan)
5. **Deploy Web Portal** (Tasks 16.1-16.11 in implementation plan)

## 💡 Pro Tips

1. **Start with low budget**: Set `billing_alarm_threshold = 50` for development
2. **Monitor weekly**: Check Cost Explorer every week
3. **Destroy when not needed**: Run `terraform destroy` at end of day for dev
4. **Use tags**: All resources tagged with `Component=AgentCore` for cost tracking
5. **Enable anomaly detection**: Set `enable_cost_anomaly_detection = true` for production

---

**Ready to deploy?** Run `terraform apply` and you're good to go! 🚀
