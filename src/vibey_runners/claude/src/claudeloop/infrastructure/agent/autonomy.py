# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The never-block-on-a-human guarantees. See
docs/architecture/decisions/0007-ask-user-question-denied-with-guidance.md and
docs/guides/never-blocking.md for the full mitigation table this implements."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import HookContext, HookMatcher
from claude_agent_sdk.types import HookInput, HookJSONOutput

_ASK_USER_QUESTION_DENY_MESSAGE = (
    "Running autonomously, no user available to answer — choose the option you "
    "would recommend, note the assumption you're making, and proceed. Do not "
    "wait for a response."
)

AUTONOMY_SYSTEM_PROMPT_FRAGMENT = (
    "You are running autonomously and unattended. Nobody is watching this "
    "session in real time and nobody can answer a question mid-task. Never end "
    "a turn by asking 'Shall I proceed?' or waiting for confirmation on a "
    "reversible action that follows from the task — just do it. If you would "
    "normally ask a clarifying question, make the most reasonable assumption, "
    "state it plainly, and continue. "
    "Structured completion verdict: leave blocked_on null unless a human or "
    "external dependency must intervene. Waiting on a background task, test "
    "suite, or build you started belongs in remaining_work with blocked_on "
    "null — a non-null blocked_on stops this autonomous run permanently."
)


async def _deny_ask_user_question(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """PreToolUse hook, not `can_use_tool`: with permission_mode="bypassPermissions"
    the SDK auto-approves every tool call before `can_use_tool` is ever consulted
    (confirmed live — the SDK itself warns CanUseToolShadowedWarning on startup),
    so that callback is dead code for gating anything. A PreToolUse hook still
    fires under bypassPermissions and is the only way to actually deny a tool."""
    del tool_use_id, context
    if input_data.get("tool_name") != "AskUserQuestion":
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": _ASK_USER_QUESTION_DENY_MESSAGE,
        }
    }


async def _auto_allow_permission_request(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    del input_data, tool_use_id, context
    return {}


async def _log_notification(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    del tool_use_id, context
    # Intentionally a no-op beyond returning an empty decision: Notification
    # hooks must never block. Actual logging happens via the AuditLog port at
    # the call site that constructs these hooks (infrastructure/agent/options.py),
    # not here, so this module stays free of an AuditLog dependency.
    del input_data
    return {}


def build_hooks() -> dict[Any, list[HookMatcher]]:
    # dict[Any, ...] rather than the SDK's own HookEvent-literal-keyed type:
    # that type isn't exported as a standalone name we can annotate against
    # without repeating its ten-member Literal union here. mypy still checks
    # the keys used below are valid at the ClaudeAgentOptions(hooks=...) call
    # site in options.py.
    return {
        "PreToolUse": [HookMatcher(matcher="AskUserQuestion", hooks=[_deny_ask_user_question])],
        "PermissionRequest": [HookMatcher(hooks=[_auto_allow_permission_request])],
        "Notification": [HookMatcher(hooks=[_log_notification])],
    }
