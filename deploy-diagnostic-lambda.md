# How to Deploy and Use the Diagnostic Lambda Function

## What is lambda_function_diagnostic.py?
It's a special Lambda function designed to diagnose exactly why your API is returning 502 errors. It tests both S3 and DynamoDB connectivity and returns detailed diagnostic information.

## How to Deploy It

### Option 1: AWS Console (Recommended)
1. **Go to AWS Lambda Console**
2. **Find your existing Lambda function** (the one that handles `/documents` POST requests)
3. **Backup your current code** (copy it to a text file)
4. **Replace the function code** with the contents of `lambda_function_diagnostic.py`
5. **Deploy the function**
6. **Test it using your frontend or API client**

### Option 2: AWS CLI
```bash
# Create a zip file with the diagnostic function
zip diagnostic-function.zip lambda_function_diagnostic.py

# Update your existing Lambda function
aws lambda update-function-code \
    --function-name trade-api-handler \
    --zip-file fileb://diagnostic-function.zip
```

## How to Test It

### Method 1: Use Your Frontend
1. Open your React app
2. Try to upload a document
3. Check the browser console for detailed diagnostic information
4. The response will include diagnostic details about what's failing

### Method 2: Direct API Test
```bash
curl -X POST "YOUR_API_GATEWAY_URL/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "test.pdf",
    "source": "BANK",
    "tradeDateRange": "test"
  }'
```

## What the Diagnostic Function Will Tell You

The response will include:
- **S3 connectivity status** (OK/FAILED with error details)
- **DynamoDB connectivity status** (OK/FAILED with error details)  
- **Environment variables** currently set
- **Specific error messages** if something is failing
- **Stack traces** for debugging

## Example Diagnostic Response
```json
{
  "message": "Diagnostic successful",
  "diagnostics": {
    "s3_status": "OK",
    "dynamodb_status": "FAILED", 
    "dynamodb_error": "User: arn:aws:sts::123:assumed-role/lambda-role is not authorized to perform: dynamodb:DescribeTable on resource: arn:aws:dynamodb:us-east-1:123:table/BankTradeData",
    "bucket_name": "fab-otc-reconciliation-deployment"
  }
}
```

## After Getting Diagnostic Results

Based on the diagnostic output:
- **If S3 fails**: Check S3 bucket permissions
- **If DynamoDB fails**: Check IAM role has DynamoDB permissions
- **If both work but still 502**: Check environment variables
- **If environment variables missing**: Set them in Lambda configuration

## Restore Your Original Function
After fixing the issue:
1. Replace the diagnostic code with your original Lambda function code
2. Test that everything works
3. Delete the diagnostic files

## Quick Start
1. **Copy the contents of `lambda_function_diagnostic.py`**
2. **Paste it into your Lambda function in AWS Console**
3. **Deploy**
4. **Test your API endpoint**
5. **Check the response for diagnostic information**

This will immediately tell you exactly what's broken and why your API started returning 502 errors.
