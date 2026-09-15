"""The last remaining branches: alerting failures, optional extras, and rendering edges.

Almost everything here is an ``except`` arm around an alert or an optional import. The
shared contract is that the surrounding operation keeps its result: telling somebody
about a problem is never allowed to become the problem.
"""

from __future__ import annotations

import logging
import threading
from unittest.mock import MagicMock

import pytest

import vibey_bootstrap.alerts as alerts
from vibey_bootstrap import config_refresh as config_refresh_mod
from vibey_bootstrap import governance as governance_mod
from vibey_bootstrap import health as health_mod
from vibey_bootstrap import phases as phases_mod
from vibey_bootstrap import scheduler as scheduler_mod
from vibey_bootstrap import softfail as softfail_mod
from vibey_bootstrap import subscription as subscription_mod
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.servicebus import dlq_alarm as dlq_alarm_mod
from vibey_bootstrap.servicebus import dlq_digest as dlq_digest_mod


@pytest.fixture(autouse=True)
def reset():
    _reset_counters()
    alerts.reset_state()
    alerts.register_dispatcher(lambda *a: None, recipients=["ops@example.com"])
    yield
    alerts.reset_state()


@pytest.fixture
def broken_alerting(monkeypatch):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )


# ═══════════════════════════════════════════════════════ alert guards


def test_a_soft_fail_still_records_when_alerting_is_broken(broken_alerting):
    with softfail_mod.soft_fail(operation="ai.summary", counter_name="ai.summary.failed") as ctx:
        raise ValueError("model returned nothing")
    assert ctx["degraded"] is True
    assert ctx["reason"] == "ValueError"
    assert counter_snapshot()["ai.summary.failed"] == 1


def test_a_phase_failure_is_recorded_even_when_alerting_is_broken(broken_alerting):
    def boom():
        raise RuntimeError("config store unreachable")

    result = phases_mod.run_phase("load-config", boom, namespace="svc")
    assert result.ok is False
    assert counter_snapshot()["svc.load-config.failed"] == 1


def test_a_subscription_alert_that_fails_does_not_propagate(broken_alerting):
    subscription_mod._fire_critical_alert("sub.renew", RuntimeError("gone"), "resource gone")


def test_a_watchdog_alert_that_fails_still_stamps_the_last_alert_time(monkeypatch, broken_alerting):
    import vibey_bootstrap.heartbeat as hb

    monkeypatch.setattr(hb, "_last_iteration_age_seconds", lambda: 9999.0)
    hb._last_watchdog_alert_at = 0.0
    stop = threading.Event()
    thread = hb.start_consumer_watchdog(stop, interval_seconds=0.05, silence_threshold_seconds=1.0)
    deadline = __import__("time").monotonic() + 3.0
    while hb._last_watchdog_alert_at == 0.0 and __import__("time").monotonic() < deadline:
        __import__("time").sleep(0.02)
    stop.set()
    thread.join(timeout=2.0)
    assert hb._last_watchdog_alert_at != 0.0
    hb._last_watchdog_alert_at = 0.0


def test_an_http_crash_is_re_raised_even_when_alerting_is_broken(broken_alerting):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from vibey_bootstrap.fastapi_middleware import install_middleware

    app = FastAPI()
    install_middleware(app)

    @app.get("/boom")
    def boom():
        raise RuntimeError("handler exploded")

    @app.get("/five-hundred")
    def five_hundred():
        from fastapi.responses import Response

        return Response(status_code=503)

    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/boom").status_code == 500
    assert client.get("/five-hundred").status_code == 503


def test_a_scheduler_alert_that_fails_still_yields_the_default_trigger(broken_alerting):
    trigger = scheduler_mod.parse_cron_trigger("not a cron expression")
    assert trigger is not None


# ═══════════════════════════════════════════════════════ scheduler


def test_the_default_trigger_is_a_cron_trigger():
    from apscheduler.triggers.cron import CronTrigger

    assert isinstance(scheduler_mod._default_trigger(), CronTrigger)


