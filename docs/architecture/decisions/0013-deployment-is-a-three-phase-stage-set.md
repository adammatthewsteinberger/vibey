# 0013 — Deployment is a three-phase stage set in the core lifecycle

**Status:** superseded in part by ADR-0014 · **Date:** 2026-08-14 · **Supersedes:** ADR-0012

> Historical safety and execution design retained. ADR-0014 supersedes only
> this record's automatic `③ → ④` entry rule; deployment now requires an
> explicit user opt-in after Phase ③. The three deployment phases, consent
> contract, retry taxonomy, and Azure safety controls remain the basis for M10.

## Context

ADR-0012 treated Azure deployment as an explicit post-phase command in a separate
package. That boundary prevented an unsafe implicit cloud mutation, but it also
ended vibey's durable, interactive/autonomous/interactive protocol at the point
where deployment uncertainty and recovery matter most.

The product lifecycle is now two macro-stages, each containing three phases:

1. **Delivery:** ① DESIGN → ② BUILD → ③ REVIEW.
2. **Deployment:** ④ DEPLOY DESIGN → ⑤ DEPLOY EXECUTE → ⑥ DEPLOY REVIEW.

"Stage" in this decision means a three-phase lifecycle group. It does not replace
the seven interview stages inside Phase ① DESIGN.

## Decision

Deployment is part of vibey's core phase machine. In the original version of
this decision, acceptance in Phase ③ automatically entered Phase ④. ADR-0014
supersedes that entry rule: current behavior first asks whether the user wants
to work on deployment, and a decline completes the run locally. An explicit
opt-in enters interactive Phase ④, which must gather enough trusted deployment
detail and explicit authorization to define a safe, replayable deployment
specification. It does not mutate Azure.

Phase ⑤ executes that accepted deployment specification autonomously through the
durable queue. It continues through retryable work and waitable capacity failures
until either:

- deployment and verification succeed, or
- a failure is classified as requiring user input.

Both outcomes enter interactive Phase ⑥. On success, Phase ⑥ demos the deployed
workload and its evidence. On a user-input failure, it explains the failure and
asks only for the missing decision or authority. Phase ⑥ can route back to Phase
④ for changed details, Phase ⑤ for an unambiguous retry, or the delivery phases
when the deployed artifact itself must change.

The current entry into Phase ④ is never automatic. Azure mutation is not either:
the `④ → ⑤` guard requires an accepted deployment specification containing the
target tenant/subscription, scope, environment, identity, cost boundary,
verification contract, recovery policy, and explicit deployment consent. Consent
is ledger evidence, not a CLI flag or an ambient default.

## Safety model

- Use infrastructure as code. Bicep is the Azure default; a target may select
  Terraform through the same port.
- Authenticate with Microsoft Entra workload identity/OIDC or an existing
  user-approved Azure CLI identity. Do not create or store client secrets.
- Apply least-privilege RBAC at the narrowest accepted scope. Elevation or a new
  role assignment is a human gate.
- Run static IaC checks, ARM preflight validation, and `what-if` before mutation.
  Unexpected deletes, scope expansion, policy denial, destructive data changes,
  or cost-bound violations require user input.
- Prefer incremental deployment mode. Complete-mode deletion is not a default.
- Select the Azure compute target from requirements; do not force every workload
  into App Service, Container Apps, Functions, or AKS.
- Use service-appropriate progressive exposure (slot, revision, canary,
  blue-green, or stamp) and health gates when the target supports it.
- A provider success response is not deployment success. Success requires
  resource convergence, application health, smoke/acceptance checks, and a bake
  window defined in the deployment specification.
- Persist every command intent, redacted result, Azure deployment/operation ID,
  resource ID, artifact digest, verification result, and recovery action. Secrets
  are references to Key Vault or another approved store, never ledger values.
- Halt rollout on health degradation. Roll back, roll forward, or fall back only
  according to the accepted recovery policy. Stateful schema changes require an
  explicit compatible migration and recovery plan.

## Loop-back rules

- `④ → ④`: deployment questions remain open.
- `④ → ⑤`: deployment specification accepted and all guards pass.
- `⑤ → ⑤`: retryable transient, capacity, or unambiguous deployment failure.
- `⑤ → ⑥`: verified success or a failure requiring user input.
- `⑥ → DONE`: successful deployment demo accepted.
- `⑥ → ④`: target, authority, topology, budget, secret reference, or recovery
  policy must change.
- `⑥ → ⑤`: user supplies the missing input and the accepted specification is
  otherwise unchanged, or requests an unambiguous redeploy.
- `⑥ → ①/②/③`: the deployed artifact or its acceptance criteria must change;
  normal delivery-stage routing decides how far back to go.
- Any nonterminal phase may enter `ABANDONED` on explicit user cancellation.

All loop-backs are bounded by deployment-attempt and cost caps. A worker never
waits on the user; it parks a durable human gate and releases its lease.

## Packaging boundary

Azure integrations remain behind application ports and optional infrastructure
dependencies so core/domain stay Azure-agnostic and stdlib-only. A separately
installable Azure extra or companion distribution may implement those ports, but
it no longer owns a separate lifecycle or command-only state machine.

## Consequences

**Good.** The no-loss ledger, retry taxonomy, capacity handling, human gates, and
phase guards now cover the complete idea-to-deployed-software journey.

**Good.** Deployment cannot silently fail after `DONE`; its result is reviewed by
the user with runtime evidence.

**Bad.** The phase machine, data model, transition properties, test matrix, and
security surface become larger. M10 therefore requires offline adapter tests plus
a tightly scoped real-Azure development-environment proof.

**Bad.** An earlier automatic-entry rule could be mistaken for automatic
authority. The explicit opt-in, `④ → ⑤` consent guard, and immutable target
scope are mandatory and must be visible in the CLI/TUI.
