# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Service Bus message-lock management.

``AutoLockRenewer`` defaults are conservative; this wrapper bounds its
lifetime and ensures ``.close()`` is called on every path. Swallows
construction failures — the renewer is a defense against long-running
handlers exceeding the lock duration, not a correctness gate.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from vibey_bootstrap.counters import bump_counter

DEFAULT_MAX_LOCK_RENEWAL_SECONDS = 3600  # 1 hour — covers the longest AI-inclusive pipeline

_logger = logging.getLogger(__name__)


def _new_auto_lock_renewer() -> Any:
    try:
        from azure.servicebus import AutoLockRenewer  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "sb_lock requires the `servicebus` extra: pip install vibey-bootstrap[servicebus]"
        ) from exc
    return AutoLockRenewer()


@contextmanager
def lock_for_process(
    receiver: Any,
    msg: Any,
    *,
    max_lock_renewal_seconds: int = DEFAULT_MAX_LOCK_RENEWAL_SECONDS,
) -> Generator[None, None, None]:
    """Register the message with an AutoLockRenewer for the block's duration."""
    renewer: Any = None
    try:
        renewer = _new_auto_lock_renewer()
        renewer.register(
            receiver,
            msg,
            max_lock_renewal_duration=max_lock_renewal_seconds,
        )
        bump_counter("sb_lock.renewer_started")
    except Exception:
        # Construction failure: the renewer is defensive — let processing
        # continue without it. The broker will redeliver if the lock expires.
        bump_counter("sb_lock.renewer_construction_failed")
        _logger.warning(
            "lock_for_process: AutoLockRenewer setup failed; proceeding without renewal",
            exc_info=True,
        )
        renewer = None
    try:
        yield
    finally:
        if renewer is not None:
            try:
                renewer.close()
            except Exception:
                bump_counter("sb_lock.close_failed")
                _logger.warning("lock_for_process: renewer.close() raised", exc_info=True)


class ManagedLock:
    """OO variant of :func:`lock_for_process`.

    Useful when callers need to extend the lock explicitly across multi-stage
    pipelines. Supports the context-manager protocol too.
    """

    def __init__(
        self,
        receiver: Any,
        msg: Any,
        *,
        max_lock_renewal_seconds: int = DEFAULT_MAX_LOCK_RENEWAL_SECONDS,
    ) -> None:
        self._receiver = receiver
        self._msg = msg
        self._max = max_lock_renewal_seconds
        self._renewer: Any = None

    def start(self) -> None:
        if self._renewer is not None:
            return
        try:
            self._renewer = _new_auto_lock_renewer()
            self._renewer.register(
                self._receiver,
                self._msg,
                max_lock_renewal_duration=self._max,
            )
            bump_counter("sb_lock.renewer_started")
        except Exception:
            bump_counter("sb_lock.renewer_construction_failed")
            _logger.warning("ManagedLock.start: AutoLockRenewer setup failed", exc_info=True)
            self._renewer = None

    def close(self) -> None:
        if self._renewer is None:
            return
        try:
            self._renewer.close()
        except Exception:
            bump_counter("sb_lock.close_failed")
            _logger.warning("ManagedLock.close: renewer.close() raised", exc_info=True)
        finally:
            self._renewer = None

    def __enter__(self) -> ManagedLock:
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


__all__ = [
    "DEFAULT_MAX_LOCK_RENEWAL_SECONDS",
    "ManagedLock",
    "lock_for_process",
]
