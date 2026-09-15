"""Framework-neutral readiness probes for Azure App Configuration + App Insights.

All three checks return a small JSON-friendly dict that callers can wire
into any HTTP framework's ``/health`` endpoint.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from vibey_bootstrap.tracing.decorators import traced


def _mock_enabled() -> bool:
    return os.environ.get("USE_MOCK_BOOTSTRAP", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@traced(operation="health.check_app_config_health", alert_on_error="warn")
def check_app_config_health() -> dict[str, Any]:
    """Verify Azure App Configuration is reachable and credentials are valid."""
    if _mock_enabled():
        return {"status": "ok", "mock": True}
    conn = os.environ.get("AZURE_APP_CONFIGURATION_CONNECTION_STRING", "").strip()
    endpoint = os.environ.get("AZURE_APPCONFIG_ENDPOINT", "").strip()
    if not conn and not endpoint:
        return {"status": "not_configured"}
    try:
        from azure.appconfiguration import (
            AzureAppConfigurationClient,  # type: ignore[import-not-found]
        )
        from azure.identity import DefaultAzureCredential  # type: ignore[import-not-found]
    except ImportError:
        return {"status": "error", "message": "azure-appconfiguration not installed"}
    try:
        if conn:
            client = AzureAppConfigurationClient.from_connection_string(conn)
        else:
            client = AzureAppConfigurationClient(endpoint, DefaultAzureCredential())
        # A readiness probe only needs to prove the endpoint answers and the
        # credential is accepted. ``list_configuration_settings`` returns a lazy
        # pager, so ``next(..., None)`` issues exactly one request and stops —
        # unlike the provider's ``load()``, which pulls every setting and
        # resolves Key Vault references on every probe.
        next(iter(client.list_configuration_settings()), None)
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc)[:200]}


@traced(operation="health.check_app_insights_health", alert_on_error="warn")
def check_app_insights_health() -> dict[str, Any]:
    """Verify ``APPLICATIONINSIGHTS_CONNECTION_STRING`` is set.

    No live API call — bootstrap validates the string at startup; this probe
    is a fast readiness check, not a synthetic ping.
    """
    if _mock_enabled():
        return {"status": "ok", "mock": True}
    conn = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "").strip()
    if not conn:
        return {"status": "not_configured"}
    return {"status": "ok"}


@traced(operation="health.check_app_insights_logging", alert_on_error="warn")
def check_app_insights_logging() -> dict[str, Any]:
    """Verify an Azure Monitor logging handler was attached by bootstrap."""
    if _mock_enabled():
        return {"status": "ok", "mock": True}
    conn = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "").strip()
    if not conn:
        return {"status": "not_configured"}

    needles = ("azure", "monitor", "opentelemetry", "appinsights")

    def matches(handler: logging.Handler) -> str | None:
        cls = type(handler)
        identifier = f"{cls.__module__}.{cls.__name__}".lower()
        if any(needle in identifier for needle in needles):
            return f"{cls.__module__}.{cls.__name__}"
        return None

    root = logging.getLogger()
    for handler in root.handlers:
        hit = matches(handler)
        if hit:
            return {"status": "ok", "handler": hit}

    for name, logger_obj in logging.Logger.manager.loggerDict.items():
        if not isinstance(logger_obj, logging.Logger):
            continue
        for handler in logger_obj.handlers:
            hit = matches(handler)
            if hit:
                return {"status": "ok", "handler": hit}

    return {
        "status": "error",
        "message": (
            "No Azure Monitor logging handler attached to root logger. "
            "Ensure ensure_bootstrap() is called before any logging operations."
        ),
    }


__all__ = [
    "check_app_config_health",
    "check_app_insights_health",
    "check_app_insights_logging",
]
