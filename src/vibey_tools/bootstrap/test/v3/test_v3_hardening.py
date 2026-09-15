"""Extra hardening tests for v3 modules before PyPI release."""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.aks.leader_election import LeaderElection, leader_election
from vibey_bootstrap.servicebus.async_ext import (
    MultiQueueRouter,
    ReplayGuard,
    run_async_consumer,
    service_bus_transport_type,
)
from vibey_bootstrap.transports.adx import AdxHandler, make_adx_handler
from vibey_bootstrap.transports.event_hubs import EventHubsHandler, make_event_hubs_handler

# --- Event Hubs factory + lifecycle ---


def test_make_event_hubs_handler_from_env(monkeypatch) -> None:
    pytest.importorskip("azure.eventhub")
    monkeypatch.setenv("EVENTHUB_FQNS", "ns.servicebus.windows.net")
    monkeypatch.setenv("EVENTHUB_NAME", "logs")
    monkeypatch.setenv("EVENTHUB_BATCH_SIZE", "50")
    handler = make_event_hubs_handler()
    assert handler is not None
    handler.close()


def test_event_hubs_on_close_swallows_errors() -> None:
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        flush_interval=3600.0,
    )
    producer = MagicMock()
    producer.close.side_effect = RuntimeError("close failed")
    h._producer = producer
    h.close()  # must not raise


# --- ADX factory + failure paths ---


def test_make_adx_handler_from_env(monkeypatch) -> None:
    monkeypatch.setenv("ADX_CLUSTER_URI", "https://cluster")
    monkeypatch.setenv("ADX_DATABASE", "db")
    monkeypatch.setenv("ADX_TABLE", "CustomLogs")
    handler = make_adx_handler()
    assert handler is not None
    handler.close()


def test_adx_ship_failure_returns_false() -> None:
    h = AdxHandler(cluster_uri="https://c", database="db", flush_interval=3600.0)
    with patch.object(h, "_get_client", side_effect=RuntimeError("kusto down")):
        assert h._ship(['{"k":1}']).ok is False
    h.close()


def test_adx_empty_batch() -> None:
    h = AdxHandler(cluster_uri="https://c", database="db", flush_interval=3600.0)
    assert h._ship([]).ok is True
    h.close()


# --- Email ---


def test_acs_email_send_with_plain_text(monkeypatch) -> None:
    pytest.importorskip("azure.communication.email")
    monkeypatch.setenv("ACS_CONNECTION_STRING", "endpoint=https://x/;accesskey=y")
    monkeypatch.setenv("ACS_SENDER_ADDRESS", "sender@test.com")
    from vibey_bootstrap.email import AcsEmailSender

    poller = MagicMock()
    poller.result.return_value = MagicMock(id="msg-42")
    client = MagicMock()
    client.begin_send.return_value = poller
    sender = AcsEmailSender()
    with patch.object(sender, "_get_client", return_value=client):
        msg_id = sender.send(
            to=["user@example.com"],
            subject="Hello",
            html_body="<p>Hi</p>",
            plain_text="Hi",
        )
    assert msg_id == "msg-42"
    payload = client.begin_send.call_args[0][0]
    assert payload["content"]["plainText"] == "Hi"


# --- Migrations ---


def test_migrations_stamp_and_current(tmp_path: Path) -> None:
    pytest.importorskip("alembic")
    ini = tmp_path / "alembic.ini"
    ini.write_text("[alembic]\nscript_location = .\n", encoding="utf-8")
    with patch("alembic.command.stamp") as stamp_cmd, patch("alembic.command.current"):
        from vibey_bootstrap.db.migrations import current, stamp

        stamp("head", alembic_ini=ini)
        stamp_cmd.assert_called_once()
        # current() returns None when alembic prints nothing to stdout
        assert current(alembic_ini=ini) is None


def test_migrations_write_env_py(tmp_path: Path) -> None:
    from vibey_bootstrap.db.migrations import write_env_py

    path = write_env_py(tmp_path)
    assert path.exists()
    assert "DATABASE_URL" in path.read_text()


# --- Leader election ---


def test_leader_election_acquires_when_unheld(monkeypatch) -> None:
    monkeypatch.setenv("LEADER_ELECTION_CONFIGMAP", "lock")
    monkeypatch.delenv("LEADER_HOLDER", raising=False)
    monkeypatch.setenv("POD_NAME", "pod-a")
    le = LeaderElection()
    assert le._try_acquire() is True
    assert le.is_leader is False  # not started yet
    le.start()
    time.sleep(0.05)
    le.stop()


def test_leader_election_factory(monkeypatch) -> None:
    monkeypatch.delenv("LEADER_ELECTION_CONFIGMAP", raising=False)
    le = leader_election()
    assert le.is_leader is True
    le.stop()


# --- Service Bus async ext ---


def test_replay_guard_max_size_eviction() -> None:
    guard = ReplayGuard(max_size=2, ttl_seconds=3600.0)
    assert guard.seen("a") is False
    assert guard.seen("b") is False
    assert guard.seen("c") is False  # evicts oldest


def test_service_bus_transport_type_amqp(monkeypatch) -> None:
    monkeypatch.setenv("SERVICE_BUS_TRANSPORT_TYPE", "amqp")
    assert service_bus_transport_type() == "amqp"


@pytest.mark.asyncio
async def test_run_async_consumer_completes_messages() -> None:
    msg = MagicMock()

    class FakeReceiver:
        def __init__(self) -> None:
            self._calls = 0

        async def __aenter__(self) -> FakeReceiver:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def receive_messages(self, max_wait_time: float = 5.0) -> list[MagicMock]:
            if self._calls == 0:
                self._calls += 1
                return [msg]
            return []

        async def complete_message(self, m: MagicMock) -> None:
            pass

        async def abandon_message(self, m: MagicMock) -> None:
            pass

    receiver = FakeReceiver()
    client = MagicMock()
    client.get_queue_receiver.return_value = receiver
    handled: list[MagicMock] = []

    async def handler(m: MagicMock) -> None:
        handled.append(m)
        stop.set()

    stop = asyncio.Event()
    await run_async_consumer(client, "q", handler, stop_event=stop, max_wait=0.01)
    assert handled == [msg]


def test_multi_queue_router_reuses_senders() -> None:
    client = MagicMock()
    sender = MagicMock()
    client.get_queue_sender.return_value = sender
    router = MultiQueueRouter(client)
    fake_sb = MagicMock()
    with patch.dict(sys.modules, {"azure.servicebus": fake_sb}):
        fake_sb.ServiceBusMessage = MagicMock()
        router.send("q1", "body1")
        router.send("q1", "body2")
    assert client.get_queue_sender.call_count == 1
    assert sender.send_messages.call_count == 2
