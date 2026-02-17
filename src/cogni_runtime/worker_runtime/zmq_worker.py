from __future__ import annotations
import asyncio
import inspect
import json
from typing import Any, Dict, Optional

import zmq
from logging import getLogger, basicConfig, INFO


logger = getLogger(__name__)


from cogni_runtime.worker_runtime.registry import AdapterRegistry


def _j(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def _uj(b: bytes):
    return json.loads(b.decode("utf-8"))


class ZmqWorker:
    """
    DEALER worker.
    controller(ROUTER)から task.run を受け取り、adapterを実行して task.result を返す。
    """

    def __init__(
        self, *, worker_name: str, connect_addr: str, registry: AdapterRegistry
    ) -> None:
        self.worker_name = worker_name
        self.connect_addr = connect_addr
        self.registry = registry
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None

        self._ctx = zmq.Context.instance()
        self._sock = self._ctx.socket(zmq.DEALER)
        self._sock.setsockopt(zmq.IDENTITY, worker_name.encode("utf-8"))
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.connect(connect_addr)

    def serve_forever(self) -> None:
        logger.info("worker start")
        while True:
            # DEALER: [empty][payload] が来る（ROUTER側が empty を挟むため）
            parts = self._sock.recv_multipart()
            payload = parts[-1]
            data = _uj(payload)

            if data.get("type") != "task.run":
                continue

            msg = self._handle_task(data)
            if msg:
                self._sock.send_multipart([b"", _j(msg)])

    def _handle_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = data["task_id"]
        kind = data["kind"]
        turn_id = data["turn_id"]
        payload = data.get("payload") or {}

        try:
            adapter = self.registry.get(kind)
            out = adapter.run(payload)  # 外部agent invoke は adapter 内でやる
            if inspect.isawaitable(out):
                out = self._run_coroutine(out)
            out = out or {}
            if not isinstance(out, dict):
                out = {"value": out}
            out.setdefault("schema_version", 1)

            return {
                "type": "task.result",
                "worker": self.worker_name,
                "task_id": task_id,
                "kind": kind,
                "turn_id": turn_id,
                "status": "DONE",
                "payload": out,
            }
        except Exception as e:
            return {
                "type": "task.result",
                "worker": self.worker_name,
                "task_id": task_id,
                "kind": kind,
                "turn_id": turn_id,
                "status": "FAILED",
                "payload": {
                    "schema_version": 1,
                    "error": {
                        "code": "worker_error",
                        "message": f"{type(e).__name__}: {e}",
                    },
                },
            }

    def _run_coroutine(self, coro: Any) -> Any:
        if self._async_loop is None:
            self._async_loop = asyncio.new_event_loop()
        return self._async_loop.run_until_complete(coro)
