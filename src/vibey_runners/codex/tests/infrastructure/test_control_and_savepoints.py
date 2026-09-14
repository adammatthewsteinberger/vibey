# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Inbox control plane and git savepoints."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from codexloop.domain.control import Prompt, PromptTiming, Stop, WindDownCommand, parse_control
from codexloop.domain.errors import ConfigurationError
from codexloop.domain.savepoint_message import format_savepoint_commit_message
from codexloop.infrastructure.control import CompositeRunControl, FileRunControl
from codexloop.infrastructure.git_savepoints import GitSavePointStore
from tests.application.fakes import FakeLogger, FakeRunControl


def test_inbox_command_archived_after_single_poll(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    control = FileRunControl(inbox)
    path = control.enqueue(Stop())
    assert path.is_file()

    commands = list(control.poll())
    assert commands == [Stop()]
    assert not path.exists()
    assert (inbox / "archive" / path.name).is_file()

    assert list(control.poll()) == []


def test_malformed_inbox_file_is_quarantined_with_log(tmp_path: Path) -> None:
    logger = FakeLogger()
    inbox = tmp_path / "inbox"
    control = FileRunControl(inbox, logger=logger)
    bad = inbox / "1-bad.json"
    bad.write_text("{not-json\n", encoding="utf-8")

    assert list(control.poll()) == []
    assert not bad.exists()
    assert (inbox / "quarantine" / bad.name).is_file()
    warnings = [event for level, event, _ in logger.events if level == "warning"]
    assert "control.quarantined" in warnings


def test_unknown_kind_is_quarantined_not_raised(tmp_path: Path) -> None:
    logger = FakeLogger()
    control = FileRunControl(tmp_path / "inbox", logger=logger)
    path = tmp_path / "inbox" / "2-unknown.json"
    path.write_text(json.dumps({"kind": "nope"}) + "\n", encoding="utf-8")

    assert list(control.poll()) == []
    assert (tmp_path / "inbox" / "quarantine" / path.name).is_file()


def test_composite_merges_drain_and_inbox(tmp_path: Path) -> None:
    inbox = FileRunControl(tmp_path / "inbox")
    inbox.enqueue(Prompt(text="hi", timing=PromptTiming.NOW))
    drain = FakeRunControl([Stop()])
    merged = CompositeRunControl(drain, inbox)
    kinds = [type(c).__name__ for c in merged.poll()]
    assert kinds == ["Stop", "Prompt"]


def test_wind_down_command_round_trips_through_inbox(tmp_path: Path) -> None:
    """WindDownCommand can be enqueued and polled back through FileRunControl."""
    inbox = tmp_path / "inbox"
    control = FileRunControl(inbox)
    cmd = WindDownCommand(reason="capacity exhausted")
    path = control.enqueue(cmd)
    assert path.is_file()

    commands = list(control.poll())
    assert commands == [cmd]
    assert not path.exists()
    assert (inbox / "archive" / path.name).is_file()


def test_savepoint_subject_format() -> None:
    subject, body = format_savepoint_commit_message(
        run_id="run-1",
        attempt=3,
        verdict_name="Continue",
        summary="Add login",
        changed_paths=("src/a.py",),
        label="turn",
    )
    assert subject.startswith("chore(codexloop): turn 3 — ")
    assert "Add login" in subject
    assert "Run: run-1" in body


def _git_init(cwd: Path) -> None:
    subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=cwd, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=cwd, check=True)
    (cwd / "README").write_text("hi\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=cwd, check=True, capture_output=True)


def test_savepoint_commits_when_tree_changes(tmp_path: Path) -> None:
    _git_init(tmp_path)
    index = tmp_path / ".codexloop" / "savepoints.jsonl"
    index.parent.mkdir(parents=True, exist_ok=True)
    store = GitSavePointStore(cwd=tmp_path, index_path=index)
    (tmp_path / "src.py").write_text("x = 1\n", encoding="utf-8")
    point = store.create(run_id="r1", label="turn", attempt=1, summary="Add src")
    assert point is not None
    assert point.committed is True
    assert point.ref.startswith("refs/codexloop/r1/")
    log = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert log.stdout.strip().startswith("chore(codexloop): turn 1 — ")


def test_savepoint_ref_only_when_unchanged(tmp_path: Path) -> None:
    _git_init(tmp_path)
    index = tmp_path / ".codexloop" / "savepoints.jsonl"
    index.parent.mkdir(parents=True, exist_ok=True)
    store = GitSavePointStore(cwd=tmp_path, index_path=index)
    first = store.create(run_id="r1", label="a", attempt=1, summary="noop")
    second = store.create(run_id="r1", label="b", attempt=2, summary="noop")
    assert first is not None and second is not None
    assert first.committed is False
    assert second.committed is False
    assert first.sha == second.sha
    assert first.n != second.n


def test_savepoint_excludes_codexloop_dir(tmp_path: Path) -> None:
    _git_init(tmp_path)
    index = tmp_path / ".codexloop" / "savepoints.jsonl"
    index.parent.mkdir(parents=True, exist_ok=True)
    store = GitSavePointStore(cwd=tmp_path, index_path=index)
    (tmp_path / ".codexloop" / "noise").write_text("x\n", encoding="utf-8")
    point = store.create(run_id="r1", label="a", attempt=1, summary="control only")
    assert point is not None
    assert point.committed is False


def test_unwind_refuses_while_live(tmp_path: Path) -> None:
    _git_init(tmp_path)
    index = tmp_path / ".codexloop" / "savepoints.jsonl"
    index.parent.mkdir(parents=True, exist_ok=True)
    store = GitSavePointStore(cwd=tmp_path, index_path=index)
    store.create(run_id="r1", label="a", attempt=1, summary="init")
    with pytest.raises(ConfigurationError, match="live"):
        store.unwind(run_id="r1", to="1", backup=False, live=True)


def test_parse_control_roundtrip_for_inbox_payload() -> None:
    raw = Stop().to_dict()
    assert parse_control(raw) == Stop()
