from __future__ import annotations
from typing import Protocol, Dict, Any, TypeVar, Mapping

T = TypeVar("T", bound=Mapping[str, Any], contravariant=True)


class TaskAdapter(Protocol[T]):
    kind: str

    def run(self, payload: T) -> Dict[str, Any]:
        """
        Must return JSON-serializable dict:
          - title, summary, result_id (optional), artifact_paths (optional)
        """
        ...
