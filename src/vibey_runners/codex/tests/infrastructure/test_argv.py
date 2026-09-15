# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Regression guards and option-matrix coverage for the Codex argv builder."""

from __future__ import annotations

from typing import Any

import pytest

from codexloop.domain.approval import ApprovalPolicy, SandboxMode
from codexloop.domain.model_profile import Effort
from codexloop.infrastructure.agent.argv import (
    ExecOpts,
    build_exec_argv,
    build_probe_argv,
    build_resume_argv,
)


def _c_overrides(argv: list[str]) -> list[str]:
    """Return the `-c` values (key="value" tokens) in order."""
    out: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "-c" and i + 1 < len(argv):
            out.append(argv[i + 1])
            i += 2
            continue
        i += 1
    return out


def _base_opts(**overrides: Any) -> ExecOpts:
    defaults: dict[str, Any] = {
        "prompt": "do the thing",
        "model": "gpt-5",
        "effort": Effort.MEDIUM,
        "approval": ApprovalPolicy.NEVER,
        "sandbox": SandboxMode.WORKSPACE_WRITE,
        "add_dirs": (),
        "network_access": False,
        "output_schema": None,
        "output_last_message": None,
        "skip_git_repo_check": False,
    }
    defaults.update(overrides)
    return ExecOpts(**defaults)


# --- Regression guards (a)–(f) -------------------------------------------------


def test_resume_argv_never_contains_bare_sandbox() -> None:
    opts = _base_opts(sandbox=SandboxMode.DANGER_FULL_ACCESS)
    for thread_id in ("thread-abc", None):
        argv = build_resume_argv(thread_id, opts)
        assert "--sandbox" not in argv
        assert 'sandbox_mode="danger-full-access"' in _c_overrides(argv)


def test_exec_and_resume_express_identical_policy_via_c() -> None:
    opts = _base_opts(
        approval=ApprovalPolicy.ON_REQUEST,
        sandbox=SandboxMode.READ_ONLY,
        effort=Effort.HIGH,
    )
    exec_c = _c_overrides(build_exec_argv(opts))
    resume_c = _c_overrides(build_resume_argv("tid-1", opts))
    resume_last_c = _c_overrides(build_resume_argv(None, opts))
    assert exec_c == resume_c == resume_last_c
    assert 'approval_policy="on-request"' in exec_c
    assert 'sandbox_mode="read-only"' in exec_c
    assert "sandbox_workspace_write.network_access=false" in exec_c
    assert 'model_reasoning_effort="high"' in exec_c


def test_full_auto_never_appears_in_any_argv() -> None:
    opts = _base_opts()
    argvs = [
        build_exec_argv(opts),
        build_resume_argv("tid", opts),
        build_resume_argv(None, opts),
        build_probe_argv(opts),
    ]
    for argv in argvs:
        assert "--full-auto" not in argv
        assert "full-auto" not in argv


def test_argv1_is_always_exec() -> None:
    opts = _base_opts()
    for argv in (
        build_exec_argv(opts),
        build_resume_argv("tid", opts),
        build_resume_argv(None, opts),
        build_probe_argv(opts),
    ):
        assert argv[0] == "codex"
        assert argv[1] == "exec"


def test_prompt_always_follows_double_dash_separator() -> None:
    opts = _base_opts(prompt="hello -- world")
    for argv in (
        build_exec_argv(opts),
        build_resume_argv("tid", opts),
        build_resume_argv(None, opts),
    ):
        sep = argv.index("--")
        assert argv[sep + 1] == "hello -- world"
        assert argv[-1] == "hello -- world"

    probe = build_probe_argv(opts)
    sep = probe.index("--")
    assert probe[sep + 1] == "reply with the single word OK"


def test_probe_argv_has_ephemeral_and_read_only_sandbox() -> None:
    argv = build_probe_argv(_base_opts())
    assert "--ephemeral" in argv
    assert 'sandbox_mode="read-only"' in _c_overrides(argv)
    assert 'approval_policy="never"' in _c_overrides(argv)


def test_builders_return_list_not_str() -> None:
    opts = _base_opts()
    assert isinstance(build_exec_argv(opts), list)
    assert isinstance(build_resume_argv("t", opts), list)
    assert isinstance(build_probe_argv(opts), list)
    assert all(isinstance(x, str) for x in build_exec_argv(opts))


# --- Exact argv table over the option matrix ----------------------------------


