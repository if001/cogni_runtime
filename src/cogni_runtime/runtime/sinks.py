from __future__ import annotations
import threading, queue
from typing import Dict, Tuple
from .types import OutputEvent
from .types import new_id


class InMemoryBroadcastSink:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: Dict[str, "queue.Queue[OutputEvent]"] = {}

    def subscribe(
        self, max_queue: int = 1000
    ) -> Tuple[str, "queue.Queue[OutputEvent]"]:
        sid = new_id()
        q: "queue.Queue[OutputEvent]" = queue.Queue(maxsize=max_queue)
        with self._lock:
            self._subs[sid] = q
        return sid, q

    def unsubscribe(self, sid: str) -> None:
        with self._lock:
            self._subs.pop(sid, None)

    def emit(self, ev: OutputEvent) -> None:
        with self._lock:
            subs = list(self._subs.values())
        for q in subs:
            try:
                q.put_nowait(ev)
            except queue.Full:
                pass
