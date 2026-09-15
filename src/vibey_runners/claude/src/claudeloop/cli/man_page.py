# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Manual-page style help for the root ``claudeloop`` command.

PyPI users and packagers often expect ``--help`` to read like ``man 1`` output.
Subcommands keep Typer's usual ``--help`` (option details); only the top-level
invocation uses this document.
"""

from __future__ import annotations

from claudeloop import __version__

_DOCS = "https://adammatthewsteinberger.github.io/claudeloop/"
_REPO = "https://github.com/adammatthewsteinberger/claudeloop"
_PYPI = "https://pypi.org/project/claudeloop/"
_TESTPYPI = "https://test.pypi.org/project/claudeloop/"


def render_man_page() -> str:
    """Return a plain-text manual page (suitable for ``man -l -``)."""
    return f"""\
CLAUDELOOP(1)                         User Commands                         CLAUDELOOP(1)

NAME
       claudeloop - autonomous Claude Code session runner and Anthropic SDK CLI

SYNOPSIS
       claudeloop [--help | -h] [--version | --man] [-v...|-q]
                  [--log-level LEVEL] [--log-file PATH]
       claudeloop run [OPTIONS] PLAN_FILE
       claudeloop resume [OPTIONS]
       claudeloop stop [--run-id ID]
       claudeloop prompt (--now | --at-break) TEXT [--run-id ID]
       claudeloop permission-mode MODE [--run-id ID]
       claudeloop cwd DIR [--run-id ID]
       claudeloop slash /COMMAND [--run-id ID]
       claudeloop tool approve|deny REQUEST_ID [--run-id ID]
       claudeloop attach|unattach|folder|skill|plugin|connector|github …
       claudeloop memory|artifact|chat|response|research|web-search …
       claudeloop voice|speak …
       claudeloop logs [--run-id ID] [--follow | -f]
       claudeloop status [--run-id ID]
       claudeloop snapshot [--run-id ID] [--out PATH] [--bundle | --no-bundle]
       claudeloop runs
       claudeloop savepoints [--run-id ID]
       claudeloop unwind --to N [--backup | --no-backup] [--run-id ID]
       claudeloop reset --yes
       claudeloop watch [--run-id ID] [--follow]
       claudeloop sessions [--cwd PATH]
       claudeloop doctor
       claudeloop api [OPTIONS] COMMAND [ARGS]...


DESCRIPTION
       claudeloop drives Claude Code sessions to completion without blocking on
       a human.  It classifies capacity rejections, waits only when a rate-limit
       window reset is knowable, probes when credits may return after a top-up,
       and resumes across turns.  A capacity rejection always outranks a
       completion claim on the same turn.

       Credits exhausted is never treated as waitable-with-a-deadline; a rate-
       limit window with a resets_at time is.  Conflating the two is the bug
       this project exists to replace.

       While claudeloop run (or resume) is in the foreground, a second terminal
       talks to it through .claudeloop/runs/<run_id>/ — soft stop, prompt inject,
       permission/cwd, attachments/skills/MCP, memories, chat metadata,
       response actions, realtime logs, status, git save points, and unwind.
       Sessions always start with permission_mode=bypassPermissions so mid-run
       switches can return to bypass. Manual mode uses control-plane approvals
       with timeout (never stdin).


       It also exposes a generated 1:1 command tree over the anthropic Python
       SDK as claudeloop api.

       Run claudeloop doctor before long unattended runs.

