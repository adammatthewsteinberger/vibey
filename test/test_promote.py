# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Promotion: the half of the flow that used to be a hand-written workflow per repository.

Driven against a real bare repository over file:// and a fake `gh` on PATH, because the
things that go wrong here — comparing by commit count instead of content, promoting
without a version bump, merging before the checks land — are all in the interaction, not
in any single function.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from vibey_gh import promote as promote_mod
from vibey_gh.config import GhConfig


def git(cwd: Path, *a: str) -> str:
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    """A bare origin plus a clone with develop and main at the same commit."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)

    work = tmp_path / "work"
    work.mkdir()
    git(work, "init", "-q", "-b", "main", ".")
    git(work, "config", "user.email", "t@example.com")
    git(work, "config", "user.name", "t")
    (work / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "1.0.0"\n')
    (work / "content").mkdir()
    (work / "content" / "a.md").write_text("a\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "base")
    git(work, "remote", "add", "origin", str(origin))
    git(work, "push", "-q", "origin", "main")
    git(work, "push", "-q", "origin", "main:develop")
    git(work, "fetch", "-q", "origin")
    monkeypatch.chdir(work)
    return work


def cfg_for(root: Path) -> GhConfig:
    return GhConfig(
        root=root,
        version_files=("pyproject.toml",),
        content_paths=("content/",),
        code_paths=("src/",),
        integration_branch="develop",
        release_branch="main",
    )


@pytest.fixture
def fake_gh(tmp_path: Path, monkeypatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(f"""#!/usr/bin/env python3
import json, pathlib, sys
here = pathlib.Path({str(bin_dir)!r})
with (here / "calls.txt").open("a") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\\n")
answers = json.loads((here / "answers.json").read_text())
for key, entry in answers.items():
    if " ".join(sys.argv[1:]).startswith(key):
        sys.stdout.write(entry.get("out", ""))
        raise SystemExit(entry.get("code", 0))
