# Never blocking

The fastest way to lose an unattended night is a single `Press y to continue`
nobody is there to press. cursorloop removes every place a run can silently
park on input:

- **Managed hooks** (`CURSORLOOP_MANAGED_HOOKS`, on by default) install a
  session preamble that pre-answers interactive prompts.
- **The preamble** tells the agent it is unattended: no questions, no stdin.
- **Force paths** prefer non-interactive variants of tool invocations.
- **Watchdogs** back all of it: a turn that hangs anyway hits
  `--turn-timeout`, and silent output hits `--stall-timeout` — the run fails
  loudly instead of waiting politely forever.

Verify the hook state any time with `cursorloop hooks`. Disable management
(for a session you are actually watching) with `--no-managed-hooks`.
