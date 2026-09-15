# Runbook: loop-runner containers — each *loop repo ships its own k8s

> **Status (2026-09-15):** open. No Phase 0 lane spike is recorded for any
> runner. The runners are no longer separate repositories: all five
> (with qwenloop) are uv workspace members under `src/vibey_runners/`
> (imported with history 2026-09-10, ADR-0021). Only qwenloop has a
> Dockerfile, and it does not meet the contract below. The vibey image still
> ships no engines. Read "repo" below as "runner package in this repository".

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

## Current state (originally verified 2026-08-21; versions and layout updated 2026-09-15)

| Package | Path | Version | Python | Console script | Vendor binary |
|---|---|---|---|---|---|
| `claudeloop` | `src/vibey_runners/claude` | 0.8.0 | >=3.10 | `claudeloop` | `claude` |
| `codexloop` | `src/vibey_runners/codex` | 0.4.0 | >=3.12 | `codexloop` | `codex` |
| `cursorloop` | `src/vibey_runners/cursor` | 0.7.0 | >=3.12 | `cursorloop` | `cursor-sdk-bridge` |
| `agyloop` | `src/vibey_runners/agy` | 0.5.0 | >=3.12 | `agyloop` | `agy` |
| `qwenloop` | `src/vibey_runners/qwen` | 0.2.0 | >=3.12 | `qwenloop` | none (local llama.cpp / vLLM model) |

- All five are workspace members of this repository, share vibey's onion
  layout (`domain/application/infrastructure/cli`), and still publish to
  PyPI as their own projects.
- **Only qwenloop has a `deploy/` directory**
  (`src/vibey_runners/qwen/deploy/docker/Dockerfile`): two stages, but the
  runtime layer keeps `pip`, has no fixed uid, and uses the default
  `python:3.12-slim` base — it must be brought to the contract below.
- Each subtree still carries its old `.github/` tree, but only the root
  workflows run. The root CI `tools` matrix covers `vibey-gh`,
  `vibey-skills` and `vibey-bootstrap`; it has no runner entries and no
  runner image job. Releases are cut by `vibey-gh promote`
  (`chore(release): x.y.z` commits); release-please is retired
  (ADR-0028).
- **API-key auth already exists in the four hosted-model runners** —
  `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN`, `OPENAI_API_KEY` /
  `AZURE_OPENAI_API_KEY` / `CODEX_API_KEY`, `CURSOR_API_KEY`,
  `GOOGLE_API_KEY` / `GEMINI_API_KEY` / ADC (the same map
  `infrastructure/cluster_preflight.py` checks) — each with
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

qwenloop needs no vendor binary or API key, but it needs model weights in
the image or on a volume, and a GPU for the vLLM profile.

Do not plan the images until this is settled per runner. It is Phase 0.

## Design

### Phase 0 — the lane spike (blocks everything; one spike per repo)

For each runner, answer with a running process, not a code read: *can the
autonomous loop complete a real session with no vendor binary on PATH,
authenticated only by an API key from the environment?*

- **agyloop** — likely already yes (`--gateway sdk`). Confirm, then it is
  the reference implementation the other three copy.
- **claudeloop / cursorloop / codexloop** — if no, the deliverable is a
  runner-side work item in that runner's package: promote the API gateway
  to a lane the loop can select, mirroring agyloop's `--gateway`. That is
  a genuine feature, sized separately, and it must land
  before that runner's image is worth building.

The spike's output per runner is one of two verdicts, recorded in that
runner's docs:

- **SDK lane works** → slim image, `python:3.12-slim`, no Node, no vendor
  CLI, no TTY problem. This is the container-native path and the one to
  fight for.
- **CLI lane only** → the image must carry the vendor binary (Node +
  npm-installed agent CLI for `claude`/`codex`; a proprietary installer
  for `cursor-sdk-bridge`/`agy`), and headless API-key auth for that
  binary must be proven before anything else is built. Vendor licensing
  for redistribution inside an image is a real question here, not a
  formality — answer it in the spike, not after publishing.

