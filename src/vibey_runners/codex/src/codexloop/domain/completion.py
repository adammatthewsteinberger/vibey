# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Three-layer completion evaluation: structured output → marker → continue."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import assert_never

from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    CapacityState,
    QuotaExhausted,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
)
from codexloop.domain.signals import TurnSignals

DEFAULT_DONE_MARKER = "CODEXLOOP_TASK_FULLY_COMPLETE"


@dataclass(frozen=True, slots=True)
class Done:
    pass


@dataclass(frozen=True, slots=True)
class Continue:
    remaining: list[str]


@dataclass(frozen=True, slots=True)
class Blocked:
    reason: str


CompletionVerdict = Done | Continue | Blocked


class CompletionEvaluator:
    """Map turn signals + capacity into a completion verdict.

    Capacity rejection always outranks a completion claim. Within an
    ``Available`` turn the layers are: structured output, then a done-marker
    line in the final message, then ``Continue``.
    """

    def __init__(self, done_marker: str = DEFAULT_DONE_MARKER) -> None:
        self._done_marker = done_marker

    def evaluate(self, signals: TurnSignals, capacity: CapacityState) -> CompletionVerdict:
        parsed = _parse_structured(signals.structured_output)

        if not _is_available(capacity):
            return Continue(remaining=_remaining_from(parsed))

        if parsed is not None:
            structured = _verdict_from_structured(parsed)
            if structured is not None:
                return structured

        if _marker_on_own_line(signals.final_message, self._done_marker):
            return Done()

        return Continue(remaining=[])


def _is_available(capacity: CapacityState) -> bool:
    match capacity:
        case Available():
            return True
        case (
            ThrottleExhausted()
            | WindowExhausted()
            | QuotaExhausted()
            | AuthFailed()
            | TransientBackendError()
        ):
            return False
        case _:  # pragma: no cover — match is exhaustive over CapacityState
            assert_never(capacity)


def _parse_structured(value: object | None) -> Mapping[str, object] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return None
        if isinstance(loaded, Mapping):
            return loaded
        return None
    return None


def _verdict_from_structured(parsed: Mapping[str, object]) -> CompletionVerdict | None:
    blocked_on = parsed.get("blocked_on")
    if blocked_on:
        return Blocked(reason=str(blocked_on))

    remaining = _remaining_from(parsed)
    complete = parsed.get("complete")
    if complete is True:
        if not remaining:
            return Done()
        return Continue(remaining=remaining)
    if complete is False:
        return Continue(remaining=remaining)
    return None


def _remaining_from(parsed: Mapping[str, object] | None) -> list[str]:
    if parsed is None:
        return []
    raw = parsed.get("remaining_work")
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw]


def _marker_on_own_line(message: str | None, done_marker: str) -> bool:
    if message is None:
        return False
    return any(line.strip() == done_marker for line in message.splitlines())
