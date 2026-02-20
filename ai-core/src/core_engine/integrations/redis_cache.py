"""Optional Redis caching (MVP)."""

from __future__ import annotations
from typing import Any, Optional


class RedisCache:
    def __init__(self, url: str):
        self.url = url

    def get_json(self, key: str) -> Optional[Any]:
        return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 600) -> None:
        pass
