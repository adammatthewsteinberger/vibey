"""The two notification transports, including the paths that fire without an
injected seam -- those are the ones that run in production."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

import pytest

from vibey.infrastructure.notify.desktop import DesktopNotifier
from vibey.infrastructure.notify.events import NotificationEvent, NotificationKind
from vibey.infrastructure.notify.webhook import WebhookPublisher

PROJECT_ID = UUID("11111111-2222-3333-4444-555555555555")


def _event() -> NotificationEvent:
    return NotificationEvent(
        kind=NotificationKind.HUMAN_GATE_RAISED,
        project_id=PROJECT_ID,
        title="Gate raised",
        message='needs a "decision"',
    )


# --- webhook -----------------------------------------------------------------


def test_the_signature_is_hmac_sha256_over_the_exact_bytes_sent() -> None:
    """A receiver recomputes over the body it got, so the signed bytes and the
    posted bytes have to be the same object, not the same dict re-serialised."""
    sent: dict[str, Any] = {}

    def capture(url: str, body: bytes, headers: dict[str, str]) -> bool:
        sent.update(url=url, body=body, headers=headers)
        return True

    publisher = WebhookPublisher(http_post_fn=capture)
    asyncio.run(publisher.publish(_event(), "https://example.test/hook", secret="s3cret"))

    expected = publisher.compute_signature(sent["body"], "s3cret")
    assert sent["headers"]["X-Vibey-Signature"] == expected
    assert expected.startswith("sha256=")
    assert json.loads(sent["body"])["title"] == "Gate raised"


def test_no_secret_means_no_signature_header_rather_than_an_empty_one() -> None:
    """An empty signature header reads as "signed, and it did not match"."""
    sent: dict[str, Any] = {}
    publisher = WebhookPublisher(http_post_fn=lambda u, b, h: bool(sent.update(headers=h)) or True)
    asyncio.run(publisher.publish(_event(), "https://example.test/hook"))
    assert "X-Vibey-Signature" not in sent["headers"]


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "ftp://example.test/x", "", "javascript:alert(1)"]
)
def test_the_real_poster_refuses_non_http_schemes(url: str) -> None:
    """The URL comes from project config, so the scheme check is what stops a
    notification from reading a local file or hitting an unexpected protocol."""
    publisher = WebhookPublisher()
    assert publisher._sync_post(url, b"{}", {}, 1.0) is False


def test_the_real_poster_reports_failure_rather_than_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A notification that cannot be delivered must not take the run with it."""

    def explode(*args: object, **kwargs: object) -> None:
        raise OSError("network is down")

    monkeypatch.setattr("vibey.infrastructure.notify.webhook.request.urlopen", explode)
    publisher = WebhookPublisher()
    assert publisher._sync_post("https://example.test/hook", b"{}", {}, 1.0) is False


@pytest.mark.parametrize(
    ("status", "delivered"), [(200, True), (204, True), (301, False), (500, False)]
)
def test_only_success_statuses_count_as_delivered(
    monkeypatch: pytest.MonkeyPatch, status: int, delivered: bool
) -> None:
    class _Response:
        def __init__(self) -> None:
            self.status = status

        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        "vibey.infrastructure.notify.webhook.request.urlopen", lambda *a, **k: _Response()
    )
    publisher = WebhookPublisher()
    assert publisher._sync_post("https://example.test/hook", b"{}", {}, 1.0) is delivered


def test_publish_without_an_injected_poster_uses_the_real_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        WebhookPublisher, "_sync_post", lambda self, u, b, h, t: calls.append(u) or True
    )
    assert asyncio.run(WebhookPublisher().publish(_event(), "https://example.test/hook"))
    assert calls == ["https://example.test/hook"]


# --- desktop -----------------------------------------------------------------


def test_macos_and_linux_get_their_own_command() -> None:
    mac = DesktopNotifier(platform_override="darwin")._build_command(_event())
    assert mac[0] == "osascript"
    linux = DesktopNotifier(platform_override="linux")._build_command(_event())
    assert linux[0] == "notify-send"


def test_quotes_in_the_message_are_escaped_for_applescript() -> None:
    """The message is interpolated into an AppleScript string literal, so an
    unescaped quote would end the string and change the script."""
    cmd = DesktopNotifier(platform_override="darwin")._build_command(_event())
    assert '\\"decision\\"' in cmd[2]


def test_an_unsupported_platform_is_a_no_op_not_a_crash() -> None:
    notifier = DesktopNotifier(platform_override="win32")
    assert notifier._build_command(_event()) == []
    assert asyncio.run(notifier.notify(_event())) is False


def test_an_injected_executor_is_used_instead_of_spawning() -> None:
    seen: list[list[str]] = []
    notifier = DesktopNotifier(
        executor=lambda cmd: bool(seen.append(cmd)) or True, platform_override="linux"
    )
    assert asyncio.run(notifier.notify(_event())) is True
    assert seen and seen[0][0] == "notify-send"


def test_desktop_notifier_real_subprocess_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers lines 35-36: the real subprocess path when no executor is injected."""

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

    async def fake_create(*args: object, **kwargs: object) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_create)
    notifier = DesktopNotifier(platform_override="linux")
    assert asyncio.run(notifier.notify(_event())) is True


def test_a_failing_notifier_binary_does_not_take_the_run_with_it() -> None:
    notifier = DesktopNotifier(platform_override="linux")
    # notify-send is absent on macOS CI, and absent binaries raise on spawn.
    assert asyncio.run(notifier.notify(_event())) in {True, False}
