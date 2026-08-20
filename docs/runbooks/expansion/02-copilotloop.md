# Runbook: copilotloop — the fifth engine

## Goal

A `copilotloop` autonomous session runner wrapping GitHub Copilot CLI,
conforming to the same contract the other four runners expose, so vibey
rotates across five engines with zero vibey-side special-casing.

## Current state (verified)

- Copilot CLI is GA (Feb 2026) with headless mode (`copilot -p "<prompt>"`)
  and `--mode autopilot` for fully autonomous sessions; `--plan` composes
  with both. Model selection spans Anthropic/OpenAI/Google.
- vibey's engine contract is defined by `EngineAdapter`
  (`application/interfaces/engines.py`) + an `EngineDescriptor`
  (`infrastructure/engines/descriptors.py`): binary, state_dir,
  done_marker, capabilities, effort projection onto native flags.
- The conformance suite (`application/conformance.py`, 9 checks) is the
  acceptance bar: binary, flags, state_dir, run_dir_shape,
  snapshot_schema, capacity_map, done_marker, control_plane,
  structured_verdict.

## Design

Build `copilotloop` as its own repo (`~/git/copilotloop`), mirroring
claudeloop's shape — vibey orchestrates runners, it does not absorb them
(ADR-0001). The runner owns:

- `copilotloop run <plan.md> --run-id --preset --effort --cwd`: spawns
  `copilot -p` with `--mode autopilot`, translating preset/effort to model
  + allow-list flags.
- State dir `.copilotloop/runs/<run-id>/` with `meta.json`,
  `events.jsonl` (translated from Copilot CLI output stream),
  `snapshots/latest.json`, `stop-summary.md`.
- Done marker `COPILOTLOOP_TASK_FULLY_COMPLETE`; structured verdict block;
  control-plane inbox (`wind-down` honored at turn boundaries — document
  the same "needs one more turn" semantics claudeloop has).
- `copilotloop doctor`: binary present, `gh auth status`, Copilot
  entitlement check.
- Capacity classification: map Copilot quota/rate errors →
  WindowExhausted (resets_at from headers when present) vs
  CreditsExhausted (entitlement exhausted; never a deadline).

vibey side (small): a `COPILOTLOOP` descriptor with effort projection
(TRIVIAL/LOW→cheap model, STANDARD→default, HIGH/MAX→best available;
`achieved` saturates honestly if Copilot lacks a MAX-grade knob), argv
goldens (5 efforts), classify fixtures, and `LOOP_EVENT_MAP` entries
sourced from **real captured output** — never fabricated (the #32/#34
lesson: every prior engine's event map had to be re-verified against
source).

## Work items

1. copilotloop repo: runner skeleton, run dir shape, done marker.
2. Output→events.jsonl translation + structured verdict.
3. doctor + capacity classification.
4. Control plane (send-prompt, wind-down) + stop-summary.
5. vibey: descriptor + goldens + classify fixtures + event map (from
   captured real output).
6. Conformance run: `vibey doctor --conformance` all 9 checks green.
7. Live: one paid greeter work item implemented by copilotloop end-to-end,
   plus a cross-engine verify (copilot implements, claudeloop verifies).

## Verification

All 9 conformance checks pass; the live item lands through
implement→verify→integrate with copilotloop in the health table and
rotation selecting it.

## Needs from operator

`gh` authenticated with a Copilot-entitled account; `copilot` CLI
installed (`npm i -g @github/copilot` or platform installer).

## Risks

- Copilot CLI output format is young and changes on its weekly release
  train — the docs-scraper workstream (04) should watch its changelog.
- Autopilot permission flags must be scoped to the worktree only.
- Quota semantics are org-plan-dependent; classify conservatively
  (unknown → WindowExhausted with short backoff, never Credits).
