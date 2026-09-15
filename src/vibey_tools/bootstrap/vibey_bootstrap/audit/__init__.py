"""Audit log conventions.

Standardize the audit-line pattern so PII/secret leakage at log call sites
is handled consistently. Mask email-shaped values via the v2
:func:`mask_email_address` helper; non-email secrets via :func:`mask_api_key`;
truncate / strip control chars from text fields via :func:`sanitize_for_log`.

Always inserts a UTC ISO-8601 timestamp and the operation name into the
extras dict so structured aggregators have a stable schema.

Hash-chained audit records (v3)
--------------------------------
:class:`ChainedAuditRecord` is a dataclass whose ``record_hash`` field is a
SHA-256 digest of the canonical JSON representation of all other fields
(including ``prev_hash``).  :class:`AuditChain` sequences records so that
each record's ``prev_hash`` equals the preceding record's ``record_hash``,
making undetected tampering computationally infeasible.

Usage::

    def store(record: ChainedAuditRecord) -> None:
        db.insert(record)          # or blob, queue, etc.

    chain = AuditChain(storage_fn=store)
    r1 = chain.append_chained("LOGIN", actor="alice", resource="/portal")
    r2 = chain.append_chained("EXPORT", actor="alice", resource="/report/42")

    ok = verify_chain([r1, r2])    # True if untampered
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.logging.masking import (
    mask_api_key,
    mask_email_address,
    sanitize_for_log,
)

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Existing constants
# ---------------------------------------------------------------------------

AUDIT_LINE_NAMES: tuple[str, ...] = (
    "EMAIL_AUDIT",
    "REPORT_AUDIT",
    "SHAREPOINT_AUDIT",
    "BLOB_AUDIT",
    "QUEUE_AUDIT",
    "AUTH_AUDIT",
)

AUDIT_MASKED_FIELDS: frozenset[str] = frozenset(
    {
        "sender",
        "recipient",
        "to",
        "from",
        "email",
        "api_key",
        "token",
        "secret",
        "client_secret",
        "connection_string",
    }
)

AUDIT_TRUNCATED_FIELDS: dict[str, int] = {
    "subject": 100,
    "error": 500,
    "exception_message": 500,
    "error_summary": 500,
    "traceback": 2000,
    "body_preview": 500,
    "filename": 256,
}


# ---------------------------------------------------------------------------
# Existing helpers (unchanged)
# ---------------------------------------------------------------------------


def mask_email_field(value: str | None) -> str:
    """Ergonomic alias of :func:`mask_email_address`."""
    return mask_email_address(value)


def truncate_field(name: str, value: Any) -> Any:
    """Apply ``AUDIT_TRUNCATED_FIELDS`` truncation when applicable."""
    cap = AUDIT_TRUNCATED_FIELDS.get(name.lower())
    if cap is None or not isinstance(value, str):
        return value
    return sanitize_for_log(value, max_len=cap)


def _is_email_shaped(value: Any) -> bool:
    return isinstance(value, str) and "@" in value


def build_audit_extra(operation: str, **fields: Any) -> dict[str, Any]:
    """Construct the ``extra={}`` dict for an audit log call.

    Email-shaped values for masked fields go through :func:`mask_email_address`;
    other masked values through :func:`mask_api_key`. Truncated fields get
    :func:`sanitize_for_log` applied with the configured cap.

    Always adds ``operation`` and a UTC ISO-8601 ``timestamp``.
    """
    out: dict[str, Any] = {
        "operation": operation,
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    for name, value in fields.items():
        lowered = name.lower()
        if lowered in AUDIT_MASKED_FIELDS:
            if value:
                if _is_email_shaped(value):
                    out[name] = mask_email_address(value)
                else:
                    out[name] = mask_api_key(value if isinstance(value, str) else str(value))
                bump_counter(f"audit.field_masked.{lowered}")
            else:
                out[name] = value
            continue
        if lowered in AUDIT_TRUNCATED_FIELDS and isinstance(value, str):
            truncated = sanitize_for_log(value, max_len=AUDIT_TRUNCATED_FIELDS[lowered])
            if truncated != value:
                bump_counter(f"audit.field_truncated.{lowered}")
            out[name] = truncated
            continue
        out[name] = value
    return out


# ---------------------------------------------------------------------------
# Hash-chained audit records (v3 addition)
# ---------------------------------------------------------------------------


def _compute_record_hash(
    id: str,
    ts: str,
    event_type: str,
    actor: str,
    resource: str,
    detail: dict[str, Any],
    prev_hash: str | None,
) -> str:
    """Return the SHA-256 hex digest over the canonical JSON of the record fields.

    ``record_hash`` itself is excluded from the digest input — all other fields
    are serialised with sorted keys so the output is deterministic regardless of
    insertion order.
    """
    payload: dict[str, Any] = {
        "id": id,
        "ts": ts,
        "event_type": event_type,
        "actor": actor,
        "resource": resource,
        "detail": detail,
        "prev_hash": prev_hash,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class ChainedAuditRecord:
    """An immutable audit event linked to its predecessor via ``prev_hash``.

    Fields
    ------
    id
        UUID4 string uniquely identifying this record.
    ts
        UTC ISO-8601 timestamp (``Z`` suffix) at creation time.
    event_type
        Caller-supplied label such as ``"LOGIN"``, ``"EXPORT"``, ``"DELETE"``.
    actor
        Identity performing the action (user, service principal, system).
    resource
        The object or endpoint being acted upon.
    detail
        Arbitrary key-value metadata; must be JSON-serialisable.
    prev_hash
        ``record_hash`` of the preceding record, or ``None`` for the chain head.
    record_hash
        SHA-256 hex digest of the canonical JSON of all other fields.
        Computed automatically by :meth:`__post_init__` when left as the
        empty-string sentinel ``""``.
    """

    id: str
    ts: str
    event_type: str
    actor: str
    resource: str
    detail: dict[str, Any]
    prev_hash: str | None
    record_hash: str = field(default="")

    def __post_init__(self) -> None:
        if self.record_hash == "":
            self.record_hash = _compute_record_hash(
                id=self.id,
                ts=self.ts,
                event_type=self.event_type,
                actor=self.actor,
                resource=self.resource,
                detail=self.detail,
                prev_hash=self.prev_hash,
            )


class AuditChain:
    """Thread-safe, append-only sequence of :class:`ChainedAuditRecord` objects.

    Each new record's ``prev_hash`` is set to the ``record_hash`` of the most
    recently appended record (or ``None`` for the very first record), forming a
    cryptographic chain of custody.

    Parameters
    ----------
    storage_fn:
        Callable invoked with each new :class:`ChainedAuditRecord` immediately
        after it is appended.  Suitable for writing to a database, blob store,
        audit queue, or any other durable sink.  The callable is invoked while
        the internal lock is *not* held, so it may perform I/O without blocking
        concurrent appends.
    """

    def __init__(self, storage_fn: Callable[[ChainedAuditRecord], None]) -> None:
        self._storage_fn = storage_fn
        self._lock = threading.Lock()
        self._head_hash: str | None = None

    def append_chained(
        self,
        event_type: str,
        actor: str,
        resource: str,
        detail: dict[str, Any] | None = None,
    ) -> ChainedAuditRecord:
        """Create and store a new :class:`ChainedAuditRecord`.

        Parameters
        ----------
        event_type:
            Short label identifying the kind of action (e.g. ``"LOGIN"``).
        actor:
            Identity performing the action.
        resource:
            The object or endpoint being acted upon.
        detail:
            Optional mapping of additional metadata.  Defaults to ``{}``.

        Returns
        -------
        ChainedAuditRecord
            The newly created record, already passed to ``storage_fn``.
        """
        if detail is None:
            detail = {}

        with self._lock:
            prev_hash = self._head_hash
            record = ChainedAuditRecord(
                id=str(uuid.uuid4()),
                ts=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                event_type=event_type,
                actor=actor,
                resource=resource,
                detail=detail,
                prev_hash=prev_hash,
            )
            self._head_hash = record.record_hash

        bump_counter("audit.chain.append")
        self._storage_fn(record)
        return record

    def verify_chain(self, records: list[ChainedAuditRecord]) -> bool:
        """Verify a sequence of :class:`ChainedAuditRecord` objects is untampered.

        Delegates to the module-level :func:`verify_chain` function.
        """
        return verify_chain(records)


def verify_chain(records: list[ChainedAuditRecord]) -> bool:
    """Verify the integrity of an ordered list of :class:`ChainedAuditRecord` objects.

    For each record the function recomputes the expected ``record_hash`` from
    the record's fields and confirms it matches the stored ``record_hash``.  It
    also verifies that each record's ``prev_hash`` equals the preceding record's
    ``record_hash`` (or ``None`` for the first record).

    Returns ``True`` if the chain is intact, ``False`` on the first detected
    anomaly (and logs a warning with tamper-evidence details).

    Parameters
    ----------
    records:
        Ordered list of records as originally produced by
        :meth:`AuditChain.append_chained`.
    """
    if not records:
        return True

    expected_prev: str | None = None
    for idx, record in enumerate(records):
        # Verify linkage
        if record.prev_hash != expected_prev:
            _log.warning(
                "audit chain tamper detected: prev_hash mismatch",
                extra={
                    "chain_index": idx,
                    "record_id": record.id,
                    "expected_prev_hash": expected_prev,
                    "actual_prev_hash": record.prev_hash,
                    "event_type": record.event_type,
                    "actor": record.actor,
                    "resource": record.resource,
                },
            )
            bump_counter("audit.chain.tamper_detected")
            return False

        # Verify self-hash
        expected_hash = _compute_record_hash(
            id=record.id,
            ts=record.ts,
            event_type=record.event_type,
            actor=record.actor,
            resource=record.resource,
            detail=record.detail,
            prev_hash=record.prev_hash,
        )
        if record.record_hash != expected_hash:
            _log.warning(
                "audit chain tamper detected: record_hash mismatch",
                extra={
                    "chain_index": idx,
                    "record_id": record.id,
                    "expected_record_hash": expected_hash,
                    "actual_record_hash": record.record_hash,
                    "event_type": record.event_type,
                    "actor": record.actor,
                    "resource": record.resource,
                },
            )
            bump_counter("audit.chain.tamper_detected")
            return False

        expected_prev = record.record_hash

    bump_counter("audit.chain.verify_ok")
    return True


# ---------------------------------------------------------------------------
# Test-only reset helper
# ---------------------------------------------------------------------------


def _reset_audit_chain() -> None:  # pragma: no cover
    """Reset module-level audit chain state.

    Only available when ``AZURE_BOOTSTRAP_ALLOW_RESET=1`` is set in the
    environment.  Production code must never call this function.
    """
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("_reset_audit_chain() requires AZURE_BOOTSTRAP_ALLOW_RESET=1")
    # No module-level singleton state to reset — AuditChain instances are
    # caller-owned.  This function exists for symmetry with other subpackages
    # and to allow future module-level state to be reset safely in tests.


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    # Pre-existing
    "AUDIT_LINE_NAMES",
    "AUDIT_MASKED_FIELDS",
    "AUDIT_TRUNCATED_FIELDS",
    "build_audit_extra",
    "mask_email_field",
    "truncate_field",
    # v3 additions
    "AuditChain",
    "ChainedAuditRecord",
    "verify_chain",
    "_reset_audit_chain",
]
