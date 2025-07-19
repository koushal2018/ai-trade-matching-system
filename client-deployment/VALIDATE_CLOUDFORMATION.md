# CloudFormation Template Validation Guide

This guide provides instructions for validating the CloudFormation templates before deployment to ensure they are correctly formatted and will deploy successfully.

## Prerequisites

- AWS CLI installed and configured
- Appropriate AWS permissions to validate CloudFormation templates

## Validation Steps

### 1. Validate Core Infrastructure Template

```bash
aws cloudformation validate-template \
  --template-body file://client-deployment/infrastructure/cloudformation/fixed-core-infrastructure.yaml
```

### 2. Validate API Lambda Template

```bash
aws cloudformation validate-template \
  --template-body file://client-deployment/infrastructure/cloudformation/minimal-api-lambda-v2.yaml
```

### 3. Validate Frontend Hosting Template

```bash
aws cloudformation validate-template \
  --template-body file://client-deployment/infrastructure/cloudformation/s3-frontend-hosting.yaml
```

## Using the Validation Script

For convenience, you can use the provided validation script:

```bash
./client-deployment/validate_and_upload.sh \
  --template client-deployment/infrastructure/cloudformation/fixed-core-infrastructure.yaml \
  --bucket your-company-name-trade-reconciliation-deployment \
  --key cloudformation-templates/fixed-core-infrastructure.yaml \
  --region us-west-2
```

Repeat for each template.

## Common Validation Errors

### Invalid YAML Syntax

If you see an error like:
```
Error parsing parameter 'template-body': Invalid YAML: ...
```

Check for:
- Indentation issues
- Missing colons after property names
- Unbalanced quotes or brackets

### Invalid Resource Properties

If you see an error like:
```
Template format error: Unrecognized resource type: ...
```

Check for:
- Typos in resource types
- Incorrect property names
- Missing required properties

### Circular Dependencies

If you see an error like:
```
Circular dependency between resources: ...
```

Check for:
- Resources that reference each other in a circular manner
- Use DependsOn to establish clear dependency chains

## Best Practices

1. **Always validate templates before deployment**: This saves time by catching errors early.
2. **Use parameter files**: For complex templates, create parameter files to simplify deployment.
3. **Use stack policies**: Protect critical resources from accidental updates or deletions.
4. **Use change sets**: Preview changes before applying them to production stacks.
5. **Document parameters**: Include descriptions for all parameters to make templates self-documenting.

## Next Steps

After validating the templates, proceed to the deployment steps outlined in the main deployment instructions document.