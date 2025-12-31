from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from .config import settings

# Define the Security Scheme
# This tells FastAPI to look for a header named "X-API-Key"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency that validates the incoming request has the correct API Key.
    If the key is missing or wrong, it rejects the request immediately.
    """
    if api_key != settings.PROXY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="⛔ Invalid or Missing API Key"
        )
    return api_key