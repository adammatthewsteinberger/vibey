---
name: okta-mcp-server-landscape
description: Use when evaluating or integrating an MCP (Model Context Protocol) server for Okta automation — the official okta/okta-mcp-server (tools, auth, distribution, beta status), third-party alternatives (Tako MCP, kapilduraphe, indranilokg, StackOne), the near-total absence of MCP coverage for Okta Identity Governance, and the one narrow third-party IGA MCP project that exists. Triggers on "Okta MCP server", "MCP Okta agent", "okta-mcp-server", "AI agent Okta automation", "Okta MCP governance tools".
---

# Okta MCP Server Landscape

Reference for the state of Model Context Protocol (MCP) server coverage across Okta's core platform
and its Identity Governance (IGA) product, as of the source this was distilled from (mid-2026
snapshot — this ecosystem is volatile; re-verify tool inventories before depending on any of them).

## TL;DR

Okta's own MCP server covers core platform resources reasonably well but is still beta and
source-only (no PyPI package). MCP coverage for Identity Governance is effectively **absent** —
Okta's official server exposes zero governance tools, and the one community project that targets
IGA is a narrow, single-author, unreviewed effort covering a small slice of governance workflows.

## Official server: `okta/okta-mcp-server`

- **Repository**: `github.com/okta/okta-mcp-server` — Apache-2.0, Python, Okta-published.
  Announced September 22, 2025 on `developer.okta.com`.
- **Status**: still described by Okta as **beta**, "not recommended for production use or critical
  workloads." As of the source snapshot the repo had no formal GitHub releases published.
- **Distribution**: **not on PyPI**. Install only via `git clone` + `uv sync` + `uv run
  okta-mcp-server`, or the published Docker image.
- **Transport**: stdio (compatible with Claude Desktop, VS Code Copilot, Cursor, etc.), configured
  via `mcp.json` / `claude_desktop_config.json`.
- **Authentication to Okta**: OAuth 2.0 only — either the **Device Authorization Grant**
  (interactive, browser-based; suited to local dev) or **Private Key JWT** (browserless; suited to
  headless/Docker/CI deployments). Configured via `OKTA_ORG_URL`, `OKTA_CLIENT_ID`, `OKTA_SCOPES`,
  `OKTA_PRIVATE_KEY`, `OKTA_KEY_ID` environment variables. Under the hood it uses Okta's Python SDK
  (a specific version pin was v3.4.1 in the source snapshot — verify current) for API calls.
- **Tools exposed** (by category):
  - *Users*: `list_users`, `get_user`, `create_user`, `update_user`, `deactivate_user`,
    `delete_deactivated_user`, `get_user_profile_attributes`
  - *Groups*: `list_groups`, `get_group`, `create_group`, `update_group`, `delete_group`,
    `list_group_users`, `list_group_apps`, `add_user_to_group`, `remove_user_from_group`
  - *Applications*: `list_applications`, `get_application`, `create_application`,
    `update_application`, `delete_application`, `activate_application`, `deactivate_application`
  - *Policies / Policy Rules*: full CRUD plus activate/deactivate for both policies and rules
  - *Logs*: `get_logs`
  - Plus deprecated fallback `confirm_delete_*` tools for MCP clients that don't yet support the MCP
    Elicitation API.
- **Safety features**: scope-based tool loading (a tool whose required scope isn't present in
  `OKTA_SCOPES` is hidden rather than exposed-and-failing); MCP Elicitation for destructive-operation
  confirmation; a full audit trail via the Okta System Log (every tool call is still a normal,
  logged Okta API call).
- **Zero governance coverage**: the tool registry contains no governance-prefixed tools, its
  `.env.example` lists only `okta.users.read okta.groups.read` as example scopes, and its README's
  feature list explicitly covers "users, groups, applications, policies, device assurance policies,
  brands, themes, custom pages, email templates, custom domains, email domains, and more" —
  Identity Governance is not mentioned. It also pins the core `okta` SDK, which itself doesn't wrap
  governance endpoints (see `okta-iga-governance-api`), so there's no governance capability to
  surface even indirectly. The source this was distilled from noted that the MCP server's 2026
  release notes documented only the addition of MCP Elicitation for destructive-action confirmation
  — no governance tools had been added as of that release.

## Third-party alternatives (core platform, not Okta-published)

None of the following advertise Identity Governance coverage — all are scoped to core IAM
(users/groups/apps/policies):

