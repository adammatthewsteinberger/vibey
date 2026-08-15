# Security Policy

## Overview

Vibey is a queue-based conductor for autonomous software delivery. Because Vibey orchestrates autonomous engines, tools, code mutation, and optional deployment pipelines, isolation and defense-in-depth are foundational architectural requirements (see ADR-0008, ADR-0012, ADR-0013, ADR-0014).

---

## Threat Model & Security Boundaries

### 1. Worktree & Container Isolation Runtime (ADR-0008, Task 9.1)
- **Worktree Sandboxing**: Every job and phase executes inside an isolated ephemeral git worktree branched from base or integration heads.
- **OCI Container Hardening**: When container runtime execution is enabled:
  - **Read-Only Root Filesystem**: Containers run with `--read-only`.
  - **Dropped Capabilities**: All Linux kernel capabilities are dropped (`--cap-drop=ALL`).
  - **Privilege Escalation Prevention**: Containers run with `--security-opt=no-new-privileges:true`.
  - **Ephemeral Storage**: `/tmp` is mounted as a restricted tmpfs (`rw,noexec,nosuid,size=512m`).
  - **Resource Capping**: Hard memory limits (`--memory=4g`) and CPU quotas (`--cpus=2.0`).
  - **Network Isolation**: Defaults to `--network=none` unless explicitly configured for network-dependent build phases.

### 2. Destructive-Command Prevention (Task 9.2)
- Autonomous engines are prohibited from executing destructive operations.
- `CommandSecurityPolicy` scans all command strings and argument vectors prior to subprocess invocation:
  - **Git Safety**: Blocks `git reset --hard`, `git push --force`, `git push -f`, `git branch -D main|master`.
  - **Filesystem Safety**: Blocks `rm -rf /`, `rm -rf ~`, `rm -rf *`, `mkfs.*`, `dd of=/dev/`.
  - **System Safety**: Blocks `reboot`, `shutdown`, `poweroff`, fork bombs.
  - **Database Safety**: Blocks raw `DROP DATABASE` or `DROP TABLE` outside migration harnesses.

### 3. Scope-Bound Mutation Enforcement (Task 9.3)
- Phase ② (Build Implement) file mutations are strictly bounded by `MutationScope`.
- Any edit attempting:
  - Directory traversal (`../`, absolute paths escaping the worktree root)
  - Symlink escapes pointing outside the repository tree
  - Modification of sensitive repository assets (`.git/`, `.env*`, `id_rsa`, `secrets.json`)
  - Modification of files outside declared `spec.md` work item paths
  is blocked with a `ScopeViolation` before staging.

### 4. Untrusted Prompt Defense & Delimiter Shielding (Task 9.4)
- User seed prompts, interview answers, issue descriptions, and third-party inputs are framed using `PromptShield`:
  - Strips non-printable ASCII control codes and ANSI escape sequences.
  - Generates unique cryptographic nonces per interaction (`<{label}_{nonce}>...<{label}_{nonce}>`).
  - Neutralizes XML/tag delimiter breakouts (`</...` escaping).
  - Prepends explicit security directives instructing models to treat framed inputs strictly as data.
  - Audits for common injection heuristics (`is_suspicious_injection`).

### 5. Secret Redaction & Environment Hygiene
- Subprocess execution strips sensitive git and shell environment variables (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, etc.) using `CleanGitEnvSubprocessExecutor`.
- All ledger and telemetry records run through redaction masks (`redact.py`) to prevent leakage of credentials, tokens, or private keys.

### 6. Webhook Payload Integrity
- External notifications dispatched via `WebhookPublisher` are signed with HMAC-SHA256 signatures (`X-Vibey-Signature: sha256=...`) and validated against URL scheme restrictions.

---

## Reporting a Vulnerability

If you discover a security vulnerability in Vibey, please report it responsibly:

1. **Do NOT open a public issue.**
2. Send a detailed report to the security team or repository maintainers.
3. Include reproducible steps, affected versions, and potential impact.
4. We will acknowledge receipt within 48 hours and coordinate remediation before public disclosure.
