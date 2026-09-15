# Testing strategy

The suite requires 100% first-party line and branch coverage. Unit tests cover configuration,
decision logic, subprocess contracts, idempotency, and failures. Template tests parse all
YAML, require immutable action pins, assert least privilege, and prohibit permanent-branch
deletion. Dogfood tests compare installed workflows with rendered templates byte for byte.
Release acceptance additionally observes real GitHub runs and public surfaces.
The debug suite also compiles nested code objects, rejects unsupported branch opcodes,
exercises taken and fallthrough edges, verifies correlation fields and every SHA-256 chain
link, confirms file/stderr lifecycle, and proves tracing remains opt-in and data-minimal.
