"""Audit chaining tests."""

from __future__ import annotations

from vibey_bootstrap.audit import AuditChain, ChainedAuditRecord, verify_chain


def test_verify_chain_detects_tamper() -> None:
    stored: list[ChainedAuditRecord] = []

    def store(rec: ChainedAuditRecord) -> None:
        stored.append(rec)

    chain = AuditChain(storage_fn=store)
    r1 = chain.append_chained("LOGIN", actor="alice", resource="/portal")
    r2 = chain.append_chained("EXPORT", actor="alice", resource="/report/42")
    assert verify_chain([r1, r2]) is True

    tampered = ChainedAuditRecord(
        id=r2.id,
        ts=r2.ts,
        event_type=r2.event_type,
        actor=r2.actor,
        resource=r2.resource,
        detail=r2.detail,
        prev_hash=r2.prev_hash,
        record_hash="deadbeef",
    )
    assert verify_chain([r1, tampered]) is False
