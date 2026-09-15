"""Secret/PII masking and log-injection sanitization primitives.

All public functions accept None and never raise; they are safe to call from
inside log statements at any phase of the application lifecycle.
"""

from __future__ import annotations

import json
import re
from typing import Any

_CONTROL_CHARS_FOR_LOGS = re.compile(r"[\x00-\x1f\x7f]")

_SECRET_KEY_ALLOWLIST: set[str] = {
    "authorization",
    "x-api-key",
    "client_secret",
    "api_key",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "connection_string",
    "sas_token",
    "azure_client_secret",
    "service_bus_connection_string",
    "blob_storage_connection_string",
    "azure_app_configuration_connection_string",
    "azure_openai_api_key",
    "applicationinsights_connection_string",
    "azure_subscription_key",
    "cognitive_services_key",
    "document_intelligence_key",
    "storage_account_key",
    "sas_url",
    "graph_webhook_client_state",
}

_SENSITIVE_SUBSTRINGS: tuple[str, ...] = (
    "secret",
    "password",
    "token",
    "api_key",
    "apikey",
    "connection_string",
    "client_secret",
    "authorization",
    "bearer",
)


def register_secret_keys(*names: str) -> None:
    """Extend the allowlist at runtime. Names are lowercased."""
    for name in names:
        if name:
            _SECRET_KEY_ALLOWLIST.add(name.lower())


def mask_api_key(secret: str | None) -> str:
    if not secret or len(secret) < 4:
        return "***"
    return f"***{secret[-4:]}"


def mask_bearer_token(token: str | None) -> str:
    if not token:
        return "***"
    if token.lower().startswith("bearer "):
        return "Bearer ***"
    return "***"


def sanitize_for_log(value: str | None, *, max_len: int = 256) -> str:
    """Replace control chars (\\x00-\\x1f, \\x7f) with '?' and truncate."""
    if value is None:
        return ""
    cleaned = _CONTROL_CHARS_FOR_LOGS.sub("?", value)
    if len(cleaned) > max_len:
        return cleaned[:max_len] + "...[truncated]"
    return cleaned


def mask_email_address(email: str | None) -> str:
    if not email:
        return "***"
    cleaned = _CONTROL_CHARS_FOR_LOGS.sub("", email)
    if "@" not in cleaned:
        return "***"
    local, _, domain = cleaned.partition("@")
    if not domain:
        return "***"
    if len(local) <= 2:
        return f"***@{domain}"
    return f"***{local[-2:]}@{domain}"


def content_preview(text: str | bytes, max_len: int = 500) -> str:
    if isinstance(text, bytes):
        try:
            decoded = text.decode("utf-8", errors="replace")
        except TypeError:
            return f"<bytes len={len(text)}>"
    else:
        decoded = text
    if len(decoded) > max_len:
        return decoded[:max_len] + "...[truncated]"
    return decoded


def safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, default=repr)
    except Exception:
        try:
            return repr(obj)
        except Exception:
            return "<unreprable>"


def mask_secrets_in_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Shallow copy with secret-keyed values replaced by '***'.

    A value is replaced only when truthy — empty strings, None, 0, etc. pass
    through unmodified so the caller can still see "field was empty".
    """
    out: dict[str, Any] = {}
    for key, value in d.items():
        if isinstance(key, str) and key.lower() in _SECRET_KEY_ALLOWLIST and value:
            out[key] = "***"
        else:
            out[key] = value
    return out


def _looks_sensitive(name: str) -> bool:
    if not isinstance(name, str):
        return False
    lowered = name.lower()
    return any(substr in lowered for substr in _SENSITIVE_SUBSTRINGS)


def _safe_repr(value: Any, max_len: int = 200) -> str:
    """Cheap repr that never invokes arbitrary __repr__ methods.

    Heavy objects (ReportLab stories, ORM rows, etc.) have repr methods that
    can do IO or be O(n) in object size. We render only primitives directly
    and summarize containers structurally.
    """
    try:
        if value is None or isinstance(value, (bool, int, float)):
            return repr(value)
        if isinstance(value, str):
            rendered = repr(value)
            if len(rendered) > max_len:
                return rendered[: max_len - 1] + "…"
            return rendered
        if isinstance(value, bytes):
            return f"<bytes len={len(value)}>"
        if isinstance(value, list):
            return f"<list len={len(value)}>"
        if isinstance(value, tuple):
            return f"<tuple len={len(value)}>"
        if isinstance(value, set):
            return f"<set len={len(value)}>"
        if isinstance(value, dict):
            return f"<dict len={len(value)}>"
        return f"<{type(value).__name__}>"
    except Exception:
        return "<unreprable>"
