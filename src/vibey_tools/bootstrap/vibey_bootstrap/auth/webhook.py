"""Microsoft-Graph-style webhook authentication helpers.

Three primitives that compose into a full webhook handler:

- :class:`WebhookDedup`: in-process dedup for replayed notifications
  (Graph retries on 5xx, network glitches, subscription renewal mismatches).
- :func:`verify_webhook_client_state`: constant-time clientState check.
- :func:`validation_token_handshake`: the subscription-creation handshake.

:func:`install_graph_webhook_route` wires the four into a FastAPI route with
the right ordering: validation token → rate limit → JSON parse → per-entry
clientState → dedup → background dispatch → 202 Accepted.

Note: this module deliberately does NOT use ``from __future__ import
annotations``. FastAPI resolves type hints at route-registration time via
``typing.get_type_hints``; stringified annotations referring to lazily-
imported names (``Request``, ``BackgroundTasks``) can't be resolved by
``get_type_hints`` outside the function's closure, and FastAPI then treats
them as query parameters (422 errors).
"""

import logging
import os
import threading
import time
from collections.abc import Callable
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import ConfigurationError
from vibey_bootstrap.security import compare_secrets

_logger = logging.getLogger(__name__)

_DEFAULT_DEDUP_TTL_SECONDS = 600.0
_DEFAULT_DEDUP_MAX_ENTRIES = 4096


class WebhookDedup:
    """In-process dedup keyed on caller-supplied tuples.

    Thread-safe (single ``threading.Lock``). Entries older than ``ttl_seconds``
    are GC'd on every check; total entries capped at ``max_entries``.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float = _DEFAULT_DEDUP_TTL_SECONDS,
        max_entries: int = _DEFAULT_DEDUP_MAX_ENTRIES,
    ) -> None:
        self._ttl = float(ttl_seconds)
        self._max_entries = int(max_entries)
        self._seen: dict[tuple[str, ...], float] = {}
        self._lock = threading.Lock()

    def already_seen(self, key: tuple[str, ...]) -> bool:
        now = time.monotonic()
        cutoff = now - self._ttl
        with self._lock:
            # GC stale entries
            stale = [k for k, ts in self._seen.items() if ts < cutoff]
            for k in stale:
                self._seen.pop(k, None)
            if key in self._seen:
                return True
            self._seen[key] = now
            if len(self._seen) > self._max_entries:
                # Evict oldest first
                ordered = sorted(self._seen.items(), key=lambda kv: kv[1])
                overflow = len(ordered) - self._max_entries
                for k, _ in ordered[:overflow]:
                    self._seen.pop(k, None)
        return False

    def reset(self) -> None:
        """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
        if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
            raise RuntimeError(
                "WebhookDedup.reset is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1"
            )
        with self._lock:
            self._seen.clear()


def verify_webhook_client_state(
    received_client_state: str | None,
    *,
    env_var: str = "GRAPH_WEBHOOK_CLIENT_STATE",
) -> bool:
    """Constant-time comparison of received clientState against the configured value.

    Raises :class:`ConfigurationError` when ``env_var`` is unset — the webhook
    endpoint MUST be configured before accepting any requests.
    """
    expected = os.environ.get(env_var, "").strip()
    if not expected:
        raise ConfigurationError(f"webhook clientState env var {env_var!r} is not configured")
    return compare_secrets(received_client_state, expected)


def validation_token_handshake(validation_token: str | None) -> str | None:
    """Graph subscription-validation handshake — echo the token, or None."""
    if validation_token is None or validation_token == "":
        return None
    return validation_token


def install_graph_webhook_route(
    app: Any,
    path: str,
    *,
    background_handler: Callable[[str], None],
    rate_limit_bucket: Any | None = None,
    dedup: WebhookDedup | None = None,
    counter_namespace: str = "webhook",
) -> None:
    """Register a Graph-flavored webhook route on the FastAPI app.

    Pipeline order: validation token → rate limit → JSON parse → per-entry
    clientState → dedup → background dispatch → 202 Accepted.
    """
    try:
        from fastapi import (  # type: ignore[import-not-found]
            BackgroundTasks,
            Request,
            Response,
        )
        from fastapi.responses import PlainTextResponse  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "install_graph_webhook_route requires the `fastapi` extra: "
            "pip install vibey-bootstrap[fastapi]"
        ) from exc

    @app.post(path, include_in_schema=False)
    async def _webhook(  # type: ignore[no-untyped-def]
        request: Request,
        background_tasks: BackgroundTasks,
    ) -> Response:
        # 1. Validation-token handshake (subscription creation)
        token = validation_token_handshake(request.query_params.get("validationToken"))
        if token is not None:
            bump_counter(f"{counter_namespace}.validation_token_handshake")
            return PlainTextResponse(token, status_code=200)

        # 2. Rate limit
        if rate_limit_bucket is not None and not rate_limit_bucket.consume(1.0):
            bump_counter(f"{counter_namespace}.rate_limited")
            return Response(status_code=429)

        # 3. Parse JSON
        try:
            payload = await request.json()
        except Exception:
            return Response(status_code=400)

        # 4. Iterate `value` entries
        entries = payload.get("value", []) if isinstance(payload, dict) else []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            received_state = entry.get("clientState")
            try:
                ok = verify_webhook_client_state(received_state)
            except ConfigurationError:
                # Endpoint unconfigured — refuse all entries; respond 401 no body.
                bump_counter(f"{counter_namespace}.client_state_mismatch")
                return Response(status_code=401)
            if not ok:
                bump_counter(f"{counter_namespace}.client_state_mismatch")
                return Response(status_code=401)

            resource_data = entry.get("resourceData") or {}
            subscription_id = entry.get("subscriptionId") or ""
            message_id = resource_data.get("id", "")
            if not message_id:
                continue
            key = (str(subscription_id), str(message_id))
            if dedup is not None and dedup.already_seen(key):
                _logger.info(
                    "webhook duplicate suppressed",
                    extra={
                        "operation": "webhook.dedup_skipped",
                        "subscription_id": subscription_id,
                        "message_id": message_id,
                    },
                )
                bump_counter(f"{counter_namespace}.dedup_skipped")
                continue
            bump_counter(f"{counter_namespace}.received")
            background_tasks.add_task(background_handler, message_id)

        return Response(status_code=202)


__all__ = [
    "WebhookDedup",
    "install_graph_webhook_route",
    "validation_token_handshake",
    "verify_webhook_client_state",
]
