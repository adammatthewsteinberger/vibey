# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Configuration precedence: CLI flags > environment variables > config file >
built-in defaults. See docs/getting-started/configuration.md for the full
settings table this backs."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):  # pragma: no cover - exactly one branch runs per interpreter
    import tomllib
else:  # pragma: no cover - exactly one branch runs per interpreter
    import tomli as tomllib

from claudeloop.domain.model_profile import (
    DEFAULT_MODEL_HIGH,
    DEFAULT_MODEL_LOW,
    DEFAULT_MODEL_MEDIUM,
    ModelAliases,
    ModelEffortProfile,
    resolve_profile,
)

_ENV_PREFIX = "CLAUDELOOP_"


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    max_turns: int | None = None
    max_dollars: float | None = None
    max_attempts: int | None = None
    max_wait_seconds: float | None = None
    credits_probe_interval_seconds: float = 120.0
    credits_probe_ceiling_seconds: float = 600.0
    window_probe_interval_seconds: float = 600.0
    reset_grace_seconds: float = 60.0
    done_marker: str | None = None
    log_level: str = "INFO"
    log_file: str | None = None
    log_chatter: str | None = None  # full|summary|off; None → derive from log_level
    retry_watchdog: bool = False
    model: str | None = None
    effort: str | None = None
    preset: str | None = None
    model_low: str = DEFAULT_MODEL_LOW
    model_medium: str = DEFAULT_MODEL_MEDIUM
    model_high: str = DEFAULT_MODEL_HIGH
    auto_model: bool = True
    stream_ui: bool = False
    include_partial_messages: bool | None = None
    # Claude Agent SDK JSON line buffer (bytes). Default applied in options.py
    # when None — raise this if tool results exceed 1MB (SDK default).
    max_buffer_size: int | None = None
    permission_mode: str = "bypass"
    tool_approval_timeout_seconds: float = 30.0
    web_search: bool = False
    deep_research: bool = False
    progress_wait_initial_seconds: float = 30.0
    progress_wait_factor: float = 2.0
    progress_wait_ceiling_seconds: float = 300.0

    def aliases(self) -> ModelAliases:
        return ModelAliases(
            low=self.model_low,
            medium=self.model_medium,
            high=self.model_high,
        )

    def resolved_profile(self) -> ModelEffortProfile:
        return resolve_profile(
            preset=self.preset,
            model=self.model,
            effort=self.effort,
            aliases=self.aliases(),
        )

    def effective_log_chatter(self) -> str:
        if self.log_chatter is not None and self.log_chatter.strip():
            mode = self.log_chatter.strip().lower()
            if mode not in {"full", "summary", "off"}:
                raise ValueError(
                    f"invalid log_chatter {self.log_chatter!r}; expected full|summary|off"
                )
            return mode
        if (self.log_level or "INFO").upper() == "DEBUG":
            return "full"
        return "summary"

    def effective_partial_messages(self) -> bool:
        if self.include_partial_messages is not None:
            return self.include_partial_messages
        return self.stream_ui or self.effective_log_chatter() == "full"


def _from_env() -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for f in fields(RunnerConfig):
        env_name = _ENV_PREFIX + f.name.upper()
        raw = os.environ.get(env_name)
        if raw is None:
            continue
        overrides[f.name] = _coerce(raw, f.type)
    return overrides


def _from_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    known = {f.name for f in fields(RunnerConfig)}
    return {k: v for k, v in data.items() if k in known}


def _coerce(raw: str, type_hint: Any) -> Any:
    hint = str(type_hint)
    if "bool" in hint:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    if "float" in hint:
        return float(raw)
    if "int" in hint:
        return int(raw)
    return raw


def load_config(
    *,
    cwd: Path,
    home: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> RunnerConfig:
    config = RunnerConfig()

    file_overrides: dict[str, Any] = {}
    home_config = (home or Path.home()) / ".config" / "claudeloop" / "config.toml"
    file_overrides.update(_from_file(home_config))
    file_overrides.update(_from_file(cwd / "claudeloop.toml"))
    if file_overrides:
        config = replace(config, **file_overrides)

    env_overrides = _from_env()
    if env_overrides:
        config = replace(config, **env_overrides)

    if cli_overrides:
        cleaned = {k: v for k, v in cli_overrides.items() if v is not None}
        if cleaned:
            config = replace(config, **cleaned)

    return config
