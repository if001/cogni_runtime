from typing import Any, Callable, Dict, Iterator, List, Optional, Protocol, Tuple
from app.runtime.runtime import (
    MainAgentRuntime,
    Client,
    SubAgentHandle,
    InputEvent,
    LlmAgentAdapter,
)


class SimpleEchoAgent(LlmAgentAdapter):
    """
    動作確認用のダミー実装（実際は LangGraph/LangChain adapter に置き換える）
    """

    def handle_event(
        self, event: InputEvent, state: Dict[str, Any]
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        if event.type == "user.message":
            text = str(event.payload.get("text", ""))
            # delta っぽく分割
            chunks = [text[i : i + 12] for i in range(0, len(text), 12)]
            final = f"Echo: {text}"
            return chunks, final, {"agent": "SimpleEchoAgent"}
        elif event.type == "sub.done":
            worker_payload = event.payload.get("payload") or {}
            title = worker_payload.get("title", "sub_agent")
            summary = worker_payload.get("summary", "")
            final = f"[sub_agent完了] {title}\n{summary}"
            return [], final, {"agent": "SimpleEchoAgent"}
        else:
            return [], "", {"agent": "SimpleEchoAgent"}


if __name__ == "__main__":
    runtime = MainAgentRuntime(llm_agent=SimpleEchoAgent())
    runtime.start()

    client = Client(runtime)

    # user input
    turn_id = client.send("こんにちは。deep researchの結果はありますか？")

    # サブエージェント（例：deep_research_worker完了通知）を擬似的に入れる
    sub = SubAgentHandle(runtime, name="deep_research")
    sub.publish_done(
        title="LangChain v1 tool calling loop",
        summary="create_agentはtool call→tool result→次の推論…を反復し、結果を踏まえて次のtool callが可能。",
        result_id="drres_xxx",
        turn_id=turn_id,  # どの質問に紐づくか（任意）
    )

    # output consumer: ストリーム表示
    try:
        for ev in client.events(timeout=5.0):
            if ev.type == "assistant.delta":
                print(ev.payload["text"], end="", flush=True)
            elif ev.type == "assistant.final":
                print("\n---\nFINAL:", ev.payload["text"])
            elif ev.type == "status":
                pass
            elif ev.type == "notice":
                print("[NOTICE]", ev.payload)
            elif ev.type == "error":
                print("[ERROR]", ev.payload)
    finally:
        client.close()
        runtime.stop()