COMMANDS
       run PLAN_FILE
              Start a new Claude Code session from a markdown plan file and
              drive until Done, Blocked, budget exhaustion, max-wait, auth
              failure, or operator stop.  Prints the run id on stderr.

       resume [--session-id ID]
              Continue an existing session.  Without --session-id, selects the
              most recently modified session for the current working directory
              and prints which session was chosen.

       stop [--run-id ID]
              Soft-stop the active (or specified) run.  The runner finishes the
              current turn or aborts a wait, writes stop-summary.md, and exits
              130.  Prefer this over Ctrl-C when you want a resume-friendly
              summary of what changed and what remains.

       prompt (--now | --at-break) TEXT [--run-id ID]
              Inject operator text into the loop.  Exactly one of --now or
              --at-break is required.
                 --now       use this text as the next turn prompt
                 --at-break  queue until a Continue (natural break), then use it

       model|effort|preset …
              Mid-run model / effort / preset changes (applied at turn boundary).

       permission-mode MODE [--run-id ID]
              Mid-run permission mode: bypass|manual|accept-edits|plan|auto.
              Sessions always start in bypass so return-to-bypass is allowed.
              Manual uses control-plane tool approve|deny with timeout (never
              stdin).

       cwd DIR [--run-id ID]
              Mid-run working directory change (reconnects the agent session).

       slash /COMMAND [--run-id ID]
              Inject a validated slash command (allowlisted; never raw shell).

       tool approve|deny REQUEST_ID [--run-id ID]
              Resolve a pending Manual-mode tool approval.

       attach|unattach|folder|skill|plugin|connector|github|research|web-search …
              Run-scoped resource CRUD (see run-resources guide).

       memory|artifact …
              Native memories (*.md) and artifacts under the run directory.

       chat …
              Local session metadata (pin/rename/share/project).  share writes
              a local export bundle — not a Claude.ai share API.

       response copy|good|bad|retry
              Last-turn clipboard/stdout, feedback events, or re-queue prompt.

       voice|speak …
              Optional TTS/STT extras (claudeloop[voice] or system say/espeak).

       logs [--run-id ID] [--follow | -f]
              Print or follow the per-run events.jsonl stream (recursively
              redacted).  Use -f like tail -f while a run is active.

       status [--run-id ID]
              Show the latest status snapshot (status.json): phase, attempt,
              session id, model/effort, capacity subtype, waiting_until, and
              snapshot fields when present.

       snapshot [--run-id ID] [--out PATH] [--bundle | --no-bundle]
              Write a handoff snapshot under .claudeloop/runs/<id>/snapshots/
              (latest.json + immutable timestamped JSON).  Publishes
              snapshot_path / snapshot_digest / snapshot_reason on the state bus.
              Optional bundle copies attachments/memories/artifacts and a
              best-effort Claude Code transcript when found under
              ~/.claude/projects/.  Missing transcripts are recorded honestly
              (claude_session.found=false) — never invented.

       runs
              List run directories under .claudeloop/runs/ for the current cwd.

       savepoints [--run-id ID]
              List git save points (refs/claudeloop/<run_id>/<n>) recorded for
              the run.

       unwind --to N [--backup | --no-backup] [--run-id ID]
              Reset the worktree to save point N (or a sha prefix / label).
              Refuses while the run meta status is still active with a live
              pid — stop first.  Default creates a backup ref under
              refs/claudeloop/backup/.

       reset --yes
              Delete the project .claudeloop/ control plane.  Requires --yes.
              Refuses while any run pid is still live.  Does not touch the
              git worktree or ~/.claude/.

       watch [--run-id ID] [--follow]
              Print or follow bus.jsonl state publications (phase changes) for
              external integrators.  status.json is the pollable snapshot;
              bus.jsonl is the append-only stream.

       sessions [--cwd PATH]
              List known Claude Code sessions (read-only).

       doctor
              Pre-flight checks: Claude CLI present, authentication, configured
              MCP servers, anthropic SDK import, api surface wiring, cwd safety.

       api
              Generated REST/SDK commands (e.g. claudeloop api models list).
              Use claudeloop api --help and claudeloop api <resource> --help.

OPTIONS (common run / resume)
       --cwd DIR
              Effective working directory for the run (default: process cwd).

       --attach PATH / --add-folder PATH / --skill NAME / --plugin PATH
              Declare run resources up front (repeatable where noted).

       --from-github OWNER/REPO[@REF] / --import-issue OWNER/REPO#N
              GitHub repo ref / issue import into run resources.

       --connector NAME=JSON|url
              MCP connector config for ClaudeAgentOptions.mcp_servers.

       --web-search / --deep-research
              Enable web-search tool flag / local research job recording.

       --permission-mode MODE
              bypass (default) | manual | accept-edits | plan | auto.

       --slash /COMMAND
              Enqueue an initial validated slash command.

       --max-turns INT
              Cap on agent turns for this process.

       --max-dollars FLOAT
              Cap on cumulative USD cost reported by the Agent SDK.

       --max-wait SECONDS
              Cap on how long to wait on capacity before failing.

       --model NAME
              Alias (low|medium|high) or raw Anthropic model id.  Default
              alias low → claude-sonnet-4-5.

       --effort LEVEL
              Effort: low|medium|high|xhigh|max (default medium).

       --preset NAME
              Preset low|medium|high sets model+effort; --model/--effort then
              override.  high → claude-fable-5 + max.

       --auto-model / --no-auto-model
              Automatic escalate/downgrade policy (default on).

       --continue-prompt TEXT
              Prompt used on subsequent turns after the first (default is a
              short continue instruction).

       --done-marker TEXT
              Fallback completion substring when structured verdicts are absent.

       --max-buffer-size BYTES
              Claude Agent SDK JSON message buffer size.  Default is 50 MiB
              (52428800).  The SDK default of 1 MiB aborts on large tool
              results.  Override with CLAUDELOOP_MAX_BUFFER_SIZE as well.

       --log-level LEVEL
              Level for dual console (+ optional file) structlog transports
              (default INFO).  DEBUG includes per-message / decision detail.

       --log-chatter MODE
              full|summary|off for prompt/response chatter in logs/events.

       --log-file PATH
              Optional JSON file transport only.  Never shares a path with
              audit.jsonl — per-run audit and events always live under
              .claudeloop/runs/<run_id>/.

       --stream-ui
              Full-screen Textual multi-pane token stream (TTY required).
              Disables the human console renderer; JSON console stays on stderr.

       Global flags
              --help / -h / --man   this manual page
              --version            print version and exit
              -v / --verbose       repeatable: -v debug, -vv also third-party
                                   libraries, -vvv full payloads
              -q / --quiet         warnings and errors only
              --log-level LEVEL    DEBUG|INFO|WARNING|ERROR|CRITICAL; overrides -v
              --log-file PATH      also write redacted JSON lines to PATH

