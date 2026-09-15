# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Immutable version tags and idempotent GitHub Releases."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vibey_gh import github_release
from vibey_gh.config import GhConfig, GithubReleaseConfig, load_config


def cfg(tmp_path: Path, **release) -> GhConfig:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"\nversion="1.2.3"\n')
    return GhConfig(
        root=tmp_path,
        version_files=("pyproject.toml",),
        github_release=GithubReleaseConfig(**release),
    )


def done(code=0, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


def test_run_uses_noninteractive_subprocess(monkeypatch):
    seen = []
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **kwargs: seen.append((args, kwargs)) or done(),
    )
    assert github_release._run("gh", "--version").returncode == 0
    assert seen == [
        (["gh", "--version"], {"cwd": None, "capture_output": True, "text": True, "check": False})
    ]


def fake(monkeypatch, answers):
    calls = []

    def run(*args):
        calls.append(args)
        for prefix, result in answers:
            if args[: len(prefix)] == prefix:
                return result
        return done(1, err="missing")

    monkeypatch.setattr(github_release, "_run", run)
    return calls


def test_config_parses_and_validates(tmp_path):
    (tmp_path / ".vibey-gh.toml").write_text(
        '[github_release]\nenabled=false\ntag_prefix="release-"\ngenerate_notes=false\n'
        "require_new_version=true\n"
    )
    value = load_config(tmp_path).github_release
    assert value == GithubReleaseConfig(False, "release-", False, True)
    for prefix in ("", "bad tag"):
        with pytest.raises(ValueError, match="tag_prefix"):
            GithubReleaseConfig(tag_prefix=prefix)


def test_existing_matching_tag_and_release_are_idempotent(monkeypatch, tmp_path):
    calls = fake(
        monkeypatch,
        [
            (("gh", "repo", "view"), done(out='{"nameWithOwner":"o/r"}')),
            (("gh", "api"), done(out='{"object":{"sha":"abc"}}')),
            (("gh", "release", "view"), done()),
        ],
    )
    result = github_release.publish(cfg(tmp_path), target="abc")
    assert result == github_release.ReleaseResult("v1.2.3", "abc", False, False)
    assert not any("create" in call for call in calls)


def test_creates_tag_and_generated_release(monkeypatch, tmp_path):
    calls = fake(
        monkeypatch,
        [
            (("gh", "repo", "view"), done(out='{"nameWithOwner":"o/r"}')),
            (("gh", "api", "repos/o/r/git/ref/tags/v2.0.0"), done(1)),
            (("gh", "api", "repos/o/r/git/refs"), done()),
            (("gh", "release", "view"), done(1)),
            (("gh", "release", "create"), done()),
        ],
    )
    result = github_release.publish(cfg(tmp_path), target="def", version="2.0.0")
    assert result.tag_created and result.release_created
    create = next(call for call in calls if call[:3] == ("gh", "release", "create"))
    assert "--generate-notes" in create and "--target" in create


def test_release_without_generated_notes(monkeypatch, tmp_path):
    calls = fake(
        monkeypatch,
        [
            (("gh", "repo", "view"), done(out='{"nameWithOwner":"o/r"}')),
            (("gh", "api"), done(out='{"object":{"sha":"abc"}}')),
            (("gh", "release", "view"), done(1)),
            (("gh", "release", "create"), done()),
        ],
    )
    github_release.publish(cfg(tmp_path, tag_prefix="release-", generate_notes=False), target="abc")
    assert "--generate-notes" not in calls[-1]


@pytest.mark.parametrize(
    "answers,match",
    [
        ([(("gh", "repo", "view"), done(1, err="no repo"))], "identify"),
        (
            [
                (("gh", "repo", "view"), done(out='{"nameWithOwner":"o/r"}')),
                (("gh", "api", "repos/o/r/git/ref"), done(1)),
                (("gh", "api", "repos/o/r/git/refs"), done(1, err="denied")),
            ],
            "could not create immutable tag",
        ),
        (
            [
                (("gh", "repo", "view"), done(out='{"nameWithOwner":"o/r"}')),
                (("gh", "api"), done(out='{"object":{"sha":"abc"}}')),
                (("gh", "release", "view"), done(1)),
                (("gh", "release", "create"), done(1, err="denied")),
            ],
            "Release creation failed",
        ),
    ],
)
def test_release_failures_are_safe(monkeypatch, tmp_path, answers, match):
    fake(monkeypatch, answers)
    with pytest.raises(RuntimeError, match=match):
        github_release.publish(cfg(tmp_path), target="abc")


def test_existing_tag_at_other_sha_is_a_no_op_by_default(monkeypatch, tmp_path):
    calls = fake(
        monkeypatch,
        [
            (("gh", "repo", "view"), done(out='{"nameWithOwner":"o/r"}')),
            (("gh", "api"), done(out='{"object":{"sha":"other"}}')),
        ],
    )
    result = github_release.publish(cfg(tmp_path), target="abc")
    assert result == github_release.ReleaseResult("v1.2.3", "other", False, False)
    assert len(calls) == 2  # never reaches the release-view/create step


def test_existing_tag_at_other_sha_raises_when_new_version_required(monkeypatch, tmp_path):
    fake(
        monkeypatch,
        [
            (("gh", "repo", "view"), done(out='{"nameWithOwner":"o/r"}')),
            (("gh", "api"), done(out='{"object":{"sha":"other"}}')),
        ],
    )
    with pytest.raises(RuntimeError, match="refusing to move"):
        github_release.publish(cfg(tmp_path, require_new_version=True), target="abc")


def test_disabled_release_does_not_touch_github(monkeypatch, tmp_path):
    monkeypatch.setattr(github_release, "_run", lambda *a: pytest.fail("must not call GitHub"))
    with pytest.raises(RuntimeError, match="disabled"):
        github_release.publish(cfg(tmp_path, enabled=False), target="abc")
