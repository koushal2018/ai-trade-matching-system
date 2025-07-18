import json
import boto3
import os
import traceback

def lambda_handler(event, context):
    """
    Diagnostic Lambda function to identify the root cause of 502 errors
    """
    try:
        print(f"Event received: {json.dumps(event)}")
        
        # Check environment variables
        bucket_name = os.environ.get('BUCKET_NAME', 'fab-otc-reconciliation-deployment')
        bank_table_name = os.environ.get('BANK_TABLE', 'BankTradeData')
        counterparty_table_name = os.environ.get('COUNTERPARTY_TABLE', 'CounterpartyTradeData')
        matches_table_name = os.environ.get('MATCHES_TABLE', 'TradeMatches')
        
        print(f"Environment variables:")
        print(f"BUCKET_NAME: {bucket_name}")
        print(f"BANK_TABLE: {bank_table_name}")
        print(f"COUNTERPARTY_TABLE: {counterparty_table_name}")
        print(f"MATCHES_TABLE: {matches_table_name}")
        
        # Test S3 access
        s3_status = "OK"
        s3_error = None
        try:
            s3 = boto3.client('s3')
            s3.head_bucket(Bucket=bucket_name)
            print(f"S3 bucket access: OK")
        except Exception as e:
            s3_status = "FAILED"
            s3_error = str(e)
            print(f"S3 bucket access failed: {str(e)}")
        
        # Test DynamoDB access
        dynamodb_status = "OK"
        dynamodb_error = None
        try:
            dynamodb = boto3.resource('dynamodb')
            bank_table = dynamodb.Table(bank_table_name)
            # Try to describe the table
            bank_table.load()
            print(f"DynamoDB access: OK")
        except Exception as e:
            dynamodb_status = "FAILED"
            dynamodb_error = str(e)
            print(f"DynamoDB access failed: {str(e)}")
        
        # Extract request details
        http_method = event.get('httpMethod', '')
        resource = event.get('resource', '')
        
        # Handle the specific request
        if resource == '/documents' and http_method == 'POST':
            body = event.get('body')
            if body:
                try:
                    body = json.loads(body)
                except Exception as e:
                    return response(400, {"message": f"Invalid request body: {str(e)}"})
            
            if not body or 'fileName' not in body or 'source' not in body:
                return response(400, {"message": "Missing required parameters: fileName and source"})
            
            # If S3 access failed, return that error
            if s3_status == "FAILED":
                return response(500, {
                    "message": f"S3 access failed: {s3_error}",
                    "diagnostics": {
                        "s3_status": s3_status,
                        "dynamodb_status": dynamodb_status,
                        "bucket_name": bucket_name
                    }
                })
            
            # Try to generate presigned URL
            try:
                import uuid
                file_name = body['fileName']
                source = body['source']
                key = f"{source}/{str(uuid.uuid4())}-{file_name}"
                
                presigned_url = s3.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': key,
                        'ContentType': 'application/pdf'
                    },
                    ExpiresIn=3600
                )
                
                return response(200, {
                    "uploadUrl": presigned_url,
                    "key": key,
                    "diagnostics": {
                        "s3_status": s3_status,
                        "dynamodb_status": dynamodb_status,
                        "bucket_name": bucket_name,
                        "message": "Diagnostic successful"
                    }
                })
            except Exception as e:
                return response(500, {
                    "message": f"Failed to generate presigned URL: {str(e)}",
                    "diagnostics": {
                        "s3_status": s3_status,
                        "dynamodb_status": dynamodb_status,
                        "bucket_name": bucket_name,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                })
        
        # For other requests, return diagnostic info
        return response(200, {
            "message": "Lambda function is working",
            "diagnostics": {
                "s3_status": s3_status,
                "s3_error": s3_error,
                "dynamodb_status": dynamodb_status,
                "dynamodb_error": dynamodb_error,
                "bucket_name": bucket_name,
                "http_method": http_method,
                "resource": resource
            }
        })
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return response(500, {
            "message": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        })

def response(status_code, body):
    """Helper function to create API Gateway response"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body)
    }
