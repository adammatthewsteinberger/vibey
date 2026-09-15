---
name: github-atlassian
description: "Advanced practitioner reference for GitHub and the Atlassian suite (Jira, Confluence, JSM, Bitbucket) covering 2025–2026 changes: GitHub rulesets, merge queue, GHAS rebundling (Secret Protection $19/Code Security $30), Copilot agent GA, AI Credits billing, artifact attestations, EMU; Atlassian Server EOL, Rovo bundling, JSM Service Collection, Forge replacing Connect, Data Center countdown; and the GitHub↔Jira integration pattern for 50–500 engineer orgs. Use when advising on GitHub governance, Atlassian configuration, tool selection, billing strategy, or cross-platform integration."
---

# GitHub & Atlassian: Advanced Practitioner Reference (2026)

## The Three Things You Must Plan Around Now

1. **GitHub billing changes (April–June 2026):** GHAS split into two SKUs (April 1, 2025); Copilot moved to usage-based AI Credits billing (June 1, 2026)
2. **Bitbucket app-password hard deadline:** brownouts start June 9, 2026; permanent removal July 28, 2026
3. **Atlassian Server is dead (Feb 2024); Data Center is on a countdown** — no new DC sales after March 30, 2026; full EOL March 28, 2029

---

## Part 1 — GitHub

### 1.1 Repositories and Governance

**Rulesets have superseded branch protection** as the model of choice:
- Multiple rulesets **aggregate** (most restrictive applies) vs branch protection (one rule "wins" by priority)
- Can be set at the **organization level** (GitHub Enterprise)
- Target branch-name patterns and tags
- Run in **evaluate (dry-run) mode** before enforcement
- Enforce **metadata rules** (commit message, branch naming, author email) natively — eliminating pre-receive hooks
- Branch protection still exists and layers with rulesets

**Three repository visibilities:**
- Public, private, and **internal** (enterprise accounts only) — internal = visible to all enterprise members, ideal for InnerSource

**CODEOWNERS:** routes review by path (last matching pattern wins); can be required via rulesets.

**GitHub merge queue (GA 2023):**
- Builds speculative merge commits (base + PRs ahead + this PR) and merges FIFO once required checks pass
- Requires the `merge_group` workflow trigger — **the single most common misconfiguration**
- Does not support wildcard branch patterns
- Designed and tested at scale (GitHub.com: 30,000+ PRs, 4.5M CI runs before GA)

### 1.2 Issues and Projects

**YAML issue forms** have largely superseded markdown templates for serious intake — structured dropdowns/checkboxes/validations.

**GitHub Issues vs Jira decision:**
- GitHub Issues + Projects: free, markdown-native, zero context-switch — sufficient for teams under ~20–30 developers
- Jira wins on: workflow enforcement (conditions/validators/post-functions), velocity/burndown/CFD reporting, cross-project portfolio visibility, issue hierarchy (Initiative→Epic→Story→Sub-task), 5,000+ Marketplace

