# EKS Deployment Specifications for AI Trade Matching System

## Architecture Overview

This specification outlines deploying the AI Trade Matching System on Amazon EKS with S3 event-driven processing, replacing the current file-based approach with a cloud-native, scalable solution.

## System Components

### 1. EKS Cluster Configuration

```yaml
# eks-cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: trade-matching-cluster
  region: us-east-1
  version: "1.28"

nodeGroups:
  - name: worker-nodes
    instanceType: m5.large
    desiredCapacity: 3
    minSize: 2
    maxSize: 10
    volumeSize: 50
    ssh:
      allow: false
    iam:
      withAddonPolicies:
        albIngress: true
        autoScaler: true
        cloudWatch: true
        ebs: true
        efs: true

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
  - name: aws-ebs-csi-driver
  - name: aws-load-balancer-controller

cloudWatch:
  clusterLogging:
    enableTypes: ["*"]
```

### 2. Application Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trade-matching-system
  namespace: trading
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trade-matching-system
  template:
    metadata:
      labels:
        app: trade-matching-system
    spec:
      serviceAccountName: trade-matching-sa
      containers:
      - name: trade-processor
        image: trade-matching-system:latest
        ports:
        - containerPort: 8080
        env:
        - name: AWS_REGION
          value: "us-east-1"
        - name: S3_BUCKET_NAME
          value: "trade-documents-bucket"
        - name: DYNAMODB_BANK_TABLE
          value: "BankTradeData"
        - name: DYNAMODB_COUNTERPARTY_TABLE
          value: "CounterpartyTradeData"
        - name: SQS_QUEUE_URL
          valueFrom:
            secretKeyRef:
              name: aws-config
              key: sqs-queue-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp/processing
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 5
      volumes:
      - name: temp-storage
        emptyDir:
          sizeLimit: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: trade-matching-service
  namespace: trading
spec:
  selector:
    app: trade-matching-system
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

### 3. Service Account & RBAC

```yaml
# service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: trade-matching-sa
  namespace: trading
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT-ID:role/EKSTradeMatchingRole
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: trading
  name: trade-matching-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: trade-matching-binding
  namespace: trading
subjects:
- kind: ServiceAccount
  name: trade-matching-sa
  namespace: trading
roleRef:
  kind: Role
  name: trade-matching-role
  apiGroup: rbac.authorization.k8s.io
```

## S3 Event-Driven Architecture

### 1. S3 Bucket Configuration

```yaml
# s3-bucket-config.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'S3 bucket for trade document processing'

Resources:
  TradeDocumentsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: trade-documents-bucket
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      NotificationConfiguration:
        QueueConfigurations:
          - Event: s3:ObjectCreated:*
            Queue: !GetAtt TradeProcessingQueue.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: "BANK/"
                  - Name: suffix
                    Value: ".pdf"
          - Event: s3:ObjectCreated:*
            Queue: !GetAtt TradeProcessingQueue.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: "COUNTERPARTY/"
                  - Name: suffix
                    Value: ".pdf"

  TradeProcessingQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: trade-processing-queue
      VisibilityTimeoutSeconds: 900
      MessageRetentionPeriod: 1209600  # 14 days
      DeadLetterTargetArn: !GetAtt DeadLetterQueue.Arn
      MaxReceiveCount: 3

  DeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: trade-processing-dlq
      MessageRetentionPeriod: 1209600  # 14 days

  QueuePolicy:
    Type: AWS::SQS::QueuePolicy
    Properties:
      Queues:
        - !Ref TradeProcessingQueue
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: s3.amazonaws.com
            Action: sqs:SendMessage
            Resource: !GetAtt TradeProcessingQueue.Arn
            Condition:
              ArnEquals:
                aws:SourceArn: !Sub "${TradeDocumentsBucket}"
```

### 2. Lambda Function for SQS Processing

