from __future__ import annotations
from typing import Protocol, Dict, Any, List, Tuple
from .types import InputEvent


class RuntimeApi(Protocol):
    def dispatch_task(
        self, *, worker: str, kind: str, turn_id: str, payload: dict
    ) -> dict: ...


class LlmAgentAdapter(Protocol):
    def __init__(self, ctx: RuntimeApi): ...
    def handle_event(
        self, event: InputEvent, state: Dict[str, Any]
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        """
        Returns:
          - deltas: list[str]  (stream chunks)
          - final_text: str
          - meta: dict         (tool history etc.)
        """
        ...


class LlmAgentAsyncAdapter(Protocol):
    def __init__(self, ctx: RuntimeApi): ...
    async def handle_event(
        self, event: InputEvent, state: Dict[str, Any]
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        """
        Returns:
          - deltas: list[str]  (stream chunks)
          - final_text: str
          - meta: dict         (tool history etc.)
        """
        ...
