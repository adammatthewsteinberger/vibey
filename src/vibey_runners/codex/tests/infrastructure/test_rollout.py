# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Read-only CODEX_HOME rollout tail: last token_count.rate_limits, staleness, containment."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from codexloop.domain.capacity import PlanWindows
from codexloop.infrastructure.rollout import read_rollout_rate_limits
from tests.application.fakes import FakeClock

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
MAX_AGE = timedelta(minutes=10)


def _token_count_line(
    *,
    used_primary: float | None = 13.0,
    used_secondary: float | None = 93.0,
    primary: object | None = ...,
    secondary: object | None = ...,
    plan_type: str | None = "plus",
) -> str:
    if primary is ...:
        primary = (
            None
            if used_primary is None
            else {
                "used_percent": used_primary,
                "window_minutes": 300,
                "resets_at": 1780171524,
            }
        )
    if secondary is ...:
        secondary = (
            None
            if used_secondary is None
            else {
                "used_percent": used_secondary,
                "window_minutes": 10080,
                "resets_at": 1780174809,
            }
        )
    return json.dumps(
        {
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "rate_limits": {
                    "primary": primary,
                    "secondary": secondary,
                    "plan_type": plan_type,
                    "rate_limit_reached_type": None,
                },
            },
        }
    )


def _rate_limits_updated_line(*, used_primary: float = 50.0) -> str:
    return json.dumps(
        {
            "type": "rate_limits.updated",
            "rate_limits": {
                "primary": {
                    "used_percent": used_primary,
                    "window_minutes": 300,
                    "resets_at": 1780171524,
                },
                "secondary": {
                    "used_percent": 10.0,
                    "window_minutes": 10080,
                    "resets_at": 1780174809,
                },
                "plan_type": "plus",
                "rate_limit_reached_type": None,
            },
        }
    )


def _write_jsonl(path: Path, lines: list[str], *, mtime: datetime = NOW) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    timestamp = mtime.timestamp()
    os.utime(path, (timestamp, timestamp))
    return path


def _read(codex_home: Path, *, max_age: timedelta = MAX_AGE) -> PlanWindows | None:
    return read_rollout_rate_limits(codex_home=codex_home, now=NOW, max_age=max_age)


# --- Step 1: newest token_count.rate_limits wins; forgiving parse ---------------


