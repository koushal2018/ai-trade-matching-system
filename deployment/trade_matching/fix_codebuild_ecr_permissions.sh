#!/bin/bash
# Fix CodeBuild ECR permissions for trade_matching_ai agent
# The CodeBuild role only has ECR permissions for http_agent_orchestrator, not trade_matching_ai

set -e

ROLE_NAME="AmazonBedrockAgentCoreSDKCodeBuild-us-east-1-0f9cb91bfb"
POLICY_NAME="CodeBuildExecutionPolicy"
REGION="us-east-1"

echo "============================================="
echo "Fixing CodeBuild ECR Permissions"
echo "============================================="
echo ""
echo "Role: ${ROLE_NAME}"
echo "Policy: ${POLICY_NAME}"
echo ""

# Create the updated policy document
POLICY_DOCUMENT=$(cat <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": [
        "arn:aws:ecr:us-east-1:401552979575:repository/bedrock-agentcore-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:401552979575:log-group:/aws/codebuild/bedrock-agentcore-*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::bedrock-agentcore-codebuild-sources-401552979575-us-east-1",
        "arn:aws:s3:::bedrock-agentcore-codebuild-sources-401552979575-us-east-1/*"
      ],
      "Condition": {
        "StringEquals": {
          "s3:ResourceAccount": "401552979575"
        }
      }
    }
  ]
}
EOF
)

echo "Step 1: Updating IAM policy to allow ECR push to all bedrock-agentcore-* repos..."
aws iam put-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-name "${POLICY_NAME}" \
  --policy-document "${POLICY_DOCUMENT}" \
  --region "${REGION}"

if [ $? -eq 0 ]; then
    echo "✅ Policy updated successfully"
else
    echo "❌ Policy update failed"
    exit 1
fi

echo ""
echo "Step 2: Verifying updated policy..."
aws iam get-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-name "${POLICY_NAME}" \
  --region "${REGION}" \
  --query 'PolicyDocument.Statement[1].Resource'

echo ""
echo "============================================="
echo "✅ CodeBuild ECR permissions fixed!"
echo "============================================="
echo ""
echo "The CodeBuild role can now push to all bedrock-agentcore-* ECR repositories."
echo ""
echo "Next step: Re-run the deployment"
echo "  cd deployment/trade_matching"
echo "  agentcore launch"
echo ""
