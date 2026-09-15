# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Sovereign readiness (doctrine 8.a): the probe that makes preferring free safe."""

from __future__ import annotations

import pytest

from vibey_gh import sovereign
from vibey_gh.cli import main
from vibey_gh.config import PrAutomationFallbackConfig
from vibey_gh.sovereign import beat, probe

REF = "refs/vibey-gh/sovereign-heartbeat"


def _fake(monkeypatch, script):
    """Drive `_run` from a table keyed on the git subcommand."""
    calls: list[tuple[str, ...]] = []

    def run(*cmd: str, cwd=None):
        calls.append(cmd)
        for key, result in script.items():
            if key in cmd:
                return result
        return (0, "")

    monkeypatch.setattr(sovereign, "_run", run)
    return calls


def test_the_sovereign_lane_is_offered_only_while_the_heartbeat_is_fresh(monkeypatch):
    _fake(monkeypatch, {"log": (0, "1000")})
    assert probe(REF, max_age_minutes=15, now=1300.0).ready
    verdict = probe(REF, max_age_minutes=15, now=1300.0)
    assert verdict.age_seconds == 300 and "300s old" in verdict.reason


def test_a_stale_heartbeat_treats_the_runner_as_offline(monkeypatch):
    """The whole point: a machine that has stopped saying it is up is not up. Offering
    the lane anyway queues a job forever against a runner nobody is running."""
    _fake(monkeypatch, {"log": (0, "1000")})
    verdict = probe(REF, max_age_minutes=15, now=1000.0 + 16 * 60)
    assert not verdict.ready
    assert "16m old" in verdict.reason and "treating the runner as offline" in verdict.reason


def test_a_missing_heartbeat_is_a_fact_not_a_failure(monkeypatch):
    _fake(monkeypatch, {"fetch": (1, "")})
    verdict = probe(REF, max_age_minutes=15)
    assert not verdict.ready and verdict.age_seconds is None
    assert "no sovereign heartbeat" in verdict.reason


@pytest.mark.parametrize("raw", [(1, "1000"), (0, "not-a-timestamp"), (0, "")])
def test_an_unreadable_heartbeat_never_reports_ready(monkeypatch, raw):
    _fake(monkeypatch, {"log": raw})
    assert not probe(REF, max_age_minutes=15).ready


def test_a_future_dated_heartbeat_is_refused(monkeypatch):
    """Clock skew must not be able to manufacture readiness."""
    _fake(monkeypatch, {"log": (0, "9000")})
    verdict = probe(REF, max_age_minutes=15, now=1000.0)
    assert not verdict.ready and "dated in the future" in verdict.reason


def test_a_heartbeat_is_an_empty_commit_on_a_ref_that_is_not_a_branch(monkeypatch):
    calls = _fake(monkeypatch, {"hash-object": (0, "tree1"), "commit-tree": (0, "c0ffee")})
    result = beat(REF)
    assert result.ready and result.age_seconds == 0
    pushed = next(c for c in calls if "push" in c)
    assert pushed[:4] == ("git", "push", "--force", "--no-verify")
    assert pushed[4] == "origin" and pushed[5] == f"c0ffee:{REF}"
    assert "refs/heads/" not in pushed[5]


def test_a_heartbeat_never_pays_the_pre_push_code_gate(monkeypatch):
    """Measured, not assumed. Against a real project whose pre-push stage runs the test
    suite, then a coverage pass that runs the suite a second time, then a network
    dependency audit, a heartbeat push ran past two minutes without finishing — against
    1.2 seconds with `--no-verify`. It carries an empty tree with no parents, so a gate
    that judges code has nothing here to judge, and a timer that cannot complete inside
    its own interval is not a heartbeat. Worse, `beat()` is called in a loop over many
    repositories, so one slow gate stalls every repository queued behind it."""
    calls = _fake(monkeypatch, {"hash-object": (0, "t"), "commit-tree": (0, "c")})
    assert beat(REF).ready
    assert "--no-verify" in next(c for c in calls if "push" in c)


