# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event, digest_range
from vibey.domain.phase import Phase
from vibey.infrastructure.ledger.full_ledger_writer import (
    read_full_ledger_line_count,
    write_full_ledger,
)

PROJECT_ID = uuid4()
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _event(seq: int, payload: dict[str, object] | None = None) -> LedgerEvent:
    payload = payload or {"prompt_digest": "x"}
    return LedgerEvent(
        event_id=uuid4(),
        project_id=PROJECT_ID,
        cycle=1,
        phase=Phase.BUILD,
        seq=seq,
        kind=EventKind.TURN_REQUESTED,
        engine_id=None,
        job_id=None,
        causation_id=None,
        correlation_id=uuid4(),
        provenance=Provenance.AGENT,
        produced_at=NOW,
        payload=payload,
        digest=digest_event(payload),
    )


def test_writes_one_json_line_per_event(tmp_path: Path) -> None:
    events = [_event(1), _event(2), _event(3)]
    path = tmp_path / ".vibey" / "handoff" / "ledger.jsonl"

    write_full_ledger(events, path)

    assert read_full_ledger_line_count(path) == 3


def test_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "nested" / "dir" / "ledger.jsonl"
    write_full_ledger([_event(1)], path)
    assert path.exists()


def test_lines_are_ordered_by_seq_regardless_of_input_order(tmp_path: Path) -> None:
    events = [_event(3), _event(1), _event(2)]
    path = tmp_path / "ledger.jsonl"

    write_full_ledger(events, path)

    seqs = [json.loads(line)["seq"] for line in path.read_text().splitlines()]
    assert seqs == [1, 2, 3]


def test_ref_digest_matches_domain_digest_range(tmp_path: Path) -> None:
    events = [_event(1), _event(2)]
    path = tmp_path / "ledger.jsonl"

    ref = write_full_ledger(events, path)

    assert ref.digest == digest_range(events)


def test_ref_fields_reflect_the_range(tmp_path: Path) -> None:
    events = [_event(5), _event(6), _event(7)]
    path = tmp_path / "ledger.jsonl"

    ref = write_full_ledger(events, path)

    assert ref.from_seq == 5
    assert ref.to_seq == 7
    assert ref.event_count == 3


def test_empty_range_produces_an_empty_ref(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"

    ref = write_full_ledger([], path)

    assert ref.event_count == 0
    assert ref.digest == digest_range(())
    assert path.exists()
    assert read_full_ledger_line_count(path) == 0


def test_written_lines_are_valid_json_with_expected_fields(tmp_path: Path) -> None:
    event = _event(1, payload={"prompt_digest": "abc"})
    path = tmp_path / "ledger.jsonl"

    write_full_ledger([event], path)

    line = path.read_text().splitlines()[0]
    parsed = json.loads(line)
    assert parsed["event_id"] == str(event.event_id)
    assert parsed["seq"] == 1
    assert parsed["kind"] == "TurnRequested"
    assert parsed["payload"] == {"prompt_digest": "abc"}


def test_custom_uri_is_used_in_the_ref(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    ref = write_full_ledger([_event(1)], path, uri="custom/path.jsonl")
    assert ref.uri == "custom/path.jsonl"
