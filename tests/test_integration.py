from __future__ import annotations

import queue
from typing import Any, Dict, List, Tuple

from cogni_runtime.runtime import MainAgentRuntime, Client, InputEvent, InputEventType
from cogni_runtime.runtime.types import TaskResult
from cogni_runtime.worker_runtime import AdapterRegistry, TaskAdapter, ZmqWorker


class SyncEchoAgent:
    def __init__(self, ctx: Any) -> None:
        self.ctx = ctx

    def handle_event(
        self, event: InputEvent, state: Dict[str, Any]
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        if event.type == InputEventType.SubDone:
            payload = event.payload.get("payload") or {}
            return [], payload.get("result", ""), {}
        return [], "", {}


class WorkerAdapter(TaskAdapter):
    kind = "work"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": payload.get("value", "")}


def _wait_for_final(q: "queue.Queue", turn_id: str, timeout: float = 2.0) -> str:
    while True:
        ev = q.get(timeout=timeout)
        if ev.type == "assistant.final" and ev.turn_id == turn_id:
            return str(ev.payload.get("text", ""))


def test_runtime_worker_integration() -> None:
    runtime = MainAgentRuntime(
        llm_agent=SyncEchoAgent,
        zmq_bind_addr="inproc://test-runtime-integration",
    )
    runtime.start()
    client = Client(runtime)

    registry = AdapterRegistry()
    registry.register(WorkerAdapter())
    worker = ZmqWorker(
        worker_name="worker_test",
        connect_addr="inproc://test-worker-integration",
        registry=registry,
    )

    try:
        turn_id = client.send("trigger")
        msg = worker._handle_task(
            {
                "type": "task.run",
                "task_id": "task1",
                "kind": "work",
                "turn_id": turn_id,
                "payload": {"value": "done"},
            }
        )
        task_result = TaskResult(
            task_id=msg["task_id"],
            kind=msg["kind"],
            turn_id=msg["turn_id"],
            status=msg["status"],
            worker=msg["worker"],
            payload=msg["payload"],
        )
        runtime._on_task_result(task_result)
        text = _wait_for_final(client._q, turn_id)
        assert text == "done"
    finally:
        worker._sock.close(0)
        client.close()
        runtime.stop()
