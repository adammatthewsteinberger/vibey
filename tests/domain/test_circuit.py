from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from vibey.domain.capacity import (
    AuthenticationFailed,
    Available,
    CapacityState,
    CreditsExhausted,
    WindowExhausted,
)
from vibey.domain.circuit import BackoffProbe, DeadlineProbe, schedule_probe

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_available_schedules_no_probe() -> None:
    assert schedule_probe(Available(), now=NOW, attempt=0) is None


def test_authentication_failed_schedules_no_probe() -> None:
    assert schedule_probe(AuthenticationFailed(), now=NOW, attempt=5) is None


def test_window_exhausted_with_deadline_schedules_a_deadline_probe() -> None:
    resets_at = NOW + timedelta(hours=1)
    probe = schedule_probe(WindowExhausted(resets_at=resets_at), now=NOW, attempt=0)

    assert isinstance(probe, DeadlineProbe)
    assert probe.at >= resets_at


def test_window_exhausted_without_deadline_schedules_a_backoff_probe() -> None:
    probe = schedule_probe(WindowExhausted(), now=NOW, attempt=2)

    assert isinstance(probe, BackoffProbe)
    assert probe.next_at > NOW
    assert probe.next_at - NOW <= timedelta(minutes=5)


def test_credits_exhausted_schedules_a_backoff_probe_with_a_floor_and_cap() -> None:
    probe = schedule_probe(CreditsExhausted(), now=NOW, attempt=0)

    assert isinstance(probe, BackoffProbe)
    assert probe.next_at - NOW >= timedelta(minutes=5)
    assert probe.next_at - NOW <= timedelta(minutes=30)


def test_negative_attempt_is_treated_as_zero() -> None:
    probe = schedule_probe(CreditsExhausted(), now=NOW, attempt=-5)
    assert isinstance(probe, BackoffProbe)
    assert probe.next_at - NOW >= timedelta(minutes=5)


def test_credits_exhausted_backoff_never_exceeds_thirty_minutes() -> None:
    probe = schedule_probe(CreditsExhausted(), now=NOW, attempt=1000)

    assert isinstance(probe, BackoffProbe)
    assert probe.next_at - NOW <= timedelta(minutes=30)


_capacity_states = st.one_of(
    st.builds(Available),
    st.builds(
        WindowExhausted,
        resets_at=st.one_of(st.none(), st.datetimes(timezones=st.just(UTC))),
        rate_limit_type=st.one_of(st.none(), st.text(max_size=10)),
    ),
    st.builds(CreditsExhausted, can_purchase=st.booleans()),
    st.builds(AuthenticationFailed, detail=st.text(max_size=20)),
)


@given(
    capacity=_capacity_states,
    now=st.datetimes(timezones=st.just(UTC)),
    attempt=st.integers(0, 100),
)
def test_credits_never_produce_a_deadline(
    capacity: CapacityState, now: datetime, attempt: int
) -> None:
    probe = schedule_probe(capacity, now=now, attempt=attempt)
    if isinstance(capacity, CreditsExhausted):
        assert not isinstance(probe, DeadlineProbe)


@given(
    capacity=_capacity_states,
    now=st.datetimes(timezones=st.just(UTC)),
    attempt=st.integers(0, 100),
)
def test_schedule_probe_never_raises(capacity: CapacityState, now: datetime, attempt: int) -> None:
    schedule_probe(capacity, now=now, attempt=attempt)
