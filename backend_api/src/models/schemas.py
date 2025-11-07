from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.core.pagination import Page


# Users
class UserBase(BaseModel):
    id: str = Field(...)
    email: EmailStr = Field(...)
    username: str = Field(...)


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Unique email")
    username: str = Field(..., min_length=3, max_length=32, description="Unique username")
    password: str = Field(..., min_length=6, max_length=128, description="Password")


class UserPublic(UserBase):
    created_at: datetime = Field(...)


# Token
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Bearer token")
    token_type: str = Field(default="bearer")
    expires_at: datetime = Field(...)


# Recipes
class RecipeBase(BaseModel):
    id: str = Field(...)
    title: str = Field(...)
    description: str = Field(default="")
    ingredients: Sequence[str] = Field(default_factory=list)
    steps: Sequence[str] = Field(default_factory=list)
    tags: Sequence[str] = Field(default_factory=list)
    cuisine: Optional[str] = Field(default=None)
    time_minutes: Optional[int] = Field(default=None, ge=1)
    owner_id: str = Field(...)
    rating_avg: float = Field(default=0.0, ge=0, le=5)
    rating_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)


class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    ingredients: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    cuisine: Optional[str] = Field(default=None)
    time_minutes: Optional[int] = Field(default=None, ge=1)


class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    ingredients: Optional[List[str]] = Field(default=None)
    steps: Optional[List[str]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    cuisine: Optional[str] = Field(default=None)
    time_minutes: Optional[int] = Field(default=None, ge=1)

    @field_validator("ingredients", "steps", "tags")
    @classmethod
    def ensure_lists(cls, v):
        return v if v is not None else None


class RecipePublic(RecipeBase):
    pass


# Ratings
class RatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)


# Errors
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


# Re-exports for generics to serialize
__all__ = [
    "UserCreate",
    "UserPublic",
    "TokenResponse",
    "RecipeCreate",
    "RecipeUpdate",
    "RecipePublic",
    "RatingRequest",
    "Page",
    "ErrorEnvelope",
]
