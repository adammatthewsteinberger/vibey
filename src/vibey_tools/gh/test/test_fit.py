# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The fit calculus (#263): both sides measured, the projection stated, the floor loud."""

from __future__ import annotations

import pytest

from vibey_gh import fit
from vibey_gh.cli import main
from vibey_gh.fit import (
    ADMIT,
    DEFER,
    FLOOR,
    Estimate,
    Machine,
    Model,
    Observation,
    decide,
    estimate_from,
    headroom_gb,
    sample_machine,
    sample_model,
    saturating_wait,
)

MACHINE = Machine(total_gb=25.77, free_gb=2.97, swap_used_gb=6.5, swap_total_gb=7.0)
MODEL = Model(name="qwen2.5-coder:14b", size_gb=10.52, context_length=9390)


def test_available_is_free_memory_plus_unspoken_paging_space():
    assert MACHINE.available_gb == 3.47
    # Over-committed swap never reports negative headroom.
    tight = Machine(total_gb=8.0, free_gb=0.5, swap_used_gb=9.0, swap_total_gb=4.0)
    assert tight.available_gb == 0.5


def test_service_time_scales_with_payload_size():
    est = Estimate(slots=3.1, base_s=40.0, rate_s_per_kb=7.5, samples=6)
    assert est.service_s(0) == 40.0
    assert est.service_s(10240) == 115.0  # 40 + 7.5 * 10 KB


def test_an_estimate_without_evidence_says_so():
    est = estimate_from([])
    assert est.samples == 0 and est.slots == 1.0
    assert est.base_s == 0.0 and est.rate_s_per_kb == 0.0


def test_one_payload_size_cannot_separate_base_from_rate():
    """Two unknowns, one distinct x: the honest fit puts it all in base and leaves
    the rate at zero rather than inventing a slope."""
    obs = [Observation(payload_bytes=8192, elapsed_s=t, concurrent=2) for t in (100.0, 120.0)]
    est = estimate_from(obs)
    assert est.rate_s_per_kb == 0.0
    assert est.base_s == 110.0


def test_varied_payloads_recover_base_and_rate():
    obs = [
        Observation(payload_bytes=1024, elapsed_s=60.0, concurrent=6),
        Observation(payload_bytes=11264, elapsed_s=160.0, concurrent=6),
    ]
    est = estimate_from(obs)
    assert est.rate_s_per_kb == pytest.approx(10.0, abs=0.01)
    assert est.base_s == pytest.approx(50.0, abs=0.5)
    assert est.slots == 2.0  # bounded by the sample count, never invented


def test_a_physically_meaningless_fit_falls_back_to_the_mean():
    """A negative slope would predict big payloads finishing sooner; refuse it."""
    obs = [
        Observation(payload_bytes=1024, elapsed_s=200.0, concurrent=2),
        Observation(payload_bytes=20480, elapsed_s=100.0, concurrent=2),
    ]
    est = estimate_from(obs)
    assert est.rate_s_per_kb == 0.0
    assert est.base_s == 150.0


def test_headroom_wants_the_model_plus_a_share_per_slot():
    assert headroom_gb(MACHINE, MODEL, slots=1.0) == 7.05
    assert headroom_gb(MACHINE, MODEL, slots=4.0) > 7.05
    roomy = Machine(total_gb=128.0, free_gb=90.0, swap_used_gb=0.0, swap_total_gb=8.0)
    assert headroom_gb(roomy, MODEL, slots=4.0) == 0.0


def test_an_unreadable_model_is_the_floor_not_a_guess():
    verdict = decide(
        MACHINE, None, estimate_from([]), queue_depth=0, payload_bytes=1024, deadline_s=900
    )
    assert verdict.verdict == FLOOR and not verdict.ok
    assert "forbids proceeding on an assumed model" in verdict.reason


