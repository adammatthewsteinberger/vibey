"""Materialize a runner's positional Markdown plan from a ``RunSpec``."""

import os
from pathlib import Path

from vibey.application.dto import RunSpec


def plan_path(spec: RunSpec) -> Path:
    return spec.worktree_path / ".vibey" / "plans" / f"{spec.run_id}.md"


def write_plan(spec: RunSpec) -> Path:
    """Atomically replace the plan consumed by the concrete runner argv."""
    destination = plan_path(spec)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".md.tmp")
    temporary.write_text(spec.prompt)
    os.replace(temporary, destination)
    return destination
