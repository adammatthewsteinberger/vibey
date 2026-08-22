# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""BUILD decomposition: the work-item graph and its two structural rules
(M6 task 6.1), per phase-protocols.md section 2.1.

`build.decompose` turns an accepted spec into a dependency-ordered work-item
graph. Two rules are checked structurally, not left to the decomposer's
judgment:

1. Every acceptance criterion maps to >= 1 work item. An unmapped criterion
   is a decomposition bug and fails the job.
2. The walking skeleton has no dependencies. It goes first, alone, and must
   go green before anything else starts.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from vibey.domain.effort import Effort


@dataclass(frozen=True, slots=True)
class VerificationSpec:
    """Exactly how a work item's completion will be checked."""

    commands: tuple[str, ...]
    criteria_checked: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkItem:
    item_id: str
    title: str
    acceptance_ids: tuple[str, ...]
    depends_on: tuple[str, ...]
    est_effort: Effort
    files_touched_hint: tuple[str, ...]
    verification: VerificationSpec


def validate_decomposition(
    items: Sequence[WorkItem],
    *,
    criteria_ids: Sequence[str],
    walking_skeleton_item_id: str,
) -> tuple[str, ...]:
    """Returns violations; empty means the decomposition can enter BUILD."""
    violations: list[str] = []

    ids = [item.item_id for item in items]
    duplicates = {item_id for item_id in ids if ids.count(item_id) > 1}
    if duplicates:
        violations.append(f"duplicate item_id(s): {', '.join(sorted(duplicates))}")

    known_ids = set(ids)
    for item in items:
        for dep in item.depends_on:
            if dep not in known_ids:
                violations.append(f"item {item.item_id!r} depends on unknown item {dep!r}")

    mapped = {acceptance_id for item in items for acceptance_id in item.acceptance_ids}
    unmapped = [criterion_id for criterion_id in criteria_ids if criterion_id not in mapped]
    if unmapped:
        violations.append(
            f"{len(unmapped)} acceptance criterion/criteria unmapped: {', '.join(unmapped)}"
        )

    skeleton = next((item for item in items if item.item_id == walking_skeleton_item_id), None)
    if skeleton is None:
        violations.append(f"walking skeleton item {walking_skeleton_item_id!r} not found")
    elif skeleton.depends_on:
        violations.append(
            f"walking skeleton item {walking_skeleton_item_id!r} must have no dependencies, "
            f"has {len(skeleton.depends_on)}"
        )

    return tuple(violations)


_DEFAULT_BUILD_PARALLELISM = 4


def build_parallelism(
    *,
    config_parallelism: int | None,
    eligible_items: int,
    cpu_count: int,
) -> int:
    """Return the concurrency bound for BUILD: ``min(config, eligible×2, cpu)``.

    ``config_parallelism`` comes from ``phases.build.parallelism`` in vibey.toml
    (None means use the default of 4).  ``eligible_items`` and ``cpu_count`` are
    supplied by the caller — the domain does not read them from the environment.
    """
    cfg = config_parallelism if config_parallelism is not None else _DEFAULT_BUILD_PARALLELISM
    return min(cfg, eligible_items * 2, cpu_count)
