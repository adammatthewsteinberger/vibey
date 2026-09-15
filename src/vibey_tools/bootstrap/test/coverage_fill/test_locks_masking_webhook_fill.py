"""Service Bus lock renewal, log masking, the Graph webhook route, and bootstrap.

Each of these sits on a request or message path, so the tests are about what happens
when the surrounding platform misbehaves: a renewer that will not construct, a value
that cannot be repr'd, a webhook body that is not JSON.
"""

from __future__ import annotations

import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap import bootstrap as bootstrap_mod
from vibey_bootstrap import sb_lock as sb_lock_mod
from vibey_bootstrap.auth import webhook as webhook_mod
from vibey_bootstrap.auth.webhook import WebhookDedup, install_graph_webhook_route
from vibey_bootstrap.bootstrap import ensure_bootstrap, load_local_settings
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.failclose import ConfigurationError
from vibey_bootstrap.logging import masking
from vibey_bootstrap.sb_lock import ManagedLock


@pytest.fixture(autouse=True)
def counters():
    _reset_counters()


# ═══════════════════════════════════════════════════════════ sb_lock


def test_the_renewer_comes_from_the_service_bus_sdk(monkeypatch):
    import azure.servicebus

    monkeypatch.setattr(azure.servicebus, "AutoLockRenewer", MagicMock(return_value="renewer"))
    assert sb_lock_mod._new_auto_lock_renewer() == "renewer"


def test_a_managed_lock_that_cannot_start_lets_processing_continue(monkeypatch, caplog):
    monkeypatch.setattr(
        sb_lock_mod, "_new_auto_lock_renewer", MagicMock(side_effect=RuntimeError("no AMQP link"))
    )
    lock = ManagedLock(MagicMock(), MagicMock())
    with caplog.at_level(logging.WARNING):
        lock.start()
    assert lock._renewer is None
    assert counter_snapshot()["sb_lock.renewer_construction_failed"] == 1
    assert "AutoLockRenewer setup failed" in caplog.text


def test_starting_a_managed_lock_twice_registers_once(monkeypatch):
    renewer = MagicMock()
    monkeypatch.setattr(sb_lock_mod, "_new_auto_lock_renewer", MagicMock(return_value=renewer))
    lock = ManagedLock(MagicMock(), MagicMock(), max_lock_renewal_seconds=120)
    lock.start()
    lock.start()
    renewer.register.assert_called_once()
    assert renewer.register.call_args.kwargs["max_lock_renewal_duration"] == 120


def test_closing_a_managed_lock_that_never_started_is_a_no_op():
    ManagedLock(MagicMock(), MagicMock()).close()


def test_a_renewer_that_will_not_close_is_still_released(monkeypatch, caplog):
    renewer = MagicMock()
    renewer.close.side_effect = RuntimeError("link already detached")
    monkeypatch.setattr(sb_lock_mod, "_new_auto_lock_renewer", MagicMock(return_value=renewer))

    with caplog.at_level(logging.WARNING), ManagedLock(MagicMock(), MagicMock()) as lock:
        assert lock._renewer is renewer
    assert lock._renewer is None
    assert counter_snapshot()["sb_lock.close_failed"] == 1


# ═══════════════════════════════════════════════════════════ masking


def test_something_that_is_not_an_email_is_fully_masked():
    assert masking.mask_email_address("not-an-address") == "***"


def test_a_short_local_part_is_masked_entirely():
    assert masking.mask_email_address("ab@example.com") == "***@example.com"


def test_a_bytes_like_object_that_cannot_be_decoded_is_described_by_length():
    class Weird(bytes):
        def decode(self, *a, **kw):  # noqa: D401 - deliberately wrong signature
            raise TypeError("cannot decode this")

    assert masking.content_preview(Weird(b"1234")) == "<bytes len=4>"


def test_an_object_that_cannot_be_serialised_falls_back_to_repr():
    class NoJson:
        def __repr__(self) -> str:
            return "<NoJson>"

    with patch.object(masking.json, "dumps", side_effect=RuntimeError("no encoder")):
        assert masking.safe_json_dumps(NoJson()) == "<NoJson>"


def test_an_object_that_cannot_even_be_repr_d_is_labelled():
    class Hostile:
        def __repr__(self) -> str:
            raise RuntimeError("repr explodes")

    with patch.object(masking.json, "dumps", side_effect=RuntimeError("no encoder")):
        assert masking.safe_json_dumps(Hostile()) == "<unreprable>"


def test_a_non_string_argument_name_is_never_sensitive():
    assert masking._looks_sensitive(42) is False  # type: ignore[arg-type]


