# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Configuration options and data structures for hardened container isolation (Milestone 9)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ContainerConfig:
    image: str
    worktree_path: Path
    container_worktree_path: str = "/workspace"
    memory_limit: str = "4g"
    cpu_limit: str = "2.0"
    network_mode: str = "none"
    read_only_root: bool = True
    drop_capabilities: Sequence[str] = field(default_factory=lambda: ("ALL",))
    tmpfs_mounts: Sequence[str] = field(
        default_factory=lambda: ("/tmp:rw,noexec,nosuid,size=512m",)  # nosec B108
    )

    security_options: Sequence[str] = field(default_factory=lambda: ("no-new-privileges:true",))
    env_vars: Mapping[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ContainerResult:
    exit_code: int
    stdout: str
    stderr: str
