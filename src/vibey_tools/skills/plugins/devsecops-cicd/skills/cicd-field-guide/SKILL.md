---
name: cicd-field-guide
description: "Practitioner's field guide to CI/CD in 2025–2026, covering DORA metrics (five-metric model, AI amplifier findings), platform selection (GitHub Actions, Azure DevOps, GitLab CI, Bitbucket, Jenkins), branching strategy (trunk-based development), OIDC/workload identity federation, supply-chain security (SLSA, Sigstore, SBOMs), GitOps (Argo CD vs Flux), progressive delivery (Argo Rollouts vs Flagger), monorepo tooling (Turborepo/Nx/Bazel), platform engineering (Backstage vs commercial IDPs), and AI-assisted CI/CD. Use when advising on pipeline design, platform choice, security hardening, deployment strategy, or delivery metrics."
---

# CI/CD Field Guide: 2025–2026 Practitioner Reference

## The Four Defining Shifts (2015 → 2025 Pipeline)

1. **OIDC/workload identity federation** has replaced long-lived secrets as table stakes
2. **GitOps (Argo CD/Flux) + progressive delivery (Argo Rollouts/Flagger)** have replaced `kubectl apply`
3. **Software supply-chain security** (SLSA provenance, Sigstore signing, SBOMs) is now expected
4. **AI assistance + platform engineering** have moved from novelty to default

The fundamentals from DORA — small batches, trunk-based development, fast feedback, automated testing — still determine whether any of it works.

---

## DORA Metrics: The Evidence Base

### The Five-Metric Model (2025)

**Throughput group:**
- Change lead time
- Deployment frequency
- **Failed deployment recovery time** (renamed MTTR — grouped with throughput because fast recovery enables flow)

**Instability group:**
- Change fail rate
- **Rework rate** (new 5th metric) — ratio of unplanned deployments triggered by a production incident

**Reliability:** SLO/SLI-based, sits alongside.

*The relabeling of "stability" to "instability" and the addition of rework rate addresses a decade-long anomaly: change failure rate never loaded statistically with the other metrics.*

### AI Is an Amplifier, Not a Fix

2025 State of AI-assisted Software Development (survey of ~5,000 professionals, June–July 2025):
- 90% report using AI at work; 80%+ believe it increased productivity
- **Trust paradox:** only ~24% report "a great deal" or "a lot" of trust in AI-generated code; 30% trust it "a little" or "not at all"
- AI in 2025 showed a **positive relationship with throughput** (a reversal from 2024) but **continued to correlate with worse delivery stability** — AI increases change volume and batch size, exposing weak testing, review, and feedback loops

2024 data (baseline): "As AI adoption increased, it was accompanied by an estimated decrease in delivery throughput by 1.5%, and an estimated reduction in delivery stability by 7.2%" per 25% increase in AI adoption.

**The through-line:** AI raises the stakes on getting the CI/CD basics right rather than changing them.

### DORA's Seven AI Capabilities
(December 2025 AI Capabilities Model — six of seven are classic CI/CD fundamentals)
1. Clear and communicated AI stance
2. Healthy data ecosystems
3. AI-accessible internal data
4. **Strong version control practices**
5. **Working in small batches**
6. User-centric focus
7. **Quality internal platforms**

### Platform Engineering Warning
Per the 2024 DORA Report: internal developer platforms increased individual developer productivity 8% and team productivity 10% — but teams *required* to use platforms exclusively saw a **decrease in change throughput (8%) and stability (14%)**. Platforms must be paved roads (opt-in golden paths), not mandates.

---

## Platform Selection

### Decision Matrix

