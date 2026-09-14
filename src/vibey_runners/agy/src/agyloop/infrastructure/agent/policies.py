# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Inspect LocalAgentConfig policies without leaking blocking HITL handlers."""

from __future__ import annotations

from google.antigravity.hooks.policy import Decision, Policy

_INTERACTIVE_HOOK_NAMES = frozenset({"ToolConfirmationHook", "AskQuestionHook"})
_INTERACTIVE_MODULE_MARKER = "utils.interactive"


def _policies_of(cfg: object) -> list[Policy]:
    raw = getattr(cfg, "policies", ()) or ()
    return [item for item in raw if isinstance(item, Policy)]


def config_has_allow_all(cfg: object) -> bool:
    """True when ``policy.allow_all()`` is on the config (the autonomy switch)."""
    return any(getattr(item, "name", "") == "allow_all" for item in _policies_of(cfg))


def _has_blocking_ask_user(cfg: object) -> bool:
    for item in _policies_of(cfg):
        if item.decision != Decision.ASK_USER:
            continue
        handler = item.ask_user
        if handler is None:
            return True
        module = getattr(handler, "__module__", "")
        if _INTERACTIVE_MODULE_MARKER in module:
            return True
    return False


def _has_interactive_hooks(cfg: object) -> bool:
    for hook in getattr(cfg, "hooks", ()) or ():
        if type(hook).__name__ in _INTERACTIVE_HOOK_NAMES:
            return True
        if _INTERACTIVE_MODULE_MARKER in type(hook).__module__:
            return True
    return False


def config_has_nonblocking_policies(cfg: object) -> bool:
    """True when no policy/hook can stall waiting for a human."""
    return not _has_blocking_ask_user(cfg) and not _has_interactive_hooks(cfg)
