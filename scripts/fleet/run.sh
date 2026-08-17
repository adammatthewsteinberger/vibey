#!/usr/bin/env bash
# scripts/fleet/run.sh REPO PHASE [DRIVER]
#
# Launch one dogfooded fleet-program run: a fresh disposable worktree off
# origin/develop, driven by one of the *loop runners against a phase plan
# file under docs/plans/fleet/<PHASE>-<REPO>.md.
#
# See docs/plans/fleet-program-runbook.md for the program this feeds and
# docs/plans/fleet/README.md for the mechanics this script implements.
set -euo pipefail

REPO="${1:?usage: run.sh REPO PHASE [DRIVER]}"
PHASE="${2:?usage: run.sh REPO PHASE [DRIVER]}"
DRIVER="${3:-claudeloop}"

case "$REPO" in
  vibey|claudeloop|agyloop|codexloop|cursorloop) ;;
  *) echo "unknown repo: $REPO (expected vibey|claudeloop|agyloop|codexloop|cursorloop)" >&2; exit 1 ;;
esac
case "$DRIVER" in
  claudeloop|agyloop|codexloop|cursorloop) ;;
  *) echo "unknown driver: $DRIVER" >&2; exit 1 ;;
esac
if ! command -v "$DRIVER" >/dev/null 2>&1; then
  echo "driver '$DRIVER' is not on PATH — install it first (uv tool install --editable ~/git/$DRIVER)" >&2
  exit 1
fi

VIBEY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLAN_FILE="$VIBEY_ROOT/docs/plans/fleet/${PHASE}-${REPO}.md"
if [ ! -f "$PLAN_FILE" ]; then
  echo "no plan file at $PLAN_FILE" >&2
  exit 1
fi

REPO_ROOT="$HOME/git/$REPO"
WT="$HOME/.cache/fleet-worktrees/${REPO}-${PHASE}"
RUN_ID="${REPO}-${PHASE}"
BRANCH="chore/${PHASE}"

echo "== $RUN_ID via $DRIVER =="

cd "$REPO_ROOT"
git fetch -q origin

if [ -d "$WT" ]; then
  echo "worktree already exists at $WT — reusing (resume, not fresh start)" >&2
else
  mkdir -p "$(dirname "$WT")"
  git worktree add -B "$BRANCH" "$WT" origin/develop
fi

# Protected paths: a run must never merge a diff touching these without a
# human. Enforced again at land.sh time, but recorded here for the seed
# prompt to see too.
PROTECTED_PATHS_NOTE="Do not modify: tests/infrastructure/db/test_chaos.py, tests/domain/test_noloss*.py, tests/domain/test_briefing.py (no-loss property suite), tests/system/test_delivery_stage_set.py, tests/live/** — these are protected; a change to them requires explicit human approval and will not auto-merge."

LOG_DIR="$WT/.$DRIVER"
mkdir -p "$LOG_DIR"

case "$DRIVER" in
  claudeloop)
    exec claudeloop run "$PLAN_FILE" \
      --cwd "$WT" \
      --run-id "$RUN_ID" \
      --add-folder "$VIBEY_ROOT/docs/plans" \
      --append-system-prompt "$PROTECTED_PATHS_NOTE" \
      --max-turns 800 --max-dollars 80 --max-wait 21600 \
      --permission-mode acceptEdits \
      --done-marker CLAUDELOOP_TASK_FULLY_COMPLETE \
      --log-level INFO --log-file "$LOG_DIR/run.log" \
      --stream-ui
    ;;
  agyloop)
    exec agyloop -v --log-file "$LOG_DIR/run.log" \
      run "$PLAN_FILE" \
      --cwd "$WT" \
      --run-id "$RUN_ID" \
      --add-dir "$VIBEY_ROOT/docs/plans" \
      --gateway sdk \
      --preset high \
      --scoped \
      --ramp 3 \
      --max-turns 800 --max-dollars 80 --max-wait 21600
    ;;
  codexloop)
    # NOTE: codexloop's `run` has no --cwd today (Phase C tracks adding it).
    # Until then, correctness depends on actually being in $WT — cd there
    # explicitly rather than relying on a flag that doesn't exist yet.
    cd "$WT"
    exec codexloop run "$PLAN_FILE" \
      --run-id "$RUN_ID" \
      --max-turns 800 --max-wait 21600 \
      --log-level INFO --log-file "$LOG_DIR/run.log" \
      --stream-ui
    ;;
  cursorloop)
    exec cursorloop run --plan "$PLAN_FILE" \
      --cwd "$WT" \
      --run-id "$RUN_ID" \
      --max-turns 800 --max-dollars 80 --max-wait 21600 \
      --log-level INFO
    ;;
esac
