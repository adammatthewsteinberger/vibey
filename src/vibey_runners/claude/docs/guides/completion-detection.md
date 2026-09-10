# Completion detection: turn-ended vs. task-done

A single `claude -p` invocation is one turn. It can end because the overall
task is genuinely finished, or just because that turn's response ended
(ran out of steps, paused, whatever) while multi-part work still remains.
From the outside — exit code 0, no limit language — the two look identical.
This is the exact problem the legacy script's done-marker mechanism was
built to solve, and `claudeloop` replaces it with something more reliable
while keeping the marker as a fallback.

## Primary mechanism: structured output

Every turn is asked to return a typed JSON verdict via
`ClaudeAgentOptions.output_format`:

```json
{"complete": bool, "remaining_work": [str], "blocked_on": str | null, "summary": str}
```

`domain.completion.evaluate()` maps this to one of three outcomes:

- **`Done(summary)`** — `complete: true` and no `blocked_on`.
- **`Blocked(reason)`** — `blocked_on` is set, regardless of `complete`. A
  turn can't claim done and blocked at the same time; blocked wins. This
  **terminates the run as failed** — it is not a wait/retry signal.
- **`Continue(remaining_work)`** — anything else. `remaining_work` tracks
  which specific plan items are left, not just a boolean, so the audit log
  shows real progress.

### What belongs in `blocked_on`

| Put in `blocked_on` (terminal) | Put in `remaining_work` instead (`blocked_on: null`) |
|---|---|
| Missing API credentials / MCP OAuth a human must complete | Background Agent/Bash task you started and can poll |
| Unpaid billing / credits a human must top up | Pending test suite, build, or deploy you kicked off |
| A required human policy decision you cannot assume | Any other waitable progress you can resume later |

The schema property descriptions and the autonomy system-prompt fragment
repeat this rule so models are less likely to treat "I'm waiting on my own
background job" as a terminal block.

## Fallback: the legacy marker

If structured output isn't available (an older model, or a configuration
that doesn't support it), `evaluate()` falls back to substring-matching a
marker string — `CLAUDELOOP_TASK_FULLY_COMPLETE` by default, overridable
with `--done-marker` — in the raw turn output, exactly as
`legacy/claude_autoresume.py`'s `with_done_marker_instruction()` does today.
This is a fallback, not the primary path, because a bare substring match has
two known failure modes the structured path doesn't:

1. **Collision** — the marker happens to appear in the user's own prompt
   text or in something the model quotes.
2. **Truncation** — a rate-limit message cutting a response off mid-stream
   could coincidentally contain marker-like text.

## The limit always wins

Regardless of which detection path produced a `Done` verdict,
`domain.loop.decide_after_turn` checks capacity *before* it looks at the
verdict at all. A `Done` claim on a turn that also hit a rate limit is
discarded in favor of entering the waiting state — see
[`../architecture/run-loop-state-machine.md`](../architecture/run-loop-state-machine.md#decide_after_turnstate-capacity-verdict-now)
for the exact rule and its dedicated test.

## Tracking a plan's checklist across turns

When the input is a markdown plan with checkbox items
(`domain.plan.WorkPlan.parse`), a `Continue` verdict's `remaining_work` list
is reconciled back against the plan via `with_items_marked_done()`, so
`claudeloop sessions` and the audit log can show which specific items are
still open rather than a single "not done yet" boolean.
