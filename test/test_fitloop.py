# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The fit calculus as a control loop (#263): self-adjusting, reconstructible, bounded."""

from __future__ import annotations

import json
from pathlib import Path

from vibey_gh import fitloop
from vibey_gh.fit import ADMIT, DEFER, FLOOR, Machine, Model
from vibey_gh.fitloop import FitLoop

# The live machine the stress run measured: 24 GB, qwen2.5-coder:14b resident.
MACHINE = Machine(total_gb=25.77, free_gb=10.6, swap_used_gb=7.79, swap_total_gb=9.22)
TIGHT = Machine(total_gb=25.77, free_gb=2.97, swap_used_gb=6.5, swap_total_gb=7.0)
MODEL = Model(name="qwen2.5-coder:14b", size_gb=10.52, context_length=9390)


def _loop(tmp_path: Path, **kw) -> FitLoop:
    ticks = iter(range(1, 10_000))
    return FitLoop(
        "qwen2.5-coder:14b",
        journal=tmp_path / "fit" / "journal.jsonl",
        clock=lambda: float(next(ticks)),
        **kw,
    )


def test_an_unmeasured_loop_admits_but_says_its_projection_is_a_floor(tmp_path: Path):
    loop = _loop(tmp_path)
    verdict = loop.admit(payload_bytes=4096, deadline_s=900, machine=MACHINE, model=MODEL)
    assert verdict.verdict == ADMIT
    assert any("τ is unmeasured" in n for n in verdict.notes)
    assert loop.estimate.samples == 0


def test_every_operation_feeds_the_estimate_and_the_constants_move(tmp_path: Path):
    """ "Computed for all operations, always" only means something if every operation
    reports what it cost. Two payload sizes are what separate base from rate."""
    loop = _loop(tmp_path)
    loop.observe(payload_bytes=1024, elapsed_s=60.0, concurrent=6)
    loop.observe(payload_bytes=11264, elapsed_s=160.0, concurrent=6)
    est = loop.estimate
    assert est.samples == 2
    assert est.rate_s_per_kb > 0 and est.base_s > 0
    # A 10 KB payload now projects longer than a 1 KB one, from measurement not guesswork.
    assert est.service_s(10240) > est.service_s(1024)


def test_the_window_is_bounded_so_the_estimate_tracks_now_not_history(tmp_path: Path):
    """A machine whose behaviour changed — a model swapped out, memory freed — must not
    be governed by an hour of stale timings averaged in."""
    loop = _loop(tmp_path, window=4)
    for _ in range(10):
        loop.observe(payload_bytes=4096, elapsed_s=500.0, concurrent=8)
    assert loop.estimate.samples == 4
    for _ in range(4):
        loop.observe(payload_bytes=4096, elapsed_s=50.0, concurrent=8)
    # The slow era is fully out of the window.
    assert loop.estimate.base_s == 50.0


def test_a_synthetic_overload_degrades_gracefully_instead_of_timing_out_en_masse(
    tmp_path: Path,
):
    """#263's acceptance case. As the queue grows the loop stops admitting, which is what
    turns a wave of timeouts into a wave of deferrals — the same work, refused early
    enough to be rescheduled rather than accepted and then lost at the deadline."""
    loop = _loop(tmp_path)
    for _ in range(8):
        loop.observe(payload_bytes=8192, elapsed_s=120.0, concurrent=4)

    verdicts = [
        loop.admit(
            payload_bytes=8192, deadline_s=600, queue_depth=q, machine=MACHINE, model=MODEL
        ).verdict
        for q in (0, 2, 4, 8, 16, 32)
    ]
    assert verdicts[0] == ADMIT, verdicts
    assert verdicts[-1] == DEFER, verdicts
    # Monotone: once it starts deferring it never flips back to admitting at a deeper
    # queue, which is what makes the boundary meaningful to a caller.
    assert verdicts == sorted(verdicts, key=lambda v: v == DEFER)


def test_the_floor_fails_loudly_with_the_numbers_that_prove_it(tmp_path: Path):
    loop = _loop(tmp_path)
    huge = Model(name="giant:400b", size_gb=400.0, context_length=128000)
    verdict = loop.admit(payload_bytes=1024, deadline_s=900, machine=TIGHT, model=huge)
    assert verdict.verdict == FLOOR
    assert "400.0 GB" in verdict.reason and "absolute ceiling" in verdict.reason
    assert loop.recommendation().startswith("FLOOR — ")


