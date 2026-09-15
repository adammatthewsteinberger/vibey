# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Local-authority mode (#206): green local branches reach the remote by themselves.

Tested against real git repositories, because the safety rails ARE the feature: a
protected branch, a dirty tree, a failing provenance check, and a stale lease must
each stop a push, and only the clean-green-ahead case may go through.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from vibey_gh import local_authority


def _run(cwd: Path, *args: str) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _fleet_repo(tmp_path: Path, name: str) -> tuple[Path, Path]:
    """A work tree on branch `topic`, one commit ahead of its own bare origin."""
    origin = tmp_path / f"{name}-origin.git"
    _run(tmp_path, "git", "init", "--bare", "--initial-branch=develop", str(origin))
    work = tmp_path / name
    _run(tmp_path, "git", "clone", "-q", str(origin), str(work))
    _run(work, "git", "config", "user.email", "t@example.invalid")
    _run(work, "git", "config", "user.name", "t")
    (work / ".vibey-gh.toml").write_text("[branches]\nintegration = 'develop'\n")
    _run(work, "git", "add", "-A")
    _run(work, "git", "commit", "-q", "-m", "chore: base")
    _run(work, "git", "push", "-q", "-u", "origin", "develop")
    _run(work, "git", "checkout", "-q", "-b", "topic")
    _run(work, "git", "push", "-q", "-u", "origin", "topic")
    (work / "change.txt").write_text("ahead\n")
    _run(work, "git", "add", "-A")
    _run(work, "git", "commit", "-q", "-m", "feat: ahead")
    return work, origin


def _origin_tip(origin: Path, branch: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(origin), "rev-parse", branch],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def test_a_clean_green_ahead_branch_is_pushed(tmp_path):
    work, origin = _fleet_repo(tmp_path, "one")
    before = _origin_tip(origin, "topic")
    outcome = local_authority.sync_repo(work, check=False)
    assert outcome.action == "pushed" and outcome.ahead == 1
    assert _origin_tip(origin, "topic") != before


def test_protected_branches_are_never_touched(tmp_path):
    work, origin = _fleet_repo(tmp_path, "two")
    _run(work, "git", "checkout", "-q", "develop")
    (work / "d.txt").write_text("x")
    _run(work, "git", "add", "-A")
    _run(work, "git", "commit", "-q", "-m", "feat: on develop")
    before = _origin_tip(origin, "develop")
    outcome = local_authority.sync_repo(work, check=False)
    assert outcome.action == "skipped" and "protected" in outcome.detail
    assert _origin_tip(origin, "develop") == before
    # explicit protection wins over the config default
    outcome = local_authority.sync_repo(work, protected=("develop",), check=False)
    assert outcome.action == "skipped"


def test_a_dirty_tree_is_never_pushed(tmp_path):
    work, _ = _fleet_repo(tmp_path, "three")
    (work / "uncommitted.txt").write_text("wip")
    outcome = local_authority.sync_repo(work, check=False)
    assert outcome.action == "skipped" and "dirty" in outcome.detail


def test_nothing_ahead_is_a_noop(tmp_path):
    work, _ = _fleet_repo(tmp_path, "four")
    local_authority.sync_repo(work, check=False)
    outcome = local_authority.sync_repo(work, check=False)
    assert outcome.action == "skipped" and "nothing ahead" in outcome.detail


def test_a_failing_provenance_check_holds_the_push(tmp_path, monkeypatch):
    work, origin = _fleet_repo(tmp_path, "five")
    before = _origin_tip(origin, "topic")
    real_run = subprocess.run

    def fake_run(cmd, **kw):
        if cmd[:2] == ["vibey-gh", "check"]:
            return subprocess.CompletedProcess(cmd, 1, "", "not intact")
        return real_run(cmd, **kw)

    monkeypatch.setattr(local_authority.subprocess, "run", fake_run)
    outcome = local_authority.sync_repo(work, check=True)
    assert outcome.action == "held" and "provenance" in outcome.detail
    assert _origin_tip(origin, "topic") == before


