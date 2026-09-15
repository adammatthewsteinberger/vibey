---
name: okta-workflows-connectors
description: "Use when using the Okta or Azure AD / Microsoft Entra ID connectors in Okta Workflows: Okta Search Groups doing exact eq only except the Custom Search Criteria input (sw, ew); OKTA_GROUP vs APP_GROUP vs BUILT_IN Group Type semantics for filtering Entra-imported groups (filter Type = APP_GROUP; misbehavior UNCONFIRMED); Search Group Rule doing keyword (not exact) search; Okta connector concurrency/rate limits (30 concurrent, 15 GET/READ per-user, 6,000/min, not shown in the dashboard, DynamicScale 5x=50/10x=80/25x=120/50x=150); Entra delegated-permissions-only with no app-only/service-principal (use a dedicated service account); reauthorization breaking when scopes/config change; the three different Entra record caps (Search Groups 4,000, Search Group Members 900, Search Users 4,000; input can't contain #); mail-enabled security and distribution groups silently failing on write cards; List Contact Folder's 2-level cap; and hard-coded-domain search cards returning incomplete results. Triggers on Search Groups, Custom Search Criteria, APP_GROUP, Search Group Rule, Okta connector rate limits, DynamicScale, Azure AD connector, delegated permissions, 4000 groups, 900 members, mail-enabled security group, distribution group, List Contact Folder, Custom API Action."
---

# Okta Workflows — Connector-Specific Quirks (§5)

Ten quirks split across the Okta connector (5.1–5.4) and the Azure AD / Microsoft Entra ID connector
(5.5–5.10).

## Okta connector

### Quirk 5.1 — Search Groups uses exact `eq` only (except Custom Search Criteria)

"The card performs an eq (equal) comparison against the provided input value, except for the Custom
Search Criteria input." For starts-with/contains you must use the Custom Search Criteria field (`sw`,
`ew`, etc.).

- *Source:* okta/actions/searchgroups.htm

### Quirk 5.2 — Group `Type` semantics for APP_GROUP filtering

On the Okta Search Groups card: `OKTA_GROUP` = "managed either directly in Okta through static
assignments, or indirectly through group rules"; `APP_GROUP` = "imported and must be managed within
the app (such as Active Directory or LDAP) that imported the group"; `BUILT_IN` = "Okta manages the
group profile and memberships and can't be modified." When syncing Entra-imported groups on the Okta
side, filter Type = APP_GROUP — but because the card uses simple `eq`, unexpected filtering usually
means you need Custom Search Criteria or the Custom API Action card. **No confirmed public bug report
of APP_GROUP filtering misbehaving was found — treat any such claim as UNCONFIRMED.**

- *Source:* okta/actions/searchgroups.htm

### Quirk 5.3 — Search Group Rule card does keyword (not exact) search

"The search function executes a keyword search rather than an exact string match… the API searches for
the provided keywords across the Name, Expression Conditions, and Group Assignments fields… even the
First Matching Record option returns an unexpected group rule." Workaround: return the list (First 200
/ Stream) then Filter or Find for an exact name match.

- *Source:* support.okta.com okta-workflows-search-group-rule-card-returns-unexpected-multiple-results
  (updated May 6, 2026)

### Quirk 5.4 — Okta connector concurrency/rate limits differ from raw API

Built-in Okta connector: 30 concurrent Workflows → Okta requests, 15 concurrent GET/READ per-user
requests, 6,000 requests/minute total. These requests do NOT appear in the rate-limits dashboard.
DynamicScale/Workforce multipliers raise the concurrent ceiling (5x=50, 10x=80, 25x=120, 50x=150).

- *Source:* workflows-system-limits.htm

## Azure AD / Microsoft Entra ID connector

### Quirk 5.5 — Delegated permissions only, tied to a signed-in account

"The connection uses delegated access and delegated permissions, not app-only access or app-only
permissions." The token is tied to an admin/user account — there is NO app-only/service-principal
option. Use a dedicated service account.

- *Source:* guidanceforazureadconnector.htm

### Quirk 5.6 — Reauthorization breaks when config/scopes change

"You can also reauthorize any existing connections if the admin hasn't changed any configuration
settings." Changing scopes/config can break simple reauthorization and force a full reconnect.

- *Source:* guidanceforazureadconnector.htm

### Quirk 5.7 — Three different record caps across Entra cards (correcting a common misconception)

- Azure AD **Search Groups**: "The Search Groups action card returns a maximum of 4,000 groups."
- Azure AD **Search Group Members**: caps at **900** records — the Result Set option is documented
  verbatim as "`First 900 Matching Records`: returns the first 900 records that match the search
  criteria" (NOT 4,000). Exceed via Stream Matching Records.
- Azure AD **Search Users**: "returns a maximum of 4,000 users."
- Search Group Members input "can't contain the `#` hash character" (verbatim CAUTION).

- *Sources:* azuread/actions/searchgroups.htm; azuread/actions/searchgroupmembers.htm;
  azuread/actions/searchusers.htm

### Quirk 5.8 — Mail-enabled security groups & distribution groups silently fail

"Attempting to manage a Microsoft Entra ID Mail-enabled security group or Distribution group using the
Okta workflows Azure Active Directory connector will fail… This can occur with any of the action
cards… such as Update Group, Add User to Group, etc." — because the Graph API treats these as
read-only. Workaround: manage O365/unified groups instead, or use the on-premises PowerShell template.

- *Source:* support.okta.com
  can-okta-workflows-be-used-to-manage-office-365-mail-enabled-security-groups-and-distribution-groups

### Quirk 5.9 — List Contact Folder returns max 2 levels

"The List Contact Folder card returns a maximum of two levels of child folders." Workaround: Custom
API Action with nested `$expand=childFolders($expand=childFolders)`.

- *Source:* guidanceforazureadconnector.htm

### Quirk 5.10 — Search cards that hard-code `domain` return incomplete results (pattern)

Documented for Google Workspace (cards hard-code the authorizing user's `domain` instead of
`customer`, returning single-domain results only; fix via Custom API Action with Customer ID). This is
a recurring pattern — Workflows "Search" cards often wrap fuzzy or scoped APIs, so post-filtering and
Custom API Action are the standard escapes.

- *Source:* support.okta.com Workflows-Google-Workspace-Search-Users-or-Search-Groups
