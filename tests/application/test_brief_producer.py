# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""DeterministicBriefProducer: the production floor producer."""

from datetime import UTC, datetime
from uuid import uuid4

from vibey.application.brief_producer import DeterministicBriefProducer
from vibey.domain.handoff import GateMode
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event
from vibey.domain.phase import Phase

NOW = datetime(2026, 8, 19, tzinfo=UTC)
PROJECT_ID = uuid4()


def _event(seq: int, kind: EventKind, payload: dict[str, object]) -> LedgerEvent:
    return LedgerEvent(
        event_id=uuid4(),
        project_id=PROJECT_ID,
        cycle=1,
        phase=Phase.BUILD,
        seq=seq,
        kind=kind,
        engine_id=None,
        job_id=None,
        causation_id=None,
        correlation_id=uuid4(),
        provenance=Provenance.AGENT,
        produced_at=NOW,
        payload=payload,
        digest=digest_event(payload),
    )


_EVENTS = (
    _event(
        1,
        EventKind.QUESTION_ASKED,
        {"question_id": "q-1", "text": "cap retries?", "blocking": True},
    ),
    _event(
        2,
        EventKind.VERDICT_RENDERED,
        {"complete": False, "remaining_work": ["finish the relay"]},
    ),
)


async def test_produce_is_deterministic_and_ignores_regeneration_inputs() -> None:
    producer = DeterministicBriefProducer(events=_EVENTS)

    first = await producer.produce(attempt=1, mode=GateMode.STRICT, violations=())
    second = await producer.produce(attempt=3, mode=GateMode.FULL_TRANSCRIPT, violations=())

    assert first == second
    assert [q.question_id for q in first.open_questions] == ["q-1"]
    assert [r.text for r in first.remaining] == ["finish the relay"]
    assert first.next_action == "finish the relay"


async def test_extra_remaining_merges_deduplicated_and_updates_next_action() -> None:
    producer = DeterministicBriefProducer(
        events=_EVENTS,
        extra_remaining=("finish the relay", "wire the backoff"),
    )

    brief = await producer.produce(attempt=1, mode=GateMode.STRICT, violations=())

    assert [r.text for r in brief.remaining] == ["finish the relay", "wire the backoff"]
    assert brief.next_action == "finish the relay"


async def test_fully_duplicated_extra_remaining_returns_the_base_brief() -> None:
    producer = DeterministicBriefProducer(events=_EVENTS, extra_remaining=("finish the relay",))

    brief = await producer.produce(attempt=1, mode=GateMode.STRICT, violations=())

    assert [r.text for r in brief.remaining] == ["finish the relay"]


async def test_stop_summary_remaining_becomes_next_action_when_no_verdict_exists() -> None:
    """A wind-down often leaves no VerdictRendered -- the outgoing
    engine's final snapshot is then the only source of remaining work."""
    producer = DeterministicBriefProducer(
        events=(_EVENTS[0],), extra_remaining=("resume the relay from the snapshot",)
    )

    brief = await producer.produce(attempt=1, mode=GateMode.STRICT, violations=())

    assert [r.text for r in brief.remaining] == ["resume the relay from the snapshot"]
    assert brief.next_action == "resume the relay from the snapshot"