def test_a_stale_lease_is_refused_not_clobbered(tmp_path):
    work, origin = _fleet_repo(tmp_path, "six")
    # someone else advances the remote topic branch behind our back
    other = tmp_path / "other"
    _run(tmp_path, "git", "clone", "-q", str(origin), str(other))
    _run(other, "git", "config", "user.email", "o@example.invalid")
    _run(other, "git", "config", "user.name", "o")
    _run(other, "git", "checkout", "-q", "topic")
    (other / "theirs.txt").write_text("remote work we have not seen")
    _run(other, "git", "add", "-A")
    _run(other, "git", "commit", "-q", "-m", "feat: theirs")
    _run(other, "git", "push", "-q", "origin", "topic")
    theirs = _origin_tip(origin, "topic")
    # our stale lease must refuse — sync_repo fetches, but HEAD diverged from @{u}
    outcome = local_authority.sync_repo(work, check=False)
    assert outcome.action in ("refused", "skipped")
    assert _origin_tip(origin, "topic") == theirs, "remote work must never be clobbered"


def test_discovery_only_admits_opted_in_work_trees(tmp_path):
    work, _ = _fleet_repo(tmp_path, "seven")
    plain = tmp_path / "plain-git"
    _run(tmp_path, "git", "init", "-q", str(plain))
    (tmp_path / "not-a-repo").mkdir()
    found = local_authority.discover(tmp_path)
    assert work in found
    assert plain not in found, ".vibey-gh.toml is the opt-in marker"
    assert local_authority.discover(tmp_path / "missing") == []


def test_detached_head_is_skipped(tmp_path):
    work, _ = _fleet_repo(tmp_path, "eight")
    _run(work, "git", "checkout", "-q", "--detach")
    outcome = local_authority.sync_repo(work, check=False)
    assert outcome.action == "skipped" and "detached" in outcome.detail


def test_a_broken_config_narrows_to_conventional_protection(tmp_path):
    work, _ = _fleet_repo(tmp_path, "nine")
    (work / ".vibey-gh.toml").write_text("this is [not valid toml")
    _run(work, "git", "checkout", "-q", "develop")
    (work / "x.txt").write_text("x")
    _run(work, "git", "add", "-A")
    _run(work, "git", "commit", "-q", "-m", "feat: x")
    outcome = local_authority.sync_repo(work, check=False)
    assert outcome.action == "skipped" and "protected" in outcome.detail


def test_run_reports_actionable_outcomes_and_honours_once(tmp_path):
    work, _ = _fleet_repo(tmp_path, "ten")
    lines: list[str] = []
    local_authority.run([work], once=True, check=False, report=lines.append)
    assert lines and "pushed" in lines[0]
    # a second pass has nothing ahead: skipped outcomes stay out of the report
    lines.clear()
    local_authority.run([work], once=True, check=False, report=lines.append)
    assert lines == []


def test_run_sleeps_between_passes_until_told_once(tmp_path):
    work, _ = _fleet_repo(tmp_path, "eleven")
    naps: list[int] = []

    def nap(seconds: int) -> None:
        naps.append(seconds)
        raise KeyboardInterrupt  # end the loop after proving it slept

    try:
        local_authority.run([work], interval=7, check=False, report=lambda s: None, sleep=nap)
    except KeyboardInterrupt:
        pass
    assert naps == [7]


def test_the_cli_runs_one_pass_and_reports(tmp_path, capsys, monkeypatch):
    from vibey_gh import cli

    work, _ = _fleet_repo(tmp_path, "twelve")
    code = cli.main(["local-authority", "--repos", str(work), "--once", "--no-check"])
    assert code == 0
    assert "pushed" in capsys.readouterr().out


def test_the_cli_refuses_an_empty_fleet(tmp_path, capsys):
    from vibey_gh import cli

    code = cli.main(["local-authority", "--root", str(tmp_path / "empty"), "--once"])
    assert code == 1
    assert "no repositories" in capsys.readouterr().err


def test_a_passing_provenance_check_falls_through_to_the_push(tmp_path, monkeypatch):
    work, _origin = _fleet_repo(tmp_path, "twelve-b")
    real_run = subprocess.run

    def fake_run(cmd, **kw):
        if cmd[:2] == ["vibey-gh", "check"]:
            return subprocess.CompletedProcess(cmd, 0, "ok", "")
        return real_run(cmd, **kw)

    monkeypatch.setattr(local_authority.subprocess, "run", fake_run)
    outcome = local_authority.sync_repo(work, check=True)
    assert outcome.action == "pushed" and outcome.ahead == 1
