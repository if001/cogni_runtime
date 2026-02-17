from __future__ import annotations
import queue
import threading
from typing import Any, Dict, Optional, Tuple, List, Type

from cogni_runtime.runtime.types import (
    InputEvent,
    InputEventType,
    OutputEvent,
    OutputEventType,
    OutputEventTypeLiteral,
    TaskSpec,
    TaskResult,
    new_id,
    now_ts,
)
from cogni_runtime.runtime.sinks import InMemoryBroadcastSink
from cogni_runtime.runtime.llm_adapter import LlmAgentAdapter
from cogni_runtime.runtime.zmq_bus import ControllerBus


class MainAgentRuntime:
    """
    - user入力 & worker結果を 1本のPriorityQueue に積む
    - llm_agent は逐次実行
    - worker は常駐（ZMQ）でタスクを投げるだけ
    """

    def __init__(
        self,
        llm_agent: Type[LlmAgentAdapter],
        *,
        zmq_bind_addr: str = "tcp://127.0.0.1:5555",
        max_inflight_per_worker: int = 1,
        output_sink: Optional[InMemoryBroadcastSink] = None,
        task_timeout_sec: Optional[float] = 300.0,
    ) -> None:
        self.llm_agent = llm_agent(self)
        self.sink = output_sink or InMemoryBroadcastSink()
        self.task_timeout_sec = task_timeout_sec

        self._in_q: "queue.PriorityQueue[Tuple[int, float, InputEvent]]" = (
            queue.PriorityQueue()
        )
        self._stop = threading.Event()
        self._th = threading.Thread(target=self._loop, daemon=True)

        # worker inflight制御（worker名ごと）
        self.max_inflight_per_worker = max_inflight_per_worker
        self._inflight_lock = threading.Lock()
        self._inflight: Dict[str, int] = {}
        self._inflight_tasks: Dict[str, Dict[str, Any]] = {}

        # ZMQ bus (ROUTER)
        self.bus = ControllerBus(zmq_bind_addr, on_result=self._on_task_result)

        # 最低限の状態
        self.state: Dict[str, Any] = {"turn_seq": 0, "last_turn_id": None}

    # ---------- lifecycle ----------
    def start(self) -> None:
        self.bus.start()
        if not self._th.is_alive():
            self._th.start()

    def stop(self) -> None:
        self._stop.set()
        self.bus.stop()
        try:
            self._in_q.put_nowait(
                (
                    9999,
                    now_ts(),
                    InputEvent(
                        new_id(), now_ts(), InputEventType.SystemTick, {}, None, 9999
                    ),
                )
            )
        except Exception:
            pass

    # ---------- output subscription ----------
    def subscribe(self, max_queue: int = 1000):
        return self.sink.subscribe(max_queue=max_queue)

    def unsubscribe(self, sid: str) -> None:
        self.sink.unsubscribe(sid)

    # ---------- user input ----------
    def submit_user_text(self, text: str) -> str:
        turn_id = self._new_turn_id()
        ev = InputEvent(
            event_id=new_id(),
            ts=now_ts(),
            type=InputEventType.User,
            payload={"text": text},
            turn_id=turn_id,
            priority=10,
        )
        self._enqueue(ev)
        return turn_id

    # ---------- worker dispatch (toolから呼ぶ想定) ----------
    def dispatch_task(
        self, *, worker: str, kind: str, turn_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        workerへタスクを投げる。
        max_inflight_per_worker を超える場合は拒否。
        """
        with self._inflight_lock:
            cur = self._inflight.get(worker, 0)
            if cur >= self.max_inflight_per_worker:
                self._emit(
                    OutputEventType.Notice,
                    {
                        "kind": "dispatch_rejected",
                        "worker": worker,
                        "reason": "inflight_limit",
                    },
                    turn_id,
                )
                return {"accepted": False, "reason": "inflight_limit", "worker": worker}
            self._inflight[worker] = cur + 1

        task_id = f"task_{new_id()}"
        task = TaskSpec(
            task_id=task_id, worker=worker, kind=kind, turn_id=turn_id, payload=payload
        )
        if self.task_timeout_sec and self.task_timeout_sec > 0:
            deadline = now_ts() + self.task_timeout_sec
            with self._inflight_lock:
                self._inflight_tasks[task_id] = {
                    "worker": worker,
                    "turn_id": turn_id,
                    "kind": kind,
                    "deadline": deadline,
                }
        self.bus.send_task(task)
        self._emit(
            OutputEventType.Notice,
            {
                "kind": "dispatch_sent",
                "worker": worker,
                "task_id": task_id,
                "task_kind": kind,
            },
            turn_id,
        )
        return {"accepted": True, "task_id": task_id, "worker": worker}

    # ---------- internal ----------
    def _new_turn_id(self) -> str:
        self.state["turn_seq"] += 1
        tid = f"turn_{self.state['turn_seq']:06d}"
        self.state["last_turn_id"] = tid
        return tid

    def _enqueue(self, ev: InputEvent) -> None:
        self._in_q.put((ev.priority, ev.ts, ev))

    def _emit(
        self,
        type_: OutputEventTypeLiteral,
        payload: Dict[str, Any],
        turn_id: Optional[str],
    ) -> None:
        out = OutputEvent(
            event_id=new_id(), ts=now_ts(), type=type_, payload=payload, turn_id=turn_id
        )
        self.sink.emit(out)

    def _on_task_result(self, r: TaskResult) -> None:
        self._apply_task_result(r, worker=r.worker)

    def _apply_task_result(self, r: TaskResult, worker: str) -> None:
        # inflight減算
        with self._inflight_lock:
            should_decrement = True
            if self.task_timeout_sec and self.task_timeout_sec > 0:
                if r.task_id in self._inflight_tasks:
                    del self._inflight_tasks[r.task_id]
                else:
                    should_decrement = False
            if should_decrement:
                self._inflight[worker] = max(0, self._inflight.get(worker, 1) - 1)

        worker_payload = self._normalize_worker_payload(r.payload)
        error_payload = None
        if r.status == "FAILED":
            err = worker_payload.get("error")
            if isinstance(err, dict) and err.get("message"):
                error_payload = err
            elif isinstance(err, str) and err:
                error_payload = {"code": "worker_error", "message": err}
            else:
                error_payload = {"code": "worker_error", "message": "worker failed"}

        payload = self._build_task_payload(
            subagent=r.kind,
            task_id=r.task_id,
            worker=worker,
            payload=worker_payload,
            error=error_payload,
        )
        if r.status == "DONE":
            ev = InputEvent(
                event_id=new_id(),
                ts=now_ts(),
                type=InputEventType.SubDone,
                payload=payload,
                turn_id=r.turn_id,
                priority=20,
            )
            self._enqueue(ev)
        elif r.status == "FAILED":
            ev = InputEvent(
                event_id=new_id(),
                ts=now_ts(),
                type=InputEventType.SubFailed,
                payload=payload,
                turn_id=r.turn_id,
                priority=20,
            )
            self._enqueue(ev)
        elif r.status == "PROGRESS":
            ev = InputEvent(
                event_id=new_id(),
                ts=now_ts(),
                type=InputEventType.SubProgress,
                payload=payload,
                turn_id=r.turn_id,
                priority=30,
            )
            self._enqueue(ev)

    def _normalize_worker_payload(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        return {"value": payload}

    def _build_task_payload(
        self,
        *,
        subagent: str,
        task_id: str,
        worker: str,
        payload: Optional[Dict[str, Any]],
        error: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "schema_version": 1,
            "subagent": subagent,
            "task_id": task_id,
            "worker": worker,
        }
        if payload:
            out["payload"] = payload
        if error:
            out["error"] = error
        return out

    def _expire_inflight(self, now: float) -> None:
        if not self.task_timeout_sec or self.task_timeout_sec <= 0:
            return

        expired: List[Dict[str, Any]] = []
        with self._inflight_lock:
            for task_id, info in list(self._inflight_tasks.items()):
                if info["deadline"] <= now:
                    expired.append({"task_id": task_id, **info})
                    del self._inflight_tasks[task_id]
                    worker = info["worker"]
                    self._inflight[worker] = max(0, self._inflight.get(worker, 1) - 1)

        for info in expired:
            payload = self._build_task_payload(
                subagent=info["kind"],
                task_id=info["task_id"],
                worker=info["worker"],
                payload=None,
                error={
                    "code": "timeout",
                    "message": "task timeout",
                },
            )
            ev = InputEvent(
                event_id=new_id(),
                ts=now_ts(),
                type=InputEventType.SubFailed,
                payload=payload,
                turn_id=info["turn_id"],
                priority=20,
            )
            self._enqueue(ev)

    def _loop(self) -> None:
        self._emit(OutputEventType.Status, {"state": "idle"}, None)

        while not self._stop.is_set():
            self._expire_inflight(now_ts())
            try:
                _prio, _ts, ev = self._in_q.get(timeout=0.2)
            except queue.Empty:
                continue

            if self._stop.is_set():
                break

            self._emit(
                OutputEventType.Status,
                {"state": "processing", "input_type": ev.type},
                ev.turn_id,
            )

            try:
                deltas, final_text, meta = self.llm_agent.handle_event(ev, self.state)

                for c in deltas:
                    if c:
                        self._emit(
                            OutputEventType.AssistantDelta, {"text": c}, ev.turn_id
                        )

                if final_text:
                    self._emit(
                        OutputEventType.AssistantFinal,
                        {"text": final_text, "meta": meta},
                        ev.turn_id,
                    )

            except Exception as e:
                self._emit(
                    OutputEventType.Error,
                    {"message": f"{type(e).__name__}: {e}"},
                    ev.turn_id,
                )

            self._emit(OutputEventType.Status, {"state": "idle"}, ev.turn_id)
