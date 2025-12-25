# Security Quick Fixes - Implementation Guide
## Immediate Actions for HTTP Agent Orchestrator

**Estimated Time**: 2-3 hours  
**Priority**: 🔴 CRITICAL  
**Target Completion**: Within 24 hours

---

## Fix 1: Remove Hardcoded ARNs (30 minutes)

### Step 1: Create Parameter Store entries

```bash
#!/bin/bash
# scripts/setup_parameter_store.sh

AWS_REGION="us-east-1"
ACCOUNT_ID="401552979575"

# Create parameters for each agent
aws ssm put-parameter \
  --name "/agentcore/agents/pdf-adapter/arn" \
  --value "arn:aws:bedrock-agentcore:us-east-1:${ACCOUNT_ID}:runtime/pdf_adapter_agent-Az72YP53FJ" \
  --type "String" \
  --description "PDF Adapter Agent Runtime ARN" \
  --tags "Key=Environment,Value=production" "Key=ManagedBy,Value=terraform" \
  --region ${AWS_REGION}

aws ssm put-parameter \
  --name "/agentcore/agents/trade-extraction/arn" \
  --value "arn:aws:bedrock-agentcore:us-east-1:${ACCOUNT_ID}:runtime/agent_matching_ai-KrY5QeCyXe" \
  --type "String" \
  --description "Trade Extraction Agent Runtime ARN" \
  --region ${AWS_REGION}

aws ssm put-parameter \
  --name "/agentcore/agents/trade-matching/arn" \
  --value "arn:aws:bedrock-agentcore:us-east-1:${ACCOUNT_ID}:runtime/trade_matching_ai-r8eaGb4u7B" \
  --type "String" \
  --description "Trade Matching Agent Runtime ARN" \
  --region ${AWS_REGION}

aws ssm put-parameter \
  --name "/agentcore/agents/exception-management/arn" \
  --value "arn:aws:bedrock-agentcore:us-east-1:${ACCOUNT_ID}:runtime/exception_manager-uliBS5DsX3" \
  --type "String" \
  --description "Exception Management Agent Runtime ARN" \
  --region ${AWS_REGION}

echo "✅ Parameter Store entries created"
```

### Step 2: Update orchestrator code

Replace lines 42-47 in `http_agent_orchestrator.py`:

```python
# OLD - Remove this
PDF_ADAPTER_ARN = os.getenv("PDF_ADAPTER_AGENT_ARN", "arn:aws:bedrock-agentcore:...")
TRADE_EXTRACTION_ARN = os.getenv("TRADE_EXTRACTION_AGENT_ARN", "arn:aws:bedrock-agentcore:...")
# ...

# NEW - Add this
from functools import lru_cache

@lru_cache(maxsize=None)
def get_agent_arns() -> Dict[str, str]:
    """Fetch agent ARNs from Parameter Store with caching."""
    ssm = boto3.client('ssm', region_name=REGION)
    
    parameter_names = [
        '/agentcore/agents/pdf-adapter/arn',
        '/agentcore/agents/trade-extraction/arn',
        '/agentcore/agents/trade-matching/arn',
        '/agentcore/agents/exception-management/arn'
    ]
    
    try:
        response = ssm.get_parameters(Names=parameter_names, WithDecryption=False)
        
        if not response['Parameters']:
            raise RuntimeError("No agent ARNs found in Parameter Store")
        
        arns = {}
        for param in response['Parameters']:
            agent_name = param['Name'].split('/')[-2]
            arns[agent_name] = param['Value']
        
        logger.info(f"Loaded {len(arns)} agent ARNs from Parameter Store")
        return arns
        
    except Exception as e:
        logger.error(f"Failed to fetch agent ARNs from Parameter Store: {e}")
        raise RuntimeError(
            "Agent configuration unavailable. Ensure Parameter Store is configured."
        )

# Load ARNs at module initialization - fail fast if missing
try:
    AGENT_ARNS = get_agent_arns()
    PDF_ADAPTER_ARN = AGENT_ARNS.get('pdf-adapter')
    TRADE_EXTRACTION_ARN = AGENT_ARNS.get('trade-extraction')
    TRADE_MATCHING_ARN = AGENT_ARNS.get('trade-matching')
    EXCEPTION_MANAGEMENT_ARN = AGENT_ARNS.get('exception-management')
except Exception as e:
    logger.critical(f"FATAL: Cannot load agent configuration: {e}")
    raise
```

### Step 3: Update IAM role

```bash
# Add SSM permissions to orchestrator role
aws iam put-role-policy \
  --role-name AgentCoreOrchestratorRole \
  --policy-name ParameterStoreAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["ssm:GetParameters"],
      "Resource": "arn:aws:ssm:us-east-1:401552979575:parameter/agentcore/agents/*"
    }]
  }'
```

### Step 4: Test

```bash
python deployment/swarm_agentcore/test_local_orchestrator.py TEST_DOC BANK
```

---

## Fix 2: Enable Structured Logging (20 minutes)

### Step 1: Install dependencies

```bash
cd deployment/swarm_agentcore
pip install aws-lambda-powertools
```

### Step 2: Update requirements.txt

```txt
# Add to requirements.txt
aws-lambda-powertools>=2.0.0
```

### Step 3: Replace logging configuration

Replace lines 28-32 in `http_agent_orchestrator.py`:

```python
# OLD - Remove this
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)

# NEW - Add this
from aws_lambda_powertools import Logger

logger = Logger(
    service="http-agent-orchestrator",
    level="INFO",
    log_uncaught_exceptions=True
)

# Update all logger calls to use structured format
# Example:
logger.info(
    "Agent invocation started",
    extra={
        "correlation_id": correlation_id,
        "agent_name": agent_name,
        "agent_arn": runtime_arn
    }
)
```

