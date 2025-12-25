# AWS Cognito Authentication Fix

## Date
December 24, 2025

## Issue
Backend API failed to start with `ModuleNotFoundError: No module named 'jose'` when trying to import from `python-jose` library.

## Root Cause
The original implementation used `python-jose` library which has compatibility issues with Python 3.13 and can be problematic to install correctly.

## Solution
Completely rewrote authentication to use **PyJWT with AWS Cognito JWKS verification** instead of generic jose library.

## Changes Made

### 1. Import Changes
```python
# ❌ OLD (python-jose)
from jose import JWTError, jwt

# ✅ NEW (PyJWT with Cognito)
import jwt
from jwt import PyJWKClient
```

### 2. Security Scheme Change
```python
# ❌ OLD (OAuth2 password flow)
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# ✅ NEW (HTTP Bearer for JWT tokens)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer(auto_error=False)
```

### 3. Cognito-Specific Configuration
```python
# Cognito configuration
COGNITO_REGION = "us-east-1"
COGNITO_USER_POOL_ID = "us-east-1_uQ2lN39dT"
COGNITO_APP_CLIENT_ID = "78daptta2m4lb6k5jm3n2hd8oc"

# Cognito JWKS URL for public key verification
COGNITO_JWKS_URL = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)

# Initialize JWKS client
jwks_client = PyJWKClient(COGNITO_JWKS_URL)
```

### 4. Token Verification with Cognito JWKS
```python
def verify_cognito_token(token: str) -> TokenData:
    """Verify AWS Cognito JWT token using JWKS."""
    try:
        # Get signing key from Cognito JWKS endpoint
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and verify token with RS256 algorithm
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            options={"verify_exp": True}
        )
        
        # Extract Cognito-specific claims
        username = payload.get("cognito:username") or payload.get("username")
        email = payload.get("email")
        sub = payload.get("sub")
        groups = payload.get("cognito:groups", [])
        
        return TokenData(username=username, email=email, sub=sub, groups=groups)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
```

### 5. Role Mapping from Cognito Groups
```python
def get_user_role(groups: list[str]) -> str:
    """Map Cognito groups to application roles."""
    if "Admins" in groups:
        return "Admin"
    elif "Auditors" in groups:
        return "Auditor"
    else:
        return "Operator"
```

### 6. Updated Dependency Functions
```python
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user (optional - returns None if not authenticated)."""
    if credentials is None:
        return None
    
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
    """Require authentication (raises 401 if not authenticated)."""
    if credentials is None:
        raise HTTPException(
            status_code=401,
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
```

## Dependencies Required

### requirements.txt
```txt
PyJWT>=2.8.0
cryptography>=41.0.0  # Required for RS256 algorithm
```

**Note**: `python-jose` is NO LONGER REQUIRED and should be removed from requirements.txt

## How It Works

1. **Frontend (AWS Amplify)**:
   - User signs in via Cognito
   - Amplify gets JWT token from Cognito
   - Token sent in `Authorization: Bearer <token>` header

2. **Backend (FastAPI)**:
   - Receives token in Authorization header
   - Fetches Cognito's public keys from JWKS endpoint
   - Verifies token signature using RS256 algorithm
   - Validates token audience matches Client ID
   - Checks token expiration
   - Extracts user claims (username, email, sub, groups)
   - Maps Cognito groups to application roles

3. **Token Claims**:
   - `cognito:username` - Username
   - `email` - User email
   - `sub` - Cognito user UUID (unique identifier)
   - `cognito:groups` - User groups for role-based access
   - `exp` - Token expiration timestamp
   - `aud` - Audience (Client ID)

## Benefits of This Approach

1. ✅ **No python-jose dependency** - Avoids installation issues
2. ✅ **Cognito-native** - Designed specifically for AWS Cognito
3. ✅ **Secure** - Uses Cognito's public keys for verification
4. ✅ **Standard PyJWT** - Well-maintained, widely-used library
5. ✅ **Role-based access** - Maps Cognito groups to application roles
6. ✅ **Better error handling** - Specific exceptions for expired/invalid tokens
7. ✅ **Production-ready** - Follows AWS best practices

## Testing

### Test with curl
```bash
# Get token from frontend (check browser DevTools → Network → Authorization header)
TOKEN="eyJraWQ..."

# Test authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/agents/status

# Test unauthenticated endpoint (should work)
curl http://localhost:8000/health
```

### Test with frontend
1. Sign in via Cognito (frontend handles this)
2. Upload files - backend will verify token automatically
3. Check backend logs for token verification messages

## Cognito Configuration

**User Pool**: `us-east-1_uQ2lN39dT`
**Client ID**: `78daptta2m4lb6k5jm3n2hd8oc`
**Region**: `us-east-1`
**JWKS URL**: `https://cognito-idp.us-east-1.amazonaws.com/us-east-1_uQ2lN39dT/.well-known/jwks.json`

## Common Issues and Solutions

### Issue: "No module named 'jwt'"
**Solution**: Install PyJWT
```bash
pip install PyJWT cryptography
```

### Issue: "Token verification failed"
**Possible Causes**:
1. Token expired (Cognito tokens expire after 1 hour by default)
2. Wrong Client ID in configuration
3. Token from different User Pool
4. Network issue fetching JWKS

**Solution**: Check token claims and configuration match

### Issue: "Invalid signature"
**Possible Causes**:
1. JWKS URL incorrect
2. Token tampered with
3. Clock skew between systems

**Solution**: Verify JWKS URL and system time

## Migration Notes

If you need to migrate from `python-jose` to PyJWT in other projects:

1. Replace `from jose import jwt` with `import jwt`
2. Replace `from jose import JWTError` with `jwt.InvalidTokenError`
3. For Cognito: Use `PyJWKClient` to fetch signing keys
4. Change algorithm from HS256 to RS256 for Cognito
5. Update security scheme from OAuth2PasswordBearer to HTTPBearer
6. Extract Cognito-specific claims (`cognito:username`, `cognito:groups`)

## References

- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [AWS Cognito JWT Verification](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Cognito JWKS Endpoint](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html#amazon-cognito-user-pools-using-tokens-step-2)

---

**Status**: ✅ FIXED
**Date**: December 24, 2025
**Impact**: Backend API now starts successfully and verifies Cognito tokens correctly