LOGGING
       After configure_logging (run/resume), stderr receives JSON console
       lines ("transport": "console_json") and, unless --stream-ui, human
       ConsoleRenderer lines.  events.jsonl rows carry trace_id and turn_id;
       chatter.* events hold prompts/responses/deltas.  See
       {_DOCS}guides/logging-and-observability/

EXIT STATUS
       0      Success (run/resume reached a Done verdict; doctor every check
              passed; most inspection commands succeeded).

       1      Failure (blocked, budget/max-wait exhausted, auth failed, doctor
              check failed, or other error).

       2      Usage error (e.g. prompt without exactly one of --now/--at-break).

       75     Wound down on purpose (claudeloop wind-down); the current turn
              finished, runs/<id>/handoff.json names every artifact produced,
              and a supervisor can resume elsewhere.

       130    Soft-stopped by claudeloop stop (or equivalent interrupt path).

FILES
       claudeloop.toml
              Optional per-project configuration in the working directory.

       ~/.config/claudeloop/config.toml
              Optional user-level configuration (overridden by cwd file, then
              env, then CLI flags).

       .claudeloop/runs/<run_id>/
              Per-run control plane:
                 meta.json           run metadata (status, pid, phase, …)
                 inbox/              operator command files (*.cmd.json)
                 events.jsonl        realtime redacted event stream
                 audit.jsonl         phase / turn audit trail
                 savepoints.jsonl    index of git save points
                 status.json         latest pollable state snapshot
                 bus.jsonl           append-only state publications
                 stop-summary.md     written on soft stop
                 resources/          attachments, skills, plugins, MCP, research
                 memories/           native memory markdown + index.json
                 artifacts/          operator/run output files
                 snapshots/          handoff JSON (latest + immutable) + optional
                                     bundles/ and best-effort Claude transcripts
                 run.lock            per-run lock file when used

       .claudeloop/chats/<session_id>.json
              Native chat metadata (pin, alias, share token, project tags).

       .claudeloop/state/, .claudeloop/locks/
              Optional run-state store and session locks.

ENVIRONMENT
       ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN
              Credentials for the Anthropic API / Claude Code.

       CLAUDELOOP_MAX_TURNS, CLAUDELOOP_MAX_DOLLARS, CLAUDELOOP_MAX_WAIT,
       CLAUDELOOP_MODEL, CLAUDELOOP_EFFORT, CLAUDELOOP_PRESET,
       CLAUDELOOP_MODEL_LOW, CLAUDELOOP_MODEL_MEDIUM, CLAUDELOOP_MODEL_HIGH,
       CLAUDELOOP_AUTO_MODEL, CLAUDELOOP_LOG_CHATTER, CLAUDELOOP_STREAM_UI,
       CLAUDELOOP_DONE_MARKER, CLAUDELOOP_CONTINUE_PROMPT,
       CLAUDELOOP_MAX_BUFFER_SIZE, CLAUDELOOP_RETRY_WATCHDOG,
       CLAUDELOOP_PERMISSION_MODE, CLAUDELOOP_TOOL_APPROVAL_TIMEOUT_SECONDS,
       CLAUDELOOP_WEB_SEARCH, CLAUDELOOP_DEEP_RESEARCH, …
              Override runner settings.  See the configuration guide.

       CLAUDELOOP_ALLOW_TEST_AGENT, CLAUDELOOP_TEST_AGENT_SCRIPT
              Test-only.  Activate a JSON-scripted agent for the system-live
              harness.  Not for production use.  See live-testing guide.

EXAMPLES
       Start an autonomous run from a plan:

              claudeloop doctor
              claudeloop run handoff.md --max-turns 40 --max-dollars 5 \\
                --permission-mode bypass --attach ./spec.md

       In another terminal, while the run is active:

              claudeloop status
              claudeloop logs -f
              claudeloop prompt --now "Also add unit tests for the parser"
              claudeloop permission-mode plan
              claudeloop tool approve REQUEST_ID   # Manual mode only
              claudeloop response retry
              claudeloop stop

       After a stop, inspect and optionally unwind git save points:

              claudeloop savepoints
              claudeloop unwind --to 2

       Raise the SDK JSON buffer (rarely needed above the 50 MiB default):

              claudeloop run handoff.md --max-buffer-size 104857600

SEE ALSO
       Documentation (github.io): {_DOCS}
       Repository: {_REPO}
       PyPI: {_PYPI}
       TestPyPI: {_TESTPYPI}
       Guides: autonomous runs, run resources and chat ops, rate limits vs
       credits, never-blocking, live testing, configuration — under {_DOCS}
       claudeloop run --help, claudeloop resume --help, claudeloop api --help

VERSION
       claudeloop {__version__}

CLAUDELOOP(1)                         User Commands                         CLAUDELOOP(1)
"""


def write_man_page() -> None:
    import sys

    text = render_man_page()
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
