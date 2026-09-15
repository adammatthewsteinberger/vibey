"""Generic leader election — K8s ConfigMap lock or soft no-op."""

from __future__ import annotations

import logging
import os
import threading
from typing import Any

_logger = logging.getLogger(__name__)


class LeaderElection:
    """Simple in-process leader election using a ConfigMap name env var.

    When ``LEADER_ELECTION_CONFIGMAP`` is unset, :meth:`is_leader` always
    returns ``True`` (soft no-op for single-replica dev).
    """

    def __init__(
        self,
        *,
        configmap_name: str | None = None,
        namespace: str | None = None,
        identity: str | None = None,
        lease_seconds: int = 30,
    ) -> None:
        self._configmap = configmap_name or os.environ.get("LEADER_ELECTION_CONFIGMAP")
        self._namespace = namespace or os.environ.get("POD_NAMESPACE", "default")
        self._identity = identity or os.environ.get("POD_NAME", "local")
        self._lease_seconds = lease_seconds
        self._is_leader = False
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_leader(self) -> bool:
        if not self._configmap:
            return True
        with self._lock:
            return self._is_leader

    def start(self) -> None:
        if not self._configmap:
            self._is_leader = True
            return
        self._thread = threading.Thread(target=self._run, name="leader-election", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                acquired = self._try_acquire()
                with self._lock:
                    self._is_leader = acquired
            except Exception:
                _logger.debug("leader election cycle failed", exc_info=True)
            self._stop.wait(self._lease_seconds / 2)

    def _try_acquire(self) -> bool:
        # Production apps use the K8s API; this stub uses env-only soft lock.
        holder = os.environ.get("LEADER_HOLDER")
        if holder is None or holder == self._identity:
            os.environ["LEADER_HOLDER"] = self._identity
            return True
        return holder == self._identity


def leader_election(**kwargs: Any) -> LeaderElection:
    """Factory for :class:`LeaderElection`."""
    le = LeaderElection(**kwargs)
    le.start()
    return le


__all__ = ["LeaderElection", "leader_election"]
