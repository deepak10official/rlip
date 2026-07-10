"""Simple persistent session memory for the Agents SDK."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents import SessionSettings

from backend.config import settings


class JsonFileSession:
    """File-backed implementation of the Agents SDK Session protocol."""

    session_settings: SessionSettings | None = None

    def __init__(self, session_id: str, memory_root: Path | None = None) -> None:
        self.session_id = session_id
        self.memory_root = memory_root or settings.memory_root
        self.memory_root.mkdir(parents=True, exist_ok=True)
        self.path = self.memory_root / f"{self.session_id}.json"

    async def get_items(self, limit: int | None = None) -> list[Any]:
        items = self._read_items()
        if limit is None:
            return items
        return items[-limit:]

    async def add_items(self, items: list[Any]) -> None:
        current = self._read_items()
        current.extend(_jsonable(item) for item in items)
        self._write_items(current)

    async def pop_item(self) -> Any | None:
        items = self._read_items()
        if not items:
            return None
        item = items.pop()
        self._write_items(items)
        return item

    async def clear_session(self) -> None:
        self._write_items([])

    def _read_items(self) -> list[Any]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []

    def _write_items(self, items: list[Any]) -> None:
        self.path.write_text(json.dumps(items, indent=2, default=str))


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "__dict__"):
            return value.__dict__
        return str(value)

