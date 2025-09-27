# Complete Deployment Guide: AI Trade Matching System on EKS

## Overview

This guide provides step-by-step instructions for deploying the AI Trade Matching System on Amazon EKS with S3 event-driven processing. The deployment transforms the current file-based system into a cloud-native, scalable solution.

## Architecture Summary

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   S3 Upload     │───▶│ S3 Event     │───▶│ SQS Queue   │───▶│   Lambda     │
│  (Trade PDFs)   │    │ Notification │    │             │    │  Processor   │
└─────────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                                      │
                                                                      ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   DynamoDB      │◀───│ CrewAI       │◀───│ EKS Service │◀───│ HTTP Request │
│  (Trade Data)   │    │ Processing   │    │             │    │              │
└─────────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

## Prerequisites

### 1. AWS Account Setup

- AWS CLI configured with appropriate permissions
- kubectl installed and configured
- eksctl installed (v0.140.0 or later)
- Docker installed for image building
- Helm installed for Kubernetes package management

### 2. Required Permissions

Your AWS account/user needs the following permissions:
- EKS cluster creation and management
- EC2 instance management
- IAM role creation and management
- S3 bucket operations
- Lambda function deployment
- DynamoDB table operations
- CloudFormation stack operations

## Step 1: Infrastructure Setup

### 1.1 Create EKS Cluster

```bash
# Create EKS cluster using eksctl
eksctl create cluster \
  --name trade-matching-cluster \
  --region us-east-1 \
  --version 1.28 \
  --nodegroup-name worker-nodes \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --with-oidc \
  --ssh-access \
  --ssh-public-key your-key-name \
  --managed

# Verify cluster creation
kubectl get nodes
```

### 1.2 Install Required Add-ons

```bash
# Install AWS Load Balancer Controller
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

eksctl create iamserviceaccount \
  --cluster=trade-matching-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=trade-matching-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Install EBS CSI Driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster trade-matching-cluster \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/Amazon_EBS_CSI_DriverPolicy \
  --approve

eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster trade-matching-cluster \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKS_EBS_CSI_DriverRole \
  --force
```

### 1.3 Deploy S3 and SQS Infrastructure

```bash
# Deploy S3 bucket and SQS queues
aws cloudformation create-stack \
  --stack-name trade-matching-infrastructure \
  --template-body file://s3-event-configuration.yaml \
  --parameters ParameterKey=Environment,ParameterValue=production \
               ParameterKey=EKSClusterName,ParameterValue=trade-matching-cluster \
               ParameterKey=AlertEmail,ParameterValue=your-email@example.com \
  --capabilities CAPABILITY_IAM

# Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name trade-matching-infrastructure

# Get outputs
aws cloudformation describe-stacks \
  --stack-name trade-matching-infrastructure \
  --query 'Stacks[0].Outputs'
```

### 1.4 Create DynamoDB Tables

```bash
# Deploy DynamoDB tables
aws cloudformation create-stack \
  --stack-name trade-matching-database \
  --template-body file://dynamodb-tables.yaml \
  --capabilities CAPABILITY_IAM

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name trade-matching-database
```

## Step 2: Application Containerization

### 2.1 Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY *.py ./

# Create necessary directories
RUN mkdir -p /tmp/processing /app/logs

# Create non-root user
RUN useradd -m -u 1000 trader && \
    chown -R trader:trader /app /tmp/processing

USER trader

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["python", "eks-enhanced-main.py"]
```

### 2.2 Build and Push Container Image

```bash
# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

# Create ECR repository
aws ecr create-repository \
  --repository-name trade-matching-system \
  --region $REGION

# Get login token
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build image
docker build -t trade-matching-system:latest .

# Tag image
docker tag trade-matching-system:latest \
  $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/trade-matching-system:latest

# Push image
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/trade-matching-system:latest
```

## Step 3: Kubernetes Deployment

### 3.1 Create Namespace and Service Account

```bash
# Create namespace
kubectl create namespace trading

