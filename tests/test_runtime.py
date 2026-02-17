from __future__ import annotations

import asyncio
import queue
from typing import Any, Dict, List, Tuple

from cogni_runtime.runtime import (
    AsyncMainAgentRuntime,
    MainAgentRuntime,
    Client,
    AsyncClient,
    InputEvent,
    InputEventType,
    LlmAgentAdapter,
    LlmAgentAsyncAdapter,
)


class SyncEchoAgent(LlmAgentAdapter):
    def handle_event(
        self, event: InputEvent, state: Dict[str, Any]
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        if event.type == InputEventType.User:
            return ["hi"], "final", {"mode": "sync"}
        return [], "", {}


class AsyncEchoAgent(LlmAgentAsyncAdapter):
    async def handle_event(
        self, event: InputEvent, state: Dict[str, Any]
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        if event.type == InputEventType.User:
            return ["hi"], "final", {"mode": "async"}
        return [], "", {}


def _wait_for_final(q: "queue.Queue", turn_id: str, timeout: float = 2.0) -> str:
    while True:
        ev = q.get(timeout=timeout)
        if ev.type == "assistant.final" and ev.turn_id == turn_id:
            return str(ev.payload.get("text", ""))


def test_main_agent_runtime_sync() -> None:
    runtime = MainAgentRuntime(
        llm_agent=SyncEchoAgent,
        zmq_bind_addr="inproc://test-runtime-sync",
    )
    runtime.start()
    client = Client(runtime)

    try:
        turn_id = client.send("hello")
        text = _wait_for_final(client._q, turn_id)
        assert text == "final"
    finally:
        client.close()
        runtime.stop()


def test_async_main_agent_runtime() -> None:
    async def _run() -> None:
        runtime = AsyncMainAgentRuntime(
            llm_agent=AsyncEchoAgent,
            zmq_bind_addr="inproc://test-runtime-async",
        )
        await runtime.a_start()
        client = AsyncClient(runtime)

        try:
            turn_id = client.send("hello")
            text = await client.await_final(turn_id, timeout=2.0)
            assert text == "final"
        finally:
            client.close()
            await runtime.a_stop()

    asyncio.run(_run())
