# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Approval policy × sandbox mode matrix, including the security-drift guard."""

from __future__ import annotations

import pytest

from codexloop.domain.approval import (
    DEFAULT_APPROVAL,
    DEFAULT_SANDBOX,
    ApprovalPolicy,
    SandboxMode,
    validate,
)
from codexloop.domain.errors import ConfigurationError


def test_default_pair_is_exactly_never_workspace_write() -> None:
    assert DEFAULT_APPROVAL is ApprovalPolicy.NEVER
    assert DEFAULT_SANDBOX is SandboxMode.WORKSPACE_WRITE
    assert DEFAULT_APPROVAL.value == "never"
    assert DEFAULT_SANDBOX.value == "workspace-write"
    validate(DEFAULT_APPROVAL, DEFAULT_SANDBOX)


def test_never_workspace_write_is_valid() -> None:
    validate(ApprovalPolicy.NEVER, SandboxMode.WORKSPACE_WRITE)


def test_enum_values_are_codex_cli_strings() -> None:
    assert {p.value for p in ApprovalPolicy} == {
        "never",
        "on-request",
        "on-failure",
        "untrusted",
    }
    assert {s.value for s in SandboxMode} == {
        "read-only",
        "workspace-write",
        "danger-full-access",
    }


@pytest.mark.parametrize("policy", list(ApprovalPolicy))
@pytest.mark.parametrize("sandbox", [SandboxMode.READ_ONLY, SandboxMode.WORKSPACE_WRITE])
def test_non_dangerous_sandbox_is_valid_for_every_policy(
    policy: ApprovalPolicy, sandbox: SandboxMode
) -> None:
    validate(policy, sandbox)


@pytest.mark.parametrize("policy", list(ApprovalPolicy))
def test_danger_full_access_requires_explicit_allow_dangerous(policy: ApprovalPolicy) -> None:
    with pytest.raises(ConfigurationError):
        validate(policy, SandboxMode.DANGER_FULL_ACCESS)
    with pytest.raises(ConfigurationError):
        validate(policy, SandboxMode.DANGER_FULL_ACCESS, allow_dangerous=False)
    validate(policy, SandboxMode.DANGER_FULL_ACCESS, allow_dangerous=True)