# Create service account with OIDC
eksctl create iamserviceaccount \
  --cluster trade-matching-cluster \
  --namespace trading \
  --name trade-matching-sa \
  --role-name EKSTradeMatchingRole \
  --attach-policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/TradeMatchingPolicy \
  --approve
```

### 3.2 Create IAM Policy for Application

```bash
# Create IAM policy
cat > trade-matching-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::trade-documents-production-*/|*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:us-east-1:$(aws sts get-caller-identity --query Account --output text):table/BankTradeData",
                "arn:aws:dynamodb:us-east-1:$(aws sts get-caller-identity --query Account --output text):table/CounterpartyTradeData"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                "arn:aws:bedrock:*::foundation-model/amazon.nova-*"
            ]
        }
    ]
}
EOF

aws iam create-policy \
  --policy-name TradeMatchingPolicy \
  --policy-document file://trade-matching-policy.json
```

### 3.3 Deploy Application

```yaml
# Create k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: trade-matching-config
  namespace: trading
data:
  AWS_REGION: "us-east-1"
  S3_BUCKET_NAME: "trade-documents-production-ACCOUNT_ID"
  DYNAMODB_BANK_TABLE: "BankTradeData"
  DYNAMODB_COUNTERPARTY_TABLE: "CounterpartyTradeData"
  LOG_LEVEL: "INFO"
```

```bash
# Apply configuration
envsubst < k8s/configmap.yaml | kubectl apply -f -

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Verify deployment
kubectl get pods -n trading
kubectl get services -n trading
kubectl logs -f deployment/trade-matching-system -n trading
```

### 3.4 Create Secrets

```bash
# Create secret for sensitive data
kubectl create secret generic aws-config \
  --from-literal=sqs-queue-url=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/bank-documents-production \
  --namespace trading

# Verify secret
kubectl get secrets -n trading
```

## Step 4: Lambda Function Deployment

### 4.1 Package Lambda Function

```bash
# Create deployment package
mkdir lambda-deployment
cd lambda-deployment

# Copy Lambda code
cp ../lambda-function/main.py .

# Install dependencies
pip install requests boto3 -t .

# Create deployment package
zip -r trade-document-processor.zip .
```

### 4.2 Deploy Lambda Function

```bash
# Deploy Lambda using SAM or CloudFormation
aws cloudformation create-stack \
  --stack-name trade-matching-lambda \
  --template-body file://lambda-deployment.yaml \
  --parameters ParameterKey=Environment,ParameterValue=production \
               ParameterKey=EKSServiceEndpoint,ParameterValue=http://trade-matching-service.trading.svc.cluster.local/process \
               ParameterKey=SNSTopicArn,ParameterValue=arn:aws:sns:us-east-1:ACCOUNT_ID:trade-processing-notifications-production \
  --capabilities CAPABILITY_IAM

# Wait for deployment
aws cloudformation wait stack-create-complete \
  --stack-name trade-matching-lambda
```

## Step 5: Monitoring and Observability

### 5.1 Deploy CloudWatch Container Insights

```bash
# Deploy CloudWatch agent
curl -O https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml

# Update cluster name in the file
sed -i 's/{{cluster_name}}/trade-matching-cluster/g' cwagent-fluentd-quickstart.yaml
sed -i 's/{{region_name}}/us-east-1/g' cwagent-fluentd-quickstart.yaml

# Deploy
kubectl apply -f cwagent-fluentd-quickstart.yaml

# Verify deployment
kubectl get pods -n amazon-cloudwatch
```

### 5.2 Create CloudWatch Dashboard

```bash
# Deploy monitoring stack
aws cloudformation create-stack \
  --stack-name trade-matching-monitoring \
  --template-body file://monitoring-stack.yaml \
  --capabilities CAPABILITY_IAM
```

### 5.3 Setup Prometheus and Grafana (Optional)

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set grafana.adminPassword=your-secure-password

# Get Grafana admin password
kubectl get secret --namespace monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# Port forward to access Grafana
kubectl port-forward --namespace monitoring svc/prometheus-grafana 3000:80
```

## Step 6: Testing and Validation

### 6.1 Upload Test Documents