def test_without_apscheduler_parsing_a_cron_expression_is_an_import_error(monkeypatch):
    import builtins as py_builtins

    real_import = py_builtins.__import__

    def refuse(name, *a, **kw):
        if name.startswith("apscheduler"):
            raise ImportError("no apscheduler")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(py_builtins, "__import__", refuse)
    with pytest.raises(ImportError, match="scheduler.* extra"):
        scheduler_mod.parse_cron_trigger("0 * * * *")


# ═══════════════════════════════════════════════════════ config refresh


def test_a_build_without_the_bootstrap_package_logs_and_moves_on(monkeypatch, caplog):
    import builtins as py_builtins

    real_import = py_builtins.__import__

    def refuse(name, *a, **kw):
        if name == "vibey_bootstrap":
            raise ImportError("not importable here")
        return real_import(name, *a, **kw)

    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setattr(py_builtins, "__import__", refuse)
    with caplog.at_level(logging.DEBUG, logger=config_refresh_mod.__name__):
        config_refresh_mod.refresh_log_flags()
    assert "no bootstrap importable" in caplog.text


def test_a_remote_read_failure_is_counted_even_when_alerting_is_broken(
    monkeypatch, broken_alerting
):
    import vibey_bootstrap

    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setattr(
        vibey_bootstrap,
        "refresh_setting",
        MagicMock(side_effect=RuntimeError("App Config unreachable")),
    )
    config_refresh_mod.refresh_log_flags()
    assert counter_snapshot()["log_flag_refresh.remote_read_failed"] == 1


def test_a_refresh_that_crashes_outright_is_counted_not_raised(monkeypatch, caplog):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setattr(
        config_refresh_mod,
        "effective_log_level",
        MagicMock(side_effect=RuntimeError("level resolver is broken")),
    )
    with caplog.at_level(logging.ERROR, logger=config_refresh_mod.__name__):
        config_refresh_mod.refresh_log_flags()
    assert counter_snapshot()["log_flag_refresh.crashed"] == 1
    assert "crashed" in caplog.text


# ═══════════════════════════════════════════════════════ subscription


def test_a_gone_resource_with_no_recreate_handler_gives_up_loudly(caplog):
    from vibey_bootstrap.subscription import RenewableResource, SubscriptionGone, renewal_loop

    stop = threading.Event()
    with caplog.at_level(logging.ERROR):
        renewal_loop(
            RenewableResource(id="s1", handle=object(), expires_at=None),
            stop_event=stop,
            renew_fn=MagicMock(side_effect=SubscriptionGone("404")),
            recreate_fn=None,
            interval_seconds=0.01,
            operation="graph.subscription",
        )
    assert "no recreate handler" in caplog.text


def test_a_recreate_handler_that_also_fails_ends_the_loop(caplog):
    from vibey_bootstrap.subscription import RenewableResource, SubscriptionGone, renewal_loop

    stop = threading.Event()
    with caplog.at_level(logging.ERROR):
        renewal_loop(
            RenewableResource(id="s1", handle=object(), expires_at=None),
            stop_event=stop,
            renew_fn=MagicMock(side_effect=SubscriptionGone("404")),
            recreate_fn=MagicMock(side_effect=RuntimeError("create quota exceeded")),
            interval_seconds=0.01,
            operation="graph.subscription",
        )
    assert "recreate failed" in caplog.text


# ═══════════════════════════════════════════════════════ Service Bus DLQ


def test_the_dlq_alarm_reset_is_test_only(monkeypatch):
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError, match="test-only"):
        dlq_alarm_mod.reset_state()


def test_a_dlq_peek_that_fails_reports_zeros(caplog):
    repo = MagicMock()
    repo.peek_dead_letter_messages.side_effect = RuntimeError("namespace unreachable")
    with caplog.at_level(logging.ERROR):
        assert dlq_alarm_mod.check_dlq_growth_rate(repo) == {"current": 0, "delta": 0, "alerted": 0}
    assert "peek failed" in caplog.text