| Platform | Best For | Key Strength | Honest Weakness |
|---|---|---|---|
| **GitHub Actions** | Cloud-native, GitHub-centric teams | Ecosystem (20,000+ marketplace actions), OIDC, Environments | 6-hour job limit; third-party action supply-chain risk |
| **Azure DevOps** | Microsoft-stack enterprise | Most mature deployment-environment/approval model | Migrating GUI pipelines to YAML (do this now) |
| **GitLab CI** | All-in-one DevSecOps | SCM + CI + security + registry in one; CI/CD Catalog (GA) | Vendor lock-in risk |
| **Jenkins** | Air-gapped, maximum flexibility, existing investment | 1,800+ plugins, any VCS | Losing share; self-managed infra; dated UX; high TCO in DevOps engineer time |
| **Bitbucket Pipelines** | Atlassian/Jira shops | Native Jira integration, zero-config deployment tracking | **Hard deprecation deadline** (app passwords); fewer Actions minutes |

### Platform Deep-Dives

**GitHub Actions key capabilities:**
- **OIDC federation** (bind to Environments with required reviewers via `environment:<env>` subject, not just branches)
- **Environments** + deployment protection rules: required reviewers, wait timers, branch restrictions
- **Actions Runner Controller (ARC)** for Kubernetes autoscaling — use **ephemeral** runner pods (fresh pod per job, destroyed after — prevents state leakage)
- ARC 0.13.0 (Oct 2025): sidecar Docker-in-Docker (K8s 1.29+), automatic pod retries (up to 5), OpenShift support, Azure Key Vault secret retrieval (GA), `kubernetes-novolume` mode
- Security: pin third-party actions to commit SHAs; minimize `GITHUB_TOKEN` permissions; set explicit `permissions` blocks
- Reusable workflows (`workflow_call`) vs composite actions vs custom JS/Docker actions

**Azure DevOps Pipelines key capabilities:**
- **Workload Identity Federation (GA):** ARM service connections use federation subject (`sc://<org>/<project>/<connection>`) instead of a client secret; use the one-click Convert tool or bulk PowerShell for migration — treat as mandatory
- YAML multi-stage pipelines supersede classic GUI pipelines — migrate now
- Templates (step/job/stage/pipeline) for reuse; variable groups + Azure Key Vault integration
- **Pipeline decorators** inject mandatory org-wide steps (compliance-as-code)
- Environments: Kubernetes/VM resources, approval gates, deployment strategies (runOnce, rolling, canary, blue-green)

**GitLab CI key capabilities:**
- **CI/CD Components + Catalog (GA in 17.0, May 2024):** versioned, reusable, semver-tagged pipeline components (modern replacement for ad-hoc `include`; catalog hosts hundreds of components, limit raised to 100 per project in 18.5)
- Built-in SAST, DAST, dependency scanning, secret detection
- Review Apps for ephemeral per-MR environments
- Merge trains for keeping main green at scale

**Bitbucket Pipelines — URGENT:**
- **App-password hard deadline:** no new creation since Sept 9, 2025; brownouts start June 9, 2026; full removal July 28, 2026
- **Action required NOW:** migrate all Bitbucket CI integrations to API tokens with scopes or OIDC (`oidc: true`, `$BITBUCKET_STEP_OIDC_TOKEN`)
- Steps (`bitbucket-pipelines.yml`) + Pipes ecosystem + OIDC for cloud auth

**Jenkins honest assessment:**
- Market share estimated ~44% (large installed base) but actively losing share
- Use only for: air-gapped/on-prem/compliance-heavy, existing large Jenkins investments, multi-VCS shops, maximum-flexibility custom pipelines
- Use Declarative over Scripted pipelines; Shared Libraries for reuse; Kubernetes plugin for dynamic agents
- AI-assisted migration tooling (GitHub Actions Importer) now compresses Jenkins→Actions migrations from years to months

---

## Branching Strategy

### The Evidence-Backed Default: Trunk-Based Development (TBD)

DORA research (based on 33,000+ professionals) identifies TBD as a key predictor of elite performance. Atlassian now labels GitFlow a "legacy workflow"; GitFlow's creator recommends against it for continuous delivery.