def test_no_rollout_files_returns_none(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    home.mkdir()
    assert _read(home) is None


def test_missing_codex_home_returns_none_without_creating(tmp_path: Path) -> None:
    home = tmp_path / "missing"
    assert _read(home) is None
    assert not home.exists()


def test_empty_jsonl_returns_none(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    _write_jsonl(home / "empty.jsonl", [])
    (home / "empty.jsonl").write_text("", encoding="utf-8")
    os.utime(home / "empty.jsonl", (NOW.timestamp(), NOW.timestamp()))
    assert _read(home) is None


def test_last_token_count_in_file_wins(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    _write_jsonl(
        home / "sessions" / "rollout.jsonl",
        [
            _token_count_line(used_primary=10.0),
            '{"type":"thread.started","thread_id":"t1"}',
            _token_count_line(used_primary=25.0),
        ],
    )
    windows = _read(home)
    assert windows is not None
    assert windows.plan_type == "plus"
    assert windows.primary is not None
    assert windows.primary.used_percent == 25.0
    assert windows.primary.window_minutes == 300
    assert windows.secondary is not None
    assert windows.secondary.used_percent == 93.0


def test_newest_jsonl_file_by_mtime_wins(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    _write_jsonl(
        home / "old.jsonl",
        [_token_count_line(used_primary=10.0)],
        mtime=NOW - timedelta(minutes=2),
    )
    _write_jsonl(
        home / "nested" / "new.jsonl",
        [_token_count_line(used_primary=77.0)],
        mtime=NOW - timedelta(minutes=1),
    )
    windows = _read(home)
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.used_percent == 77.0


def test_malformed_lines_are_skipped(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    _write_jsonl(
        home / "rollout.jsonl",
        [
            _token_count_line(used_primary=10.0),
            "not-json",
            "{",
            "",
            _rate_limits_updated_line(used_primary=40.0),
        ],
    )
    windows = _read(home)
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.used_percent == 40.0


def test_missing_window_degrades_to_none_for_that_window_only(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    _write_jsonl(
        home / "rollout.jsonl",
        [
            _token_count_line(
                primary={"used_pct": 13, "window_mins": 300},
                used_secondary=93.0,
            )
        ],
    )
    windows = _read(home)
    assert windows is not None
    assert windows.primary is None
    assert windows.secondary is not None
    assert windows.secondary.used_percent == 93.0


def test_garbage_window_is_none_for_that_window_only(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    _write_jsonl(
        home / "rollout.jsonl",
        [_token_count_line(primary=["not", "a", "window"], used_secondary=5.0)],
    )
    windows = _read(home)
    assert windows is not None
    assert windows.primary is None
    assert windows.secondary is not None
    assert windows.secondary.used_percent == 5.0


def test_unreadable_file_returns_none(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    path = _write_jsonl(home / "locked.jsonl", [_token_count_line()])
    path.chmod(0o000)
    try:
        assert _read(home) is None
    finally:
        path.chmod(0o644)


def test_default_codex_home_is_dot_codex_under_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _write_jsonl(tmp_path / ".codex" / "rollout.jsonl", [_token_count_line(used_primary=7.0)])
    windows = read_rollout_rate_limits(now=NOW)
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.used_percent == 7.0


# --- Step 2: staleness ----------------------------------------------------------


def test_snapshot_older_than_max_age_is_discarded(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    clock = FakeClock(NOW)
    _write_jsonl(
        home / "stale.jsonl",
        [_token_count_line(used_primary=99.0)],
        mtime=NOW - timedelta(minutes=11),
    )
    assert read_rollout_rate_limits(codex_home=home, now=clock.now(), max_age=MAX_AGE) is None


def test_snapshot_within_max_age_is_trusted(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    clock = FakeClock(NOW)
    _write_jsonl(
        home / "fresh.jsonl",
        [_token_count_line(used_primary=12.0)],
        mtime=NOW - timedelta(minutes=9),
    )
    windows = read_rollout_rate_limits(codex_home=home, now=clock.now(), max_age=MAX_AGE)
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.used_percent == 12.0


def test_snapshot_exactly_max_age_is_trusted(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    _write_jsonl(
        home / "boundary.jsonl",
        [_token_count_line(used_primary=3.0)],
        mtime=NOW - MAX_AGE,
    )
    windows = _read(home, max_age=MAX_AGE)
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.used_percent == 3.0


# --- Step 3: containment and read-only ------------------------------------------


def test_escaping_symlink_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    secret = _write_jsonl(outside / "secret.jsonl", [_token_count_line(used_primary=99.0)])
    home = tmp_path / "codex"
    home.mkdir()
    (home / "escape.jsonl").symlink_to(secret)
    assert _read(home) is None


def test_escaping_symlink_does_not_mask_contained_file(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    secret = _write_jsonl(outside / "secret.jsonl", [_token_count_line(used_primary=99.0)])
    home = tmp_path / "codex"
    _write_jsonl(
        home / "ok.jsonl",
        [_token_count_line(used_primary=13.0)],
        mtime=NOW - timedelta(seconds=5),
    )
    link = home / "escape.jsonl"
    link.symlink_to(secret)
    os.utime(link, (NOW.timestamp(), NOW.timestamp()), follow_symlinks=False)
    windows = _read(home)
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.used_percent == 13.0


def test_symlink_inside_codex_home_pointing_inside_is_allowed(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    real = _write_jsonl(
        home / "sessions" / "real.jsonl",
        [_token_count_line(used_primary=42.0)],
    )
    (home / "link.jsonl").symlink_to(real)
    windows = _read(home)
    assert windows is not None
    assert windows.primary is not None
    assert windows.primary.used_percent == 42.0


def test_directory_symlink_is_not_descended(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    _write_jsonl(outside / "secret.jsonl", [_token_count_line(used_primary=99.0)])
    home = tmp_path / "codex"
    home.mkdir()
    (home / "escape_dir").symlink_to(outside)
    assert _read(home) is None


def test_read_is_strictly_read_only(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    _write_jsonl(home / "rollout.jsonl", [_token_count_line()])
    before = sorted(p.relative_to(home) for p in home.rglob("*"))
    windows = _read(home)
    assert windows is not None
    after = sorted(p.relative_to(home) for p in home.rglob("*"))
    assert after == before


def test_directory_named_jsonl_does_not_raise(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    (home / "foo.jsonl").mkdir(parents=True)
    assert _read(home) is None


def test_contained_non_file_jsonl_name_is_skipped(tmp_path: Path) -> None:
    import os

    from codexloop.infrastructure import rollout as rollout_mod

    home = tmp_path / "codex"
    home.mkdir()
    fifo = home / "pipe.jsonl"
    os.mkfifo(fifo)
    assert rollout_mod._newest_contained_jsonl(home) is None
