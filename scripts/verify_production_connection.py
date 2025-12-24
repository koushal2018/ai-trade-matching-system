#!/usr/bin/env python3
"""
Verify connection to production AWS resources.
This script checks connectivity and permissions for all production resources.
"""

import boto3
import os
import sys
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.dev')

def check_aws_credentials():
    """Check if AWS credentials are configured."""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Credentials configured")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("❌ AWS credentials not configured")
        print("   Run: aws configure")
        return False
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
        return False

def check_s3_bucket():
    """Check S3 bucket access."""
    bucket_name = os.getenv('S3_BUCKET_NAME', 'trade-matching-bucket')
    try:
        s3 = boto3.client('s3')
        
        # Check if bucket exists and is accessible
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 Bucket accessible: {bucket_name}")
        
        # List objects to check permissions
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        object_count = response.get('KeyCount', 0)
        print(f"   Objects in bucket: {object_count}")
        
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"❌ S3 Bucket not found: {bucket_name}")
        elif error_code == '403':
            print(f"❌ S3 Bucket access denied: {bucket_name}")
        else:
            print(f"❌ S3 Error: {e}")
        return False

def check_dynamodb_table(table_name, description):
    """Check DynamoDB table access."""
    try:
        dynamodb = boto3.client('dynamodb')
        
        # Check if table exists
        response = dynamodb.describe_table(TableName=table_name)
        status = response['Table']['TableStatus']
        item_count = response['Table']['ItemCount']
        
        print(f"✅ DynamoDB Table accessible: {table_name}")
        print(f"   Status: {status}, Items: {item_count}")
        
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print(f"❌ DynamoDB Table not found: {table_name}")
        elif error_code == 'AccessDeniedException':
            print(f"❌ DynamoDB Table access denied: {table_name}")
        else:
            print(f"❌ DynamoDB Error for {table_name}: {e}")
        return False

def check_bedrock_access():
    """Check Bedrock model access."""
    model_id = os.getenv('BEDROCK_MODEL', 'anthropic.claude-sonnet-4-20250514-v1:0')
    try:
        bedrock = boto3.client('bedrock-runtime')
        
        # Try to invoke the model with a simple test
        response = bedrock.invoke_model(
            modelId=model_id,
            body='{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10}',
            contentType='application/json'
        )
        
        print(f"✅ Bedrock Model accessible: {model_id}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ Bedrock Model access denied: {model_id}")
        elif error_code == 'ValidationException':
            print(f"❌ Bedrock Model not found: {model_id}")
        else:
            print(f"❌ Bedrock Error: {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 Verifying Production AWS Resource Connections")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Region: {os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}")
    print()
    
    results = []
    
    # Check AWS credentials
    print("1. Checking AWS Credentials...")
    results.append(check_aws_credentials())
    print()
    
    # Check S3 bucket
    print("2. Checking S3 Bucket...")
    results.append(check_s3_bucket())
    print()
    
    # Check DynamoDB tables
    print("3. Checking DynamoDB Tables...")
    tables = [
        ('CounterpartyTradeData', 'Counterparty trade data'),
        ('BankTradeData', 'Bank trade data'),
        ('TradeMatches', 'Trade matches'),
        ('ExceptionsTable', 'Exceptions'),
        ('AgentRegistry', 'Agent registry'),
        ('HITLReviews', 'HITL reviews'),
        ('AuditTrail', 'Audit trail'),
        ('trade-matching-system-processing-status', 'Processing status')
    ]
    
    for table_name, description in tables:
        results.append(check_dynamodb_table(table_name, description))
    print()
    
    # Check Bedrock access
    print("4. Checking Bedrock Model Access...")
    results.append(check_bedrock_access())
    print()
    
    # Summary
    print("=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(results)
    
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    
    if passed_checks == total_checks:
        print("🎉 All production resources are accessible!")
        print("✅ Ready for development work")
        return 0
    else:
        print("⚠️  Some production resources are not accessible")
        print("❌ Please fix the issues above before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())