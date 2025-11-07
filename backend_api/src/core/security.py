from __future__ import annotations

import base64
import hashlib
import hmac
import os
import threading
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Request
from fastapi.security import OAuth2PasswordBearer

from src.core.config import get_settings
from src.core.errors import AppError
from src.storage.memory_repo import memory_user_repo


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


# PUBLIC_INTERFACE
def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Non-production salted SHA-256 password hashing.

    Returns:
        (salt, hash) hex pair.
    """
    salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
    pwd_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, pwd_hash


# PUBLIC_INTERFACE
def verify_password(password: str, salt: str, pwd_hash: str) -> bool:
    """Verify password using salted sha-256."""
    calc = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hmac.compare_digest(calc, pwd_hash)


# Token service (HMAC-signed opaque tokens) with in-memory store
@dataclass(frozen=True)
class TokenData:
    user_id: str
    exp: int  # epoch seconds


class TokenStore:
    """Thread-safe in-memory token store."""

    def __init__(self) -> None:
        self._tokens: dict[str, TokenData] = {}
        self._lock = threading.RLock()

    def put(self, token: str, data: TokenData) -> None:
        with self._lock:
            self._tokens[token] = data

    def get(self, token: str) -> Optional[TokenData]:
        with self._lock:
            return self._tokens.get(token)

    def revoke(self, token: str) -> None:
        with self._lock:
            self._tokens.pop(token, None)


class TokenService:
    """Service to issue and validate tokens."""

    def __init__(self, secret_key: str, exp_minutes: int, store: TokenStore) -> None:
        self.secret_key = secret_key.encode("utf-8")
        self.exp_minutes = exp_minutes
        self.store = store

    # PUBLIC_INTERFACE
    def issue_token(self, user_id: str) -> tuple[str, int]:
        """Issue a new signed token and store metadata with expiry."""
        exp = int(time.time()) + (self.exp_minutes * 60)
        # Create opaque token: base64(user_id|exp|rand|hmac)
        rand = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
        body = f"{user_id}|{exp}|{rand}".encode("utf-8")
        sig = hmac.new(self.secret_key, body, hashlib.sha256).digest()
        token = base64.urlsafe_b64encode(body + b"." + sig).decode("utf-8")
        self.store.put(token, TokenData(user_id=user_id, exp=exp))
        return token, exp

    # PUBLIC_INTERFACE
    def verify_token(self, token: str) -> TokenData:
        """Verify token signature and expiration."""
        try:
            raw = base64.urlsafe_b64decode(token.encode("utf-8"))
            body, sig = raw.rsplit(b".", 1)
            expected = hmac.new(self.secret_key, body, hashlib.sha256).digest()
            if not hmac.compare_digest(sig, expected):
                raise AppError.unauthorized("Invalid token signature")
            parts = body.decode("utf-8").split("|")
            user_id, exp_s, _ = parts[0], parts[1], parts[2]
            exp = int(exp_s)
        except Exception:  # noqa: BLE001
            raise AppError.unauthorized("Invalid token format")

        data = self.store.get(token)
        if data is None or data.user_id != user_id or data.exp != exp:
            raise AppError.unauthorized("Unknown or revoked token")
        if exp < int(time.time()):
            self.store.revoke(token)
            raise AppError.unauthorized("Token expired")
        return data


_token_store = TokenStore()


def token_service() -> TokenService:
    settings = get_settings()
    return TokenService(settings.secret_key, settings.token_exp_minutes, _token_store)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


# PUBLIC_INTERFACE
async def get_current_user_optional(request: Request) -> Optional[object]:
    """
    Attempt to return current user if Authorization header is present and valid.
    Returns None if missing/invalid without raising.
    """
    token = await oauth2_scheme(request)  # type: ignore[arg-type]
    if not token:
        return None
    data = token_service().verify_token(token)
    user = memory_user_repo.get_by_id(data.user_id)
    return user


# PUBLIC_INTERFACE
async def get_current_user(request: Request) -> object:
    """
    Dependency that enforces authentication, returning the current user object.
    """
    token = await oauth2_scheme(request)  # type: ignore[arg-type]
    if not token:
        raise AppError.unauthorized("Not authenticated")
    data = token_service().verify_token(token)
    user = memory_user_repo.get_by_id(data.user_id)
    if user is None:
        raise AppError.unauthorized("User not found")
    return user
