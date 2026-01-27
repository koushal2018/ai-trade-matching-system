"""
AWS Cognito JWT token verification for FastAPI.

This module verifies JWT tokens issued by AWS Cognito User Pool.
Frontend uses AWS Amplify with Cognito authentication.

Cognito Configuration:
- User Pool ID: Set via COGNITO_USER_POOL_ID environment variable
- Region: Set via COGNITO_REGION environment variable  
- Client ID: Set via COGNITO_APP_CLIENT_ID environment variable
"""

import os
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Cognito configuration from environment variables
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "YOUR_COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "YOUR_COGNITO_CLIENT_ID")

# Cognito JWKS URL for token verification
COGNITO_JWKS_URL = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)

# Use HTTPBearer for Authorization header (not OAuth2PasswordBearer)
security = HTTPBearer(auto_error=False)

# Lazy-load JWKS client to avoid blocking on module import
_jwks_client = None

def get_jwks_client():
    """Get or create JWKS client for Cognito token verification."""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(COGNITO_JWKS_URL)
    return _jwks_client


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
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        
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


# Development Authentication Bypass
# =================================

def get_dev_user() -> User:
    """
    Return a mock user for development/testing.

    Returns:
        Mock User object with developer credentials
    """
    return User(
        username="dev-user",
        email="dev@example.com",
        sub="dev-00000000-0000-0000-0000-000000000000",
        role="Admin"
    )


async def get_current_user_or_dev(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current authenticated user with development bypass.

    In development (DISABLE_AUTH=true):
    - Returns mock dev user without authentication

    In production (DISABLE_AUTH=false):
    - Returns authenticated user if token provided
    - Raises 401 if no token provided

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        User object (real or mock depending on environment)
    """
    if settings.disable_auth:
        logger.debug("Auth disabled - using dev user")
        return get_dev_user()

    # Production: require authentication
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


async def optional_auth_or_dev(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Optional authentication with development bypass.

    In development (DISABLE_AUTH=true):
    - Returns mock dev user

    In production (DISABLE_AUTH=false):
    - Returns authenticated user if token provided
    - Returns None if no token provided (allows unauthenticated access)

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        User object, mock user, or None
    """
    if settings.disable_auth:
        return get_dev_user()

    # Production: optional authentication
    return await get_current_user(credentials)
