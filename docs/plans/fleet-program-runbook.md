# Fleet Program Runbook — vibey + the four *loop runners

> **This document is an executable plan.** It is written to be handed to
> `claudeloop run` as the plan file for an unattended session. Task ordering is
> the §Sequencing table at the bottom; work the phases in order, and do not start
> a later phase while an earlier one is red.
>
> **Definition of done for the whole runbook:** every repo green on
> `ruff check`, `ruff format --check`, `mypy --strict`, `lint-imports`, `bandit`,
> `pip-audit`, and **100% coverage on each of the four layers separately**, with
> those floors enforced in CI; the seven surfaces present in all five repos; and
> every repo publishable to TestPyPI and then PyPI.
>
> **Working rules for the session:**
> - Never write outside the worktree you were started in. Pass `--cwd` explicitly
>   to every subcommand that takes one.
> - One phase per branch, one PR per phase. Do not batch unrelated phases.
> - Measure coverage with a fresh data file every time (`rm -f .coverage*` or
>   `COVERAGE_FILE=$(mktemp)`); accumulated data silently inflates the number.
> - Before claiming a layer is at 100%, re-run it once with `HOME=$(mktemp -d)`.
>   Tests that only pass because of files on the developer's machine are the
>   single most common false green in this fleet.
> - If a required check cannot be made to pass, stop and leave the PR open with
>   an explanation. Do not weaken a gate, delete a test, or add a coverage
>   exclusion to get to green.
> - End your final message with **your runner's done marker** — and only when the
>   definition of done above is met in full. The marker differs per runner:
>   `CLAUDELOOP_TASK_FULLY_COMPLETE`, `AGYLOOP_TASK_FULLY_COMPLETE`,
>   `CURSORLOOP_TASK_FULLY_COMPLETE`, `CODEXLOOP_TASK_FULLY_COMPLETE`. Each
>   runner injects its own instruction into the seed prompt; follow that one.

## Context

Five repos: `vibey` (orchestrator) and four autonomous session runners `claudeloop`,
`codexloop`, `cursorloop`, `agyloop`. The goal is a system a non-technical person can
drive end to end, that survives rate limits and credit exhaustion without losing work,
enforces enterprise engineering standards on what it builds, and ships publicly.

**This revision** records what has actually landed, switches execution to
claudeloop-driven autonomy, and adds five new capabilities plus a seven-surface
requirement per repo.

### Verified current state (measured, not assumed)

All five on `develop`, in sync with origin, CI green.

| | vibey | claudeloop | agyloop | cursorloop | codexloop |
|---|---|---|---|---|---|
| `application/interfaces/` | ✅ 12 | ✅ 8 | ✅ 8 | ✅ 7 | ✅ 9 |
| `domain/verbosity.py` + `-v/-vv/-vvv` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `domain/forecast.py` (capacity) | n/a | ✅ | ✅ | ✅ | ✅ |
| `domain/handoff_marker.py` | n/a | ✅ | ✅ | ✅ | ✅ |
| `WindDownAndFinish` | n/a | ✅ | ✅ | ✅ | ✅ |
| `WindDownCommand` + `wind-down` CLI | n/a | ✅ | ❌ | ❌ | ❌ |
| marker **read** path (exit 75) | n/a | ✅ | ❌ | ❌ | ❌ |
| `run --run-id` | n/a | ✅ | ✅ | ✅ | ✅ |
| coverage: domain/app/infra/cli | 100/100/**96**/**77** | 100/100/**63**/**43** | **99/97/75/81** | 100/100/100/100 | 100/100/100/100 |
| CI coverage floor | domain 100, project 90 | domain+app 100; **rest `--cov-fail-under=0`** | **none** | 4× 100 | 4× 100 |
| OS × Python in CI | ubuntu × 3.12 | ubuntu × 3.10–3.13 | ubuntu × 3.12–3.13 | ubuntu × 3.12–3.13 | **ubuntu+macos** × 3.12–3.13 |

