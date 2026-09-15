# Migrating to azure-bootstrap 3.0.0

3.0.0 is an **additive flagship** release. Upgrading is a no-op unless you opt into
new features.

## Upgrade steps

```bash
pip install -U "azure-bootstrap==3.0.0"
```

Existing code continues to work unchanged. No import paths were removed or renamed.

## What's new (opt-in)

| Feature | Extra | Enable |
|---------|-------|--------|
| Panther / Blob / SQL / NoSQL / ADX / Event Hubs transports | `[panther]`, `[bloblog]`, etc. | `configure_transports(panther=True)` + env |
| DB + outbox | `[db]` | `DATABASE_URL` + `from azure_bootstrap.db import get_db` |
| ACS email | `[email]` | `ACS_CONNECTION_STRING`, `ACS_SENDER_ADDRESS` |
| HTTP client | `[http]` | `build_session()`, `request_with_retry()` |
| AKS runtime | stdlib | `build_info()`, `install_sigterm_handler()` |
| Scaffold CLI | core install | `azbootstrap list` |

## New environment variables

See `docs/V3.0.0-PLAN.md` §11 for the full contract. All names are namespaced and
additive — none collide with 2.x variables.

## SemVer note

Despite the major version bump, 3.0.0 removes nothing and changes no defaults. The
major number signals product scope (doubled surface area), not breaking API changes.
