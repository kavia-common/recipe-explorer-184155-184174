from __future__ import annotations

from typing import List

from src.core.errors import AppError
from src.core.pagination import Page
from src.models.schemas import RecipeCreate, RecipePublic, RecipeUpdate
from src.storage.memory_repo import memory_recipe_repo


class RecipeService:
    """Recipe CRUD and rating rules."""

    def __init__(self) -> None:
        self.repo = memory_recipe_repo

    # PUBLIC_INTERFACE
    def list_recipes(
        self, page: int, page_size: int, tags: List[str] | None, cuisine: str | None, time_max: int | None
    ) -> Page[RecipePublic]:
        items = list(self.repo.list_all())
        items = self._apply_filters(items, tags=tags, cuisine=cuisine, time_max=time_max)
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = [RecipePublic.model_validate(it) for it in items[start:end]]
        return Page[RecipePublic](items=page_items, total=total, page=page, page_size=page_size)

    # PUBLIC_INTERFACE
    def create_recipe(self, owner_id: str, data: RecipeCreate) -> RecipePublic:
        created = self.repo.create(
            {
                "title": data.title,
                "description": data.description,
                "ingredients": data.ingredients,
                "steps": data.steps,
                "tags": data.tags,
                "cuisine": data.cuisine,
                "time_minutes": data.time_minutes,
                "owner_id": owner_id,
            }
        )
        return RecipePublic.model_validate(created)

    # PUBLIC_INTERFACE
    def get_recipe(self, recipe_id: str) -> RecipePublic:
        rec = self.repo.get(recipe_id)
        if not rec:
            raise AppError.not_found("Recipe not found")
        return RecipePublic.model_validate(rec)

    # PUBLIC_INTERFACE
    def update_recipe(self, recipe_id: str, user_id: str, data: RecipeUpdate) -> RecipePublic:
        rec = self.repo.get(recipe_id)
        if not rec:
            raise AppError.not_found("Recipe not found")
        if rec["owner_id"] != user_id:
            raise AppError.forbidden("You are not the owner of this recipe")
        updates = data.model_dump(exclude_none=True)
        updated = self.repo.update(recipe_id, updates)
        return RecipePublic.model_validate(updated)

    # PUBLIC_INTERFACE
    def delete_recipe(self, recipe_id: str, user_id: str) -> None:
        rec = self.repo.get(recipe_id)
        if not rec:
            raise AppError.not_found("Recipe not found")
        if rec["owner_id"] != user_id:
            raise AppError.forbidden("You are not the owner of this recipe")
        self.repo.delete(recipe_id)

    # PUBLIC_INTERFACE
    def rate_recipe(self, recipe_id: str, user_id: str, rating: int) -> RecipePublic:
        if rating < 1 or rating > 5:
            raise AppError.bad_request("Rating must be between 1 and 5")
        rec = self.repo.get(recipe_id)
        if not rec:
            raise AppError.not_found("Recipe not found")
        updated = self.repo.upsert_rating(recipe_id, user_id, rating)
        return RecipePublic.model_validate(updated)

    def _apply_filters(
        self,
        items: List[dict],
        tags: List[str] | None,
        cuisine: str | None,
        time_max: int | None,
    ) -> List[dict]:
        filtered = items
        if tags:
            tag_set = {t.lower() for t in tags}
            filtered = [it for it in filtered if tag_set.issubset({t.lower() for t in it.get("tags", [])})]
        if cuisine:
            filtered = [it for it in filtered if (it.get("cuisine") or "").lower() == cuisine.lower()]
        if time_max:
            filtered = [it for it in filtered if (it.get("time_minutes") or 10**9) <= time_max]
        return filtered
