# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""User-facing permission modes — compiled to Antigravity policies by the adapter.

The port speaks this enum only. Infrastructure must not leak
``google.antigravity`` types into application/ or domain/.
"""

from __future__ import annotations

from typing import Literal

UserPermissionMode = Literal["autonomous", "scoped", "safe", "yolo"]

USER_PERMISSION_MODES: tuple[UserPermissionMode, ...] = (
    "autonomous",
    "scoped",
    "safe",
    "yolo",
)

DEFAULT_USER_PERMISSION_MODE: UserPermissionMode = "autonomous"
DEFAULT_TOOL_APPROVAL_TIMEOUT_SECONDS = 30.0


def parse_user_permission_mode(value: str) -> UserPermissionMode:
    key = value.strip().lower().replace("_", "-")
    aliases = {
        "bypass": "autonomous",
        "bypasspermissions": "autonomous",
        "bypass-permissions": "autonomous",
        "allow-all": "autonomous",
        "workspace": "scoped",
        "workspace-only": "scoped",
        "nondestructive": "safe",
        "danger": "yolo",
        "unrestricted": "yolo",
    }
    key = aliases.get(key, key)
    if key not in USER_PERMISSION_MODES:
        raise ValueError(
            f"invalid permission mode {value!r}; expected one of {USER_PERMISSION_MODES}"
        )
    return key
