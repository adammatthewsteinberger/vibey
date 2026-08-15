"""Composite notification service coordinating desktop alerts and signed webhooks."""

import asyncio
from collections.abc import Sequence
from typing import Any

from vibey.infrastructure.notify.desktop import DesktopNotifier
from vibey.infrastructure.notify.events import NotificationEvent
from vibey.infrastructure.notify.webhook import WebhookPublisher


class NotificationService:
    def __init__(
        self,
        *,
        desktop_notifier: DesktopNotifier | None = None,
        webhook_publisher: WebhookPublisher | None = None,
        webhook_configs: Sequence[dict[str, Any]] | None = None,
        enable_desktop: bool = True,
    ) -> None:
        self._desktop = desktop_notifier or DesktopNotifier()
        self._webhook = webhook_publisher or WebhookPublisher()
        self._webhook_configs = list(webhook_configs or [])
        self._enable_desktop = enable_desktop

    async def dispatch(self, event: NotificationEvent) -> dict[str, Any]:
        tasks: list[asyncio.Task[Any]] = []
        if self._enable_desktop:
            tasks.append(asyncio.create_task(self._desktop.notify(event)))

        webhook_tasks: list[asyncio.Task[bool]] = []
        for cfg in self._webhook_configs:
            url = str(cfg.get("url", ""))
            secret = cfg.get("secret")
            if url:
                webhook_tasks.append(
                    asyncio.create_task(self._webhook.publish(event, url=url, secret=secret))
                )

        desktop_res = await tasks[0] if tasks else False
        webhook_res = await asyncio.gather(*webhook_tasks) if webhook_tasks else []

        return {
            "desktop": desktop_res,
            "webhooks": list(webhook_res),
        }
