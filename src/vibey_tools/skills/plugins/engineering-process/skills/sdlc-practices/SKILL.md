---
name: sdlc-practices
description: "Comprehensive SDLC reference covering model selection (Waterfall, V-Model, Spiral, RUP, Agile/Scrum/Kanban, Hybrid), requirements engineering in agile and traditional contexts, architecture practices (ADRs, fitness functions, C4, DDD), development practices (TDD, code review, trunk-based development, branching strategies), testing strategies (pyramid, trophy, honeycomb, Playwright, TestContainers, Pact), CI/CD and DevOps (DORA metrics, DevSecOps, SLSA, SBOMs), code quality, observability (OpenTelemetry), and AI-assisted development evidence. Use when advising on software delivery practices, SDLC model selection, CI/CD pipelines, testing strategy, team practices, or developer tooling."
---

# SDLC Practices Reference Guide

## Model Selection

### Core Principle
There is no single "best" SDLC. The correct model is a function of requirements volatility, regulatory constraints, and team context. The 2026 enterprise norm is **hybrid**: phase-gate governance wrapping Agile/continuous execution.

### Cynefin Framework for Model Selection
| Domain | Characteristics | Recommended Approach |
|---|---|---|
| Clear/Obvious | Stable requirements, known solutions | Plan-driven, predictive, PMBOK |
| Complicated | Known unknowns, expertise required | Plan-driven with analysis, RUP |
| Complex | Emergent requirements, high uncertainty | Agile/empirical, Scrum/Kanban |
| Chaotic | Crisis, novel situations | Act-first stabilization |

Most common error: treating Complex problems as Complicated — over-planning the unknowable.

### Waterfall and V-Model
Royce's 1970 paper actually advocated iteration and prototyping; the linear "waterfall" caricature inverted his argument.

**Waterfall is correct when**: requirements are genuinely fixed and change is expensive or dangerous — fixed-price/defense contracts, and safety-critical/regulated systems governed by IEC 61508, DO-178C (avionics), and ISO 26262 (automotive).

**V-Model**: extends waterfall by pairing each development phase with a verification/validation level (unit/integration/system/acceptance). Dominates embedded, medical-device, and automotive development.

### Iterative Models
- **Spiral (Boehm 1986)**: risk-driven, cycling through four quadrants (objectives/alternatives → risk identification/mitigation → development/test → plan next iteration). Suits large, high-risk programs.
- **RUP/Unified Process**: use-case-driven, architecture-centric, iterative across inception/elaboration/construction/transition. Relevant where formal artifacts and architecture rigor are required.

### Agile Family
- **Scrum**: time-boxed sprints, Product Owner, Scrum Master, Developers; empirical process control.
- **Kanban**: continuous flow, WIP limits, visualize workflow, no iterations.
- **FDD**: feature lists, design-by-feature/build-by-feature.
- **DSDM**: MoSCoW, timeboxing, fitness-for-business-purpose.
- **Crystal family (Cockburn)**: scales ceremony to team size and criticality (Clear/Yellow/Orange/Red).

---

## Requirements Engineering in the SDLC

### Types and Quality
Functional vs. non-functional (NFRs/quality attributes). Quality-attribute taxonomy: performance, scalability, availability, reliability, security, maintainability, usability, testability, observability, deployability.

**Critical rule**: NFRs must be specified concretely — "p99 latency < 200ms at 1,000 RPS," not "fast." NFRs are the most under-specified and highest-risk area in most software projects.

### Documentation Approaches
- **Traditional**: IEEE 830 SRS, Jacobson use cases, functional specs.
- **Agile**: user stories (As a/I want/So that) with **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable).
- **BDD** (Gherkin via Cucumber, SpecFlow, JBehave): builds shared dev/test/business language.
- **ATDD**: writes acceptance tests before implementation.
- **Impact mapping**: goal → actor → impact → deliverable.

