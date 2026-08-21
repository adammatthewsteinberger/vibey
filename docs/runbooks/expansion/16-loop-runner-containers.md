# Runbook: loop-runner containers — each *loop repo ships its own k8s

## Goal

Each of the four session runners — `claudeloop`, `codexloop`,
`cursorloop`, `agyloop` — becomes independently deployable on Kubernetes:
its own image, its own Helm chart, its own multi-arch CI publish, its own
docs. Two consumers are served by the same artifacts:

1. **Standalone.** Each runner is a separately published tool with its own
   users. `helm install claudeloop` should run an autonomous session in a
   cluster without vibey anywhere in the picture.
2. **The `vibey-engines` image.** Runbook 05's design calls for a second
   image layering the runners on top of the vibey base. That image
   consumes what this workstream produces instead of reinventing four
   installs.

## Current state (verified 2026-08-21)

Measured directly in the four working copies, not assumed:

| Repo | Version | Python | Console script | Vendor binary |
|---|---|---|---|---|
| `claudeloop` | 0.6.1 | >=3.10 | `claudeloop` | `claude` |
| `codexloop` | 0.3.1 | >=3.12 | `codexloop` | `codex` |
| `cursorloop` | 0.6.0 | >=3.12 | `cursorloop` | `cursor-sdk-bridge` |
| `agyloop` | 0.4.1 | >=3.12 | `agyloop` | `agy` |

- All four are on `develop`, share vibey's onion layout
  (`domain/application/infrastructure/cli`), and build with hatchling.
- **None has a `deploy/` directory.** Nothing is containerized anywhere.
- CI is uniform: `ci.yml`, `docs.yml`, `publish-*.yml`,
  `release-please.yml` (plus `api-drift.yml` in cursorloop). No image job
  in any repo.
- **API-key auth already exists in all four** — `ANTHROPIC_API_KEY` /
  `ANTHROPIC_AUTH_TOKEN`, `OPENAI_API_KEY` / `AZURE_OPENAI_API_KEY`,
  `CURSOR_API_KEY`, `GOOGLE_API_KEY` / `GEMINI_API_KEY` / ADC — each with
  a `doctor_env` check behind it. Runbook 05's work item 1 is closer to a
  verification job than an implementation job. **This is the single
  biggest de-risking fact in this runbook.**
- vibey invokes runners as **subprocess CLIs**
  (`infrastructure/engines/loop_process_adapter.py`), and the current
  vibey image ships **no engines at all** — nothing in-cluster can run a
  real engine today.

### The fact that shapes everything

Only `agyloop` selects its lane at runtime (`--gateway sdk|cli`, with
`gateway: str = "sdk"` as the default). In `claudeloop` and `cursorloop`,
`bootstrap.py` hardwires the **agent** gateway — `ClaudeAgentGateway`,
`CursorAgentGateway` from `infrastructure/agent/gateway` — for the
autonomous loop. Their `infrastructure/api/` trees (`gateway.py`,
`providers.py`, `binder.py`, `introspect.py`, `surface_baseline.json`) are
a *separate command surface* — claudeloop's "full Anthropic SDK CLI" — not
a lane the loop can be pointed at.

**So for three of four runners the autonomous loop currently requires the
vendor agent binary on PATH.** That decides image size, base image, and
whether a container can authenticate at all — vendor CLIs generally assume
an interactive TTY login, which does not exist in a cluster.

Do not plan the images until this is settled per repo. It is Phase 0.

## Design

### Phase 0 — the lane spike (blocks everything; one spike per repo)

For each runner, answer with a running process, not a code read: *can the
autonomous loop complete a real session with no vendor binary on PATH,
authenticated only by an API key from the environment?*

- **agyloop** — likely already yes (`--gateway sdk`). Confirm, then it is
  the reference implementation the other three copy.
- **claudeloop / cursorloop / codexloop** — if no, the deliverable is a
  runner-side work item in that repo: promote the API gateway to a lane
  the loop can select, mirroring agyloop's `--gateway`. That is a genuine
  feature in someone else's repo, sized separately, and it must land
  before that runner's image is worth building.

The spike's output per repo is one of two verdicts, recorded in the repo:

- **SDK lane works** → slim image, `python:3.12-slim`, no Node, no vendor
  CLI, no TTY problem. This is the container-native path and the one to
  fight for.
- **CLI lane only** → the image must carry the vendor binary (Node +
  npm-installed agent CLI for `claude`/`codex`; a proprietary installer
  for `cursor-sdk-bridge`/`agy`), and headless API-key auth for that
  binary must be proven before anything else is built. Vendor licensing
  for redistribution inside an image is a real question here, not a
  formality — answer it in the spike, not after publishing.

