---
name: okta-core-management-api
description: Use when working with the Okta core (Workforce/Customer Identity) Management REST API or the official Python SDK — base URL and domain patterns, SSWS API tokens vs OAuth 2.0 scoped access tokens, Private Key JWT for service-to-service auth, exposed resource objects, cursor pagination and rate-limit headers, System Log polling, and the official `okta` PyPI package's architecture, coverage, and known gaps. Triggers on "Okta REST API", "Okta Management API", "okta-sdk-python", "pip install okta", "SSWS token", "Okta OAuth scopes", "Okta System Log", "Okta rate limit", "Okta pagination".
---

# Okta Core Management API & Python SDK

Reference for the Okta core platform's REST API and its official Python SDK, current as of the
sources this skill was distilled from (mid-2026 snapshot — verify version numbers against
`developer.okta.com` and PyPI before relying on them, since both the API and SDK ship continuous
updates).

## Coverage snapshot

The Okta core (Workforce/Customer Identity) platform has full coverage on all three integration
dimensions as of the source snapshot: a mature REST/Management API authenticated by SSWS token or
OAuth 2.0; an official Python SDK on PyPI (package `okta`); and an official Okta-published MCP
server (`okta/okta-mcp-server`, announced September 22, 2025) — though that MCP server is still
distributed source-only via `uv`/Docker (not on PyPI) and Okta itself still labels it beta. See
`okta-mcp-server-landscape` for the full MCP picture.

## REST API basics

- **Base URL pattern**: `https://{yourOktaDomain}/api/v1/{resource}`. `{yourOktaDomain}` is a
  tenant-specific subdomain, e.g. `integrator-1234567.okta.com` (free developer orgs) or
  `acme.okta.com` / `acme.oktapreview.com` / `acme.okta-emea.com` in production. All requests must be
  HTTPS.
- The API is versioned and uses HAL/JSON hypermedia (`_links` for navigation) — see
  `developer.okta.com/docs/reference/core-okta-api/`.
- **Pagination**: cursor-based via an `after` query parameter (`limit` up to 200). Always follow the
  response's `Link` header for the next page rather than constructing your own `since`/`until` or
  offset URLs — this is true for both general resource listing and System Log polling.
- **Rate limiting**: 429 responses include an `X-Rate-Limit-Reset` header. Well-behaved clients also
  watch the `X-Rate-Limit-Remaining` header on every response and back off before hitting 429,
  rather than only reacting after the fact.

## Authentication: two schemes

1. **SSWS API token** — sent as `Authorization: SSWS {token}`. Okta's own documentation now
   recommends **against** this for new work: per the Postman setup guide
   (`developer.okta.com/docs/reference/rest/`), "Okta doesn't recommend
   using the Okta-proprietary SSWS API token authentication scheme. This API token scheme allows you
   to access a broad range of APIs because there's no scope associated with the token. Access to the
   APIs depends on the privileges of the user that created the API token. The API token also has a
   fixed expiry date." Treat SSWS as acceptable only for short-lived scripts, never as the
   authentication backbone of a persistent service.
2. **OAuth 2.0 scoped access tokens** — issued by the org authorization server at
   `https://{yourOktaDomain}/oauth2/v1/token`. Sent as `Authorization: Bearer {access_token}`.
   Service-to-service apps should use **Private Key JWT** (`client_credentials` grant). Scopes are
   granular — representative examples: `okta.users.read`, `okta.groups.manage`,
   `okta.policies.manage`, `okta.logs.read`, `okta.apps.manage`. Always request the narrowest scope
   set the calling code actually needs, and treat `*.manage` scopes as requiring more scrutiny than
   `*.read`.

## Resource surface (representative, not exhaustive)

Users, Groups, Applications, Sessions, Factors/Authenticators, Policies & Policy Rules (sign-on,
password, MFA, authentication, access), Authorization Servers (with Scopes, Claims, Access Policies,
Policy Rules), System Log, Devices, Brands/Themes/Custom Pages, Email Templates/Domains, Custom
Domains, Identity Providers, Network Zones, Trusted Origins, Roles & Resource Sets, Event/Inline
Hooks, Schemas, Realms.

Endpoint path examples that appear across real integrations: `/api/v1/users`, `/api/v1/groups`,
`/api/v1/apps`, `/api/v1/policies`, `/api/v1/devices`, `/api/v1/authenticators`,
`/api/v1/behaviors`, `/api/v1/trustedOrigins`, `/api/v1/zones`, `/api/v1/logs` (System Log),
`/api/v1/org` (whoami/org info), `/api/v1/authorizationServers` (Auth Servers, Scopes, Claims,
Policies, Rules), `/api/v1/brands` (Brands, Themes, Email Customizations, Email Domains, Domains),
`/api/v1/flows` (Okta Workflows folder list, export-as-zip, import, delete — see the caveat on
Workflows below), `/api/v1/iam` (Custom Roles, Resource Sets, Role Targets, Role Assignments),
`/api/v1/security/events/providers` (Shared Signals Framework / ITP event providers), and the
ITP-specific policy endpoints under `/api/v1/policies` for entity-risk, post-auth, and
session-violation policy types.