```python
# lambda-sqs-processor.py
import json
import boto3
import requests
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to process S3 events from SQS and trigger EKS processing
    """

    # Initialize clients
    sqs = boto3.client('sqs')

    # EKS service endpoint (internal ALB)
    EKS_SERVICE_ENDPOINT = "http://trade-matching-service.trading.svc.cluster.local/process"

    processed_count = 0
    errors = []

    try:
        for record in event['Records']:
            # Parse SQS message
            s3_event = json.loads(record['body'])

            for s3_record in s3_event['Records']:
                bucket = s3_record['s3']['bucket']['name']
                key = s3_record['s3']['object']['key']

                # Determine source type from S3 path
                source_type = "BANK" if key.startswith("BANK/") else "COUNTERPARTY"

                # Prepare payload for EKS service
                payload = {
                    "s3_bucket": bucket,
                    "s3_key": key,
                    "source_type": source_type,
                    "event_time": s3_record['eventTime'],
                    "unique_identifier": key.split('/')[-1].replace('.pdf', '')
                }

                # Send to EKS service
                response = requests.post(
                    EKS_SERVICE_ENDPOINT,
                    json=payload,
                    timeout=30,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    processed_count += 1
                    print(f"Successfully triggered processing for {key}")
                else:
                    error_msg = f"Failed to process {key}: {response.text}"
                    errors.append(error_msg)
                    print(error_msg)

    except Exception as e:
        error_msg = f"Lambda processing error: {str(e)}"
        errors.append(error_msg)
        print(error_msg)

    return {
        'statusCode': 200 if not errors else 207,
        'body': json.dumps({
            'processed_count': processed_count,
            'errors': errors
        })
    }
```

### 3. Enhanced Application Code for EKS

```python
# eks-enhanced-main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import boto3
from latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import tempfile
import os
from pathlib import Path

app = FastAPI(title="Trade Matching System", version="1.0.0")

class ProcessingRequest(BaseModel):
    s3_bucket: str
    s3_key: str
    source_type: str
    event_time: str
    unique_identifier: str

class ProcessingStatus(BaseModel):
    status: str
    message: str
    progress: int

# Global status tracking
processing_status = {}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trade-matching-system"}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "service": "trade-matching-system"}

@app.post("/process")
async def process_trade_document(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process trade document from S3 event trigger
    """
    try:
        # Start background processing
        background_tasks.add_task(process_document_async, request)

        # Initialize status tracking
        processing_status[request.unique_identifier] = ProcessingStatus(
            status="initiated",
            message=f"Processing started for {request.s3_key}",
            progress=0
        )

        return {
            "message": "Processing initiated",
            "unique_identifier": request.unique_identifier,
            "status_endpoint": f"/status/{request.unique_identifier}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate processing: {str(e)}")

@app.get("/status/{unique_identifier}")
async def get_processing_status(unique_identifier: str):
    """
    Get processing status for a specific document
    """
    if unique_identifier not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")

    return processing_status[unique_identifier]

async def process_document_async(request: ProcessingRequest):
    """
    Background task to process trade document
    """
    unique_id = request.unique_identifier

    try:
        # Update status
        processing_status[unique_id] = ProcessingStatus(
            status="downloading",
            message="Downloading document from S3",
            progress=10
        )

        # Download from S3 to temporary location
        s3_client = boto3.client('s3')

        # Create temporary directory structure
        temp_dir = Path(f"/tmp/processing/{unique_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Determine folder structure based on source type
        if request.source_type == "BANK":
            local_dir = temp_dir / "data" / "BANK"
        else:
            local_dir = temp_dir / "data" / "COUNTERPARTY"

        local_dir.mkdir(parents=True, exist_ok=True)

        # Download file
        local_file_path = local_dir / Path(request.s3_key).name
        s3_client.download_file(request.s3_bucket, request.s3_key, str(local_file_path))

        # Update status
        processing_status[unique_id] = ProcessingStatus(
            status="processing",
            message="Running CrewAI processing pipeline",
            progress=30
        )

        # Set up DynamoDB MCP server
        dynamodb_params = StdioServerParameters(
            command="uvx",
            args=["awslabs.dynamodb-mcp-server@latest"],
            env={
                "DDB-MCP-READONLY": "false",
                "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
                "FASTMCP_LOG_LEVEL": "ERROR"
            }
        )

        # Process with CrewAI
        with MCPServerAdapter(dynamodb_params) as dynamodb_tools:
            crew_instance = LatestTradeMatchingAgent(dynamodb_tools=list(dynamodb_tools))

            inputs = {
                'document_path': str(local_file_path),
                'unique_identifier': unique_id,
            }

            # Update status
            processing_status[unique_id] = ProcessingStatus(
                status="processing",
                message="CrewAI agents processing document",
                progress=60
            )

            # Run the crew
            result = crew_instance.crew().kickoff(inputs=inputs)

            # Update status
            processing_status[unique_id] = ProcessingStatus(
                status="completed",
                message="Document processing completed successfully",
                progress=100
            )

        # Cleanup temporary files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        processing_status[unique_id] = ProcessingStatus(
            status="failed",
            message=f"Processing failed: {str(e)}",
            progress=-1
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Infrastructure Components

### 1. DynamoDB Tables

```yaml
# dynamodb-tables.yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  BankTradeDataTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: BankTradeData
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: Trade_ID
          AttributeType: S
      KeySchema:
        - AttributeName: Trade_ID
          KeyType: HASH
      StreamSpecification:
        StreamViewType: NEW_AND_OLD_IMAGES
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      Tags:
        - Key: Environment
          Value: production
        - Key: Application
          Value: trade-matching

  CounterpartyTradeDataTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: CounterpartyTradeData
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: Trade_ID
          AttributeType: S
      KeySchema:
        - AttributeName: Trade_ID
          KeyType: HASH
      StreamSpecification:
        StreamViewType: NEW_AND_OLD_IMAGES
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      Tags:
        - Key: Environment
          Value: production
        - Key: Application
          Value: trade-matching
