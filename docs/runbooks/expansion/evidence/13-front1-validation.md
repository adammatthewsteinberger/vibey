# Workstream 13 Front 1 — independent validation record

Verification of PR #70 (`7067b2a`) re-measured **on merged develop by the
operator's session**, not taken from the building engine's own evidence
file (`13-front1-before-after.md`). Every number below was produced by a
command run after the merge landed.

Machine: macOS (Darwin 25.6.0), 10 cores, 24 GB. Date: 2026-08-21.

## Results

| Criterion | Bar | Measured | Verdict |
|---|---|---|---|
| Suite wall time | ≤120 s must / ≤90 s target | 138 / 133 / 135 s (median **135 s**) | **DEVIATION** (accepted, see below) |
| Suite vs baseline | — | 383 s → 135 s (**2.8×**) | pass |
| AC-04 determinism | 0 differences over 3 runs | 3× identical `1375 passed, 2 xfailed` | pass |
| AC-06/07 unified coverage | 4 floors from 1 run | domain/application/infrastructure/cli all **100%** from one `.coverage` | pass |
| NFR-03 gate cost | exactly 1 suite execution | 1 pytest + 4 `coverage report` = **136 s** (was ~1530 s) — **11.3×** | pass |
| AC-09 CI step names | no removals | `Gate 4a–4d` names preserved verbatim; single instrumented run at ci.yml:65 | pass |
| AC-13 protected files | empty diff | empty | pass |
| AC-05 no test hiding | 0 new markers | 0 new `skip`/`xfail` | pass |
| AC-14 crash recovery | stale worker DB recreated | seeded `vibey_test_gw3`; run cleaned it up, no "already exists" failure | pass |
| NFR-09 cleanup hygiene | 0 leftover worker DBs | only `vibey_test` + `vibey_test_template` remain | pass |
| AC-03 isolation | per-worker DB, no sharing | conftest: advisory-locked template + `vibey_test_<worker_id>` clones | pass |

## Accepted deviation: suite wall time 135 s vs the ≤120 s "must"

Operator-accepted on 2026-08-21. Rationale:

- It is a **speed** shortfall, not a correctness one. Every correctness
  property the design worried about — determinism under parallelism,
  per-layer granularity surviving a merged coverage run, crash recovery,
  protected-file integrity — passes.
- The headline win is the **gate cost**, not the bare suite: the four
  per-layer floors went from ~25 minutes (four sequential suite runs) to
  136 seconds. That is the number every future workstream's verify step
  pays, and it landed intact at 11.3×.
- The remaining gap is squarely the scope of Front 1 items **5** (uv /
  hypothesis CI caching, fail-fast lint stage) and **6** (suite-duration
  perf regression guard), which are already specified in
  `13-cost-performance.md` and deliberately out of this cycle's scope.

Reopening the bar is therefore deferred to those items rather than
treated as a defect in this delivery.

## Note for anyone pulling this change

`pyproject.toml`'s `addopts` now carries `-n auto --maxprocesses=8`. A
venv that predates the merge fails immediately with
`pytest: error: unrecognized arguments: -n --maxprocesses=8` — this looks
like a broken test suite but is only a stale environment. Run:

```bash
uv sync --extra dev
```
