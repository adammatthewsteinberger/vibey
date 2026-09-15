"""AKS runtime helpers — graceful shutdown, build info, probes, pod context."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import threading
from collections.abc import Callable
from typing import Any

from vibey_bootstrap.counters import counter_snapshot

_logger = logging.getLogger(__name__)


def install_sigterm_handler(stop_event: threading.Event) -> None:
    """Register SIGTERM handler that sets *stop_event* for graceful drain."""

    def _handler(signum: int, frame: Any) -> None:
        _logger.info("SIGTERM received — setting stop event")
        stop_event.set()

    signal.signal(signal.SIGTERM, _handler)


def setup_async_sigterm_handler() -> asyncio.Event:
    """Return an asyncio.Event set on SIGTERM."""
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _handler() -> None:
        _logger.info("SIGTERM received — setting async stop event")
        stop.set()

    loop.add_signal_handler(signal.SIGTERM, _handler)
    return stop


def build_info() -> dict[str, str | None]:
    """Return version/build metadata from downward-API or CI env vars."""
    return {
        "version": os.environ.get("BUILD_VERSION") or os.environ.get("APP_VERSION"),
        "git_sha": os.environ.get("GIT_SHA"),
        "build_time": os.environ.get("BUILD_TIME"),
        "image_tag": os.environ.get("IMAGE_TAG"),
        "pod_name": os.environ.get("POD_NAME"),
        "pod_namespace": os.environ.get("POD_NAMESPACE"),
        "node_name": os.environ.get("NODE_NAME"),
    }


def keda_metric_value(name: str = "queue_depth") -> float:
    """Scalar metric for KEDA metrics-api scaler (from counters snapshot)."""
    snap = counter_snapshot()
    return float(snap.get(name, 0))


def mount_build_info_route(app: Any, path: str = "/api/version") -> None:
    """Mount a FastAPI route returning :func:`build_info`."""

    @app.get(path)
    def _version() -> dict[str, str | None]:
        return build_info()


def pod_context_extra() -> dict[str, str | None]:
    """Correlation/log extras from Kubernetes downward API env vars."""
    return {
        "pod_name": os.environ.get("POD_NAME"),
        "pod_namespace": os.environ.get("POD_NAMESPACE"),
        "node_name": os.environ.get("NODE_NAME"),
    }


__all__ = [
    "build_info",
    "install_sigterm_handler",
    "keda_metric_value",
    "mount_build_info_route",
    "pod_context_extra",
    "setup_async_sigterm_handler",
]
