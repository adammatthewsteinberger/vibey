# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Parsing and validation of the vibey.toml schema.

Pure: this module accepts already-loaded TOML text or a dict and returns
either a validated ``VibeyConfig`` or a list of ``ConfigError``s. It never
touches the filesystem — reading the file is an infrastructure concern.
"""

import tomllib
from dataclasses import dataclass, field
from typing import Any

from vibey.domain.errors import VibeyError

VALID_ISOLATION_LEVELS = ("worktree", "container", "vm")
VALID_EFFORTS = ("trivial", "low", "standard", "high", "max")
KNOWN_ENGINES = ("claudeloop", "codexloop", "cursorloop", "agyloop")


class ConfigError(VibeyError):
    """Raised when vibey.toml fails validation."""

    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    name: str
    repo: str = "."
    max_cycles: int = 10
    strict_loopback: bool = False


@dataclass(frozen=True, slots=True)
class IsolationConfig:
    level: str = "worktree"
    allow_push: bool = False
    egress: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BudgetConfig:
    max_dollars_per_cycle: float | None = None
    max_dollars_total: float | None = None
    max_turns_per_item: int | None = None


@dataclass(frozen=True, slots=True)
class EnginesConfig:
    enabled: tuple[str, ...] = KNOWN_ENGINES
    weights: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PhaseConfig:
    effort: str = "standard"
    engines: tuple[str, ...] | None = None
    parallelism: int | None = None


@dataclass(frozen=True, slots=True)
class PhasesConfig:
    design: PhaseConfig = field(default_factory=lambda: PhaseConfig(effort="high"))
    build: PhaseConfig = field(default_factory=lambda: PhaseConfig(effort="low"))
    review: PhaseConfig = field(default_factory=lambda: PhaseConfig(effort="high"))


@dataclass(frozen=True, slots=True)
class ProvisionConfig:
    plugins: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DeployConfig:
    enabled: bool = False
    target: str = "azure"
    iac: str = "bicep"


@dataclass(frozen=True, slots=True)
class VibeyConfig:
    project: ProjectConfig
    isolation: IsolationConfig = field(default_factory=IsolationConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    engines: EnginesConfig = field(default_factory=EnginesConfig)
    phases: PhasesConfig = field(default_factory=PhasesConfig)
    provision: ProvisionConfig = field(default_factory=ProvisionConfig)
    deploy: DeployConfig = field(default_factory=DeployConfig)


def parse_toml_string(text: str) -> dict[str, Any]:
    return tomllib.loads(text)


def _require(table: dict[str, Any], key: str, path: str, type_: type) -> Any:
    if key not in table:
        raise ConfigError(path, f"missing required field {key!r}")
    value = table[key]
    if not isinstance(value, type_):
        raise ConfigError(path, f"{key!r} must be a {type_.__name__}, got {type(value).__name__}")
    return value


def _optional(table: dict[str, Any], key: str, path: str, type_: type, default: Any) -> Any:
    if key not in table:
        return default
    value = table[key]
    if not isinstance(value, type_):
        raise ConfigError(path, f"{key!r} must be a {type_.__name__}, got {type(value).__name__}")
    return value


def _parse_project(data: dict[str, Any]) -> ProjectConfig:
    table = _optional(data, "project", "project", dict, {})
    if "name" not in table:
        raise ConfigError("project.name", "missing required field 'name'")
    return ProjectConfig(
        name=_require(table, "name", "project.name", str),
        repo=_optional(table, "repo", "project.repo", str, "."),
        max_cycles=_optional(table, "max_cycles", "project.max_cycles", int, 10),
        strict_loopback=_optional(table, "strict_loopback", "project.strict_loopback", bool, False),
    )


def _parse_isolation(data: dict[str, Any]) -> IsolationConfig:
    table = _optional(data, "isolation", "isolation", dict, {})
    level = _optional(table, "level", "isolation.level", str, "worktree")
    if level not in VALID_ISOLATION_LEVELS:
        raise ConfigError(
            "isolation.level", f"must be one of {VALID_ISOLATION_LEVELS}, got {level!r}"
        )
    egress = _optional(table, "egress", "isolation.egress", list, [])
    return IsolationConfig(
        level=level,
        allow_push=_optional(table, "allow_push", "isolation.allow_push", bool, False),
        egress=tuple(egress),
    )


def _parse_budget(data: dict[str, Any]) -> BudgetConfig:
    table = _optional(data, "budget", "budget", dict, {})
    return BudgetConfig(
        max_dollars_per_cycle=table.get("max_dollars_per_cycle"),
        max_dollars_total=table.get("max_dollars_total"),
        max_turns_per_item=table.get("max_turns_per_item"),
    )


def _parse_engines(data: dict[str, Any]) -> EnginesConfig:
    table = _optional(data, "engines", "engines", dict, {})
    enabled = tuple(_optional(table, "enabled", "engines.enabled", list, list(KNOWN_ENGINES)))
    for engine in enabled:
        if engine not in KNOWN_ENGINES:
            raise ConfigError("engines.enabled", f"unknown engine {engine!r}")
    weights = _optional(table, "weights", "engines.weights", dict, {})
    for engine in weights:
        if engine not in KNOWN_ENGINES:
            raise ConfigError("engines.weights", f"unknown engine {engine!r}")
    return EnginesConfig(enabled=enabled, weights=dict(weights))


def _parse_phase(table: dict[str, Any], path: str, default_effort: str) -> PhaseConfig:
    effort = _optional(table, "effort", f"{path}.effort", str, default_effort)
    if effort not in VALID_EFFORTS:
        raise ConfigError(f"{path}.effort", f"must be one of {VALID_EFFORTS}, got {effort!r}")
    engines_raw = table.get("engines")
    engines = tuple(engines_raw) if engines_raw is not None else None
    parallelism = table.get("parallelism")
    return PhaseConfig(effort=effort, engines=engines, parallelism=parallelism)


def _parse_phases(data: dict[str, Any]) -> PhasesConfig:
    table = _optional(data, "phases", "phases", dict, {})
    design = _optional(table, "design", "phases.design", dict, {})
    build = _optional(table, "build", "phases.build", dict, {})
    review = _optional(table, "review", "phases.review", dict, {})
    return PhasesConfig(
        design=_parse_phase(design, "phases.design", "high"),
        build=_parse_phase(build, "phases.build", "low"),
        review=_parse_phase(review, "phases.review", "high"),
    )


def _parse_provision(data: dict[str, Any]) -> ProvisionConfig:
    table = _optional(data, "provision", "provision", dict, {})
    plugins = tuple(_optional(table, "plugins", "provision.plugins", list, []))
    return ProvisionConfig(plugins=plugins)


def _parse_deploy(data: dict[str, Any]) -> DeployConfig:
    table = _optional(data, "deploy", "deploy", dict, {})
    return DeployConfig(
        enabled=_optional(table, "enabled", "deploy.enabled", bool, False),
        target=_optional(table, "target", "deploy.target", str, "azure"),
        iac=_optional(table, "iac", "deploy.iac", str, "bicep"),
    )


def parse_config(data: dict[str, Any]) -> VibeyConfig:
    """Validate an already-parsed TOML dict and build a VibeyConfig.

    Raises ConfigError on the first violation found.
    """
    return VibeyConfig(
        project=_parse_project(data),
        isolation=_parse_isolation(data),
        budget=_parse_budget(data),
        engines=_parse_engines(data),
        phases=_parse_phases(data),
        provision=_parse_provision(data),
        deploy=_parse_deploy(data),
    )


def load_config_from_string(text: str) -> VibeyConfig:
    return parse_config(parse_toml_string(text))
