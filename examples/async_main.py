from __future__ import annotations

import asyncio
import sys
from contextlib import suppress
from typing import Dict, Any, Tuple, List

from cogni_runtime import runtime
from cogni_runtime.runtime import (
    AsyncMainAgentRuntime,
    AsyncClient,
    LlmAgentAsyncAdapter,
    InputEvent,
    InputEventType,
    OutputEventType,
)
from cogni_runtime.runtime.llm_adapter import RuntimeApi


class SimpleAsyncEchoAgent(LlmAgentAsyncAdapter):
    def __init__(self, runtimeApi: RuntimeApi):
        self.runtimeApi = runtimeApi

    async def handle_event(
        self,
        event: InputEvent,
        state: Dict[str, Any],
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        if event.type == InputEventType.User:
            text = event.payload.get("text", "")
            if text == "dispatch":
                self.runtimeApi.dispatch_task(
                    worker="sample_worker",
                    kind="sample_agent",
                    turn_id="",
                    payload={"message": "ok"},
                )

            return [], f"Echo: {text}", {}

        if event.type == InputEventType.SubDone:
            worker_payload = event.payload or {}
            print("worker_payload: ", worker_payload)
            message = worker_payload.get("message", "")
            return [], f"[Worker Done]\n{message}", {}

        if event.type == InputEventType.SubFailed:
            err = event.payload.get("error") or {}
            message = err.get("message", "worker failed")
            return [], f"[Worker Failed] {message}", {}

        return [], "", {}


async def output_loop(client: AsyncClient, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        ev = await client.queue_get()

        if ev.type == OutputEventType.AssistantDelta:
            print(ev.payload.get("text", ""), end="", flush=True)

        elif ev.type == OutputEventType.AssistantFinal:
            print(f"\nassistant> {ev.payload.get('text', '')}")

        elif ev.type == OutputEventType.Status:
            pass

        elif ev.type == OutputEventType.Notice:
            pass

        elif ev.type == OutputEventType.Error:
            print(f"[error] {ev.payload.get('message')}", file=sys.stderr)


async def main() -> None:
    runtime = AsyncMainAgentRuntime(
        llm_agent=SimpleAsyncEchoAgent,
        zmq_bind_addr="tcp://127.0.0.1:5555",
    )

    await runtime.a_start()

    client = AsyncClient(runtime)

    stop_event = asyncio.Event()

    out_task = asyncio.create_task(output_loop(client, stop_event))

    print("CLI started. Ctrl+C to exit.")

    try:
        while True:
            text = await asyncio.to_thread(input, "\nyou> ")

            if not text.strip():
                continue

            client.send(text)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        stop_event.set()
        out_task.cancel()
        with suppress(asyncio.CancelledError):
            await out_task
        client.close()
        await runtime.a_stop()


if __name__ == "__main__":
    asyncio.run(main())
