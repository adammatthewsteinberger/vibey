# Expansion master plan

> **Status (2026-09-15):** 21 workstreams. Landed: 05 on minikube, 13 Front 1,
> 19 (as a merged monorepo, not submodules). Partial: 09, 12, 14, 20.
> Open with no deliverable yet: 06, 16. Superseded: 02 (qwenloop became the fifth engine). The rest have not started.
> The family now lives in this repository as a uv workspace (ADR-0021); see the
> status ledger below.

Twenty-one workstreams that take vibey from "conducts five session runners on
one MacBook" to a multi-cloud, multi-surface, self-maintaining delivery
platform — **built by vibey itself**. This document sequences them; each
numbered runbook in this directory is a self-contained execution plan
written to be consumed as a vibey DESIGN-phase seed.

The runbooks were committed on 2026-08-20 and 2026-08-21, when the
runners, `vibey-gh`, `vibey-skills` and `vibey-bootstrap` were separate
GitHub repositories. They are now subtrees of this repository
(`src/vibey_runners/{claude,codex,cursor,agy,qwen,common}`,
`src/vibey_tools/{gh,skills,bootstrap}`), registered as a uv workspace
(ADR-0021). The sibling repositories no longer exist; their PyPI projects
do. Where a runbook still says "each repo", read "each workspace member".

## Status ledger (as of 2026-09-15)

| # | Workstream | Status | Evidence |
|---|---|---|---|
| 01 | Jira integration | Not started | No Jira code under `src/vibey` |
| 02 | copilotloop | Superseded | qwenloop is the fifth engine (ADR-0015, `src/vibey_runners/qwen`); copilotloop would be a sixth |
| 03 | AWS + GCP | Not started | `vibey worker --azure {memory,az}` is the only cloud flag; no `infrastructure/aws` or `infrastructure/gcp` |
| 04 | Docs scraper | Not started | No `docwatch` module, job kind or migration |
| 05 | Kubernetes | Landed on minikube | PRs #73, #74, #76 (2026-08-21); CI `Helm install on minikube` job. Open: engines in the image, cloud presets, `server` Deployment, AKS/EKS/GKE runs |
| 06 | Live engine confirmation | Open | claudeloop and agyloop live-proven; codexloop, cursorloop, qwenloop not |
| 07 | Store submissions | Not started | Blocked on 08 |
| 08 | Clients | Not started | Blocked on 12's HTTP API |
| 09 | Package managers | Partial | PyPI publishing via `release.yml`; ADR-0019 now governs channel order |
| 10 | Keep-awake | Not started | No `power` port or adapter |
| 11 | OpenClaw / Moltbook | Not started | Constrained by sub-doctrine 4.a |
| 12 | Integration surfaces | Partial | `vibey-gh` projects api/mcp/sdk/webhook (`vibey_gh/surfaces.py`); conductor has a signed outbound `WebhookPublisher` only |
| 13 | Cost & performance | Front 1 landed | PR #70 (2026-08-21); Front 1 items 5–6 and Front 2 open |
| 14 | Social engagement | Partial | Community files, badges, ProperDocs site, social-signals surface |
| 15 | Agent surface sync | Not started | Must build on in-tree `vibey-skills` (ADR-0017) |
| 16 | Runner containers | Open | Runners are workspace members; only qwenloop has a Dockerfile |
| 17 | Plan-drift reconciliation | Not started, unblocked | 05's operator + CRD landed (#76) |
| 18 | Production fitness | Not started | Waits on 17's machinery |
| 19 | Monorepo & shared libraries | Landed differently | Subtree imports (runners 2026-09-10, tools 2026-09-15) + uv workspace (ADR-0021); domain extraction open |
| 20 | PR reviewer | Partial | `vibey_gh` `merge_train`, `pr_automation`, `local_review` |
| 21 | Explorer | Not started | — |

House rule: every runbook carries a `> **Status (YYYY-MM-DD):** …` line
under its title. Update it in the PR that changes the facts.

## The dogfooding protocol (applies to every workstream)

Every workstream ships through vibey's own queue, not through ad-hoc
sessions:

1. `vibey new <workstream> --repo ~/git/vibey --max-cycle-dollars <cap>`.
   Runner and tool work targets the same repository: the runners and
   `vibey-gh`/`vibey-skills`/`vibey-bootstrap` are workspace members
   (ADR-0021). Budget caps are real now —
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
(import-linter), 100% branch coverage per layer (ADR-0023), Conventional Commits,
never implement on `main`, ledger append-only, a bounded repair ladder
parks with a grant rather than looping (ADR-0024), `CreditsExhausted` never
gets `resets_at`, never block a worker on a human.