@pytest.mark.parametrize(
    "script, expected",
    [
        ({"hash-object": (1, "")}, "empty tree"),
        ({"hash-object": (0, "t"), "commit-tree": (0, "")}, "heartbeat commit"),
        ({"hash-object": (0, "t"), "commit-tree": (0, "c"), "push": (1, "")}, "could not push"),
    ],
)
def test_every_heartbeat_failure_is_reported_rather_than_raised(monkeypatch, script, expected):
    _fake(monkeypatch, script)
    result = beat(REF)
    assert not result.ready and expected in result.reason


def test_run_survives_a_missing_or_hanging_git(monkeypatch):
    def boom(*a, **k):
        raise OSError("no git here")

    monkeypatch.setattr(sovereign.subprocess, "run", boom)
    assert sovereign._run("git", "status") == (1, "")

    class Failed:
        returncode = 2
        stdout = " out \n"

    monkeypatch.setattr(sovereign.subprocess, "run", lambda *a, **k: Failed())
    assert sovereign._run("git", "status") == (2, "out")


def test_the_probe_publishes_its_verdict_to_the_job_output(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vibey-gh.toml").write_text("", encoding="utf-8")
    out = tmp_path / "gh-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    _fake(monkeypatch, {"log": (0, "1000")})
    monkeypatch.setattr(sovereign.time, "time", lambda: 1100.0)
    assert main(["sovereign"]) == 0
    assert "ready=true" in out.read_text(encoding="utf-8")

    _fake(monkeypatch, {"fetch": (1, "")})
    assert main(["sovereign"]) == 0  # not available is not an error
    assert "ready=false" in out.read_text(encoding="utf-8")
    assert "no sovereign heartbeat" in capsys.readouterr().out


def test_the_probe_runs_outside_actions_without_a_job_output(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vibey-gh.toml").write_text("", encoding="utf-8")
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    _fake(monkeypatch, {"fetch": (1, "")})
    assert main(["sovereign"]) == 0
    assert "vibey-gh sovereign:" in capsys.readouterr().out


def test_publishing_a_heartbeat_reports_failure_to_the_operator(monkeypatch, tmp_path, capsys):
    """`--beat` is the one form that exits non-zero: the supervisor calling it needs to
    know its heartbeat never landed, or it will believe the lane is offered when it is not."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".vibey-gh.toml").write_text("", encoding="utf-8")
    _fake(monkeypatch, {"hash-object": (0, "t"), "commit-tree": (0, "c")})
    assert main(["sovereign", "--beat"]) == 0
    _fake(monkeypatch, {"hash-object": (1, "")})
    assert main(["sovereign", "--beat"]) == 1
    assert "empty tree" in capsys.readouterr().out


def test_the_sovereign_lane_is_available_by_default_now(monkeypatch):
    """8.a: the sovereign path is the preference, so it may not be the one that has to
    be opted into while the paid lane runs automatically. Safe because the probe gates
    scheduling — a repository with no heartbeat simply never offers the lane."""
    assert PrAutomationFallbackConfig().enabled is True
    assert PrAutomationFallbackConfig().heartbeat_max_age_minutes == 15


@pytest.mark.parametrize(
    "field, value, expected",
    [
        ("heartbeat_ref", "sovereign-heartbeat", "must be a full refs/ path"),
        ("heartbeat_ref", "refs/heads/heartbeat", "must not be a branch"),
        ("heartbeat_max_age_minutes", 0, "between 1 and 1440"),
        ("heartbeat_max_age_minutes", 1441, "between 1 and 1440"),
    ],
)
def test_a_heartbeat_that_would_pollute_or_never_expire_is_refused(field, value, expected):
    with pytest.raises(ValueError, match=expected):
        PrAutomationFallbackConfig(**{field: value})


def test_a_toml_block_overrides_the_heartbeat_defaults(tmp_path):
    from vibey_gh.config import load_config

    (tmp_path / ".vibey-gh.toml").write_text(
        "[pr_automation.fallback]\n"
        'heartbeat_ref = "refs/vibey/pulse"\n'
        "heartbeat_max_age_minutes = 60\n",
        encoding="utf-8",
    )
    fallback = load_config(tmp_path).pr_automation.fallback
    assert fallback.heartbeat_ref == "refs/vibey/pulse"
    assert fallback.heartbeat_max_age_minutes == 60
