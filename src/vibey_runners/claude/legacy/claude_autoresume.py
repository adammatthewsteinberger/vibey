#!/usr/bin/env python3
"""LEGACY REFERENCE IMPLEMENTATION — not part of the `claudeloop` package.

This is the original single-file script `claudeloop` is replacing. It is kept
here, unmodified in behavior, because it is the source of truth for every
behavioral requirement the new implementation must satisfy or deliberately
improve on (see docs/architecture/decisions/ for the specific supersessions:
structured rate-limit signals replacing the regex scraping below, the
credits-vs-window distinction, list_sessions() replacing the glob-based
session discovery, etc.). Do not add new features here — extend
`src/claudeloop/` instead. This file may be deleted once `claudeloop` reaches
feature parity (milestone M2) and the team is confident nothing here was
missed.

Original docstring follows.
---

Runs `claude` and automatically resumes whenever it stops because a
usage limit was hit. Two ways to point it at work:

    python3 claude_autoresume.py handoff.md
        Starts a brand-new session seeded with the contents of handoff.md,
        then auto-resumes that session (via `claude --continue`) every time
        it gets cut off by a limit.

    python3 claude_autoresume.py --session-id <id>
        Resumes an existing session by its Claude Code session id (via
        `claude --resume <id>`) instead of starting fresh from a prompt
        file. Use this to pick up a session you (or another invocation of
        this script) already started elsewhere.

    python3 claude_autoresume.py
        Neither given: auto-detects the most recently modified Claude Code
        session for the CURRENT WORKING DIRECTORY (by reading
        ~/.claude/projects/<sanitized-cwd>/*.jsonl) and resumes that one.
        Prints a loud, impossible-to-miss warning banner showing exactly
        which session it picked (id, transcript path, last-activity time,
        git branch, first-prompt preview) before doing anything, so you can
        Ctrl-C if it grabbed the wrong one. If no session exists for this
        directory, it errors out immediately rather than guessing further.

Passing BOTH a prompt-file and --session-id is ambiguous and is an error.

Run this from whatever working directory you want `claude` to operate in
(e.g. your project's repo root) -- that's the directory the session and any
file edits happen in, and (in the no-argument form) the directory whose
most recent session gets auto-selected.

How it works:
- Before doing any real work, runs a cheap preflight ping (a trivial
  "reply with the word OK" prompt against the same session) to check
  whether you're *already* in a limit cooldown right now -- e.g. because
  you (or a prior run of this script) hit the limit before launching this
  invocation. If so, it waits out the cooldown before spending a real
  attempt. If there's no prior session to resume yet (fresh prompt-file
  start with no existing session), the preflight just no-ops and the
  script proceeds straight to the real first run.
- Real attempts: first run (prompt-file mode only) seeds a fresh session
  with the file's contents; every attempt after that -- including the
  very first one in --session-id mode -- resumes via --continue or
  --resume <id>.
- Streams a readable one-line-per-event summary to your terminal as it
  works (assistant text, tool calls, final result), while writing the full
  raw JSON stream to a log file so nothing is lost. This is headless `-p`
  mode, not the interactive UI, so it won't look identical to running
  `claude` directly in a terminal -- but you do see live progress instead
  of silence until the end.
- When a real attempt's process exits, decides whether a hard usage/session
  limit was hit by inspecting structured stream-json signals (rate_limit_event
  status:rejected, error:rate_limit, api_error_status:429) and limit phrasing
  in the final result / API-error message only -- NOT the whole stream (which
  often contains allowed_warning events with a weekly resetsAt, and repo docs
  that mention "rate limit"). If limited, sleeps until the rejected event's
  resetsAt or a parsed "resets 5pm"-style time; otherwise falls back to
  --wait-minutes (default 60) and retries.
- A single `claude -p` invocation is one turn: it can end because the
  overall task is genuinely finished, OR just because that turn's response
  ended (ran out of steps, paused, whatever) while multi-part work
  (E19-E26, say) remains. The two look identical from the outside -- exit
  code 0, no limit language -- so every prompt sent (the initial one, and
  --continue-prompt) has a completion-marker instruction appended at
  runtime: "if the entire task is done, end your final message with
  <marker>; if not, don't." Only seeing that exact marker in the output
  means "stop looping". Exit 0 with no limit language and no marker means
  "that turn ended but the task isn't done" -- the script immediately
  fires another --continue attempt (no cooldown wait, since this isn't a
  limit) and keeps going. Override the marker with --done-marker if it
  collides with something in your own prompt.
- If a real attempt exits with an error that ISN'T limit-related, the
  script stops and prints the error rather than retrying blindly (so a
  real bug doesn't get silently retried forever).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Text phrases applied ONLY to trusted surfaces (final result text / API-error
# assistant messages) — never to the raw stream, which routinely contains repo
# docs and code mentioning "rate limit", "rejected", etc. and would false-positive.
# Keep these tight: bare "rate limit" matches ordinary prose like "rate limiter".
LIMIT_TEXT_PATTERNS = [
    r"usage limit",
    r"session limit",
    r"hit your .{0,40}limit",
    r"reached your limit",
    r"reached the limit",
    r"limit reached",
    r"try again later",
    r"try again in",
    r"quota exceeded",
    r"too many requests",
]

# Looks for things like "resets at 3:45 PM", "resets 5pm", "resets at 15:45",
# or an ISO timestamp -- best-effort only, falls back to a fixed wait if unmatched.
# Applied only to trusted limit-message text (not raw stream / warning events).
RESET_TIME_PATTERNS = [
    re.compile(r"resets?\s+(?:at\s+)?(\d{1,2}:\d{2}\s*[APap][Mm]?)", re.IGNORECASE),
    re.compile(r"resets?\s+(?:at\s+)?(\d{1,2}\s*[APap][Mm])", re.IGNORECASE),  # "resets 5pm"
    re.compile(r"resets?\s+(?:at\s+)?(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", re.IGNORECASE),
]

PING_PROMPT = "Reply with the single word OK and nothing else."

DEFAULT_DONE_MARKER = "AUTOCLAUDE_TASK_FULLY_COMPLETE"

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def sanitize_cwd_for_project_dir(cwd: str) -> str:
    """Claude Code stores session transcripts under
    ~/.claude/projects/<cwd with every "/" replaced by "-">/*.jsonl -- e.g.
    /home/you/git/myproject -> -home-you-git-myproject. Confirmed against actual
    directories on disk, not documented publicly, so this is best-effort:
    if Claude Code ever changes this scheme, find_most_recent_session()
    below just won't find a directory and will report "no sessions found"
    rather than crashing."""
    return cwd.replace("/", "-")


def find_most_recent_session(cwd: str) -> dict[str, object] | None:
    """Finds the most recently modified session transcript for `cwd` and
    pulls out enough detail (session id, last-activity time, git branch,
    first-prompt preview) to show a human a meaningful "is this the right
    one?" summary before we resume it unattended. Returns None if there's
    no project directory or no transcripts in it -- the caller is
    responsible for treating that as a hard error, not a silent no-op."""
    project_dir = CLAUDE_PROJECTS_DIR / sanitize_cwd_for_project_dir(cwd)
    if not project_dir.is_dir():
        return None

    transcripts = sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not transcripts:
        return None

    latest = transcripts[0]
    info: dict[str, object] = {
        "session_id": latest.stem,
        "transcript_path": str(latest),
        "last_modified": datetime.fromtimestamp(latest.stat().st_mtime),
    }

    # Best-effort enrichment from the transcript contents -- a malformed or
    # unreadable transcript still yields a usable session id above, just
    # without the extra detail.
    first_prompt_preview = None
    git_branch = None
    last_timestamp = None
    line_count = 0
    try:
        with open(latest, encoding="utf-8") as f:
            for raw_line in f:
                line_count += 1
                try:
                    entry = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if git_branch is None and entry.get("gitBranch"):
                    git_branch = entry["gitBranch"]
                if entry.get("timestamp"):
                    last_timestamp = entry["timestamp"]
                if first_prompt_preview is None and entry.get("type") == "user":
                    content = entry.get("message", {}).get("content")
                    if isinstance(content, str):
                        first_prompt_preview = content
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                first_prompt_preview = block.get("text")
                                break
    except OSError:
        pass

    info["line_count"] = line_count
    info["git_branch"] = git_branch
    info["last_activity_timestamp"] = last_timestamp
    info["first_prompt_preview"] = (first_prompt_preview or "")[:200]
    return info


def print_auto_selected_session_warning(cwd: str, info: dict[str, object]) -> None:
    """Loud, hard-to-miss banner so nobody silently resumes the wrong
    session -- printed to stdout (not just the log file) since this is
    exactly the kind of thing a person needs to see before walking away
    from an unattended run."""
    bar = "!" * 78
    lines = [
        bar,
        "WARNING: no prompt file and no --session-id given.",
        f"Auto-selected the MOST RECENT Claude Code session for directory: {cwd}",
        "",
        f"  session id      : {info['session_id']}",
        f"  transcript file : {info['transcript_path']}",
        f"  last modified   : {info['last_modified']}",
    ]
    if info.get("last_activity_timestamp"):
        lines.append(f"  last activity   : {info['last_activity_timestamp']}")
    if info.get("git_branch"):
        lines.append(f"  git branch      : {info['git_branch']}")
    if info.get("line_count"):
        lines.append(f"  transcript lines: {info['line_count']}")
    preview = info.get("first_prompt_preview")
    if preview:
        preview_str = str(preview).replace("\n", " ")
        truncated = "..." if len(preview_str) >= 200 else ""
        lines.append(f"  first prompt    : {preview_str}{truncated}")
    lines += [
        "",
        "If this is NOT the session you meant to resume: stop now (Ctrl-C) and",
        "re-run with an explicit --session-id <id>, or a prompt-file argument to",
        "start fresh instead.",
        bar,
    ]
    for line in lines:
        print(line, flush=True)


def with_done_marker_instruction(prompt_text: str, done_marker: str) -> str:
    """Appends a runtime instruction (not something the user has to put in
    their own prompt file) telling Claude to signal true end-of-task with an
    exact marker string, and to omit it if there's still work left. This is
    what lets the script tell "this turn ended" apart from "the whole task
    is done" -- see module docstring."""
    return (
        f"{prompt_text}\n\n"
        "---\n"
        "Process note (from the automation running you, not the user): this session "
        "may be resumed automatically across multiple turns if you get cut off. "
        f"If, and only if, the ENTIRE task above is now fully complete with nothing "
        f"left to do, end your final message with this exact line on its own: "
        f"{done_marker}\n"
        "If any work remains -- including work you were mid-way through -- do NOT "
        "include that line, so the automation knows to resume you."
    )


def _text_looks_like_limit(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in LIMIT_TEXT_PATTERNS)


def _assistant_text(event: dict) -> str:
    parts: list[str] = []
    for block in event.get("message", {}).get("content", []) or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text") or "")
    return "\n".join(parts)


def iter_stream_events(output: str):
    """Yield parsed JSON objects from a stream-json capture; skip non-JSON lines."""
    for line in output.splitlines():
        line = line.strip()
        if not line or line[0] not in "{[":
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def extract_limit_signals(output: str) -> tuple[bool, datetime | None]:
    """Decide whether a captured claude run hit a hard usage/session limit, and
    if so, best-effort parse when it resets.

    Important: Claude's stream routinely includes *allowed_warning* rate_limit
    events (with a far-future weekly resetsAt) and tool_result/file contents that
    mention "rate limit" / "rejected" in ordinary project docs. Matching those
    as a hard limit caused multi-day false cooldowns. Only treat as limited when:
      - a rate_limit_event has status "rejected", or
      - an event carries error/api_error_status 429 / is_api_error_message, or
      - the final result text (or synthetic API-error assistant text) matches
        limit phrasing.
    resetsAt is only trusted from rejected rate_limit_events; human-readable
    "resets 5pm" is parsed only from those trusted message texts.
    """
    limited = False
    reset_time: datetime | None = None
    trusted_texts: list[str] = []

    for event in iter_stream_events(output):
        if event.get("type") == "rate_limit_event":
            info = event.get("rate_limit_info") or {}
            if info.get("status") == "rejected":
                limited = True
                ts = info.get("resetsAt")
                if isinstance(ts, (int, float)) and reset_time is None:
                    # seconds (~10 digits) or ms (~13 digits)
                    ts_int = int(ts)
                    if ts_int >= 10_000_000_000:  # 11+ digits → treat as ms
                        ts_int //= 1000
                    reset_time = datetime.fromtimestamp(ts_int)
            continue

        if event.get("error") == "rate_limit" or event.get("api_error_status") == 429:
            limited = True

        if event.get("is_api_error_message") or (
            event.get("type") == "assistant" and event.get("error") == "rate_limit"
        ):
            limited = True
            text = _assistant_text(event)
            if text:
                trusted_texts.append(text)

        if event.get("type") == "result":
            if event.get("api_error_status") == 429:
                limited = True
            result_text = event.get("result") or ""
            if isinstance(result_text, str) and result_text:
                trusted_texts.append(result_text)

    for text in trusted_texts:
        if _text_looks_like_limit(text):
            limited = True
            if reset_time is None:
                reset_time = _parse_reset_time_from_text(text)

    return limited, reset_time


def looks_like_limit(output: str) -> bool:
    limited, _ = extract_limit_signals(output)
    return limited


def _parse_reset_time_from_text(text: str) -> datetime | None:
    for pattern in RESET_TIME_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        stamp = match.group(1).strip()
        for fmt in ("%I:%M %p", "%I:%M%p", "%I %p", "%I%p", "%H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = datetime.strptime(stamp, fmt)
            except ValueError:
                continue
            now = datetime.now()
            candidate = now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate
    return None


def try_parse_reset_time(output: str) -> datetime | None:
    _, reset_time = extract_limit_signals(output)
    return reset_time


def format_stream_event(raw_line: str) -> str | None:
    """Turns one stream-json line into a short human-readable line, e.g.
    "Reading docs/platform-hardening.md..." or "[tool: Bash] git status".
    Returns None (skip printing) for event types not worth showing. Falls
    back to printing the raw line if it isn't valid JSON, so nothing is
    silently swallowed."""
    raw_line = raw_line.strip()
    if not raw_line:
        return None
    try:
        event = json.loads(raw_line)
    except json.JSONDecodeError:
        return raw_line

    event_type = event.get("type")
    if event_type == "assistant":
        message = event.get("message", {})
        parts = []
        for block in message.get("content", []):
            block_type = block.get("type")
            if block_type == "text":
                parts.append(block.get("text", ""))
            elif block_type == "tool_use":
                name = block.get("name", "?")
                tool_input = block.get("input", {})
                summary = tool_input.get("command") or tool_input.get("description") or ""
                parts.append(f"[tool: {name}] {summary}".strip())
        return "\n".join(p for p in parts if p) or None
    if event_type == "result":
        return f"[result] {event.get('subtype', '')} {event.get('result', '')}".strip()
    return None


def run_once(cmd: list[str], log_path: str, quiet: bool = False) -> tuple[int, str]:
    if not quiet:
        print(f"\n$ {' '.join(cmd[:-1])} <prompt omitted, see log>\n", flush=True)

    captured: list[str] = []
    with open(log_path, "a") as log_file:
        log_file.write(f"\n\n===== run at {datetime.now().isoformat()} (quiet={quiet}) =====\n")
        log_file.write(f"command: {cmd}\n")
        log_file.flush()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()
            captured.append(line)
            if not quiet:
                pretty = format_stream_event(line)
                if pretty:
                    print(pretty, flush=True)
        process.wait()

    return process.returncode, "".join(captured)


def base_flags() -> list[str]:
    return [
        "--dangerously-skip-permissions",
        "--output-format",
        "stream-json",
        "--verbose",
    ]


def build_initial_cmd(prompt_text: str) -> list[str]:
    return ["claude", *base_flags(), "-p", prompt_text]


def build_continue_cmd(prompt_text: str) -> list[str]:
    return ["claude", "--continue", *base_flags(), "-p", prompt_text]


def build_resume_cmd(session_id: str, prompt_text: str) -> list[str]:
    return ["claude", "--resume", session_id, *base_flags(), "-p", prompt_text]


def preflight_wait(
    resume_cmd_builder,
    log_path: str,
    wait_minutes: int,
) -> None:
    """Pings with a trivial prompt before doing any real work, to catch the
    case where we're already mid-cooldown when this script starts (e.g.
    launched right after a manual run hit its limit). A ping that fails for
    a NON-limit reason (most commonly: no prior session exists yet to
    resume) is treated as "nothing to wait for" and we proceed straight to
    the real work -- this only ever delays, never blocks, startup."""
    print("Checking whether we're already in a usage-limit cooldown...", flush=True)
    while True:
        cmd = resume_cmd_builder(PING_PROMPT)
        returncode, output = run_once(cmd, log_path, quiet=True)

        limited, reset_time = extract_limit_signals(output)
        if not limited:
            if returncode == 0:
                print("Not currently limited — proceeding.", flush=True)
            else:
                print(
                    "Preflight ping failed for a non-limit reason (likely no prior "
                    "session to resume yet) — proceeding to the real run.",
                    flush=True,
                )
            return

        if reset_time is not None:
            wait_seconds = max((reset_time - datetime.now()).total_seconds() + 60, 30)
            print(
                f"Already in cooldown. Parsed reset time {reset_time.isoformat()} — "
                f"sleeping {wait_seconds / 60:.1f} minutes before checking again.",
                flush=True,
            )
        else:
            wait_seconds = wait_minutes * 60
            print(
                f"Already in cooldown, no reset time found — sleeping {wait_minutes} "
                "minutes before checking again.",
                flush=True,
            )
        time.sleep(wait_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "prompt_file",
        nargs="?",
        default=None,
        help="Path to a markdown (or plain text) file whose contents seed a fresh session. "
        "Omit this and pass --session-id instead to resume an existing session.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Resume an existing Claude Code session by id (via `claude --resume <id>`) "
        "instead of starting fresh from a prompt file.",
    )
    parser.add_argument(
        "--wait-minutes",
        type=int,
        default=60,
        help="Fallback wait when a limit is hit but no reset time can be parsed (default: 60)",
    )
    parser.add_argument(
        "--continue-prompt",
        default="Continue exactly where you left off.",
        help="Prompt sent on each resume (default when not using a prompt file / after the first run)",
    )
    parser.add_argument(
        "--log-file",
        default="claude_autoresume.log",
        help="Path to append full output to (default: ./claude_autoresume.log)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=200,
        help="Safety cap on total real attempts, counting both limit-triggered retries "
        "and normal turn-to-turn continuations (default: 200)",
    )
    parser.add_argument(
        "--done-marker",
        default=DEFAULT_DONE_MARKER,
        help="Exact line Claude must output to signal the whole task (not just this turn) "
        f"is complete (default: {DEFAULT_DONE_MARKER})",
    )
    args = parser.parse_args()

    if args.prompt_file and args.session_id:
        print(
            "Provide at most one of: a prompt-file argument, or --session-id "
            "(they're ambiguous together).",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.prompt_file and not args.session_id:
        cwd = str(Path.cwd())
        session_info = find_most_recent_session(cwd)
        if session_info is None:
            print(
                f"No prompt file or --session-id given, and no prior Claude Code sessions "
                f"found for this directory ({cwd}) — looked in "
                f"{CLAUDE_PROJECTS_DIR / sanitize_cwd_for_project_dir(cwd)}. "
                "Nothing to resume. Pass a prompt-file to start fresh, or --session-id to "
                "target a specific session. Stopping.",
                file=sys.stderr,
            )
            sys.exit(1)
        print_auto_selected_session_warning(cwd, session_info)
        args.session_id = session_info["session_id"]

    prompt_text: str | None = None
    if args.prompt_file:
        prompt_path = Path(args.prompt_file)
        if not prompt_path.is_file():
            print(f"Prompt file not found: {prompt_path}", file=sys.stderr)
            sys.exit(1)
        prompt_text = with_done_marker_instruction(prompt_path.read_text(), args.done_marker)

    continue_prompt = with_done_marker_instruction(args.continue_prompt, args.done_marker)

    session_mode = args.session_id is not None

    # Preflight: catch an already-active cooldown before spending a real
    # attempt. In session mode this pings the specific session; in
    # prompt-file mode it pings via --continue, which harmlessly no-ops if
    # no session exists yet (nothing to be mid-cooldown on).
    if session_mode:
        preflight_wait(
            lambda p: build_resume_cmd(args.session_id, p), args.log_file, args.wait_minutes
        )
    else:
        preflight_wait(build_continue_cmd, args.log_file, args.wait_minutes)

    attempt = 0
    first_run = True
    while attempt < args.max_retries:
        attempt += 1
        mode_label = "session-resume" if session_mode else ("initial" if first_run else "continue")
        print(f"=== attempt {attempt}/{args.max_retries} ({mode_label}) ===", flush=True)

        if session_mode:
            cmd = build_resume_cmd(args.session_id, continue_prompt)
        elif first_run:
            cmd = build_initial_cmd(prompt_text)  # type: ignore[arg-type]
        else:
            cmd = build_continue_cmd(continue_prompt)

        returncode, output = run_once(cmd, args.log_file)
        first_run = False

        limited, reset_time = extract_limit_signals(output)
        done = args.done_marker in output

        if not limited and done:
            print(
                f"\nDone marker ({args.done_marker!r}) seen — the whole task reports "
                "complete. Stopping.",
                flush=True,
            )
            return

        if not limited and not done:
            if returncode != 0:
                print(
                    f"\nClaude exited with code {returncode}, no limit language and no done "
                    "marker — stopping rather than retrying blindly, since this looks like a "
                    "real error rather than a normal turn ending. Check the log and re-run "
                    "manually if this was transient.",
                    flush=True,
                )
                sys.exit(returncode)
            print(
                "\nTurn ended (exit 0) with no limit language and no done marker — the task "
                "isn't finished yet. Resuming immediately (no cooldown wait, this wasn't a "
                "limit).",
                flush=True,
            )
            continue

        # limited (regardless of what `done` looked like — a limit message
        # cutting off mid-response could coincidentally contain marker-like
        # text, but a real limit always takes priority over treating it as
        # completion)
        if reset_time is not None:
            wait_seconds = max((reset_time - datetime.now()).total_seconds() + 60, 30)
            print(
                f"\nLimit hit. Parsed reset time {reset_time.isoformat()} — "
                f"sleeping {wait_seconds / 60:.1f} minutes.",
                flush=True,
            )
        else:
            wait_seconds = args.wait_minutes * 60
            print(
                f"\nLimit hit. No reset time found in output — "
                f"sleeping {args.wait_minutes} minutes before retrying.",
                flush=True,
            )
        time.sleep(wait_seconds)

    print(f"\nHit --max-retries ({args.max_retries}) without a clean finish. Stopping.", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
