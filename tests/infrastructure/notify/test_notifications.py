import hashlib
import hmac
import json
from uuid import uuid4

import pytest

from vibey.infrastructure.notify import (
    DesktopNotifier,
    NotificationEvent,
    NotificationKind,
    NotificationService,
    WebhookPublisher,
)


def test_notification_event_creation_and_payload() -> None:
    project_id = uuid4()
    event = NotificationEvent(
        kind=NotificationKind.HUMAN_GATE_RAISED,
        project_id=project_id,
        title="Human Gate Raised",
        message="Awaiting approval for Phase 2",
        payload={"gate_id": "gate-123", "rule": "R1"},
    )

    data = event.to_dict()
    assert data["kind"] == "human_gate_raised"
    assert data["project_id"] == str(project_id)
    assert data["title"] == "Human Gate Raised"
    assert data["payload"]["gate_id"] == "gate-123"


def test_webhook_publisher_signature() -> None:
    publisher = WebhookPublisher()
    project_id = uuid4()
    event = NotificationEvent(
        kind=NotificationKind.BUDGET_EXCEEDED,
        project_id=project_id,
        title="Budget Exceeded",
        message="Spend exceeded $40.00",
        payload={"spend": 42.50, "cap": 40.0},
    )

    secret = "vibey-secret-key"
    payload_bytes = json.dumps(event.to_dict(), sort_keys=True).encode("utf-8")
    expected_sig = (
        "sha256=" + hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    )

    signature = publisher.compute_signature(payload_bytes, secret)
    assert signature == expected_sig


@pytest.mark.asyncio
async def test_desktop_notifier_command_construction() -> None:
    calls: list[list[str]] = []

    def fake_runner(cmd: list[str]) -> bool:
        calls.append(cmd)
        return True

    notifier = DesktopNotifier(executor=fake_runner, platform_override="darwin")
    project_id = uuid4()
    event = NotificationEvent(
        kind=NotificationKind.PHASE_TRANSITIONED,
        project_id=project_id,
        title="Phase Transitioned",
        message="Moved to REVIEW phase",
        payload={"from": "build", "to": "review"},
    )

    result = await notifier.notify(event)
    assert result is True
    assert len(calls) == 1
    assert calls[0][0] == "osascript"
    assert "Phase Transitioned" in calls[0][2]


@pytest.mark.asyncio
async def test_notification_service_composite_dispatch() -> None:
    dispatched_desktop: list[NotificationEvent] = []
    dispatched_webhooks: list[tuple[str, str, dict[str, object]]] = []

    class FakeDesktopNotifier:
        async def notify(self, ev: NotificationEvent) -> bool:
            dispatched_desktop.append(ev)
            return True

    class FakeWebhookPublisher:
        async def publish(self, ev: NotificationEvent, url: str, secret: str | None = None) -> bool:
            dispatched_webhooks.append((url, secret or "", ev.to_dict()))
            return True

    service = NotificationService(
        desktop_notifier=FakeDesktopNotifier(),  # type: ignore[arg-type]
        webhook_publisher=FakeWebhookPublisher(),  # type: ignore[arg-type]
        webhook_configs=[{"url": "https://example.com/webhook", "secret": "sec123"}],
    )

    project_id = uuid4()
    event = NotificationEvent(
        kind=NotificationKind.RUN_COMPLETED,
        project_id=project_id,
        title="Run Completed",
        message="Cycle 1 completed successfully",
        payload={"cycle": 1, "verdict": "pass"},
    )

    results = await service.dispatch(event)
    assert results["desktop"] is True
    assert results["webhooks"] == [True]
    assert len(dispatched_desktop) == 1
    assert len(dispatched_webhooks) == 1
    assert dispatched_webhooks[0][0] == "https://example.com/webhook"
    assert dispatched_webhooks[0][1] == "sec123"


@pytest.mark.asyncio
async def test_notification_service_desktop_disabled() -> None:
    dispatched_desktop: list[NotificationEvent] = []

    class FakeDesktopNotifier:
        async def notify(self, ev: NotificationEvent) -> bool:
            dispatched_desktop.append(ev)
            return True

    service = NotificationService(
        desktop_notifier=FakeDesktopNotifier(),  # type: ignore[arg-type]
        webhook_publisher=WebhookPublisher(http_post_fn=lambda u, b, h: True),
        webhook_configs=[],
        enable_desktop=False,
    )

    event = NotificationEvent(
        kind=NotificationKind.RUN_COMPLETED,
        project_id=uuid4(),
        title="Done",
        message="done",
    )

    results = await service.dispatch(event)
    assert results["desktop"] is False
    assert len(dispatched_desktop) == 0


@pytest.mark.asyncio
async def test_notification_service_skips_empty_url_webhook() -> None:
    dispatched_webhooks: list[str] = []

    class FakeWebhookPublisher:
        async def publish(self, ev: NotificationEvent, url: str, secret: str | None = None) -> bool:
            dispatched_webhooks.append(url)
            return True

    service = NotificationService(
        desktop_notifier=DesktopNotifier(executor=lambda cmd: True, platform_override="linux"),
        webhook_publisher=FakeWebhookPublisher(),  # type: ignore[arg-type]
        webhook_configs=[{"url": "", "secret": "s"}, {"secret": "s2"}],
    )

    event = NotificationEvent(
        kind=NotificationKind.RUN_COMPLETED,
        project_id=uuid4(),
        title="Done",
        message="done",
    )

    results = await service.dispatch(event)
    assert results["webhooks"] == []
    assert len(dispatched_webhooks) == 0