### Backlog Management
- Refinement keeps stories ready; ruthless pruning counters "backlog obesity."
- **Prioritization**: MoSCoW, Kano, RICE (Reach × Impact × Confidence ÷ Effort), WSJF (cost of delay ÷ job size from SAFe).
- **Story mapping** (Jeff Patton): user journey backbone with release slices.
- Epic decomposition patterns: by workflow step, user role, data type, business rule, happy/unhappy path.

---

## Architecture as a Continuous Concern

### Key Practices
- **Architecture Decision Records (ADRs)**: Nygard format or MADR; stored in-repo alongside code; version-controlled.
- **Fitness functions** (Ford/Parsons/Kua, *Building Evolutionary Architectures*): make architectural qualities testable in CI.
- **Spikes**: time-box architectural uncertainty.
- Tech debt identified and classified as a first-class backlog activity.

### Design Principles
- **SOLID, DRY, KISS, YAGNI** — applied with judgment; premature DRY/abstraction is itself a smell.
- **Clean Architecture**: dependency rule — dependencies point inward; frameworks are details.
- **DDD strategic**: bounded contexts, context maps, ubiquitous language.
- **DDD tactical**: aggregates, entities, value objects, domain events.
- **API-first/contract-first**: OpenAPI/AsyncAPI before implementation.

### Documentation
- **C4 model** (Simon Brown — Context/Container/Component/Code): with Structurizr; visualizes architecture at four levels of detail.
- **Docs-as-code**: version-controlled, reviewed, tested.
- Agile "just enough, just in time" — not big upfront design.

---

## Development Practices

### Code Quality Enforcement
- **Linters**: ESLint, Pylint, Checkstyle.
- **Formatters**: Prettier, Black, gofmt.
- **Static analysis**: part of the CI pipeline.

### Code Review — Empirical Guidance
The SmartBear/Cisco study (~2,500 reviews, 3.2M LOC, 10 months) found:
- Review **fewer than 200–400 LOC at a time**.
- Spread the review over **no more than 60–90 minutes**.
- At this size: **70–90% defect-detection yield**.
- Defect detection drops sharply beyond ~400 LOC.
- **Author pre-annotation** measurably reduces defects.

**Common dysfunctions**: nitpick theater, rubber-stamping, PRs blocked for weeks. Google's guidelines emphasize splitting large CLs.

### Test-Driven Development (TDD)
Red-Green-Refactor cycle. Evidence:
- Nagappan et al. (Microsoft/IBM) found pre-release defect-density reductions of **40–90%** with a **15–35%** increase in initial development time.
- Meta-analyses (Rafique & Mišić; Bissi et al.) confirm moderate quality benefit with inconclusive productivity effects.
- TDD's quality benefit is well-supported; productivity effect is not.

### Pair and Mob Programming
- **Pair programming** (Hannay et al. meta-analysis): *small* positive effect on quality, *medium* positive effect on duration (speed), *medium negative* effect on effort. Faster on simple tasks, higher-quality on complex tasks, costs more total person-hours.
- **Mob/ensemble programming**: excels for complex, high-knowledge-transfer work.

### Refactoring
- Fowler's catalog (2nd ed.) tied to code smells.
- Kent Beck's *Tidy First?* (2023): separate structural "tidyings" from behavioral changes as economic options.

---

## Version Control and Branching

### Commit Discipline
- Atomic commits.
- **Conventional Commits**: feat/fix/docs/chore/refactor/test — enables semantic-release and changelog automation.

### Branching Strategies

| Strategy | Best For | Key Rule |
|---|---|---|
| **Trunk-Based Development** | Most software, DORA-supported default | Integrate to trunk ≥ daily; ≤3 active branches; feature flags decouple deploy from release |
| **GitFlow** | Versioned/released software (mobile, embedded, on-prem) | Release branches for specific version cycles |
| **GitHub Flow** | Web apps with continuous delivery | One main + short-lived branches |

**DORA finding**: "Elite performers who meet their reliability targets are 2.3 times more likely to use trunk-based development," in which "developers work in small batches and merge their work into a shared trunk frequently."

