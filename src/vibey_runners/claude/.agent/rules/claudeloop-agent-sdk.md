# claudeloop-agent-sdk (Antigravity mirror of `.claude/skills/claudeloop-agent-sdk/SKILL.md`)


# claudeloop + claude-agent-sdk

`infrastructure/agent/` is the only place `claude_agent_sdk` may be
imported.

- Default gateway is the SDK (`ClaudeSDKClient`). Use `ClaudeSDKClient`,
  never `query()` — the client stays alive across error results.
- Autonomy: `permission_mode="bypassPermissions"` (no
  `dangerously_skip_permissions` field in Python SDK — this is the
  equivalent).
- `can_use_tool` denies `AskUserQuestion` with guidance, never awaits input.
- `output_format` is JSON schema (`{complete, remaining_work, blocked_on,
  summary}`) — structured output is primary, substring fallback is legacy.
- `blocked_on` must be null for waitable work — only true external/human
  blockers. Non-null terminates the run as `Blocked`.
- Rate-limit signals: read three (`RateLimitEvent`, `ResultMessage
  .api_error_status`, `AssistantMessage.error`), trust none alone.
- `CLAUDE_CODE_RETRY_WATCHDOG` off by default. Opt-in via
  `--retry-watchdog`. See ADR 0005.

See ADR 0002, 0005, 0007.