Note on Okta Workflows: the `/api/v1/flows` endpoint only supports folder-level list/export
(zip)/import/delete — there is no API to modify Workflows logic inside a flow. Any tool that
manages Workflows folders via the API can only really do drift-*detection* on the exported bundle
(compare by hash), not field-level create/update of flow contents.

## System Log polling pattern

The canonical, safe way to consume the System Log for near-real-time event ingestion:

- `GET /api/v1/logs?after={cursor}`, always in ascending order.
- Follow the response's `Link` header for continuation — never hand-construct `since`/`until` query
  parameters, since Okta's own guidance and real-world integrations both treat `Link`-header
  following as the only supported pagination contract for this endpoint.
- Persist the cursor after every processed batch (not just at the end of a run) so that a crash or
  restart resumes exactly where it left off rather than skipping or re-processing events.
- Okta may return up to 1,000 events per page.

## The official Python SDK — `okta`

- **Install**: `pip install okta`. **Do not confuse this with `okta-sdk-python` (hyphenated) on
  PyPI** — that is an inactive community fork (last release 0.2.1 as of the source this was
  distilled from) and is not the maintained package. The maintained package name is `okta`.
- **Version snapshot** (verify current values on PyPI before relying on them — this package ships
  frequent regens): the source this skill was distilled from recorded the latest release as
  **3.4.2**, dated **April 15, 2026**, with a PyPI dependency specifier of **`Python >=3.10`**.
  Watch for drift between docs and package metadata here: some older GitHub README/contributor docs
  reference "Python 3.9+" while the live PyPI specifier on 3.4.2 requires 3.10+ — trust the installed
  package's actual `Requires-Python` metadata over prose docs if the two disagree.
- **Repository**: `github.com/okta/okta-sdk-python`, Apache-2.0, maintained by Okta.
- **Architecture (v3.x)**: a breaking rewrite from v2.x. The SDK's own CHANGELOG states: "The SDK
  has been regenerated using the v5.1.0 Okta Management OpenAPI specifications, bringing support
  for new endpoints and enhanced functionality across the API surface." The generation toolchain is
  named explicitly in Okta's contributor guide (`developer.okta.com/code/contribute-sdk/`):
  "OpenAPI Generator: openapi-generator-cli version 7.7.0." Models moved from a custom `OktaObject`
  base class to Pydantic `BaseModel` subclasses; modules moved from `okta/resource_clients/` to
  `okta/api/`. Every list method returns a `(data, response, error)` tuple, with `_with_http_info`
  variants available when you need raw response headers (e.g. to read `X-Rate-Limit-Remaining`
  yourself).
- **Coverage**: the Okta **Management** API surface only — Users, Groups, Apps, Policies,
  Factors/Authenticators, System Log, Devices, Brands, Authorization Servers, etc.
- **Auth support**: SSWS token (`config={'orgUrl': ..., 'token': ...}`) or OAuth 2.0 Private Key JWT
  — but the SDK's own README states this OAuth support is **only for service-to-service
  applications** (verbatim: "This SDK supports this feature (OAuth 2.0) only for service-to-service
  applications."). It does not implement user-context OAuth flows (authorization code, etc.) — for
  those, use the Sign-In Widget or AuthJS instead.
- **Known gaps** (verify current status before relying on the absence of these — SDKs evolve):
  - Does **not** wrap the Identity Governance (`/governance/api/v1|v2`) endpoints — separate OpenAPI
    spec, separate URL prefix. See `okta-iga-governance-api` for that surface.
  - Does not cover the legacy Authentication (`/api/v1/authn`) primary-auth flows as a first-class
    citizen — those are typically driven through the Sign-In Widget or AuthJS instead.
  - Coverage of newly released Management endpoints lags spec releases until the SDK's next
    regeneration/release cycle.
  - A separately-named PyPI package, **`okta-sdk-python`** (with hyphens), exists and is an
    inactive community fork (last release 0.2.1) — do not use it; the supported package is `okta`.

## Practical guidance

1. Default to OAuth 2.0 Private Key JWT with narrowly-scoped `okta.*.read` scopes for any
   long-lived integration; add `*.manage` scopes per-task rather than provisioning them broadly
   up front, and audit which scopes are actually exercised periodically.
2. Reserve SSWS tokens for throwaway scripts and local experimentation only — never wire them into
   a production service, given Okta's own recommendation against the scheme and its lack of
   scoping.
3. Always follow `Link` headers for pagination (both general resource lists and the System Log) —
   never hand-roll offset math against Okta's cursor-based pagination contract.
4. Before assuming the official Python SDK covers an endpoint, check whether it's a Management API
   path (`/api/v1/...`) or a Governance path (`/governance/api/...`) — only the former is in scope
   for the `okta` package as of this snapshot.
