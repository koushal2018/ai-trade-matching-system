"""
AWS Cognito JWT token verification for FastAPI.

This module verifies JWT tokens issued by AWS Cognito User Pool.
Frontend uses AWS Amplify with Cognito authentication.

Cognito Configuration:
- User Pool ID: us-east-1_uQ2lN39dT
- Region: us-east-1
- Client ID: 78daptta2m4lb6k5jm3n2hd8oc
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Cognito configuration (should match frontend .env)
COGNITO_REGION = "us-east-1"
COGNITO_USER_POOL_ID = "us-east-1_uQ2lN39dT"
COGNITO_APP_CLIENT_ID = "78daptta2m4lb6k5jm3n2hd8oc"

# Cognito JWKS URL for token verification
COGNITO_JWKS_URL = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)

# Use HTTPBearer for Authorization header (not OAuth2PasswordBearer)
security = HTTPBearer(auto_error=False)

# Initialize JWKS client for Cognito public keys
jwks_client = PyJWKClient(COGNITO_JWKS_URL)


class TokenData(BaseModel):
    """Decoded Cognito token data."""
    username: str
    email: Optional[str] = None
    sub: str  # Cognito user UUID
    groups: list[str] = []  # Cognito user groups (for role-based access)


class User(BaseModel):
    """Authenticated user model."""
    username: str
    email: Optional[str] = None
    sub: str
    role: str = "Operator"  # Default role, can be derived from Cognito groups


def verify_cognito_token(token: str) -> TokenData:
    """
    Verify AWS Cognito JWT token.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        TokenData with decoded claims
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Get signing key from Cognito JWKS
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            options={"verify_exp": True}
        )
        
        # Extract user information from token claims
        username = payload.get("cognito:username") or payload.get("username")
        email = payload.get("email")
        sub = payload.get("sub")
        groups = payload.get("cognito:groups", [])
        
        if not username or not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims"
            )
        
        return TokenData(
            username=username,
            email=email,
            sub=sub,
            groups=groups
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


def get_user_role(groups: list[str]) -> str:
    """
    Determine user role from Cognito groups.
    
    Args:
        groups: List of Cognito user groups
        
    Returns:
        Role string (Admin, Operator, or Auditor)
    """
    # Map Cognito groups to application roles
    if "Admins" in groups:
        return "Admin"
    elif "Auditors" in groups:
        return "Auditor"
    else:
        return "Operator"


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current authenticated user (optional).
    
    Returns None if no token provided (allows unauthenticated access).
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        User object or None
    """
    if credentials is None:
        return None  # Allow unauthenticated access
    
    token_data = verify_cognito_token(credentials.credentials)
    role = get_user_role(token_data.groups)
    
    return User(
        username=token_data.username,
        email=token_data.email,
        sub=token_data.sub,
        role=role
    )


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Require authentication (raises 401 if not authenticated).
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        User object
        
    Raises:
        HTTPException: If not authenticated
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token_data = verify_cognito_token(credentials.credentials)
    role = get_user_role(token_data.groups)
    
    return User(
        username=token_data.username,
        email=token_data.email,
        sub=token_data.sub,
        role=role
    )
