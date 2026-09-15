"""Dispatcher paths that only appear when something is already going wrong.

Alerts are the last line of defence during an incident, so every one of these asserts
the same property from a different angle: the dispatcher absorbs the failure rather
than becoming one.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from unittest.mock import MagicMock

import pytest

from vibey_bootstrap.alerts import dispatcher
from vibey_bootstrap.alerts.dispatcher import (
    AlertRecord,
    AlertSeverity,
    alert_dev_team,
    drain_pending_alerts,
    install_global_exception_hooks,
    register_dispatcher,
    reset_state,
)


@pytest.fixture(autouse=True)
def clean_state():
    reset_state()
    yield
    reset_state()


def a_record(subject: str = "boom", **ctx) -> AlertRecord:
    now = time.monotonic()
    return AlertRecord(
        severity=AlertSeverity.CRITICAL,
        subject=subject,
        context=ctx,
        dedup_key=subject,
        first_seen=now,
        last_seen=now,
    )


# ── env resolvers: a malformed value must not take the dispatcher down ──────


@pytest.mark.parametrize(
    "env, resolver, default",
    [
        ("ALERT_DEDUP_WINDOW_SECONDS", dispatcher._dedup_window, 600.0),
        ("ALERT_MAX_PER_HOUR", dispatcher._max_per_hour, 30),
        ("ALERT_ESCALATE_AFTER", dispatcher._escalation_threshold, 5),
        ("ALERT_ESCALATE_WINDOW_SECONDS", dispatcher._escalation_window, 900.0),
    ],
)
def test_an_unparsable_setting_falls_back_to_its_default(monkeypatch, env, resolver, default):
    monkeypatch.setenv(env, "not-a-number")
    assert resolver() == default


def test_recipients_come_from_the_environment_when_none_are_passed(monkeypatch):
    monkeypatch.setenv("DEV_ALERT_RECIPIENTS", " a@example.com , ,b@example.com ")
    register_dispatcher(MagicMock())
    assert dispatcher._state.recipients == ["a@example.com", "b@example.com"]


# ── alert_dev_team ─────────────────────────────────────────────────────────


def test_an_unknown_severity_string_is_treated_as_an_error():
    sender = MagicMock()
    register_dispatcher(sender, ["ops@example.com"])
    alert_dev_team("catastrophic", "unknown severity")
    assert drain_pending_alerts()[0].severity is AlertSeverity.ERROR
    sender.assert_not_called()


def test_a_known_severity_string_is_honoured():
    register_dispatcher(MagicMock(), ["ops@example.com"])
    alert_dev_team("warn", "just a warning")
    assert drain_pending_alerts() == []  # WARN is log-only


def test_the_dedup_table_is_pruned_once_it_grows_too_large(monkeypatch):
    # Past the cap, entries older than the dedup window are dropped — otherwise a
    # long-running process with high-cardinality subjects grows the table forever.
    monkeypatch.setattr(dispatcher, "_DEDUP_MAX_ENTRIES", 4)
    monkeypatch.setenv("ALERT_DEDUP_WINDOW_SECONDS", "0")
    register_dispatcher(MagicMock(), ["ops@example.com"])
    for i in range(6):
        alert_dev_team(AlertSeverity.WARN, f"subject {i}")
    # Not an exact count: two alerts can share a monotonic reading, so the cutoff can
    # spare the last pair. The invariant is that the table shrank and kept the newest.
    assert len(dispatcher._state.dedup) < 4
    assert "subject 5" in dispatcher._state.dedup
    assert "subject 0" not in dispatcher._state.dedup


def test_a_dispatch_that_blows_up_internally_is_swallowed(monkeypatch, caplog):
    monkeypatch.setattr(
        dispatcher, "_redact", MagicMock(side_effect=RuntimeError("redaction exploded"))
    )
    with caplog.at_level(logging.ERROR):
        alert_dev_team(AlertSeverity.CRITICAL, "boom")  # must not raise
    assert "dispatch failed" in caplog.text


# ── _send_critical ─────────────────────────────────────────────────────────


def test_stale_send_timestamps_are_evicted_before_the_rate_limit_is_judged(monkeypatch):
    monkeypatch.setenv("ALERT_MAX_PER_HOUR", "1")
    sender = MagicMock()
    register_dispatcher(sender, ["ops@example.com"])
    # One send from more than an hour ago must not count against this hour's budget.
    dispatcher._state.sent_timestamps.append(time.monotonic() - 4000.0)

    dispatcher._send_critical(a_record())
    sender.assert_called_once()
    assert list(dispatcher._state.sent_timestamps) == [pytest.approx(time.monotonic(), abs=5)]


def test_send_critical_swallows_a_failure_in_its_own_machinery(monkeypatch, caplog):
    register_dispatcher(MagicMock(), ["ops@example.com"])
    monkeypatch.setattr(
        dispatcher, "_render_alert_html", MagicMock(side_effect=RuntimeError("template exploded"))
    )
    with caplog.at_level(logging.ERROR):
        dispatcher._send_critical(a_record())  # must not raise
    assert "_send_critical failed" in caplog.text


# ── global exception hooks ─────────────────────────────────────────────────


@pytest.fixture
def restore_excepthook():
    saved = sys.excepthook
    yield
    sys.excepthook = saved


def test_the_sync_hook_alerts_and_still_chains_to_its_predecessor(restore_excepthook):
    previous = MagicMock()
    sys.excepthook = previous
    install_global_exception_hooks()
    register_dispatcher(MagicMock(), ["ops@example.com"])

    err = ValueError("the roof is on fire")
    sys.excepthook(ValueError, err, None)

    previous.assert_called_once_with(ValueError, err, None)


def test_the_sync_hook_survives_both_halves_failing(monkeypatch, restore_excepthook):
    sys.excepthook = MagicMock(side_effect=RuntimeError("previous hook is broken too"))
    install_global_exception_hooks()
    monkeypatch.setattr(
        dispatcher, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is broken"))
    )
    sys.excepthook(ValueError, ValueError("x"), None)  # must not raise


async def test_the_asyncio_handler_alerts_and_chains(monkeypatch):
    install_global_exception_hooks()
    loop = asyncio.get_running_loop()
    handler = loop.get_exception_handler()
    assert handler is not None

    seen: list[dict] = []
    monkeypatch.setattr(dispatcher, "alert_dev_team", lambda *a, **k: seen.append(k))
    monkeypatch.setattr(loop, "default_exception_handler", MagicMock())

    handler(loop, {"exception": KeyError("missing"), "message": "task blew up"})
    assert seen[0]["dedup_key"] == "uncaught_async:KeyError"
    assert "KeyError" in seen[0]["subject"]
    loop.default_exception_handler.assert_called_once()
    loop.set_exception_handler(None)


async def test_the_asyncio_handler_copes_with_a_context_carrying_no_exception(monkeypatch):
    install_global_exception_hooks()
    loop = asyncio.get_running_loop()
    handler = loop.get_exception_handler()

    seen: list[dict] = []
    monkeypatch.setattr(dispatcher, "alert_dev_team", lambda *a, **k: seen.append(k))
    monkeypatch.setattr(loop, "default_exception_handler", MagicMock())

    handler(loop, {"message": "socket.send() raised"})
    assert seen[0]["dedup_key"] == "uncaught_async:AsyncioError"
    loop.set_exception_handler(None)


async def test_the_asyncio_handler_survives_both_halves_failing(monkeypatch):
    install_global_exception_hooks()
    loop = asyncio.get_running_loop()
    handler = loop.get_exception_handler()
    monkeypatch.setattr(
        dispatcher, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is broken"))
    )
    monkeypatch.setattr(
        loop,
        "default_exception_handler",
        MagicMock(side_effect=RuntimeError("chained handler is broken")),
    )
    handler(loop, {"exception": KeyError("missing")})  # must not raise
    loop.set_exception_handler(None)


def test_reset_state_refuses_outside_a_test_environment(monkeypatch):
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError, match="test-only"):
        reset_state()


def test_a_deduped_alert_gains_context_it_did_not_have_without_losing_what_it_did():
    register_dispatcher(MagicMock(), ["ops@example.com"])
    alert_dev_team(AlertSeverity.WARN, "same subject", {"tenant": "acme"})
    alert_dev_team(AlertSeverity.WARN, "same subject", {"tenant": "other", "region": "eu"})

    rec = dispatcher._state.dedup["same subject"]
    assert rec.count == 2
    assert rec.context == {"tenant": "acme", "region": "eu"}  # first writer wins


def test_a_critical_with_nowhere_to_send_it_is_kept_for_the_digest():
    register_dispatcher(MagicMock(), [])  # a sender, but no recipients
    alert_dev_team(AlertSeverity.CRITICAL, "nobody to tell")
    assert [r.subject for r in drain_pending_alerts()] == ["nobody to tell"]


def test_the_dispatcher_survives_even_its_own_error_logging_failing(monkeypatch):
    broken = MagicMock()
    broken.exception.side_effect = RuntimeError("logging is down too")
    monkeypatch.setattr(dispatcher, "_logger", broken)
    monkeypatch.setattr(dispatcher, "_redact", MagicMock(side_effect=RuntimeError("boom")))
    alert_dev_team(AlertSeverity.CRITICAL, "everything is broken")  # must not raise


def test_send_critical_survives_even_its_own_error_logging_failing(monkeypatch):
    register_dispatcher(MagicMock(), ["ops@example.com"])
    broken = MagicMock()
    broken.exception.side_effect = RuntimeError("logging is down too")
    monkeypatch.setattr(dispatcher, "_logger", broken)
    monkeypatch.setattr(dispatcher, "_render_alert_html", MagicMock(side_effect=RuntimeError("x")))
    dispatcher._send_critical(a_record())  # must not raise


# ── the escalation ladder ──────────────────────────────────────────────────


def test_a_threshold_of_zero_disables_escalation_entirely():
    from collections import deque

    from vibey_bootstrap.alerts.escalation import should_escalate

    history: deque[float] = deque()
    assert should_escalate(history, threshold=0, window_seconds=900.0) is False
    assert not history  # and nothing was recorded


def test_events_that_fell_out_of_the_window_do_not_count_towards_the_threshold():
    from collections import deque

    from vibey_bootstrap.alerts.escalation import should_escalate

    history = deque([time.monotonic() - 5000.0, time.monotonic() - 4000.0])
    assert should_escalate(history, threshold=2, window_seconds=60.0) is False
    assert len(history) == 1  # both stale entries pruned, this one appended


def test_installing_the_hooks_before_any_event_loop_exists_is_not_fatal(
    monkeypatch, restore_excepthook
):
    """No loop yet: the sync hook still installs and the asyncio half is skipped.

    Patched rather than relying on the interpreter, because the behaviour is
    version-dependent — `asyncio.get_event_loop()` raises RuntimeError from 3.12 but
    quietly creates a loop on 3.11, so on 3.11 this branch is otherwise unreachable.
    """
    monkeypatch.setattr(
        asyncio, "get_event_loop", MagicMock(side_effect=RuntimeError("no current event loop"))
    )
    previous = MagicMock()
    sys.excepthook = previous

    install_global_exception_hooks()  # must not raise

    assert sys.excepthook is not previous  # the sync half still went in
