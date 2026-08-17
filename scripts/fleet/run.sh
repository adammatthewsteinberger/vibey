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

# Protected paths (tests/infrastructure/db/test_chaos.py, the no-loss
# property suite, tests/system/test_delivery_stage_set.py, tests/live/**)
# are called out in each plan file directly and enforced again by land.sh's
# refusal check — no driver here supports an appended system prompt, so
# there is no out-of-band note to inject at launch time.

LOG_DIR="$WT/.$DRIVER"
mkdir -p "$LOG_DIR"

case "$DRIVER" in
  claudeloop)
    exec claudeloop run "$PLAN_FILE" \
      --cwd "$WT" \
      --run-id "$RUN_ID" \
      --add-folder "$VIBEY_ROOT/docs/plans" \
      --max-turns 800 --max-dollars 80 --max-wait 21600 \
      --permission-mode acceptEdits \
      --done-marker CLAUDELOOP_TASK_FULLY_COMPLETE \
      --log-level INFO --log-file "$LOG_DIR/run.log" \
      --stream-ui
    ;;
  agyloop)
    # KNOWN BROKEN as of 2026-08-17, tracked in
    # docs/plans/fleet/c2-harness-fix-agyloop.md — do not launch an
    # agyloop-driven run until that lands:
    #   --gateway sdk (this default): the local Antigravity harness fails
    #     to start ("Failed to read length from stdout").
    #   --gateway cli: --scoped has no effect on the CLI gateway's exported
    #     `agy` settings, so every tool call is silently auto-denied and the
    #     run falsely reports AGYLOOP_TASK_FULLY_COMPLETE having done
    #     nothing. Do NOT "fix" this here by switching to --gateway cli —
    #     that's the worse of the two failure modes (silent false success,
    #     not a loud crash).
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
