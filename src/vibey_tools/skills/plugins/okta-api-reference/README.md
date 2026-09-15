# Okta API Reference Plugin

A reference for the **Okta API surface** across the core Workforce/Customer Identity platform and
the separate Identity Governance (OIG) product, plus the current MCP (Model Context Protocol)
server ecosystem for both. Distilled from vendor documentation and public package/repository
metadata as of a mid-2026 snapshot — API surfaces, SDK versions, and MCP tool inventories all change
continuously, so treat specific version numbers and tool lists as a starting point to verify against
`developer.okta.com`, PyPI, and the relevant GitHub repositories, not a permanent source of truth.

- **okta-core-management-api**: The core Okta REST API (`/api/v1/...`) — base URL/domain patterns,
  SSWS API tokens vs. OAuth 2.0 scoped tokens and Private Key JWT, the representative resource
  surface (Users, Groups, Apps, Policies, Auth Servers, System Log, etc.), cursor pagination and
  rate-limit headers, the System Log polling pattern, and the official `okta` PyPI package —
  its Pydantic-based v3.x architecture, Management-API-only coverage, and known gaps (no Authn
  flows, no Governance endpoints, don't confuse it with the stale `okta-sdk-python` fork).
- **okta-iga-governance-api**: The Identity Governance API (`/governance/api/v1` and `/v2`) —
  OAuth-only auth with `okta.governance.*` scopes, the full governance resource surface (campaigns,
  access requests, entitlements, bundles, risk rules, security access reviews, etc.), subscription
  and feature-flag gating, why there is no official Python SDK for this surface, and the two
  practical alternatives (raw HTTP with your own OAuth exchange, or the Okta Terraform Provider
  v6.1.0+).
- **okta-mcp-server-landscape**: The state of MCP servers for Okta automation — the official
  `okta/okta-mcp-server` (tools, auth, beta status, zero governance coverage), third-party
  alternatives for core IAM (Tako MCP, kapilduraphe, indranilokg, StackOne), and the single
  narrow, unreviewed, single-author third-party project that targets IGA workflows
  (`ashwinramn/okta-mcp-em-python`) — plus the threshold signals that would change this landscape.

## Scope

This plugin is about the **Okta API/SDK/MCP surface itself** — what's callable, how to authenticate,
what's covered and what isn't. It intentionally does not cover the Okta Workflows low-code
automation product's own quirks and limits (see the separate `okta-workflows` plugin for that), and
it does not cover any specific internal tooling or platform built on top of these APIs.