@pytest.mark.parametrize(
    ("opts", "expected"),
    [
        pytest.param(
            ExecOpts(
                prompt="p",
                model="gpt-5",
                effort=Effort.LOW,
                approval=ApprovalPolicy.NEVER,
                sandbox=SandboxMode.WORKSPACE_WRITE,
            ),
            [
                "codex",
                "exec",
                "--json",
                "--model",
                "gpt-5",
                "-c",
                'approval_policy="never"',
                "-c",
                'sandbox_mode="workspace-write"',
                "-c",
                "sandbox_workspace_write.network_access=false",
                "-c",
                'model_reasoning_effort="low"',
                "--",
                "p",
            ],
            id="defaults-plus-model-effort",
        ),
        pytest.param(
            ExecOpts(
                prompt="schema turn",
                model="o3",
                effort=Effort.HIGH,
                approval=ApprovalPolicy.UNTRUSTED,
                sandbox=SandboxMode.READ_ONLY,
                add_dirs=("/tmp/a", "/tmp/b"),
                output_schema="/tmp/schema.json",
                output_last_message="/tmp/last.txt",
                skip_git_repo_check=True,
            ),
            [
                "codex",
                "exec",
                "--json",
                "--model",
                "o3",
                "-c",
                'approval_policy="untrusted"',
                "-c",
                'sandbox_mode="read-only"',
                "-c",
                "sandbox_workspace_write.network_access=false",
                "-c",
                'model_reasoning_effort="high"',
                "--add-dir",
                "/tmp/a",
                "--add-dir",
                "/tmp/b",
                "--output-schema",
                "/tmp/schema.json",
                "--output-last-message",
                "/tmp/last.txt",
                "--skip-git-repo-check",
                "--",
                "schema turn",
            ],
            id="full-matrix",
        ),
        pytest.param(
            ExecOpts(
                prompt="minimal",
                approval=ApprovalPolicy.ON_FAILURE,
                sandbox=SandboxMode.DANGER_FULL_ACCESS,
            ),
            [
                "codex",
                "exec",
                "--json",
                "-c",
                'approval_policy="on-failure"',
                "-c",
                'sandbox_mode="danger-full-access"',
                "-c",
                "sandbox_workspace_write.network_access=false",
                "--",
                "minimal",
            ],
            id="no-model-no-effort",
        ),
        pytest.param(
            ExecOpts(
                prompt='say "hi"',
                model='mod"el',
                effort=Effort.MEDIUM,
                approval=ApprovalPolicy.ON_REQUEST,
                sandbox=SandboxMode.WORKSPACE_WRITE,
            ),
            [
                "codex",
                "exec",
                "--json",
                "--model",
                'mod"el',
                "-c",
                'approval_policy="on-request"',
                "-c",
                'sandbox_mode="workspace-write"',
                "-c",
                "sandbox_workspace_write.network_access=false",
                "-c",
                'model_reasoning_effort="medium"',
                "--",
                'say "hi"',
            ],
            id="quoted-c-values-prompt-unquoted",
        ),
    ],
)
def test_exec_argv_matrix(opts: ExecOpts, expected: list[str]) -> None:
    assert build_exec_argv(opts) == expected


@pytest.mark.parametrize(
    ("thread_id", "opts", "expected_prefix"),
    [
        pytest.param(
            "thread-42",
            ExecOpts(prompt="cont", model="gpt-5", effort=Effort.LOW),
            ["codex", "exec", "resume", "thread-42", "--json"],
            id="resume-by-id",
        ),
        pytest.param(
            None,
            ExecOpts(prompt="cont", model="gpt-5", effort=Effort.LOW),
            ["codex", "exec", "resume", "--last", "--json"],
            id="resume-last",
        ),
    ],
)
def test_resume_argv_prefix_and_shared_flags(
    thread_id: str | None, opts: ExecOpts, expected_prefix: list[str]
) -> None:
    argv = build_resume_argv(thread_id, opts)
    assert argv[: len(expected_prefix)] == expected_prefix
    assert "--sandbox" not in argv
    assert argv[-2:] == ["--", "cont"]
    # Same optional/policy flags as exec after the resume-specific prefix.
    exec_argv = build_exec_argv(opts)
    # exec: codex exec --json ... ; resume: codex exec resume <id|--last> --json ...
    assert argv[len(expected_prefix) :] == exec_argv[3:]


def test_network_access_is_a_toml_boolean_for_exec_and_resume() -> None:
    opts = _base_opts(network_access=True)
    for argv in (build_exec_argv(opts), build_resume_argv("tid", opts)):
        overrides = _c_overrides(argv)
        assert "sandbox_workspace_write.network_access=true" in overrides
        assert 'sandbox_workspace_write.network_access="true"' not in overrides


def test_probe_argv_exact() -> None:
    assert build_probe_argv(_base_opts(prompt="ignored")) == [
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        "-c",
        'approval_policy="never"',
        "-c",
        'sandbox_mode="read-only"',
        "--",
        "reply with the single word OK",
    ]


def test_exec_opts_defaults() -> None:
    opts = ExecOpts(prompt="x")
    assert opts.approval is ApprovalPolicy.NEVER
    assert opts.sandbox is SandboxMode.WORKSPACE_WRITE
    assert opts.model is None
    assert opts.effort is None
    assert opts.add_dirs == ()
    assert opts.network_access is False
    assert opts.output_schema is None
    assert opts.output_last_message is None
    assert opts.skip_git_repo_check is False