### Advanced Git Tools
- **Merge queues** (GitHub Merge Queue, GitLab Merge Trains): serialize integration at scale.
- **Stacked PRs** (Graphite, ghstack): keep changes small.
- **Monorepo tooling**: Nx, Turborepo, Bazel with affected-change detection.
- **Git internals**: reflog, interactive rebase, cherry-pick, bisect for bug-finding.

### Dependency Management
- **SemVer** (MAJOR.MINOR.PATCH).
- **Lock files**: pin transitive dependency trees; prevent the diamond dependency problem.
- **SCA/automation**: Dependabot, Renovate, Snyk.
- **SBOMs** (CycloneDX, SPDX): increasingly required by regulation (US EO 14028, EU Cyber Resilience Act).

---

## Testing Strategy

### Testing Pyramid Variants
| Model | Shape | Best For |
|---|---|---|
| **Classic pyramid** (Cohn) | Many unit, fewer integration, fewest E2E | General software |
| **Trophy** (Dodds) | Integration-weighted | Modern JavaScript/React |
| **Honeycomb** (Spotify) | Service/integration-focused | Microservices |
| **Ice-cream cone (anti-pattern)** | E2E-heavy | Avoid — slow and flaky |

**Shift-left**: move testing earlier. **Shift-right**: add production observability, chaos engineering, and A/B testing.

### Unit Testing
- **Arrange-Act-Assert / Given-When-Then**; test behavior, not implementation.
- Test doubles: dummy/stub/spy/mock/fake — over-mocking couples tests to implementation.
- **Coverage**: 80% is a heuristic, not a law; line/branch/path/mutation types.
- **Mutation testing** (PIT, mutmut, Stryker): tests the tests themselves.
- **Property-based testing** (Hypothesis, fast-check): auto-discovers edge cases.

### Integration and Contract Testing
- **TestContainers**: runs real dependencies (DBs, queues) in Docker — now the integration standard.
- **Consumer-driven contract testing (Pact)**: verifies service contracts without full E2E.
- API contract validation: OpenAPI schema checks, Dredd, Schemathesis.
- DB migration testing (Flyway/Liquibase/Alembic) in CI.

### End-to-End Testing
- **Playwright (Microsoft)**: overtook Cypress as the default in mid-2024 — native cross-browser (Chromium/Firefox/WebKit), native parallelism/sharding, trace viewer; used by Amazon, Microsoft, Walmart.
- **Cypress**: retains best in-browser/time-travel debugging DX for JS-centric SPA teams.
- **Selenium**: persists in large/legacy/multi-language enterprises.
- Use the **Page Object Model**; quarantine flaky tests rather than blanket auto-retry.
- **Visual regression**: Chromatic, Percy, Playwright snapshots.

### Performance Testing
- **k6**: load-as-code, thresholds; good for CI integration.
- **Gatling**: Scala, complex flows.
- **Locust**: Python, distributed.
- Performance gates and trend tracking belong in CI; profiling (async-profiler, py-spy, pprof) and flame graphs for root cause.

### Security Testing
- **SAST**: CodeQL, SonarQube, Semgrep, Checkmarx.
- **DAST**: OWASP ZAP, Burp.
- **SCA**: Dependabot, Trivy, Snyk.
- **Secrets scanning**: gitleaks, detect-secrets, truffleHog, GitHub Secret Scanning.
- **IaC scanning**: Checkov, tfsec, KICS.
- **Container scanning**: Trivy, Grype.
- **OWASP Top 10 (2021)** anchors training.
- **Threat modeling**: STRIDE, DREAD, attack trees, PASTA.

---

## CI/CD and DevOps

### CI/CD Principles
- **CI**: integrate to shared mainline ≥ daily; automated build + test; keep the build green (Andon-cord discipline — stop the line on red).
- Pipeline ordering (fail-fast): lint → unit → build → integration → security → deploy.
- Hermetic, reproducible builds (Docker multi-stage).
- **CD (Delivery)**: every commit is releasable.
- **CD (Deployment)**: every commit is released automatically.

