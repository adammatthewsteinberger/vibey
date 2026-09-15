---
name: okta-iga-governance-api
description: Use when working with Okta Identity Governance (OIG) API endpoints — the /governance/api/v1 and /v2 surface (campaigns, access requests, entitlements, bundles, grants, principal entitlements, collections, risk rules, labels, delegates, security access reviews), OAuth-only okta.governance.* scopes, why there is no official Python SDK for these endpoints, and the Okta Terraform Provider as the closest thing to typed tooling. Triggers on "Okta IGA API", "Okta governance API", "okta.governance scopes", "Okta entitlements API", "Okta access requests API", "Okta campaigns API", "okta-iga Python SDK".
---

# Okta Identity Governance (OIG) API

Reference for the Okta Identity Governance REST API surface — a separately-versioned API from the
core Management API, with different authentication requirements and no official Python SDK.

## Base URL and versioning

Same tenant host as the core API, distinct path prefix:

- `https://{yourOktaDomain}/governance/api/v1/...`
- `https://{yourOktaDomain}/governance/api/v2/...` (V2 Access Requests, V2 Principal Access)

Documented at `developer.okta.com/docs/api/iga`.

## Authentication: OAuth 2.0 only — no SSWS support

Unlike the core Management API, OIG endpoints accept **only** OAuth 2.0 bearer tokens — there is no
SSWS token fallback. The token comes from either an OIDC app (user-based) or a service app
(`client_credentials` / Private Key JWT), and must include the relevant `okta.governance.*` scopes.
Representative scope names:

- `okta.governance.campaigns.read` / `.manage`
- `okta.governance.accessRequests.read` / `.manage`
- `okta.governance.entitlements.read` / `.manage`
- `okta.governance.labels.manage`
- `okta.governance.securityAccessReviews.admin.manage`
- `okta.governance.delegates.manage`

Service apps additionally need an admin role (e.g. `SUPER_ADMIN` or a custom admin role) because the
resulting access token acts *as* that principal — scopes alone aren't sufficient without the
underlying admin-role grant.

## Resource surface

Campaigns, Reviews, Entitlements (and entitlement-values), Entitlement Bundles, Grants, Principal
Entitlements, Principal Access (v1 and v2), Collections (Beta), Risk Rules (Separation-of-Duties),
Resource Owners, Labels, Principal Settings, Delegates, Security Access Reviews, Org Governance
Settings, Entitlement Settings, Access Requests V1 (Request Types) and V2 (conditions-based). There
are also end-user–facing surfaces exposed through the admin/end-user UI backed by this API: My
Requests, My Catalogs, My Security Access Reviews, My Access Certification Reviews, My Settings.

## Availability caveats

- OIG is a **paid subscription add-on** — the API is generally available on both Preview and
  Production for subscribed customers, but individual endpoints (Collections, some V2 Access
  Request features) may still be in Beta.
- Several capabilities are additionally gated by feature flags on top of the subscription. The
  source this was distilled from names: Realms, Resource Collections, Govern Okta Admin Roles,
  Bidirectional Group Management for AD, Campaign types, Slack notifications, Security Access
  Reviews, and the Unified Requester Experience. A 404 or 403 on a documented endpoint can mean
  "feature not enabled for this org," not necessarily a bug in calling code — check
  feature-flag/subscription state before assuming an integration defect.
- Historically, V2 Access Request APIs did **not** accept the `client_credentials` grant (tracked
  under internal Okta issue IDs referenced as OKTA-1044065 / OKTA-926552 in Okta's 2025 release
  notes). Test `client_credentials` against your specific org and API version before depending on
  it for service-to-service access-request automation — this may or may not still apply depending
  on when it shipped relative to your org's release train.

## No dedicated Python SDK

There is no `okta-iga`, `okta-governance`, or equivalently-named package on PyPI (official or
community, as of the source this was distilled from). The official `okta` Python package (see
`okta-core-management-api`) is generated from the Management OpenAPI spec (`management.yaml`), which
does not declare any `/governance/api/...` paths. Two practical options for calling this API from
Python:

1. Drop to the SDK's underlying request executor / HTTP transport (effectively raw HTTP), reusing
   only its OAuth token-acquisition machinery.
2. Bypass the SDK entirely: use `httpx` or `requests` with your own client-credentials JWT exchange
   against `/oauth2/v1/token`, then call `/governance/api/v1|v2/...` directly with the resulting
   bearer token. This is the pattern Okta's own documentation demonstrates — every IGA example in
   Okta's docs uses raw `curl`, never SDK calls.

### Practical pattern

Use a library like `authlib`, or a hand-rolled JWT assertion, to perform the client-credentials
exchange, then make direct calls, e.g.:

```
requests.get(
    f"{org}/governance/api/v1/campaigns",
    headers={"Authorization": f"Bearer {token}"},
)
```

## Alternatives to a Python SDK

- **Okta Workflows** ships first-class connector cards for OIG (campaign create/launch/end,
  access-request create/decision, entitlement CRUD, etc.) — the path of least resistance for
  no-code/low-code IGA automation, at the cost of Workflows' own execution-limit and card-type
  constraints (see the `okta-workflows` plugin for those specifics).
- **Okta Terraform Provider** — per the provider's own README (`okta/terraform-provider-okta`),
  "With v6.1.0, the Terraform Okta provider now officially supports the Okta Governance API." The
  source this was distilled from recorded the most recent release as **v6.10.0 (April 27, 2026)** —
  re-check the current release before depending on a specific version's resource coverage. This is
  the closest thing to typed/schema-validated tooling for OIG resources if you need declarative,
  GitOps-style management (campaigns, entitlements, related resources) without hand-writing raw
  HTTP calls. Confirm the installed provider version is `>= 6.1.0` before assuming
  governance-resource support at all.

## Practical guidance

1. Before building any IGA integration, confirm the target org actually has the OIG subscription and
   the specific feature flags for the resources you need (Collections, V2 Access Requests, Realms,
   etc.) — don't assume parity with the base Management API's availability.
2. Do not search for an official Python SDK for governance endpoints — none exists as of this
   snapshot. Plan for either raw HTTP or the Terraform provider from the start, rather than
   discovering the gap mid-project.
3. If service-to-service (`client_credentials`) access to V2 Access Request endpoints is required,
   validate it against the specific org and API version early — this has been a historically
   inconsistent area.
4. Remember OIG is OAuth-only: any design that assumes SSWS-token access will work "the same way it
   does for core Okta" will fail for governance endpoints specifically.
