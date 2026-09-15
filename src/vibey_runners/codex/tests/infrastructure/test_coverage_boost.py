# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Fill remaining infrastructure coverage gaps with focused unit cases."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from codexloop.domain.errors import ConfigurationError
from codexloop.domain.savepoint import SavePointRef
from codexloop.infrastructure.agent import events as events_mod
from codexloop.infrastructure.agent.process import _StdoutCollector
from codexloop.infrastructure.clock import AnyioSleeper, SystemClock
from codexloop.infrastructure.config import _coerce_field
from codexloop.infrastructure.control import FileRunControl
from codexloop.infrastructure.git_savepoints import GitSavePointStore
from codexloop.infrastructure.snapshot import create_snapshot, restore_snapshot
from tests.application.fakes import FakeClock, FakeLogger


def test_opt_int_rejects_bool() -> None:
    assert events_mod._opt_int(True) is None
    assert events_mod._opt_int(3.0) == 3


@pytest.mark.anyio
async def test_sleeper_sleeps_when_future(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []

    async def fake_sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr("codexloop.infrastructure.clock.anyio.sleep", fake_sleep)
    clock = FakeClock(datetime(2026, 1, 1, tzinfo=UTC))
    sleeper = AnyioSleeper(clock)
    await sleeper.sleep_until(clock.now() + timedelta(seconds=2))
    assert slept == [2.0]
    assert SystemClock().now().tzinfo is UTC


def test_coerce_field_fallback() -> None:
    assert _coerce_field("mystery", 9) == 9


def test_control_rejects_non_object_payload(tmp_path: Path) -> None:
    logger = FakeLogger()
    control = FileRunControl(tmp_path / "inbox", logger=logger)
    bad = tmp_path / "inbox" / "1.json"
    bad.write_text("[1]\n", encoding="utf-8")
    assert list(control.poll()) == []
    assert (tmp_path / "inbox" / "quarantine" / "1.json").is_file()


def test_control_quarantine_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    logger = FakeLogger()
    control = FileRunControl(tmp_path / "inbox", logger=logger)
    path = tmp_path / "inbox" / "1.json"
    path.write_text("{not-json\n", encoding="utf-8")

    def boom(self: Path, target: Path) -> None:
        raise OSError("busy")

    monkeypatch.setattr(Path, "replace", boom)
    assert list(control.poll()) == []
    warnings = [e for level, e, _ in logger.events if level == "warning"]
    assert "control.quarantined" in warnings


def test_stdout_collector_truncation_paths() -> None:
    collector = _StdoutCollector(max_line_bytes=4)
    collector.feed(b"ab")
    collector.feed(b"cdef\n")  # overflows with newline
    assert collector.truncated_lines == 1
    collector.feed(b"zzzz")  # overflow without newline → skipping
    collector.feed(b"more\nok\n")
    collector.feed(b"tail")
    collector.flush()
    assert "ok" in collector.lines
    assert collector.lines[-1] == "tail"


def test_snapshot_skips_and_restores(tmp_path: Path) -> None:
    src = tmp_path / "workspace"
    src.mkdir()
    (src / "file.txt").write_text("a\n", encoding="utf-8")
    (src / "dir").mkdir()
    (src / "dir" / "nested.txt").write_text("b\n", encoding="utf-8")
    (src / ".codexloop").mkdir()
    (src / ".codexloop" / "x").write_text("skip\n", encoding="utf-8")
    dest = tmp_path / "snap"
    create_snapshot(cwd=src, dest=dest)
    assert not (dest / ".codexloop").exists()
    assert (dest / "dir" / "nested.txt").is_file()

    (src / "dir" / "nested.txt").write_text("changed\n", encoding="utf-8")
    restore_snapshot(snapshot=dest, cwd=src)
    assert (src / "dir" / "nested.txt").read_text(encoding="utf-8") == "b\n"
    assert (src / "file.txt").read_text(encoding="utf-8") == "a\n"


def _git_init(cwd: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=cwd, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=cwd, check=True)
    (cwd / "README").write_text("hi\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=cwd, check=True, capture_output=True)


def test_git_savepoints_list_unwind_and_errors(tmp_path: Path) -> None:
    _git_init(tmp_path)
    index = tmp_path / ".codexloop" / "savepoints.jsonl"
    store = GitSavePointStore(cwd=tmp_path, index_path=index)
    # empty lines + other run skipped
    index.write_text(
        "\n"
        + json.dumps(
            {
                "run_id": "other",
                "n": 9,
                "ref": "refs/codexloop/other/9",
                "sha": "dead",
                "label": "x",
                "at": "2026-01-01T00:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert store.list_points("r1") == []

    (tmp_path / "src.py").write_text("x=1\n", encoding="utf-8")
    point = store.create(run_id="r1", label="turn", attempt=1, summary="add")
    assert point is not None
    assert point.committed is True

    # clean tree → ref-only
    point2 = store.create(run_id="r1", label="clean")
    assert point2 is not None
    assert point2.committed is False

    listed = store.list_points("r1")
    assert len(listed) >= 2

    with pytest.raises(ConfigurationError, match="live"):
        store.unwind(run_id="r1", to="1", backup=False, live=True)

    result = store.unwind(run_id="r1", to="1", backup=True, live=False)
    assert result.to.n == 1
    assert result.backup_ref is not None

    result2 = store.unwind(run_id="r1", to=point.sha[:7], backup=False, live=False)
    assert result2.backup_ref is None

    result3 = store.unwind(run_id="r1", to="turn", backup=False, live=False)
    assert result3.to.label == "turn"

    with pytest.raises(ValueError, match="numbered"):
        # Longer than any real SHA, so it can never accidentally match via
        # the sha.startswith() fallback -- a short literal like "99" has a
        # real (if small) chance of prefix-matching one of the SHAs created
        # above, which intermittently failed this exact assertion in CI.
        store.unwind(run_id="r1", to="9" * 50, backup=False, live=False)
    with pytest.raises(ValueError, match="matching"):
        store.unwind(run_id="r1", to="nope", backup=False, live=False)

    # staged_paths failure path
    store2 = GitSavePointStore(cwd=tmp_path, index_path=tmp_path / "idx2.jsonl")
    monkey_result = type("R", (), {"returncode": 1, "stdout": ""})()
    original = store2._run

    def flaky(args: list[str], *, check: bool = True) -> object:
        if args[:3] == ["git", "diff", "--cached"] and "-z" in args:
            return monkey_result
        return original(args, check=check)

    store2._run = flaky  # type: ignore[method-assign]
    assert store2._staged_paths() == ()


def test_resolve_target_accepts_all_digit_sha_prefix(tmp_path: Path) -> None:
    """Short SHAs can be decimal-only; do not treat them as save-point indexes."""
    store = GitSavePointStore(cwd=tmp_path, index_path=tmp_path / "idx.jsonl")
    point = SavePointRef(
        n=1,
        ref="refs/codexloop/r1/1",
        sha="41585994ef67172a1b376616357ca2b92f4cb33d",
        label="turn",
        at=datetime.now(UTC),
        plan_item=None,
        committed=True,
    )
    assert store._resolve_target([point], "4158599") is point
    assert store._resolve_target([point], "1") is point
    with pytest.raises(ValueError, match="numbered"):
        store._resolve_target([point], "99")


def test_git_savepoints_missing_index_file(tmp_path: Path) -> None:
    store = GitSavePointStore(cwd=tmp_path, index_path=tmp_path / "missing.jsonl")
    store._index_path.unlink()
    assert store.list_points("r") == []


def test_rollout_error_and_stale_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from codexloop.infrastructure import rollout as rollout_mod

    assert rollout_mod.read_rollout_rate_limits(codex_home=tmp_path / "missing") is None

    home = tmp_path / "codex"
    home.mkdir()
    assert rollout_mod.read_rollout_rate_limits(codex_home=home) is None

    nested = home / "sessions"
    nested.mkdir()
    old = nested / "old.jsonl"
    old.write_text("{}\n", encoding="utf-8")
    import os

    os.utime(old, (0, 0))
    assert (
        rollout_mod.read_rollout_rate_limits(
            codex_home=home,
            now=datetime(2026, 1, 1, tzinfo=UTC),
            max_age=timedelta(minutes=1),
        )
        is None
    )

    def boom_walk(*_a: object, **_k: object) -> object:
        raise OSError("walk")

    monkeypatch.setattr(os, "walk", boom_walk)
    assert rollout_mod._newest_contained_jsonl(home) is None
    monkeypatch.undo()

    assert rollout_mod._contained(Path("/tmp/outside"), home) is False

    def bad_resolve(self: Path) -> Path:
        raise OSError("x")

    monkeypatch.setattr(Path, "resolve", bad_resolve)
    assert rollout_mod._contained(old, home) is False
    assert (
        rollout_mod._read(codex_home=home, max_age=timedelta(minutes=1), now=datetime.now(UTC))
        is None
    )
    monkeypatch.undo()

    def bad_stat(self: Path) -> object:
        raise OSError("stat")

    monkeypatch.setattr(Path, "stat", bad_stat)
    assert rollout_mod._is_stale(old, now=datetime.now(UTC), max_age=timedelta(minutes=1)) is True
    monkeypatch.undo()

    bad_file = home / "bad.jsonl"
    bad_file.write_bytes(b"\xff\xfe")
    assert rollout_mod._parse_file(bad_file, now=datetime.now(UTC)) is None

    def boom_read(*_a: object, **_k: object) -> object:
        raise RuntimeError("explode")

    monkeypatch.setattr(rollout_mod, "_read", boom_read)
    assert rollout_mod.read_rollout_rate_limits(codex_home=home) is None


def test_ratelimits_helpers() -> None:
    from codexloop.infrastructure.appserver import ratelimits as rl

    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert rl.plan_windows_from_rpc([], now=now) is None
    assert rl.plan_windows_from_rpc({"payload": {}}, now=now) is None
    assert rl._rate_limits_blob({"rate_limits": {"primary": {}}}) is not None
    assert rl._rate_limits_blob({"payload": {"rate_limits": {"primary": {}}}}) is not None
    assert rl._rate_limits_blob({"primary": {}}) is not None
    assert rl._window("x", now=now) is None
    assert rl._window({"window_minutes": True}, now=now) is None
    assert rl._window({"window_minutes": 5, "used_percent": 1.5}, now=now) is not None
    assert rl._resets_at({"resets_at": True}, now=now) is None
    assert rl._resets_at({"resets_at": 1_700_000_000}, now=now) is not None
    assert rl._resets_at({"resets_in_seconds": True}, now=now) is None
    assert rl._resets_at({"resets_in_seconds": 30}, now=now) is not None
    assert rl._opt_str(1) is None
    assert rl._opt_int(True) is None
    assert rl._opt_int(3.0) == 3
    assert rl._opt_int("x") is None
    assert rl._opt_float(True) is None
    assert rl._opt_float(1.5) == 1.5
    win = rl._window({"window_minutes": 5, "resets_at": 1e400}, now=now)
    assert win is None or win.resets_at is None


def test_doctor_private_failure_paths() -> None:
    from codexloop.infrastructure.doctor_env import CodexDoctorEnvironment, _default_run

    env = CodexDoctorEnvironment(run=lambda *_a, **_k: (_ for _ in ()).throw(OSError("x")))
    assert env._codex_version("codex") is None
    assert env._login_status_ok("codex") is False
    assert env._exec_help_has_flags("codex") is False
    assert env._probe_app_server_live() is False

    class _Bad:
        returncode = 1
        stdout = ""
        stderr = ""

    env2 = CodexDoctorEnvironment(
        which=lambda _name: "/bin/codex",
        run=lambda *_a, **_k: _Bad(),
    )
    assert env2._codex_version("codex") is None
    assert env2._version_meets_floor(None) is False
    assert env2._version_meets_floor("nope") is False
    assert env2._version_meets_floor("codex-cli 0.0.1") is False
    assert env2._probe_app_server_live() is False

    env3 = CodexDoctorEnvironment(
        which=lambda _name: "/bin/codex",
        run=lambda *_a, **_k: (_ for _ in ()).throw(subprocess.TimeoutExpired("codex", 1)),
    )
    assert env3._probe_app_server_live() is False

    result = _default_run([sys.executable, "-c", "print('ok')"], timeout=5)
    assert result.returncode == 0
