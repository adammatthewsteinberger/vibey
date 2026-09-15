# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Configuration precedence: CLI flags > AGYLOOP_* env > agyloop.toml > defaults."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

from agyloop.domain.model_profile import (
    DEFAULT_MODEL_HIGH,
    DEFAULT_MODEL_LOW,
    DEFAULT_MODEL_MEDIUM,
    ModelAliases,
    ModelEffortProfile,
    resolve_profile,
)

_ENV_PREFIX = "AGYLOOP_"


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    max_turns: int | None = None
    max_dollars: float | None = None
    max_tokens: int | None = None
    max_wait_seconds: float | None = None
    log_level: str = "INFO"
    log_file: str | None = None
    model: str | None = None
    effort: str | None = None
    preset: str | None = None
    model_low: str = DEFAULT_MODEL_LOW
    model_medium: str = DEFAULT_MODEL_MEDIUM
    model_high: str = DEFAULT_MODEL_HIGH
    auto_model: bool = True
    gateway: str = "sdk"
    ramp: int = 0
    permission_mode: str = "autonomous"

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


def _from_env() -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for item in fields(RunnerConfig):
        env_name = _ENV_PREFIX + item.name.upper()
        raw = os.environ.get(env_name)
        if raw is None:
            continue
        overrides[item.name] = _coerce(raw, item.type)
    return overrides


def _from_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    known = {item.name for item in fields(RunnerConfig)}
    out: dict[str, Any] = {}
    for key, value in data.items():
        if key == "model" and isinstance(value, dict):
            for alias in ("low", "medium", "high"):
                if alias in value:
                    out[f"model_{alias}"] = value[alias]
            continue
        if key == "run" and isinstance(value, dict):
            out.update(
                {inner: inner_value for inner, inner_value in value.items() if inner in known}
            )
            continue
        if key in known:
            out[key] = value
    return out


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
    home_config = (home or Path.home()) / ".config" / "agyloop" / "config.toml"
    file_overrides.update(_from_file(home_config))
    file_overrides.update(_from_file(cwd / "agyloop.toml"))
    if file_overrides:
        config = replace(config, **file_overrides)
    env_overrides = _from_env()
    if env_overrides:
        config = replace(config, **env_overrides)
    if cli_overrides:
        cleaned = {key: value for key, value in cli_overrides.items() if value is not None}
        if cleaned:
            config = replace(config, **cleaned)
    return config
