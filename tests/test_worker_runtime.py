from __future__ import annotations

import asyncio
from typing import Dict, Any

from cogni_runtime.worker_runtime import (
    AdapterRegistry,
    TaskAdapter,
    AsyncTaskAdapter,
    ZmqWorker,
)


class SyncAdapter(TaskAdapter):
    kind = "sync"

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "payload": payload}


class AsyncAdapter(AsyncTaskAdapter):
    kind = "async"

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0)
        return {"ok": True, "payload": payload}


def _make_worker(registry: AdapterRegistry) -> ZmqWorker:
    worker = ZmqWorker(
        worker_name="worker_test",
        connect_addr="inproc://test-worker",
        registry=registry,
    )
    return worker


def test_worker_sync_adapter() -> None:
    registry = AdapterRegistry()
    registry.register(SyncAdapter())
    worker = _make_worker(registry)

    try:
        msg = worker._handle_task(
            {
                "type": "task.run",
                "task_id": "task1",
                "kind": "sync",
                "turn_id": "turn1",
                "payload": {"a": 1},
            }
        )
        assert msg["status"] == "DONE"
        assert msg["payload"]["ok"] is True
        assert msg["payload"]["schema_version"] == 1
    finally:
        worker._sock.close(0)


def test_worker_async_adapter() -> None:
    registry = AdapterRegistry()
    registry.register(AsyncAdapter())
    worker = _make_worker(registry)

    try:
        msg = worker._handle_task(
            {
                "type": "task.run",
                "task_id": "task1",
                "kind": "async",
                "turn_id": "turn1",
                "payload": {"a": 1},
            }
        )
        assert msg["status"] == "DONE"
        assert msg["payload"]["ok"] is True
        assert msg["payload"]["schema_version"] == 1
    finally:
        worker._sock.close(0)
