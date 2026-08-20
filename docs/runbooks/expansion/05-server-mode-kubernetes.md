# Runbook: server mode — Kubernetes everywhere (minikube → AKS/EKS/GKE)

## Goal

vibey runs as a long-lived server deployment, not a MacBook process:
containerized workers on Kubernetes, packaged as a Helm chart, autoscaled
by queue depth via KEDA, operated by a kopf-based operator, runnable
locally on minikube and hosted on AKS, EKS, and GKE. Engine sessions run
against LLM provider APIs/SDKs (API-key auth), since interactive
subscription login doesn't exist in a cluster.

## Current state (verified)

- `vibey worker` is a solid headless process already: Postgres queue
  (`FOR UPDATE SKIP LOCKED`), leases + reaping, `LISTEN/NOTIFY`, per-kind
  leases, advisory-locked integrates — worker death is already survivable
  (idempotent replay). This is 90% of being cluster-ready.
- Nothing is containerized; engines are installed as host CLIs; claudeloop
  et al. currently authenticate via subscription login on the Mac.
- `infrastructure/container/runtime.py` exists (container runtime helpers)
  — check its scope before adding a second container path.

## Design

1. **Images**: one `vibey` base image (uv-built, non-root, distroless-ish)
   and one `vibey-engines` image layering the loop runners + their
   API-key configuration. Engine API-key mode: each runner must support
   `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/`GOOGLE_API_KEY` auth (runner-side
   work item where missing — subscription login is a TTY flow).
2. **Helm chart** (`deploy/helm/vibey/`): Deployments for `worker` (N
   replicas) and `server` (the FastAPI ingress from workstream 12 —
   webhooks, API, health); CloudNativePG-or-managed-Postgres option;
   Secrets for DSN + engine keys; ConfigMap for project defaults;
   PodDisruptionBudget; liveness = DB ping, readiness = migration status.
3. **KEDA**: `ScaledObject` on the worker Deployment using the
   **postgresql scaler** — query = ready-job count due now (the claim
   query's SELECT arm); min 0 / max N replicas. Long engine sessions are
   protected from scale-in by lease-aware terminationGracePeriod +
   preStop (finish current job, stop claiming).
4. **kopf operator** (`deploy/operator/`): a `VibeyProject` CRD — spec
   holds repo URL, budget caps, engine allow-list; the operator runs
   `vibey new`, watches phase, surfaces parks as CR status conditions +
   Kubernetes Events, and applies answers written into the CR
   (`spec.answers`). Timers reap expired leases and re-run doctor sweeps.
   AKS/EKS/GKE-specific bits (workload identity per cloud) live in values
   presets: `values-aks.yaml`, `values-eks.yaml`, `values-gke.yaml`.
5. **Worktrees in-cluster**: a PVC per worker for git worktrees; repos
   cloned via deploy keys mounted as Secrets.
6. **Keep-awake is a non-problem here** (10 covers desktops).

## Work items

1. Engine API-key auth across the four runners (per-runner work items).
2. Dockerfiles + CI image builds (multi-arch: arm64 + amd64).
3. Helm chart + kind/minikube smoke test in CI (helm install → seed a
   scripted-engine project → DONE local).
4. KEDA ScaledObject + scale test (enqueue 20 jobs → replicas rise → drain
   → scale to zero).
5. kopf operator + CRD + park-to-condition flow + answer application.
6. Cloud presets: AKS/EKS/GKE values + workload-identity wiring (reuses
   workstream 03 tenants).
7. `vibey doctor --cluster`: in-cluster preflight (DB, secrets, engines).
8. Runbook doc: `docs/guides/kubernetes.md`.

## Verification

- minikube: `helm install` → full greeter run with scripted engines →
  DONE, zero manual steps; KEDA scales 0→N→0 observed.
- One paid live greeter on minikube with API-key claudeloop.
- AKS + EKS + GKE: chart installs, a scripted-engine project completes on
  each (managed Postgres), teardown clean.

## Needs from operator

Docker/colima + minikube locally; the 03 cloud tenants; LLM API keys for
API-key engine mode.

## Risks

- Engine subscription-vs-API pricing differs materially — budget caps are
  mandatory in cluster values (the brake now reads real spend).
- Scale-in during a 2h implement session — preStop + lease handoff is the
  contract; test it explicitly with a forced drain.
- CRD answer channel is a second write path to gates — it must call the
  same application service as `vibey answer` (single choke point).
