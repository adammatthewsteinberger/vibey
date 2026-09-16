# CLI reference

All commands return zero on success and a nonzero status on validation, policy, or
transport failure. Run `vibey-gh COMMAND --help` for argparse's generated reference.

| Command | Arguments and options | Behavior |
|---|---|---|
| `check` | `--apply`, `--commits RANGE`, `--quiet`, `--ci` | Verify assets, fingerprints, documentation, provenance, that every `scan_workflows` entry present in `.github/workflows/` can fire for a pull request, and optionally a commit range. `--apply` adds missing headers and collapses a header duplicated within a file; `--ci` skips the local hooks-path check. |
| `install` | none | Render configured workflows, install/chains hooks, and install release-site assets. |
| `version` | `--since REF` (default `origin/main`), `--dev BUILD`, `--apply`, `--explain`, `--config PATH` | Derive, explain, or write the semantic version. `--config` derives against an alternate configuration — a second distribution the same repository publishes — without moving the root: a monorepo holds several version lines, and one `.vibey-gh.toml` holds one. The paths inside an alternate config stay repository-root-relative, because the deriver reads them with `git show <rev>:<path>`, which resolves only from the top of the tree. |
| `trailer` / `trailer-key` | none | Print the configured provenance trailer or only its key. |
| `conventional-message` | `--file COMMIT_EDITMSG` or stdin | Normalize the first line without changing the remaining bytes. This git-hook helper is intentionally CLI-only because it edits a local file or stdin. |
| `conventional-check` | required `--commits BASE..HEAD` | Audit every subject in an explicit revision range. This local/CI git helper is intentionally CLI-only, not a remote automation capability. |
| `merge-train` | `--method squash\|rebase\|merge`, `--pr N`, `--dry-run`, `--label LABEL`, `--summary FILE` | Revalidate and merge one or all policy-ready exact heads. |
| `pr-automation evaluate` | required `--pr N --head-sha SHA` | Classify one exact PR head and emit stable JSON. |
| `pr-automation ready-draft` | required `--pr N --head-sha SHA` | Convert a stable exact draft head to ready-for-review. |
| `pr-automation record-review` | required `--pr N --input JSON\|FILE\|-` | Persist a structured exact-head review. Use `-` for large stdin payloads. |
| `pr-automation record-repair` | required `--pr N --input JSON\|FILE\|-` | Persist a structured repair attempt. |
| `pr-automation mirror-fork` | required `--pr N` | Create a linked repository-owned replacement when a fork needs edits. |
| `pr-automation ensure-labels` | none | Create or reconcile all managed labels idempotently. |
| `issue-automation evaluate` | required `--issue N` | Classify one issue and emit stable JSON, including the derived solution branch and a Conventional Commit `pr_title`. |
| `issue-automation context` | required `--issue N`; optional `--output FILE`, `--max-bytes N` | Render one issue as a bounded, explicitly untrusted briefing. Writes to stdout when `--output` is omitted; parent directories are created. |
| `issue-automation record-solution` | required `--issue N --input JSON\|FILE\|-` | Persist a structured solution attempt against the issue's content lineage. |
| `issue-automation list-eligible` | none | Emit the JSON array of open issues a recovery sweep should dispatch. |
| `issue-automation ensure-labels` | none | Create or reconcile the issue automation labels idempotently. |
| `github-release` | required `--target SHA`; optional `--version VERSION` | Create or reuse an immutable tag and GitHub Release. |
| `promote` | `--method rebase\|squash\|merge`, `--dry-run`, `--wait` or `--no-wait`, `--summary FILE` | Open/reuse the integration-to-release PR. Event-driven `--no-wait` is the default. |
| `realign` | none | Bring the integration branch forward after release without rewriting it. |
| `report-superseded` | required `--index pypi\|testpypi --project NAME --version VERSION`; optional `--governance-since REF` | Report which prior releases on the index the given version supersedes. PyPI exposes no yank API, so this prints the release list and the management URL for a human to act on; it never yanks anything itself. With `--governance-since`, the release range is checked against `[yank] governance_paths`: a RATIFIED governance change (Article V.4) names every previous release, overriding `keep` and the per-index switches — zero exceptions; an unreadable ref is reported loudly, never silently waived. |
| `paper` | required `--author NAME`; optional `--source docs/paper.md`, `--output paper/paper.tex`, `--journal`, `--keywords` | Render the repository's research paper (docs/paper.md, markdown with LaTeX math inline) as an IEEEtran-class document — conference two-column by default, `--journal` for the journal layout. `$...$`, `$$...$$`, and ```latex fences pass through untouched; prose is escaped; `## References` becomes `thebibliography`. The LaTeX-to-PDF compile belongs to the workflow (TeX Live/tectonic), keeping the package dependency-free. |
| `book` | required `--site-dir DIR --title T --author A`; optional `--config-file properdocs.yml`, `--output-dir book`, `--subtitle`, `--publisher`, `--description`, `--language` | Export the built docs site as a book: a valid EPUB 3.0 (Dublin Core metadata, chapters spined in nav order) and a KDP print-ready HTML (6in x 9in trim, 11pt serif) that a headless-Chromium print-to-PDF turns into a paperback interior. Chapters come from the nav, so the doctrine order carries into the book. Stdlib only; the PDF step lives in the workflow, not the package. |
| `local-authority` | optional `--repos PATH...` or `--root ~/git`, `--interval 120`, `--once`, `--protected a,b`, `--no-check` | The capped-lane sync loop (#206): every pass, any clean, provenance-green local branch ahead of its upstream is pushed with an explicit pre-fetch `--force-with-lease`, so remote tracks local in near-realtime while local is the source of truth. Permanent branches (each repo's own integration/release names by default) are never touched; dirty trees and check-failing branches are held; unseen remote work always refuses the push. Discovery scans `--root` for work trees carrying `.vibey-gh.toml` — the opt-in marker. Safe to leave running in healthy periods: nothing-ahead is a no-op. |
| `failover` | optional `--config PATH` (default `~/.config/vibey-gh/failover.toml`), `--state PATH`, `--once` | The operator-seat failover engine (#208): when the paid lane's probe stops answering, the seat moves to the first healthy local agent (qwenloop, then opencode, by default) and moves back the moment the probe succeeds — the paid lane always leads. Machine-level config, off until the operator enables it; every probe, launch, and health check is an operator-supplied command judged by exit status. Lossless: seats share the working tree and `local-authority` keeps both fronts synced throughout. |
| `tidy` | optional `--apply`, `--ci` | The clean repo (sub-doctrine 9.a): surveys every technical-clutter class a forge and a clone accumulate — merged-and-undeleted remote branches, merged and gone-upstream locals, prunable worktrees, draft releases, orphan tags — and with `--apply` removes exactly the provably-lossless classes (two proofs: ancestry for merge-commit flows, the forge's own deletion-at-merge event for squash/rebase flows via `trust_forge_deletions`). Drafts, orphan tags, stashes, and untracked files are reported for the human, never machine-removed; human messiness is expressly welcome and untouched. `--ci` limits judgment to the cloud classes. |
| `local-review` | `--diff FILE` or stdin; optional `--model`, `--base-url`, `--max-chars`, `--timeout` (default from `[pr_automation.fallback]`) | Review a diff with a local Ollama-compatible model when the primary paid review returned no verdict at all. Reports only `pass`, `summary`, and `findings`; never executes repository code. |
| `doctor` | none | Offline adoption preflight: reads `.vibey-gh.toml`, `pyproject.toml`, and `.github/workflows/` to catch a config key silently landing in the wrong section, `pr_automation.enabled` with no installed gate workflow (a merge train stuck forever), a ruff `E501` select that conflicts with the provenance header width, two workflows contending over GitHub Pages, and files still carrying a superseded fingerprint header. No network, no credentials, no execution; exits nonzero only on error-level findings. |
| `marketplace` | optional `--check` | Render `.claude-plugin/marketplace.json` at the repository root from the `[marketplace] members` — every plugin from every member, its `./` source re-rooted to the repository, under the root's own `[marketplace] name` — so `/plugin marketplace add owner/repo` finds one manifest for the whole monorepo. Deterministic bytes; `--check` fails loudly when the file on disk is not what the members render to, and `check` runs the same comparison whenever members are declared. A member manifest that is missing, unreadable, ownerless, empty, escapes its member with `..`, or declares a plugin name another member already declares is a named error, never a silent drop. |
| `local-triage` | `--issue FILE` or stdin; optional `--model`, `--base-url`, `--max-chars`, `--timeout` | Triage an issue with the same local model when the primary paid solver produced nothing. Always forces `needs_human: true`; writes no code and opens no branch. |
| `pr-automation self-heal` | `--pr N` optional | Refill a spent repair budget, itself bounded by `branch_sync.max_self_heals`. Omit `--pr` to sweep every exhausted pull request. |
| `conversation evaluate` | required `--subject N`; optional `--comment-id ID` | Decide whether one comment gets a response, and how far it may reach. |
| `conversation context` | required `--subject N`; optional `--comment-id ID`, `--output FILE`, `--max-bytes N` | Render the thread as a bounded, explicitly untrusted briefing. |
| `conversation reply` | required `--subject N --body TEXT\|FILE\|-` | Post an answer. A trusted step calls this; the model never gets the tool. |
| `conversation record-response` | required `--subject N --input JSON\|FILE\|-` | Persist one interaction against the thread's budget. |
| `reconcile-branches` | `--dry-run` | Rebase, close, or leave each open pull-request branch stranded by a realign rewrite. `--dry-run` decides without mutating anything. Realign calls this itself; the command exists for recovery and inspection. |
| `rulesets` | `--dry-run` | Reconcile the integration and release branch rulesets declared by `[rulesets]`. `--dry-run` reports drift without creating or updating anything. `repository-profile.yml` calls this itself; the command exists for recovery and inspection. |
| `api`, `mcp`, `sdk` | `CAPABILITY`, `--arguments JSON_ARRAY` | Invoke a canonical capability through that adapter. |
| `webhook` | `CAPABILITY`, `--arguments JSON_ARRAY`, required `--delivery ID` | Sign and dispatch locally using `VIBEY_GH_WEBHOOK_SECRET`; claims persist by default. |

`VIBEY_GH_WEBHOOK_STATE_DIR` overrides the default
`.vibey-gh/webhook-deliveries` store. The CLI atomically creates a mode-0600 SHA-256 marker
for every accepted delivery ID in a mode-0700 directory, so rejection survives restarts
and concurrent invocations. Put it on durable storage when the CLI receives webhooks.

## Library and server adapters

SDK, API, MCP, and webhook implementations are dependency-free application callables, not
bundled network daemons. Adopters own TLS, authentication, process management, rate limits,
and request-size limits in their chosen server framework.

```python
from vibey_gh.surfaces import api_dispatch, mcp_dispatch

status, response = api_dispatch("POST", "/v1/capabilities/check", b'{"arguments":["--ci"]}')
tools = mcp_dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
```

Map HTTP `POST /v1/capabilities/{name}` to `api_dispatch` and MCP JSON-RPC objects to
`mcp_dispatch`. For an inbound webhook, retain the sender's raw bytes and signature:

```python
from pathlib import Path
from vibey_gh.surfaces import WebhookDispatcher

webhooks = WebhookDispatcher(secret, delivery_dir=Path("/var/lib/vibey-gh/deliveries"))
status, response = webhooks.dispatch(delivery_id, signature_header, raw_body)
```

Never put the secret in arguments or logs. The convenience CLI computes its signature for
integration and smoke testing; an HTTP adapter must forward and verify the sender's HMAC.
