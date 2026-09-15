"""Correlation context for structured logs.

Apps push correlation/email/request IDs via ``correlation_scope(...)``; the
``CorrelationFilter`` then automatically attaches them as record attributes so
``ExtraFieldsFormatter`` renders them on every line inside the scope.

Context vars are lazily created — apps can push any kwarg into a scope and
the filter will pick it up without registration.
"""

from __future__ import annotations

import contextvars
import logging
import uuid
from collections.abc import Generator
from contextlib import contextmanager

_DEFAULT_CONTEXT_FIELDS: tuple[str, ...] = (
    "correlation_id",
    "email_id",
    "attachment_name",
    "request_id",
    "user_id",
)

_VARS: dict[str, contextvars.ContextVar[str | None]] = {}


def _var_for(name: str) -> contextvars.ContextVar[str | None]:
    var = _VARS.get(name)
    if var is None:
        var = contextvars.ContextVar(f"vibey_bootstrap_{name}", default=None)
        _VARS[name] = var
    return var


for _name in _DEFAULT_CONTEXT_FIELDS:
    _var_for(_name)


def get_correlation_id() -> str | None:
    return _var_for("correlation_id").get()


def set_correlation_id(value: str | None) -> contextvars.Token[str | None]:
    return _var_for("correlation_id").set(value)


@contextmanager
def correlation_scope(
    correlation_id: str | None = None,
    **fields: str | None,
) -> Generator[str, None, None]:
    """Push correlation context for the duration of the with-block.

    Yields the resolved correlation_id, always a non-empty string. A fresh
    12-char uuid hex is minted when ``correlation_id`` is None. Any keyword
    argument becomes a context var (e.g. ``email_id``, ``request_id``).
    """
    resolved = correlation_id or uuid.uuid4().hex[:12]
    tokens: list[tuple[contextvars.ContextVar[str | None], contextvars.Token[str | None]]] = []
    tokens.append((_var_for("correlation_id"), _var_for("correlation_id").set(resolved)))
    for key, value in fields.items():
        if value is None:
            continue
        var = _var_for(key)
        tokens.append((var, var.set(value)))
    try:
        yield resolved
    finally:
        for var, token in reversed(tokens):
            try:
                var.reset(token)
            except Exception:
                pass


class CorrelationFilter(logging.Filter):
    """Attach every set context var as a record attribute.

    Only sets attributes the record doesn't already carry — so explicit
    ``extra={"correlation_id": "..."}`` overrides win.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            for name, var in _VARS.items():
                value = var.get()
                if value and not hasattr(record, name):
                    try:
                        record.__dict__[name] = value
                    except Exception:
                        pass
        except Exception:
            pass
        return True