| Strategy | When to Use |
|---|---|
| **Trunk-based development** | SaaS/web apps, strong CI/CD, continuous deployment — **the default** |
| **GitHub Flow** (main + short-lived feature branches) | Pragmatic middle ground for web teams wanting PR review without GitFlow complexity |
| **GitFlow** | Versioned/released software — mobile apps, desktop/firmware, OSS with external contributors, heavy-compliance |

**The most common, well-documented anti-pattern:** long-lived feature branches — they drift from trunk, compound merge conflicts, and defeat true continuous integration.

**Tooling solutions:**
- **Merge queues** (GitHub merge queue, GitLab merge trains): build speculative merge commits to keep main green at scale
- **Stacked PRs** (Graphite): decompose large changes while keeping PRs reviewable

---

## Security: The Highest-Leverage Action

### OIDC / Workload Identity Federation — Do This First

Replace long-lived cloud service-principal secrets with short-lived OIDC tokens per run.

**Platform-by-platform:**
- **GitHub Actions → Azure/AWS/GCP:** `permissions: id-token: write` + `azure/login`; bind federated credentials to GitHub Environments (`environment:<env>` subject), not branches
- **Azure DevOps:** GA via the Convert tool; federation subject constrains identity to a specific service connection — a stricter guarantee than a secret; run the bulk PowerShell for mass migration
- **GitLab:** ID tokens (`id_tokens:` block)
- **Bitbucket:** `oidc: true` flag, `$BITBUCKET_STEP_OIDC_TOKEN`

**Hard deadline:** Bitbucket app passwords — brownouts June 9, 2026; permanent removal July 28, 2026.

### Supply-Chain Security: SLSA + Sigstore + SBOMs

**SLSA (OpenSSF, v1.0 April 2023):**
- L1: provenance exists
- L2: hosted build + signed provenance
- L3: hardened, isolated, ephemeral build environment
- GitHub's `actions/attest-build-provenance` + `slsa-github-generator` achieve L2–L3 "in an afternoon"

**Sigstore stack:**
- **Cosign:** signs container images/artifacts
- **Fulcio:** issues short-lived certs tied to OIDC identity (keyless signing — no long-lived keys)
- **Rekor:** append-only public transparency log

**SBOM generators:**
- **Syft (Anchore):** best dedicated SBOM generator; SPDX + CycloneDX, broad ecosystem coverage
- **Trivy (Aqua):** Swiss Army knife — vuln scanning + IaC misconfig + secret detection + license checks + SBOM in one binary (note: reported compromised in a supply-chain attack in early 2026 — pin versions and verify provenance of your scanners)
- **Grype (Anchore):** pairs with Syft for SBOM-first vuln scanning with EPSS/KEV-based risk prioritization

**Critical principle:** prioritize findings by exploitability (EPSS, CISA KEV), not raw CVSS count — alerting on every CVE destroys developer trust.

**Verify provenance at deploy time** — generating SBOMs without verification is theater.

---

## GitOps and Progressive Delivery (Kubernetes Standard)

### Argo CD vs Flux CD

Both are CNCF-graduated and excellent.

| | Argo CD | Flux CD |
|---|---|---|
| **Wins on** | Developer UX, rich web UI, SSO/RBAC, multi-cluster visibility, fast onboarding | Kubernetes-native modularity, lightweight footprint, native OCI/SOPS, air-gapped, 100% pull-based |
| **Favored by** | Teams where non-engineers (PMs, compliance) need sync status visibility | Platform teams building reproducible multi-cluster infrastructure |
| **Shorthand** | "Argo CD is for humans" | "Flux is for robots" |

### Argo Rollouts vs Flagger (Progressive Delivery)

