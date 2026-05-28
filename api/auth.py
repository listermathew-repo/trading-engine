import os
from fastapi import HTTPException, Header
from typing import Optional


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """FastAPI dependency to validate webhook API key."""
    expected_key = os.getenv("WEBHOOK_API_KEY")

    if not expected_key:
        raise HTTPException(status_code=500, detail="Webhook API key not configured")

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key