- **`fctr-id/okta-mcp-server`** ("Tako MCP") — Python; stdio + HTTP/SSE transports; API-token or
  OAuth Private Key JWT; includes risk-assessment and access-analysis tooling on top of core IAM
  resources.
- **`kapilduraphe/okta-mcp-server`** — TypeScript/Node; SSWS token auth; focused on user/group
  management and onboarding workflows.
- **`indranilokg/okta-mcp-server`** — npm-installable; app/group/user management.
- **StackOne Okta MCP** — a managed commercial offering. StackOne's own marketing states it "ships
  with 32 pre-built actions, fully extensible via the Connector Builder — plus managed
  authentication, prompt injection defense, and optimized agent context."

## The one IGA-focused MCP project

`ashwinramn/okta-mcp-em-python` (`github.com/ashwinramn/okta-mcp-em-python`) is the **only** public
MCP server in this ecosystem that specifically targets Identity Governance workflows, and it comes
with significant caveats:

- MIT-licensed, Python, single author, 0 stars / 0 forks, 13 commits at the time of the source
  snapshot.
- Self-described (verbatim from its own README) as "vibe coded — built rapidly through AI-assisted
  development with Claude/Copilot. While functional and tested against real Okta tenants, it: May
  contain unconventional patterns or edge cases not fully handled · Has not undergone formal
  security review · Is provided as-is for experimentation and learning · Should be tested thoroughly
  in a sandbox environment before any production use."
- **Authentication**: legacy SSWS API token only (`OKTA_DOMAIN`, `OKTA_API_TOKEN` env vars) — no
  OAuth or scoped-token support at all.
- **Tool coverage** (by category, verbatim tool names from its README):
  - *Navigation*: `okta_test`, `show_workflow_menu`
  - *CSV import*: `list_csv_files`, `analyze_csv_for_entitlements`,
    `prepare_entitlement_structure`, `execute_user_grants`
  - *Governance & compliance*: `generate_governance_summary`, `analyze_sod_context`,
    `create_sod_risk_rule`, `list_sod_risk_rules`, `test_sod_risk_rule`
  - *Bundle mining*: `analyze_entitlement_patterns`, `preview_bundle_creation`,
    `create_bundle_from_pattern`, `create_entitlement_bundle`
  - *Utility*: `okta_user_search`, `okta_batch_user_search`, `okta_batch_create_grants`,
    `okta_get_rate_status`, `get_entitlement_ids_for_values`
- **What's missing**: no access-request creation/approval/decision tools, no campaign CRUD or
  launch/end, no review-decision tooling, no security-access-review trigger, no labels/delegates/
  collections support. Its real scope is "bulk-onboard entitlements from a CSV and create
  SoD-safe bundles" — not a general-purpose governance MCP server, despite the category name.

## No Okta-affiliated IGA MCP server exists

As of the source snapshot, nothing on Okta's developer site, blog, or release notes references an
OIG-specific MCP server from Okta itself.

## Practical guidance

1. For AI-agent automation of **core** Okta resources: adopt the official `okta/okta-mcp-server`,
   authenticate with Private Key JWT outside of local dev, grant only the `*.read` scopes actually
   needed, add `*.manage` scopes per-task, and pin to a specific Git SHA (not `main`) since it ships
   with no formal releases and is explicitly labeled beta/not-for-production by Okta itself.
2. For AI-agent automation of **Identity Governance**: do not deploy
   `ashwinramn/okta-mcp-em-python` in a production context — it is unreviewed, SSWS-only, and covers
   a narrow CSV/bundle/SoD slice, not campaigns or access requests. Either wait for Okta's official
   server to add `okta.governance.*` tools, or build a small in-house MCP server wrapping only the
   OIG REST endpoints actually needed (campaigns + access requests are typically the
   highest-value pair) — the `mcp` Python SDK plus a few dozen lines of `httpx` calling the raw
   governance API (see `okta-iga-governance-api`) is sufficient for a focused internal server.
3. Re-verify tool inventories and auth models before relying on any specific third-party server
   listed here — this ecosystem changes quickly and none of these projects have Okta's backing.
4. Watch for two threshold signals that would change the above guidance: (a) Okta's official server
   adding `okta.governance.*` scopes or campaign/access-request tools — switch immediately and
   retire any in-house wrapper; (b) an `okta-iga` package appearing on PyPI under the official
   `okta` GitHub organization — adopt it in place of raw HTTP once it exists.