| | Argo Rollouts | Flagger |
|---|---|---|
| **Model** | Replaces Deployment with `Rollout` CRD; explicit step-based control + UI | Wraps existing Deployments with zero manifest changes; automated canary lifecycle |
| **Metric providers** | More native providers (Prometheus, Datadog, New Relic, CloudWatch, Wavefront, Graphite) | Fewer native; same core function |
| **Natural pairing** | Argo CD teams | Flux teams |
| **Patterns supported** | Canary, blue-green, A/B, automated rollback | Same |

**Always define both success-rate AND latency thresholds** — error rate alone misses performance regressions.

### Azure PaaS Deployment Patterns

**Azure Container Apps (cleanest pattern):**
- Blue-green/canary via revisions + traffic weights + revision labels
- Set `activeRevisionsMode: multiple`
- Each revision gets its own FQDN for testing before taking traffic
- Rollback: `az containerapp ingress traffic set --label-weight blue=100 green=0`
- Revisions are immutable; standby revision scales to zero (no extra cost on Consumption)

**App Service:** deployment slots with warm-up health checks; mark env-specific config as slot-sticky.

**Azure Container Apps Jobs** can host self-hosted CI runners.

---

## Pipeline Architecture Principles

### Core Rules
1. **Fail fast:** order cheap → expensive (lint → unit → build → integration → security scan → deploy staging → smoke → prod)
2. **Build once, promote the artifact:** same immutable image (tagged by git SHA, never `latest`) flows dev→staging→prod; rebuilding per environment is an anti-pattern
3. **Hermetic/deterministic builds:** same input → same artifact; Docker multi-stage builds, distroless/Chainguard/Alpine minimal bases

### Containerization
- **BuildKit/buildx:** multi-platform (arm64/amd64), cache mounts, registry cache
- **Kaniko:** rootless in-cluster builds
- **Caching:** layer caching, dependency caching (npm/pip/cargo/Maven), build-system caches (Gradle, Bazel remote cache, Nx Cloud, Turborepo)

---

## Monorepo CI/CD at Scale

| Tool | Best For | Key Feature |
|---|---|---|
| **Turborepo** | JS/TS workspaces, "CI is slow" problem | Content-aware hashing, local+remote caching, `--filter='...[origin/main...HEAD]'` |
| **Nx** | JS/TS to polyglot, growing monorepo | Task sandboxing (flags undeclared inputs/outputs — Turborepo lacks this), module-boundary enforcement, distributed task execution |
| **Bazel** | Very large multi-language orgs (Google/Stripe-scale) | Hermetic, remote execution, polyglot — steep learning curve; Stripe: ~45min→~7min |
| **Lerna** | Legacy (now runs on Nx under the hood) | — |

**In CI:** `fetch-depth: 0` for git history; `nrwl/nx-set-shas` for correct base/head; path filtering + dynamic matrices.

---

## Testing in CI/CD

- **Test pyramid:** unit → integration → contract → E2E
- **Parallelization/splitting:** platform-native or tools like Jest `--shard`
- **Consumer-driven contract testing:** Pact
- **Visual regression:** Chromatic/Percy/Playwright
- **Performance:** k6/Gatling/Locust
- **Flaky-test management:** detect via quarantine and flakiness scoring; fix root causes; use auto-retry sparingly (masks real bugs)
- **Ephemeral environments per PR:** Review Apps, Neon/PlanetScale DB branching, Testcontainers for portable integration dependencies

---

## Database Migrations in CI

- Tools: Flyway/Liquibase/Alembic/golang-migrate
- **Expand-contract (backward-compatible) migrations** are mandatory for zero-downtime and blue-green compatibility
- Test migrations in pipelines
- Prefer forward-only in many SaaS contexts

---

## AI-Assisted CI/CD

### AI Code Review
- **CodeRabbit:** most widely adopted (millions of PRs reviewed); strong on speed and PR summaries; 44% catch rate per a competitor benchmark (methodology-dependent)
- **Greptile:** 82% catch rate per its own July 2025 benchmark (self-reported, 50 real bugs, 5 repos) — 11 false positives vs CodeRabbit's 2
- No single tool dominates; many teams layer them
- Strategic shift: 2025 = AI speed; 2026 = AI quality with code review as a quality gate on AI-generated code

