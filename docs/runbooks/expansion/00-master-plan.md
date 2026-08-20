# Expansion master plan

Sixteen workstreams that take vibey from "conducts four session runners on
one MacBook" to a multi-cloud, multi-surface, self-maintaining delivery
platform — **built by vibey itself**. This document sequences them; each
numbered runbook in this directory is a self-contained execution plan
written to be consumed as a vibey DESIGN-phase seed.

## The dogfooding protocol (applies to every workstream)

Every workstream ships through vibey's own queue, not through ad-hoc
sessions:

1. `vibey new <workstream> --repo ~/git/vibey --max-cycle-dollars <cap>`
   (or the target repo for loop-runner work). Budget caps are real now —
   the brake reads TurnCompleted `cost_usd` (PR #58).
2. Seed DESIGN with the workstream's runbook file as the interview input;
   answer routine gates with `vibey answer <gate> --defaults`.
3. BUILD runs unattended on the engine pool (`-j 2+`). Repair rounds are
   bounded and self-terminating (PR #59); parks advertise their grant
   contracts (`--raw '{"max_rounds": N}'`, `{"max_dollars": N}`,
   `{"max_attempts": N}`).
4. REVIEW demos to the operator; deployment stage set only on explicit
   opt-in.
5. A workstream is DONE when its runbook's **Verification** section passes
   with evidence (test output, live-tenant resource IDs, store listing
   URLs, published package versions).

House rules that no workstream may violate: onion architecture
(import-linter), 100% branch coverage per layer, Conventional Commits,
never implement on `main`, ledger append-only, `CreditsExhausted` never
gets `resets_at`, never block a worker on a human.

## Sequencing

```
Phase A — foundation (unblocks everything else)
  13-cost-performance      # cheaper/faster loops = cheaper dogfooding
  06-engine-live-confirmation  # more live engines = more parallel capacity
Phase B — scale-out
  05-server-mode-kubernetes    # minikube/helm/keda/kopf + AKS/EKS/GKE
Phase C — integration surfaces
  12-integration-surfaces      # MCP/API/webhooks/skills/SDKs, all repos
  01-jira-integration          # rides on 12's webhook + API plumbing
  02-copilotloop               # fifth engine
Phase D — clouds
  03-multicloud-aws-gcp        # AWS + GCP adapters, live-verified + Azure live
Phase E — products
  08-clients                   # RN mobile, Next.js web, desktop, TUI logs
  07-store-submissions         # App Store / Play Store
  09-package-managers          # pip/brew/apt/yum/npm/...
  10-keep-awake                # desktop no-sleep contract
  15-agent-surface-sync        # one customization set across every IDE/bot
                               # (standalone — can start any time)
Phase F — ecosystem
  04-docs-scraper              # integration docs drift watcher
  11-openclaw-moltbook         # OpenClaw AgentSkill + Moltbook presence
  14-social-engagement         # all five repos
```

Phases are dependency-ordered; workstreams inside a phase can run as
parallel vibey projects when engine capacity allows.

## What each workstream needs from the operator (collected)

| Workstream | Needs before live verification |
|---|---|
| 06 engines | `CURSOR_API_KEY`; a codexloop session to capture real `events.jsonl` output; Copilot CLI installed + `gh auth` for 02 |
| 03 clouds | `az login` + subscription; AWS free-tier account + access key; GCP free-tier project + service-account JSON |
| 05 k8s | Docker Desktop or colima; minikube; (cloud phases reuse 03's tenants) |
| 07 stores | Apple Developer account + App Store Connect API key; Google Play Console account + service account |
| 01 jira | A Jira Cloud site (free tier) + API token / OAuth app |
| 11 openclaw | An OpenClaw install; Moltbook agent registration (claim tweet is a human step) |
| 09 packages | PyPI token; npm token; Homebrew tap repo; optionally packagecloud/OBS accounts for apt/yum |
| 15 surface sync | Nothing to start; a private git remote for the store if multi-machine sync is wanted |

Everything else runs on what the MacBook already has.

## Cross-cutting acceptance bar

- Every new adapter sits behind a Protocol in `application/interfaces/`;
  `domain/` stays pure; `bootstrap.py` stays the sole composition root.
- Every live integration ships with (a) fixture-level tests at the
  subprocess/HTTP boundary and (b) a `tests/live/` opt-in test that runs
  against the real service, gated on env credentials being present.
- Every workstream updates the four agent-surface trees
  (`.claude/skills/`, `.cursor/rules/`, `.agents/skills/`,
  `.agent/rules/`) in the same PR when it changes a procedure.
- Findings discovered mid-build follow the repair-ticket protocol:
  raised → repaired → resolved-on-completion → re-verified (PR #59).
