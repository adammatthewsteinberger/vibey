# 0022 — An absorbed package keeps every gate it was already held to

**Status:** accepted · **Date:** 2026-09-15 · **Extends:** ADR-0021, ADR-0016

## Context

ADR-0021 brought eight packages into this tree. Each arrived with its own quality contract: `vibey-gh` a 100% branch-coverage floor over 984 tests with black, isort and mypy; `vibey-bootstrap` a 100% line floor over 1,057 tests; `vibey-skills` manifest and link validators plus a unittest suite on a 3.10 floor. Root `pytest` is `testpaths = ["tests"]` and the nested workflows are inert once the repositories are gone, so on the first absorbed commit every one of those suites was in **no gate at all** — they could regress with CI green while the pull request description claimed a combined-tree gate.

The uv workspace makes a second, quieter lowering possible. The lock resolves at the intersection of every member's `requires-python`, which is 3.12; a `uv sync --package` environment can never run the 3.10 and 3.11 floors those wheels publish. A floor nothing runs on is a claim, not a contract.

## Decision

**Absorbing a package must not quietly lower what it was already held to.** Every absorbed package's own suite, own linters, own coverage floor and own Python floors run in this repository's CI, with the package's own command, unchanged.

- The `tools` matrix installs each package with plain `pip` and `actions/setup-python` on every interpreter its wheel declares, and runs the command its repository ran. Not `uv sync --package`, because the workspace cannot reach those floors.
- The floor is enforced where it always was — the package's own `pyproject` addopts — not re-derived in the workflow. If a test needs a real binary (`vibey-gh` shells out to `uv lock`), the binary is provided; the test is never weakened.
- Package-specific linters and drift checks (`tools-lint`: black, isort, mypy, and `vibey-gh`'s managed-automation `installed()` check) run as their own job.
- ADR-0016's converse still holds: the tenant is not rewritten to this tree's conventions on arrival. It converges module by module, and each step must keep the tenant's own suite green.

## Consequences

**Good.** Absorption is provably lossless with respect to quality: the numbers that were true the day before the import are asserted the day after. A regression in `vibey-gh`'s provenance gate — the one check whose job is to be unfoolable — fails this repository's CI.

**Bad.** Two toolchains in one CI (uv for the conductor, pip for the tenants) and a matrix of seven jobs that will grow with every absorption. Accepted: the alternative is a floor nobody measures.

**Rule status.** This binds every future absorption, survives any rewrite of the packages involved, and is about how the project treats its own work. It passes ADR-0020's test and owes a sub-doctrine, not yet proposed; the parent doctrine and the wording are the operator's to ratify.

## Alternatives rejected

- **Fold the tenants into the root pytest run and the four 100% gates.** Changes the floor's definition (branch vs line), the interpreter it runs on, and the command — three silent lowerings in one move.
- **`uv sync --package <tenant>` in the matrix.** Cannot exercise 3.10/3.11; the published floor becomes a claim.
- **Trust the tenants' own nested workflows.** They do not fire in this repository; that is exactly how the suites went ungated on the first absorbed commit.
- **Raise the tenants' floors to the conductor's on arrival.** Rejected by ADR-0016 for the same reason: a rewrite on import destroys the property the import exists to create.