### Other AI Tools
- **Launchable (CloudBees Smart Tests) + Nx/Turborepo affected-detection:** predictive/selective test execution — run only tests likely affected by a change
- **GitHub Copilot in Actions:** AI workflow generation and failure explanations

---

## Platform Engineering and Internal Developer Platforms

### Backstage vs Commercial IDPs

**Backstage (Spotify, CNCF):**
- 89% market share vs SaaS competitors (DX March 2025); 67% overall penetration; 3,400+ orgs
- **Heavy warning:** "average Backstage adoption rate is stuck at 10%"; requires 3–5 dedicated engineers including React/TypeScript skills; Gartner reports 12+ month setup times for large enterprises
- Use only with committed staffing and maximum extensibility requirement

**Commercial alternatives:** Port, Cortex, OpsLevel, Roadie (managed Backstage, ~$35/dev/mo), Spotify Portal SaaS (~$84K/yr for 200 engineers)
- Trade flexibility for faster time-to-value
- Gartner's 2025 guidance now favors turnkey IDPs
- Use when you need fast ROI without a dedicated platform team

**Decision rule:** if Backstage adoption stalls near ~10% or your platform team spends most time maintaining the portal, switch to managed/commercial.

---

## IaC in Pipelines

- Pattern: **plan → approval gate → apply**
- `terraform plan` in CI for drift detection
- Testing: Terratest/Pester
- Scanning: Checkov/tfsec/KICS
- Principle: immutable infrastructure (replace, don't patch)

---

## Staged Implementation Roadmap

### Stage 0 — Eliminate Static Credentials (Weeks, Not Months)
Migrate every CI→cloud connection to OIDC. **Hard deadline: Bitbucket app-password integrations must move before June 9, 2026.**

Benchmark: if any pipeline still reads a long-lived cloud secret from CI, you are not done.

### Stage 1 — Delivery Fundamentals
- Trunk-based development + feature flags
- Small PRs + required status checks + merge queue
- Build once, promote immutable artifacts by git SHA
- Fail-fast pipeline ordering
- Instrument all five DORA metrics (including rework rate)

Threshold: if median PR lifetime exceeds a few days or you rebuild artifacts per environment, fix this before investing in advanced tooling.

### Stage 2 — Supply-Chain Security
- Generate SBOMs (Syft or CycloneDX build plugins)
- Scan with Trivy or Grype (pin and verify scanner versions)
- Sign images keyless with Cosign
- Emit SLSA provenance (target L2→L3)
- Prioritize by EPSS/KEV, not CVSS volume

### Stage 3 — Progressive Delivery and GitOps
- Argo CD (UI + RBAC) or Flux (lightweight, multi-cluster)
- Argo Rollouts (Argo shops) or Flagger (Flux shops)
- Always gate on success-rate AND latency; automated rollback
- Azure PaaS: Container Apps revisions or App Service slots

### Stage 4 — Platform Engineering and AI
- Encode best practices as opt-in golden paths — never mandates
- Commercial IDP for fast ROI; Backstage only with ≥3–5 dedicated engineers
- AI code review as quality gate; predictive test selection to control CI cost

### Startup vs Enterprise Calibration
- **Startups (1–3 teams):** GitHub Actions or GitLab SaaS, hosted runners, GitHub Flow, OIDC, Trivy + Cosign, App Service/Container Apps slots — skip Backstage and Bazel
- **Enterprise (10+ teams, 100+ services):** self-hosted ephemeral runners (ARC), org-wide golden-path templates + policy-as-code, Argo CD/Flux multi-cluster GitOps, an IDP, DORA-metrics tooling (LinearB/Sleuth/Faros/Jellyfish)
