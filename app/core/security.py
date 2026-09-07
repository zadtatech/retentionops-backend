from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer
from typing import Optional
from app.config import settings


# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(
    api_key_header_value: Optional[str] = Security(api_key_header),
    authorization: Optional[str] = Security(bearer_scheme)
) -> str:
    """
    Verify API key from either X-API-Key header or Authorization Bearer token.
    
    Args:
        api_key_header_value: API key from X-API-Key header
        authorization: Authorization header value
        
    Returns:
        str: The validated API key
        
    Raises:
        HTTPException: If authentication fails
    """
    # Try X-API-Key header first
    if api_key_header_value and api_key_header_value == settings.API_AUTH_TOKEN:
        return api_key_header_value
    
    # Try Authorization Bearer token
    if authorization and authorization.credentials == settings.API_AUTH_TOKEN:
        return authorization.credentials
    
    # Authentication failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_api_key_optional(
    api_key_header_value: Optional[str] = Security(api_key_header),
    authorization: Optional[str] = Security(bearer_scheme)
) -> Optional[str]:
    """
    Optional API key verification for endpoints that can work without authentication.
    
    Args:
        api_key_header_value: API key from X-API-Key header
        authorization: Authorization header value
        
    Returns:
        Optional[str]: The validated API key or None
    """
    # Try X-API-Key header first
    if api_key_header_value and api_key_header_value == settings.API_AUTH_TOKEN:
        return api_key_header_value
    
    # Try Authorization Bearer token
    if authorization and authorization.credentials == settings.API_AUTH_TOKEN:
        return authorization.credentials
    
    return None
