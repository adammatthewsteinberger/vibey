"""Per-operation slow-budget defaults.

The defaults are conventional Azure-SDK operation names. Apps override with
``register_slow_threshold(op, seconds)`` at startup.
"""

from __future__ import annotations

import os
import threading

_DEFAULT_SLOW_THRESHOLDS: dict[str, float] = {
    "email_repository.send_email": 10.0,
    "email_repository.list_unread_messages": 8.0,
    "email_repository.get_attachment_content": 30.0,
    "blob_storage_repository.upload_blob_bytes": 10.0,
    "blob_storage_repository.download_blob_bytes": 10.0,
    "service_bus_repository.send_message": 5.0,
    "service_bus_repository.receive_one": 30.0,
    "sharepoint_repository.upload_file": 30.0,
    "ai_analyzer_repository.analyze": 60.0,
    "azure_openai_sheet_extractor_repository.extract_fields": 60.0,
    "pipeline.process": 180.0,
    "pipeline.poll": 60.0,
}

_lock = threading.Lock()
_overrides: dict[str, float] = {}


def default_slow_threshold(operation: str) -> float | None:
    with _lock:
        if operation in _overrides:
            return _overrides[operation]
    return _DEFAULT_SLOW_THRESHOLDS.get(operation)


def register_slow_threshold(operation: str, seconds: float) -> None:
    with _lock:
        _overrides[operation] = float(seconds)


def reset_slow_thresholds() -> None:
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("reset_slow_thresholds is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1")
    with _lock:
        _overrides.clear()
