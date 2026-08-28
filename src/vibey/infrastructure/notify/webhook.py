# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Webhook publisher with HMAC-SHA256 signing."""

import asyncio
import hashlib
import hmac
import json
from collections.abc import Callable
from contextlib import suppress
from urllib import request

from vibey.infrastructure.notify.events import NotificationEvent


class WebhookPublisher:
    def __init__(
        self,
        *,
        http_post_fn: Callable[[str, bytes, dict[str, str]], bool] | None = None,
    ) -> None:
        self._http_post_fn = http_post_fn

    def compute_signature(self, payload_bytes: bytes, secret: str) -> str:
        digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    async def publish(
        self,
        event: NotificationEvent,
        url: str,
        secret: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> bool:
        payload_bytes = json.dumps(event.to_dict(), sort_keys=True).encode("utf-8")
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "vibey-notifier/1.0",
        }
        if secret:
            headers["X-Vibey-Signature"] = self.compute_signature(payload_bytes, secret)

        if self._http_post_fn is not None:
            return self._http_post_fn(url, payload_bytes, headers)

        return await asyncio.to_thread(
            self._sync_post, url, payload_bytes, headers, timeout_seconds
        )

    def _sync_post(
        self,
        url: str,
        payload_bytes: bytes,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> bool:
        if not (url.startswith("http://") or url.startswith("https://")):
            return False
        with suppress(Exception):
            req = request.Request(url, data=payload_bytes, headers=headers, method="POST")
            with request.urlopen(req, timeout=timeout_seconds) as response:  # nosec B310
                return int(response.status) in {200, 201, 202, 204}
        return False
