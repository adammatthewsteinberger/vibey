# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure qwenloop configuration parsing."""

from dataclasses import dataclass
from typing import Any

from qwenloop.domain.model import Backend


@dataclass(frozen=True, slots=True)
class QwenConfig:
    backend: Backend = Backend.AUTO
    portable_profile: str = "qwen2.5-coder-14b-q5-k-m"
    nvidia_profile: str = "qwen2.5-coder-14b-bf16"
    idle_timeout_seconds: int = 900
    startup_timeout_seconds: int = 180
    context_window: int = 32_768
    max_turns: int = 40


def parse_config(data: dict[str, Any]) -> QwenConfig:
    defaults = QwenConfig()
    backend = Backend(str(data.get("backend", "auto")))
    config = QwenConfig(
        backend=backend,
        portable_profile=str(data.get("portable_profile", defaults.portable_profile)),
        nvidia_profile=str(data.get("nvidia_profile", defaults.nvidia_profile)),
        idle_timeout_seconds=int(data.get("idle_timeout_seconds", 900)),
        startup_timeout_seconds=int(data.get("startup_timeout_seconds", 180)),
        context_window=int(data.get("context_window", 32_768)),
        max_turns=int(data.get("max_turns", 40)),
    )
    if config.idle_timeout_seconds < 0:
        raise ValueError("idle_timeout_seconds must be non-negative")
    if config.startup_timeout_seconds <= 0 or config.context_window <= 0 or config.max_turns <= 0:
        raise ValueError("timeouts, context_window, and max_turns must be positive")
    return config