**GitHub Projects (v2) honest gaps vs Jira:**
- No native velocity/cycle-time analytics
- Flat hierarchy (no true epics/parent-child without task-list workarounds)
- Limited fine-grained permissions ("QA can only move to Done" isn't expressible)
- Managed via GraphQL API

### 1.3 GitHub Actions

**Core building blocks:** triggers, matrix builds, concurrency controls, reusable workflows (`workflow_call`) vs composite/JS/Docker actions.

**Security and scale features:**
- **OIDC federation:** bind to Environments (`environment:<env>` subject) with required reviewers, not just branches — the right way to gate production
- **Environments + deployment protection rules:** required reviewers, wait timers, branch restrictions
- **Actions Runner Controller (ARC):** Kubernetes-native autoscaling using **ephemeral** runner pods (fresh pod per job, destroyed after — prevents state leakage and ensures no job is assigned to a shutting-down runner)
  - ARC 0.14.0 (March 2026): moved to `actions/scaleset` library client
  - Earlier releases added: native sidecar DinD, automatic pod retries (up to 5), OpenShift support, Azure Key Vault secret retrieval (GA), dual-stack IPv4/IPv6

**Security best practices:**
- Pin third-party actions to commit SHAs (Dependabot updates them)
- Minimize `GITHUB_TOKEN` permissions; set explicit `permissions` blocks
- Marketplace actions introduce third-party supply-chain risk

**Repository secrets/variables scope:** org, repo, and environment levels.

### 1.4 GitHub Advanced Security (GHAS) — Repriced April 1, 2025

GHAS was unbundled into two metered, committer-priced SKUs available even on Team:

| SKU | Price | Includes |
|---|---|---|
| **Secret Protection** | $19/active committer/mo | Push protection, validity checks, AI-detected generic secrets, 200+ partner patterns |
| **Code Security** | $30/active committer/mo | CodeQL code scanning, Copilot Autofix, security campaigns, dependency review |

**Active committer definition:** unique active committers on a 90-day window over repos where the feature is enabled.

**Cost control:** scope to specific repos — org-wide enablement counts every contractor and bot that pushes.

**Copilot Autofix:** covers 90%+ of alert types in JS/TS/Java/Python; suggestions remediate 2/3+ of found vulnerabilities.

**Other security features:**
- Dependabot: alerts, security updates, version updates, grouped updates via `dependabot.yml`
- Secret scanning push protection: blocks at push; delegated bypass (approval workflow); validity checks against provider APIs
- Custom patterns (up to 500/org via Hyperscan regex)
- **Artifact attestations** (GA June 2024): `actions/attest-build-provenance` via Sigstore → SLSA Build Level 2 out of the box, Level 3 with reusable workflows; no key management; Kubernetes admission controller for enforcement
- Security campaigns (2025): org-level security debt remediation workflows

### 1.5 GitHub Copilot

**The product is now a family of agents:**

| Feature | Status | Notes |
|---|---|---|
| Code completions | GA | Unlimited and unbilled on paid plans |
| Copilot Chat (IDE + GitHub.com) | GA | PR summaries, repo Q&A, slash commands, `@workspace` |
| Copilot code review | GA (April 4, 2025) | Automatic (via rules) + on-demand; 1M+ devs in first month of preview |
| Copilot coding agent | GA (Sept 25, 2025) | Assign issue → opens draft PR via GitHub Actions |
| Copilot CLI | GA | — |
| Agent mode (VS Code, JetBrains) | GA by early 2026 | Multi-file/multi-step agentic sessions |

**Billing changed June 1, 2026 to usage-based AI Credits (1 credit = $0.01, priced by token/model):**

| Plan | Price | AI Credits included |
|---|---|---|
| Business | $19/user/mo | $19 credits |
| Enterprise | $39/user/mo | $39 credits (also requires GHEC ~$21/user → real cost ~$60/user) |

- Code completions remain unlimited and unbilled
- **Copilot code review additionally consumes GitHub Actions minutes on private repos starting June 1, 2026** (public repos remain free)
- Agentic sessions can consume credits and Actions minutes quickly — set spend alerts

**Honest assessment:** measurably helps on boilerplate, tests, and low-to-medium-complexity well-tested codebases; underdelivers on novel architecture and large unfamiliar codebases.

### 1.6 Enterprise Identity (EMU)

**True SCIM provisioning requires GitHub Enterprise Cloud with Enterprise Managed Users (EMU).**
- Standard GHEC: only SCIM-triggered invitations (not full provisioning)
- **EMU hard tradeoff:** managed users cannot contribute to public repos or external OSS
- Okta + Entra split-IdP combination is explicitly unsupported
- **Data residency (GHE.com) requires EMU**

**GitHub Enterprise options:**
- **GHEC:** cloud-hosted, EMU optional, GitHub Connect bridge
- **GHES:** self-hosted HA (primary-replica, backup-utils), GitHub Connect bridge to GHEC; air-gapped option

### 1.7 Packages and Ecosystem

**GHCR** for GitHub-native flows; choose **Azure Artifacts/Artifactory** for polyglot enterprise artifact governance.

**GitHub Apps vs OAuth Apps vs PATs vs Actions tokens:**
- GitHub Apps (JWT→installation tokens): the right credential for automation
- PATs: simpler but coarser; fine-grained PATs now available
- Actions `GITHUB_TOKEN`: repo-scoped, short-lived — prefer over PATs in Actions workflows

**Codespaces:** devcontainers + prebuilds; billed per compute-hour.

---

## Part 2 — Atlassian

### 2.1 Server EOL and Data Center Countdown

| Milestone | Date |
|---|---|
| Server end of support | February 15, 2024 — **DONE** |
| No new DC sales | March 30, 2026 |
| DC license/tier/app purchases stop | March 30, 2028 |
| DC full EOL (read-only) | March 28, 2029 |

Migration path: Cloud Migration Assistant; "Atlassian Ascend"/FastShift programs for 1,000+ user orgs.
A Bitbucket Hybrid License (DC + Cloud) arrives mid-2026.

### 2.2 Jira Software

**Two project types:**
- **Team-managed (formerly next-gen):** simple, autonomous
- **Company-managed (classic):** deep scheme model (workflow, permission, notification, issue type, field, screen schemes + project roles) — required for workflow gates, cross-project portfolio

**Hierarchy:** Initiatives (in Plans) → Epics → Stories/Tasks → Sub-tasks

**Workflows:** statuses/transitions with conditions, validators, post-functions — the feature that makes Jira worth it over GitHub Issues.

**JQL tips:** write index-friendly queries; avoid full-text scans at scale; use functions (`currentUser()`, `membersOf()`, `startOfWeek()`).

**Jira Automation:** no-code triggers/conditions/actions/branches at project and org level.

**Jira Plans (Advanced Roadmaps):** cross-team/program planning and dependency tracking.

### 2.3 Jira Service Management (JSM) — Now "Service Collection"

**JSM + Assets + Rovo + Customer Service Management** are now sold as the Service Collection.

**Premium tier (~$47–53/agent/mo) gates the features that matter:**
- CMDB/Assets
- Change management with CI/CD deployment gating
- Major incident management
- Atlassian Intelligence
- Virtual Service Agent

**Billed per agent** — requesters are free.

**Opsgenie status:** new sales ended June 4, 2025; full shutdown April 5, 2027; capabilities folded into JSM.

**JSM vs ServiceNow vs Zendesk:**
- JSM wins: Atlassian-ecosystem integration, per-agent price
- ServiceNow wins: heavyweight enterprise ITSM breadth
- Zendesk wins: pure customer-facing support UX

### 2.4 Rovo — Atlassian's AI Layer

**"Rovo for all" (from April 9, 2025):** Rovo Search/Chat/Agents/Studio included in paid Jira/Confluence/JSM Cloud plans — no separate SKU for core features.

**Credit allowances (pooled at org level, monthly, no rollover):**

| Plan | Credits/user/mo |
|---|---|
| Standard | 25 |
| Premium | 70 |
| Enterprise | 150 |

- Jira, Confluence, and Service Collection/JSM
- A single Rovo Chat/Agent question = 10 credits; Deep Research = 100 credits
- Atlassian Intelligence (in-product drafting/summaries) is the foundation; Rovo is the cross-product layer
- **Rovo Dev** (for engineers — CLI, PR analysis) is a separate $20/dev/mo product with 2,000 credits
- Rovo is **Cloud-only**
- Rovo credit overages are not yet billed but Atlassian has signaled future consumption-based charging (≥90 days notice)

### 2.5 Bitbucket — URGENT Deprecation

**App-password hard deadline:**
- No new creation: September 9, 2025 — **PASSED**
- Controlled brownouts begin: June 9, 2026
- Permanent removal: July 28, 2026

**Action required immediately:** migrate all Bitbucket CI integrations to API tokens with scopes (or OIDC for cloud auth).

**Bitbucket Pipelines OIDC:** `oidc: true` flag; `$BITBUCKET_STEP_OIDC_TOKEN` for keyless cloud auth.

**Code Insights/Annotations API:** pushes CI quality/coverage/security results back onto PRs.

**Bitbucket Pipelines vs GitHub Actions:**
- Actions wins on: ecosystem (20,000+ marketplace), reusable workflows, matrix builds, macOS/Windows runners, free minutes (2,000/mo vs Bitbucket's 50 free; Standard 2,500, Premium 3,500)
- Pipelines wins on: simplicity and zero-config Jira deployment tracking

**Main reason to keep Bitbucket:** native Jira integration — same-vendor, deeper integration than GitHub's, strongest reason Atlassian-centric orgs stay

### 2.6 Confluence

**Key capabilities:**
- Spaces with a permission model (space admin; page view/add/edit/delete/export)
- Page hierarchy and restrictions
- Fabric editor with macros (code, ToC, panels, status, live Jira issue lists, children display, excerpt/excerpt-include)
- **Whiteboards** (GA February 29, 2024): Cloud-only
- **Databases** (broad rollout July 10, 2024): structured data as fields + entries, sync from Jira/Confluence/CSV — Cloud-only
- CQL search and Confluence Analytics (Cloud)
- Page properties + reports for lightweight tracking

**Confluence vs Notion vs SharePoint:**
- Confluence wins: Atlassian-integrated teams (live Jira embeds, JSM knowledge base, space permissions)
- Notion wins: flexible databases/UX for smaller teams
- SharePoint wins: Microsoft 365-centric document governance

### 2.7 Forge vs Connect

**Forge has replaced Connect** as the app platform.

| | Connect | Forge |
|---|---|---|
| Model | External iframe (third-party servers) | Serverless on Atlassian infrastructure |
| Storage | External DB | Key-value + Forge SQL |
| Compliance | Requires vendor trust | Preferred model (Atlassian-hosted) |
| Status | **End of support Q4 2026** | Active, all new investment |

**Connect deprecation timeline:**
- No new Connect listings: September 17, 2025 — **PASSED**
- No Connect updates: March 31, 2026
- End of support: Q4 2026

**Action required:** audit Connect app dependencies; confirm vendors have Forge versions before Q4 2026.

### 2.8 Atlassian Guard (Security Layer)

- **Guard Standard** (SSO/SCIM/API-token control/audit log) — included free in Cloud Enterprise
- **Guard Premium** (data classification, content scanning/DLP, anomalous-activity threat detection, extended audit) — currently supports Jira and Confluence

---

## Part 3 — GitHub ↔ Atlassian Integration

### The Official "GitHub for Jira" App

- Atlassian-maintained; **Jira Cloud only**
- Links commits/branches/PRs/builds/deployments to issues by string-matching the Jira issue key
- Surfaces data in the Jira development panel, board card icons, Code/Releases/Deployments tabs, JQL
- Smart commits: `PROJ-123 #comment ... #time 2h #done`
- "Create branch" button in Jira; JQL queries over development data

**Limitation:** only as reliable as naming discipline — which is why mature teams enforce issue-keyed branch names via rulesets and drive status transitions via Actions.

**GitHub Enterprise Server ↔ Jira DC:** not supported by the native app — requires third-party (e.g., GitKraken's Git Integration for Jira).

### Production Integration Pattern (50–500 Engineers)

1. **Enforce issue-keyed branch names** via GitHub rulesets (regex rejecting non-conforming branches at push)
2. **Drive Jira status transitions from GitHub Actions** on `pull_request`/`push`/deployment events calling the Jira API or `atlassian/gajira-*` actions — more reliable than smart commits (which depend on developer discipline and email matching)
3. **Track deployments** via GitHub Environments → Jira deployment panel
4. **Pipe CodeQL/Dependabot findings into Jira** as security issues via Actions for SLA-tracked remediation
5. **Keep Jira as system of record;** use GitHub Projects only for engineering-local sprint views to avoid dual-maintenance

---

## Part 4 — Cross-Cutting Concerns

### Org Design
- Mono-repo vs poly-repo drives GitHub org/team structure and Jira project layout (one project per team is the common default)
- Standardize naming across both: branch names, PR titles, Jira summaries
- Standardize identity: one IdP (Entra ID/Okta) → GitHub teams via EMU SCIM → Jira groups/roles via Guard SCIM

### End-to-End Agile Delivery Flow
Jira issue → issue-keyed branch → PR (linked) → CI (Actions/Pipelines) → human + Copilot code review → merge queue → Jira transition → release → deployment tracked in Jira

- **Dual-track agile:** Confluence (discovery) + Jira sprints (delivery)
- **DoD enforcement:** Jira automation + GitHub required checks

### DORA Metrics Cross-Platform
- **Deployment frequency:** GitHub releases/deployments
- **Lead time:** Jira create → PR merge → deploy
- **Change failure rate:** bug/incident tickets
- **MTTR:** incident resolution
- **Tooling:** LinearB, Sleuth, Faros AI, Jellyfish, Haystack

### Security and Compliance Integration
- GHAS findings → Jira security issues (via Actions)
- Both audit logs → SIEM
- JSM change requests linked to GitHub PRs/deployments
- Secret-scanning alerts → JSM incidents
- Both platforms carry SOC 2 / ISO 27001; Atlassian Cloud adds FedRAMP

### Licensing and Cost Optimization
| Product | Standard | Premium |
|---|---|---|
| Jira | ~$7.91/user/mo | ~$14.54/user/mo |
| Confluence | ~$5.42/user/mo | ~$10.44/user/mo |
| JSM | ~$20/agent/mo | ~$47–53/agent/mo |
| GitHub Team | $4/user/mo | — |
| GitHub Enterprise | ~$21/user/mo | — |
| GHAS Secret Protection | $19/committer/mo | — |
| GHAS Code Security | $30/committer/mo | — |
| Copilot Business | $19/user/mo | — |
| Copilot Enterprise | $39/user/mo (+ GHEC) | — |

**Optimization levers:**
- Prune inactive users (metered billing means unused seats still cost)
- Scope GHAS to specific repos, not org-wide
- Reconcile licenses against IdP group sync
- Consolidate on Enterprise where volume discounts apply
- Set Copilot spend alerts given usage-based billing

---

## Staged Implementation Roadmap

### Stage 1 — Stabilize Identity and Deprecation Exposure (Now)
1. **Migrate Bitbucket app passwords to API tokens/OIDC before June 9, 2026 brownouts** — this is the most urgent hard deadline
2. Audit Connect app dependencies; confirm vendors have Forge versions before Q4 2026
3. Standardize SSO/SCIM on one IdP feeding both ecosystems
4. Decide **EMU vs standard GHEC** using the OSS-contribution and data-residency tests

### Stage 2 — Modernize Governance (Next Quarter)
1. Migrate branch protection → **organization rulesets** in evaluate mode first, then enforce; add metadata rules for issue-keyed branch names
2. Enable **merge queue** on busy default branches (remember the `merge_group` trigger)
3. Scope **GHAS Secret Protection + Code Security** to active repos; turn on push protection org-wide with delegated bypass

### Stage 3 — Integrate and Measure (6–12 Months)
1. Deploy GitHub for Jira; replace smart-commit reliance with Actions-driven transitions
2. Stand up DORA metrics via a cross-platform tool
3. Pilot **Copilot coding agent / code review** and **Rovo agents** on contained workflows; set spend alerts

### Thresholds That Change the Plan
- Cross ~30 engineers or need workflow gates/portfolio reporting → move planning to Jira (not GitHub Projects)
- Active-committer count balloons with bots/contractors → re-scope GHAS repos to control cost
- Copilot agentic usage drives credit overages → cap org spend and restrict premium models
- Air-gapped/sovereign requirements → GHES + Bitbucket DC (until 2029)
