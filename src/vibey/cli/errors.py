"""Turning exceptions into something an operator can act on.

Every CLI command runs inside ``asyncio.run(...)``, so an unhandled error
arrives as a traceback whose most prominent frames are asyncio's. That is the
worst possible presentation: the interesting line is buried, and a person who
is not a Python developer has no way to read it.

``guard`` renders known errors as one plain sentence plus, where we have one,
the next thing to try. Unknown errors keep their traceback -- suppressing a
stack trace we do not understand would trade a confusing message for a silent
one.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import NoReturn

import typer

from vibey.domain.errors import (
    BudgetExceeded,
    EscalationExhausted,
    HandoffRejected,
    IllegalTransitionError,
    InvalidPhaseError,
    InvalidSpecError,
    NoEligibleEngine,
    VibeyError,
)

EXIT_USAGE = 2
EXIT_BLOCKED = 3

# What to suggest next, per error type. Absent means "no honest suggestion" --
# better to say nothing than to invent a remedy that does not work.
_NEXT_STEP: dict[type[BaseException], str] = {
    NoEligibleEngine: (
        "Every engine is excluded, circuit-open, or missing a required capability.\n"
        "Run `vibey engines` to see why, or `vibey doctor` to check installs and auth."
    ),
    BudgetExceeded: (
        "Raise the cap in vibey.toml under [budget], or run `vibey cost` to see\n"
        "where the spend went."
    ),
    EscalationExhausted: (
        "The work item failed at every rung of the effort ladder. `vibey gates`\n"
        "lists the human gate it raised."
    ),
    HandoffRejected: (
        "The no-loss gate refused the handoff, so nothing was lost -- the run is\n"
        "parked instead. `vibey gates` shows what the gate could not carry over."
    ),
    IllegalTransitionError: (
        "The project is not in a phase this command applies to. `vibey status`\n"
        "shows the current phase."
    ),
    InvalidSpecError: "Run `vibey design` to finish the spec before building.",
    InvalidPhaseError: "This looks like a bug in vibey rather than your project.",
}


def render(exc: VibeyError) -> str:
    lines = [f"Error: {exc}"]
    hint = _NEXT_STEP.get(type(exc))
    if hint:
        lines += ["", hint]
    return "\n".join(lines)


def fail(exc: VibeyError) -> NoReturn:
    typer.echo(render(exc), err=True)
    raise typer.Exit(code=EXIT_BLOCKED)


@contextmanager
def guard() -> Iterator[None]:
    """Render VibeyError as a message; let anything else keep its traceback."""
    try:
        yield
    except VibeyError as exc:
        fail(exc)
    except KeyboardInterrupt:
        # Ctrl-C is a decision, not a failure. 130 is what a shell expects.
        typer.echo("Interrupted.", err=True)
        raise typer.Exit(code=130) from None
    except BrokenPipeError:
        # `vibey ledger | head` closes the pipe early; that is not an error.
        sys.stderr.close()
        raise typer.Exit(code=0) from None
