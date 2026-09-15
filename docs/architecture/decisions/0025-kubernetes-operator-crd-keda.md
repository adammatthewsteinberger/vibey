# 0025 — Kubernetes: a chart, KEDA on claimable work, and an operator that never grows its own logic

**Status:** accepted · **Date:** 2026-08-21 (PRs #73 and #76; recorded 2026-09-15) · **Extends:** ADR-0002, ADR-0009

## Context

Runbook 05 set the goal: vibey as a long-lived deployment rather than a laptop process. The queue was already the right shape for it — `FOR UPDATE SKIP LOCKED` claims (ADR-0002) mean N workers need no coordinator — but three things were not: nothing could scale workers with the queue, nothing could stop a worker without orphaning a two-hour engine session, and the only way to create a project or answer a gate was a CLI on a shell.

## Decision

**Image.** Two stages; the runtime layer has no compiler, no uv, no pip, runs as uid 10001, and ships the migrations so a chart install never depends on someone running SQL by hand. CI asserts each of these as an image contract, because a property stated only in a Dockerfile comment is one refactor from lapsing (pip was in fact present until the check was written).

**Chart.** A worker Deployment, a worktree PVC, an optional in-cluster Postgres, the DSN assembled in exactly one place (qualified, because KEDA dials it from another namespace). `terminationGracePeriodSeconds: 7200`: engine sessions run for hours and cutting one mid-turn wastes paid work and leaves a turn with no verdict. An init container waits for Postgres so the failure mode is *pending*, not *CrashLoopBackOff*. `--wait-for-project` makes a projectless worker park and poll instead of exiting — exiting is the right answer for a one-shot CLI and a restart loop for a Deployment.

**Autoscaling.** KEDA's postgresql scaler on the **claimable-work** query — ready, due, dependencies satisfied — mirroring `JobRepository.claim`'s SELECT arm. Raw queue depth would start workers for jobs nothing can claim yet. Scale-down is capped at one pod per 300s: every worker carries in-flight sessions and losing several at once turns a drain into a stampede of orphaned leases. Scale-in is safe because the worker drains on SIGTERM — finishes the job in hand, claims no more — as a property of the process, not a preStop hook, since a preStop script cannot tell a running worker to stop claiming. (How that signal is made to arrive at all is ADR-0026.)

**Operator.** A `VibeyProject` CRD (repo, budget caps, engine allow-list, `spec.answers`) reconciled by kopf. The design rule the runbook named: **the CR is a second entry point into gates, and a second entry point that grows its own copy of the logic drifts from `vibey answer` without anyone noticing.** So every write goes through the same application service the CLI calls — the transition-and-enqueue logic behind `vibey new` was extracted into `application/project_kickoff.py` for this. The decisions worth testing are pure (`application/operator_projection.py`); the handlers are glue. Level-triggered: every handler is safe on unchanged input (guarded by `status.projectId`, the job's idempotency key, the gate no longer being open). Answers that cannot be applied are reported in `status.ignoredAnswers`, never dropped. Conditions use Kubernetes' vocabulary (`Ready`/`Parked`/`Complete`, CamelCase reasons). kopf is an optional extra so `vibey worker` on a laptop never pulls the Kubernetes client; the image installs it because one image serving both Deployments beats two differing by one dependency.

## Consequences

**Good.** `helm install` → migrations → a project created in-cluster → jobs processed, verified on minikube and asserted by four cluster contracts in CI (park not crash-loop, project pickup, ScaledObject Ready against real Postgres, drain under 60s of a 7200s grace). Gates are visible as `kubectl get vibeyprojects` output.

**Bad.** Engines do not ship in the image; in-cluster runs are `--provider scripted` until runbook 16 lands. The cluster-smoke job adds a real minikube install to every push (a few minutes in practice, under a 25-minute ceiling). `pip install vibey[operator]` is a separate install surface to document.

**Rule status.** The operator clause — a second entry point never grows its own copy of the logic — binds future entry points (an HTTP API, a bot) and is conduct rather than mechanism; it is the one part of this ADR that passes ADR-0020's test, and it owes a sub-doctrine, not yet proposed. The rest is mechanism.

## Alternatives rejected

- **Scale on raw queue depth.** Starts workers for jobs whose dependencies are unmet; they sit idle and then get scaled in mid-drain.
- **A preStop hook for drain.** Cannot reach into the worker's claim loop; the drain has to be the process's own behaviour.
- **A short grace period with lease reaping.** Loses hours of paid session work on every scale-in; the reaper exists for crashes, not for routine scaling.
- **The operator shelling out to `vibey new`/`vibey answer`.** Works, but the second copy of the argument parsing and the error taxonomy drifts; the application service is the seam the CLI and the operator must share.
- **Bespoke status vocabulary.** Rejected so that `kubectl` and existing tooling can filter on `BudgetExhausted` like any other controller's reason.
