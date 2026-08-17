# claudeloop — Phase C2: expose `--append-system-prompt` on `run`

You are working unattended in a disposable git worktree of `claudeloop`
(`~/git/claudeloop`), on branch `chore/c2-append-system-prompt`. Pass
`--cwd` explicitly to `run`/`sessions` (the only two commands that support
it today — that gap is tracked separately in
`docs/plans/fleet/c-guardrails-claudeloop.md`, don't duplicate that work
here unless it's already landed and you need it for your own tests).

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green.

## Why this task exists

This is not a naming mismatch — the underlying capability already exists
end to end, it just isn't exposed. Trace it:

- `infrastructure/agent/options.py:70,78-79` — `system_prompt_append: str`
  is a real parameter that gets appended to the agent's system prompt.
- `infrastructure/agent/gateway.py:60,81,112,165,180-181` — the gateway
  carries `system_prompt_append` all the way to the Claude Agent SDK call.
- `bootstrap.py:184` — `system_prompt_append=str(gw_payload.get("system_prompt_append") or "")`,
  where `gw_payload` comes from `resources.gateway_payload()` — the
  `RunResourceStore`/`ResourcePortAdapter` machinery that also carries
  `--attach`/`--add-folder`/`--from-github`/`--skill`/`--plugin`/`--connector`
  into a session.

So the value is currently only ever populated indirectly, through
skills/plugins/resources — **there is no direct CLI flag to hand the runner
a raw string to append to the system prompt.** `cli/commands/run.py` has
`--skill`, `--plugin`, `--connector` (lines ~60-63) but nothing for a plain
string. This came up because the fleet program's launcher
(`~/git/vibey/scripts/fleet/run.sh`) wanted to pass a short protected-paths
reminder into unattended runs and discovered the flag simply doesn't exist
— `claudeloop run --help` lists only `--continue-prompt` (a different,
unrelated thing: the prompt used on continuation turns, not a system-prompt
addition).

## Deliverable

Add a `--append-system-prompt <str>` option to `cli/commands/run.py` (and
to `resume` if `resume` already threads other gateway-payload-affecting
flags — check first, follow whatever precedent exists for keeping `run`
and `resume` consistent). Wire it into whatever currently produces
`gw_payload`/`resources.gateway_payload()` — find the resource-store
construction path (`RunResourceStore`, `ResourcePortAdapter`, or wherever
`--skill`/`--plugin`/`--connector` values are collected before being handed
to `bootstrap.py`) and add this as another field it carries, appended
(not replacing) whatever skills/plugins already contribute to
`system_prompt_append` — multiple sources should compose, not clobber each
other. If the flag is given multiple times, decide a sensible join (repeat
`typer.Option` accumulating a list, joined with blank lines, is consistent
with how `--skill`/`--plugin` already work — follow that pattern rather
than inventing a new one).

## Tests

Test-first. Cover: the flag parses and reaches `gw_payload`/
`system_prompt_append` correctly; it composes correctly alongside a skill
or plugin that also contributes to the system prompt (neither should
silently drop the other's contribution); an empty/omitted flag behaves
exactly as today (no regression to the existing skill/plugin-only path).
Reuse whatever test infrastructure already covers `--skill`/`--plugin`
plumbing (`tests/cli/`) rather than building a parallel harness.

Keep all four layers at 100% branch coverage. Full 7-gate sweep: ruff
check/format, `mypy --strict src/claudeloop`, the four
`pytest --cov=<layer> --cov-branch --cov-fail-under=100` runs,
`lint-imports`, `bandit`, `pip-audit`. Re-run the full suite 3-5 times
before trusting green.

## Smoke test

```bash
claudeloop run <trivial plan> --cwd /tmp/smoke --run-id smoke \
  --append-system-prompt "Never write outside /tmp/smoke." \
  --max-turns 1 --max-dollars 1
# confirm (via --log-level DEBUG / --log-file) that the appended text
# actually reached the outbound system prompt, not just that the flag
# parsed without error.
```

## Done

Full gate sweep green, Conventional Commit, end your final message with
**CLAUDELOOP_TASK_FULLY_COMPLETE** — only when genuinely done. If a gate
can't be made to pass, stop and explain why instead of weakening it.
