# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The -v ladder. Same meaning in every runner, so it is tested identically."""

from __future__ import annotations

import pytest

from claudeloop.domain.verbosity import (
    Verbosity,
    parse_verbosity,
    resolve_log_plan,
)


def test_default_is_info_and_narrow() -> None:
    plan = resolve_log_plan()
    assert plan.level == "INFO"
    assert plan.include_third_party is False
    assert plan.include_payloads is False


def test_quiet_raises_the_floor_to_warning() -> None:
    assert resolve_log_plan(quiet=True).level == "WARNING"


@pytest.mark.parametrize("count", [1, 2, 3, 9])
def test_any_verbosity_reaches_debug(count: int) -> None:
    assert resolve_log_plan(verbose=count).level == "DEBUG"


def test_extra_v_widens_scope_rather_than_lowering_level() -> None:
    """Past DEBUG there is no lower level, so -vv/-vvv widen the net instead."""
    one = resolve_log_plan(verbose=1)
    two = resolve_log_plan(verbose=2)
    three = resolve_log_plan(verbose=3)
    assert (one.include_third_party, one.include_payloads) == (False, False)
    assert (two.include_third_party, two.include_payloads) == (True, False)
    assert (three.include_third_party, three.include_payloads) == (True, True)


def test_verbosity_saturates_past_the_top_rung() -> None:
    assert parse_verbosity(verbose=99) is Verbosity.FIREHOSE


def test_explicit_log_level_beats_the_count() -> None:
    """Silently overriding a named level with a count from a shell alias is
    the more surprising behaviour, so the named level wins."""
    plan = resolve_log_plan(verbose=3, log_level="warning")
    assert plan.level == "WARNING"
    assert plan.include_third_party is True
    assert plan.include_payloads is True


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid log level"):
        resolve_log_plan(log_level="LOUD")


def test_quiet_and_verbose_together_are_refused() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        resolve_log_plan(verbose=1, quiet=True)