vibey has no `domain/loop.py`, `domain/control.py` or `application/runner.py` — it is the
orchestrator, not a runner. The wind-down half is architecturally n/a there.

### Defects found in the audit, to fix as part of this work

1. **claudeloop's "full suite" CI step gates nothing** — `pytest --cov-report=term-missing
   --cov-fail-under=0` with no `--cov=` source. Its 63%/43% is entirely ungated.
2. **agyloop enforces no coverage at all**, and `pytest-cov` is undeclared in its `[dev]`
   extra — a clean `pip install -e ".[dev]"` in CI would not have it.
3. **codexloop has an intermittent test failure**, ~1-in-6, not reproduced under repeat
   runs. Its CI runs pytest 4× per matrix cell × 8 cells, so it will surface.
4. **agyloop `develop` and `main` have diverged** (2 commits in `main` absent from
   `develop`). cursorloop/codexloop local `main` are stale; claudeloop's local `main` has
   no upstream.
5. `uv.lock` untracked in claudeloop/cursorloop/codexloop — commit or ignore, consistently.
6. **vibey's `apply_third_party_level` does not exist** — the logic is inlined in
   `configure_logging`, inconsistent with the other four.

---

## Execution model: claudeloop drives the remaining work

The runbook from here is executed **by claudeloop**, not by hand.

- **Worktree-isolated.** Every run gets its own `git worktree` off `develop`, never the
  primary checkout. This is the direct fix for the incident where a `resume` defaulted its
  cwd to the live repo and auto-committed uncommitted work. Every invocation passes an
  explicit `--cwd <worktree>` on **every** subcommand, not just `run`.
- **PR + auto-merge on green.** Each run pushes its branch, opens a PR, and merges when
  every required check passes. **A passing CI is the only thing between a bad plan and
  `develop`** — which is why §Coverage gates at 100% *first*, before autonomy is turned on.
- **Guardrails that must be in place before the first autonomous run:**
  - branch protection already enforces PR + all checks (done; bypass for owner + Cursor app)
  - `--wind-down-at` enabled so a run hands off rather than dying mid-task
  - `--max-dollars` / `--max-turns` per run, and `[credits] ceiling_usd`
  - the repo's own scope guard: no writes outside the worktree
  - a run that cannot reach green does **not** merge; it parks the PR for a human

**Ordering constraint:** claudeloop cannot autonomously merge anything into claudeloop
until claudeloop's own coverage reaches 100% (§Coverage). So the coverage work is
hand-driven or worktree-driven first, then autonomy is enabled fleet-wide.

---

## Coverage: gate at 100% now

Chosen deliberately over ratcheting: floors go to **100% on every layer in every repo
immediately**, and PRs that do not meet them do not merge.

- **All five repos**, CI: one `--cov-fail-under=100` step **per layer** (domain,
  application, infrastructure, cli). Per layer, not aggregate — a blanket number lets a
  well-tested domain hide an untested adapter, and pytest-cov unions `--cov` scopes within
  one invocation, so each floor needs its own run.
- Branch coverage on everywhere (vibey and agyloop currently measure statements only).
- Add `pytest-cov` to agyloop's `[dev]` extra.
- Replace claudeloop's no-op step.
- **Consequence, accepted:** claudeloop's ~1,400 uncovered statements block every
  claudeloop PR until closed. That work is therefore first in the queue.

The codexloop push already proved what this buys: the gap between 99% and 100% was
entirely **tests that passed only on my machine** — `~/.codex/auth.json` existing, a
rollout directory existing, macOS resolving `TMPDIR` through a symlink, and an `os.walk`
order that isn't guaranteed. Expect the same class of finding in claudeloop's 1,400.

Run coverage with a fresh data file every time (`COVERAGE_FILE=<tmp>` or `rm -f
.coverage*`); accumulated data silently inflates the number.

---

## Wave 1 remainder

### 1.4d Finish the soft stop (agyloop, cursorloop, codexloop)

claudeloop is the reference. Each of the other three needs:
- `WindDownCommand` in `domain/control.py`, outranked by `StopCommand` in `stop_outranks`.
  Held, not dropped, when it arrives mid-turn — discarding it makes the command depend on
  poll timing.
- inbox payload round-trip in `infrastructure/control.py`.
- `<loop> wind-down [--run-id] [--reason]` CLI + `bootstrap_ops.enqueue_wind_down` +
  `request_wind_down` use case.
- the **marker read path**: `rundir.write_handoff_marker` (tmp→`os.replace`), and
  `run` exiting **75** with the marker path echoed. Today three repos write a marker
  nothing consumes.
- codexloop additionally: extract `_finish_wound_down` from the inline `case
  WindDownAndFinish()` at `application/runner.py:250`.
- tri-state `_sleep_interruptible` (`None | "stop" | "wind_down"`) so a wind-down breaks an
  in-progress capacity wait. **This is what makes "rotate when the window wait starts"
  work**, and it is the last dependency vibey's rotation needs.

### 1.3 TUI: full conversation, live, hotkeys

claudeloop's `infrastructure/stream_ui/app.py` is the reference (two `RichLog` panes,
header/thinking bars, 5 bindings, 10 Hz live / 5 Hz tail / 20 Hz replay, delta dedupe).
Port to the other three; add `f` follow-toggle, `/` filter, and an events pane fed by
`events.jsonl`. Per-repo prerequisites: agyloop's runner must actually emit
`chatter.delta`/`chatter.tool` (its UI already parses events the runner never produces);
codexloop wire `JsonlParser` → `chatter.*`; cursorloop replace the one-shot buffer replay
with a live tail. vibey: `ChatPanel` tailing the active engine via the existing
`EngineAdapter.tail`, `LISTEN vibey_job_ready` instead of polling, fix the inert
`_state_fetcher`, and gate-answering bindings.

### 1.5 `credits`

`<loop> credits` reads balance/limits/usage; `credits add --usd N` raises the vendor spend
limit bounded by `[credits] ceiling_usd`. No vendor sells credits over an API — this
raises caps and otherwise notifies + parks. codexloop's real `capacity` command is the
model; cursorloop's `usage` stub gets implemented.

---

## Wave 1.7 — seven surfaces, every repo (NEW)

Every repo — all five — exposes the same seven surfaces. (You said six; you listed seven.)

| surface | state today | work |
|---|---|---|
| **cli** | ✅ all five | — |
| **tui** | claudeloop only real | §1.3 |
| **api** | ❌ none | HTTP (FastAPI) + SSE event stream, `<pkg> serve --port --token`, loopback-bound by default. codexloop bans `fastapi` in its domain-purity contract — the ban stays, the dep lives in `infrastructure/` |
| **mcp** | ❌ none | `infrastructure/mcp/server.py` exposing run/resume/stop/wind_down/prompt/status/capacity/credits/watch — a thin binding over the existing `bootstrap_ops`, which already backs every control-plane CLI command. `<pkg> mcp serve` |
| **webhook** | vibey has an unwired `notify/webhook.py` | outbound emitter for run lifecycle, capacity, wind-down, completion. HMAC-signed over the exact bytes posted (vibey's already is) |
| **sdk** | ❌ none | **both**: (a) in-process library — a stable, documented, `py.typed`, semver'd `from <pkg> import Runner` surface so the runner embeds without shelling out; (b) a generated typed client from the HTTP API's OpenAPI spec for out-of-process callers. Reuse each repo's existing generated-surface + committed-baseline drift pattern (`infrastructure/api/introspect.py` + `surface_baseline.json`) so the SDK cannot silently diverge |
| **openclaw** | ❌ none | `openclaw/` per repo: `SOUL.md` + skills + a channel config pointing at the MCP/HTTP surface. Behind `[openclaw] enabled = true`, token auth, loopback-only — OpenClaw has a substantial published attack-surface literature |

The API/MCP/SDK/webhook surfaces are four renderings of **one operation set**. Define that
set once per repo in `application/interfaces/`, and have all four bind to it — otherwise
they drift and only the CLI stays correct.

---

## Wave 1.8 — five new capabilities (NEW)

### 1.8.1 GitHub: PR management + remote-branch deep scan

Today: `claudeloop/infrastructure/github_import.py` is the **only** GitHub client in any
repo — one endpoint (`repos/{o}/{r}/issues/{n}`), with a two-tier `gh api` →
`urllib`+`GITHUB_TOKEN` fallback that is a near-drop-in template for more. **No repo has
any PR handling, and none fetches a remote branch** — `resources/adapter.py:73-96` records
`{owner, repo, ref}` into `github.json` and reads not one byte.

- Generalize into a `GitHubClient` port + adapter: `gh api <path>` with pagination, the
  urllib fallback, and an injectable transport (copy agyloop's `HttpTransport` /
  `UrllibTransport` / `_FakeTransport` seam — the cleanest in the fleet).
- PR management: list/create/review/merge, checks status, branch-protection read.
- **Remote-branch deep scan**: fetch a ref into a scratch worktree via vibey's existing
  `CleanGitEnvSubprocessExecutor` + `worktree_manager.create(item_id, base_ref)` (which
  already accepts an arbitrary base ref), then run §1.8.2 over it. No shell, no
  `shell=True`, and the fetch is bounded by the existing scope guard.

### 1.8.2 Deep scan of local code

Today: **no repo imports `ast` or walks a source tree.** The nearest things are
subprocess linter runners and SDK object-tree introspection.

- New `application/interfaces/codescan.py` — a `CodeScanner` port returning a
  `ScanReport` shaped like the existing `ConformanceReport` (named checks, each
  `(name, ok, detail)`, degrading rather than crashing).
- Adapter composes: (a) an AST/`os.walk` inventory bounded by `MutationScope`;
  (b) the existing `SubprocessAutomatedReviewRunner` for ruff/bandit/mypy — **and fixes
  its current behaviour of discarding findings detail unless the exit code is non-zero**;
  (c) the standards-pack checks from §2.3 (interfaces present, onion respected, coverage
  floors, Azure quirks in any IaC).
- **Wire it into DESIGN.** Today `ClaudeLoopDesignProvider.research()` explicitly instructs
  *"Do not inspect repository files"* — DESIGN is web-research + interview only, with zero
  repo inspection by construction. Add a `CodeScanner` sibling to `ResearchProvider` so a
  brownfield project starts from facts about its own code.

### 1.8.3 Automated tests for CI/CD runners

Today: **nothing parses or asserts on workflow YAML in any repo**, and no repo checks
that CI job names match what branch protection requires. That gap is exactly what bit
codexloop — its ruleset required claudeloop's job names, so every PR was blocked forever.

- A test per repo that parses `.github/workflows/*.yml` and asserts:
  - every job name required by the repo's rulesets **exists in the workflow**, and vice
    versa — matrix-expanded names included (`pytest (py3.12)`, `Gates py3.12 /
    ubuntu-latest`), which is precisely where the drift lives;
  - the coverage floor steps exist, one per layer, at 100%;
  - the publish workflow `needs:` the test job (today it does not — see §3.4).
- Needs a YAML parser in four repos (only cursorloop has `pyyaml`); add to `[dev]` only.
- Model: cursorloop's `api-drift.yml` + `tests/infrastructure/test_api_drift.py` — a
  scheduled job whose entire purpose is to fail on drift.

### 1.8.4 Automated fakes for Azure/AKS

Today the Azure port is small and complete (`AzureClientPort`, 4 methods, 3 DTOs), and
there are doubles in **both** src and tests — but three independent `FakeAzureClient`
classes exist across test files, `bootstrap.py` has **no Azure wiring at all**, and
`AzureCliAdapter` never actually invokes `az` (there is no subprocess call in the whole
azure package). There is **no AKS/kubectl/helm code anywhere** — `TopologyConfig.service_type`
is `container_app`; AKS appears only in ADR prose.

- Promote the best existing double (`tests/application/test_deploy_execute_handler.py:87`
  — it already models per-step failure and degradation) into `tests/fakes/azure.py`, and
  delete the three copies.
- Extend it to model Azure **failure semantics** properly: throttling, quota,
  `Conflict`/`InUse`, eventual consistency on delete, and partial `what-if` — today the
  only failure is a raised `RuntimeError`.
- Wire Azure into `bootstrap.py` so the deploy stack exists outside tests.
- AKS: add it as a real `service_type` with its own fake, or record an ADR that Container
  Apps is the target and AKS is out of scope. The plan currently promises AKS in the
  standards pack while no code models it.

### 1.8.5 Automated fakes for every other third-party surface

Surfaces with **no double anywhere**: the `anthropic` SDK client object, the `openai` SDK
client object, **`asyncpg`/Postgres**, the GitHub HTTP/`gh` surface, and agyloop's
`google.antigravity` agent in `src/` (agyloop is the only loop with no shipped
`scripted.py`).

- **vibey is the outlier and the priority.** Its `tests/application/fakes.py` has three
  doubles; the other ~35 are duplicated inline across **27 test files** (`FakeLedger` ×7,
  `FakeProjectRepo` ×5, `FakeAzureClient` ×3 …) against ~40 declared ports. Consolidate
  into `tests/fakes/`, one per port.
- Adopt cursorloop's `test_fakes_satisfy_ports.py` in all five: `isinstance(FakeX(),
  PortX)` for every fake. Protocol conformance is structural, so a drifted fake otherwise
  fails silently. **Only cursorloop has this test.**
- Add the missing doubles: an `anthropic`/`openai` client double (or an injectable client
  factory — `providers.py::PROVIDER_FACTORIES` is already the seam), an agyloop
  `src/.../agent/scripted.py` to match its three siblings, and a GitHub transport double
  (§1.8.1 makes the seam injectable).
- **Postgres**: keep the real database for `tests/live`, but the port-level fakes must be
  proven equivalent — `tests/contracts/test_*_contract.py` parameterized over
  `[fake, postgres]`. Nothing today proves `FakeJobRepository.defer` behaves like
  `PostgresJobRepository.defer`, and untrustworthy fakes make faked mode worthless.
- Reuse the two best existing patterns: codexloop's `tests/shim/fake_codex.py` +
  `fake_appserver.py` (real executable process fakes — the only ones in the fleet) and
  cursorloop's `tests/fixtures/sdk_payloads.py`.

---

## Wave 2 — Vibey orchestration

Unchanged from the previous revision except where noted:

- **2.1 Live engine adapters + rotation wiring** — one parameterized `LoopProcessAdapter`
  (not four), `loop_events.py::LOOP_EVENT_MAP` (without it `tailer.translate_event` raises
  on line one of any real run), `RotationCursorRepository`, `EngineSelector` (first caller
  of `domain/rotation.py`), `EngineHealthService`, `rotation_handoff.py`. A wind-down
  settles as `Success` — not `Failure` (burns the ladder, opens a circuit on a healthy
  engine) and not `Defer` (re-runs on the exhausted engine). Livelock bound: 3 wind-downs
  per work item, then `--no-wind-down`.
- **2.2 Engine specialization** via existing `Capability` + `affinity_factor` — zero lines
  change in `rotation.py`.
- **2.3 Standards pack + skills + research** — `ProvisionSpec.non_negotiables` is a field
  with no config key and no population today, and the BUILD prompt carries no standards at
  all.
- **2.4 Adaptive interactive sessions** — vibey has *no* interactive TTY prompting today.
- **2.5 Test harness** — two-mode (faked/live), unwind ledger, post-prod run in Phase ⑤.

### 2.6 Rich intake for the initial prompt (NEW)

The prompt that starts a vibey job must accept everything a normal AI prompt accepts.
Effort stays **high/standard** as today — this widens *inputs*, not effort.

- `vibey new` / `vibey design` gain: `--attach PATH` (repeatable, files and directories),
  `--add-folder`, `--from-github OWNER/REPO[@REF]` (via §1.8.1, actually fetched now),
  `--import-issue`, `--web-search`, `--deep-research`, `--skill`/`--plugin`,
  `--connector`.
- These map onto surfaces the runners **already have** — claudeloop's `run` already takes
  `--attach/--add-folder/--from-github/--import-issue/--web-search/--deep-research/--skill/
  --plugin/--connector`, and `RunResourceStore` + `ResourcePortAdapter.gateway_payload()`
  already carry them into the session. vibey's job is to accept them at intake, persist
  them on the project, and pass them through `RunSpec` → `build_argv` to whichever engine
  rotation picks.
- Parity item: the three other loops need the same resource flags (§2.3 already lists
  `--skill`/`--plugin`/`--append-system-prompt`).
- Attachments and fetched repos are **inputs to the scan** in §1.8.2, so DESIGN reasons
  about real artifacts rather than a description of them.

---

## Wave 3 — Docs, publish, governance

- **3.1 vibey public surface** — mkdocs + Pages, community health files, CODEOWNERS,
  dependabot, CHANGELOG. **Stays private and free until it is genuinely publishable**;
  branch protection on a private repo needs GitHub Pro, so vibey is ungated until then.
- **3.2 Docs refresh, all five** — every new surface from Waves 1–2, plus ADRs for each
  hard call.
- **3.3 Branch protection** — done: all 12 rulesets carry bypass for `RepositoryRole:5`
  (owner, and therefore Claude Code / Codex CLI / Antigravity CLI, which share those
  credentials) and `Integration:1210556` (the Cursor app); everyone else needs PR +
  1 review + all checks. If Codex/Antigravity ever need to be revocable independently,
  they need their own GitHub Apps — today revoking one revokes all.
- **3.4 Close the publish hole** — `publish-to-pypi.yml` is `build → publish` with **no
  test job** in every repo. Insert a `harness` job both `needs:`, running the full gate
  set plus `pytest -m live` and the unwind residue check.
- **3.5 Publish order** — TestPyPI → smoke-install into a clean venv → PyPI, per repo.
  vibey's live local harness must be green before vibey publishes at all.

---

## Verification

```bash
# every repo — the gate that must pass before anything merges
rm -f .coverage*                      # accumulated data silently inflates the number
for L in domain application infrastructure cli; do
  uv run pytest -q -p no:cacheprovider --cov=<pkg>.$L --cov-fail-under=100
done
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy --strict src/<pkg> && uv run lint-imports
uv run bandit -q -r src/<pkg> && uv run pip-audit
HOME=$(mktemp -d) uv run pytest -q     # catches tests that only pass on this machine
for i in 1 2 3 4 5; do uv run pytest -q; done   # codexloop's 1-in-6 flake

# Wave 1.4d
<loop> wind-down --run-id X --reason rotate     # exits 75, writes handoff.json
python -c "import json;d=json.load(open('runs/X/handoff.json'));[open(p) for p in
  (d['snapshot_path'],d['stop_summary_path']) if p]"   # every named artifact exists

# Wave 1.7 — seven surfaces
<pkg> --help && <pkg> run --stream-ui
<pkg> serve --port 8099 & curl -H "Authorization: Bearer $T" localhost:8099/runs
<pkg> mcp serve & npx @modelcontextprotocol/inspector
python -c "from <pkg> import Runner"            # in-process SDK imports
openclaw run --agent ./openclaw/SOUL.md          # drives a run end to end

# Wave 1.8
<pkg> scan --repo . --json                       # local deep scan
<pkg> scan --github OWNER/REPO@branch            # fetches a real ref, scans it
uv run pytest tests/ci/test_workflow_contract.py # job names == ruleset requirements
uv run pytest tests/fakes/test_port_parity.py    # every port has a conforming fake

# Wave 2
uv run pytest -m live                            # real pg + git + binaries, scripted models
vibey new --attach ./spec.pdf --from-github o/r@main --web-search --deep-research
vibey start                                      # onboarding on a fresh machine

# Wave 3
mkdocs build --strict && python -m build && twine check --strict dist/*
```

## Sequencing

| # | Scope | Blocks |
|---|---|---|
| A | **Coverage to 100% + gates, all five** (claudeloop's 1,400 stmts first), fix the six audit defects | autonomy, everything |
| B | 1.4d soft stop ×3, tri-state sleep | vibey rotation |
| C | Enable claudeloop autonomy (worktree + PR + auto-merge on green) | — |
| D | 1.3 TUI, 1.5 credits, 1.7 seven surfaces, 1.8 five capabilities | Wave 2 |
| E | Wave 2: adapters + rotation, standards, adaptive UX, rich intake, harness | Wave 3 |
| F | Wave 3: docs, publish gate, TestPyPI → PyPI, then vibey public | — |

---

## How this runbook is executed

`claudeloop` 0.5.5 runs this file unattended. The three things that make an
unattended run safe here are a **disposable worktree**, an explicit **`--cwd` on
every subcommand**, and **hard budget caps** — the runner will otherwise default
its working directory to wherever it was invoked, which is how an earlier session
committed unrelated work.

### Per-repo invocation

```bash
REPO=claudeloop                                   # or vibey|agyloop|cursorloop|codexloop
PHASE=a-coverage                                  # one phase per run, per the Sequencing table
WT=$HOME/.cache/fleet-worktrees/$REPO-$PHASE

cd ~/git/$REPO
git fetch -q origin
git worktree add -B "chore/$PHASE" "$WT" origin/develop

claudeloop run ~/git/vibey/docs/plans/fleet-program-runbook.md \
  --cwd "$WT" \
  --run-id "$REPO-$PHASE" \
  --add-folder ~/git/vibey/docs/plans \
  --skill software-architecture --skill quality-engineering \
  --skill security-first-dev \
  --web-search \
  --max-turns 400 --max-dollars 40 --max-wait 21600 \
  --permission-mode acceptEdits \
  --done-marker CLAUDELOOP_TASK_FULLY_COMPLETE \
  --log-level INFO --log-file "$WT/.claudeloop/run.log" \
  --stream-ui
```

### Running it with agyloop instead

agyloop 0.1.0 has a different surface. The differences are not cosmetic — three
of them are gaps this very runbook exists to close, so a run driven by agyloop
is working with fewer inputs than one driven by claudeloop:

| claudeloop | agyloop | note |
|---|---|---|
| `--add-folder` | `--add-dir` | same idea, different spelling |
| `--permission-mode` | `--safe` / `--scoped` / `--yolo` / `--strict-autonomy` | posture is a set of flags, not one enum |
| `--done-marker` | *(none)* | fixed at `AGYLOOP_TASK_FULLY_COMPLETE` |
| `--stream-ui` | *(none)* | use `agyloop watch --stream`; the TUI is one pane with no hotkeys until §1.3 |
| `--skill` / `--plugin` | *(none)* | **§2.3 gap** — no vibe-engineering-skills injection |
| `--web-search` / `--deep-research` | *(none)* | **§2.6 gap** — no research inputs |
| `--attach` / `--from-github` / `--import-issue` | *(none)* | **§2.6 gap** — no attachments or repo intake |
| `wind-down` | *(none)* | **§1.4d gap.** `agyloop unwind` is unrelated — it rolls back git save points |
| — | `--gateway sdk\|cli` | transport choice; `sdk` is the default |
| — | `--no-probe` | skip the preflight capacity probe |
| — | `--ramp N` | pace the first N turns against acceleration 429s |
| — | `--max-tokens` | agyloop meters tokens as well as dollars |

```bash
REPO=agyloop
PHASE=a-coverage
WT=$HOME/.cache/fleet-worktrees/$REPO-$PHASE

cd ~/git/$REPO
git fetch -q origin
git worktree add -B "chore/$PHASE" "$WT" origin/develop

agyloop -v --log-file "$WT/.agyloop/run.log" \
  run ~/git/vibey/docs/plans/fleet-program-runbook.md \
  --cwd "$WT" \
  --run-id "$REPO-$PHASE" \
  --add-dir ~/git/vibey/docs/plans \
  --gateway sdk \
  --preset high \
  --scoped \
  --ramp 3 \
  --max-turns 400 --max-dollars 40 --max-wait 21600
```

Verbosity is a **root** flag on agyloop, so `-v` comes before `run`, not after.
`--scoped` keeps workspace and destructive denies in place without `allow_all`;
prefer it to `--yolo` for an unattended run. `--ramp 3` paces the opening turns,
which is what the acceleration 429s want.

If the Antigravity SDK harness misbehaves, `--gateway cli` now selects a CLI
transport **and** a matching CLI capacity probe — before that fix the probe
booted the SDK harness regardless and died with
`Failed to read length from stdout`. `--no-probe` skips the preflight entirely.

Steering agyloop:

```bash
agyloop watch  --run-id "$REPO-$PHASE" --cwd "$WT" --stream
agyloop logs   --run-id "$REPO-$PHASE" --cwd "$WT" --follow --chatter
agyloop status --run-id "$REPO-$PHASE" --cwd "$WT"
agyloop prompt "finish the CLI layer first" --at-break --run-id "$REPO-$PHASE" --cwd "$WT"
agyloop stop   --run-id "$REPO-$PHASE" --cwd "$WT"        # no soft stop until §1.4d
```

Watch a run already in flight, or replay one:

```bash
claudeloop watch --run-id "$REPO-$PHASE" --cwd "$WT" --stream     # live, full chat
claudeloop watch --run-id "$REPO-$PHASE" --cwd "$WT" --replay --speed 4
claudeloop logs  --run-id "$REPO-$PHASE" --cwd "$WT" --follow --chatter full
claudeloop status --run-id "$REPO-$PHASE" --cwd "$WT"
```

Steer or stop it without killing it:

```bash
claudeloop prompt "reprioritise: finish the CLI layer first" --at-break \
  --run-id "$REPO-$PHASE" --cwd "$WT"
claudeloop wind-down --run-id "$REPO-$PHASE" --cwd "$WT" --reason rotate   # soft: exits 75
claudeloop stop      --run-id "$REPO-$PHASE" --cwd "$WT"                   # hard: exits 130
```

`wind-down` is the one to reach for when the run should hand off rather than
die: it lets the turn in flight finish, writes `runs/<id>/handoff.json` naming
every artifact it produced, and exits **75** so a supervisor can tell "resume me
elsewhere" from "this failed".

### Exit codes

| code | meaning | next step |
|---|---|---|
| 0 | done marker emitted, work complete | merge the PR |
| 75 | wound down on purpose | resume, or hand the branch to another runner |
| 130 | operator stopped it | read `stop-summary.md`, then resume |
| 1 | failed | read the log; do not merge |

### Landing the work

Branch protection requires a PR and all checks; the owner's credentials bypass
the review requirement, so the run can open and merge its own PR once CI is
green. It must never merge red.

```bash
cd "$WT"
gh pr create --base develop --fill
gh pr checks --watch
gh pr merge --squash --delete-branch     # only after every check passes
cd ~/git/$REPO && git worktree remove "$WT"
```

### Cleanup

```bash
git worktree list
git worktree prune
```
