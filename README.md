# Cogni Runtime

Minimal runtime and worker runtime scaffold for a ZMQ-based event model.

Overview (from `docs/design.md`):
- Wraps LLM agents such as LangChain; agents are started via `app.invoke({})`.
- A main agent drives the flow and starts sub LLM agents as workers.
- The runtime receives user input and worker completions, queues them, and feeds them to the main agent.
- Workers report completion back to the runtime.
- Runtime and workers communicate over ZMQ.

Quick start:
1) `python main.py` (smoke run; prints a hello message)
2) `python sample/main.py` (run the sample CLI)

Development:
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e .`
- `pyright`

Structure:
- `runtime/`: core runtime (event queue, ZMQ bus, sinks, adapters)
- `worker_runtime/`: worker-side ZMQ loop and adapter registry
- `sample/`: runnable CLI example
- `docs/`: design notes and architecture context

For the event model details, see `docs/design.md`.


---

ZMQ ベースのイベントモデル向けに、ランタイムとワーカー側ランタイムの最小構成を提供します。

概要:
- LangChain などの LLM エージェントをラップし、`app.invoke({})` で起動します。
- main のエージェントが全体を制御し、sub の LLM エージェントを worker として起動します。
- runtime がユーザー入力や worker の完了通知を受け取り、キューに積んで main のエージェントへ渡します。
- worker は終了時に runtime へ完了を通知します。
- runtime と worker は ZMQ で通信します。

クイックスタート:
1) `python main.py` (スモーク実行; hello を表示)
2) `python sample/main.py` (サンプル CLI を実行)

開発:
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e .`
- `pyright`

構成:
- `runtime/`: コアランタイム (イベントキュー, ZMQ バス, sink, adapter)
- `worker_runtime/`: ワーカー側 ZMQ ループと adapter レジストリ
- `sample/`: 実行可能な CLI サンプル
- `docs/`: 設計ノートとアーキテクチャ情報

イベントモデルの詳細は `docs/design.md` を参照してください。
