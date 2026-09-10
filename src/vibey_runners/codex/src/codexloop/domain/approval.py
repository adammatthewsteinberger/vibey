# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Approval policy × sandbox mode. Defaults never wait and stay in-workspace."""

from __future__ import annotations

from enum import StrEnum

from codexloop.domain.errors import ConfigurationError


class ApprovalPolicy(StrEnum):
    NEVER = "never"
    ON_REQUEST = "on-request"
    ON_FAILURE = "on-failure"
    UNTRUSTED = "untrusted"


class SandboxMode(StrEnum):
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"
    DANGER_FULL_ACCESS = "danger-full-access"


DEFAULT_APPROVAL = ApprovalPolicy.NEVER
DEFAULT_SANDBOX = SandboxMode.WORKSPACE_WRITE


def validate(
    policy: ApprovalPolicy,
    sandbox: SandboxMode,
    *,
    allow_dangerous: bool = False,
) -> None:
    """Raise unless ``danger-full-access`` is paired with ``allow_dangerous=True``."""
    if sandbox is SandboxMode.DANGER_FULL_ACCESS and not allow_dangerous:
        raise ConfigurationError(
            f"sandbox mode {sandbox.value} requires allow_dangerous=True"
            f" (approval_policy={policy.value})"
        )