```bash
# Upload test documents to S3
aws s3 cp sample-bank-trade.pdf s3://trade-documents-production-ACCOUNT_ID/BANK/2024/01/01/test-bank-001.pdf
aws s3 cp sample-counterparty-trade.pdf s3://trade-documents-production-ACCOUNT_ID/COUNTERPARTY/2024/01/01/test-cp-001.pdf

# Monitor SQS queue
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/bank-documents-production \
  --attribute-names ApproximateNumberOfMessages

# Check Lambda logs
aws logs tail /aws/lambda/trade-document-processor-production --follow
```

### 6.2 Verify Processing

```bash
# Check pod logs
kubectl logs -f deployment/trade-matching-system -n trading

# Check processing status via API
kubectl port-forward service/trade-matching-service 8080:80 -n trading &
curl http://localhost:8080/status/test-bank-001

# Verify DynamoDB records
aws dynamodb scan --table-name BankTradeData --limit 5
aws dynamodb scan --table-name CounterpartyTradeData --limit 5
```

### 6.3 Load Testing

```bash
# Run load test
python load-test.py

# Monitor metrics during load test
# - CloudWatch metrics
# - Kubernetes metrics
# - Application logs
```

## Step 7: Security Hardening

### 7.1 Network Policies

```bash
# Apply network policies
kubectl apply -f k8s/network-policy.yaml

# Verify network policies
kubectl get networkpolicies -n trading
```

### 7.2 Pod Security Standards

```bash
# Apply pod security standards
kubectl label namespace trading \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

# Verify security policies
kubectl describe namespace trading
```

### 7.3 Secrets Management

```bash
# Install and configure External Secrets Operator (optional)
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets-system \
  --create-namespace

# Configure AWS Secrets Manager integration
kubectl apply -f k8s/secret-store.yaml
```

## Step 8: Backup and Disaster Recovery

### 8.1 DynamoDB Backup

```bash
# Enable point-in-time recovery
aws dynamodb update-continuous-backups \
  --table-name BankTradeData \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups \
  --table-name CounterpartyTradeData \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Create backup CronJob
kubectl apply -f k8s/backup-cronjob.yaml
```

### 8.2 EKS Backup

```bash
# Install Velero for cluster backup
wget https://github.com/vmware-tanzu/velero/releases/download/v1.12.1/velero-v1.12.1-linux-amd64.tar.gz
tar -xzf velero-v1.12.1-linux-amd64.tar.gz
sudo mv velero-v1.12.1-linux-amd64/velero /usr/local/bin/

# Create S3 bucket for backups
aws s3 mb s3://trade-matching-backups-ACCOUNT_ID

# Install Velero
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.1 \
  --bucket trade-matching-backups-ACCOUNT_ID \
  --backup-location-config region=us-east-1 \
  --snapshot-location-config region=us-east-1

# Create backup schedule
velero schedule create daily-backup \
  --schedule="@daily" \
  --include-namespaces trading
```

## Step 9: Performance Optimization

### 9.1 Cluster Autoscaler

```bash
# Deploy cluster autoscaler
kubectl apply -f k8s/cluster-autoscaler.yaml

# Verify deployment
kubectl get deployment cluster-autoscaler -n kube-system
kubectl logs -f deployment/cluster-autoscaler -n kube-system
```

### 9.2 Vertical Pod Autoscaler

```bash
# Install VPA
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler/
./hack/vpa-install.sh

# Apply VPA to application
kubectl apply -f k8s/vpa.yaml
```

### 9.3 Resource Optimization

```bash
# Monitor resource usage
kubectl top nodes
kubectl top pods -n trading

# Adjust resource requests/limits based on monitoring
kubectl patch deployment trade-matching-system -n trading -p '{"spec":{"template":{"spec":{"containers":[{"name":"trade-processor","resources":{"requests":{"memory":"2Gi","cpu":"1000m"},"limits":{"memory":"4Gi","cpu":"2000m"}}}]}}}}'
```

## Step 10: Production Readiness Checklist

### 10.1 Security Checklist

