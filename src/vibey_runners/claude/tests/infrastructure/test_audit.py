# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/audit.py — JsonlAuditLog adapter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from claudeloop.infrastructure.audit import JsonlAuditLog


def test_audit_log_creates_parent_directory(tmp_path: Path) -> None:
    """JsonlAuditLog creates parent directory if it doesn't exist."""
    audit_path = tmp_path / "nested" / "dir" / "audit.jsonl"
    log = JsonlAuditLog(audit_path, run_id="run-123")
    log.record("test_event", {})
    assert audit_path.exists()
    assert audit_path.parent.is_dir()


def test_audit_log_appends_entries(tmp_path: Path) -> None:
    """JsonlAuditLog appends new entries to existing file."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path, run_id="run-123")
    log.record("event1", {"data": "first"})
    log.record("event2", {"data": "second"})

    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])
    assert entry1["event_type"] == "event1"
    assert entry1["data"] == "first"
    assert entry2["event_type"] == "event2"
    assert entry2["data"] == "second"


def test_audit_log_includes_run_id_when_set(tmp_path: Path) -> None:
    """Audit entries include run_id when provided."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path, run_id="run-abc")
    log.record("test", {})

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    assert entry["run_id"] == "run-abc"


def test_audit_log_includes_session_id_when_bound(tmp_path: Path) -> None:
    """Audit entries include session_id when bound."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path)
    log.bind(session_id="sess-xyz")
    log.record("test", {})

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    assert entry["session_id"] == "sess-xyz"


def test_audit_log_bind_updates_run_id(tmp_path: Path) -> None:
    """bind() can update run_id after initialization."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path, run_id="original")
    log.bind(run_id="updated")
    log.record("test", {})

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    assert entry["run_id"] == "updated"


def test_audit_log_bind_can_set_both(tmp_path: Path) -> None:
    """bind() can set both run_id and session_id."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path)
    log.bind(run_id="run-123", session_id="sess-456")
    log.record("test", {})

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    assert entry["run_id"] == "run-123"
    assert entry["session_id"] == "sess-456"


def test_audit_log_includes_timestamp(tmp_path: Path) -> None:
    """Every audit entry includes a UTC ISO timestamp."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path)
    before = datetime.now(timezone.utc)
    log.record("test", {})
    after = datetime.now(timezone.utc)

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    assert "timestamp" in entry
    timestamp = datetime.fromisoformat(entry["timestamp"])
    assert before <= timestamp <= after
    assert timestamp.tzinfo is not None


def test_audit_log_merges_payload_into_entry(tmp_path: Path) -> None:
    """Payload dict is merged into the audit entry."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path, run_id="run-123")
    log.record("custom_event", {"user_id": "alice", "action": "login", "count": 42})

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    assert entry["event_type"] == "custom_event"
    assert entry["user_id"] == "alice"
    assert entry["action"] == "login"
    assert entry["count"] == 42


def test_audit_log_redacts_sensitive_data(tmp_path: Path) -> None:
    """Audit log redacts sensitive data using the redact function."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path)
    log.record("test", {"api_key": "secret-key-12345", "data": "safe"})

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    # The redact function should have redacted the api_key field
    assert entry["api_key"] == "***REDACTED***"
    assert entry["data"] == "safe"


def test_audit_log_handles_non_json_serializable_values(tmp_path: Path) -> None:
    """Non-JSON-serializable values are converted using default=str."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path)
    now = datetime.now(timezone.utc)
    log.record("test", {"time": now, "path": Path("/tmp/test")})

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    # datetime and Path should be serialized to strings
    assert isinstance(entry["time"], str)
    assert isinstance(entry["path"], str)
    assert "/tmp/test" in entry["path"]


def test_audit_log_without_run_id_or_session_id(tmp_path: Path) -> None:
    """Audit entries can be created without run_id or session_id."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path)
    log.record("test", {"data": "value"})

    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    assert "run_id" not in entry
    assert "session_id" not in entry
    assert entry["event_type"] == "test"
    assert entry["data"] == "value"


def test_audit_log_multiple_records_different_sessions(tmp_path: Path) -> None:
    """Can log different sessions by rebinding session_id."""
    audit_path = tmp_path / "audit.jsonl"
    log = JsonlAuditLog(audit_path, run_id="run-1")

    log.bind(session_id="sess-a")
    log.record("event1", {})

    log.bind(session_id="sess-b")
    log.record("event2", {})

    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])

    assert entry1["session_id"] == "sess-a"
    assert entry2["session_id"] == "sess-b"
    assert entry1["run_id"] == "run-1"
    assert entry2["run_id"] == "run-1"
