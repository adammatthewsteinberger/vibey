"""Generic external-resource renewal loop pattern.

Generalized from the Microsoft Graph webhook subscription lifecycle but
applicable to any resource that has an expiration and might be reaped
upstream before its declared lifetime ends.

Sleep slices in the renewal loop are bounded at 5 s so SIGTERM lands
promptly — Kubernetes default grace period is 30 s.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.tracing.decorators import traced

R = TypeVar("R")
_logger = logging.getLogger(__name__)
_MAX_SLEEP_SLICE_SECONDS = 5.0


@dataclass
class RenewableResource(Generic[R]):
    id: str
    handle: R
    expires_at: float | None = None


class SubscriptionGone(Exception):
    """The upstream resource is no longer there — caller should mint a fresh one."""


def _fire_critical_alert(operation: str, exc: BaseException, dedup_suffix: str) -> None:
    try:
        from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

        alert_dev_team(
            AlertSeverity.CRITICAL,
            subject=f"{operation}: {dedup_suffix}",
            context={
                "operation": operation,
                "exception_type": type(exc).__name__,
                "error": str(exc)[:500],
            },
            dedup_key=f"{operation}:{dedup_suffix}",
        )
    except Exception:
        pass


@traced(operation="subscription.ensure_resource", alert_on_error="error")
def ensure_resource(
    *,
    operation: str,
    list_fn: Callable[[], list[RenewableResource[R]]],
    create_fn: Callable[[], RenewableResource[R]],
    match_fn: Callable[[RenewableResource[R]], bool] = lambda r: True,
) -> RenewableResource[R]:
    """Idempotent find-or-create.

    1. Iterate the existing resources via ``list_fn``; return the first one
       matching ``match_fn``.
    2. Otherwise, mint a new one via ``create_fn``.
    """
    existing = list_fn() or []
    for resource in existing:
        if match_fn(resource):
            _logger.info(
                "resource found",
                extra={
                    "operation": operation,
                    "resource_id": resource.id,
                },
            )
            return resource
    created = create_fn()
    _logger.info(
        "resource created",
        extra={"operation": operation, "resource_id": created.id},
    )
    return created


def renewal_loop(
    resource: RenewableResource[R],
    *,
    stop_event: threading.Event,
    renew_fn: Callable[[str], RenewableResource[R]],
    recreate_fn: Callable[[], RenewableResource[R]] | None = None,
    interval_seconds: float,
    operation: str,
    gone_exception: type[BaseException] = SubscriptionGone,
    counter_namespace: str = "subscription",
) -> None:
    """Long-running renewal thread body. Sleeps in ≤ 5 s slices."""

    def _slept_through(total: float) -> bool:
        """Sleep ``total`` seconds in ≤ 5 s slices; return True if not stopped."""
        remaining = total
        while remaining > 0:
            slice_s = min(_MAX_SLEEP_SLICE_SECONDS, remaining)
            if stop_event.wait(slice_s):
                return False
            remaining -= slice_s
        return True

    while True:
        if not _slept_through(interval_seconds):
            return
        try:
            updated = renew_fn(resource.id)
            if updated is not None:
                resource = updated
        except gone_exception as exc:
            if recreate_fn is None:
                _logger.error(
                    "%s: resource gone and no recreate handler",
                    operation,
                    exc_info=True,
                )
                _fire_critical_alert(operation, exc, "resource gone and no recreate handler")
                return
            try:
                resource = recreate_fn()
                bump_counter(f"{counter_namespace}.recreated")
                _logger.info(
                    "renewal_loop recreated resource",
                    extra={
                        "operation": operation,
                        "resource_id": resource.id,
                    },
                )
            except Exception as recreate_exc:  # noqa: BLE001
                _logger.exception("%s: recreate failed", operation)
                _fire_critical_alert(operation, recreate_exc, "recreate handler raised")
                return
        except Exception as exc:  # noqa: BLE001
            _logger.exception("%s: renewal raised", operation)
            _fire_critical_alert(operation, exc, f"renewal raised {type(exc).__name__}")
            return


__all__ = [
    "RenewableResource",
    "SubscriptionGone",
    "ensure_resource",
    "renewal_loop",
]