def test_dlq_growth_is_reported_even_when_alerting_is_broken(broken_alerting):
    dlq_alarm_mod.reset_state()
    repo = MagicMock()
    repo.peek_dead_letter_messages.return_value = [{}] * 2
    dlq_alarm_mod.check_dlq_growth_rate(repo, alert_threshold=1)
    repo.peek_dead_letter_messages.return_value = [{}] * 20
    result = dlq_alarm_mod.check_dlq_growth_rate(repo, alert_threshold=1)
    assert result["delta"] == 18 and result["alerted"] == 0  # the alert itself failed


def test_a_resubmit_token_that_is_not_ours_is_rejected():
    from vibey_bootstrap.servicebus.dlq_digest import (
        InvalidResubmitToken,
        issue_resubmit_token,
        verify_resubmit_token,
    )
    from vibey_bootstrap.tokens import issue_action_token

    verify_resubmit_token("secret", issue_resubmit_token("secret"))
    other = issue_action_token("secret", action="something-else", ttl_seconds=60)
    with pytest.raises(InvalidResubmitToken):
        verify_resubmit_token("secret", other)


def test_a_digest_without_a_resubmit_url_says_how_to_resubmit():
    body = dlq_digest_mod.build_dlq_digest_body(entries=[], resubmit_url=None)
    assert "resubmit CLI" in body


def test_a_digest_peek_that_fails_still_mails_the_pending_alerts(caplog):
    repo = MagicMock()
    repo.peek_dead_letter_messages.side_effect = RuntimeError("namespace unreachable")
    email = MagicMock()
    alerts.alert_dev_team(alerts.AlertSeverity.ERROR, "something was already wrong")

    with caplog.at_level(logging.ERROR):
        result = dlq_digest_mod.run_dlq_digest(
            repo,
            email,
            dev_recipients=["ops@example.com"],
            api_key="k",
            public_base_url="https://ops.example.com",
        )

    assert "peek failed" in caplog.text
    assert result == {
        "dlq_count": 0,
        "email_sent": True,
        "skipped_reason": None,
        "pending_alert_count": 1,
    }
    email.send_email.assert_called_once()


# ═══════════════════════════════════════════════════════ governance


def test_committing_against_a_project_with_no_budget_records_the_spend():
    guard = governance_mod.BudgetGuard()
    guard.commit("unbudgeted", "monthly", 12.5)
    assert guard.check("unbudgeted", "monthly", 1.0).allowed is True


def test_the_module_level_budget_check_uses_the_default_guard():
    assert governance_mod.budget_guard("p", "monthly", 1.0).allowed is True


# ═══════════════════════════════════════════════════════ health


def test_app_config_health_needs_the_appconfiguration_extra(monkeypatch):
    import builtins as py_builtins

    real_import = py_builtins.__import__

    def refuse(name, *a, **kw):
        if "appconfiguration" in name or name == "azure.identity":
            raise ImportError("not installed")
        return real_import(name, *a, **kw)

    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setenv("AZURE_APP_CONFIGURATION_CONNECTION_STRING", "Endpoint=https://x")
    monkeypatch.setattr(py_builtins, "__import__", refuse)
    assert health_mod.check_app_config_health()["status"] == "error"


def test_app_insights_health_is_ok_once_a_connection_string_is_present(monkeypatch):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "InstrumentationKey=k")
    assert health_mod.check_app_insights_health() == {"status": "ok"}


def test_app_insights_logging_short_circuits_in_mock_mode(monkeypatch):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "1")
    assert health_mod.check_app_insights_logging() == {"status": "ok", "mock": True}


def test_app_insights_logging_finds_an_attached_azure_handler(monkeypatch):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "InstrumentationKey=k")

    class AzureMonitorLogExporterHandler(logging.Handler):
        def emit(self, record): ...

    root = logging.getLogger()
    handler = AzureMonitorLogExporterHandler()
    root.addHandler(handler)
    try:
        assert health_mod.check_app_insights_logging()["status"] == "ok"
    finally:
        root.removeHandler(handler)
