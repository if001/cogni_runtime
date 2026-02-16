from __future__ import annotations
import json
import threading
import time
from typing import Callable, Optional

from aiohttp import worker

import zmq

from app.runtime.types import TaskSpec, TaskResult


def _j(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def _uj(b: bytes):
    return json.loads(b.decode("utf-8"))


class ControllerBus:
    """
    controller側の ZMQ バス。
    ROUTERで worker と接続し、
      - send_task(): 特定workerへ TaskSpec を送る
      - recv loop: workerから TaskResult を受けて callback
    """

    def __init__(self, bind_addr: str, on_result: Callable[[TaskResult], None]) -> None:
        self.bind_addr = bind_addr
        self.on_result = on_result

        self._ctx = zmq.Context.instance()
        self._sock = self._ctx.socket(zmq.ROUTER)
        # すぐ再起動できるように
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.bind(self.bind_addr)

        self._stop = threading.Event()
        self._th: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._th and self._th.is_alive():
            return
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            self._sock.close(0)
        except Exception:
            pass

    def send_task(self, task: TaskSpec) -> None:
        # ROUTER: [identity][empty][payload]
        msg = {
            "type": "task.run",
            "task_id": task.task_id,
            "kind": task.kind,
            "turn_id": task.turn_id,
            "payload": task.payload,
        }
        ident = task.worker.encode("utf-8")
        self._sock.send_multipart([ident, b"", _j(msg)])

    def _loop(self) -> None:
        poller = zmq.Poller()
        poller.register(self._sock, zmq.POLLIN)

        while not self._stop.is_set():
            try:
                items = dict(poller.poll(timeout=200))
            except Exception:
                break
            if self._sock not in items:
                continue

            try:
                ident, _empty, payload = self._sock.recv_multipart()
                data = _uj(payload)
                # worker -> controller
                # type: "task.result"
                if data.get("type") != "task.result":
                    continue

                r = TaskResult(
                    task_id=data["task_id"],
                    kind=data["kind"],
                    turn_id=data["turn_id"],
                    status=data["status"],
                    worker=data["worker"],
                    title=data.get("title", ""),
                    summary=data.get("summary", ""),
                    result_id=data.get("result_id"),
                    artifact_paths=data.get("artifact_paths") or [],
                    error=data.get("error", ""),
                    progress=float(data.get("progress", 0.0)),
                )
                self.on_result(r)
            except Exception:
                # 必要ならログ
                continue
