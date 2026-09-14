# Security

Repository-root [SECURITY.md](https://github.com/adammatthewsteinberger/agyloop/blob/main/SECURITY.md)
is the reporting policy. Operator notes:

- Never `shell=True`. The CLI gateway builds argv lists.
- Default `--gateway cli` is `--sandbox` plus proceed-in-sandbox / deny unsandboxed.
- `--unsafe-skip-permissions` maps to `agy --dangerously-skip-permissions`, which
  defeats `--sandbox` ([antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36)).
  Refused as root, refused with sandbox, refused outside git unless allowlisted.
  Refused entirely on `--gateway sdk`.
- Snapshots redact `api_key` / `authorization` / `GOOGLE_API_KEY` / ADC-shaped
  fields.
- Generated REST (`agyloop api`) sends `GOOGLE_API_KEY` as a query parameter
  to Google's Developer endpoint. Treat that key as secret.
- Input-detection retarget may copy-patch Apache-2.0 `localharness`. The
  optional rewrite proxy is loopback-only and does not install a system CA
  unless `AGYLOOP_INSTALL_REWRITE_CA=1`.
