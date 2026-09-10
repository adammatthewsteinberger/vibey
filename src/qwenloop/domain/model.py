# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure model, capacity, and run state."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

EXIT_CODE_WIND_DOWN = 75
DONE_MARKER = "QWENLOOP_TASK_FULLY_COMPLETE"


class Backend(StrEnum):
    AUTO = "auto"
    LLAMA_CPP = "llama.cpp"
    VLLM = "vllm"


class RunStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    WINDING_DOWN = "winding_down"
    COMPLETED = "completed"
    FAILED = "failed"


class CapacityKind(StrEnum):
    AVAILABLE = "available"
    LOCAL_BUSY = "local_busy"
    CONFIGURATION = "configuration"


@dataclass(frozen=True, slots=True)
class ModelProfile:
    name: str
    backend: Backend
    repository: str
    revision: str
    filename: str | None
    sha256: str | None
    size: int | None
    quantization: str
    context_window: int = 32_768


@dataclass(frozen=True, slots=True)
class ServerInfo:
    backend: Backend
    profile: str
    endpoint: str
    owned: bool
    healthy: bool
    pid: int | None = None
    token: str = ""


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class RepoItem:
    """One open issue or pull request, as reported by `gh`."""

    number: int
    title: str
    body: str


@dataclass(frozen=True, slots=True)
class ChatChunk:
    text: str = ""
    tool_call: dict[str, Any] | None = None
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(slots=True)
class RunState:
    run_id: str
    status: RunStatus = RunStatus.CREATED
    turns: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    transcript: list[ChatMessage] = field(default_factory=list)


def terminal_status(capacity: CapacityKind, completion_claimed: bool) -> RunStatus:
    """Capacity rejection always outranks a completion claim."""
    if capacity is not CapacityKind.AVAILABLE:
        return RunStatus.FAILED
    return RunStatus.COMPLETED if completion_claimed else RunStatus.RUNNING
