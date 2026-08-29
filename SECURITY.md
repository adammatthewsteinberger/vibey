# Security Policy

## Overview

Vibey is a queue-based conductor for autonomous software delivery. Because Vibey orchestrates autonomous engines, tools, code mutation, and optional deployment pipelines, isolation and defense-in-depth are foundational architectural requirements (see ADR-0008, ADR-0012, ADR-0013, ADR-0014).

---

## Threat Model & Security Boundaries

### 1. Worktree Isolation Runtime (ADR-0008, Task 9.1)
- **Worktree Sandboxing**: Every job and phase executes inside an isolated ephemeral git worktree branched from base or integration heads. This is wired through `bootstrap.py` via `GitWorktreeManager` and is active today.
- **OCI Container Hardening — designed, not yet wired**: `infrastructure/container/` (`OciContainerExecutor`, `ContainerConfig`) implements read-only root filesystem, dropped capabilities (`--cap-drop=ALL`), `--security-opt=no-new-privileges:true`, a restricted `/tmp` tmpfs, memory/CPU caps, and `--network=none` by default. These are unit-tested but **not currently invoked from `bootstrap.py` or any job/phase dispatch path** — no engine subprocess today actually runs inside one of these hardened containers. Treat this as a designed-and-tested primitive awaiting integration, not an active runtime control.

### 2. Destructive-Command Prevention (Task 9.2) — designed, not yet wired
- `domain/command_guard.py` defines `CommandSecurityPolicy`/`scan_command`, which can block `git reset --hard`, `git push --force`/`-f`, `git branch -D main|master`, `rm -rf /`/`~`/`*`, `mkfs.*`, `dd of=/dev/`, `reboot`/`shutdown`/`poweroff`, fork bombs, and raw `DROP DATABASE`/`DROP TABLE` outside migration harnesses.
- **This policy is unit-tested but not called from any subprocess invocation path** (verified: no import outside `domain/command_guard.py` and its tests; `bootstrap.py` never references it). Autonomous engines are **not currently prevented** by vibey from issuing destructive commands — any protection today comes from the underlying engine runner (`claudeloop`, etc.), not from vibey.

### 3. Scope-Bound Mutation Enforcement (Task 9.3) — designed, not yet wired
- `domain/scope_guard.py` defines `MutationScope`, which can reject directory traversal, symlink escapes, edits to sensitive repository assets (`.git/`, `.env*`, `id_rsa`, `secrets.json`), and edits outside a declared `spec.md` work item path, raising `ScopeViolation`.
- **This guard is unit-tested but not called from the Phase ② (Build Implement) mutation path or anywhere else in `application/`/`infrastructure/`.** Phase ② file mutations are not currently scope-checked by vibey itself.

### 4. Untrusted Prompt Defense & Delimiter Shielding (Task 9.4) — designed, not yet wired
- `domain/prompt_shield.py` defines `PromptShield`, which can strip non-printable/ANSI control codes, generate per-interaction nonces (`<{label}_{nonce}>...<{label}_{nonce}>`), neutralize tag-delimiter breakouts, prepend directives instructing models to treat framed input as data, and flag suspicious injection heuristics (`is_suspicious_injection`).
- **This is unit-tested but not called from `seed_prompt.py` or any other prompt-construction path.** User seed prompts, interview answers, issue descriptions, and other untrusted inputs are **not currently framed** through `PromptShield` before reaching an engine.

### 5. Secret Redaction & Environment Hygiene
- Subprocess execution strips sensitive git and shell environment variables (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, etc.) using `CleanGitEnvSubprocessExecutor`.
- All ledger and telemetry records run through redaction masks (`redact.py`) to prevent leakage of credentials, tokens, or private keys.

### 6. Webhook Payload Integrity — designed, not yet wired
- `infrastructure/notify/service.py` (`NotificationService`) and `infrastructure/notify/webhook.py` (`WebhookPublisher`) implement HMAC-SHA256 request signing (`X-Vibey-Signature: sha256=...`) and validation against URL scheme restrictions for outbound webhook notifications.
- **This is unit-tested but not imported or instantiated from `bootstrap.py` or any gate-raised, phase-change, or budget-event dispatch path** (verified: no reference to `infrastructure/notify/` outside its own module and tests). No webhook — signed or otherwise — is sent by vibey today; treat this as a designed-and-tested primitive awaiting integration, not an active runtime control, and do not rely on it for out-of-band visibility into a run.

---

## Reporting a Vulnerability

If you discover a security vulnerability in Vibey, please report it responsibly:

1. **Do NOT open a public issue.**
2. Use [GitHub Security Advisories](https://github.com/adammatthewsteinberger/vibey/security/advisories/new) to send a private report to the repository maintainers.
3. Include reproducible steps, affected versions, and potential impact.
4. We will acknowledge receipt within 48 hours and coordinate remediation before public disclosure.
