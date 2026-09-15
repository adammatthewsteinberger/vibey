# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The operator-seat failover engine (#208): policy, probes, and the handoff lifecycle."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from vibey_gh import failover
from vibey_gh.failover import (
    ENGAGE,
    HOLD,
    RECLAIM,
    FailoverConfig,
    Seat,
    load,
    probe,
    run,
    run_once,
    step,
)


def test_the_policy_is_three_decisions_and_the_paid_lane_leads():
    assert step(paid_ok=True, seat_active=True) == RECLAIM
    assert step(paid_ok=False, seat_active=False) == ENGAGE
    assert step(paid_ok=True, seat_active=False) == HOLD
    assert step(paid_ok=False, seat_active=True) == HOLD


def test_a_missing_config_file_is_a_disabled_engine_not_an_error(tmp_path: Path):
    cfg = load(tmp_path / "nowhere.toml")
    assert cfg.enabled is False
    assert cfg.paid_probe == ""


def test_the_default_seat_order_is_qwenloop_then_opencode():
    seats = FailoverConfig().seats
    assert [seat.name for seat in seats] == ["qwenloop", "opencode"]


def test_config_loads_seats_probe_and_interval(tmp_path: Path):
    where = tmp_path / "failover.toml"
    where.write_text(
        'enabled = true\npaid_probe = "true"\ninterval_seconds = 7\n'
        '[[seats]]\nname = "a"\nlaunch = "sleep 60"\nhealth = "true"\n'
        '[[seats]]\nname = "b"\nlaunch = "sleep 60"\n',
        encoding="utf-8",
    )
    cfg = load(where)
    assert cfg.enabled is True
    assert cfg.paid_probe == "true"
    assert cfg.interval_seconds == 7
    assert cfg.seats == (
        Seat(name="a", launch="sleep 60", health="true"),
        Seat(name="b", launch="sleep 60"),
    )


def test_config_drops_incomplete_seats_and_falls_back_to_the_defaults(tmp_path: Path):
    where = tmp_path / "failover.toml"
    where.write_text(
        'enabled = true\n[[seats]]\nname = "nameless"\n[[seats]]\nlaunch = "orphan"\n',
        encoding="utf-8",
    )
    assert [seat.name for seat in load(where).seats] == ["qwenloop", "opencode"]


def test_probe_judges_only_the_exit_status():
    assert probe("true") is True
    assert probe("false") is False
    assert probe("") is False


def test_a_hanging_probe_is_down_not_a_hang():
    assert probe("sleep 30", timeout=1) is False


def _cfg(tmp_path: Path, paid: str, seats: tuple[Seat, ...]) -> FailoverConfig:
    return FailoverConfig(enabled=True, paid_probe=paid, seats=seats)


def test_disabled_engine_holds_and_says_how_to_enable(tmp_path: Path, capsys):
    assert run_once(FailoverConfig(), state_path=tmp_path / "s.json") == HOLD
    assert "disabled" in capsys.readouterr().out


def test_paid_lane_down_hands_the_seat_to_the_first_healthy_agent(tmp_path: Path):
    lines: list[str] = []
    state = tmp_path / "s.json"
    cfg = _cfg(
        tmp_path,
        paid="false",
        seats=(
            Seat(name="sick", launch="sleep 60", health="false"),
            Seat(name="well", launch="sleep 60", health="true"),
        ),
    )
    try:
        assert run_once(cfg, state_path=state, report=lines.append) == ENGAGE
        recorded = json.loads(state.read_text(encoding="utf-8"))
        assert recorded["seat"] == "well"
        assert any("failed its health check" in line for line in lines)
        assert any("seat handed to well" in line for line in lines)
        # The engaged seat holds across the next pass while the paid lane stays down.
        assert run_once(cfg, state_path=state, report=lines.append) == HOLD
    finally:
        os.killpg(recorded["pid"], 15)


