"""v2.1 JSON log formatter — one JSON object per record.

Distinct from :class:`ExtraFieldsFormatter` (human-readable ``key=repr(value)``
text). ``JsonLogFormatter`` renders a single-line JSON document suitable for
remote ingestion (Sumo Logic, etc.). It reuses the same reserved-key filter and
secret-masking primitives so structured ``extra={}`` fields are emitted as JSON
fields with secrets redacted.

The formatter never raises: a serialization failure falls back to a minimal
``{"level", "logger", "message"}`` document so a logging call can never crash
the caller.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from vibey_bootstrap.logging.formatter import _STDLIB_LOG_RECORD_KEYS
from vibey_bootstrap.logging.masking import mask_secrets_in_dict, safe_json_dumps


def _dumps(payload: dict[str, Any], *, ensure_ascii: bool) -> str:
    try:
        return json.dumps(payload, default=repr, ensure_ascii=ensure_ascii)
    except Exception:
        return safe_json_dumps(payload)


class JsonLogFormatter(logging.Formatter):
    """Render a log record as a single line of JSON.

    Emitted fields: ``timestamp`` (ISO-8601 UTC), ``level``, ``logger``,
    ``message``, ``exception`` (only when ``exc_info`` is present), plus every
    non-reserved ``extra={}`` field (correlation IDs included, since
    :class:`CorrelationFilter` attaches them as record attributes). Extra fields
    are passed through :func:`mask_secrets_in_dict` so secret-keyed values are
    redacted to ``***``.
    """

    def __init__(self, *, ensure_ascii: bool = False, mask_extras: bool = True) -> None:
        super().__init__()
        self._ensure_ascii = ensure_ascii
        self._mask_extras = mask_extras

    def format(self, record: logging.LogRecord) -> str:
        try:
            return _dumps(self._record_to_dict(record), ensure_ascii=self._ensure_ascii)
        except Exception:
            # Last-resort minimal document — never raise from a formatter.
            try:
                return _dumps(
                    {
                        "level": getattr(record, "levelname", "ERROR"),
                        "logger": getattr(record, "name", "unknown"),
                        "message": record.getMessage(),
                    },
                    ensure_ascii=self._ensure_ascii,
                )
            except Exception:
                return '{"level":"ERROR","message":"<unformattable log record>"}'

    def _record_to_dict(self, record: logging.LogRecord) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extras: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in _STDLIB_LOG_RECORD_KEYS or key.startswith("_"):
                continue
            extras[key] = value

        if extras:
            if self._mask_extras:
                extras = mask_secrets_in_dict(extras)
            payload.update(extras)

        return payload
