# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The clean repo (sub-doctrine 9.a): survey classes, the two losslessness proofs,
and the human-messiness exemption."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vibey_gh import tidy
from vibey_gh.config import GhConfig, TidyConfig, load_config


def _sh(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture()
def repos(tmp_path: Path, monkeypatch):
    """A local clone with an `origin`, one merged branch, one gone-upstream branch,
    one live open-PR head, a stash, an untracked file, and an orphan tag."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", origin], check=True)
    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
    _sh(work, "config", "user.email", "t@example.com")
    _sh(work, "config", "user.name", "t")
    (work / "a.txt").write_text("a\n")
    _sh(work, "add", "-A")
    _sh(work, "commit", "-qm", "base")
    _sh(work, "branch", "-M", "develop")
    _sh(work, "push", "-qu", "origin", "develop")
    _sh(work, "push", "-q", "origin", "develop:main")
    _sh(work, "remote", "set-head", "origin", "develop")

    # merged: tip is an ancestor of develop (the ancestry proof)
    _sh(work, "branch", "merged-work", "develop")
    _sh(work, "push", "-qu", "origin", "merged-work")

    # gone: upstream deleted after a squash-style merge (the forge-event proof)
    _sh(work, "checkout", "-qb", "gone-work")
    (work / "b.txt").write_text("b\n")
    _sh(work, "add", "-A")
    _sh(work, "commit", "-qm", "squashed elsewhere")
    _sh(work, "push", "-qu", "origin", "gone-work")
    _sh(work, "push", "-q", "origin", "--delete", "gone-work")
    _sh(work, "checkout", "-q", "develop")

    # an open-PR head: unmerged remote branch that must never be touched
    _sh(work, "checkout", "-qb", "pr-head")
    (work / "c.txt").write_text("c\n")
    _sh(work, "add", "-A")
    _sh(work, "commit", "-qm", "open pr work")
    _sh(work, "push", "-qu", "origin", "pr-head")
    _sh(work, "checkout", "-q", "develop")
    _sh(work, "branch", "-qD", "pr-head")

    # an orphan tag on a commit no kept branch contains
    _sh(work, "checkout", "-qb", "throwaway")
    (work / "d.txt").write_text("d\n")
    _sh(work, "add", "-A")
    _sh(work, "commit", "-qm", "never merged")
    _sh(work, "tag", "orphaned-tag")
    _sh(work, "checkout", "-q", "develop")
    _sh(work, "branch", "-qD", "throwaway")

    # a tag on kept history (never orphan), a live local matching the open PR head,
    # and an unmerged-but-tracked local: three things the survey must leave alone
    _sh(work, "tag", "kept-tag", "develop")
    _sh(work, "branch", "pr-head", "origin/pr-head")
    _sh(work, "checkout", "-qb", "wip-local")
    (work / "e.txt").write_text("e\n")
    _sh(work, "add", "-A")
    _sh(work, "commit", "-qm", "unfinished")
    _sh(work, "push", "-qu", "origin", "wip-local")
    _sh(work, "checkout", "-q", "develop")

    (work / "wip.txt").write_text("human mess — welcome\n")
    (work / "a.txt").write_text("stashable\n")
    _sh(work, "stash", "push", "-q", "-m", "keep me")

    # gh is stubbed: one open PR (pr-head), one draft release
    def fake_gh(cmd, cwd=None, capture_output=True, text=True, check=False):
        class R:
            returncode = 0
            stdout = ""

        r = R()
        if cmd[:3] == ["gh", "pr", "list"]:
            r.stdout = '[{"headRefName": "pr-head"}]'
        elif cmd[:3] == ["gh", "release", "list"]:
            r.stdout = '[{"tagName": "v9.9.9-draft", "isDraft": true}, {"tagName": "v1.0.0", "isDraft": false}]'
        return r

    real_run = subprocess.run

    def router(cmd, **kw):
        if cmd and cmd[0] == "gh":
            return fake_gh(cmd, **kw)
        return real_run(cmd, **kw)

    monkeypatch.setattr(tidy.subprocess, "run", router)
    cfg = GhConfig(root=work)
    return work, cfg


def test_survey_finds_every_class_and_spares_the_human_mess(repos):
    _work, cfg = repos
    report = tidy.survey(cfg)
    assert report.remote_merged == ("merged-work",)
    assert report.local_merged == ("merged-work",)
    assert report.local_gone == ("gone-work",)
    assert "pr-head" not in report.remote_merged
    assert report.draft_releases == ("v9.9.9-draft",)
    assert report.orphan_tags == ("orphaned-tag",)
    assert "kept-tag" not in report.orphan_tags
    assert "pr-head" not in report.local_merged and "pr-head" not in report.local_gone
    assert "wip-local" not in report.local_merged
    assert report.stashes == 1
    assert report.untracked >= 1
    assert report.clean is False
    assert report.deletable == 3


def test_ci_mode_surveys_only_the_cloud_classes(repos):
    _work, cfg = repos
    report = tidy.survey(cfg, local=False)
    assert report.remote_merged == ("merged-work",)
    assert report.local_merged == ()
    assert report.local_gone == ()
    assert report.stashes == 0 and report.untracked == 0


def test_apply_deletes_both_proof_classes_and_nothing_human(repos):
    work, cfg = repos
    report = tidy.survey(cfg)
    actions = tidy.apply(cfg, report)
    assert any("deleted origin/merged-work" in a for a in actions)
    assert any("deleted local merged-work" in a for a in actions)
    assert any("deleted local gone-work" in a for a in actions)
    after = tidy.survey(cfg)
    assert after.deletable == 0
    # the human's material survives untouched
    assert after.stashes == 1
    assert after.untracked >= 1
    assert (work / "wip.txt").exists()
    # drafts and orphan tags remain: reported, never machine-removed
    assert after.draft_releases == ("v9.9.9-draft",)
    assert after.orphan_tags == ("orphaned-tag",)


def test_forge_deletion_proof_can_be_declined(repos):
    work, cfg = repos
    cfg = GhConfig(root=work, tidy=TidyConfig(trust_forge_deletions=False))
    report = tidy.survey(cfg)
    tidy.apply(cfg, report)
    names = _sh(work, "branch", "--format=%(refname:short)")
    assert "gone-work" in names
    assert "merged-work" not in names


def test_missing_kept_branches_refuse_to_judge(tmp_path: Path):
    work = tmp_path / "solo"
    subprocess.run(["git", "init", "-q", work], check=True)
    report = tidy.survey(GhConfig(root=work))
    assert report.problems and "refusing to judge" in report.problems[0]
    assert report.clean is False or report.deletable == 0


def test_prunable_worktrees_are_detected_and_pruned(repos):
    work, cfg = repos
    healthy = work.parent / "healthy-wt"
    _sh(work, "worktree", "add", "-q", "--detach", str(healthy), "develop")
    wt = work.parent / "wt"
    _sh(work, "worktree", "add", "-q", "--detach", str(wt), "develop")
    import shutil

    shutil.rmtree(wt)
    report = tidy.survey(cfg)
    assert len(report.prunable_worktrees) == 1
    assert str(healthy) not in report.prunable_worktrees
    actions = tidy.apply(cfg, report)
    assert any("pruned 1 worktree" in a for a in actions)
    assert tidy.survey(cfg).prunable_worktrees == ()


def test_apply_reports_a_failed_deletion_without_raising(repos, monkeypatch):
    _work, cfg = repos
    report = tidy.survey(cfg)

    class Fail:
        returncode = 1

    actions = tidy.apply(cfg, report, run=lambda *a, **k: Fail())
    assert any("could not delete" in a for a in actions)


def test_gh_failures_and_garbage_are_survivable(repos, monkeypatch):
    _work, cfg = repos

    real_run = subprocess.run

    def garbled_gh(cmd, **kw):
        if cmd and cmd[0] == "gh":

            class R:
                returncode = 0
                stdout = "not json" if "pr" in cmd else '"a bare string is not a listing"'

            return R()
        return real_run(cmd, **kw)

    monkeypatch.setattr(tidy.subprocess, "run", garbled_gh)
    report = tidy.survey(cfg)
    assert report.draft_releases == ()
    # with pr list unreadable, no head is exempt — but nothing crashes
    assert isinstance(report.remote_merged, tuple)

    def refusing_gh(cmd, **kw):
        if cmd and cmd[0] == "gh":

            class R:
                returncode = 1
                stdout = ""

            return R()
        return real_run(cmd, **kw)

    monkeypatch.setattr(tidy.subprocess, "run", refusing_gh)
    report = tidy.survey(cfg)
    assert report.draft_releases == ()


def test_tidy_config_loads_from_toml(tmp_path: Path):
    (tmp_path / ".vibey-gh.toml").write_text(
        '[tidy]\nenabled = false\nkeep_branches = ["lts"]\ntrust_forge_deletions = false\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.tidy.enabled is False
    assert cfg.tidy.keep_branches == ("lts",)
    assert cfg.tidy.trust_forge_deletions is False
    assert load_config.__module__  # keep the import honest


def test_tidy_cli_reports_applies_and_confirms_clean(repos, monkeypatch, capsys):
    from vibey_gh.cli import main

    work, _cfg = repos
    monkeypatch.chdir(work)
    assert main(["tidy"]) == 1
    out = capsys.readouterr().out
    assert "technical clutter present" in out
    assert "yours, untouched" in out
    assert main(["tidy", "--apply"]) == 0
    out = capsys.readouterr().out
    assert "deleted origin/merged-work" in out
    # drafts and orphan tags still stand: the human's call, so the survey is not
    # clean — but everything machine-deletable is gone.
    assert main(["tidy"]) == 1
    out = capsys.readouterr().out
    assert "draft releases" in out and "orphan tags" in out


def test_tidy_cli_ci_mode_and_problem_path(repos, tmp_path, monkeypatch, capsys):
    from vibey_gh.cli import main

    work, _cfg = repos
    monkeypatch.chdir(work)
    assert main(["tidy", "--ci"]) == 1
    assert "merged remote branches" in capsys.readouterr().out
    solo = tmp_path / "solo"
    subprocess.run(["git", "init", "-q", solo], check=True)
    monkeypatch.chdir(solo)
    assert main(["tidy"]) == 1
    assert "refusing to judge" in capsys.readouterr().err


def test_tidy_cli_clean_repo_says_so(tmp_path, monkeypatch, capsys):
    from vibey_gh.cli import main

    origin = tmp_path / "o.git"
    subprocess.run(["git", "init", "-q", "--bare", origin], check=True)
    work = tmp_path / "w"
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
    _sh(work, "config", "user.email", "t@example.com")
    _sh(work, "config", "user.name", "t")
    (work / "a.txt").write_text("a")
    _sh(work, "add", "-A")
    _sh(work, "commit", "-qm", "base")
    _sh(work, "branch", "-M", "develop")
    _sh(work, "push", "-qu", "origin", "develop")
    _sh(work, "push", "-q", "origin", "develop:main")

    def no_gh(cmd, **kw):
        if cmd and cmd[0] == "gh":

            class R:
                returncode = 0
                stdout = "[]"

            return R()
        return (
            subprocess.run.__wrapped__(cmd, **kw)
            if hasattr(subprocess.run, "__wrapped__")
            else _REAL(cmd, **kw)
        )

    global _REAL
    _REAL = tidy.subprocess.run
    monkeypatch.setattr(tidy.subprocess, "run", no_gh)
    monkeypatch.chdir(work)
    assert main(["tidy"]) == 0
    assert "clean — no technical clutter" in capsys.readouterr().out


def test_survey_survives_crafted_git_output(repos, monkeypatch):
    """Defensive guards for output shapes real git rarely emits: blank tag lines
    and worktree stanzas with no path line."""
    _work, cfg = repos
    real = tidy._git

    def crafted(root, *args):
        if args[:2] == ("tag", "--list"):
            return "\n  \n" + real(root, *args)
        if args[:2] == ("worktree", "list"):
            return "prunable ghost\n\n" + real(root, *args)
        return real(root, *args)

    monkeypatch.setattr(tidy, "_git", crafted)
    report = tidy.survey(cfg)
    assert report.orphan_tags == ("orphaned-tag",)
    assert all(p for p in report.prunable_worktrees)
