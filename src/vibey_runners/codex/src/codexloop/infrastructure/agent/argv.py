# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure Codex CLI argv construction — list building only, no subprocess."""

from __future__ import annotations

from dataclasses import dataclass

from codexloop.domain.approval import (
    DEFAULT_APPROVAL,
    DEFAULT_SANDBOX,
    ApprovalPolicy,
    SandboxMode,
)
from codexloop.domain.model_profile import Effort

PROBE_PROMPT = "reply with the single word OK"


def _quote_c_value(value: str) -> str:
    """Wrap ``value`` in double quotes, escaping any internal quotes."""
    return '"' + value.replace('"', '\\"') + '"'


def _c_override(key: str, value: str) -> list[str]:
    return ["-c", f"{key}={_quote_c_value(value)}"]


def _c_bool_override(key: str, value: bool) -> list[str]:
    return ["-c", f"{key}={'true' if value else 'false'}"]


@dataclass(frozen=True, slots=True)
class ExecOpts:
    """Options for ``codex exec`` / ``codex exec resume`` argv construction."""

    prompt: str
    model: str | None = None
    effort: Effort | None = None
    approval: ApprovalPolicy = DEFAULT_APPROVAL
    sandbox: SandboxMode = DEFAULT_SANDBOX
    add_dirs: tuple[str, ...] = ()
    network_access: bool = False
    output_schema: str | None = None
    output_last_message: str | None = None
    skip_git_repo_check: bool = False


def _shared_flags(opts: ExecOpts) -> list[str]:
    """Flags common to exec and resume (after ``--json``)."""
    argv: list[str] = []
    if opts.model is not None:
        argv.extend(["--model", opts.model])
    argv.extend(_c_override("approval_policy", opts.approval.value))
    argv.extend(_c_override("sandbox_mode", opts.sandbox.value))
    argv.extend(_c_bool_override("sandbox_workspace_write.network_access", opts.network_access))
    if opts.effort is not None:
        argv.extend(_c_override("model_reasoning_effort", opts.effort.value))
    for directory in opts.add_dirs:
        argv.extend(["--add-dir", directory])
    if opts.output_schema is not None:
        argv.extend(["--output-schema", opts.output_schema])
    if opts.output_last_message is not None:
        argv.extend(["--output-last-message", opts.output_last_message])
    if opts.skip_git_repo_check:
        argv.append("--skip-git-repo-check")
    return argv


def build_exec_argv(opts: ExecOpts) -> list[str]:
    """Build ``codex exec … -- <prompt>``."""
    argv: list[str] = ["codex", "exec", "--json"]
    argv.extend(_shared_flags(opts))
    argv.extend(["--", opts.prompt])
    return argv


def build_resume_argv(thread_id: str | None, opts: ExecOpts) -> list[str]:
    """Build ``codex exec resume <id|--last> … -- <prompt>``.

    Policy is always expressed via ``-c`` overrides — never a bare ``--sandbox``.
    """
    argv: list[str] = ["codex", "exec", "resume"]
    if thread_id is None:
        argv.append("--last")
    else:
        argv.append(thread_id)
    argv.append("--json")
    argv.extend(_shared_flags(opts))
    argv.extend(["--", opts.prompt])
    return argv


def build_probe_argv(opts: ExecOpts) -> list[str]:
    """Build the capacity-probe argv (ephemeral, read-only, fixed prompt).

    ``opts`` is accepted for API symmetry with exec/resume; probe policy and
    prompt are fixed and do not vary with ``opts``.
    """
    _ = opts
    return [
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        *_c_override("approval_policy", ApprovalPolicy.NEVER.value),
        *_c_override("sandbox_mode", SandboxMode.READ_ONLY.value),
        "--",
        PROBE_PROMPT,
    ]