def test_a_model_beyond_the_machine_fails_loudly_with_the_numbers():
    tiny = Machine(total_gb=8.0, free_gb=2.0, swap_used_gb=1.0, swap_total_gb=2.0)
    huge = Model(name="giant:400b", size_gb=240.0, context_length=128000)
    verdict = decide(
        tiny, huge, estimate_from([]), queue_depth=0, payload_bytes=1024, deadline_s=900
    )
    assert verdict.verdict == FLOOR
    assert "240.0 GB" in verdict.reason and "absolute ceiling" in verdict.reason
    assert verdict.headroom_gb == 230.0


def test_work_that_cannot_meet_the_deadline_defers_with_the_arithmetic():
    est = Estimate(slots=2.0, base_s=100.0, rate_s_per_kb=10.0, samples=8)
    verdict = decide(MACHINE, MODEL, est, queue_depth=40, payload_bytes=10240, deadline_s=300)
    assert verdict.verdict == DEFER and not verdict.ok
    assert "exceeds the 300" in verdict.reason
    assert verdict.projected_wait_s > 0 and verdict.projected_service_s == 200.0


def test_work_that_fits_is_admitted_and_still_reports_headroom():
    est = Estimate(slots=4.0, base_s=50.0, rate_s_per_kb=5.0, samples=12)
    verdict = decide(MACHINE, MODEL, est, queue_depth=2, payload_bytes=4096, deadline_s=900)
    assert verdict.verdict == ADMIT and verdict.ok
    assert "fits the 900" in verdict.reason
    # Headroom is reported even on admit: the projection wants more than exists here.
    assert verdict.headroom_gb > 0
    assert any("grow paging space" in n for n in verdict.notes)


def test_an_unmeasured_projection_says_it_is_a_floor_not_a_forecast():
    verdict = decide(
        MACHINE, MODEL, estimate_from([]), queue_depth=0, payload_bytes=1024, deadline_s=900
    )
    assert any("τ is unmeasured" in n for n in verdict.notes)


def test_sample_machine_reads_the_real_shapes(monkeypatch):
    def fake(*cmd: str) -> str:
        if "hw.memsize" in cmd:
            return "25769803776\n"
        if "vm.swapusage" in cmd:
            return "total = 7168.00M  used = 6651.12M  free = 516.88M  (encrypted)\n"
        if cmd[0] == "vm_stat":
            return (
                "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
                "Pages free:                    100000.\n"
                "Pages active:                  400000.\n"
                "Pages inactive:                 80000.\n"
                "Pages wired down:              200000.\n"
                "Pages occupied by compressor:  120000.\n"
            )
        return ""

    monkeypatch.setattr(fit, "_run", fake)
    machine = sample_machine()
    assert machine.total_gb == 25.77
    assert machine.free_gb == pytest.approx(2.95, abs=0.05)
    assert machine.swap_total_gb == 7.0 and machine.swap_used_gb == pytest.approx(6.5, abs=0.01)


def test_sample_machine_reports_zero_rather_than_guessing(monkeypatch):
    monkeypatch.setattr(fit, "_run", lambda *cmd: "")
    machine = sample_machine()
    assert machine.total_gb == 0.0 and machine.free_gb == 0.0


def test_sample_model_reads_the_runner(monkeypatch):
    monkeypatch.setattr(fit.shutil, "which", lambda _: "/usr/bin/curl")
    monkeypatch.setattr(
        fit,
        "_run",
        lambda *cmd: (
            '{"models": [{"name": "qwen2.5-coder:14b", "size": 10520000000,'
            ' "context_length": 9390}]}'
        ),
    )
    model = sample_model("qwen2.5-coder:14b")
    assert model is not None and model.size_gb == 10.52 and model.context_length == 9390
    assert sample_model("not-loaded") is None


@pytest.mark.parametrize(
    "which, body",
    [
        (None, ""),
        ("/usr/bin/curl", ""),
        ("/usr/bin/curl", "not json"),
        ("/usr/bin/curl", '{"models": ["a bare string", {"name": "other"}]}'),
    ],
)
def test_an_unreadable_runner_yields_no_model(monkeypatch, which, body):
    monkeypatch.setattr(fit.shutil, "which", lambda _: which)
    monkeypatch.setattr(fit, "_run", lambda *cmd: body)
    assert sample_model("qwen2.5-coder:14b") is None