- [ ] IAM roles follow least privilege principle
- [ ] Network policies implemented
- [ ] Pod security standards enforced
- [ ] Secrets properly managed
- [ ] S3 bucket encryption enabled
- [ ] DynamoDB encryption at rest enabled
- [ ] VPC endpoints configured for AWS services

### 10.2 Monitoring Checklist

- [ ] CloudWatch Container Insights enabled
- [ ] Application metrics exposed
- [ ] Log aggregation configured
- [ ] Alerting rules configured
- [ ] Dashboard created
- [ ] Health checks implemented

### 10.3 Reliability Checklist

- [ ] Multi-AZ deployment
- [ ] Auto-scaling configured
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan tested
- [ ] Circuit breakers implemented
- [ ] Graceful degradation tested

### 10.4 Performance Checklist

- [ ] Load testing completed
- [ ] Resource limits optimized
- [ ] Caching strategies implemented
- [ ] Database performance tuned
- [ ] CDN configured for static assets

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Pod Stuck in Pending State

```bash
# Check node resources
kubectl describe nodes

# Check pod events
kubectl describe pod <pod-name> -n trading

# Common solutions:
# - Increase cluster capacity
# - Adjust resource requests
# - Check node selectors/tolerations
```

#### 2. Lambda Function Timeout

```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/trade-document-processor

# Common solutions:
# - Increase timeout setting
# - Optimize EKS service response time
# - Implement async processing
```

#### 3. DynamoDB Throttling

```bash
# Check DynamoDB metrics
aws dynamodb describe-table --table-name BankTradeData

# Solutions:
# - Enable auto-scaling
# - Implement exponential backoff
# - Optimize query patterns
```

#### 4. S3 Event Not Triggering

```bash
# Check S3 event configuration
aws s3api get-bucket-notification-configuration --bucket trade-documents-production-ACCOUNT_ID

# Check SQS queue
aws sqs get-queue-attributes --queue-url QUEUE_URL --attribute-names All

# Solutions:
# - Verify S3 bucket policies
# - Check SQS queue permissions
# - Validate file naming conventions
```

## Maintenance Procedures

### 1. Regular Updates

```bash
# Update cluster
eksctl upgrade cluster --name trade-matching-cluster

# Update node groups
eksctl upgrade nodegroup --cluster trade-matching-cluster --name worker-nodes

# Update application
docker build -t trade-matching-system:v2.0 .
docker tag trade-matching-system:v2.0 $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/trade-matching-system:v2.0
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/trade-matching-system:v2.0

kubectl set image deployment/trade-matching-system trade-processor=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/trade-matching-system:v2.0 -n trading
```

### 2. Monitoring and Alerting

```bash
# Check system health daily
kubectl get pods -A
kubectl get nodes
aws cloudformation describe-stacks

# Review metrics weekly
# - Application performance
# - Resource utilization
# - Error rates
# - Cost optimization opportunities
```

### 3. Backup Verification

```bash
# Test DynamoDB restore
aws dynamodb restore-table-from-backup \
  --target-table-name BankTradeData-test \
  --backup-arn arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/BankTradeData/backup/BACKUP_ARN

# Test Velero restore
velero restore create --from-backup daily-backup-20240101000000
```

## Cost Optimization

### 1. Spot Instances

```bash
# Add spot instance node group
eksctl create nodegroup \
  --cluster trade-matching-cluster \
  --name spot-workers \
  --instance-types m5.large,m5.xlarge,m4.large \
  --spot \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 5
```

### 2. Resource Right-sizing

```bash
# Use VPA recommendations
kubectl get vpa trade-matching-vpa -n trading -o yaml

# Implement resource requests based on actual usage
kubectl patch deployment trade-matching-system -n trading --patch-file resource-patch.yaml
```

### 3. Storage Optimization

```bash
# Configure S3 lifecycle policies
aws s3api put-bucket-lifecycle-configuration \
  --bucket trade-documents-production-ACCOUNT_ID \
  --lifecycle-configuration file://lifecycle-policy.json
```

This comprehensive deployment guide provides a production-ready setup for the AI Trade Matching System on EKS with proper monitoring, security, and scalability considerations.