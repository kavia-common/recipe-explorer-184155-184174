from __future__ import annotations

from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic page envelope."""

    items: Sequence[T] = Field(default_factory=list, description="Page items")
    total: int = Field(..., ge=0, description="Total items available")
    page: int = Field(..., ge=1, description="Page number (1-based)")
    page_size: int = Field(..., ge=1, le=100, description="Page size (max 100)")
