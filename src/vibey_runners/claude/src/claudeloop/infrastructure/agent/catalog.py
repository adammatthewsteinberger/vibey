# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""SessionCatalog over claude_agent_sdk.list_sessions() / get_session_info().

Never parses ~/.claude/projects/*.jsonl directly — that format is explicitly
documented as changing between Claude Code releases. This is the supported
replacement for find_most_recent_session() in the legacy script."""

from __future__ import annotations

from datetime import datetime, timezone

from claude_agent_sdk import SDKSessionInfo, list_sessions

from claudeloop.domain.session import SessionRef

# domain.SessionRef requires a non-blank cwd (a session with no known
# directory is a real, observed case from list_sessions() with no `directory`
# filter — global cross-project listings return entries whose own `cwd` field
# can be empty). Rather than weaken that domain invariant for this one
# ambiguous upstream case, substitute a visible sentinel so a broken chain
# fails loudly as "(unknown)" in `claudeloop sessions` output instead of
# raising InvalidSessionSelectorError and crashing the whole listing.
_UNKNOWN_CWD = "(unknown)"


class SdkSessionCatalog:
    def most_recent(self, cwd: str) -> SessionRef | None:
        sessions = list_sessions(directory=cwd, limit=1)
        if not sessions:
            return None
        return _to_session_ref(sessions[0], cwd)

    def list_all(self, cwd: str | None = None) -> list[SessionRef]:
        sessions = list_sessions(directory=cwd)
        return [_to_session_ref(s, cwd or s.cwd or _UNKNOWN_CWD) for s in sessions]


def _to_session_ref(info: SDKSessionInfo, cwd: str) -> SessionRef:
    resolved_cwd = info.cwd or cwd or _UNKNOWN_CWD
    # SDKSessionInfo.last_modified is milliseconds since the epoch (confirmed
    # against a live claude_agent_sdk.list_sessions() call — a 13-digit int,
    # not the 10-digit seconds form; datetime.fromtimestamp() on the raw
    # value raises ValueError('year 58576 is out of range') otherwise).
    last_modified: datetime | None = None
    if isinstance(info.last_modified, int | float):
        last_modified = datetime.fromtimestamp(info.last_modified / 1000, tz=timezone.utc)
    preview = (info.first_prompt or "")[:200] or None
    return SessionRef(
        session_id=info.session_id,
        cwd=resolved_cwd,
        last_modified=last_modified,
        git_branch=info.git_branch,
        first_prompt_preview=preview,
    )
