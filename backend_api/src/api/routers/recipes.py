from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from src.core.pagination import Page
from src.core.security import get_current_user
from src.models.schemas import (
    RecipeCreate,
    RecipePublic,
    RecipeUpdate,
    RatingRequest,
)
from src.services.recipe_service import RecipeService, recipe_service

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", summary="List recipes with pagination and optional filters")
def list_recipes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tags: list[str] | None = Query(None),
    cuisine: str | None = Query(None),
    time_max: int | None = Query(None, ge=1),
    service: Annotated[RecipeService, Depends(recipe_service)] = None,
) -> Page[RecipePublic]:
    """
    PUBLIC_INTERFACE
    Return paginated list of recipes with filters.

    Args:
        page: Page number (1-based).
        page_size: Items per page (max 100).
        tags: Optional list of tags to filter.
        cuisine: Optional cuisine.
        time_max: Optional max cook time in minutes.
        service: RecipeService.

    Returns:
        Page[RecipePublic]
    """
    return service.list_recipes(page=page, page_size=page_size, tags=tags, cuisine=cuisine, time_max=time_max)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a recipe",
)
def create_recipe(
    payload: RecipeCreate,
    current_user=Depends(get_current_user),
    service: Annotated[RecipeService, Depends(recipe_service)] = None,
) -> RecipePublic:
    """
    PUBLIC_INTERFACE
    Create a recipe owned by the current user.
    """
    return service.create_recipe(owner_id=current_user.id, data=payload)


@router.get(
    "/{recipe_id}",
    summary="Get a recipe by id",
)
def get_recipe(
    recipe_id: str = Path(...),
    service: Annotated[RecipeService, Depends(recipe_service)] = None,
) -> RecipePublic:
    """
    PUBLIC_INTERFACE
    Fetch a recipe by id.
    """
    return service.get_recipe(recipe_id)


@router.put(
    "/{recipe_id}",
    summary="Update a recipe",
)
def update_recipe(
    payload: RecipeUpdate,
    recipe_id: str = Path(...),
    current_user=Depends(get_current_user),
    service: Annotated[RecipeService, Depends(recipe_service)] = None,
) -> RecipePublic:
    """
    PUBLIC_INTERFACE
    Update a recipe. Only the owner can update.
    """
    return service.update_recipe(recipe_id=recipe_id, user_id=current_user.id, data=payload)


from fastapi import Response

@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a recipe",
)
def delete_recipe(
    recipe_id: str = Path(...),
    current_user=Depends(get_current_user),
    service: Annotated[RecipeService, Depends(recipe_service)] = None,
) -> Response:
    """
    PUBLIC_INTERFACE
    Delete a recipe. Only the owner can delete.
    Returns 204 No Content with an empty body.
    """
    service.delete_recipe(recipe_id=recipe_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{recipe_id}/rate",
    summary="Rate a recipe (1..5). Upserts per-user rating.",
)
def rate_recipe(
    payload: RatingRequest,
    recipe_id: str = Path(...),
    current_user=Depends(get_current_user),
    service: Annotated[RecipeService, Depends(recipe_service)] = None,
) -> RecipePublic:
    """
    PUBLIC_INTERFACE
    Rate a recipe (enforces 1..5), one rating per user (updated on re-rate).
    """
    return service.rate_recipe(recipe_id=recipe_id, user_id=current_user.id, rating=payload.rating)