### Deployment Strategies
- **Feature flags**: decouple deploy from release.
- **Rolling**: gradual replacement.
- **Blue-green**: instant switch between two environments.
- **Canary**: metric-gated gradual rollout.
- **A/B testing**: traffic split for experiments.
- **Dark launching**: new code runs but results are not surfaced.
- **GitOps** (Argo CD, Flux): Git as the source of truth for declarative desired state.

### DORA Metrics (5 metrics as of 2025)
1. **Deployment frequency**: how often code is deployed to production.
2. **Lead time for changes**: time from commit to production.
3. **Change failure rate**: percentage of deployments causing production failures.
4. **Failed deployment recovery time** (formerly MTTR, redefined): time to recover from a change-caused failure.
5. **Rework rate** (added 2024): ratio of unplanned deployments caused by a production incident to total deployments.

**2025 evolution**: DORA replaced low/medium/high/elite tiers with **seven team archetypes**:
- Harmonious High-Achievers (20%)
- Pragmatic Performers (20%)
- Constrained by Process (17%)
- Stable and Methodical (15%)
- Legacy Bottleneck (11%)
- Foundational Challenges (10%)
- High Impact/Low Cadence (7%)

Top two archetypes (~40%) share: strong platform engineering, small batches, and clear AI stance.

### DevSecOps and Supply Chain Security
Supply-chain attacks roughly doubled in 2025 (Sonatype: 454,600+ new malicious packages, 99% in npm).

**Regulatory mandates**: US EO 14028, EU Cyber Resilience Act — both mandate SBOMs and provenance.

**Key standards and tools**:
- **SLSA** (Supply-chain Levels for Software Artifacts): provenance/build integrity, levels 1–3+. Level 2 + Sigstore signing is achievable on GitHub Actions/GitLab CI in 1–2 days.
- **Sigstore**: keyless signing via Cosign/Fulcio + Rekor transparency log.
- **in-toto attestations**.
- **NIST SSDF (SP 800-218)**, **OWASP SAMM**, **BSIMM** — measure program maturity.

---

## Code Quality and Tech Debt

### Key Metrics
- **Cyclomatic complexity** (McCabe): concern threshold ~10–15.
- **Cognitive complexity** (SonarSource): better proxy for comprehensibility than cyclomatic.
- **Duplication**: jscpd, Simian, SonarQube.
- **Coupling/cohesion**: afferent/efferent, instability metric.
- **LCOM**: lack of cohesion of methods.

### Tech Debt Management
- **Fowler's quadrant**: deliberate/inadvertent × reckless/prudent.
- **SonarQube SQALE method**: quantifies debt ratio.
- Manage via ~20% capacity allocation, debt as first-class backlog items.
- **Boy Scout Rule**: leave code cleaner than you found it.
- **Strangler Fig pattern**: for legacy modernization.
- Feathers's *Working Effectively with Legacy Code*: characterization tests, seam identification.

### Code Review Culture
- Automate style/lint/security checks; reserve humans for design, logic, and intent.
- Keep PRs <400 LOC and review SLAs short — review lag is a measurable productivity drag.
- **Psychological safety**: non-personal feedback is prerequisite for effective review culture.

---

## Release and Operations

### Versioning and Releases
- **SemVer** (MAJOR.MINOR.PATCH) automated via semantic-release/release-please.
- Changelogs generated from Conventional Commits.
- Release trains vs. continuous delivery; feature freezes signal either genuine stabilization needs or accumulated debt.

### Database Change Management
- Tools: Flyway, Liquibase, Alembic, golang-migrate.
- **Expand-contract pattern**: for zero-downtime schema changes.

### Incident Management
- **Blameless postmortems**: 5 Whys, timeline reconstruction.
- **Severity levels**: P0–P4 with response SLAs.
- **Error budgets and SLI/SLO/SLA hierarchy** (SRE).
- **Chaos engineering**: Chaos Monkey, AWS FIS, Azure Chaos Studio.
- Sustainable on-call rotations with runbooks and escalation paths.

---

## Observability

### Three (Plus One) Pillars
1. **Metrics**: time-series measurements; SLO-based/burn-rate alerting.
2. **Logs**: structured logging (JSON, correlation IDs).
3. **Traces**: distributed request tracing; W3C TraceContext propagation.
4. **Continuous profiling** (fourth pillar, emerging).

