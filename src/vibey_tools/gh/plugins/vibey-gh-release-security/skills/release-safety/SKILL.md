---
name: release-safety
description: This skill should be used for versioning, publishing, tagging, GitHub Releases, Pages, Packages, promotion, or branch realignment.
---
# Release safety

Verify exact SHA, branch, environment, version, artifacts, attestations, and gates. Develop
targets TestPyPI and Preview; main targets PyPI and Production. Never delete or force-push
main/develop. Use immutable tags and idempotent releases. See `references/checklist.md`.

## Resources
- `references/checklist.md` defines preflight and post-release evidence.
