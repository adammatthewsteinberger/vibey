# Security policy

## Why this matters more than usual for this project

`agyloop` drives Google Antigravity / Gemini **unattended**, often across
quota windows that last hours. That means it:

- Grants tool autonomy by default via SDK policies (`policy.allow_all()`
  plus `workspace_only()` and destructive-command denies). `--yolo` drops
  those scopes. A misconfigured run has more latitude than an interactive
  IDE session.
- Reads Google credentials (`GOOGLE_API_KEY` or Application Default
  Credentials) and must not log them.
- Never blocks on a human. Clarifying questions (`ask_question`) are
  **denied with guidance** so the model proceeds on a stated assumption —
  they are never auto-answered and never wait on stdin.
- May, on the optional `agy` CLI adapter path, run with a sandbox. Combining
  that sandbox with skip-permissions is a documented upstream footgun.

Treat any report touching these areas as high priority.

## Sandbox + skip-permissions footgun (antigravity-cli #36)

Upstream issue:
[google-antigravity/antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36).

`agy --sandbox --dangerously-skip-permissions` auto-approves the
sandbox-bypass prompt (`bypassSandbox` / `unsandboxed`). The sandbox then
does nothing. agyloop's controls:

1. **SDK path (default).** Autonomy is `policy.allow_all()` with
   `workspace_only()` and destructive-command denies. agyloop never passes
   `--dangerously-skip-permissions` on this path. `--yolo` is the explicit
   way to drop workspace/destructive scopes. `agyloop run --unsafe-skip-permissions`
   is **refused** (fail closed): that flag is for `build_agy_argv`, not the
   SDK gateway. The refusal prints the #36 footgun warning.
2. **CLI adapter argv.** Default invocation is `--sandbox` with settings
   `toolPermission = "proceed-in-sandbox"` and
   `permissions.deny = ["unsandboxed"]`. The argv builder **refuses to emit**
   `--dangerously-skip-permissions` together with `--sandbox`.
3. **`--unsafe-skip-permissions` opt-in** (maps to
   `--dangerously-skip-permissions` on the CLI adapter argv builder only;
   not honored by `agyloop run`):
   - refuses to combine with `--sandbox` (does not silently neuter it)
   - refuses to run as root (`euid == 0`)
   - refuses to run outside a git repository unless the cwd is allowlisted
     (`AGYLOOP_UNSAFE_SKIP_ALLOWLIST`)
   - emits a WARNING naming the risk and citing issue #36

`--print-timeout` is always raised explicitly; the CLI default of 5 minutes
is too short for an autonomous turn.

## Harness input-detection retarget

The Antigravity Go `localharness` hardcodes `gemini-2.5-flash-lite` for
input detection. agyloop may copy-patch that binary (Apache-2.0) into
`~/.cache/agyloop/localharness` and set `ANTIGRAVITY_HARNESS_PATH`. A
site-packages overwrite always writes a `.agyloop-bak` first and restores on
`agyloop doctor repair-harness` or process exit when agyloop created the
backup. `AGYLOOP_NO_SITE_PACKAGES_PATCH=1` disables that layer.

The optional localhost Gemini rewrite proxy (`AGYLOOP_GEMINI_REWRITE_PROXY`)
listens on loopback only and rewrites only the withdrawn model id. It does
**not** intercept other hosts or other users' traffic. It does **not**
install a system-wide CA unless you pass `AGYLOOP_INSTALL_REWRITE_CA=1`.

## Never block on a human

Interactive hooks (`ToolConfirmationHook`, `AskQuestionHook`) are never
registered. `ask_question` is denied with guidance. Operator control
(`agyloop stop`, `agyloop prompt --now|--at-break`) writes the run inbox;
it does not wait on stdin. `agyloop doctor` fails if interactive hooks are
injected.

## Supported versions

Only the latest released version on PyPI receives security fixes. This
project is pre-1.0; there is no long-term-support branch.

## Reporting a vulnerability

**Do not open a public GitHub issue for a security vulnerability.**

Report privately via one of:

1. [GitHub Security Advisories](https://github.com/adammatthewsteinberger/agyloop/security/advisories/new)
   for this repository (preferred — supports coordinated disclosure).
2. Email **adam@matthewsteinberger.com** with a clear description, steps to
   reproduce, and the version affected.

## What to expect

- **Acknowledgment** within 5 business days.
- **An initial assessment** (severity, affected versions) within 10
  business days.
- **Coordinated disclosure**: a fix is prepared and released before public
  details are shared, unless the reporter and maintainer agree on a
  different timeline.

## Threat model, briefly

**In scope:**

- Any way agyloop could be induced to bypass "never block on a human" in a
  way that causes *harmful* unattended action (as opposed to simply
  failing).
- Credential handling — logging or storage of `GOOGLE_API_KEY`, ADC JSON,
  bearer tokens, or `application_default_credentials.json` contents.
- Path traversal or command injection from a plan file or CLI arguments.
  Design goal: no `shell=True` anywhere.
- Emitting `--dangerously-skip-permissions` together with `--sandbox`, or
  honoring `--unsafe-skip-permissions` as root / outside git.

**Out of scope:**

- Vulnerabilities in `google-antigravity`, the `agy` CLI, or Gemini APIs —
  report those to Google.
- Issues requiring an attacker to already have arbitrary code execution on
  the machine running agyloop.
- Quota / billing exhaustion on your own Google project — that's an
  account concern, not a vulnerability in this tool.
- The generated `agyloop api` REST surface (see ADR 0015); treat
  `GOOGLE_API_KEY` as secret. Vertex lane is not inventoried.
