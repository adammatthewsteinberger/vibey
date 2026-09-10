# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Completion verdicts from a fenced JSON block, a marker, or an empty turn.

Cursor has no vendor structured-output schema, so completion is a four-tier
convention: parse the last ``cursorloop-verdict`` fence, fall back to a
substring marker, soft-fail empty zero-token turns, then plain Continue.
Plan reconciliation (``reconcile``) can still downgrade Done when unchecked
checkboxes remain.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from cursorloop.domain.plan import WorkPlan

DEFAULT_DONE_MARKER = "CURSORLOOP_TASK_FULLY_COMPLETE"
VERDICT_FENCE = "cursorloop-verdict"

_VERDICT_BLOCK_RE = re.compile(
    rf"```{re.escape(VERDICT_FENCE)}\s*\n(.*?)```",
    re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class Done:
    summary: str = ""


@dataclass(frozen=True, slots=True)
class Continue:
    remaining_work: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Blocked:
    reason: str


CompletionVerdict = Done | Continue | Blocked


@dataclass(frozen=True, slots=True)
class StructuredVerdict:
    """Mirrors the JSON object the autonomy preamble asks the model to emit:

    ``{"complete": bool, "remaining_work": [str], "blocked_on": str|null, "summary": str}``

    ``blocked_on`` is terminal (evaluate → Blocked). It is only for true
    external/human blockers; waitable self-started work belongs in
    ``remaining_work`` with ``blocked_on`` left null.
    """

    complete: bool
    remaining_work: tuple[str, ...] = ()
    blocked_on: str | None = None
    summary: str = ""


def parse_verdict_block(text: str) -> StructuredVerdict | None:
    """Return the last well-formed fenced verdict, or ``None`` if absent.

    Malformed JSON, a missing ``complete`` key, or a wrong type is absent —
    never fatal. The last fence wins so a quoted instruction is not the verdict.
    """
    matches = _VERDICT_BLOCK_RE.findall(text)
    if not matches:
        return None
    try:
        data = json.loads(matches[-1])
    except json.JSONDecodeError:
        return None
    return _structured_from_payload(data)


def _structured_from_payload(data: object) -> StructuredVerdict | None:
    if not isinstance(data, dict):
        return None
    complete = data.get("complete")
    if not isinstance(complete, bool):
        return None
    remaining_raw = data.get("remaining_work", [])
    if not isinstance(remaining_raw, list) or not all(
        isinstance(item, str) for item in remaining_raw
    ):
        return None
    blocked_on = data.get("blocked_on")
    if blocked_on is not None and not isinstance(blocked_on, str):
        return None
    summary = data.get("summary", "")
    if not isinstance(summary, str):
        return None
    return StructuredVerdict(
        complete=complete,
        remaining_work=tuple(remaining_raw),
        blocked_on=blocked_on,
        summary=summary,
    )


def evaluate(
    *,
    structured: StructuredVerdict | None,
    output_text: str,
    done_marker: str = DEFAULT_DONE_MARKER,
    tokens: int = 0,
    empty_turn_streak: int = 0,
    empty_turn_limit: int = 3,
) -> CompletionVerdict:
    """Decide what a single turn's outcome means for the overall task.

    Precedence: structured (``blocked_on`` outranks ``complete`` → Continue),
    then the marker, then the empty-turn soft-fail, then plain Continue.
    """
    if structured is not None:
        if structured.blocked_on:
            return Blocked(reason=structured.blocked_on)
        if structured.complete:
            return Done(summary=structured.summary)
        return Continue(remaining_work=structured.remaining_work)

    if done_marker in output_text:
        return Done()

    if not output_text.strip() and tokens <= 0:
        if empty_turn_streak + 1 >= empty_turn_limit:
            return Blocked(reason="repeated empty model responses")
        return Continue(
            remaining_work=("Waiting for a non-empty model response",),
        )

    return Continue()


def reconcile(verdict: CompletionVerdict, plan: WorkPlan) -> CompletionVerdict:
    """Downgrade ``Done`` to ``Continue`` when unchecked plan items remain.

    Never the reverse: a Continue or Blocked verdict is left untouched even
    if every checkbox is already marked done.
    """
    if not isinstance(verdict, Done):
        return verdict
    remaining = tuple(item.text for item in plan.remaining_items)
    if remaining:
        return Continue(remaining_work=remaining)
    return verdict