### OpenTelemetry (OTel)
The unified, vendor-neutral CNCF graduated standard (OTLP, semantic conventions, 90+ vendors). Spans traces/metrics/logs; profiling as a fourth signal. Replaces per-vendor agents.

### Alerting Philosophy
- **Symptom-based alerting over cause-based** — alert on user-visible impact, not internal indicators.
- Error tracking (Sentry, Rollbar, Bugsnag) integrated into the SDLC.
- Feature-flag-driven gradual rollouts double as observability tools.

---

## AI-Assisted Development (2024–2026)

### Evidence Summary
The evidence is mixed and important — do not apply AI tooling uncritically.

| Study | Finding |
|---|---|
| **DORA 2024** | AI adoption correlated with −1.5% throughput, −7.2% stability per 25% adoption increase; larger batch sizes were the cause. |
| **DORA 2025** | AI now correlates positively with throughput (reversed), but instability remains negative. AI is a "mirror and multiplier" — amplifies existing strengths or dysfunctions. |
| **METR RCT (July 2025)** | Experienced developers were 19% *slower* with AI on familiar codebases, despite forecasting a 24% speedup. |
| **Veracode 2025** | 45% of AI-generated code introduced a detectable OWASP Top 10 vulnerability; XSS failed 86% of the time. |
| **Stack Overflow 2025** | 84% adoption; trust in AI accuracy *fell* from 40% to 29%. Biggest frustration (66%): "AI solutions that are almost right, but not quite." |

### DORA AI Capabilities Model (7 foundational capabilities)
1. Clear and communicated AI stance
2. Healthy data ecosystems
3. AI-accessible internal data
4. Strong version control practices
5. Working in small batches
6. User-centric focus
7. Quality internal platforms

### Production Guidance
- **Spec-driven development** (GitHub Spec-Kit, Amazon Kiro) has replaced "vibe coding" for production work.
- "Vibe coding" (Karpathy, Feb 2025) is appropriate for prototyping, dangerous for production.
- The "90% problem": AI reaches 90% quickly; the last 10% (debugging, integration, edge cases) is where human expertise is decisive.
- Gate AI-generated code through the same SAST/secrets/SCA pipeline as human-written code.
- Intensify (do not relax) testing when using AI-assisted development.
- **If instability/rework rate climbs after AI rollout**: slow AI adoption and fix the testing/review pipeline first.

### AI Code Review Tools
- **CodeRabbit**: breadth and precision.
- **Greptile**: deep-context recall (~82% catch rate in independent benchmark).
- **GitHub Copilot code review**: zero-friction GitHub integration.
- False positives remain the #1 complaint — tune aggressively for the "cry wolf" problem.

---

## Team Structures

- **Feature vs. component teams**: cross-functional, stream-aligned teams reduce cognitive load.
- **Team Topologies** (Skelton & Pais): Stream-Aligned, Platform, Enabling, Complicated-Subsystem; three interaction modes (Collaboration, X-as-a-Service, Facilitating).
- **"You build it, you run it"** (Werner Vogels / Amazon): ties ownership to on-call, changes development behavior.
- **Platform engineering / IDPs**: Gartner forecasts 80% of large software-engineering organizations will have platform teams by 2026 (up from 45% in 2022).

---

## Key Evidence and Caveats

- **The speed-quality "tradeoff" is largely a myth**: a decade of DORA data shows throughput and stability move *together* in elite organizations — quality practices accelerate delivery over the medium term.
- **DORA is correlation, not causation**: survey-based correlations; do not use as cross-org benchmarks.
- **METR 19%-slowdown result**: small (16-developer) RCT on experienced devs working on *familiar, large* codebases — does not generalize to greenfield work or junior developers.
- **Vendor benchmarks for AI code-review tools are self-serving**: treat single-vendor claims skeptically.
- **Coverage targets and "more process" are weakly supported** by research — flow metrics and small batch sizes have the most robust evidence.
