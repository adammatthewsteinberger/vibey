# Configuration

## Auth lanes

Set **one** lane. `agyloop doctor` reports what it can prove.

**Developer API**

```bash
export GOOGLE_API_KEY=...   # or GEMINI_API_KEY — same Developer lane
agyloop doctor
```

**Enterprise / Vertex (ADC)**

```bash
export GOOGLE_GENAI_USE_VERTEXAI=1   # or GOOGLE_GENAI_USE_ENTERPRISE=1
agyloop doctor
```

If `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) and a Vertex flag are both set, doctor
reports a conflict, fails the auth check, and does not pick a lane. The SDK
path forwards the Developer key into `LocalAgentConfig(api_key=...)` so
`GOOGLE_API_KEY` alone is enough.

## `agyloop.toml`

Precedence: CLI flags > `AGYLOOP_*` environment variables >
`./agyloop.toml` > `~/.config/agyloop/config.toml` > built-in defaults.

```toml
[run]
max_turns = 40
max_dollars = 5.0          # labeled estimate (ADR 0009)
gateway = "sdk"
ramp = 0

[model]
low = "gemini-flash-lite-latest"
medium = "gemini-2.5-flash"
high = "gemini-2.5-pro"
```

`agyloop config` prints the effective table. `--preset low|medium|high` selects
both model and default effort. `--max-dollars` stops the run when the labeled
USD estimate reaches the cap.

## Environment

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Developer API key (preferred) |
| `GEMINI_API_KEY` | Same Developer lane if `GOOGLE_API_KEY` is unset |
| `GOOGLE_ACCESS_TOKEN` / `CLOUDSDK_AUTH_ACCESS_TOKEN` | Bearer token for `agyloop api --lane vertex` |
| `GOOGLE_GENAI_USE_VERTEXAI` / `GOOGLE_GENAI_USE_ENTERPRISE` | Select Vertex lane for doctor / SDK |
| `GOOGLE_APPLICATION_CREDENTIALS` | ADC JSON path |
| `AGYLOOP_MAX_TURNS` / `AGYLOOP_MAX_DOLLARS` / `AGYLOOP_MODEL_LOW` … | Override toml keys |
| `AGYLOOP_UNSAFE_SKIP_ALLOWLIST` | Directories allowed with `--unsafe-skip-permissions` outside git |
| `AGYLOOP_AGY_SETTINGS` / `AGYLOOP_AGY_SETTINGS_FILE` | Written for `--gateway cli` sandbox settings |
| `ANTIGRAVITY_HARNESS_PATH` | Operator override for the Antigravity `localharness` binary. agyloop does not clobber a pre-set path. |
| `AGYLOOP_HARNESS_CACHE` | Directory for a patched `localharness` copy (default `~/.cache/agyloop/localharness`) |
| `AGYLOOP_NO_SITE_PACKAGES_PATCH=1` | Never overwrite `google-antigravity`'s bundled binary |
| `AGYLOOP_GEMINI_REWRITE_PROXY=0` | Disable the localhost Gemini model-id rewrite proxy |
| `AGYLOOP_INSTALL_REWRITE_CA=1` | Explicit opt-in to install the rewrite-proxy CA (never silent) |
| `AGYLOOP_SKIP_HARNESS_RETARGET=1` | Skip binary patch / monkeypatch / proxy (tests) |

State lives under `.agyloop/` in the working directory. `agyloop reset --yes`
deletes that tree only (refuses while a run PID is live).

## Input-detection model retarget

`--preset low` already uses `gemini-flash-lite-latest`. Antigravity's Go
`localharness` still hardcodes `models/gemini-2.5-flash-lite` for **input
detection** (a sidecar call on `run_command`). Google has withdrawn that id
for new users, which 404s and used to look like an empty Available turn.

agyloop retargets that sidecar, in order:

1. **SDK config.** `LocalAgentConfig.env` carries
   `AGYLOOP_INPUT_DETECTION_MODEL=gemini-flash-lite-latest`, and an extra
   TEXT `ModelTarget` with that alias is appended after the operator's chat
   model.
2. **Patched harness copy.** If the bundled binary still contains
   `gemini-2.5-flash-lite`, agyloop copies it to the cache and same-length
   patches the Go string to `gemini-3.5-flash-lite` (the live id behind the
   alias). `ANTIGRAVITY_HARNESS_PATH` points at the copy unless you already
   set that variable.
3. **Fallbacks.** Monkeypatch the SDK path helper; last-resort site-packages
   overwrite with a `.agyloop-bak` backup (`agyloop doctor repair-harness`
   restores it); localhost-only HTTPS rewrite proxy that replaces only that
   model id. The proxy listens on loopback, does not log API keys, and does
   not install a system CA unless `AGYLOOP_INSTALL_REWRITE_CA=1`.

The bundled `localharness` is Apache-2.0 (Google). A runtime copy-patch is a
modified work of that binary; see
[harness-patch](../contributing/harness-patch.md). Point
`ANTIGRAVITY_HARNESS_PATH` at the stock binary to disable the copy.

A 404 / `NOT_FOUND` / "no longer available to new users" exception, or an
**empty** successful drain with those markers in harness logs, raises
`AgentConfigError` and aborts. Non-empty assistant text plus leftover sidecar
404 noise is ignored. `run.exception` is emitted on the per-run event stream.

## Logging

`--verbose` / `--log-level` / `--log-file` on the root command. File logs are
JSON lines and pass through redaction. Per-run `events.jsonl` is a separate
sink under `.agyloop/runs/<id>/`.

## Gateway and permissions

`--gateway sdk` (default) uses `google-antigravity`. `--unsafe-skip-permissions`
is refused on this path.

`--gateway cli` runs `agy -p` with `--sandbox` and
`proceed-in-sandbox` / `deny: unsandboxed`. `--unsafe-skip-permissions` is
valid after refusing root, refusing `--sandbox`, and refusing a non-git cwd.
agyloop never emits skip-permissions together with `--sandbox`
([antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36)).

See [Security](../security.md).
