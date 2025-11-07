from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.errors import AppError
from src.core.security import (
    get_current_user,
    TokenService,
    token_service,
)
from src.models.schemas import (
    TokenResponse,
    UserCreate,
    UserPublic,
)
from src.services.user_service import UserService, user_service

router = APIRouter(prefix="/users", tags=["users", "auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User created"},
        400: {"description": "Bad Request"},
        409: {"description": "Duplicate user"},
    },
)
def register_user(
    payload: UserCreate,
    users: Annotated[UserService, Depends(user_service)],
) -> UserPublic:
    """
    PUBLIC_INTERFACE
    Register a new user with unique email and username.

    Args:
        payload: UserCreate model including email, username, and password.
        users: UserService dependency.

    Returns:
        UserPublic: Public user information.

    Raises:
        AppError: With status 409 on duplicate email/username.
    """
    return users.register_user(payload)


@router.post(
    "/login",
    summary="Login and obtain bearer token",
    responses={
        200: {"description": "Token returned"},
        401: {"description": "Invalid credentials"},
    },
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    users: Annotated[UserService, Depends(user_service)],
    tokens: Annotated[TokenService, Depends(token_service)],
) -> TokenResponse:
    """
    PUBLIC_INTERFACE
    Authenticate user using username and password, returning an access token.

    Args:
        form_data: OAuth2PasswordRequestForm containing username and password.
        users: UserService
        tokens: TokenService

    Returns:
        TokenResponse: bearer token and expiry timestamp.
    """
    user = users.authenticate(form_data.username, form_data.password)
    if user is None:
        raise AppError.unauthorized("Invalid credentials")
    token, exp = tokens.issue_token(user.id)
    return TokenResponse(access_token=token, token_type="bearer", expires_at=datetime.fromtimestamp(exp))


@router.get(
    "/me",
    summary="Get current user",
    responses={
        200: {"description": "Current user"},
        401: {"description": "Unauthorized"},
    },
)
def get_me(current_user=Depends(get_current_user)) -> UserPublic:
    """
    PUBLIC_INTERFACE
    Return the current authenticated user.

    Args:
        current_user: Injected authenticated user.

    Returns:
        UserPublic
    """
    return UserPublic.model_validate(current_user)
