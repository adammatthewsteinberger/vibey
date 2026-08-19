"""Faked-mode conformance against REAL installed binaries, not ScriptedEngine.

test_faked_conformance.py only ever exercises the in-memory ScriptedEngine
double -- it never spawns a real subprocess, so it can't catch a bug in
argv construction, real events.jsonl production, or LOOP_EVENT_MAP
translation the way a real (even if scripted-mode) engine run can. This
file closes that gap for the three engines that ship their own
env-gated scripted/offline agent (claudeloop, codexloop, cursorloop):
`LoopProcessAdapter` drives the real installed binary, which runs its own
scripted agent instead of calling a real model -- no network, no API key,
no cost, but a genuine subprocess spawn through the real production code
path `vibey doctor --conformance` and `vibey worker` both use.

agyloop has no scripted/offline agent of its own (confirmed: no
ALLOW_TEST_AGENT env gate anywhere in its source) -- there is currently no
way to exercise it here without a real, paid Gemini call, so it stays on
the ScriptedEngine-only test in test_faked_conformance.py. That's a real,
documented gap, not an oversight; see
docs/plans/fleet-program-runbook.md's scripted/offline agent table.

codexloop and cursorloop are xfail (strict) here, not skipped or passing --
this real subprocess-level test found two genuine, previously-unknown bugs
in those repos themselves, distinct from anything vibey's own code was
doing wrong:

- codexloop: `infrastructure/rundir.py` writes meta.json exactly once, at
  run-directory creation, and never updates it again -- there is no
  "status" field write anywhere in its codebase at all. It records
  completion in `state.json`'s "reason" field instead. Every other engine
  (claudeloop, agyloop, cursorloop) writes meta.json's status through
  active/finished/failed/stopped -- the exact vocabulary
  LoopProcessAdapter.tail() depends on for completion detection. Until
  codexloop's own run-lifecycle code is fixed to match that contract,
  vibey can spawn it and stream its raw events, but can never correctly
  detect when it's done.
- cursorloop: `infrastructure/agent/scripted.py`'s ScriptedAgentGateway
  raises IndexError on an unexpected second `send_turn` call --
  AutonomousRunner sends a "Continue exactly where you left off" follow-up
  prompt after a scripted "done" turn instead of recognizing the verdict
  as complete, crashing the run.

Both are queued as real fleet plan files, not fixed inline here, since
each requires understanding that engine's own control-flow in enough
depth to place the fix correctly. `strict=True` means either xfail turns
into a real failure the moment its underlying repo is out of sync with
this comment (e.g. someone "fixes" it without updating this file) --
that's intentional, not a bug in this test.

Every test here skips (not fails) when its binary or fixture script isn't
present on this machine -- mirroring test_paid_preflight.py's pattern --
since these tests depend on sibling repo checkouts at ~/git/<engine> that
won't exist in every environment (e.g. a clean CI runner that only checks
out vibey).
"""

import shutil
from pathlib import Path

import pytest

from vibey.application.conformance import run_conformance
from vibey.domain.capacity import CreditsExhausted
from vibey.domain.engine import EngineId
from vibey.infrastructure.engines.classify import CREDITS_FIXTURES
from vibey.infrastructure.engines.descriptors import BY_ENGINE_ID
from vibey.infrastructure.engines.loop_process_adapter import LoopProcessAdapter

_SCRIPTED_ENGINES: dict[EngineId, tuple[str, str]] = {
    EngineId.CLAUDELOOP: ("CLAUDELOOP_ALLOW_TEST_AGENT", "CLAUDELOOP_TEST_AGENT_SCRIPT"),
    EngineId.CODEXLOOP: ("CODEXLOOP_ALLOW_TEST_AGENT", "CODEXLOOP_TEST_AGENT_SCRIPT"),
    EngineId.CURSORLOOP: ("CURSORLOOP_ALLOW_TEST_AGENT", "CURSORLOOP_TEST_AGENT_SCRIPT"),
}

_KNOWN_BROKEN_UPSTREAM: dict[EngineId, str] = {
    EngineId.CODEXLOOP: (
        "codexloop never writes a terminal status to meta.json (see module "
        "docstring) -- queued as docs/plans/fleet/d0-meta-status-codexloop.md"
    ),
    EngineId.CURSORLOOP: (
        "ScriptedAgentGateway raises on an unexpected second send_turn "
        "(see module docstring) -- queued as "
        "docs/plans/fleet/d0-completion-detection-cursorloop.md"
    ),
}


def _done_script_for(engine_id: EngineId) -> Path:
    return (
        Path.home()
        / "git"
        / engine_id.value
        / "tests"
        / "live"
        / "fixtures"
        / "agent_scripts"
        / "done.json"
    )


def _param(engine_id: EngineId) -> object:
    reason = _KNOWN_BROKEN_UPSTREAM.get(engine_id)
    marks = () if reason is None else (pytest.mark.xfail(reason=reason, strict=True),)
    return pytest.param(engine_id, marks=marks, id=engine_id.value)


_SCRIPTED_ENGINE_PARAMS = [_param(e) for e in sorted(_SCRIPTED_ENGINES, key=lambda e: e.value)]


@pytest.mark.live
@pytest.mark.parametrize("engine_id", _SCRIPTED_ENGINE_PARAMS)
async def test_real_binary_scripted_conformance(
    engine_id: EngineId,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    descriptor = BY_ENGINE_ID[engine_id]
    if shutil.which(descriptor.binary) is None:
        pytest.skip(f"{descriptor.binary} not installed")
    script = _done_script_for(engine_id)
    if not script.is_file():
        pytest.skip(f"no scripted-agent fixture at {script} (sibling repo not checked out?)")

    allow_env, script_env = _SCRIPTED_ENGINES[engine_id]
    monkeypatch.setenv(allow_env, "1")
    monkeypatch.setenv(script_env, str(script))

    adapter = LoopProcessAdapter(descriptor=descriptor)
    fixtures = [("credits", CREDITS_FIXTURES[engine_id], CreditsExhausted)]
    report = await run_conformance(
        adapter,
        capacity_fixtures=fixtures,
        trivial_worktree=str(tmp_path / "conformance-wt"),
    )

    assert report.ok, [c for c in report.checks if not c.ok]


@pytest.mark.live
def test_agyloop_has_no_scripted_agent_yet() -> None:
    """Documents the real gap rather than silently omitting agyloop above:
    fails loudly the day agyloop grows a scripted agent, as a prompt to add
    it to _SCRIPTED_ENGINES and this file's coverage."""
    agyloop_src = Path.home() / "git" / "agyloop" / "src" / "agyloop"
    if not agyloop_src.is_dir():
        pytest.skip(f"agyloop checkout not found at {agyloop_src}")

    hits = list(agyloop_src.rglob("scripted.py"))
    assert not hits, f"agyloop now has {hits} -- add it to _SCRIPTED_ENGINES above"
