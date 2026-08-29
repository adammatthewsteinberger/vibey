# Running vibey on Kubernetes

This guide takes vibey from a laptop process to a long-lived deployment:
a containerized worker, a Helm chart, an in-cluster PostgreSQL, and
queue-depth autoscaling via KEDA. Everything below was verified on
minikube (Kubernetes v1.35.1); the chart is written so the same values
work against a managed Postgres on AKS/EKS/GKE, but only the local path
has been exercised end to end so far.

## What works today, and what does not

Be clear about this before you install anything:

- **The worker runs, applies migrations, claims jobs, and autoscales.**
- **Engines do not ship in the image.** `deploy/docker/Dockerfile` builds
  vibey only — no `claudeloop`, `codexloop`, `cursorloop`, or `agyloop`
  binaries. In-cluster runs therefore use `--provider scripted`, and the
  worker will log `no recorded conformance for agyloop, claudeloop,
  codexloop, cursorloop`. That warning is correct, not a misconfiguration.
  Real engines in-cluster are workstreams
  [05](../runbooks/expansion/05-server-mode-kubernetes.md) item 1 and
  [16](../runbooks/expansion/16-loop-runner-containers.md).
- **The operator is implemented, but off by default.** `vibey operator`
  (`pip install 'vibey[operator]'`) runs kopf handlers that create
  projects and apply `spec.answers` through the same application services
  `vibey new` / `vibey answer` use, then reconcile `VibeyProject` status
  every 15s. The chart does not install it unless you set
  `operator.enabled=true` (step 7 below); without that flag, creating
  projects and answering gates is still `vibey new` / `vibey answer`, run
  inside a pod or against the database.

## Prerequisites

- Docker (or colima) and `minikube`, `helm`, `kubectl`.
- For autoscaling, KEDA installed in the cluster (step 5).

## 1. Build the image into the cluster's daemon

The chart defaults to `image.pullPolicy: Never` and tag `vibey:dev`,
because a locally built image has never been pushed anywhere and `Always`
would send kubelet hunting a registry that has never seen it. Build
directly into minikube's Docker daemon:

```bash
minikube start -p vibey
eval $(minikube -p vibey docker-env)
docker build -f deploy/docker/Dockerfile -t vibey:dev .
```

The image is two-stage on purpose: the runtime layer carries no compiler
and no package manager, so a compromised engine session inside a worker
does not find build tools waiting. Migrations ship inside it, so an
install never depends on someone running SQL by hand first.

## 2. Install the chart

```bash
helm install vibey deploy/helm/vibey -n vibey --create-namespace
```

This creates a worker Deployment, a worktree PVC, and a single-replica
PostgreSQL StatefulSet. An init container waits for Postgres so the
failure mode is "pod pending" rather than "CrashLoopBackOff with a stack
trace", and the worker applies migrations itself at startup.

The built-in Postgres is **development only** — `postgres.password`
defaults to `vibey` in plain values. For anything real, set
`postgres.enabled: false` and point `dsn.existingSecret` at a Secret
holding a managed instance's DSN.

## 3. Create a project

A worker with nothing to do would normally exit, which in a Deployment is
a restart loop that ends only when a human creates a project — and the
crash counter makes a healthy worker look broken. The chart therefore
sets `--wait-for-project 15`, so the worker parks and polls:

```
no project yet; polling every 15s
```

Create one from inside the cluster:

```bash
kubectl exec -n vibey deploy/vibey-vibey-worker -- \
  vibey new demo --repo /work/demo --max-cycles 1
```

> **Set `worker.project` explicitly.** Left empty, the worker binds to
> whichever project was created most recently — convenient on a laptop, a
> footgun in a cluster the moment a second project exists. The value is
> the project **UUID**, not its name. `vibey new` prints it on creation;
> there is no list-projects command yet, so otherwise read it from the
> database (`SELECT id, name FROM project;`). The chart does not enforce
> this, so it is on you:
>
> ```bash
> helm upgrade vibey deploy/helm/vibey -n vibey \
>   --set worker.project=<uuid>
> ```

## 4. Watch it work

```bash
kubectl logs -n vibey deploy/vibey-vibey-worker -f
```

```
worker started: project=demo engines=all parallelism=2 provider=scripted
processed one job
```

## 5. Autoscaling with KEDA

