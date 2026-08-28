# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Resolving how loud the process should be, from CLI flags.

Pure: no logging library, no I/O. The ladder is a domain decision because it
has to mean the same thing everywhere -- an operator who learns `-vv` on one
runner should not get something different from the next one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

VALID_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class Verbosity(IntEnum):
    """How much detail the operator asked for.

    QUIET and NORMAL differ only in level. The three DEBUG tiers differ in
    *scope*: our own logs, then third-party libraries, then full payloads --
    because "more detail" past DEBUG is not a level, it is a wider net.
    """

    QUIET = -1
    NORMAL = 0
    VERBOSE = 1
    TRACE = 2
    FIREHOSE = 3


@dataclass(frozen=True, slots=True)
class LogPlan:
    """The resolved logging intent a composition root acts on."""

    level: str
    include_third_party: bool
    include_payloads: bool


def parse_verbosity(*, verbose: int = 0, quiet: bool = False) -> Verbosity:
    if quiet and verbose:
        raise ValueError("--quiet and --verbose are mutually exclusive")
    if quiet:
        return Verbosity.QUIET
    return Verbosity(min(verbose, int(Verbosity.FIREHOSE)))


def resolve_log_plan(
    *,
    verbose: int = 0,
    quiet: bool = False,
    log_level: str | None = None,
) -> LogPlan:
    """Turn CLI flags into a logging plan.

    An explicit ``--log-level`` always wins over the ``-v`` count: if someone
    names a level, honouring it is less surprising than silently overriding it
    with a count they may have set in an alias. The count still widens scope,
    so ``--log-level WARNING -vvv`` is a legitimate way to ask for warnings
    from everything.
    """
    verbosity = parse_verbosity(verbose=verbose, quiet=quiet)
    if log_level is not None:
        candidate = log_level.strip().upper()
        if candidate not in VALID_LEVELS:
            raise ValueError(
                f"invalid log level {log_level!r}; expected one of {', '.join(VALID_LEVELS)}"
            )
        level = candidate
    elif verbosity is Verbosity.QUIET:
        level = "WARNING"
    elif verbosity is Verbosity.NORMAL:
        level = "INFO"
    else:
        level = "DEBUG"
    return LogPlan(
        level=level,
        include_third_party=verbosity >= Verbosity.TRACE,
        include_payloads=verbosity >= Verbosity.FIREHOSE,
    )