## Sequencing

```
Phase A — foundation (unblocks everything else)
  13-cost-performance          # Front 1 LANDED (#70); items 5-6 + Front 2 open
  06-engine-live-confirmation  # open; includes qwenloop (fifth engine, ADR-0015)
Phase B — scale-out
  05-server-mode-kubernetes    # LANDED on minikube (#73/#74/#76, ADR-0025):
                               # image, chart, KEDA, kopf operator + CRD,
                               # doctor --cluster. Open: engines in the image,
                               # server Deployment, cloud presets, AKS/EKS/GKE
  16-loop-runner-containers    # open; runners are workspace members under
                               # src/vibey_runners/; feeds 05's engines image
Phase C — integration surfaces
  19-monorepo-and-shared-libraries
                               # LANDED DIFFERENTLY: subtree imports + uv
                               # workspace (ADR-0021), not submodules;
                               # domain extraction still open
  17-plan-drift-reconciliation # unblocked (05's operator landed); not started
  18-production-fitness-reconciliation
                               # sibling loop on the same rails: is what
                               # the jobs produced fit for production?
  12-integration-surfaces      # partial: vibey-gh ships api/mcp/sdk/webhook;
                               # conductor surfaces not started
  01-jira-integration          # rides on 12's webhook + API plumbing
  02-copilotloop               # SUPERSEDED: qwenloop is the fifth engine
Phase D — clouds
  03-multicloud-aws-gcp        # AWS + GCP adapters, live-verified + Azure live
Phase E — products
  20-vibey-pr-reviewer         # partial inside vibey-gh (merge_train,
                               # pr_automation); cross-account + stop list open
  21-vibey-explorer            # daily open-source discovery, build, and ship
  08-clients                   # RN mobile, Next.js web, desktop, TUI logs
  07-store-submissions         # App Store / Play Store
  09-package-managers          # PyPI done; remaining channels per ADR-0019
  10-keep-awake                # desktop no-sleep contract
  15-agent-surface-sync        # one customization set across every IDE/bot
                               # (standalone — can start any time)
Phase F — ecosystem
  04-docs-scraper              # integration docs drift watcher
  11-openclaw-moltbook         # OpenClaw AgentSkill + Moltbook presence
  14-social-engagement         # partial; one repository now
```

Phases are dependency-ordered; workstreams inside a phase can run as
parallel vibey projects when engine capacity allows.

## What each workstream needs from the operator (collected)

| Workstream | Needs before live verification |
|---|---|
| 06 engines | `CURSOR_API_KEY`; a codexloop session to capture real `events.jsonl` output; for qwenloop, local model weights (llama.cpp or vLLM backend) and `[features] qwenloop = true` |
| 03 clouds | `az login` + subscription; AWS free-tier account + access key; GCP free-tier project + service-account JSON |
| 05 k8s | The minikube path already runs in CI (`Helm install on minikube`). Remaining: 03's cloud tenants for AKS/EKS/GKE; LLM API keys for API-key engine mode |
| 16 runner containers | A registry namespace + `packages:write` token; the same LLM API keys as 05; deploy keys for private target repos |
| 17 drift reconciliation | Nothing new — rides on 05's operator and 16's containers; needs a decision on the production `driftPolicy` ceiling |
| 18 production fitness | metrics-server (or Prometheus) in-cluster; `pg_stat_statements` enabled on the target database; a decision on the `fitnessPolicy` ceiling |
| 19 monorepo & libraries | Nothing: the monorepo question is closed (subtrees + uv workspace, ADR-0021) and ADR-0017 treats `vibey-bootstrap` as the family cross-cutting layer |
| 20 pr-reviewer | Account list + per-account credentials; per-repo policy (review / merge / merge+deploy); the deletion threshold; confirmation of the default-yes posture |
| 21 explorer | GitHub account(s) + repo-create rights; the daily PR cap and staleness window; any ecosystems to exclude; discovery-source API access |
| 07 stores | Apple Developer account + App Store Connect API key; Google Play Console account + service account |
| 01 jira | A Jira Cloud site (free tier) + API token / OAuth app |
| 11 openclaw | An OpenClaw install; Moltbook agent registration (claim tweet is a human step) |
| 09 packages | PyPI: done (trusted publishing, no token). Per ADR-0019: `packages:write` on ghcr.io; a single-file executable tool choice (shiv, pex or PyInstaller); the existing, empty `the-vibey-project/homebrew-tap`; winget/Scoop/Chocolatey accounts; AUR account + ssh key; npm token last |
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
