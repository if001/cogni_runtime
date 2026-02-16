from __future__ import annotations

import threading
import sys
from typing import Dict, Any, Tuple, List
from runtime.runtime import MainAgentRuntime
from runtime.client import Client
from runtime.llm_adapter import LlmAgentAdapter
from runtime.types import InputEvent, InputEventType, OutputEventType


class SimpleEchoAgent(LlmAgentAdapter):
    def handle_event(
        self,
        event: InputEvent,
        state: Dict[str, Any],
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        if event.type == InputEventType.User:
            text = event.payload.get("text", "")
            return [], f"Echo: {text}", {}

        elif event.type == InputEventType.SubDone:
            title = event.payload.get("title", "")
            summary = event.payload.get("summary", "")
            return [], f"[Worker Done] {title}\n{summary}", {}

        elif event.type == InputEventType.SubFailed:
            err = event.payload.get("error", "")
            return [], f"[Worker Failed] {err}", {}

        return [], "", {}


def output_loop(client: Client, stop_event: threading.Event):
    """
    OutputEvent を購読してターミナル表示
    """
    while not stop_event.is_set():
        ev = client.q.get()

        if ev.type == OutputEventType.AssistantDelta:
            print(ev.payload.get("text", ""), end="", flush=True)

        elif ev.type == OutputEventType.AssistantFinal:
            print(f"\nassistant> {ev.payload.get('text', '')}")

        elif ev.type == OutputEventType.Status:
            pass  # 必要なら表示

        elif ev.type == OutputEventType.Notice:
            pass  # dispatchなどの通知

        elif ev.type == OutputEventType.Error:
            print(f"[error] {ev.payload.get('message')}", file=sys.stderr)


def main():
    # --- runtime 初期化 ---
    runtime = MainAgentRuntime(
        llm_agent=SimpleEchoAgent,
        zmq_bind_addr="tcp://127.0.0.1:5555",
    )

    runtime.start()

    client = Client(runtime)

    stop_event = threading.Event()

    # 出力購読スレッド
    th = threading.Thread(target=output_loop, args=(client, stop_event), daemon=True)
    th.start()

    print("CLI started. Ctrl+C to exit.")

    try:
        while True:
            text = input("\nyou> ")

            if not text.strip():
                continue

            turn_id = client.send(text)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        stop_event.set()
        client.close()
        runtime.stop()


if __name__ == "__main__":
    main()
