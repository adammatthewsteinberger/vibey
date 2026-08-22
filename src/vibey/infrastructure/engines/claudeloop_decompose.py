# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Live ClaudeLoop implementation of the WorkPlanProducer port.

Modeled on ClaudeLoopDesignProvider: model text crosses this boundary only
through strict JSON decoders, and a structurally invalid decomposition
fails fast here (with the violation named) rather than surviving to
confuse the handler -- BuildDecomposeHandler re-validates independently,
but a producer that ships known-bad output would waste a whole job attempt
learning what this module can already see.
"""

import json
import re
from pathlib import Path
from uuid import uuid4

from vibey.application.dto import RunSpec
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.domain.plan import VerificationSpec, WorkItem, validate_decomposition
from vibey.domain.spec import DesignSpec
from vibey.infrastructure.engines.claudeloop_design import _object
from vibey.infrastructure.interfaces import BoundedClaudeLoop


class ClaudeLoopWorkPlanProducer:
    def __init__(self, *, process: BoundedClaudeLoop, worktree_path: Path) -> None:
        self._process = process
        self._worktree_path = worktree_path

    async def decompose(self, spec: DesignSpec) -> tuple[WorkItem, ...]:
        prompt = (
            "Decompose this accepted design spec into a dependency-ordered work-item graph. "
            "The FIRST item must be the walking skeleton, with no dependencies. Every "
            "acceptance criterion must appear in at least one item's acceptance_ids, and "
            "every item's verification.criteria_checked must be non-empty. Items must be "
            "ordered so every dependency precedes its dependents. Every item_id must be "
            'lowercase alphanumeric with hyphens (e.g. "ws", "cli-parsing") -- it '
            "becomes a git branch name. Items that will modify the same file MUST be "
            "chained via depends_on (they run in parallel branches otherwise and their "
            "merges conflict). Every verification command must be self-contained and "
            "pass in a clean checkout with nothing installed (no pip install, no "
            "network); prefer one pytest suite under tests/ shared by all items over "
            "inventing per-item test styles. Do not inspect files; "
            "answer immediately in this first turn. Return only JSON with shape "
            '{"items":[{"item_id":str,"title":str,"acceptance_ids":[str],'
            '"depends_on":[str],"est_effort":"trivial|low|standard|high|max",'
            '"verification":{"commands":[str],"criteria_checked":[str]}}]}.\n'
            f"Spec: {json.dumps(_spec_json(spec), default=str)}"
        )
        result = await self._process.run(
            RunSpec(
                run_id=uuid4(),
                worktree_path=self._worktree_path,
                prompt=prompt,
                effort=Effort.STANDARD,
                isolation=IsolationLevel.WORKTREE,
            )
        )
        data = _object(result.response)
        raw_items = data.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise ValueError("decomposition requires a non-empty items list")
        items = tuple(_item(entry) for entry in raw_items)

        # Caught live: the model returned ids like "WI-01" despite the
        # prompt, and every downstream consumer (branch names, worktrees)
        # requires the lowercase-hyphen shape -- so normalization must be
        # guaranteed here, not requested politely.
        seen: set[str] = set()
        for item in items:
            if item.item_id in seen:
                raise ValueError(
                    f"model produced an invalid decomposition: duplicate item id "
                    f"{item.item_id!r} after normalization"
                )
            seen.add(item.item_id)

        violations = validate_decomposition(
            items,
            criteria_ids=[criterion.criterion_id for criterion in spec.criteria],
            walking_skeleton_item_id=items[0].item_id,
        )
        if violations:
            raise ValueError(f"model produced an invalid decomposition: {'; '.join(violations)}")
        return items


def _slug(raw: object) -> str:
    """Deterministic projection onto domain/worktree.py's id shape:
    lowercase alphanumeric and hyphens, starting alphanumeric, <= 64."""
    text = re.sub(r"[^a-z0-9-]+", "-", str(raw).lower()).strip("-")[:64]
    if not text:
        raise ValueError(f"decomposition item id {raw!r} normalizes to nothing")
    return text


def _item(entry: object) -> WorkItem:
    if not isinstance(entry, dict):
        raise ValueError("every decomposition item must be an object")
    try:
        verification = entry.get("verification", {})
        if not isinstance(verification, dict):
            raise ValueError("verification must be an object")
        return WorkItem(
            item_id=_slug(entry["item_id"]),
            title=str(entry["title"]),
            acceptance_ids=tuple(str(a) for a in _str_list(entry.get("acceptance_ids", []))),
            depends_on=tuple(_slug(d) for d in _str_list(entry.get("depends_on", []))),
            est_effort=Effort[str(entry.get("est_effort", "low")).upper()],
            files_touched_hint=(),
            verification=VerificationSpec(
                commands=tuple(str(c) for c in _str_list(verification.get("commands", []))),
                criteria_checked=tuple(
                    str(c) for c in _str_list(verification.get("criteria_checked", []))
                ),
            ),
        )
    except KeyError as exc:
        raise ValueError(f"decomposition item is missing {exc.args[0]}") from exc


def _str_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("expected a list")
    return value


def _spec_json(spec: DesignSpec) -> dict[str, object]:
    return {
        "objective": spec.objective,
        "constraints": [{"text": c.text, "kind": c.kind.value} for c in spec.constraints],
        "non_goals": list(spec.non_goals),
        "criteria": [
            {
                "criterion_id": c.criterion_id,
                "given": c.given,
                "when": c.when,
                "then": c.then,
                "fit": c.fit,
            }
            for c in spec.criteria
        ],
        "walking_skeleton": spec.walking_skeleton,
    }
