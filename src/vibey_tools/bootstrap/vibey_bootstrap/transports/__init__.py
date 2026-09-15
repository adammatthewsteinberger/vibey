"""Logging transport registry — choose where logs go, toggle each independently.

A *transport* is a named factory that produces a ``logging.Handler``. Enabling a
transport builds its handler and attaches it to the root logger; disabling
removes (and closes) it. The registry is the single source of truth for what is
currently attached, so enable/disable are idempotent.

Ten transports are pre-registered:

==============  ===============================  ==============================
name            sink                             toggle env flag
==============  ===============================  ==============================
``console``     stdout ``StreamHandler``          ``CONSOLE_LOGGING_ENABLED``
``app_insights``Azure Monitor / App Insights      ``APP_INSIGHTS_LOGGING_ENABLED``
``sumo_logic``  Sumo Logic HTTP Source            ``SUMO_LOGIC_LOGGING_ENABLED``
``panther``     Panther SIEM HTTP Source          ``PANTHER_LOGGING_ENABLED``
``file``        Rotating local log file           ``FILE_LOGGING_ENABLED``
``blob``        Azure Blob Storage                ``BLOB_LOGGING_ENABLED``
``sql``         SQL database table                ``SQL_LOGGING_ENABLED``
``nosql``       NoSQL / Cosmos DB collection      ``NOSQL_LOGGING_ENABLED``
``adx``         Azure Data Explorer               ``ADX_LOGGING_ENABLED``
``event_hubs``  Azure Event Hubs                  ``EVENTHUBS_LOGGING_ENABLED``
==============  ===============================  ==============================

Typical usage::

    from vibey_bootstrap import configure_transports
    configure_transports(console=True, app_insights=False, sumo_logic=True)

``configure_transports`` resolves each sink from an explicit boolean (wins) or
the env flag (fallback). Lower-level ``register_transport`` /
``enable_transport`` / ``disable_transport`` / ``list_transports`` are available
for custom transports.

Ordering note: if you also call ``configure_logging()`` (which uses
``basicConfig(force=True)`` and *replaces* all root handlers), call it **before**
``configure_transports`` — otherwise it wipes the registry's handlers. Enable and
disable reconcile against the live root handlers so a later wipe is recovered on
the next call.
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from typing import Any

from vibey_bootstrap.logging.config import effective_log_level, env_flag

TransportFactory = Callable[[], "logging.Handler | None"]

_lock = threading.RLock()
_factories: dict[str, TransportFactory] = {}
_active: dict[str, logging.Handler] = {}

_ENV_FLAGS: dict[str, str] = {
    "console": "CONSOLE_LOGGING_ENABLED",
    "app_insights": "APP_INSIGHTS_LOGGING_ENABLED",
    "sumo_logic": "SUMO_LOGIC_LOGGING_ENABLED",
    "panther": "PANTHER_LOGGING_ENABLED",
    "file": "FILE_LOGGING_ENABLED",
    "blob": "BLOB_LOGGING_ENABLED",
    "sql": "SQL_LOGGING_ENABLED",
    "nosql": "NOSQL_LOGGING_ENABLED",
    "adx": "ADX_LOGGING_ENABLED",
    "event_hubs": "EVENTHUBS_LOGGING_ENABLED",
}
_DEFAULTS: dict[str, bool] = {
    "console": True,
    "app_insights": False,
    "sumo_logic": False,
    "panther": False,
    "file": False,
    "blob": False,
    "sql": False,
    "nosql": False,
    "adx": False,
    "event_hubs": False,
}


def register_transport(name: str, factory: TransportFactory, *, replace: bool = False) -> None:
    """Register a transport factory under ``name``.

    Raises ``ValueError`` if ``name`` is already registered and ``replace`` is
    False. Re-registering a currently-enabled transport disables it first; the
    caller must re-enable to pick up the new factory.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("transport name must be a non-empty string")
    with _lock:
        if name in _factories and not replace:
            raise ValueError(f"transport {name!r} is already registered (pass replace=True)")
        if name in _active:
            disable_transport(name)
        _factories[name] = factory


