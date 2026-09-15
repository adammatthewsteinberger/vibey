"""Transactional outbox — reliable send with idempotency and claim/drain."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from vibey_bootstrap.counters import bump_counter

_logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_SENDING = "sending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"


def _validate_identifier(name: str) -> None:
    import re

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")


OUTBOX_DDL = """
CREATE TABLE IF NOT EXISTS outbox (
    id UUID PRIMARY KEY,
    idempotency_key TEXT UNIQUE NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempt_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);
"""


@dataclass
class OutboxMessage:
    id: str
    idempotency_key: str
    payload: dict[str, Any]
    status: str
    attempt_count: int
    last_error: str | None
    created_at: datetime
    sent_at: datetime | None


class Outbox:
    """DB-backed transactional outbox with atomic claim semantics."""

    def __init__(self, session: Any, *, table: str = "outbox") -> None:
        _validate_identifier(table)
        self._session = session
        self._table = table

    def enqueue(self, *, idempotency_key: str, payload: dict[str, Any]) -> OutboxMessage:
        from sqlalchemy import text  # type: ignore[import-untyped]

        msg_id = str(uuid.uuid4())
        sql = text(f"""
            INSERT INTO {self._table} (id, idempotency_key, payload, status, attempt_count, created_at)
            VALUES (:id, :key, :payload, :status, 0, :created_at)
            ON CONFLICT (idempotency_key) DO NOTHING
            """)  # nosec B608 — table validated in __init__
        now = datetime.now(UTC)
        self._session.execute(
            sql,
            {
                "id": msg_id,
                "key": idempotency_key,
                "payload": json.dumps(payload),
                "status": STATUS_PENDING,
                "created_at": now,
            },
        )
        bump_counter("outbox.enqueued")
        return OutboxMessage(
            id=msg_id,
            idempotency_key=idempotency_key,
            payload=payload,
            status=STATUS_PENDING,
            attempt_count=0,
            last_error=None,
            created_at=now,
            sent_at=None,
        )

    def claim(self, msg_id: str) -> bool:
        from sqlalchemy import text  # type: ignore[import-untyped]

        sql = text(f"""
            UPDATE {self._table}
            SET status = :sending
            WHERE id = :id AND status = :pending
            """)  # nosec B608 — table validated in __init__
        result = self._session.execute(
            sql,
            {"id": msg_id, "sending": STATUS_SENDING, "pending": STATUS_PENDING},
        )
        claimed = result.rowcount == 1
        if claimed:
            bump_counter("outbox.claimed")
        return bool(claimed)

    def mark_sent(self, msg_id: str) -> None:
        from sqlalchemy import text  # type: ignore[import-untyped]

        self._session.execute(
            text(
                f"UPDATE {self._table} SET status = :sent, sent_at = :now WHERE id = :id"  # nosec B608
            ),
            {"sent": STATUS_SENT, "now": datetime.now(UTC), "id": msg_id},
        )
        bump_counter("outbox.sent")

    def mark_failed(self, msg_id: str, error: str, *, max_attempts: int = 5) -> None:
        from sqlalchemy import text  # type: ignore[import-untyped]

        self._session.execute(
            text(f"""
                UPDATE {self._table}
                SET attempt_count = attempt_count + 1,
                    last_error = :error,
                    status = CASE WHEN attempt_count + 1 >= :max THEN :failed ELSE :pending END
                WHERE id = :id
                """),  # nosec B608 — table validated in __init__
            {
                "error": error[:2000],
                "max": max_attempts,
                "failed": STATUS_FAILED,
                "pending": STATUS_PENDING,
                "id": msg_id,
            },
        )
        bump_counter("outbox.failed")


def drain_outbox(
    session: Any,
    sender_fn: Callable[[dict[str, Any]], None],
    *,
    batch_size: int = 10,
    max_attempts: int = 5,
    table: str = "outbox",
) -> int:
    """Claim and drain pending outbox rows. Returns count sent."""
    from sqlalchemy import text  # type: ignore[import-untyped]

    _validate_identifier(table)
    sql = text(f"""
        SELECT id, payload FROM {table}
        WHERE status = :pending AND attempt_count < :max
        ORDER BY created_at
        LIMIT :batch
        FOR UPDATE SKIP LOCKED
        """)  # nosec B608 — table validated above
    rows = session.execute(
        sql, {"pending": STATUS_PENDING, "max": max_attempts, "batch": batch_size}
    ).fetchall()
    sent = 0
    outbox = Outbox(session, table=table)
    for row in rows:
        msg_id = str(row[0])
        payload = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        if not outbox.claim(msg_id):
            continue
        try:
            sender_fn(payload)
            outbox.mark_sent(msg_id)
            sent += 1
        except Exception as exc:
            outbox.mark_failed(msg_id, str(exc), max_attempts=max_attempts)
            _logger.warning("outbox drain failed for %s: %s", msg_id, exc)
    return sent


__all__ = ["Outbox", "OutboxMessage", "OUTBOX_DDL", "drain_outbox"]
