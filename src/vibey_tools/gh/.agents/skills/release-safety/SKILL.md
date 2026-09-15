# Release safety

Verify the exact head and every required gate before mutation. Develop publishes only to
TestPyPI and preview surfaces; main publishes only to PyPI and production surfaces. Never
delete or force-push main/develop. Preserve immutable tags, releases, package provenance,
and branch-specific documentation.
