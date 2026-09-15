# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Configuration: CLI/env/file/defaults. Only ``CURSORLOOP_*`` and ``CURSOR_API_KEY``.

Vendor-foreign env prefixes are ignored. Config files use stdlib ``tomllib``.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

_ENV_PREFIX = "CURSORLOOP_"
_API_KEY_ENV = "CURSOR_API_KEY"
_DEFAULT_BILLING_TERMS: tuple[str, ...] = (
    "out_of_credits",
    "credits_required",
    "insufficient_credits",
    "spend_limit",
    "hard_limit",
    "quota_exceeded",
    "plan_limit",
    "payment_required",
    "upgrade_required",
    "add_credits",
    "subscription_expired",
)


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    api_key: str | None = None
    max_wait_seconds: float | None = None
    max_turns: int | None = None
    max_dollars: float | None = None
    turn_timeout_seconds: float | None = None
    stall_timeout_seconds: float | None = None
    log_level: str = "INFO"
    log_file: str | None = None
    model: str | None = None
    billing_terms: tuple[str, ...] = field(default_factory=lambda: _DEFAULT_BILLING_TERMS)
    rate_limit_terms: tuple[str, ...] = ()
    managed_hooks: bool = True
    observed_env: frozenset[str] = field(default_factory=frozenset)


def _split_terms(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _from_env() -> tuple[dict[str, Any], frozenset[str]]:
    overrides: dict[str, Any] = {}
    observed: set[str] = set()
    for key, value in os.environ.items():
        if key == _API_KEY_ENV:
            overrides["api_key"] = value
            observed.add(key)
            continue
        if not key.startswith(_ENV_PREFIX):
            continue
        observed.add(key)
        suffix = key[len(_ENV_PREFIX) :].lower()
        if suffix == "max_wait":
            overrides["max_wait_seconds"] = float(value)
        elif suffix == "max_turns":
            overrides["max_turns"] = int(value)
        elif suffix == "max_dollars":
            overrides["max_dollars"] = float(value)
        elif suffix == "turn_timeout":
            overrides["turn_timeout_seconds"] = float(value)
        elif suffix == "stall_timeout":
            overrides["stall_timeout_seconds"] = float(value)
        elif suffix == "log_level":
            overrides["log_level"] = value
        elif suffix == "log_file":
            overrides["log_file"] = value
        elif suffix == "model":
            overrides["model"] = value
        elif suffix == "billing_lexicon":
            overrides["billing_terms"] = _split_terms(value)
        elif suffix == "rate_limit_lexicon":
            overrides["rate_limit_terms"] = _split_terms(value)
        elif suffix == "managed_hooks":
            overrides["managed_hooks"] = value.strip().lower() not in {
                "0",
                "false",
                "no",
                "off",
            }
    return overrides, frozenset(observed)


def _from_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    section = data.get("cursorloop", data)
    if not isinstance(section, dict):
        return {}
    out: dict[str, Any] = {}
    mapping = {
        "api_key": "api_key",
        "max_wait": "max_wait_seconds",
        "max_wait_seconds": "max_wait_seconds",
        "max_turns": "max_turns",
        "max_dollars": "max_dollars",
        "turn_timeout": "turn_timeout_seconds",
        "stall_timeout": "stall_timeout_seconds",
        "log_level": "log_level",
        "log_file": "log_file",
        "model": "model",
        "billing_lexicon": "billing_terms",
        "managed_hooks": "managed_hooks",
    }
    for src, dest in mapping.items():
        if src not in section:
            continue
        value = section[src]
        if dest in {"billing_terms"} and isinstance(value, str):
            out[dest] = _split_terms(value)
        elif dest in {"billing_terms"} and isinstance(value, list):
            out[dest] = tuple(str(item) for item in value)
        else:
            out[dest] = value
    return out


def load_config(*, config_file: Path | None = None) -> RunnerConfig:
    """Load config: env > optional TOML file > defaults. Tracks observed env keys."""
    file_overrides = _from_file(config_file) if config_file is not None else {}
    env_overrides, observed = _from_env()
    merged: dict[str, Any] = {**file_overrides, **env_overrides, "observed_env": observed}
    known = {f.name for f in fields(RunnerConfig)}
    return RunnerConfig(**{k: v for k, v in merged.items() if k in known})