def test_recovery_reclaims_the_seat_and_clears_the_state(tmp_path: Path):
    lines: list[str] = []
    state = tmp_path / "s.json"
    cfg = _cfg(tmp_path, paid="false", seats=(Seat(name="well", launch="sleep 60"),))
    assert run_once(cfg, state_path=state, report=lines.append) == ENGAGE
    healed = FailoverConfig(enabled=True, paid_probe="true", seats=cfg.seats)
    assert run_once(healed, state_path=state, report=lines.append) == RECLAIM
    assert json.loads(state.read_text(encoding="utf-8")) == {}
    assert any("seat reclaimed from well" in line for line in lines)
    # Reclaiming again is a quiet hold: the paid lane leads and nothing is active.
    assert run_once(healed, state_path=state, report=lines.append) == HOLD


def test_no_healthy_seat_is_reported_loudly(tmp_path: Path):
    lines: list[str] = []
    cfg = _cfg(
        tmp_path, paid="false", seats=(Seat(name="sick", launch="sleep 60", health="false"),)
    )
    assert run_once(cfg, state_path=tmp_path / "s.json", report=lines.append) == ENGAGE
    assert any("NO seat is healthy — operator needed" in line for line in lines)


def test_a_seat_that_died_on_its_own_is_cleared_then_replaced(tmp_path: Path):
    state = tmp_path / "s.json"
    state.write_text(json.dumps({"seat": "gone", "pid": 2**22 + os.getpid()}), encoding="utf-8")
    lines: list[str] = []
    cfg = _cfg(tmp_path, paid="false", seats=(Seat(name="well", launch="sleep 60"),))
    try:
        assert run_once(cfg, state_path=state, report=lines.append) == ENGAGE
        recorded = json.loads(state.read_text(encoding="utf-8"))
        assert recorded["seat"] == "well"
    finally:
        os.killpg(recorded["pid"], 15)


def test_reclaim_survives_a_pid_that_no_longer_exists(tmp_path: Path):
    state = tmp_path / "s.json"
    state.write_text(json.dumps({"seat": "gone", "pid": 2**22 + os.getpid()}), encoding="utf-8")
    lines: list[str] = []
    # Force the reclaim path: the recorded pid is treated as alive.
    real = failover._seat_alive
    try:
        failover._seat_alive = lambda state: True  # type: ignore[assignment]
        cfg = FailoverConfig(enabled=True, paid_probe="true")
        assert run_once(cfg, state_path=state, report=lines.append) == RECLAIM
    finally:
        failover._seat_alive = real  # type: ignore[assignment]
    assert json.loads(state.read_text(encoding="utf-8")) == {}


def test_garbage_state_reads_as_empty(tmp_path: Path):
    state = tmp_path / "s.json"
    state.write_text("not json", encoding="utf-8")
    assert failover._read_state(state) == {}
    state.write_text("[1, 2]", encoding="utf-8")
    assert failover._read_state(state) == {}
    assert failover._read_state(tmp_path / "missing.json") == {}


def test_a_foreign_pid_is_not_our_seat(monkeypatch):
    def deny(pid, sig):
        raise PermissionError

    monkeypatch.setattr(os, "kill", deny)
    assert failover._seat_alive({"pid": 1}) is False
    assert failover._seat_alive({"pid": "not-an-int"}) is False


def test_the_loop_runs_until_told_once(tmp_path: Path):
    lines: list[str] = []
    run(FailoverConfig(), state_path=tmp_path / "s.json", once=True, report=lines.append)
    assert len(lines) == 1

    class Stop(Exception):
        pass

    def stop(seconds):
        assert seconds == 300
        raise Stop

    with pytest.raises(Stop):
        run(FailoverConfig(), state_path=tmp_path / "s.json", report=lines.append, sleep=stop)


def test_reclaim_with_no_recorded_pid_just_clears_the_state(tmp_path: Path):
    state = tmp_path / "s.json"
    state.write_text(json.dumps({"seat": "ghost"}), encoding="utf-8")
    real = failover._seat_alive
    try:
        failover._seat_alive = lambda state: True  # type: ignore[assignment]
        cfg = FailoverConfig(enabled=True, paid_probe="true")
        assert run_once(cfg, state_path=state, report=lambda line: None) == RECLAIM
    finally:
        failover._seat_alive = real  # type: ignore[assignment]
    assert json.loads(state.read_text(encoding="utf-8")) == {}
