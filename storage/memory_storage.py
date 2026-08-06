from __future__ import annotations

from collections import OrderedDict
from typing import Any


class MemoryStorage:
    def __init__(self, max_size: int = 1000):
        self._storage: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size

    def set(self, key: str, value: Any) -> None:
        if key in self._storage:
            del self._storage[key]
        elif len(self._storage) >= self._max_size:
            self._storage.popitem(last=False)
        self._storage[key] = value

    def get(self, key: str) -> Any | None:
        if key in self._storage:
            value = self._storage.pop(key)
            self._storage[key] = value
            return value
        return None

    def delete(self, key: str) -> bool:
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    def clear(self) -> None:
        self._storage.clear()

    def keys(self) -> list[str]:
        return list(self._storage.keys())

    def __len__(self) -> int:
        return len(self._storage)

    def __contains__(self, key: str) -> bool:
        return key in self._storage
