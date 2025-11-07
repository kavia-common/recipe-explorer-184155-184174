from __future__ import annotations

from typing import List

from src.core.pagination import Page
from src.models.schemas import RecipePublic
from src.storage.memory_repo import memory_recipe_repo


class SearchService:
    """Search recipes by text and filters."""

    def __init__(self) -> None:
        self.repo = memory_recipe_repo

    # PUBLIC_INTERFACE
    def search(
        self,
        q: str | None,
        tags: List[str] | None,
        cuisine: str | None,
        time_max: int | None,
        page: int,
        page_size: int,
    ) -> Page[RecipePublic]:
        items = list(self.repo.list_all())
        if q:
            ql = q.lower()
            items = [
                it
                for it in items
                if ql in it.get("title", "").lower()
                or ql in it.get("description", "").lower()
                or any(ql in ing.lower() for ing in it.get("ingredients", []))
            ]
        # reuse simple filters
        if tags:
            tag_set = {t.lower() for t in tags}
            items = [it for it in items if tag_set.issubset({t.lower() for t in it.get("tags", [])})]
        if cuisine:
            items = [it for it in items if (it.get("cuisine") or "").lower() == cuisine.lower()]
        if time_max:
            items = [it for it in items if (it.get("time_minutes") or 10**9) <= time_max]

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = [RecipePublic.model_validate(it) for it in items[start:end]]
        return Page[RecipePublic](items=page_items, total=total, page=page, page_size=page_size)


def search_service() -> SearchService:
    return SearchService()
