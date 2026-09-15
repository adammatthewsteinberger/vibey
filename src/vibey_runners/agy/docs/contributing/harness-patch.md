# Reproducing the localharness input-detection patch

The Antigravity SDK (`google-antigravity`, Apache-2.0) ships a Go
`localharness` binary. Input detection in `run_command_handler.go` names
`models/gemini-2.5-flash-lite`, which Google has withdrawn for new users.
Python `LocalAgentConfig` has no public `INPUT_DETECTION` model type.

## `strings` notes (installed wheel)

Hits in `google/antigravity/bin/localharness`:

- Literal `gemini-2.5-flash-lite` (21 bytes, once)
- `error during input detection model call: %v`
- Enum `MODEL_GOOGLE_GEMINI_2_5_FLASH_LITE`
- No env var such as `INPUT_DETECTION_MODEL`

Resolution order (`_get_default_binary_path_external`):

1. `ANTIGRAVITY_HARNESS_PATH`
2. wheel `google/antigravity/bin/localharness`
3. `importlib.resources`
4. `PATH`

## Runtime copy-patch (A0b)

`gemini-flash-lite-latest` is 24 bytes and will not fit. agyloop replaces the
21-byte withdrawn id with `gemini-3.5-flash-lite` (same length; the live id
behind the low-preset alias) in a **copy** under
`~/.cache/agyloop/localharness` (or `AGYLOOP_HARNESS_CACHE`). The stock
site-packages file is left alone unless later layers run.

```bash
# Disable the copy; use the SDK binary as shipped
export ANTIGRAVITY_HARNESS_PATH=/path/to/venv/lib/python3.12/site-packages/google/antigravity/bin/localharness
```

## If upstream publishes Go source

The Python SDK is Apache-2.0. If Google publishes `run_command_handler.go`,
change the hardcoded id to `gemini-flash-lite-latest` (or
`INPUT_DETECTION_MODEL`), rebuild for the host OS, keep NOTICE/LICENSE
attribution, and point `ANTIGRAVITY_HARNESS_PATH` at the rebuild.

## Site-packages overwrite

Last filesystem resort. Backup is `localharness.agyloop-bak` next to the
original. Restore:

```bash
agyloop doctor repair-harness
```

`AGYLOOP_NO_SITE_PACKAGES_PATCH=1` skips this layer.

## Localhost rewrite proxy

Only if the binary still calls the withdrawn id. Loopback only. Rewrite only
that model id. No API-key logging. No system CA unless
`AGYLOOP_INSTALL_REWRITE_CA=1`. Disable with `AGYLOOP_GEMINI_REWRITE_PROXY=0`.
