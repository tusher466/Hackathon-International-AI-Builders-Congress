"""FastAPI dependencies."""
from __future__ import annotations

from fastapi import Header, HTTPException
from typing import Optional

from config.settings import get_settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    settings = get_settings()
    if settings.API_KEY:
        if x_api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API Key")


def get_settings_dep():
    return get_settings()
