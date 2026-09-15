"""v1-compatible wrappers and helpers.

``ensure_bootstrap()`` is the lazy idempotent entry-point most apps want;
``load_local_settings()`` mirrors the Azure Functions ``local.settings.json``
convention for ergonomic dev setups.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from vibey_bootstrap.services.bootstrap_logging import get_bootstrap_logger

_bootstrap_initialized: bool = False


def _mock_bootstrap_enabled() -> bool:
    raw = os.environ.get("USE_MOCK_BOOTSTRAP", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def bootstrap_initialized() -> bool:
    """Process-local state probe — useful for /api/health/ready endpoints."""
    return _bootstrap_initialized


def ensure_bootstrap() -> None:
    """Lazy idempotent wrapper around v1 ``initialize_application``.

    Short-circuits when ``USE_MOCK_BOOTSTRAP`` is truthy (sets the
    initialized flag and returns without contacting Azure). On real
    bootstrap, calls v1 ``initialize_application()`` and sets the flag.
    Re-raises on failure after logging at ERROR with traceback.
    """
    global _bootstrap_initialized
    if _bootstrap_initialized:
        return
    logger = get_bootstrap_logger(__name__)
    if _mock_bootstrap_enabled():
        logger.info("Bootstrap mock mode active; skipping Azure connections")
        _bootstrap_initialized = True
        return
    try:
        from vibey_bootstrap.services.application_bootstrap import initialize_application

        initialize_application()
        _bootstrap_initialized = True
    except Exception:
        logger.error("Bootstrap initialization failed", exc_info=True)
        raise


def load_local_settings(path: str | Path = "local.settings.json") -> int:
    """Load env vars from an Azure-Functions-style ``local.settings.json``.

    Behavior:
    - Missing file: silent, returns 0.
    - Keys starting with ``_`` are documentation sentinels; skipped.
    - Never overrides an existing ``os.environ`` entry.
    - JSON / OS errors are logged at WARNING and return 0.
    """
    p = Path(path)
    if not p.exists():
        return 0
    logger = logging.getLogger(__name__)
    try:
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load local settings from %s: %s", path, exc)
        return 0
    values = data.get("Values") if isinstance(data, dict) else None
    if not isinstance(values, dict):
        return 0
    loaded = 0
    for key, value in values.items():
        if not isinstance(key, str) or key.startswith("_"):
            continue
        if key in os.environ:
            continue
        try:
            os.environ[key] = str(value)
            loaded += 1
        except Exception:
            continue
    return loaded


def _reset_bootstrap_state() -> None:
    """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError(
            "_reset_bootstrap_state is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1"
        )
    global _bootstrap_initialized
    _bootstrap_initialized = False


__all__: list[Any] = [
    "bootstrap_initialized",
    "ensure_bootstrap",
    "load_local_settings",
]