def enable_transport(name: str) -> bool:
    """Attach the transport's handler to the root logger. Idempotent.

    Returns True if a handler was added, False if the transport was already
    enabled or its factory returned ``None`` (transport unavailable).
    """
    with _lock:
        _reconcile()
        factory = _factories.get(name)
        if factory is None:
            raise ValueError(f"transport {name!r} is not registered")
        if name in _active:
            return False
        try:
            handler = factory()
        except Exception:
            logging.getLogger(__name__).debug("transport %r factory raised", name, exc_info=True)
            return False
        if handler is None:
            return False
        handler._ab_transport = name  # type: ignore[attr-defined]
        logging.getLogger().addHandler(handler)
        _active[name] = handler
        return True


def disable_transport(name: str) -> bool:
    """Detach (and close) the transport's handler. Idempotent.

    Returns True if a handler was removed, False if it was not enabled.
    """
    with _lock:
        handler = _active.pop(name, None)
        if handler is None:
            return False
        try:
            logging.getLogger().removeHandler(handler)
        finally:
            try:
                handler.close()
            except Exception:
                pass
        return True


def list_transports() -> dict[str, dict[str, Any]]:
    """Return ``{name: {"registered": True, "enabled": bool}}`` for all transports."""
    with _lock:
        _reconcile()
        return {name: {"registered": True, "enabled": name in _active} for name in _factories}


def configure_transports(
    *,
    console: bool | None = None,
    app_insights: bool | None = None,
    sumo_logic: bool | None = None,
    panther: bool | None = None,
    file: bool | None = None,
    blob: bool | None = None,
    sql: bool | None = None,
    nosql: bool | None = None,
    adx: bool | None = None,
    event_hubs: bool | None = None,
) -> None:
    """Enable/disable the ten built-in transports. Idempotent and re-runnable.

    For each sink, an explicit boolean wins; otherwise the per-transport env flag
    is consulted (defaults: console on, all others off).

    ==============  ==============================
    parameter       env flag
    ==============  ==============================
    console         CONSOLE_LOGGING_ENABLED
    app_insights    APP_INSIGHTS_LOGGING_ENABLED
    sumo_logic      SUMO_LOGIC_LOGGING_ENABLED
    panther         PANTHER_LOGGING_ENABLED
    file            FILE_LOGGING_ENABLED
    blob            BLOB_LOGGING_ENABLED
    sql             SQL_LOGGING_ENABLED
    nosql           NOSQL_LOGGING_ENABLED
    ==============  ==============================

    Also sets the root logger to ``effective_log_level()`` so enabled transports
    actually receive records (the stdlib root default of WARNING would otherwise
    drop INFO/DEBUG). Honors the ``LOG_LEVEL`` / ``DEBUG_LOGGING_ENABLED`` env
    contract shared with ``configure_logging()``.
    """
    logging.getLogger().setLevel(effective_log_level())
    params = {
        "console": console,
        "app_insights": app_insights,
        "sumo_logic": sumo_logic,
        "panther": panther,
        "file": file,
        "blob": blob,
        "sql": sql,
        "nosql": nosql,
        "adx": adx,
        "event_hubs": event_hubs,
    }
    for name, param in params.items():
        if _resolve(param, _ENV_FLAGS[name], _DEFAULTS[name]):
            enable_transport(name)
        else:
            disable_transport(name)


def _resolve(param: bool | None, env_name: str, default: bool) -> bool:
    if param is not None:
        return param
    return env_flag(env_name, default=default)


def _reconcile() -> None:
    """Drop ``_active`` entries whose handler is no longer attached to root.

    Defends against ``configure_logging()``'s ``basicConfig(force=True)`` wiping
    handlers out from under the registry — a subsequent enable then re-adds.
    """
    root_handlers = set(logging.getLogger().handlers)
    for name in list(_active):
        if _active[name] not in root_handlers:
            del _active[name]


def _reset_transports() -> None:
    """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("_reset_transports is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1")
    with _lock:
        for name in list(_active):
            disable_transport(name)
        _factories.clear()
        _active.clear()
        _register_builtins()


from vibey_bootstrap.transports.builtins import _register_builtins  # noqa: E402

_register_builtins()


__all__ = [
    "TransportFactory",
    "configure_transports",
    "disable_transport",
    "enable_transport",
    "list_transports",
    "register_transport",
]
