#!/usr/bin/env bash
# scripts/fleet/status.sh
#
# Tabulate every fleet worktree currently on disk: repo, phase, branch head,
# ahead/behind develop, and (if pushed) PR number + check state.
set -euo pipefail

ROOT="$HOME/.cache/fleet-worktrees"
if [ ! -d "$ROOT" ]; then
  echo "no fleet worktrees at $ROOT"
  exit 0
fi

printf '%-14s %-22s %-9s %-8s %-6s %s\n' "REPO" "PHASE" "HEAD" "AHEAD" "PR" "CHECKS"
for wt in "$ROOT"/*/; do
  [ -d "$wt" ] || continue
  name="$(basename "$wt")"
  repo="${name%-*}"
  phase="${name#*-}"
  cd "$wt"
  head="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
  branch="$(git branch --show-current 2>/dev/null || echo '?')"
  ahead="$(git log origin/develop.."$branch" --oneline 2>/dev/null | wc -l | tr -d ' ')"
  pr="$(gh pr list -R "adammatthewsteinberger/$repo" --head "$branch" --json number -q '.[0].number' 2>/dev/null || true)"
  if [ -n "$pr" ]; then
    checks="$(gh pr checks "$pr" -R "adammatthewsteinberger/$repo" 2>/dev/null | awk '{print $2}' | sort | uniq -c | tr '\n' ' ')"
  else
    checks="(no PR yet)"
  fi
  printf '%-14s %-22s %-9s %-8s %-6s %s\n' "$repo" "$phase" "$head" "$ahead" "${pr:--}" "$checks"
done
