# Quick Deployment Guide

## First Time Setup

### 1. Deploy Infrastructure
```bash
cd terraform
terraform init
terraform apply
```

Note the outputs - you'll need the CloudFront URL.

### 2. Configure API Endpoint
Edit `web-portal/.env.production`:
```env
VITE_API_URL=https://your-api-endpoint.amazonaws.com
```

### 3. Deploy Frontend
```bash
cd scripts
./deploy-frontend.sh
```

Or from web-portal directory:
```bash
npm run deploy
```

### 4. Access Your App
```
https://<cloudfront-domain>.cloudfront.net
```

## Subsequent Deployments

After making changes:
```bash
cd scripts
./deploy-frontend.sh
```

Or:
```bash
cd web-portal
npm run deploy
```

## What Gets Deployed

- Build artifacts from `web-portal/dist/`
- Optimized for production (minified, tree-shaken)
- Environment variables from `.env.production`
- CloudFront cache automatically invalidated

## Need Help?

See [CLOUDFRONT_DEPLOYMENT.md](./CLOUDFRONT_DEPLOYMENT.md) for detailed documentation.
