# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import subprocess

import pytest

import qwenloop.infrastructure.github as github
from qwenloop.domain.model import RepoItem


class Result:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


def test_gh_missing_reports_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(github.shutil, "which", lambda _name: None)
    assert github.list_repo_names("owner") is None
    assert github.list_open_issues("owner", "repo") is None
    assert github.list_open_pull_requests("owner", "repo") is None


def test_repo_list_success_and_filters_bad_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(github.shutil, "which", lambda _name: "/usr/bin/gh")
    payload = '[{"name": "a"}, {"name": "b"}, {"nope": 1}, "not-a-dict"]'
    monkeypatch.setattr(github.subprocess, "run", lambda *_args, **_kwargs: Result(payload))
    assert github.list_repo_names("owner") == ["a", "b"]


def test_repo_list_handles_non_list_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(github.shutil, "which", lambda _name: "/usr/bin/gh")
    monkeypatch.setattr(github.subprocess, "run", lambda *_args, **_kwargs: Result("{}"))
    assert github.list_repo_names("owner") is None


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.CalledProcessError(1, ["gh"]),
        subprocess.TimeoutExpired(["gh"], 30),
        OSError("no such file"),
        ValueError("bad json"),
    ],
)
def test_repo_list_reports_failures_as_none(
    monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    monkeypatch.setattr(github.shutil, "which", lambda _name: "/usr/bin/gh")

    def fail(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise failure

    monkeypatch.setattr(github.subprocess, "run", fail)
    assert github.list_repo_names("owner") is None


def test_open_issues_and_pull_requests_parse_items(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(github.shutil, "which", lambda _name: "/usr/bin/gh")
    payload = (
        '[{"number": 1, "title": "fix it", "body": "details"}, '
        '{"number": 2, "title": "no body"}, '
        '{"title": "missing number"}]'
    )
    monkeypatch.setattr(github.subprocess, "run", lambda *_args, **_kwargs: Result(payload))
    issues = github.list_open_issues("owner", "repo")
    assert issues == [
        RepoItem(number=1, title="fix it", body="details"),
        RepoItem(number=2, title="no body", body=""),
    ]
    prs = github.list_open_pull_requests("owner", "repo")
    assert prs == issues


def test_open_issues_command_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(github.shutil, "which", lambda _name: "/usr/bin/gh")
    captured: list[list[str]] = []

    def record(argv, **_kwargs):  # type: ignore[no-untyped-def]
        captured.append(list(argv))
        return Result("[]")

    monkeypatch.setattr(github.subprocess, "run", record)
    assert github.list_open_issues("acme", "widgets") == []
    assert captured[0] == [
        "/usr/bin/gh",
        "issue",
        "list",
        "-R",
        "acme/widgets",
        "--state",
        "open",
        "--json",
        "number,title,body",
    ]
