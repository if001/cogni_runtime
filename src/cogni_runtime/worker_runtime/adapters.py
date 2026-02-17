from __future__ import annotations
from typing import Protocol, Dict, Any, TypeVar, Mapping

T = TypeVar("T", bound=Mapping[str, Any], contravariant=True)


class TaskAdapter(Protocol[T]):
    kind: str

    def run(self, payload: T) -> Dict[str, Any]:
        """
        Must return JSON-serializable dict.
        The shape is defined by the library user and passed through as-is.
        Large artifacts should be saved to files and returned as paths.
        """
        ...


class AsyncTaskAdapter(Protocol[T]):
    kind: str

    async def run(self, payload: T) -> Dict[str, Any]:
        """
        Async variant of TaskAdapter.run.
        """
        ...