def test_safe_repr_of_a_hostile_value_is_labelled():
    # _safe_repr deliberately never calls an arbitrary __repr__; it summarises containers
    # structurally instead. So the only way to break it is to break the summary itself.
    class HostileDict(dict):
        def __len__(self) -> int:
            raise RuntimeError("len explodes")

    assert masking._safe_repr(HostileDict()) == "<unreprable>"


# ═══════════════════════════════════════════════════════════ webhook


def test_the_dedup_reset_is_test_only(monkeypatch):
    dedup = WebhookDedup()
    dedup.already_seen(("s", "m"))
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError, match="test-only"):
        dedup.reset()

    monkeypatch.setenv("AZURE_BOOTSTRAP_ALLOW_RESET", "1")
    dedup.reset()
    assert dedup.already_seen(("s", "m")) is False  # the memory really was cleared


@pytest.fixture
def client(monkeypatch):
    """A FastAPI test client with the Graph webhook route installed."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    monkeypatch.setenv("GRAPH_WEBHOOK_CLIENT_STATE", "shared-secret")
    app = FastAPI()
    handled: list[str] = []
    dedup = WebhookDedup()
    install_graph_webhook_route(app, "/hook", background_handler=handled.append, dedup=dedup)
    return TestClient(app), handled


def test_a_body_that_is_not_json_is_a_bad_request(client):
    api, _ = client
    response = api.post(
        "/hook", content=b"not json at all", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400


def test_entries_that_are_not_objects_are_skipped(client):
    api, handled = client
    body = {
        "value": [
            "a string, not an entry",
            {"clientState": "shared-secret", "subscriptionId": "s1", "resourceData": {"id": "m1"}},
        ]
    }
    assert api.post("/hook", json=body).status_code == 202
    assert handled == ["m1"]


def test_an_entry_with_no_message_id_is_skipped(client):
    api, handled = client
    body = {"value": [{"clientState": "shared-secret", "subscriptionId": "s1", "resourceData": {}}]}
    assert api.post("/hook", json=body).status_code == 202
    assert handled == []


def test_an_unconfigured_endpoint_refuses_every_entry(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    install_graph_webhook_route(app, "/hook", background_handler=lambda mid: None)
    with patch.object(
        webhook_mod,
        "verify_webhook_client_state",
        side_effect=ConfigurationError("GRAPH_WEBHOOK_CLIENT_STATE unset"),
    ):
        response = TestClient(app).post("/hook", json={"value": [{"clientState": "x"}]})
    assert response.status_code == 401
    assert counter_snapshot()["webhook.client_state_mismatch"] == 1


# ═══════════════════════════════════════════════════════════ bootstrap


def test_a_failed_bootstrap_is_logged_and_re_raised(monkeypatch, caplog):
    from vibey_bootstrap.services import application_bootstrap

    monkeypatch.setattr(bootstrap_mod, "_bootstrap_initialized", False)
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setattr(
        application_bootstrap,
        "initialize_application",
        MagicMock(side_effect=RuntimeError("App Config unreachable")),
    )
    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
        ensure_bootstrap()
    assert "Bootstrap initialization failed" in caplog.text
    assert bootstrap_mod._bootstrap_initialized is False


def test_a_successful_bootstrap_is_run_once(monkeypatch):
    from vibey_bootstrap.services import application_bootstrap

    monkeypatch.setattr(bootstrap_mod, "_bootstrap_initialized", False)
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    initialize = MagicMock()
    monkeypatch.setattr(application_bootstrap, "initialize_application", initialize)
    ensure_bootstrap()
    ensure_bootstrap()
    initialize.assert_called_once()
    bootstrap_mod._bootstrap_initialized = False


def test_local_settings_without_a_values_object_load_nothing(tmp_path):
    path = tmp_path / "local.settings.json"
    path.write_text(json.dumps({"IsEncrypted": False}))
    assert load_local_settings(path) == 0


def test_a_setting_the_environment_refuses_is_skipped(tmp_path, monkeypatch):
    path = tmp_path / "local.settings.json"
    path.write_text(json.dumps({"Values": {"GOOD": "1", "_DOC": "x", "BAD": "2"}}))

    class PickyEnviron(dict):
        def __setitem__(self, key, value):
            if key == "BAD":
                raise RuntimeError("environment is read-only for this key")
            super().__setitem__(key, value)

    fake = PickyEnviron(os.environ)
    fake.pop("GOOD", None)
    monkeypatch.setattr(bootstrap_mod.os, "environ", fake)

    assert load_local_settings(path) == 1
    assert fake["GOOD"] == "1" and "BAD" not in fake


def test_resetting_bootstrap_state_is_test_only(monkeypatch):
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError, match="test-only"):
        bootstrap_mod._reset_bootstrap_state()
