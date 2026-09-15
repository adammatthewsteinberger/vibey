# Run resources and chat ops

Operator mid-run control for attachments, folders, skills, plugins, MCP
connectors, GitHub imports, memories/artifacts, chat metadata, response
actions, slash commands, and permission/cwd switching.

## Design (hybrid)

- **Native store** under `.claudeloop/runs/<run_id>/resources/` (and sibling
  `memories/`, `artifacts/`) is always authoritative for claudeloop.
- **Agent SDK options** (`permission_mode`, `skills`, `plugins`, `mcp_servers`,
  `add_dirs`, `allowed_tools`) are applied at session connect / reconnect.
- Product APIs (Claude.ai share, Anthropic `memory_stores`, deep-research
  backends) are **best-effort**: when unavailable, commands fail with an
  actionable message or fall back to a local export — never invent a fake
  success.

## Permission modes

| CLI | SDK `permission_mode` |
|---|---|
| `bypass` (default) | `bypassPermissions` |
| `manual` | `default` + `can_use_tool` approvals |
| `accept-edits` | `acceptEdits` |
| `plan` | `plan` |
| `auto` | `auto` |

Sessions **always start in bypass** so mid-run switches can return to bypass
(SDK security constraint). Manual mode never blocks on stdin: the runner
emits `tool.approval_needed` events; approve/deny via:

```bash
claudeloop tool approve REQUEST_ID
claudeloop tool deny REQUEST_ID --reason "…"
```

Timed-out approvals are **denied** with guidance — autonomy over waiting.

```bash
claudeloop run PLAN --permission-mode bypass
claudeloop permission-mode plan --run-id …
claudeloop permission-mode bypass --run-id …
claudeloop cwd /path/to/worktree --run-id …
```

## Start-of-run resources

```bash
claudeloop run PLAN \
  --cwd DIR \
  --attach ./spec.md --attach ./shots \
  --add-folder ../shared \
  --from-github owner/repo@main \
  --import-issue owner/repo#42 \
  --skill my-skill \
  --plugin ./plugins/local \
  --connector docs='{"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","."]}' \
  --web-search \
  --permission-mode bypass \
  --slash /status
```

## Mid-run CRUD

Same inbox pattern as `prompt` / `model`:

```bash
claudeloop attach PATH
claudeloop unattach NAME
claudeloop folder add|rm PATH
claudeloop skill add|rm NAME
claudeloop plugin add|rm NAME
claudeloop connector add|rm|list …
claudeloop github add OWNER/REPO[@REF]
claudeloop github import-issue OWNER/REPO#N
claudeloop research start "query"
claudeloop research status
claudeloop web-search "query"
claudeloop slash /compact
```

## Memories and artifacts

```bash
claudeloop memory list|get|set|rm [--run-id]
claudeloop artifact list|get|put|rm [--run-id]
```

Selected memories are appended into the system prompt for the run. Anthropic
hosted memory stores are not required; if a generated `claudeloop api`
surface later exposes them, thin sync wrappers can be added without changing
the native paths.

## Chat ops

Chats map to Claude Code sessions plus native metadata in
`.claudeloop/chats/<session_id>.json`:

```bash
claudeloop chat list|show|rename|delete|pin|unpin|unread|read|share|project …
```

`share` writes a **local** redacted bundle path (no invented Claude.ai share
API). `delete` removes native metadata; OS-owned Claude Code transcripts may
remain.

## Response actions

```bash
claudeloop response copy [--run-id]     # last assistant text → stdout
claudeloop response good|bad [--note]
claudeloop response retry               # re-queues last prompt as PromptNow
```

## Voice (optional)

```bash
pip install 'claudeloop[voice]'
claudeloop speak "hello"
claudeloop voice status
```

Without extras, `speak` uses macOS `say` or `espeak` when present; otherwise
prints an install hint. Voice input remains a stub and is never required for
autonomous runs.

## Run handoff snapshots

Every run writes control-plane snapshots under
`.claudeloop/runs/<run_id>/snapshots/`:

| File | When |
|---|---|
| `latest.json` | Overwritten on each status persist (digest-skip if unchanged) |
| `<ts>-<reason>.json` | Immutable copies for `started` / `waiting` / `stopped` / `finished` / `failed` / `manual` |
| `bundles/<ts>-<reason>/` | Optional portable copy of attachments/memories/artifacts (+ Claude transcript when found) |
| `claude/<session_id>.jsonl` | Best-effort copy from `~/.claude/projects/…` |

Auto triggers: run start, enter waiting, soft stop, auto finish/fail, and
every `_persist` (latest only). Explicit:

```bash
claudeloop snapshot [--run-id …] [--out PATH] [--bundle|--no-bundle]
```

Each write publishes on the existing state bus (`status.json` + `bus.jsonl`)
with `snapshot_path`, `snapshot_digest`, and `snapshot_reason` (`snapshot.written`
or `snapshot.latest`). External systems can poll `status.json`, follow
`bus.jsonl`, or read `snapshots/latest.json` directly.

**Honesty bars:** Claude Code transcripts are best-effort only — if missing,
JSON records `claude_session: {found: false, reason: …}` and the run continues.
Bundles may omit non-portable absolute folder / MCP paths; the JSON always
stands alone.

## Related

- [Autonomous runs](autonomous-runs.md)
- [Logging and observability](logging-and-observability.md)
- [Configuration](../getting-started/configuration.md)
- [CLI reference](../reference/cli.md)
