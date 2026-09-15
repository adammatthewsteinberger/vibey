# ADR 0007: `AskUserQuestion` is denied with guidance, not auto-answered

## Status

Accepted, scoped for M2/M3. Not yet implemented.

## Context

`claudeloop` must never stall waiting for a human — that's the entire point
of an autonomous runner. Claude Code exposes an `AskUserQuestion` tool the
model can call when it genuinely wants a decision from the user. Two ways to
prevent this from blocking an unattended run were considered:

1. **Auto-answer** — synthesize a plausible choice and return it as if a
   human picked it.
2. **Deny with guidance** — refuse the tool call, but tell the model *why*
   and what to do instead.

## Decision

Deny with guidance, via the `can_use_tool` callback intercepting
`AskUserQuestion` specifically: return a denial whose message says
something like *"running autonomously, no user available — choose the
option you would recommend, note the assumption, and proceed."*

## Consequences

- Auto-answering would fabricate a decision the user never made and present
  it as if they had — silently inventing consent. Denying with guidance
  instead hands the decision back to the model *with the constraint stated*,
  and the model's own reasoning about which option it picked (and why) lands
  in the transcript, where a human reviewing the run afterward can see the
  assumption that was made and correct it if it was wrong.
- This is one of several mitigations for the broader "never block on a
  human" requirement, alongside: `permission_mode="bypassPermissions"` (the
  Python SDK has no `dangerously_skip_permissions` field — this is its
  equivalent) plus a defensive `can_use_tool` that never awaits input as
  belt-and-suspenders; `ExitPlanMode` auto-approved so a plan-mode turn
  can't park; `Notification` hooks that log rather than wait;
  never inheriting a TTY so the runner is safe under `nohup`/systemd; and an
  appended system-prompt fragment establishing autonomous operation so the
  model doesn't simply end a turn with "Shall I proceed?" text that carries
  no tool call to intercept in the first place.
- MCP OAuth flows are the one stall path this mitigation *cannot* cover —
  they inherently require a browser round-trip. The planned `doctor` command
  checks configured MCP servers up front and fails fast, naming the servers
  that need attention, rather than letting a run discover the problem
  hours into an unattended session.
