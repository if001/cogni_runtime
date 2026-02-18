# Cogni Runtime
Minimal runtime and worker runtime scaffold for a ZMQ-based event model.

## Overview
- Wraps LLM agents such as LangChain; agents are started via `app.invoke({})`.
- A main agent drives the flow and starts sub LLM agents as workers.
- The runtime receives user input and worker completions, queues them, and feeds them to the main agent.
- Workers report completion back to the runtime.
- Runtime and workers communicate over ZMQ.

## Quick start:
``` python
uv sync
uv pip install -e .


uv run examples/worker.py --name sample_worker
uv run examples/async_main.py
```

## Structure:
- `runtime/`: core runtime (event queue, ZMQ bus, sinks, adapters)
- `worker_runtime/`: worker-side ZMQ loop and adapter registry
- `sample/`: runnable CLI example
- `docs/`: design notes and architecture context

## Async runtime:
- `AsyncMainAgentRuntime.start()` starts a dedicated event loop thread.
- Use `await AsyncMainAgentRuntime.a_start()` when running inside an existing loop.
- Use `await AsyncMainAgentRuntime.a_stop()` to stop when started via `a_start()`.

For the event model details, see `docs/design.md`.


---

ZMQ ベースのイベントモデル向けに、ランタイムとワーカー側ランタイムの最小構成を提供します。

## 概要:
- LangChain などの LLM エージェントをラップし、`app.invoke({})` で起動します。
- main のエージェントが全体を制御し、sub の LLM エージェントを worker として起動します。
- runtime がユーザー入力や worker の完了通知を受け取り、キューに積んで main のエージェントへ渡します。
- worker は終了時に runtime へ完了を通知します。
- runtime と worker は ZMQ で通信します。

## クイックスタート:
``` python
uv sync
uv pip install -e .


uv run examples/worker.py --name sample_worker
uv run examples/async_main.py
```

## 構成:
- `runtime/`: コアランタイム (イベントキュー, ZMQ バス, sink, adapter)
- `worker_runtime/`: ワーカー側 ZMQ ループと adapter レジストリ
- `examples/`: 実行可能な CLI サンプル
- `docs/`: 設計ノートとアーキテクチャ情報

## Async runtime:
- `AsyncMainAgentRuntime.start()` は専用のイベントループスレッドを起動します。
- 既存ループ内では `await AsyncMainAgentRuntime.a_start()` を使います。
- `a_start()` で起動した場合は `await AsyncMainAgentRuntime.a_stop()` で停止します。

イベントモデルの詳細は `docs/design.md` を参照してください。
