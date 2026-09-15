# Governance

Adam Matthew Steinberger is the current maintainer and release authority. Decisions favor
security, reproducibility, accessibility, compatibility, and low operational complexity.
Substantial architecture or policy changes should include an ADR and public rationale.
Maintainer succession, additional committers, and conflict-of-interest rules will be
documented before authority is delegated.

## Standing subdoctrine 9.a — the clean repo

*Filed under doctrine 9 (the vibe): clutter is drag. Ratified by the operator's merge
of the pull request that carried this text.*

1. **Every repository is kept technically clean at all times — no exceptions — both
   locally and in the cloud.** No orphan branches, no merged-and-undeleted branches,
   no closed-pull-request heads lingering, no gone-upstream locals, no dangling
   worktrees; draft releases and orphan tags are surfaced, never silently
   accumulated.
2. **The rule covers every messiness class a forge technically permits** — GitHub,
   GitLab, and Forgejo alike: refs, releases, tags, artifacts, workflow state —
   enumerated in `vibey-gh tidy` and extended whenever a forge grows a new way to be
   messy.
3. **Human messiness is expressly welcome and stays.** Prose, discussions,
   half-finished thoughts, stashes, untracked work in progress, imperfect words —
   that is the warmth of this project, and nothing here reads, judges, or touches
   it. The clutter this subdoctrine wars on is machine-state clutter only.
4. **Losslessness governs cleanup.** Automation deletes only what is provably
   redundant — by ancestry where merges preserve history, by the forge's own
   deletion-at-merge event where squash and rebase rewrite it. Anything not provably
   redundant is reported to the human and never removed by a machine.

