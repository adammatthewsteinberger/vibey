# Security Policy

## Overview

Vibey is a queue-based conductor for autonomous software delivery. Because Vibey orchestrates autonomous engines, tools, code mutation, and optional deployment pipelines, isolation and defense-in-depth are foundational architectural requirements (see ADR-0008, ADR-0012, ADR-0013, ADR-0014).

---

## Threat Model & Security Boundaries

### 1. Worktree & Container Isolation Runtime (ADR-0008, Task 9.1)
- **Worktree Sandboxing**: Every job and phase executes inside an isolated ephemeral git worktree branched from base or integration heads. This is the only isolation boundary active today.
- **OCI Container Hardening — implemented and unit-tested, not yet an active runtime path**: `ContainerConfig` and `OciContainerExecutor`
  (`src/vibey/infrastructure/container/config.py`, `runtime.py`) implement the
  hardening described below, but nothing outside their own test file
  (`tests/infrastructure/container/test_runtime.py`) ever constructs them —
  `bootstrap.py` does not import `vibey.infrastructure.container`, and no CLI
  flag or `vibey.toml` key (`[isolation] level = "container"` included; see
  [the configuration reference](docs/reference/configuration.md#isolation))
  reaches this code. Every job runs in a plain worktree regardless of what
  `[isolation]` says. Do not rely on the controls below until this adapter is
  wired into the composition root:
  - **Read-Only Root Filesystem**: Containers run with `--read-only`.
  - **Dropped Capabilities**: All Linux kernel capabilities are dropped (`--cap-drop=ALL`).
  - **Privilege Escalation Prevention**: Containers run with `--security-opt=no-new-privileges:true`.
  - **Ephemeral Storage**: `/tmp` is mounted as a restricted tmpfs (`rw,noexec,nosuid,size=512m`).
  - **Resource Capping**: Hard memory limits (`--memory=4g`) and CPU quotas (`--cpus=2.0`).
  - **Network Isolation**: Defaults to `--network=none` unless explicitly configured for network-dependent build phases.

### 2. Destructive-Command Prevention (Task 9.2) — implemented and unit-tested, not yet an active runtime path
- `CommandSecurityPolicy` (`src/vibey/domain/command_guard.py`) implements the
  scans described below, but nothing outside its own test file
  (`tests/domain/test_command_guard.py`) ever constructs or calls it — none of
  the actual subprocess call sites (`infrastructure/engines/claudeloop_process.py`,
  `infrastructure/build/gate_runner.py`, the CLI's `az` invocations, etc.)
  invoke `check_command` before running a command. **Do not rely on the
  controls below: autonomous engines are not currently prevented from
  executing destructive operations.**
  - **Git Safety**: Blocks `git reset --hard`, `git push --force`, `git push -f`, `git branch -D main|master`.
  - **Filesystem Safety**: Blocks `rm -rf /`, `rm -rf ~`, `rm -rf *`, `mkfs.*`, `dd of=/dev/`.
  - **System Safety**: Blocks `reboot`, `shutdown`, `poweroff`, fork bombs.
  - **Database Safety**: Blocks raw `DROP DATABASE` or `DROP TABLE` outside migration harnesses.

### 3. Scope-Bound Mutation Enforcement (Task 9.3) — implemented and unit-tested, not yet an active runtime path
- `MutationScope` (`src/vibey/domain/scope_guard.py`) implements the checks
  described below, but nothing outside its own test file
  (`tests/domain/test_scope_guard.py`) ever constructs or calls it — the
  Phase ② (Build Implement) file-mutation path
  (`application/build_implement_handler.py`) never invokes it. **Do not rely
  on the controls below: file mutations are not currently scope-checked.**
  - Directory traversal (`../`, absolute paths escaping the worktree root)
  - Symlink escapes pointing outside the repository tree
  - Modification of sensitive repository assets (`.git/`, `.env*`, `id_rsa`, `secrets.json`)
  - Modification of files outside declared `spec.md` work item paths
  would be blocked with a `ScopeViolation` before staging, once wired in.

### 4. Untrusted Prompt Defense & Delimiter Shielding (Task 9.4) — implemented and unit-tested, not yet an active runtime path
- `PromptShield` (`src/vibey/domain/prompt_shield.py`) implements the
  protections described below, but nothing outside its own test file
  (`tests/domain/test_prompt_shield.py`) ever constructs or calls it — no
  design or build handler (`application/seed_prompt.py`,
  `application/design_handler.py`, `application/build_implement_handler.py`,
  etc.) frames untrusted input through it. This includes the skills-context
  packet: `infrastructure/skills_context.py`'s `VibeySkillsContextCompiler`
  retrieves markdown from the independently-versioned, third-party
  `vibey-skills` marketplace, and `build_implement_handler.py` appends it
  verbatim to the BUILD prompt whenever a project's `skills_context.mode` is
  `inject` — with no `PromptShield` framing. **Do not rely on the controls
  below: seed prompts, interview answers, issue descriptions, skills-context
  packets, and other third-party inputs are not currently shielded.**
  - Strips non-printable ASCII control codes and ANSI escape sequences.
  - Generates unique cryptographic nonces per interaction (`<{label}_{nonce}>...<{label}_{nonce}>`).
  - Neutralizes XML/tag delimiter breakouts (`</...` escaping).
  - Prepends explicit security directives instructing models to treat framed inputs strictly as data.
  - Audits for common injection heuristics (`is_suspicious_injection`).

### 5. Secret Redaction & Environment Hygiene
- Subprocess execution strips sensitive git and shell environment variables (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, etc.) using `CleanGitEnvSubprocessExecutor`.
- All ledger and telemetry records run through redaction masks (`redact.py`) to prevent leakage of credentials, tokens, or private keys.

### 6. Webhook Payload Integrity — implemented and unit-tested, not yet an active runtime path
- `infrastructure/notify/` implements a `NotificationService` whose webhook
  dispatch signs payloads with HMAC-SHA256 signatures
  (`X-Vibey-Signature: sha256=...`) and validates them against URL scheme
  restrictions, and it is covered by tests. It is **not yet wired into
  `bootstrap.py`, the worker, or the CLI** — no flag or `vibey.toml` key
  constructs it today, so no webhook notifications are dispatched at all.
  Treat it as implemented-and-tested, not yet an active runtime path (see
  the README's [Notifications](README.md#notifications) section).

---

## Reporting a Vulnerability

If you discover a security vulnerability in Vibey, please report it responsibly:

1. **Do NOT open a public issue.**
2. Send a detailed report to the security team or repository maintainers.
3. Include reproducible steps, affected versions, and potential impact.
4. We will acknowledge receipt within 48 hours and coordinate remediation before public disclosure.
