# How an autonomous run works, end to end

This walks through the full lifecycle of `claudeloop run handoff.md`,
tying together the pieces documented individually elsewhere.

## 1. Preflight

Before spending a single real turn, the runner checks whether it's already
mid-cooldown — for example if a prior manual session hit its limit right
before you started `claudeloop`. `domain.loop.decide_preflight` handles
this; see [`../architecture/run-loop-state-machine.md`](../architecture/run-loop-state-machine.md).

## 2. The first turn

For `claudeloop run handoff.md`, the plan file's contents seed a brand-new
Claude Code session (`domain.plan.WorkPlan.parse` turns any checkbox items
in it into tracked work). For `claudeloop resume`, a continuation prompt is
sent to the resolved session instead. Every prompt gets a runtime-appended
instruction establishing autonomous operation — see
[never-blocking.md](never-blocking.md).

## 3. Evaluating what happened

When a turn completes, two independent things are checked, and their order
matters:

1. **Capacity** — did this turn hit a rate limit or run out of credits? See
   [rate-limits-and-credits.md](rate-limits-and-credits.md).
2. **Completion** — does the model report the *whole task* done, not just
   this turn? See [completion-detection.md](completion-detection.md).

**A capacity rejection always outranks a completion claim.** A turn cut off
mid-response by a limit could coincidentally contain marker-like text; the
run loop checks capacity first and never trusts a "done" claim from a turn
that didn't actually complete cleanly.

## 4. If capacity is available and the task isn't done

Send another turn immediately — no cooldown, because this wasn't a limit,
just a turn boundary. This mirrors the legacy script's observation that a
single `claude -p` invocation can end because the *turn* ended, not because
the *task* did, and the two look identical from the outside without a
structured signal to tell them apart.

## 5. If capacity is exhausted

Enter the waiting policy described in
[rate-limits-and-credits.md](rate-limits-and-credits.md) — a scheduled probe
loop, never a blind sleep.

## 6. Terminal states

- **Complete** — the model reports the whole task genuinely done, and
  capacity was available on that turn. Exit 0.
- **Failed** — authentication failure (never retried), a `Blocked` verdict
  (the model reports it can't proceed — e.g. missing MCP credentials), the
  configured budget exhausted, or `--max-wait` exceeded while still waiting
  on capacity. Exit non-zero, with the reason recorded in the audit log.
- **Stopped** — an operator ran `claudeloop stop` against the active run.
  The runner finishes the current turn or aborts a wait, writes
  `stop-summary.md`, and exits 130.

## Mid-run operator control

While `claudeloop run` is in the foreground, a second terminal can talk to
it via `.claudeloop/runs/<run_id>/`:

| Command | Effect |
|---|---|
| `claudeloop stop` | Soft-stop; writes `stop-summary.md` |
| `claudeloop prompt --now "..."` | Next turn uses this prompt |
| `claudeloop prompt --at-break "..."` | Applied after a Continue verdict |
| `claudeloop model low\|medium\|high\|<id>` | Queue model change at next turn |
| `claudeloop effort LEVEL` | Queue effort change (`low`…`max`) |
| `claudeloop preset low\|medium\|high` | Queue preset (model+effort) |
| `claudeloop logs --follow [--chatter]` | Tail redacted `events.jsonl` (optionally chatter only) |
| `claudeloop status` / `runs` | Poll live status (`status.json`) |
| `claudeloop snapshot [--out] [--bundle]` | Write handoff snapshot under `snapshots/` (+ bus path/digest) |
| `claudeloop watch [--stream] [--replay]` | Bus follow, or Textual stream live/replay |
| `claudeloop savepoints` | List git save points for the run |
| `claudeloop unwind --to N` | Reset worktree to save point N (refuse if still active) |

Save points are `refs/claudeloop/<run-id>/<n>` on the current HEAD. When a
turn changes files, claudeloop commits them first; when the tree is
unchanged (e.g. a wait/poll turn), it only updates the ref — no empty
commits.
| `claudeloop permission-mode MODE` | Mid-run permission mode (`bypass`/`manual`/`accept-edits`/`plan`/`auto`) |
| `claudeloop cwd DIR` | Mid-run working directory (reconnects the agent session) |
| `claudeloop tool approve\|deny ID` | Manual-mode tool decisions (timeout auto-denies — never stdin) |
| `claudeloop attach` / `folder` / `skill` / … | Run-scoped resource CRUD |
| `claudeloop slash /CMD` | Validated slash-command inject |
| `claudeloop memory` / `artifact` | Native memories and artifacts |
| `claudeloop chat …` | Session metadata (pin/share/project — local share bundles only) |
| `claudeloop response copy\|good\|bad\|retry` | Last-turn actions |

Full surface: [run-resources-and-chat-ops.md](run-resources-and-chat-ops.md).

### Model / effort presets

Defaults: model alias `low` (`claude-sonnet-4-5`) + effort `medium`.

| Preset | Model alias → id | Effort |
|---|---|---|
| `low` | `low` → `claude-sonnet-4-5` | `medium` |
| `medium` | `medium` → `claude-opus-4-6` | `high` |
| `high` | `high` → `claude-fable-5` | `max` |

Override aliases with `CLAUDELOOP_MODEL_LOW` / `_MEDIUM` / `_HIGH`. Mid-run
auto policy (default on; `--no-auto-model` to disable) escalates after stuck
Continues / Blocked, and downgrades on plan progress or ≥80% of `--max-dollars`.
Operator `model`/`effort`/`preset` commands lock auto for the rest of the run.

### Pub/sub for external systems

Every phase change is published to:

- `.claudeloop/runs/<run_id>/status.json` — latest snapshot (atomic replace; poll this)
- `.claudeloop/runs/<run_id>/bus.jsonl` — append-only stream of every publish (follow this)

No network bus is required. Other apps can `tail -f` the bus file, poll
`status.json`, or use `claudeloop status` / `claudeloop watch`. Snapshot
writes also publish `snapshot_path` / `snapshot_digest` / `snapshot_reason`
(see [run-resources-and-chat-ops.md](run-resources-and-chat-ops.md#run-handoff-snapshots)).

### Large tool results (1MB SDK buffer)

The Claude Agent SDK defaults to a 1MB JSON line buffer and aborts with
`JSON message exceeded maximum buffer size of 1048576 bytes` on large tool
outputs. claudeloop sets `ClaudeAgentOptions.max_buffer_size` to **50MiB** by
default. Override with `--max-buffer-size BYTES` or `CLAUDELOOP_MAX_BUFFER_SIZE`.

### Console + file logging

`run` / `resume` configure dual stderr transports (human + JSON
`transport=console_json`) plus optional `--log-file`, in addition to
`events.jsonl` / `audit.jsonl`. See
[`logging-and-observability.md`](logging-and-observability.md).

## Everything is logged

Every SDK message is streamed into the per-run `events.jsonl` as it arrives,
and phase transitions also go to `audit.jsonl`. Both carry `run_id`,
`session_id`, `attempt`, `phase`, and `event_type`, with recursive redaction
of secret-shaped keys and credential-looking substrings. Use
`claudeloop logs --follow` to watch a live run. Structlog `--log-file` is a
separate sink and never shares a path with the audit JSONL.
