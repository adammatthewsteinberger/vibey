# 0012 — Deployment is a separate CLI built on `azure-bootstrap`

**Status:** accepted · **Date:** 2026-08-14

## Context

The specification places automatic Azure deployment in a "post-phases" row,
explicitly as a *separate CLI library* rather than a phase of the main loop.

An `azure-bootstrap` library (3.0.1) already exists in this workspace, published to
PyPI, providing an `azbootstrap` scaffold entry point, the App Configuration ↔
Key Vault ↔ Application Insights bootstrap, ten logging transports, and an AI
usage tracker with sliding-window cost caps.

## Decision

**`vibey-deploy` is a separate package**, installable independently, that layers
target detection, IaC emission, environment promotion, and post-deploy
verification over `azure-bootstrap`.

It is invoked explicitly:

```bash
vibey deploy --confirm
```

Deployment never happens implicitly, and never as an automatic consequence of
reaching `DONE`.

## Rationale

**Why separate.** Deployment has a different blast radius from everything else
vibey does. Phases 1–3 write to local branches in local worktrees; a mistake costs
a rebuild. Deployment touches infrastructure that costs money and can serve
traffic. Different blast radius, different release cadence, different dependency
set (`azure-*` SDKs are heavy), and different security posture — so a different
package, with its own gate.

**Why build on `azure-bootstrap`.** It already solves the cross-cutting layer
every Azure project re-implements, it is the house standard, and its AI usage
tracker is the reference implementation for vibey's own budget caps. Rewriting it
inside vibey would be duplication of exactly the kind ADR-0001 rejects.

**Why `--confirm`.** Vibey's default posture everywhere is that nothing leaves the
machine without an explicit human decision: no `git push`, no PR, no deploy. An
autonomous system that can provision cloud infrastructure while its operator
sleeps needs the gate to be a deliberate act, not a config default.

## Scope

1. **Target detection** — classify the built artifact using the
   `azure-services-catalog` decision ladder: App Service (modular monolith) →
   Container Apps (containerized default) → AKS (only when the full Kubernetes API
   is genuinely needed).
2. **IaC emission** — Bicep by default; Terraform behind `iac = "terraform"`.
3. **Environment promotion** — `dev → staging → prod` using App Service deployment
   slots for near-instant, reversible swaps.
4. **Post-deploy verification** — health endpoint probe plus smoke test. On
   failure, a `DEPLOY → REVIEW` transition carrying the failure as a
   `FindingRaised`, so a broken deployment re-enters the loop as a review finding
   rather than as a dead end.

## Consequences

**Good.** Vibey core stays deployment-agnostic and dependency-light. The Azure
knowledge lives where the Azure library already is. A future `vibey-deploy-aws`
implements the same interface without touching core.

**Bad.** Two packages to version and release together when the interface changes.
Mitigated by keeping the interface narrow: `detect(artifact) → Target`,
`emit(target) → IaC`, `apply(iac, env) → DeployResult`, `verify(env) → Findings`.

**Out of scope for v1.** Non-Azure targets, multi-region topology, and blue-green
beyond slot swaps.