def test_run_survives_a_missing_or_hanging_command(monkeypatch):
    def boom(*a, **k):
        raise OSError("no such tool")

    monkeypatch.setattr(fit.subprocess, "run", boom)
    assert fit._run("nope") == ""

    class Failed:
        returncode = 1
        stdout = "ignored"

    monkeypatch.setattr(fit.subprocess, "run", lambda *a, **k: Failed())
    assert fit._run("false") == ""


def test_fit_cli_reports_both_sides(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(fit, "sample_machine", lambda: MACHINE)
    monkeypatch.setattr(fit, "sample_model", lambda name, base_url=...: MODEL)
    assert main(["fit"]) == 0
    out = capsys.readouterr().out
    assert "25.77 GB total" in out and "qwen2.5-coder:14b 10.52 GB" in out
    assert "ADMIT" in out and "headroom wanted" in out

    monkeypatch.setattr(fit, "sample_model", lambda name, base_url=...: None)
    assert main(["fit"]) == 1
    assert "could not be read from the runner" in capsys.readouterr().out


def test_a_page_size_line_without_digits_falls_back_to_the_default(monkeypatch):
    """vm_stat's header is not contractual; an unparseable one uses 4096 rather
    than crashing or inventing a size."""
    monkeypatch.setattr(
        fit,
        "_run",
        lambda *cmd: (
            "Mach Virtual Memory Statistics:\nPages free: 100000.\n" if cmd[0] == "vm_stat" else ""
        ),
    )
    machine = sample_machine()
    assert machine.free_gb == pytest.approx(0.41, abs=0.01)  # 100000 * 4096 bytes


def test_a_comfortable_machine_reports_no_headroom_note():
    roomy = Machine(total_gb=128.0, free_gb=90.0, swap_used_gb=0.0, swap_total_gb=16.0)
    est = Estimate(slots=4.0, base_s=50.0, rate_s_per_kb=5.0, samples=12)
    verdict = decide(roomy, MODEL, est, queue_depth=1, payload_bytes=4096, deadline_s=900)
    assert verdict.verdict == ADMIT
    assert verdict.headroom_gb == 0.0
    assert not any("grow paging space" in n for n in verdict.notes)


def test_wait_is_superlinear_because_the_measurements_said_so():
    """The stress escalation falsified this module's original linear wait one rung
    after it shipped: 22 s/job through N=12, then 59 s/job by N=16. Slack stays
    nearly linear; saturation goes quadratic."""
    # Idle runner: no queue, no wait, whatever the slot count.
    assert saturating_wait(100.0, queue_depth=0, slots=4.0) == 0.0
    # Slack (rho < 1): close to the linear estimate.
    assert saturating_wait(100.0, queue_depth=2, slots=4.0) == pytest.approx(75.0)
    # Saturated (rho = 4): four times the linear projection, matching the observed
    # slope growth rather than a line.
    linear = 100.0 * (16 / 4)
    assert saturating_wait(100.0, queue_depth=16, slots=4.0) == pytest.approx(5 * linear)
    # A runner with no slots cannot be projected onto.
    assert saturating_wait(100.0, queue_depth=8, slots=0.0) == 0.0


def test_the_superlinear_wait_defers_work_a_linear_model_would_have_admitted():
    """The concrete regression: at sixteen deep on four slots the linear model
    projected 400 s and would have admitted against a 900 s deadline; the measured
    behaviour is far worse, and the corrected rule defers."""
    est = Estimate(slots=4.0, base_s=100.0, rate_s_per_kb=0.0, samples=16)
    verdict = decide(MACHINE, MODEL, est, queue_depth=16, payload_bytes=1024, deadline_s=900)
    assert verdict.verdict == DEFER
    assert verdict.projected_wait_s == pytest.approx(2000.0)
