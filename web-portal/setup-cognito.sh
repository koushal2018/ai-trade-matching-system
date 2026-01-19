#!/bin/bash
# Cognito Setup Script for Trade Matching Portal
# Creates a secure Cognito User Pool for authentication

set -e

AWS_REGION="us-east-1"
ACCOUNT_ID="979873657001"
PROJECT_NAME="trade-matching-portal"
USER_POOL_NAME="${PROJECT_NAME}-users"

echo "========================================="
echo "Setting up Cognito Authentication"
echo "========================================="

# Check if user pool already exists
EXISTING_POOL=$(aws cognito-idp list-user-pools \
    --max-results 50 \
    --region "${AWS_REGION}" \
    --query "UserPools[?Name=='${USER_POOL_NAME}'].Id" \
    --output text 2>/dev/null)

if [ -z "$EXISTING_POOL" ] || [ "$EXISTING_POOL" == "None" ]; then
    echo "Creating Cognito User Pool: ${USER_POOL_NAME}"

    USER_POOL_RESULT=$(aws cognito-idp create-user-pool \
        --pool-name "${USER_POOL_NAME}" \
        --region "${AWS_REGION}" \
        --auto-verified-attributes email \
        --username-attributes email \
        --mfa-configuration OPTIONAL \
        --policies '{
            "PasswordPolicy": {
                "MinimumLength": 12,
                "RequireUppercase": true,
                "RequireLowercase": true,
                "RequireNumbers": true,
                "RequireSymbols": true,
                "TemporaryPasswordValidityDays": 7
            }
        }' \
        --account-recovery-setting '{
            "RecoveryMechanisms": [
                {"Priority": 1, "Name": "verified_email"}
            ]
        }' \
        --user-pool-tags "Project=TradeMatchingPortal,Environment=Production" \
        --admin-create-user-config '{
            "AllowAdminCreateUserOnly": false,
            "InviteMessageTemplate": {
                "EmailSubject": "Welcome to Trade Matching Portal",
                "EmailMessage": "Your username is {username} and temporary password is {####}."
            }
        }' 2>/dev/null)

    USER_POOL_ID=$(echo "$USER_POOL_RESULT" | grep -o '"Id": "[^"]*"' | head -1 | cut -d'"' -f4)
    echo "Created User Pool: ${USER_POOL_ID}"
else
    USER_POOL_ID="$EXISTING_POOL"
    echo "Using existing User Pool: ${USER_POOL_ID}"
fi

# Check for existing app client
CLIENT_NAME="${PROJECT_NAME}-web-client"
EXISTING_CLIENT=$(aws cognito-idp list-user-pool-clients \
    --user-pool-id "${USER_POOL_ID}" \
    --region "${AWS_REGION}" \
    --query "UserPoolClients[?ClientName=='${CLIENT_NAME}'].ClientId" \
    --output text 2>/dev/null)

if [ -z "$EXISTING_CLIENT" ] || [ "$EXISTING_CLIENT" == "None" ]; then
    echo "Creating App Client: ${CLIENT_NAME}"

    CLIENT_RESULT=$(aws cognito-idp create-user-pool-client \
        --user-pool-id "${USER_POOL_ID}" \
        --client-name "${CLIENT_NAME}" \
        --region "${AWS_REGION}" \
        --generate-secret false \
        --explicit-auth-flows "ALLOW_USER_SRP_AUTH" "ALLOW_REFRESH_TOKEN_AUTH" \
        --supported-identity-providers "COGNITO" \
        --prevent-user-existence-errors "ENABLED" \
        --access-token-validity 60 \
        --id-token-validity 60 \
        --refresh-token-validity 30 \
        --token-validity-units '{
            "AccessToken": "minutes",
            "IdToken": "minutes",
            "RefreshToken": "days"
        }' 2>/dev/null)

    CLIENT_ID=$(echo "$CLIENT_RESULT" | grep -o '"ClientId": "[^"]*"' | head -1 | cut -d'"' -f4)
    echo "Created App Client: ${CLIENT_ID}"
else
    CLIENT_ID="$EXISTING_CLIENT"
    echo "Using existing App Client: ${CLIENT_ID}"
fi

# Create a test user (optional)
echo ""
echo "Creating test user..."
TEST_EMAIL="admin@tradematching.local"
aws cognito-idp admin-create-user \
    --user-pool-id "${USER_POOL_ID}" \
    --username "${TEST_EMAIL}" \
    --temporary-password "TempPass123!" \
    --user-attributes Name=email,Value="${TEST_EMAIL}" Name=email_verified,Value=true \
    --region "${AWS_REGION}" 2>/dev/null || echo "User may already exist"

echo ""
echo "========================================="
echo "Cognito Setup Complete!"
echo "========================================="
echo ""
echo "User Pool ID: ${USER_POOL_ID}"
echo "Client ID: ${CLIENT_ID}"
echo ""
echo "Add these to your .env.production file:"
echo ""
echo "VITE_COGNITO_USER_POOL_ID=${USER_POOL_ID}"
echo "VITE_COGNITO_CLIENT_ID=${CLIENT_ID}"
echo ""
echo "Test User: ${TEST_EMAIL}"
echo "Temporary Password: TempPass123!"
echo "(User will need to change password on first login)"

# Save to env file
cat > .env.production << EOF
# Production Environment Configuration
# Generated on $(date)

VITE_API_URL=https://api.tradematching.example.com
VITE_AWS_REGION=${AWS_REGION}
VITE_COGNITO_USER_POOL_ID=${USER_POOL_ID}
VITE_COGNITO_CLIENT_ID=${CLIENT_ID}
VITE_DISABLE_MSW=true
EOF

echo ""
echo "Saved configuration to .env.production"