sys.stderr.write("no scripted answer\\n")
raise SystemExit(3)
""")
    gh.chmod(0o755)
    (bin_dir / "answers.json").write_text("{}")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return bin_dir


def script(bin_dir: Path, answers: dict) -> None:
    (bin_dir / "answers.json").write_text(json.dumps(answers))


def calls(bin_dir: Path) -> list[str]:
    path = bin_dir / "calls.txt"
    return path.read_text().splitlines() if path.exists() else []


def advance_develop(work: Path, message: str = "new content") -> None:
    git(work, "checkout", "-qB", "develop", "origin/develop")
    (work / "content" / "b.md").write_text(message + "\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", message)
    git(work, "push", "-q", "origin", "develop")
    git(work, "fetch", "-q", "origin")


# ── nothing to do ──────────────────────────────────────────────────────────


def test_the_release_commit_is_itself_a_conventional_commit():
    """This subject does not stay on the release branch.

    Any topic branch that later merges the integration branch in pulls it into its own
    commit range, where the provenance gate reads it like any other commit. `Release
    1.23.0` blocked a pull request exactly that way, and the repair could not fix it by
    editing files because the problem was history rather than content.
    """
    from vibey_gh.fingerprints import conventional_subject
    from vibey_gh.promote import promote as _promote

    source = Path(_promote.__code__.co_filename).read_text(encoding="utf-8")
    assert "chore(release): " in source
    assert '"Release {' not in source and 'f"Release ' not in source
    for version in ("1.23.0", "2.0.0", "0.1.0.dev3"):
        assert conventional_subject(f"chore(release): {version}")


def test_identical_trees_promote_nothing(project, fake_gh):
    result = promote_mod.promote(cfg_for(project), wait=True)
    assert result.pull_request is None
    assert "nothing to promote" in " ".join(result.notes)
    assert not calls(fake_gh)  # and it does not even talk to GitHub


def test_a_rewritten_history_with_the_same_tree_is_still_nothing(project, fake_gh):
    """The case a commit count gets wrong: rebase-merging leaves divergent histories."""
    git(project, "checkout", "-qB", "develop", "origin/develop")
    git(project, "commit", "-q", "--allow-empty", "-m", "rewritten copy")
    git(project, "push", "-q", "origin", "develop")
    git(project, "fetch", "-q", "origin")
    assert git(project, "rev-parse", "origin/develop") != git(project, "rev-parse", "origin/main")

    result = promote_mod.promote(cfg_for(project), wait=True)
    assert "nothing to promote" in " ".join(result.notes)


# ── the happy path ─────────────────────────────────────────────────────────


def test_a_content_change_bumps_opens_waits_and_merges(project, fake_gh):
    advance_develop(project)
    script(
        fake_gh,
        {
            "pr list": {"out": "\n"},
            "pr create": {"out": "https://github.com/o/r/pull/42\n"},
            "pr checks 42": {},
            "pr merge 42 --rebase": {},
        },
    )

    result = promote_mod.promote(cfg_for(project), wait=True)

    assert result.bumped == "1.1.0"  # content changed -> minor
    assert result.version == "1.1.0"
    assert result.pull_request == 42
    assert result.merged is True and result.bypassed is False
    # the bump was pushed, so the promotion actually publishes something
    assert 'version = "1.1.0"' in git(project, "show", "origin/develop:pyproject.toml")
    joined = " ".join(calls(fake_gh))
    assert "pr checks 42 --watch" in joined  # it waited


def test_an_existing_pull_request_is_reused(project, fake_gh):
    advance_develop(project)
    script(
        fake_gh,
        {
            "pr list": {"out": "7\n"},
            "pr checks 7": {},
            "pr merge 7 --rebase": {},
        },
    )
    result = promote_mod.promote(cfg_for(project), wait=True)
    assert result.pull_request == 7
    assert "reusing #7" in " ".join(result.notes)
    assert not [c for c in calls(fake_gh) if c.startswith("pr create")]


def test_a_ruleset_that_refuses_the_plain_merge_falls_back_to_admin(project, fake_gh):
    advance_develop(project)
    script(
        fake_gh,
        {
            "pr list": {"out": "7\n"},
            "pr checks 7": {},
            "pr merge 7 --rebase --admin": {},
        },
    )
    result = promote_mod.promote(cfg_for(project), wait=True)
    assert result.merged is True and result.bypassed is True


def test_a_merge_nothing_can_satisfy_leaves_the_pull_request_open(project, fake_gh):
    advance_develop(project)
    script(fake_gh, {"pr list": {"out": "7\n"}, "pr checks 7": {}})
    result = promote_mod.promote(cfg_for(project), wait=True)
    assert result.merged is False
    assert "open and green for a human" in " ".join(result.notes)


# ── the guards ─────────────────────────────────────────────────────────────


def test_failing_checks_stop_the_merge(project, fake_gh):
    advance_develop(project)
    script(
        fake_gh,
        {
            "pr list": {"out": "7\n"},
            "pr checks 7": {"code": 1},
        },
    )
    result = promote_mod.promote(cfg_for(project), wait=True)
    assert result.merged is False
    assert "checks did not pass" in " ".join(result.notes)
    assert not [c for c in calls(fake_gh) if c.startswith("pr merge")]


def test_event_driven_mode_does_not_wait_or_merge(project, fake_gh):
    advance_develop(project)
    script(fake_gh, {"pr list": {"out": "7\n"}, "pr merge 7 --rebase": {}})
    result = promote_mod.promote(cfg_for(project), wait=False)
    assert result.merged is False
    assert not [c for c in calls(fake_gh) if c.startswith("pr checks")]
    assert not [c for c in calls(fake_gh) if c.startswith("pr merge")]
    assert "event-driven" in " ".join(result.notes)


def test_a_bump_that_cannot_be_pushed_is_fatal(project, fake_gh):
    """An unpushed bump means the promotion publishes nothing — silently, without this."""
    advance_develop(project)
    origin = project.parent / "origin.git" / "hooks"
    origin.mkdir(exist_ok=True)
    (origin / "pre-receive").write_text("#!/bin/sh\nexit 1\n")
    (origin / "pre-receive").chmod(0o755)

    with pytest.raises(RuntimeError, match="publish nothing"):
        promote_mod.promote(cfg_for(project))


def test_a_pull_request_that_cannot_be_opened_is_fatal(project, fake_gh):
    advance_develop(project)
    script(fake_gh, {"pr list": {"out": "\n"}})  # create has no scripted answer
    with pytest.raises(RuntimeError, match="could not open"):
        promote_mod.promote(cfg_for(project))


# ── dry run ────────────────────────────────────────────────────────────────


def test_a_dry_run_bumps_nothing_and_opens_nothing(project, fake_gh):
    advance_develop(project)
    result = promote_mod.promote(cfg_for(project), dry_run=True)

    assert result.bumped == "1.1.0"
    assert "would bump to 1.1.0" in " ".join(result.notes)
    assert result.pull_request is None
    assert 'version = "1.0.0"' in git(project, "show", "origin/develop:pyproject.toml")
    assert not [c for c in calls(fake_gh) if c.startswith("pr create")]


def test_a_promotion_with_nothing_to_bump_still_proceeds(project, fake_gh):
    """Docs and CI reach no installed user; `none` is a legitimate answer."""
    git(project, "checkout", "-qB", "develop", "origin/develop")
    (project / "README.md").write_text("docs\n")
    git(project, "add", "-A")
    git(project, "commit", "-qm", "docs only")
    git(project, "push", "-q", "origin", "develop")
    git(project, "fetch", "-q", "origin")

    script(fake_gh, {"pr list": {"out": "7\n"}, "pr checks 7": {}, "pr merge 7 --rebase": {}})
    result = promote_mod.promote(cfg_for(project), wait=True)

    assert result.bumped is None
    assert result.merged is True
    assert "none reach an installed user" in " ".join(result.notes)


def test_a_deliberate_bump_already_in_place_is_not_doubled(project, fake_gh):
    advance_develop(project)
    git(project, "checkout", "-qB", "develop", "origin/develop")
    (project / "pyproject.toml").write_text('[project]\nname = "demo"\nversion = "2.0.0"\n')
    git(project, "add", "-A")
    git(project, "commit", "-qm", "bump by hand")
    git(project, "push", "-q", "origin", "develop")
    git(project, "fetch", "-q", "origin")

    script(fake_gh, {"pr list": {"out": "7\n"}, "pr checks 7": {}, "pr merge 7 --rebase": {}})
    result = promote_mod.promote(cfg_for(project))
    assert result.bumped is None
    assert result.version == "2.0.0"