---

## Fix 3: Add IAM Policy Validation (30 minutes)

### Add validation method to AgentCoreClient class:

```python
def validate_permissions(self) -> bool:
    """Validate execution role has required permissions."""
    iam = boto3.client('iam')
    sts = boto3.client('sts')
    
    try:
        identity = sts.get_caller_identity()
        role_arn = identity.get('Arn')
        
        if not role_arn or 'assumed-role' not in role_arn:
            logger.warning("Not running with assumed role - skipping validation")
            return True
        
        # Extract role name from assumed-role ARN
        role_name = role_arn.split('/')[-2]
        
        required_actions = [
            'bedrock-agentcore:InvokeAgent',
            'ssm:GetParameters',
            'logs:CreateLogGroup',
            'logs:CreateLogStream',
            'logs:PutLogEvents'
        ]
        
        response = iam.simulate_principal_policy(
            PolicySourceArn=f"arn:aws:iam::{identity['Account']}:role/{role_name}",
            ActionNames=required_actions
        )
        
        denied = [
            r['EvalActionName'] 
            for r in response['EvaluationResults'] 
            if r['EvalDecision'] != 'allowed'
        ]
        
        if denied:
            logger.error(f"Missing required permissions: {denied}")
            return False
        
        logger.info("IAM permissions validated successfully")
        return True
        
    except Exception as e:
        logger.warning(f"Could not validate IAM permissions: {e}")
        return True  # Fail open for backward compatibility

# Call in __init__
def __init__(self, region: str = REGION):
    self.region = region
    self.session = boto3.Session()
    self.endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com"
    
    # Validate permissions on initialization
    if not self.validate_permissions():
        logger.warning("Running with insufficient permissions - some operations may fail")
```

---

## Fix 4: Enable CloudTrail Data Events (15 minutes)

### Create CloudTrail configuration:

```bash
# scripts/enable_cloudtrail_data_events.sh

TRAIL_NAME="trade-matching-audit-trail"
S3_BUCKET="trade-matching-cloudtrail-logs"
REGION="us-east-1"

# Create S3 bucket for CloudTrail logs
aws s3 mb s3://${S3_BUCKET} --region ${REGION}

# Apply bucket policy
aws s3api put-bucket-policy --bucket ${S3_BUCKET} --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AWSCloudTrailAclCheck",
    "Effect": "Allow",
    "Principal": {"Service": "cloudtrail.amazonaws.com"},
    "Action": "s3:GetBucketAcl",
    "Resource": "arn:aws:s3:::'${S3_BUCKET}'"
  }, {
    "Sid": "AWSCloudTrailWrite",
    "Effect": "Allow",
    "Principal": {"Service": "cloudtrail.amazonaws.com"},
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::'${S3_BUCKET}'/AWSLogs/*",
    "Condition": {
      "StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}
    }
  }]
}'

# Create or update trail
aws cloudtrail create-trail \
  --name ${TRAIL_NAME} \
  --s3-bucket-name ${S3_BUCKET} \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --region ${REGION}

# Add data events
aws cloudtrail put-event-selectors \
  --trail-name ${TRAIL_NAME} \
  --event-selectors '[{
    "ReadWriteType": "All",
    "IncludeManagementEvents": true,
    "DataResources": [{
      "Type": "AWS::S3::Object",
      "Values": ["arn:aws:s3:::trade-matching-system-agentcore-production/*"]
    }, {
      "Type": "AWS::DynamoDB::Table",
      "Values": [
        "arn:aws:dynamodb:us-east-1:401552979575:table/BankTradeData",
        "arn:aws:dynamodb:us-east-1:401552979575:table/CounterpartyTradeData"
      ]
    }]
  }]' \
  --region ${REGION}

# Start logging
aws cloudtrail start-logging --name ${TRAIL_NAME} --region ${REGION}

echo "✅ CloudTrail data events enabled"
```

---

## Verification Checklist

After implementing all fixes:

```bash
# 1. Verify Parameter Store access
aws ssm get-parameters \
  --names /agentcore/agents/pdf-adapter/arn \
  --region us-east-1

# 2. Test orchestrator with new configuration
python deployment/swarm_agentcore/test_local_orchestrator.py TEST_DOC BANK

# 3. Verify CloudTrail is logging
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::S3::Object \
  --max-results 5 \
  --region us-east-1

# 4. Check CloudWatch Logs for structured logging
aws logs tail /aws/bedrock-agentcore/http-agent-orchestrator --follow

# 5. Verify IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::401552979575:role/AgentCoreOrchestratorRole \
  --action-names bedrock-agentcore:InvokeAgent ssm:GetParameters
```

---

## Rollback Plan

If issues occur:

```bash
# 1. Revert to environment variables
export PDF_ADAPTER_AGENT_ARN="arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/pdf_adapter_agent-Az72YP53FJ"
export TRADE_EXTRACTION_AGENT_ARN="arn:aws:bedrock-agentcore:us-east-1:401552979575:runtime/agent_matching_ai-KrY5QeCyXe"
# ... etc

# 2. Restore original code from git
git checkout HEAD -- deployment/swarm_agentcore/http_agent_orchestrator.py

# 3. Redeploy
cd deployment/swarm_agentcore
agentcore deploy
```

---

## Success Criteria

✅ No hardcoded ARNs in source code  
✅ All agent ARNs loaded from Parameter Store  
✅ Structured JSON logs in CloudWatch  
✅ IAM permissions validated at startup  
✅ CloudTrail data events capturing S3/DynamoDB access  
✅ All tests passing  
✅ No production incidents during rollout

---

**Next Steps**: After completing these fixes, proceed with the short-term actions in the full security assessment report.
