from __future__ import annotations

import threading

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Dict, Iterable, Optional

from src.storage.repository import RecipeRepository, UserRepository


class MemoryUserRepository(UserRepository):
    """Thread-safe in-memory user repo."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_id: Dict[str, dict] = {}
        self._by_email: Dict[str, str] = {}
        self._by_username: Dict[str, str] = {}

    def create(self, email: str, username: str, salt: str, pwd_hash: str) -> dict:
        with self._lock:
            if email in self._by_email:
                raise ValueError("email_exists")
            if username in self._by_username:
                raise ValueError("username_exists")
            uid = str(uuid.uuid4())
            now = datetime.utcnow()
            user = {
                "id": uid,
                "email": email,
                "username": username,
                "salt": salt,
                "pwd_hash": pwd_hash,
                "created_at": now,
            }
            self._by_id[uid] = user
            self._by_email[email] = uid
            self._by_username[username] = uid
            return user

    def get_by_email(self, email: str) -> Optional[dict]:
        with self._lock:
            uid = self._by_email.get(email)
            return self._by_id.get(uid) if uid else None

    def get_by_username(self, username: str) -> Optional[dict]:
        with self._lock:
            uid = self._by_username.get(username)
            return self._by_id.get(uid) if uid else None

    def get_by_id(self, user_id: str) -> Optional[dict]:
        with self._lock:
            return self._by_id.get(user_id)


class MemoryRecipeRepository(RecipeRepository):
    """Thread-safe in-memory recipe repo with per-user ratings."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_id: Dict[str, dict] = {}
        self._ratings: Dict[str, Dict[str, int]] = defaultdict(dict)  # recipe_id -> user_id -> rating

    def create(self, data: dict) -> dict:
        with self._lock:
            rid = str(uuid.uuid4())
            now = datetime.utcnow()
            recipe = {
                "id": rid,
                "created_at": now,
                "updated_at": now,
                "rating_avg": 0.0,
                "rating_count": 0,
                **data,
            }
            self._by_id[rid] = recipe
            return recipe

    def get(self, recipe_id: str) -> Optional[dict]:
        with self._lock:
            return self._by_id.get(recipe_id)

    def update(self, recipe_id: str, updates: dict) -> Optional[dict]:
        with self._lock:
            rec = self._by_id.get(recipe_id)
            if not rec:
                return None
            rec.update({k: v for k, v in updates.items() if v is not None})
            rec["updated_at"] = datetime.utcnow()
            return rec

    def delete(self, recipe_id: str) -> bool:
        with self._lock:
            existed = recipe_id in self._by_id
            if existed:
                self._by_id.pop(recipe_id, None)
                self._ratings.pop(recipe_id, None)
            return existed

    def list_all(self) -> Iterable[dict]:
        with self._lock:
            return list(self._by_id.values())

    def _recalc_rating(self, recipe_id: str) -> None:
        ratings = self._ratings.get(recipe_id, {})
        count = len(ratings)
        avg = sum(ratings.values()) / count if count else 0.0
        rec = self._by_id.get(recipe_id)
        if rec:
            rec["rating_count"] = count
            rec["rating_avg"] = round(avg, 2)
            rec["updated_at"] = datetime.utcnow()

    def upsert_rating(self, recipe_id: str, user_id: str, rating: int) -> Optional[dict]:
        with self._lock:
            rec = self._by_id.get(recipe_id)
            if not rec:
                return None
            self._ratings[recipe_id][user_id] = rating
            self._recalc_rating(recipe_id)
            return rec


# Singleton in-memory repos (simple module-level instances)
memory_user_repo = MemoryUserRepository()
memory_recipe_repo = MemoryRecipeRepository()
