---
name: conflict-resolution
description: This skill should be used when a pull request conflicts with its target branch and requires a guarded semantic resolution.
---
# Conflict resolution

Materialize conflicts against the current base, enumerate unresolved paths, preserve both
intents, edit only the conflict set, and let normal CI validate. Never delete or rename a
permanent branch and never force-push.
