from __future__ import annotations
from typing import Iterator, Optional
from .runtime import MainAgentRuntime
from .types import OutputEvent


class Client:
    def __init__(self, runtime: MainAgentRuntime, max_queue: int = 1000) -> None:
        self.runtime = runtime
        self.sub_id, self._q = runtime.subscribe(max_queue=max_queue)

    def close(self) -> None:
        self.runtime.unsubscribe(self.sub_id)

    def send(self, text: str) -> str:
        return self.runtime.submit_user_text(text)

    def queue_get(self) -> OutputEvent:
        return self._q.get()

    def await_final(self, turn_id: str, timeout: float = 120.0) -> str:
        import time

        t0 = time.time()
        while time.time() - t0 < timeout:
            ev: OutputEvent = self._q.get()
            if ev.type == "assistant.final" and ev.turn_id == turn_id:
                return str(ev.payload.get("text", ""))
        raise TimeoutError(f"final not received: {turn_id}")
