from __future__ import annotations
from typing import Dict
from .adapters import TaskAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self._m: Dict[str, TaskAdapter] = {}

    def register(self, adapter: TaskAdapter) -> None:
        self._m[adapter.kind] = adapter

    def get(self, kind: str) -> TaskAdapter:
        if kind not in self._m:
            raise KeyError(f"adapter not found for kind={kind}")
        return self._m[kind]
