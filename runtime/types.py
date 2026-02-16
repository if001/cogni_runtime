from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Literal
from enum import StrEnum
import time
import uuid


def now_ts() -> float:
    return time.time()


def new_id() -> str:
    return uuid.uuid4().hex


class InputEventType(StrEnum):
    User = "user.message"
    SubDone = "sub.done"
    SubFailed = "sub.failed"
    SubProgress = "sub.progress"
    SystemTick = "system.tick"


class OutputEventType(StrEnum):
    AssistantDelta = "assistant.delta"
    AssistantFinal = "assistant.final"
    Status = "status"
    Notice = "notice"
    Error = "error"


InputEventLiteral = Literal[
    InputEventType.User,
    InputEventType.SubDone,
    InputEventType.SubFailed,
    InputEventType.SubProgress,
    InputEventType.SystemTick,
]


@dataclass(frozen=True)
class InputEvent:
    event_id: str
    ts: float
    type: InputEventLiteral
    payload: Dict[str, Any]
    turn_id: Optional[str] = None
    priority: int = 10


OutputEventTypeLiteral = Literal[
    OutputEventType.AssistantDelta,
    OutputEventType.AssistantFinal,
    OutputEventType.Status,
    OutputEventType.Notice,
    OutputEventType.Error,
]


@dataclass(frozen=True)
class OutputEvent:
    event_id: str
    ts: float
    type: OutputEventTypeLiteral
    payload: Dict[str, Any]
    turn_id: Optional[str] = None


@dataclass(frozen=True)
class TaskSpec:
    """
    controller -> worker に送る実行依頼
    """

    task_id: str
    kind: str  # "deep_research" など
    turn_id: str
    payload: Dict[str, Any]
    # どの worker に投げるか（ルーティング）
    worker: str  # 例: "worker1"


@dataclass(frozen=True)
class TaskResult:
    """
    worker -> controller の実行結果
    """

    task_id: str
    kind: str
    turn_id: str
    status: str  # "DONE" / "FAILED" / "PROGRESS"
    worker: str
    payload: Dict[str, Any] = field(default_factory=dict)
