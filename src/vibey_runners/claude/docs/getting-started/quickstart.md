# Quickstart

## Run a plan file to completion, unattended

```bash
claudeloop run handoff.md
```

Seeds a brand-new Claude Code session with the contents of `handoff.md`, then
keeps resuming it — across turns, across rate-limit windows, across a
credits top-up — until the task reports itself genuinely complete. Run this
from whatever directory you want Claude Code to operate in; that's the
directory the session and any file edits happen in.

## Resume a specific session

```bash
claudeloop resume --session-id <id>
```

## Resume whatever you were last working on

```bash
claudeloop resume
```

Auto-selects the most recently modified Claude Code session for the current
working directory (via the SDK's `list_sessions()`, not by parsing
transcript files directly) and prints exactly which one it picked — session
id, last-activity time, git branch, first-prompt preview — before doing
anything, so you can interrupt it if it guessed wrong.

## Mid-run control (second terminal)

While `claudeloop run` is in the foreground:

```bash
claudeloop status
claudeloop logs -f
claudeloop prompt --now "Also add tests for the edge case"
claudeloop permission-mode plan   # or bypass / manual / accept-edits / auto
claudeloop attach ./notes.md
claudeloop stop                 # writes stop-summary.md; process exits 130
claudeloop savepoints
# after stop:
claudeloop unwind --to 1
```

See [autonomous runs](../guides/autonomous-runs.md) and
[run resources and chat ops](../guides/run-resources-and-chat-ops.md) for the
full control-plane layout under `.claudeloop/runs/<run_id>/`.

## See what's running or waiting

```bash
claudeloop sessions
claudeloop runs
claudeloop status
```

## Check your setup before starting a long unattended run

```bash
claudeloop doctor
```

Verifies Claude Code is installed and authenticated, checks any configured
MCP servers up front (since MCP OAuth can't complete unattended — see
[`../architecture/decisions/0007-ask-user-question-denied-with-guidance.md`](../architecture/decisions/0007-ask-user-question-denied-with-guidance.md)),
and confirms the working directory is safe to bypass permissions in.

## Configuration

`claudeloop` reads configuration in this precedence order (highest wins):

1. Command-line flags (`--max-wait`, `--max-turns`, `--log-level`, ...)
2. Environment variables (`CLAUDELOOP_*`)
3. A config file (`claudeloop.toml` in the working directory, or
   `~/.config/claudeloop/config.toml`)
4. Built-in defaults

See [`../guides/never-blocking.md`](../guides/never-blocking.md) and
[`../guides/rate-limits-and-credits.md`](../guides/rate-limits-and-credits.md)
for what each of the safety-relevant settings actually controls.
