# AgentCore Identity Setup

This directory contains configuration for AgentCore Identity using Amazon Cognito.

## User Pool

**Name**: trade-matching-system-agentcore-identity-production
**ID**: us-east-1_uQ2lN39dT
**Domain**: trade-matching-system-agentcore-production.auth.us-east-1.amazoncognito.com

## User Groups and Roles

### 1. Admin
- **Full system access**
- Can manage all resources
- MFA required
- IAM Role: arn:aws:iam::401552979575:role/trade-matching-system-cognito-admin-production

### 2. Operator
- **View and HITL decision access**
- Can view trades and make matching decisions
- Can access Web Portal
- IAM Role: arn:aws:iam::401552979575:role/trade-matching-system-cognito-operator-production

### 3. Auditor
- **Read-only access**
- Can view audit trails
- Cannot modify data
- IAM Role: arn:aws:iam::401552979575:role/trade-matching-system-cognito-auditor-production

## OAuth2 Configuration

### Web Portal Client
- **Client ID**: 2cjk0av9te5if6rbccf2vj6aa8
- **Flows**: Authorization Code, Implicit
- **Scopes**: email, openid, profile
- **Token Validity**: 1 hour (access/id), 30 days (refresh)

### API Client (Machine-to-Machine)
- **Client ID**: 78daptta2m4lb6k5jm3n2hd8oc
- **Flow**: Client Credentials
- **Scopes**: read, write, admin
- **Token Validity**: 1 hour

## Creating Users

### Using AWS CLI

```bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_uQ2lN39dT \
  --username john.doe@example.com \
  --user-attributes Name=email,Value=john.doe@example.com Name=name,Value="John Doe" \
  --temporary-password "TempPass123!" \
  --region us-east-1

# Add user to group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id us-east-1_uQ2lN39dT \
  --username john.doe@example.com \
  --group-name Operator \
  --region us-east-1
```

### Using Console

1. Go to Cognito User Pools
2. Select: trade-matching-system-agentcore-identity-production
3. Click "Create user"
4. Fill in email and temporary password
5. Add user to appropriate group

## MFA Setup

MFA is optional but recommended for all users, required for Admin users.

### Enable MFA for User

```bash
aws cognito-idp admin-set-user-mfa-preference \
  --user-pool-id us-east-1_uQ2lN39dT \
  --username john.doe@example.com \
  --software-token-mfa-settings Enabled=true,PreferredMfa=true \
  --region us-east-1
```

## Authentication Flow

### Web Portal (Authorization Code Flow)

1. User navigates to Web Portal
2. Redirected to Cognito Hosted UI
3. User enters credentials (+ MFA if enabled)
4. Cognito redirects back with authorization code
5. Web Portal exchanges code for tokens
6. Access token used for API calls

### API Client (Client Credentials Flow)

```bash
# Get access token
curl -X POST \
  https://trade-matching-system-agentcore-production.auth.us-east-1.amazoncognito.com/oauth2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials&client_id=78daptta2m4lb6k5jm3n2hd8oc&client_secret=<CLIENT_SECRET>&scope=trade-matching-system-api/read'
```

## JWT Token Validation

### Python Example

```python
import jwt
from jwt import PyJWKClient

# Get JWKS URL
jwks_url = f"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_uQ2lN39dT/.well-known/jwks.json"

# Create JWKS client
jwks_client = PyJWKClient(jwks_url)

# Get signing key
signing_key = jwks_client.get_signing_key_from_jwt(token)

# Decode and validate token
decoded_token = jwt.decode(
    token,
    signing_key.key,
    algorithms=["RS256"],
    audience=aws_cognito_user_pool_client.web_portal.id,
    issuer=f"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_uQ2lN39dT"
)

# Check user role
user_groups = decoded_token.get('cognito:groups', [])
if 'Admin' in user_groups:
    # Admin access
    pass
elif 'Operator' in user_groups:
    # Operator access
    pass
```

## RBAC Enforcement

### API Gateway Integration

```python
def check_permission(token, required_role):
    """Check if user has required role."""
    decoded = validate_jwt_token(token)
    user_groups = decoded.get('cognito:groups', [])
    
    role_hierarchy = {
        'Admin': 3,
        'Operator': 2,
        'Auditor': 1
    }
    
    user_level = max([role_hierarchy.get(g, 0) for g in user_groups])
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level
```

## Monitoring

### User Activity

```bash
# List users
aws cognito-idp list-users \
  --user-pool-id us-east-1_uQ2lN39dT \
  --region us-east-1

# Get user details
aws cognito-idp admin-get-user \
  --user-pool-id us-east-1_uQ2lN39dT \
  --username john.doe@example.com \
  --region us-east-1
```

### CloudWatch Metrics

Monitor Cognito metrics in CloudWatch:
- SignInSuccesses
- SignInThrottles
- TokenRefreshSuccesses
- UserAuthentication

## Security Best Practices

1. **Enable MFA** for all Admin users
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Rotate client secrets** regularly
4. **Monitor failed login attempts**
5. **Review user permissions** quarterly
6. **Enable advanced security features** (risk-based authentication)
7. **Use short-lived tokens** (1 hour for access tokens)
8. **Implement token refresh** properly in applications

## Troubleshooting

### User Cannot Sign In

1. Check user status: `aws cognito-idp admin-get-user ...`
2. Verify user is in correct group
3. Check MFA configuration
4. Review CloudWatch logs for errors

### Token Validation Fails

1. Verify token hasn't expired
2. Check audience (client ID) matches
3. Verify issuer URL is correct
4. Ensure JWKS URL is accessible

## Cleanup

To delete user pool (WARNING: This will delete all users):
```bash
aws cognito-idp delete-user-pool \
  --user-pool-id us-east-1_uQ2lN39dT \
  --region us-east-1
```
