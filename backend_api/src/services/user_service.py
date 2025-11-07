from __future__ import annotations

from typing import Optional

from src.core.errors import AppError
from src.core.security import hash_password, verify_password
from src.models.schemas import UserCreate, UserPublic
from src.storage.memory_repo import memory_user_repo


class UserService:
    """User business logic."""

    def __init__(self) -> None:
        self.repo = memory_user_repo

    # PUBLIC_INTERFACE
    def register_user(self, data: UserCreate) -> UserPublic:
        """Register user; reject duplicate email/username."""
        salt, pwd_hash = hash_password(data.password)
        try:
            user = self.repo.create(email=str(data.email), username=data.username, salt=salt, pwd_hash=pwd_hash)
        except ValueError as e:
            code = str(e)
            if code == "email_exists":
                raise AppError.conflict("Email already registered")
            if code == "username_exists":
                raise AppError.conflict("Username already taken")
            raise
        return UserPublic.model_validate(user)

    # PUBLIC_INTERFACE
    def authenticate(self, username_or_email: str, password: str) -> Optional[UserPublic]:
        """Authenticate by username or email."""
        user = self.repo.get_by_username(username_or_email) or self.repo.get_by_email(username_or_email)
        if not user:
            return None
        if not verify_password(password, user["salt"], user["pwd_hash"]):
            return None
        return UserPublic.model_validate(user)


def user_service() -> UserService:
    return UserService()