```

### 2. IAM Roles and Policies

```yaml
# iam-roles.yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  EKSTradeMatchingRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: EKSTradeMatchingRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Federated: !Sub 'arn:aws:iam::${AWS::AccountId}:oidc-provider/${OIDC_PROVIDER}'
            Action: 'sts:AssumeRoleWithWebIdentity'
            Condition:
              StringEquals:
                '${OIDC_PROVIDER}:sub': 'system:serviceaccount:trading:trade-matching-sa'
      Policies:
        - PolicyName: TradeMatchingPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:PutObject'
                  - 's3:DeleteObject'
                Resource:
                  - 'arn:aws:s3:::trade-documents-bucket/*'
              - Effect: Allow
                Action:
                  - 'dynamodb:GetItem'
                  - 'dynamodb:PutItem'
                  - 'dynamodb:UpdateItem'
                  - 'dynamodb:DeleteItem'
                  - 'dynamodb:Query'
                  - 'dynamodb:Scan'
                Resource:
                  - !Sub 'arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/BankTradeData'
                  - !Sub 'arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/CounterpartyTradeData'
              - Effect: Allow
                Action:
                  - 'bedrock:InvokeModel'
                  - 'bedrock:InvokeModelWithResponseStream'
                Resource:
                  - 'arn:aws:bedrock:*::foundation-model/anthropic.claude-*'
                  - 'arn:aws:bedrock:*::foundation-model/amazon.nova-*'
              - Effect: Allow
                Action:
                  - 'sqs:ReceiveMessage'
                  - 'sqs:DeleteMessage'
                  - 'sqs:GetQueueAttributes'
                Resource: !Sub 'arn:aws:sqs:${AWS::Region}:${AWS::AccountId}:trade-processing-queue'

  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: TradeLambdaExecutionRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: 'sts:AssumeRole'
      ManagedPolicyArns:
        - 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        - 'arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole'
      Policies:
        - PolicyName: SQSProcessingPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 'sqs:ReceiveMessage'
                  - 'sqs:DeleteMessage'
                  - 'sqs:GetQueueAttributes'
                Resource: !Sub 'arn:aws:sqs:${AWS::Region}:${AWS::AccountId}:trade-processing-queue'
```

## Monitoring and Observability

### 1. CloudWatch Configuration

```yaml
# monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cloudwatch-config
  namespace: trading
data:
  cwagentconfig.json: |
    {
      "metrics": {
        "namespace": "TradeMatching/EKS",
        "metrics_collected": {
          "cpu": {
            "measurement": [
              "cpu_usage_idle",
              "cpu_usage_iowait",
              "cpu_usage_user",
              "cpu_usage_system"
            ],
            "metrics_collection_interval": 60
          },
          "disk": {
            "measurement": [
              "used_percent"
            ],
            "metrics_collection_interval": 60,
            "resources": [
              "*"
            ]
          },
          "diskio": {
            "measurement": [
              "io_time"
            ],
            "metrics_collection_interval": 60,
            "resources": [
              "*"
            ]
          },
          "mem": {
            "measurement": [
              "mem_used_percent"
            ],
            "metrics_collection_interval": 60
          }
        }
      },
      "logs": {
        "logs_collected": {
          "files": {
            "collect_list": [
              {
                "file_path": "/var/log/pods/trading_trade-matching-system-*/*/*.log",
                "log_group_name": "/aws/eks/trade-matching/application",
                "log_stream_name": "{container_name}-{pod_name}",
                "timezone": "UTC"
              }
            ]
          }
        }
      }
    }
