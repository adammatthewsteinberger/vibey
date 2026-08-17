#!/usr/bin/env bash
# scripts/fleet/land.sh REPO PHASE
#
# Land a completed fleet run: open (or reuse) a PR from chore/<PHASE> onto
# develop, wait for checks, and squash-merge only if every check is green
# AND the diff does not touch a protected path. Otherwise leaves the PR
# open and explains why.
set -euo pipefail

REPO="${1:?usage: land.sh REPO PHASE}"
PHASE="${2:?usage: land.sh REPO PHASE}"

case "$REPO" in
  vibey|claudeloop|agyloop|codexloop|cursorloop) ;;
  *) echo "unknown repo: $REPO" >&2; exit 1 ;;
esac

REPO_ROOT="$HOME/git/$REPO"
WT="$HOME/.cache/fleet-worktrees/${REPO}-${PHASE}"
BRANCH="chore/${PHASE}"

if [ ! -d "$WT" ]; then
  echo "no worktree at $WT — nothing to land" >&2
  exit 1
fi

cd "$WT"

# Protected paths: refuse to land a diff that touches the no-loss gate, the
# chaos test, or the full-cycle system test without a human. This mirrors
# the plan's "Protected tests" guardrail (docs/plans/implementation-plan.md
# "Bootstrapping: vibey builds vibey").
PROTECTED_PATTERN='tests/infrastructure/db/test_chaos\.py|tests/domain/test_noloss.*\.py|tests/domain/test_briefing\.py|tests/system/test_delivery_stage_set\.py|^tests/live/'
CHANGED="$(git diff origin/develop... --name-only || true)"
if echo "$CHANGED" | grep -qE "$PROTECTED_PATTERN"; then
  echo "REFUSING TO AUTO-LAND: diff touches a protected path:" >&2
  echo "$CHANGED" | grep -E "$PROTECTED_PATTERN" >&2
  echo "This needs explicit human review. Open the PR by hand if you want it merged." >&2
  exit 2
fi

if git diff --quiet origin/develop... 2>/dev/null && [ -z "$(git log origin/develop..HEAD --oneline)" ]; then
  echo "no commits ahead of develop on $BRANCH — nothing to land" >&2
  exit 1
fi

git push -u origin "$BRANCH"

PR_NUM="$(gh pr list -R "adammatthewsteinberger/$REPO" --head "$BRANCH" --json number -q '.[0].number' || true)"
if [ -z "$PR_NUM" ]; then
  gh pr create -R "adammatthewsteinberger/$REPO" --base develop --fill
  PR_NUM="$(gh pr list -R "adammatthewsteinberger/$REPO" --head "$BRANCH" --json number -q '.[0].number')"
fi

echo "PR #$PR_NUM — watching checks..."
if gh pr checks "$PR_NUM" -R "adammatthewsteinberger/$REPO" --watch --fail-fast; then
  echo "green — merging"
  gh pr merge "$PR_NUM" -R "adammatthewsteinberger/$REPO" --squash --delete-branch --admin
  git -C "$REPO_ROOT" worktree remove --force "$WT"
  echo "merged and worktree removed: $WT"
else
  echo "PR #$PR_NUM is red — left open for a human. Run log: $WT/.*/run.log" >&2
  exit 3
fi
