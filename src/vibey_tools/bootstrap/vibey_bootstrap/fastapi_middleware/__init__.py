# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""FastAPI request-timing + alerting middleware.

Requires the ``fastapi`` extra. Import the module without it installed; only
``install_middleware`` raises ``ImportError`` if called when FastAPI isn't
present.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from typing import Any

_logger = logging.getLogger(__name__)


def install_middleware(
    app: Any,
    *,
    probe_paths: Iterable[str] = (
        "/health/live",
        "/health/ready",
        "/api/health/live",
        "/api/health/ready",
    ),
    alert_subject_prefix: str = "",
    fire_alerts: bool = True,
) -> None:
    """Register a single timing/alerting middleware on the FastAPI app.

    Probes are silent. Non-probes log at DEBUG on entry, INFO/WARNING on
    exit. 5xx and uncaught exceptions fire ERROR alerts (when ``fire_alerts``
    is True).
    """
    try:
        from fastapi import (  # type: ignore[import-not-found]  # noqa: F401
            FastAPI,
            Request,
            Response,
        )
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "install_middleware requires the `fastapi` extra: pip install vibey-bootstrap[fastapi]"
        ) from exc

    probe_set = set(probe_paths)

    @app.middleware("http")
    async def _timing_middleware(request: Any, call_next: Any) -> Any:
        path = request.url.path
        method = request.method
        is_probe = path in probe_set
        start = time.monotonic()

        if not is_probe:
            _logger.debug(
                "→ HTTP %s %s",
                method,
                path,
                extra={"operation": "http_request", "method": method, "path": path},
            )

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = round(time.monotonic() - start, 3)
            _logger.exception(
                "✗ HTTP %s %s raised %s after %ss",
                method,
                path,
                type(exc).__name__,
                elapsed,
                extra={
                    "operation": "http_request_failed",
                    "method": method,
                    "path": path,
                    "elapsed_seconds": elapsed,
                    "exception_type": type(exc).__name__,
                },
            )
            if fire_alerts:
                try:
                    from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

                    alert_dev_team(
                        AlertSeverity.ERROR,
                        subject=(
                            f"{alert_subject_prefix}HTTP {method} {path} "
                            f"crashed: {type(exc).__name__}"
                        ),
                        context={
                            "method": method,
                            "path": path,
                            "elapsed_seconds": elapsed,
                            "error": str(exc)[:500],
                        },
                        dedup_key=f"http_crash:{path}:{type(exc).__name__}",
                    )
                except Exception:
                    pass
            raise

        elapsed = round(time.monotonic() - start, 3)
        if not is_probe:
            status = response.status_code
            level = logging.WARNING if status >= 400 else logging.INFO
            _logger.log(
                level,
                "✓ HTTP %s %s → %d in %ss",
                method,
                path,
                status,
                elapsed,
                extra={
                    "operation": "http_response",
                    "method": method,
                    "path": path,
                    "status_code": status,
                    "elapsed_seconds": elapsed,
                },
            )
            if status >= 500 and fire_alerts:
                try:
                    from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

                    alert_dev_team(
                        AlertSeverity.ERROR,
                        subject=(f"{alert_subject_prefix}HTTP 5xx: {method} {path} → {status}"),
                        context={
                            "method": method,
                            "path": path,
                            "status_code": status,
                            "elapsed_seconds": elapsed,
                        },
                        dedup_key=f"http_5xx:{path}:{status}",
                    )
                except Exception:
                    pass
        return response


__all__ = ["install_middleware"]
