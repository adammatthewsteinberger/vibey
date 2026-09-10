# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Configuration precedence: flags > env > project toml > user toml > defaults."""

from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from datetime import timedelta
from pathlib import Path
from typing import Any

from codexloop.domain.errors import ConfigurationError

_ENV_PREFIX = "CODEXLOOP_"
_DURATION = re.compile(
    r"^(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)s)?$"
)


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    """Runtime knobs. ``model=None`` leaves model selection to the Codex CLI."""

    model: str | None = None
    max_turns: int = 100
    json_logs: bool = False
    max_wait: timedelta = timedelta(hours=24)
    add_dirs: tuple[str, ...] = ()
    network_access: bool = False
    log_level: str = "INFO"
    log_file: str | None = None
    notify_command: str | None = None


_KNOWN = {f.name for f in fields(RunnerConfig)}


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    raise ConfigurationError(f"invalid bool {value!r}")


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        raise ConfigurationError(f"invalid int {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value.strip())
    raise ConfigurationError(f"invalid int {value!r}")


def _as_duration(value: object) -> timedelta:
    if isinstance(value, timedelta):
        return value
    if isinstance(value, bool):
        raise ConfigurationError(f"invalid duration {value!r}")
    if isinstance(value, int | float):
        return timedelta(seconds=float(value))
    if isinstance(value, str):
        text = value.strip()
        try:
            return timedelta(seconds=float(text))
        except ValueError:
            pass
        matched = _DURATION.fullmatch(text)
        if matched is not None and any(matched.groups()):
            days = int(matched.group("days") or 0)
            hours = int(matched.group("hours") or 0)
            minutes = int(matched.group("minutes") or 0)
            seconds = float(matched.group("seconds") or 0)
            return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    raise ConfigurationError(f"invalid duration {value!r}")


def _as_str_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        return tuple(part for part in parts if part)
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value)
    raise ConfigurationError(f"invalid list {value!r}")


def _coerce_field(name: str, value: object) -> Any:
    if name in {"model", "log_level"}:
        return str(value)
    if name == "max_turns":
        return _as_int(value)
    if name in {"json_logs", "network_access"}:
        return _as_bool(value)
    if name == "max_wait":
        return _as_duration(value)
    if name == "add_dirs":
        return _as_str_tuple(value)
    if name in {"log_file", "notify_command"}:
        return None if value is None else str(value)
    return value


def _from_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return {key: value for key, value in data.items() if key in _KNOWN}


def _from_env(environ: Mapping[str, str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for name in _KNOWN:
        raw = environ.get(_ENV_PREFIX + name.upper())
        if raw is not None:
            overrides[name] = raw
    return overrides


def load_config(
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    flags: Mapping[str, object] | None = None,
) -> RunnerConfig:
    cwd = Path.cwd() if cwd is None else cwd
    home = Path.home() if home is None else home
    env = os.environ if environ is None else environ

    merged: dict[str, Any] = {}
    merged.update(_from_file(home / ".config" / "codexloop" / "codexloop.toml"))
    merged.update(_from_file(cwd / "codexloop.toml"))
    merged.update(_from_env(env))
    if flags:
        merged.update({key: value for key, value in flags.items() if value is not None})

    if not merged:
        return RunnerConfig()
    coerced: dict[str, Any] = {
        key: _coerce_field(key, value) for key, value in merged.items() if key in _KNOWN
    }
    return replace(RunnerConfig(), **coerced)
