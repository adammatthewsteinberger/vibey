#!/usr/bin/env bash
# scripts/fleet/smoke.sh [--repo NAME]... [--live] [--skip-conformance]
#
# Fleet-wide smoke-test harness ("layer 4" of the test-harness strategy in
# the fleet plan): runs the same 7-gate sweep this program uses to judge
# every PR — 4x 100%-branch-coverage layer floors, ruff check + format,
# mypy --strict, lint-imports, bandit, pip-audit — against each repo's
# actual primary checkout on its current branch, not a disposable worktree.
# Then runs vibey's own two-mode live harness (faked mode always; --live
# opts into the real-API mode against whatever engines are installed) and
# `vibey doctor --conformance` across every installed engine binary.
#
# Meant to be green before any TestPyPI/PyPI publish (Phase F's `harness`
# gate). Never trust this script's own "PASS" without reading the tail of
# a failing gate's log — see docs/plans/fleet-program-runbook.md.
set -uo pipefail  # not -e: we want every gate to run so the summary is complete

ALL_REPOS=(vibey claudeloop agyloop codexloop cursorloop)
REPOS=()
RUN_LIVE=0
SKIP_CONFORMANCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPOS+=("$2"); shift 2 ;;
    --live) RUN_LIVE=1; shift ;;
    --skip-conformance) SKIP_CONFORMANCE=1; shift ;;
    -h|--help)
      echo "usage: smoke.sh [--repo NAME]... [--live] [--skip-conformance]"
      exit 0
      ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done
[ ${#REPOS[@]} -eq 0 ] && REPOS=("${ALL_REPOS[@]}")

SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# macOS ships bash 3.2 (no associative arrays) and this program never
# assumes a newer bash is on PATH — see run.sh/land.sh/status.sh, which are
# 3.2-safe for the same reason. Track results as TSV lines instead.
RESULTS_FILE="$SCRATCH/results.tsv"
: >"$RESULTS_FILE"
ANY_FAIL=0

# run_gate REPO LABEL CMD...
# Runs CMD from the repo's current directory, records PASS/FAIL, and on
# failure prints the log tail immediately (don't make the human wait for
# the summary to learn something broke).
run_gate() {
  local repo="$1" label="$2"; shift 2
  local log="$SCRATCH/${repo}--${label// /_}.log"
  printf '  %-42s ' "$label"
  if "$@" >"$log" 2>&1; then
    printf '%s::%s\tPASS\n' "$repo" "$label" >>"$RESULTS_FILE"
    echo "PASS"
  else
    printf '%s::%s\tFAIL\n' "$repo" "$label" >>"$RESULTS_FILE"
    ANY_FAIL=1
    echo "FAIL"
    echo "    log: $log"
    tail -n 15 "$log" | sed 's/^/    | /'
  fi
}

echo "=== fleet smoke: ${REPOS[*]} ==="

for repo in "${REPOS[@]}"; do
  ROOT="$HOME/git/$repo"
  if [ ! -d "$ROOT" ]; then
    echo "-- $repo: no checkout at $ROOT, skipping --"
    printf '%s::checkout\tFAIL\n' "$repo" >>"$RESULTS_FILE"
    ANY_FAIL=1
    continue
  fi
  cd "$ROOT" || { echo "cannot cd into $ROOT"; ANY_FAIL=1; continue; }
  BRANCH="$(git branch --show-current)"
  echo "-- $repo (branch: $BRANCH) --"

  if [ -n "$(git status --porcelain)" ]; then
    echo "  WARNING: $repo has uncommitted changes — smoke results reflect the worktree, not develop"
  fi

  for layer in domain application infrastructure cli; do
    run_gate "$repo" "coverage:$layer" \
      uv run pytest -q -p no:cacheprovider \
        --cov="${repo}.${layer}" --cov-branch --cov-report=term-missing --cov-fail-under=100
  done

  run_gate "$repo" "ruff check"          uv run ruff check src tests
  run_gate "$repo" "ruff format --check" uv run ruff format --check src tests
  run_gate "$repo" "mypy --strict"       uv run mypy --strict "src/${repo}"
  run_gate "$repo" "lint-imports"        uv run lint-imports
  run_gate "$repo" "bandit"              uv run bandit -q -r "src/${repo}"
  run_gate "$repo" "pip-audit"           uv run pip-audit
done

if printf '%s\n' "${REPOS[@]}" | grep -qx vibey; then
  cd "$HOME/git/vibey" || exit 1
  echo "-- vibey: two-mode live harness --"
  run_gate vibey "live-harness:faked" env VIBEY_LIVE_ENGINES= uv run pytest -q -m live

  if [ "$RUN_LIVE" -eq 1 ]; then
    run_gate vibey "live-harness:live(claudeloop,agyloop)" \
      env VIBEY_LIVE_ENGINES=claudeloop,agyloop uv run pytest -q -m live --max-dollars 5
  fi

  if [ "$SKIP_CONFORMANCE" -eq 0 ]; then
    echo "  vibey doctor --conformance"
    if uv run vibey doctor --conformance >"$SCRATCH/vibey--conformance.log" 2>&1; then
      printf 'vibey::conformance\tPASS\n' >>"$RESULTS_FILE"
      echo "  PASS"
    else
      printf 'vibey::conformance\tFAIL\n' >>"$RESULTS_FILE"
      ANY_FAIL=1
      echo "  FAIL — see $SCRATCH/vibey--conformance.log (a known, deferred claudeloop"
      echo "  done-detection gap can legitimately fail this; check before assuming smoke.sh is wrong)"
      tail -n 30 "$SCRATCH/vibey--conformance.log" | sed 's/^/    | /'
    fi
  fi
fi

echo
echo "=== summary ==="
sort "$RESULTS_FILE" | awk -F'\t' '{printf "%-45s %s\n", $1, $2}'

if [ "$ANY_FAIL" -eq 1 ]; then
  echo
  echo "SMOKE FAILED — do not publish. Logs kept at: $SCRATCH"
  trap - EXIT
  exit 1
fi

echo
echo "SMOKE GREEN across: ${REPOS[*]}"
