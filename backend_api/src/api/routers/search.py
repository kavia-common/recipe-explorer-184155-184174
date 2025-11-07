from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.core.pagination import Page
from src.models.schemas import RecipePublic
from src.services.search_service import SearchService, search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", summary="Search recipes")
def search(
    q: str | None = Query(None),
    tags: list[str] | None = Query(None),
    cuisine: str | None = Query(None),
    time_max: int | None = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: Annotated[SearchService, Depends(search_service)] = None,
) -> Page[RecipePublic]:
    """
    PUBLIC_INTERFACE
    Search recipes by text and filters with pagination.

    Returns:
        Page[RecipePublic]
    """
    return service.search(q=q, tags=tags, cuisine=cuisine, time_max=time_max, page=page, page_size=page_size)
