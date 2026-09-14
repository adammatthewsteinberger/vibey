# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Thread refs and session selectors."""

from __future__ import annotations

from datetime import UTC, datetime

from codexloop.domain.session import Explicit, MostRecent, PlanFile, SessionSelector, ThreadRef

STARTED = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def test_thread_ref_holds_identity_fields_and_is_frozen() -> None:
    ref = ThreadRef(thread_id="thr_1", cwd="/work", started_at=STARTED, model="gpt-5")
    assert ref.thread_id == "thr_1"
    assert ref.cwd == "/work"
    assert ref.started_at == STARTED
    assert ref.model == "gpt-5"
    assert ref.__dataclass_params__.frozen is True
    assert ref.__dataclass_params__.slots is True
    assert hash(ref) == hash(ref)


def test_session_selector_variants_are_frozen() -> None:
    plan = PlanFile(path="handoff.md")
    recent = MostRecent()
    explicit = Explicit(thread_id="thr_9")
    selectors: tuple[SessionSelector, ...] = (plan, recent, explicit)
    assert plan.path == "handoff.md"
    assert explicit.thread_id == "thr_9"
    for selector in selectors:
        assert selector.__dataclass_params__.frozen is True
        assert selector.__dataclass_params__.slots is True
        assert hash(selector) == hash(selector)