### Per-repo artifacts (identical shape in all four)

```
deploy/
  docker/Dockerfile          # two-stage, non-root, uid 10001
  helm/<runner>/
    Chart.yaml
    values.yaml
    templates/{_helpers.tpl,job.yaml,secret.yaml,rbac.yaml}
.github/workflows/image.yml  # multi-arch buildx -> ghcr.io
docs/kubernetes.md
```

1. **Dockerfile.** Copy vibey's two-stage pattern
   (`deploy/docker/Dockerfile`) — it is already load-bearing and its
   reasoning transfers exactly: the runtime layer carries no compiler and
   no package manager, because a compromised agent session inside the
   container should not find build tools waiting. Same `/app` WORKDIR in
   both stages for the editable-install path pointer. `git` is a genuine
   runtime dependency — these runners work in real worktrees.
   `ENTRYPOINT ["<runner>"]`, `CMD ["--help"]`: an image that silently
   starts a session when someone runs it to inspect the filesystem is a
   footgun. Note the Python floor differs — claudeloop allows 3.10, the
   others require 3.12; pin every image to 3.12 anyway so one base layer
   is shared and cached across all four.

2. **Chart: a Job, not a Deployment.** These are one-shot autonomous
   session runners, not servers — they start, work, and finish. A
   Deployment would restart a *successfully completed* session forever.
   `Job` with `backoffLimit: 0` and `restartPolicy: Never` is the honest
   shape; offer `CronJob` for scheduled runs. This is the sharpest
   divergence from vibey's chart and must not be copied from it blindly.

3. **Secrets.** API keys come from a Secret, never values.yaml — the same
   `engineAuth.existingSecret` convention vibey's chart already uses, so
   one Secret can serve a vibey worker and a standalone runner alike.

4. **Workspace.** A PVC for the repo under work, cloned via a deploy key
   mounted as a Secret. Reuse vibey's worktree PVC conventions.

5. **CI.** `docker/build-push-action` multi-arch (arm64 + amd64) to
   `ghcr.io/<owner>/<runner>`, tagged on release-please releases so image
   tags track the PyPI version already published. Do not invent a second
   versioning scheme.

### The `vibey-engines` image (this side)

Once the four images exist, `deploy/docker/Dockerfile.engines` layers the
runners onto the vibey base and vibey's chart grows an
`image.engines` value the worker Deployment can select. Prefer installing
the four **PyPI packages** into one image over `COPY --from` of four
images: one Python environment, one resolver run, no four-way base-image
skew. The per-repo images remain the standalone deliverable.

## Work items

1. Phase 0 lane spike × 4; record the verdict per repo (blocks 2–4).
2. Runner-side `--gateway` work in whichever repos the spike says need it.
3. Dockerfile × 4 + local `docker run <runner> doctor` green.
4. Helm chart × 4 (Job/CronJob shape) + minikube install per runner.
5. `image.yml` multi-arch CI publish × 4, wired to release-please tags.
6. `docs/kubernetes.md` × 4.
7. `Dockerfile.engines` + `image.engines` in vibey's chart.
8. One real greeter on minikube driven by a containerized engine — the
   first time vibey runs a live engine in-cluster.

## Verification

- `docker run --rm -e <KEY> <runner>:dev doctor` passes for all four.
- `helm install <runner>` on minikube → a scripted session reaches
  completion → Job `Complete`, pod exits 0, no restarts.
- One paid live session per runner in-cluster, API-key authenticated.
- vibey worker running the engines image selects a real engine and
  completes a BUILD job — verified against `vibey doctor --conformance`
  recording a real conformance, which today is empty in-cluster
  ("no recorded conformance for agyloop, claudeloop, codexloop,
  cursorloop" is the live warning from the running worker).

## Needs from operator

- LLM API keys for each vendor (the same set runbook 05 needs).
- A GHCR namespace (or other registry) and a token with `packages:write`.
- Deploy keys for any private repo a runner is pointed at.
- A decision on vendor-CLI redistribution if any repo lands on CLI-only.

## Risks

- **The spike may fail for a runner.** If a vendor's agent CLI cannot
  authenticate headlessly by API key, that runner is not clusterable this
  quarter regardless of how good its chart is. Better to learn it in a
  one-day spike than after four charts are written.
- **Four repos drift.** The chart shape must be copied deliberately, not
  by cargo cult — a Job here, a Deployment in vibey, for a stated reason.
  Consider a shared chart library only after all four exist and the
  duplication is measured, not before.
- **Python floor mismatch.** claudeloop's 3.10 floor tempts a second base
  image; resist it.
- **Coverage gates.** Each repo carries its own 100% floors. Runner-side
  `--gateway` work is real code in someone else's coverage budget, not a
  packaging change.