def test_an_unreadable_model_is_the_floor_and_the_loop_samples_it_itself(
    tmp_path: Path, monkeypatch
):
    """The machine is re-sampled per admission rather than cached: free memory moved by
    three points inside a single stress rung, and a confident answer from a stale reading
    is the failure this module exists to avoid."""
    calls: list[str] = []
    monkeypatch.setattr(fitloop, "sample_machine", lambda: (calls.append("machine"), MACHINE)[1])
    monkeypatch.setattr(fitloop, "sample_model", lambda name: (calls.append(name), None)[1])
    loop = _loop(tmp_path)
    verdict = loop.admit(payload_bytes=1024, deadline_s=900)
    assert verdict.verdict == FLOOR
    assert "forbids proceeding on an assumed model" in verdict.reason
    assert calls == ["machine", "qwen2.5-coder:14b"]


def test_every_decision_is_reconstructible_from_the_journal(tmp_path: Path):
    """Recording only the verdict leaves "why was this deferred?" unanswerable. The
    inputs and the projection are the record."""
    loop = _loop(tmp_path)
    for _ in range(6):
        loop.observe(payload_bytes=8192, elapsed_s=120.0, concurrent=4)
    loop.admit(payload_bytes=8192, deadline_s=600, queue_depth=32, machine=MACHINE, model=MODEL)

    lines = (tmp_path / "fit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines]
    # Observations and decisions share the journal but are distinct records; a decision
    # must never be replayable as if it were a measurement.
    assert [e["kind"] for e in entries] == ["observation"] * 6 + ["decision"]
    entry = entries[-1]
    for key in (
        "at",
        "verdict",
        "reason",
        "payload_bytes",
        "deadline_s",
        "queue_depth",
        "slots",
        "base_s",
        "rate_s_per_kb",
        "samples",
        "projected_wait_s",
        "projected_service_s",
        "headroom_gb",
        "free_gb",
        "model",
    ):
        assert key in entry, key
    assert entry["verdict"] == DEFER and entry["queue_depth"] == 32
    assert entry["samples"] == 6 and entry["model"] == "qwen2.5-coder:14b"
    # In-memory decisions mirror the journal, so a caller need not read the file back.
    assert loop.decisions[-1].verdict == DEFER


def test_the_journal_appends_across_decisions_and_orders_by_the_clock(tmp_path: Path):
    loop = _loop(tmp_path)
    for _ in range(3):
        loop.admit(payload_bytes=1024, deadline_s=900, machine=MACHINE, model=MODEL)
    entries = [
        json.loads(line)
        for line in (tmp_path / "fit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [e["at"] for e in entries if e["kind"] == "decision"] == [1.0, 2.0, 3.0]


def test_an_unwritable_journal_never_takes_the_admission_down_with_it(tmp_path: Path):
    """Losing the record is bad. Refusing the work because the record could not be
    written is worse, and would make observability a single point of failure."""
    blocked = tmp_path / "file"
    blocked.write_text("not a directory", encoding="utf-8")
    loop = FitLoop("qwen2.5-coder:14b", journal=blocked / "journal.jsonl")
    verdict = loop.admit(payload_bytes=1024, deadline_s=900, machine=MACHINE, model=MODEL)
    assert verdict.verdict == ADMIT
    assert loop.decisions[-1].verdict == ADMIT


def test_a_loop_with_no_journal_still_keeps_its_decisions(tmp_path: Path):
    loop = FitLoop("qwen2.5-coder:14b")
    loop.admit(payload_bytes=1024, deadline_s=900, machine=MACHINE, model=MODEL)
    assert len(loop.decisions) == 1


def test_the_recommendation_asks_a_human_and_never_resizes_anything(tmp_path: Path):
    """#263 asks for headroom to be scaled autonomously. Growing paging space is an
    irreversible change to somebody's machine, which the floor rule reserves for a human,
    so the loop computes exactly what to change and stops there."""
    loop = _loop(tmp_path)
    assert loop.recommendation() is None  # nothing decided yet

    loop.admit(payload_bytes=4096, deadline_s=900, machine=TIGHT, model=MODEL)
    advice = loop.recommendation()
    assert advice and "grow paging space by at least" in advice
    assert "will not resize swap by itself" in advice
    assert "yours to make" in advice

    roomy = Machine(total_gb=128.0, free_gb=90.0, swap_used_gb=0.0, swap_total_gb=16.0)
    loop.admit(payload_bytes=4096, deadline_s=900, machine=roomy, model=MODEL)
    assert loop.recommendation() is None


def test_only_measurements_are_replayed_never_projections(tmp_path: Path):
    """The circularity this guards against: a decision's `projected_service_s` is the
    loop's own guess. Reading it back as an observation would let the estimate confirm
    itself and drift from the machine while growing more confident with every cycle."""
    from vibey_gh.fitloop import recorded_observations

    journal = tmp_path / "fit" / "journal.jsonl"
    loop = _loop(tmp_path)
    loop.observe(payload_bytes=2048, elapsed_s=70.0, concurrent=1)
    loop.admit(payload_bytes=2048, deadline_s=900, machine=MACHINE, model=MODEL)

    kinds = [json.loads(line)["kind"] for line in journal.read_text(encoding="utf-8").splitlines()]
    assert kinds == ["observation", "decision"]

    replayed = recorded_observations(journal)
    assert len(replayed) == 1
    assert replayed[0].elapsed_s == 70.0 and replayed[0].payload_bytes == 2048


def test_a_replayed_journal_carries_the_constants_across_invocations(tmp_path: Path):
    """What makes repeated calls a loop rather than a series of unrelated guesses."""
    from vibey_gh.fitloop import recorded_observations

    journal = tmp_path / "fit" / "journal.jsonl"
    first = _loop(tmp_path)
    first.observe(payload_bytes=2048, elapsed_s=70.0, concurrent=1)
    first.observe(payload_bytes=20480, elapsed_s=240.0, concurrent=1)

    second = FitLoop("qwen2.5-coder:14b", journal=journal)
    second._observations.extend(recorded_observations(journal))
    assert second.estimate.samples == 2
    # Interpolated from measurement: a 10 KB payload sits between the two observed sizes.
    assert 70.0 < second.estimate.service_s(10240) < 240.0


def test_a_damaged_journal_yields_what_it_can_rather_than_raising(tmp_path: Path):
    from vibey_gh.fitloop import recorded_observations

    journal = tmp_path / "j.jsonl"
    journal.write_text(
        "not json\n"
        '{"kind": "observation", "payload_bytes": 1024, "elapsed_s": 50.0, "concurrent": 1}\n'
        '{"kind": "observation", "payload_bytes": "nope", "elapsed_s": 1, "concurrent": 1}\n'
        '{"kind": "observation", "elapsed_s": 5.0}\n'
        '{"kind": "decision", "verdict": "admit"}\n'
        "[1, 2, 3]\n",
        encoding="utf-8",
    )
    replayed = recorded_observations(journal)
    assert len(replayed) == 1 and replayed[0].elapsed_s == 50.0
    assert recorded_observations(tmp_path / "absent.jsonl") == []


def test_the_fit_cli_records_a_measurement_and_reads_it_back(monkeypatch, capsys, tmp_path):
    from vibey_gh.cli import main

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vibey-gh.toml").write_text("", encoding="utf-8")
    monkeypatch.setattr(fitloop, "sample_machine", lambda: MACHINE)
    monkeypatch.setattr(fitloop, "sample_model", lambda name: MODEL)
    import vibey_gh.fit as fitmod

    monkeypatch.setattr(fitmod, "sample_machine", lambda: MACHINE)
    monkeypatch.setattr(fitmod, "sample_model", lambda name: MODEL)

    journal = str(tmp_path / "j.jsonl")
    assert (
        main(["fit", "--journal", journal, "--payload-bytes", "2048", "--observed-seconds", "70"])
        == 0
    )
    assert (
        main(["fit", "--journal", journal, "--payload-bytes", "20480", "--observed-seconds", "240"])
        == 0
    )
    capsys.readouterr()
    assert main(["fit", "--journal", journal, "--payload-bytes", "10240"]) == 0
    out = capsys.readouterr().out
    # Measured, so the projection is a forecast rather than the unmeasured floor.
    assert "τ is unmeasured" not in out
    assert "ADMIT" in out


def test_the_fit_cli_runs_without_a_journal(monkeypatch, capsys, tmp_path):
    from vibey_gh.cli import main

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vibey-gh.toml").write_text("", encoding="utf-8")
    monkeypatch.setattr(fitloop, "sample_machine", lambda: MACHINE)
    monkeypatch.setattr(fitloop, "sample_model", lambda name: MODEL)
    import vibey_gh.fit as fitmod

    monkeypatch.setattr(fitmod, "sample_machine", lambda: MACHINE)
    monkeypatch.setattr(fitmod, "sample_model", lambda name: MODEL)
    assert main(["fit"]) == 0
    assert "ADMIT" in capsys.readouterr().out
