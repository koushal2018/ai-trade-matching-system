# CloudFront Deployment Guide

This guide explains how to deploy the Trade Matching Portal frontend to AWS CloudFront.

## Architecture

The frontend is deployed using:
- **S3 Bucket**: Hosts the static build files
- **CloudFront**: CDN for global content delivery with HTTPS
- **Origin Access Control (OAC)**: Secures S3 bucket access to CloudFront only

## Prerequisites

1. AWS CLI installed and configured
2. Terraform installed
3. Node.js and npm installed
4. `jq` command-line tool for JSON parsing

Install jq (if needed):
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Amazon Linux
sudo yum install jq
```

## Initial Deployment

### Step 1: Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform (first time only)
terraform init

# Review the infrastructure plan
terraform plan

# Apply the infrastructure
terraform apply
```

This will create:
- S3 bucket for frontend hosting
- CloudFront distribution
- Origin Access Control (OAC)
- Bucket policies

After successful deployment, note the outputs:
- `cloudfront_domain_name`: Your CloudFront URL (e.g., d111111abcdef8.cloudfront.net)
- `cloudfront_distribution_id`: Distribution ID for cache invalidation
- `frontend_s3_bucket`: S3 bucket name

### Step 2: Configure Production Environment

Edit `web-portal/.env.production` and update the API URL:

```env
# Update this with your actual API endpoint
VITE_API_URL=https://your-api-endpoint.amazonaws.com
```

You can find your API endpoint from:
- **API Gateway**: AWS Console → API Gateway → Your API → Stages
- **ALB**: AWS Console → EC2 → Load Balancers → Copy DNS name

### Step 3: Build and Deploy Frontend

```bash
cd scripts
chmod +x deploy-frontend.sh
./deploy-frontend.sh
```

The deployment script will:
1. Build the frontend with production settings
2. Upload files to S3 with proper cache headers
3. Invalidate CloudFront cache
4. Wait for deployment to complete

### Step 4: Access Your Application

After deployment completes, access your application at:
```
https://<your-cloudfront-domain>.cloudfront.net
```

## Subsequent Deployments

After making changes to the frontend:

```bash
cd scripts
./deploy-frontend.sh
```

## Cache Headers

The deployment script sets optimal cache headers:

- **Static assets** (JS, CSS, images): 1 year cache (`max-age=31536000, immutable`)
- **index.html**: No cache (`max-age=0, must-revalidate`) to ensure SPA routing works

## CloudFront Configuration

### Price Class
By default, uses `PriceClass_100` (US, Canada, Europe). To change:

Edit `terraform/variables.tf`:
```hcl
variable "cloudfront_price_class" {
  default = "PriceClass_200"  # Includes Asia
}
```

### Custom Domain (Optional)

To add a custom domain:

1. **Register/have a domain in Route53**

2. **Request ACM certificate in us-east-1**:
```bash
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

3. **Update CloudFront configuration** in `terraform/cloudfront.tf`:

```hcl
resource "aws_cloudfront_distribution" "frontend" {
  aliases = ["yourdomain.com"]

  viewer_certificate {
    acm_certificate_arn      = "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT_ID"
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

4. **Create Route53 record**:
```hcl
resource "aws_route53_record" "frontend" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "yourdomain.com"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
    evaluate_target_health = false
  }
}
```

## Updating API Configuration

If your API endpoint changes:

1. Update `web-portal/.env.production`
2. Run deployment script:
```bash
cd scripts
./deploy-frontend.sh
```

## Troubleshooting

### 403 Forbidden Errors
- Check S3 bucket policy allows CloudFront OAC access
- Verify CloudFront distribution is deployed (status: Deployed)
- Check `index.html` exists in S3 bucket

### Changes Not Visible
- CloudFront cache may not be invalidated
- Manual invalidation:
```bash
aws cloudfront create-invalidation \
  --distribution-id <DISTRIBUTION_ID> \
  --paths "/*"
```

### CORS Errors
- Ensure API has proper CORS headers
- CloudFront passes CORS headers through
- Check browser console for specific CORS issues

### Slow First Load
- Normal for CloudFront - first request fetches from S3
- Subsequent requests are cached at edge locations
- Consider enabling CloudFront prewarming for critical pages

## Cost Optimization

- **S3**: Minimal cost (few MB of static files)
- **CloudFront**: Pay for data transfer and requests
  - First 1TB/month: ~$0.085/GB
  - Use PriceClass_100 for lower costs if users are in US/EU
- **Estimated**: ~$5-20/month for moderate traffic

## Security Best practices

1. ✅ S3 bucket blocks all public access
2. ✅ CloudFront uses Origin Access Control (OAC)
3. ✅ HTTPS enforced (redirect HTTP to HTTPS)
4. ✅ Server-side encryption enabled (AES256)
5. ✅ S3 versioning enabled for rollback capability

## Monitoring

### CloudFront Metrics (CloudWatch)
- Requests
- Bytes downloaded
- Error rates (4xx, 5xx)
- Cache hit ratio

### View Logs
```bash
# CloudFront access logs (if enabled)
aws s3 ls s3://cloudfront-logs-bucket/

# Recent CloudFront distributions
aws cloudfront list-distributions --query 'DistributionList.Items[].{ID:Id,Domain:DomainName,Status:Status}'
```

## Rollback

If deployment causes issues:

### Option 1: Rollback S3 Content
```bash
# List versions
aws s3api list-object-versions --bucket <bucket-name>

# Restore specific version
aws s3api copy-object \
  --copy-source <bucket-name>/<key>?versionId=<version-id> \
  --bucket <bucket-name> \
  --key <key>

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

### Option 2: Redeploy Previous Build
```bash
cd web-portal
git checkout <previous-commit>
npm run build
cd ../scripts
./deploy-frontend.sh
```

## References

- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [CloudFront Origin Access Control](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
