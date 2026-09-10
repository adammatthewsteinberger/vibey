# Never blocking on a human

The entire point of an autonomous runner is that it doesn't need anyone
present. A run that stalls silently waiting for terminal input is worse than
one that fails loudly — at least a failure shows up in monitoring.

## Every stall path and its mitigation

| Stall path | Mitigation |
|---|---|
| Permission prompts (default) | Sessions **always start** with `permission_mode="bypassPermissions"` so autonomy is the baseline and mid-run switches can return to bypass (the SDK forbids escalating *into* bypass if the session did not start there). |
| Mid-run Manual mode | Maps to SDK `default` + `can_use_tool`. Approvals are **control-plane only**: the runner emits `tool.approval_needed`; the operator runs `claudeloop tool approve\|deny ID`. A timeout **auto-denies** with autonomy guidance — never waits on stdin/TTY. |
| Accept-edits / plan / auto | SDK `acceptEdits` / `plan` / `auto` via `claudeloop permission-mode` or `--permission-mode`. |
| An unexpected permission path slipping through anyway | Autonomy hooks deny human-gated tools (e.g. `AskUserQuestion`) with guidance; Manual mode still times out rather than blocking. |
| `AskUserQuestion` | Intercepted and **denied with guidance** — not auto-answered. See [ADR 0007](../architecture/decisions/0007-ask-user-question-denied-with-guidance.md). |
| `ExitPlanMode` | Auto-approved, so a plan-mode turn can't park waiting for confirmation |
| `Notification` hooks | Logged, never awaited |
| The model asking "Shall I proceed?" in plain text | No tool call exists to intercept here — handled by an appended system-prompt fragment establishing autonomous operation, and by the completion evaluator treating an incomplete-with-no-progress turn as a continuation, not a stop |
| A TTY-dependent stdin read | The runner never inherits a TTY; it's designed to run safely under `nohup` or as a systemd unit. Mid-run ops use the file inbox under `.claudeloop/runs/<id>/`, not interactive prompts. |
| MCP OAuth flows | Genuinely can't complete unattended — `claudeloop doctor` checks configured MCP servers *before* a run starts and fails fast, naming the servers that need attention, rather than discovering the problem hours in |

## Why "deny with guidance" instead of "fabricate an answer"

It would be easy to make `AskUserQuestion` always return, say, the first
listed option. That silently invents a decision nobody made. Instead,
`claudeloop` denies the call with a message along the lines of:

> "Running autonomously, no user available — choose the option you would
> recommend, note the assumption, and proceed."

This puts the choice back where it belongs — with the model's own
reasoning, visible in the transcript — rather than with an arbitrary
default a human reviewing the run later would have no way to distinguish
from a real answer.

## Testing this guarantee

Paid live coverage includes a plan that instructs the model to ask a
clarifying question and asserts the runner denies the tool call with
guidance and continues rather than hanging
(`tests/live/test_paid_tier.py::test_never_blocks_on_a_clarifying_question`).
Manual-mode tool approval timeout is covered in unit/infrastructure tests
(`ToolApprovalGate`). See also
[run resources and chat ops](run-resources-and-chat-ops.md) and
[live testing](live-testing.md).
