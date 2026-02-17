from __future__ import annotations
from typing import Dict, Union
from .adapters import TaskAdapter, AsyncTaskAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self._m: Dict[str, Union[TaskAdapter, AsyncTaskAdapter]] = {}

    def register(self, adapter: Union[TaskAdapter, AsyncTaskAdapter]) -> None:
        self._m[adapter.kind] = adapter

    def get(self, kind: str) -> Union[TaskAdapter, AsyncTaskAdapter]:
        if kind not in self._m:
            raise KeyError(f"adapter not found for kind={kind}")
        return self._m[kind]
