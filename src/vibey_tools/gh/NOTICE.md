# NOTICE

`vibey-gh` was extracted from the `vibey_bootstrap.gh` subpackage of
[vibey-bootstrap](https://github.com/the-vibey-project/vibey-bootstrap), where it
first shipped in 4.1.0.

It was split out because it has **no dependencies** while vibey-bootstrap pulls the Azure
SDK and OpenTelemetry — 48 packages. Release tooling runs in every CI job of every
repository that adopts it, so making those repositories carry an unrelated dependency tree
(and its security advisories) to run a stdlib CLI was the wrong trade.

vibey-bootstrap depends on this package and re-exports it, so nothing changed for anyone
already importing `vibey_bootstrap.gh`.

The subpackage was authored in full for vibey-bootstrap and contains none of that
project's earlier code, so the copyright here is held solely by Adam Matthew Steinberger.