KEDA is a cluster-wide operator and is not assumed, so the ScaledObject is
off by default and inert without it.

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm install keda kedacore/keda -n keda --create-namespace --wait
helm upgrade vibey deploy/helm/vibey -n vibey --set keda.enabled=true
```

The trigger is the **claimable-work** query — ready, due now, and not
blocked behind an unsatisfied dependency — deliberately mirroring
`JobRepository.claim`'s SELECT arm. Scaling on raw queue depth would
start workers for jobs nothing can claim yet.

Measured behavior on minikube with `maxReplicas: 4`:

| Event | Observed |
|---|---|
| 20 claimable jobs enqueued | 0 → 4 replicas in ~8s |
| queue drained | 4 → 0 after the 300s `cooldownPeriod` |
| pod receives SIGTERM | exits in 4-5s |

Note that the N→0 transition happens in **one step**. KEDA's deactivation
path sets the replica count directly and bypasses the HPA `scaleDown`
behavior policy entirely. That policy only smooths HPA-driven scaling
between `minReplicas` and max — do not read it as protection against
losing several in-flight sessions at once.

## 6. Scale-in and long sessions

Engine sessions run for minutes to hours, so `terminationGracePeriodSeconds`
defaults to **7200**. That is a ceiling for one long in-flight turn, not
an expected shutdown time.

On SIGTERM the worker drains: it finishes the job in hand and claims no
more, then exits.

```
draining on SIGTERM: finishing in-flight job, claiming no more
```

An idle worker therefore exits in seconds. Only a worker genuinely
mid-turn uses any meaningful part of the grace period.

## 7. The kopf operator (optional)

The chart can also install a cluster-scoped operator that reconciles
`VibeyProject` custom resources, so a project is a CR instead of a
`kubectl exec` command:

```bash
helm upgrade vibey deploy/helm/vibey -n vibey --set operator.enabled=true
```

This installs, in addition to the worker:

- the `VibeyProject` CRD (`vibeyprojects.vibey.dev`, short name `vp`),
  annotated `helm.sh/resource-policy: keep` so `helm uninstall` never
  deletes a project mid-`BUILD` along with it. Set
  `operator.installCRD=false` if another release already owns the CRD.
- a `ClusterRole` scoped to `vibeyprojects`/`vibeyprojects/status`
  (`list, watch, get, patch, update` — deliberately no `delete`) plus the
  `events` and kopf peering permissions it needs to run.
- a single-replica operator Deployment (`kind: Recreate`; two operators
  patching the same CR is a race with no upside at this scale). Set
  `operator.watchNamespace` to scope it to one namespace instead of the
  cluster.

Create a project by applying a CR instead of `vibey new`:

```yaml
apiVersion: vibey.dev/v1alpha1
kind: VibeyProject
metadata:
  name: demo
spec:
  repo: /work/demo
  maxCycles: 10
  maxCycleDollars: 25
  engines: [claudeloop]
  answers:
    some-gate-id: { choice: "yes" }
```

```bash
kubectl apply -n vibey -f vibeyproject.yaml
kubectl get vibeyprojects -n vibey
```

The operator creates the project on first reconcile, then re-reconciles
every 15s: it applies any new `spec.answers` through the same gate-answer
service `vibey answer` calls (a key naming an already-answered gate is
recorded in `status.ignoredAnswers`, not treated as an error), and writes
`status.phase`, `status.cycle`, `status.openGates`, and `Ready`/`Parked`
conditions — visible via `kubectl get vibeyprojects` and
`kubectl describe`. It never deletes a project, so removing the CR does
not remove the underlying project or its data.

## Troubleshooting

**`helm upgrade` fails with `lookup <release>-postgres ... no such host`.**
You are on a chart older than the DSN fix. KEDA's operator runs in its own
namespace and dials Postgres itself, so the DSN must be fully qualified —
a bare Service name resolves only from inside the release namespace, which
is why the worker was fine and the autoscaler was not. Set
`clusterDomain` if your cluster does not use `cluster.local`.

**Deployment shows `0/0` but pods are still `Terminating` and working.**
The worker is ignoring SIGTERM — you are running an image built before the
drain landed. Rebuild. This state is deceptive: `kubectl` reports capacity
released while the pods still hold CPU, memory, and Postgres connections.

**`kubectl delete pod --force --grace-period=0` leaves workers running.**
Force delete removes the pod object without waiting for the container to
die, exactly as its warning says. The container keeps running, keeps its
database connections, and **keeps claiming jobs** — invisible to
`kubectl`, since the pod is gone from the API server. Check with:

```bash
kubectl exec -n vibey vibey-vibey-postgres-0 -- \
  psql -U vibey -d vibey -c \
  "SELECT client_addr, count(*) FROM pg_stat_activity
   WHERE datname='vibey' AND client_addr IS NOT NULL GROUP BY client_addr;"
```

Connections from addresses with no corresponding pod are orphans; kill
them at the container runtime (`docker kill` inside `minikube docker-env`).
Prefer a normal delete — the drain makes it fast.

**Workers scale up but claim nothing.** The scaler counts claimable jobs
across *all* projects, while the worker Deployment binds to one. Work in
another project will scale workers that cannot claim it.

## Values worth knowing

| Value | Default | Why |
|---|---|---|
| `worker.terminationGracePeriodSeconds` | `7200` | ceiling for one long in-flight turn |
| `worker.waitForProjectSeconds` | `15` | park instead of restart-looping |
| `worker.parallelism` | `2` | concurrent job loops per pod |
| `worker.project` | `""` | **set this**; empty binds to the newest project |
| `keda.minReplicas` / `maxReplicas` | `0` / `4` | scale to zero when idle |
| `keda.cooldownPeriod` | `300` | delay before deactivating to zero |
| `clusterDomain` | `cluster.local` | only change on a custom `--service-dns-domain` |
| `postgres.enabled` | `true` | dev only; use `dsn.existingSecret` for managed |
| `operator.enabled` | `false` | install the kopf `VibeyProject` operator |
| `operator.watchNamespace` | `""` | empty watches cluster-wide |
| `operator.installCRD` | `true` | disable if another release already owns the CRD |
