# Dependency policy

The installed runtime remains Python-standard-library only. Development dependencies are
bounded in the optional `dev` extra. Workflow Actions are pinned to immutable commits;
inference and documentation tools run only in isolated CI jobs. New dependencies require
a documented necessity, license and security review, pin/update strategy, and tests.
