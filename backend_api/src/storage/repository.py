from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional


class UserRepository(ABC):
    @abstractmethod
    def create(self, email: str, username: str, salt: str, pwd_hash: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[dict]:
        raise NotImplementedError


class RecipeRepository(ABC):
    @abstractmethod
    def create(self, data: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get(self, recipe_id: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def update(self, recipe_id: str, updates: dict) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, recipe_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Iterable[dict]:
        raise NotImplementedError

    @abstractmethod
    def upsert_rating(self, recipe_id: str, user_id: str, rating: int) -> Optional[dict]:
        raise NotImplementedError