```

### 2. Application Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Metrics
DOCUMENTS_PROCESSED = Counter('trade_documents_processed_total', 'Total documents processed', ['source_type', 'status'])
PROCESSING_DURATION = Histogram('trade_processing_duration_seconds', 'Time spent processing documents', ['source_type'])
ACTIVE_PROCESSING = Gauge('trade_active_processing', 'Currently processing documents')
CREW_AGENT_DURATION = Histogram('crew_agent_duration_seconds', 'Agent processing time', ['agent_name'])

def record_processing_metrics(source_type: str, status: str, duration: float):
    """Record processing metrics"""
    DOCUMENTS_PROCESSED.labels(source_type=source_type, status=status).inc()
    PROCESSING_DURATION.labels(source_type=source_type).observe(duration)

def track_agent_performance(agent_name: str, duration: float):
    """Track individual agent performance"""
    CREW_AGENT_DURATION.labels(agent_name=agent_name).observe(duration)

# Start metrics server
def start_metrics_server():
    start_http_server(9090)
```

## Deployment Process

### 1. Pre-deployment Checklist

- [ ] EKS cluster created and configured
- [ ] IAM roles and policies applied
- [ ] S3 bucket and SQS queue configured
- [ ] DynamoDB tables created
- [ ] Docker image built and pushed to ECR
- [ ] Lambda function deployed
- [ ] Monitoring and logging configured

### 2. Deployment Commands

```bash
# Create namespace
kubectl create namespace trading

# Deploy application
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n trading
kubectl get services -n trading

# Check logs
kubectl logs -f deployment/trade-matching-system -n trading

# Monitor processing
kubectl port-forward service/trade-matching-service 8080:80 -n trading
```

### 3. Testing the Pipeline

```bash
# Upload test document to trigger processing
aws s3 cp sample-trade.pdf s3://trade-documents-bucket/BANK/test-trade-001.pdf

# Monitor SQS queue
aws sqs get-queue-attributes --queue-url https://sqs.us-east-1.amazonaws.com/ACCOUNT/trade-processing-queue

# Check processing status
curl http://localhost:8080/status/test-trade-001

# Verify DynamoDB records
aws dynamodb scan --table-name BankTradeData
```

## Scaling and Performance

### 1. Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: trade-matching-hpa
  namespace: trading
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: trade-matching-system
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Cluster Autoscaler

```yaml
# cluster-autoscaler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/trade-matching-cluster
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
```

## Security Considerations

### 1. Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: trade-matching-network-policy
  namespace: trading
spec:
  podSelector:
    matchLabels:
      app: trade-matching-system
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          app: aws-load-balancer-controller
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS to AWS services
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

### 2. Pod Security Standards

```yaml
# pod-security.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: trading
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Disaster Recovery

### 1. Backup Strategy

```yaml
# backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: dynamodb-backup
  namespace: trading
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: amazon/aws-cli:latest
            command:
            - /bin/sh
            - -c
            - |
              aws dynamodb create-backup --table-name BankTradeData --backup-name "BankTradeData-$(date +%Y%m%d)"
              aws dynamodb create-backup --table-name CounterpartyTradeData --backup-name "CounterpartyTradeData-$(date +%Y%m%d)"
          restartPolicy: OnFailure
```

### 2. Multi-AZ Deployment

The EKS cluster should be configured across multiple availability zones with proper data replication and failover mechanisms.

## Cost Optimization

### 1. Spot Instances

```yaml
# spot-nodegroup.yaml
nodeGroups:
  - name: spot-workers
    instancesDistribution:
      maxPrice: 0.10
      instanceTypes: ["m5.large", "m5.xlarge", "m4.large"]
      onDemandBaseCapacity: 1
      onDemandPercentageAboveBaseCapacity: 0
      spotInstancePools: 3
    desiredCapacity: 3
    minSize: 1
    maxSize: 10
```

### 2. Resource Optimization

- Use resource requests and limits appropriately
- Implement efficient caching strategies
- Consider using AWS Fargate for Lambda-like pricing model
- Use S3 Intelligent Tiering for document storage

This comprehensive specification provides a production-ready EKS deployment with S3 event-driven processing, maintaining the AI-powered trade matching capabilities while adding cloud-native scalability, monitoring, and security features.