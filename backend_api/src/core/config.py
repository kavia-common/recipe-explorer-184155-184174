from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    secret_key: str = Field(default="dev-secret-key-change", description="HMAC signing key for tokens")
    token_exp_minutes: int = Field(default=60 * 12, description="Access token expiration, minutes")
    cors_allow_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS allow origins")

    site_url: str | None = Field(default=None, description="Public site URL for email redirects (not used here)")

    class Config:
        frozen = True


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings from environment variables."""
    return Settings(
        secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change"),
        token_exp_minutes=int(os.getenv("TOKEN_EXP_MINUTES", "720")),
        cors_allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
        site_url=os.getenv("SITE_URL"),
    )