### Per-runner artifacts (identical shape in all five)

```
src/vibey_runners/<runner>/
  deploy/
    docker/Dockerfile        # two-stage, non-root, uid 10001
    helm/<runner>/
      Chart.yaml
      values.yaml
      templates/{_helpers.tpl,job.yaml,secret.yaml,rbac.yaml}
  docs/kubernetes.md
.github/workflows/ci.yml     # root: one runner-matrix image job, multi-arch -> ghcr.io
```

1. **Dockerfile.** Copy vibey's two-stage pattern
   (`deploy/docker/Dockerfile`) — it is already load-bearing and its
   reasoning transfers exactly: the runtime layer carries no compiler and
   no package manager, because a compromised agent session inside the
   container should not find build tools waiting. Same `/app` WORKDIR in
   both stages for the editable-install path pointer. `git` is a genuine
   runtime dependency — these runners work in real worktrees.
   `ENTRYPOINT ["<runner>"]`, `CMD ["--help"]` (with tini as PID 1 when
   the runner must drain on SIGTERM, as vibey's image does — ADR-0026): an image that silently
   starts a session when someone runs it to inspect the filesystem is a
   footgun. Note the Python floor differs — claudeloop allows 3.10, the
   others require 3.12; pin every image to 3.12 anyway so one base layer
   is shared and cached across all five.

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

5. **CI.** A matrix entry in the root CI image job:
   `docker/build-push-action` multi-arch (arm64 + amd64) to
   `ghcr.io/the-vibey-project/<runner>`, tagged with the version
   `vibey-gh promote` releases so image tags track the PyPI version
   already published. Do not invent a second
   versioning scheme.

### The `vibey-engines` image (this side)

Once the runner images exist, `deploy/docker/Dockerfile.engines` layers
the runners onto the vibey base and vibey's chart grows an
`image.engines` value the worker Deployment can select. Prefer installing
the five **runner packages from the workspace tree** into one image —
the way vibey's Dockerfile already installs `vibey-skills` from
`src/vibey_tools/skills` — over `COPY --from` of five images: one Python
environment, one resolver run, no five-way base-image skew. The per-repo images remain the standalone deliverable.

## Work items

1. Phase 0 lane spike × 4 hosted-model runners, plus a weights-and-GPU
   spike for qwenloop; record the verdict per runner (blocks 2–4).
2. Runner-side `--gateway` work in whichever runners the spike says need it.
3. Dockerfile × 5 (qwenloop's rewritten to the contract) + local
   `docker run <runner> doctor` green.
4. Helm chart × 5 (Job/CronJob shape) + minikube install per runner.
5. Root CI runner-matrix image job, multi-arch, wired to `vibey-gh`
   promoted versions.
6. `docs/kubernetes.md` × 5.
7. `Dockerfile.engines` + `image.engines` in vibey's chart.
8. One real greeter on minikube driven by a containerized engine — the
   first time vibey runs a live engine in-cluster.

## Verification

- `docker run --rm -e <KEY> <runner>:dev doctor` passes for all five.
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
- A decision on vendor-CLI redistribution if any runner lands on CLI-only.
- For qwenloop: where model weights come from in-cluster (baked, volume,
  or pulled at start) and GPU node availability for the vLLM profile.

## Risks

- **The spike may fail for a runner.** If a vendor's agent CLI cannot
  authenticate headlessly by API key, that runner is not clusterable this
  quarter regardless of how good its chart is. Better to learn it in a
  one-day spike than after five charts are written.
- **Five runner packages drift.** The chart shape must be copied deliberately, not
  by cargo cult — a Job here, a Deployment in vibey, for a stated reason.
  Consider a shared chart library only after all five exist and the
  duplication is measured, not before.
- **Python floor mismatch.** claudeloop's 3.10 floor tempts a second base
  image; resist it.
- **Coverage gates.** Each runner keeps its own 100% floors after absorption
  (ADR-0022). Runner-side `--gateway` work is real code in that runner's
  coverage budget, not a packaging change.
