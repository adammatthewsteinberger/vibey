"""Local rotating-file logging transport — stdlib only, no extra required.

``make_file_handler()`` builds a :class:`logging.handlers.RotatingFileHandler`
(size-based rotation, default) or :class:`logging.handlers.TimedRotatingFileHandler`
(time-based rotation) and attaches ``JsonLogFormatter`` + ``CorrelationFilter`` so
every on-disk record carries structured fields and a correlation id.

Design guarantees:
- **No extra** — pure stdlib, always available.
- **Path-safe** — the log file path is validated against an allowed root via
  :func:`vibey_bootstrap.path_safety.confine_to_root`; a misconfigured
  ``FILE_LOG_PATH`` that escapes the root is rejected with a warning and the
  factory returns ``None`` (soft no-op).
- **Parent dir auto-created** — ``os.makedirs(exist_ok=True)`` at handler
  construction; file permissions default to ``0o640``.
- **Never raises** — disk-full / permission errors route through
  ``logging.Handler.handleError``; they do not propagate to the caller.
- **Counters** — a thin ``_CountingFileHandler`` wrapper bumps
  ``file.transport.records`` on each successful ``emit`` and
  ``file.transport.error`` via ``handleError``.
- **Factory returns ``None``** when ``FILE_LOG_PATH`` is unset.

Environment variables
---------------------
``FILE_LOG_PATH``
    Absolute (or ``~``-relative) path to the log file. **Required** to enable
    the transport; when unset the factory returns ``None``.

``FILE_LOG_ROOT``
    Allowed root directory. The resolved ``FILE_LOG_PATH`` must be a descendant
    of this directory. Defaults to the parent directory of ``FILE_LOG_PATH`` when
    unset (i.e. the path is self-rooted — any path is accepted as long as it is
    canonical). Set this to e.g. ``/var/log/app`` to enforce a confinement zone.

``FILE_LOG_ROTATION``
    ``size`` (default) or ``time``. Selects ``RotatingFileHandler`` vs
    ``TimedRotatingFileHandler``.

``FILE_LOG_MAX_BYTES``
    Maximum file size before rotation (size-based mode only). Default ``52428800``
    (50 MiB).

``FILE_LOG_BACKUP_COUNT``
    Number of backup files to keep after rotation. Default ``5``.

``FILE_LOG_WHEN``
    Rotation interval for time-based mode (e.g. ``midnight``, ``h``, ``d``).
    Default ``midnight``.

``FILE_LOG_ENCODING``
    File encoding. Default ``utf-8``.

Counters
--------
``file.transport.records``
    Incremented once per successfully formatted and written log record.

``file.transport.error``
    Incremented once per ``handleError`` call (disk-full, permission denied, …).
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import fail_open_env, optional_env
from vibey_bootstrap.logging.correlation import CorrelationFilter
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter

_COUNTER_RECORDS = "file.transport.records"
_COUNTER_ERROR = "file.transport.error"

_DEFAULT_MAX_BYTES = 50 * 1024 * 1024  # 50 MiB
_DEFAULT_BACKUP_COUNT = 5
_DEFAULT_WHEN = "midnight"
_DEFAULT_ENCODING = "utf-8"

_log = logging.getLogger(__name__)


class _CountingFileHandler(logging.Handler):
    """Wraps a stdlib rotating-file handler to track per-record counters.

    ``emit`` delegates to the inner handler and bumps ``file.transport.records``
    on success. ``handleError`` bumps ``file.transport.error`` before delegating
    to the inner handler's error-handling path so failures are visible in the
    counter snapshot without raising.

    All other ``logging.Handler`` methods (``flush``, ``close``, ``setFormatter``,
    ``setLevel``, ``addFilter``) delegate to the inner handler so the transport
    registry's enable/disable cycle works correctly.
    """

    def __init__(self, inner: logging.Handler) -> None:
        super().__init__()
        self._inner = inner
        # Mirror formatter, filters, and level so the registry-owned handler
        # behaves identically to the inner handler from the root logger's POV.
        self.setFormatter(inner.formatter)
        self.setLevel(inner.level)
        for f in list(inner.filters):
            self.addFilter(f)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._inner.emit(record)
            bump_counter(_COUNTER_RECORDS)
        except Exception:
            self.handleError(record)

    def handleError(self, record: logging.LogRecord) -> None:  # noqa: N802
        bump_counter(_COUNTER_ERROR)
        # Delegate to inner handler's error path (logs to sys.stderr by default).
        try:
            self._inner.handleError(record)
        except Exception:
            pass

    def flush(self) -> None:
        try:
            self._inner.flush()
        except Exception:
            pass

    def close(self) -> None:
        try:
            self._inner.close()
        except Exception:
            pass
        super().close()


def make_file_handler() -> logging.Handler | None:
    """Build a rotating-file handler from environment configuration.

    Returns ``None`` (transport stays disabled / soft no-op) when:

    - ``FILE_LOG_PATH`` is unset.
    - The resolved path escapes the configured ``FILE_LOG_ROOT``.
    - The parent directory cannot be created (e.g. permission denied) — logged
      as a warning, no exception propagated.

    On success returns a ``_CountingFileHandler`` wrapping either a
    :class:`~logging.handlers.RotatingFileHandler` (size-based, default) or a
    :class:`~logging.handlers.TimedRotatingFileHandler` (time-based), both
    formatted with ``JsonLogFormatter`` and ``CorrelationFilter``.
    """
    raw_path = fail_open_env("FILE_LOG_PATH")
    if not raw_path:
        return None

    # --- path safety ---------------------------------------------------
    # Determine the allowed root. When FILE_LOG_ROOT is unset we use the
    # *parent* of the requested log file, which effectively allows any path
    # (the file is always its own child). Operators should set FILE_LOG_ROOT
    # to restrict the confinement zone (e.g. /var/log/app).
    raw_root = fail_open_env("FILE_LOG_ROOT")
    if raw_root:
        allowed_root: str | Path = raw_root
    else:
        # Default: self-rooted — parent of the requested path. We expand the
        # user-home tilde before taking the parent so ~/ paths work correctly.
        allowed_root = Path(raw_path).expanduser().parent

    try:
        from vibey_bootstrap.path_safety import confine_to_root

        safe_path = confine_to_root(raw_path, allowed_root=allowed_root)
    except ValueError as exc:
        _log.warning(
            "file transport disabled: FILE_LOG_PATH failed path-safety check — %s",
            exc,
            extra={"component": "file.transport"},
        )
        return None

    # --- parent directory ----------------------------------------------
    try:
        os.makedirs(safe_path.parent, mode=0o750, exist_ok=True)
    except OSError as exc:
        _log.warning(
            "file transport disabled: could not create log directory %r — %s",
            str(safe_path.parent),
            exc,
            extra={"component": "file.transport"},
        )
        return None

    # --- configuration -------------------------------------------------
    rotation = optional_env("FILE_LOG_ROTATION", default="size").lower()
    backup_count = _int_env("FILE_LOG_BACKUP_COUNT", _DEFAULT_BACKUP_COUNT)
    encoding = optional_env("FILE_LOG_ENCODING", default=_DEFAULT_ENCODING) or _DEFAULT_ENCODING

    # --- build stdlib handler ------------------------------------------
    try:
        if rotation == "time":
            when = optional_env("FILE_LOG_WHEN", default=_DEFAULT_WHEN) or _DEFAULT_WHEN
            inner: logging.Handler = logging.handlers.TimedRotatingFileHandler(
                filename=str(safe_path),
                when=when,
                backupCount=backup_count,
                encoding=encoding,
                delay=False,
            )
        else:
            # Default: size-based rotation.
            max_bytes = _int_env("FILE_LOG_MAX_BYTES", _DEFAULT_MAX_BYTES)
            inner = logging.handlers.RotatingFileHandler(
                filename=str(safe_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=encoding,
                delay=False,
            )
    except OSError as exc:
        _log.warning(
            "file transport disabled: could not open log file %r — %s",
            str(safe_path),
            exc,
            extra={"component": "file.transport"},
        )
        return None

    # --- formatter + correlation filter --------------------------------
    inner.setFormatter(JsonLogFormatter())
    inner.addFilter(CorrelationFilter())

    # --- set file permissions on the newly created log file ------------
    # RotatingFileHandler / TimedRotatingFileHandler open the file in the
    # constructor (delay=False), so the file exists at this point.
    try:
        os.chmod(str(safe_path), 0o640)
    except OSError:
        pass  # Non-fatal — permissions may already be controlled by the OS/container.

    return _CountingFileHandler(inner)


def _int_env(name: str, default: int) -> int:
    raw = optional_env(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


__all__ = ["make_file_handler"]
