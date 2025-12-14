# Cognito User Pool for AgentCore Identity
resource "aws_cognito_user_pool" "agentcore_identity" {
  name = "${var.project_name}-agentcore-identity-${var.environment}"

  # Password policy
  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  # MFA configuration
  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # User attributes
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 5
      max_length = 256
    }
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    name                = "role"
    attribute_data_type = "String"
    required            = false
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 50
    }
  }

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # Auto-verified attributes
  auto_verified_attributes = ["email"]

  # Username configuration
  username_configuration {
    case_sensitive = false
  }

  # User pool add-ons
  user_pool_add_ons {
    advanced_security_mode = "ENFORCED"
  }

  # Deletion protection
  deletion_protection = "ACTIVE"

  tags = merge(var.tags, {
    Name        = "AgentCore Identity User Pool"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "agentcore_identity" {
  domain       = "${var.project_name}-agentcore-${var.environment}"
  user_pool_id = aws_cognito_user_pool.agentcore_identity.id
}

# Cognito User Pool Client for Web Portal
resource "aws_cognito_user_pool_client" "web_portal" {
  name         = "${var.project_name}-web-portal-${var.environment}"
  user_pool_id = aws_cognito_user_pool.agentcore_identity.id

  # OAuth configuration
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code", "implicit"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  callback_urls                        = var.web_portal_callback_urls
  logout_urls                          = var.web_portal_logout_urls

  # Supported identity providers
  supported_identity_providers = ["COGNITO"]

  # Token validity
  access_token_validity  = 1  # 1 hour
  id_token_validity      = 1  # 1 hour
  refresh_token_validity = 30 # 30 days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # Read and write attributes
  read_attributes  = ["email", "name", "custom:role"]
  write_attributes = ["email", "name"]

  # Enable token revocation
  enable_token_revocation = true
}

# Cognito User Pool Client for API (Machine-to-Machine)
resource "aws_cognito_user_pool_client" "api_client" {
  name         = "${var.project_name}-api-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.agentcore_identity.id

  # OAuth configuration for client credentials flow
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials"]
  allowed_oauth_scopes                 = aws_cognito_resource_server.agentcore_api.scope_identifiers

  # Generate secret
  generate_secret = true

  # Token validity
  access_token_validity = 1 # 1 hour

  token_validity_units {
    access_token = "hours"
  }

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # Enable token revocation
  enable_token_revocation = true
}

# Cognito Resource Server for API
resource "aws_cognito_resource_server" "agentcore_api" {
  identifier   = "${var.project_name}-api"
  name         = "${var.project_name}-api-${var.environment}"
  user_pool_id = aws_cognito_user_pool.agentcore_identity.id

  scope {
    scope_name        = "read"
    scope_description = "Read access to API"
  }

  scope {
    scope_name        = "write"
    scope_description = "Write access to API"
  }

  scope {
    scope_name        = "admin"
    scope_description = "Admin access to API"
  }
}

# Cognito User Groups

# Admin Group
resource "aws_cognito_user_group" "admin" {
  name         = "Admin"
  user_pool_id = aws_cognito_user_pool.agentcore_identity.id
  description  = "Administrators with full system access"
  precedence   = 1
  role_arn     = aws_iam_role.cognito_admin_role.arn
}

# Operator Group
resource "aws_cognito_user_group" "operator" {
  name         = "Operator"
  user_pool_id = aws_cognito_user_pool.agentcore_identity.id
  description  = "Operators with view and HITL decision access"
  precedence   = 2
  role_arn     = aws_iam_role.cognito_operator_role.arn
}

# Auditor Group
resource "aws_cognito_user_group" "auditor" {
  name         = "Auditor"
  user_pool_id = aws_cognito_user_pool.agentcore_identity.id
  description  = "Auditors with read-only access to audit trails"
  precedence   = 3
  role_arn     = aws_iam_role.cognito_auditor_role.arn
}

# IAM Roles for Cognito Groups

# Admin Role
resource "aws_iam_role" "cognito_admin_role" {
  name = "${var.project_name}-cognito-admin-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_user_pool.agentcore_identity.id
          }
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Cognito Admin Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Admin Policy
resource "aws_iam_policy" "cognito_admin_policy" {
  name        = "${var.project_name}-cognito-admin-policy-${var.environment}"
  description = "Policy for Admin users"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:*",
          "s3:*",
          "sqs:*",
          "bedrock:*"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Cognito Admin Policy"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_iam_role_policy_attachment" "cognito_admin_policy_attachment" {
  role       = aws_iam_role.cognito_admin_role.name
  policy_arn = aws_iam_policy.cognito_admin_policy.arn
}

# Operator Role
resource "aws_iam_role" "cognito_operator_role" {
  name = "${var.project_name}-cognito-operator-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_user_pool.agentcore_identity.id
          }
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Cognito Operator Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Operator Policy
resource "aws_iam_policy" "cognito_operator_policy" {
  name        = "${var.project_name}-cognito-operator-policy-${var.environment}"
  description = "Policy for Operator users"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "s3:GetObject",
          "s3:ListBucket",
          "sqs:SendMessage",
          "sqs:ReceiveMessage"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Cognito Operator Policy"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_iam_role_policy_attachment" "cognito_operator_policy_attachment" {
  role       = aws_iam_role.cognito_operator_role.name
  policy_arn = aws_iam_policy.cognito_operator_policy.arn
}

# Auditor Role
resource "aws_iam_role" "cognito_auditor_role" {
  name = "${var.project_name}-cognito-auditor-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_user_pool.agentcore_identity.id
          }
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Cognito Auditor Role"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

# Auditor Policy (Read-only)
resource "aws_iam_policy" "cognito_auditor_policy" {
  name        = "${var.project_name}-cognito-auditor-policy-${var.environment}"
  description = "Policy for Auditor users (read-only)"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Cognito Auditor Policy"
    Component   = "AgentCore"
    Environment = var.environment
  })
}

resource "aws_iam_role_policy_attachment" "cognito_auditor_policy_attachment" {
  role       = aws_iam_role.cognito_auditor_role.name
  policy_arn = aws_iam_policy.cognito_auditor_policy.arn
}

# Create README for AgentCore Identity
resource "local_file" "agentcore_identity_readme" {
  filename = "${path.module}/configs/AGENTCORE_IDENTITY_README.md"
  content  = <<-EOT
# AgentCore Identity Setup

This directory contains configuration for AgentCore Identity using Amazon Cognito.

## User Pool

**Name**: ${aws_cognito_user_pool.agentcore_identity.name}
**ID**: ${aws_cognito_user_pool.agentcore_identity.id}
**Domain**: ${aws_cognito_user_pool_domain.agentcore_identity.domain}.auth.${var.aws_region}.amazoncognito.com

## User Groups and Roles

### 1. Admin
- **Full system access**
- Can manage all resources
- MFA required
- IAM Role: ${aws_iam_role.cognito_admin_role.arn}

### 2. Operator
- **View and HITL decision access**
- Can view trades and make matching decisions
- Can access Web Portal
- IAM Role: ${aws_iam_role.cognito_operator_role.arn}

### 3. Auditor
- **Read-only access**
- Can view audit trails
- Cannot modify data
- IAM Role: ${aws_iam_role.cognito_auditor_role.arn}

## OAuth2 Configuration

### Web Portal Client
- **Client ID**: ${aws_cognito_user_pool_client.web_portal.id}
- **Flows**: Authorization Code, Implicit
- **Scopes**: email, openid, profile
- **Token Validity**: 1 hour (access/id), 30 days (refresh)

### API Client (Machine-to-Machine)
- **Client ID**: ${aws_cognito_user_pool_client.api_client.id}
- **Flow**: Client Credentials
- **Scopes**: read, write, admin
- **Token Validity**: 1 hour

## Creating Users

### Using AWS CLI

```bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id ${aws_cognito_user_pool.agentcore_identity.id} \
  --username john.doe@example.com \
  --user-attributes Name=email,Value=john.doe@example.com Name=name,Value="John Doe" \
  --temporary-password "TempPass123!" \
  --region ${var.aws_region}

# Add user to group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id ${aws_cognito_user_pool.agentcore_identity.id} \
  --username john.doe@example.com \
  --group-name Operator \
  --region ${var.aws_region}
```

### Using Console

1. Go to Cognito User Pools
2. Select: ${aws_cognito_user_pool.agentcore_identity.name}
3. Click "Create user"
4. Fill in email and temporary password
5. Add user to appropriate group

## MFA Setup

MFA is optional but recommended for all users, required for Admin users.

### Enable MFA for User

```bash
aws cognito-idp admin-set-user-mfa-preference \
  --user-pool-id ${aws_cognito_user_pool.agentcore_identity.id} \
  --username john.doe@example.com \
  --software-token-mfa-settings Enabled=true,PreferredMfa=true \
  --region ${var.aws_region}
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
  https://${aws_cognito_user_pool_domain.agentcore_identity.domain}.auth.${var.aws_region}.amazoncognito.com/oauth2/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials&client_id=${aws_cognito_user_pool_client.api_client.id}&client_secret=<CLIENT_SECRET>&scope=${var.project_name}-api/read'
```

## JWT Token Validation

### Python Example

```python
import jwt
from jwt import PyJWKClient

# Get JWKS URL
jwks_url = f"https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.agentcore_identity.id}/.well-known/jwks.json"

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
    issuer=f"https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.agentcore_identity.id}"
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
  --user-pool-id ${aws_cognito_user_pool.agentcore_identity.id} \
  --region ${var.aws_region}

# Get user details
aws cognito-idp admin-get-user \
  --user-pool-id ${aws_cognito_user_pool.agentcore_identity.id} \
  --username john.doe@example.com \
  --region ${var.aws_region}
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
  --user-pool-id ${aws_cognito_user_pool.agentcore_identity.id} \
  --region ${var.aws_region}
```
EOT
}

# Outputs
output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.agentcore_identity.id
}

output "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.agentcore_identity.arn
}

output "cognito_user_pool_domain" {
  description = "Domain of the Cognito User Pool"
  value       = "${aws_cognito_user_pool_domain.agentcore_identity.domain}.auth.${var.aws_region}.amazoncognito.com"
}

output "cognito_web_portal_client_id" {
  description = "Client ID for Web Portal"
  value       = aws_cognito_user_pool_client.web_portal.id
}

output "cognito_api_client_id" {
  description = "Client ID for API (Machine-to-Machine)"
  value       = aws_cognito_user_pool_client.api_client.id
}

output "cognito_api_client_secret" {
  description = "Client Secret for API (Machine-to-Machine)"
  value       = aws_cognito_user_pool_client.api_client.client_secret
  sensitive   = true
}

output "cognito_user_groups" {
  description = "List of Cognito user groups"
  value = {
    admin    = aws_cognito_user_group.admin.name
    operator = aws_cognito_user_group.operator.name
    auditor  = aws_cognito_user_group.auditor.name
  }
}
