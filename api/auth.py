"""
Authentication module for webhook API key validation.
"""

from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """Verify incoming webhook API key."""
    import os
    valid_key = os.getenv("WEBHOOK_API_KEY", "")
    
    if not api_key or api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key
