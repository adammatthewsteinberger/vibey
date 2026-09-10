# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Permission-mode mapping for Claude Agent SDK — pure, no I/O."""

from __future__ import annotations

from typing import Literal

# User-facing names → SDK permission_mode literals.
UserPermissionMode = Literal["bypass", "manual", "accept-edits", "plan", "auto"]
SdkPermissionMode = Literal[
    "bypassPermissions", "default", "acceptEdits", "plan", "auto", "dontAsk"
]

USER_TO_SDK: dict[str, SdkPermissionMode] = {
    "bypass": "bypassPermissions",
    "manual": "default",
    "accept-edits": "acceptEdits",
    "plan": "plan",
    "auto": "auto",
}

SDK_TO_USER: dict[SdkPermissionMode, UserPermissionMode] = {
    "bypassPermissions": "bypass",
    "default": "manual",
    "acceptEdits": "accept-edits",
    "plan": "plan",
    "auto": "auto",
    "dontAsk": "manual",
}

DEFAULT_USER_PERMISSION_MODE: UserPermissionMode = "bypass"
DEFAULT_TOOL_APPROVAL_TIMEOUT_SECONDS = 30.0


def parse_user_permission_mode(value: str) -> UserPermissionMode:
    key = value.strip().lower().replace("_", "-")
    aliases = {
        "bypasspermissions": "bypass",
        "bypass-permissions": "bypass",
        "acceptedits": "accept-edits",
        "accept_edits": "accept-edits",
    }
    key = aliases.get(key, key)
    if key not in USER_TO_SDK:
        raise ValueError(f"invalid permission mode {value!r}; expected one of {tuple(USER_TO_SDK)}")
    # key is validated against USER_TO_SDK keys, which are the UserPermissionMode literals.
    return key  # type: ignore[return-value]


def to_sdk_permission_mode(mode: UserPermissionMode) -> SdkPermissionMode:
    return USER_TO_SDK[mode]
