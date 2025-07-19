# CloudFormation Deployment Validation Checklist

This checklist confirms that all critical issues that could cause deployment failures have been addressed.

## Critical Issues Verification

✅ **S3 URL Format**: All template URLs in master-template.yaml now use the correct format with AWS region:
```yaml
TemplateURL: !Sub https://${S3BucketForTemplates}.s3.${AWS::Region}.amazonaws.com/${S3PrefixForTemplates}core-infrastructure.yaml
```

✅ **Circular Dependencies**: Resolved by:
- Creating separate IAM role for ReconciliationEngineFunction
- Removing direct circular references between resources
- Using proper DependsOn attributes

✅ **S3 Bucket Naming**: Shortened bucket names to prevent exceeding the 63-character limit:
```yaml
BucketName: !Sub trec-docs-${Environment}-${AWS::AccountId}
```

✅ **Parameter References**: All parameter references are valid and parameters are properly defined in each template

✅ **Resource Naming**: Function names now include stack name to prevent conflicts:
```yaml
FunctionName: !Sub ${AWS::StackName}-document-processor-${Environment}
```

✅ **Lambda Runtime**: Updated all Lambda functions to use nodejs18.x instead of nodejs16.x

✅ **Template Validation**: The deploy.sh script now validates all templates before deployment:
```bash
for template in master-template.yaml core-infrastructure.yaml api-lambda.yaml frontend-amplify.yaml; do
  echo "Validating $template..."
  aws cloudformation validate-template \
    --template-url https://$S3_BUCKET.s3.$REGION.amazonaws.com/$S3_PREFIX/$template \
    --region $REGION
  
  if [ $? -ne 0 ]; then
    echo "Error validating $template. Exiting."
    exit 1
  fi
done
```

## Pre-Deployment Checklist

Before deploying, ensure:

1. The S3 bucket specified in deploy.sh exists and is accessible
2. You have proper IAM permissions to create all resources
3. The AWS region specified in deploy.sh is correct
4. All template files are uploaded to the S3 bucket before validation
5. The CreateCustomCFNS3NotificationFunction parameter is set to 'false' to avoid circular dependencies

## Post-Deployment Manual Steps

After successful deployment:

1. Configure S3 event notifications manually if needed
2. Verify all resources were created correctly
3. Test the API endpoints
4. Check CloudWatch Logs for any errors