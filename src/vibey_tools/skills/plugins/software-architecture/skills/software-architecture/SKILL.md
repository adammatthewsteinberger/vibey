---
name: software-architecture
description: "Production software architecture reference for Python (FastAPI), Next.js/TypeScript, and Azure at scale. Covers when to use modular monolith vs microservices, API style selection (tRPC/REST/GraphQL/gRPC), Python backend layered architecture with FastAPI + SQLAlchemy + dependency injection, Next.js App Router with Server Components and state management, Azure landing zones and hub-and-spoke networking, zero-downtime migrations with expand-contract, observability with OpenTelemetry, Conway's Law team alignment, and ADRs. Use when advising on architecture decisions, stack selection, migration strategy, or scaling approaches for Python/TypeScript/Azure systems."
---

# Production Software Architecture: Python, Next.js/TypeScript, and Azure

## Core Philosophy

**Start with a modular monolith, not microservices.** Roughly 80% of microservices benefits come from logical boundaries, not independent deployment. Extract services only when concrete signals appear: independent scaling needs, team coordination friction exceeding ~30–40 engineers, or regulatory isolation. The Prime Video case study (90% cost reduction by consolidating to a monolith) and CNCF 2024 data showing 42% of organizations consolidating microservices confirm the trend.

**Decision thresholds:**
- Modular monolith: team ~10–100 engineers, scale up to millions of users, fewer than ~5 platform engineers
- Microservices: team >~100 engineers, a component needs ~50x the compute of others, polyglot requirements, or PCI/regulatory isolation
- Cost reality: microservices infrastructure runs 3.75–6x higher than monoliths for equivalent functionality

**Enforcement matters more than the label.** A modular monolith only works with enforced module boundaries: public APIs per module, schema-per-module data ownership, and architecture tests (import-linter in Python, ESLint boundary rules / dependency-cruiser in TypeScript).

---

## Architecture Style Decision

### Modular Monolith
- Single deployable, one pipeline, in-process calls
- Logical module boundaries enforced by tooling
- Schema-per-module, public APIs only, no cross-module internal imports
- Martin Fowler's "MonolithFirst" and Sam Newman's "never start with microservices" both apply: get boundaries right by living in the domain first

### Microservices
- Only when you have a concrete scaling, team, or regulatory driver you can name
- Supports: asynchronous (events/messages preferred for decoupling) and synchronous (REST, gRPC) comms
- Distributed transactions via **Saga pattern** with compensating transactions
- Supporting patterns: Sidecar, Ambassador, Anti-Corruption Layer (ACL)

### Migration: Strangler Fig + Anti-Corruption Layer
- Put legacy system behind a façade/proxy
- Start with the **easiest slice, not the most important one** — build confidence in the process
- Cut along **business boundaries, not technical ones**
- Build an ACL inside the monolith to translate calls to/from new services
- Watch failure modes: façade becoming its own monolith; "temporary" dual-write sync becoming permanent; migrations that never finish because they are horizontal instead of vertical slices

---

## API Style Selection

| Style | Best For | Avoid When |
|---|---|---|
| **tRPC** | TypeScript-first, full-stack, monorepos, internal tools | Public/polyglot APIs, multi-repo without versioning story |
| **GraphQL** | Complex client-driven data, multiple heterogeneous clients | Simple CRUD, performance-critical simple queries |
| **REST** | Public APIs, broad compatibility, HTTP caching, CRUD | High-throughput internal service calls |
| **gRPC** | Internal high-throughput service-to-service, streaming | Browser clients (needs transcoding proxy) |

**Hybrid is normal:** REST/GraphQL at the public boundary, tRPC or gRPC internally.

**tRPC specifics:** ~0.1ms request overhead in-process; reported 35–40% productivity gain vs REST for TypeScript projects (treat as directional). Contracts live in code — need explicit versioning story for public/multi-repo scenarios.

**GraphQL specifics:** N+1 problem solved with DataLoader batching. Mandatory query depth/complexity/cost limits to prevent DoS. One benchmark: GraphQL ~1864ms vs REST ~922ms for simple queries — GraphQL's win is flexibility, not raw speed.

---

## Python Backend Architecture

### Layered / Clean Architecture (FastAPI)
```
API (routers) → application/services → domain (entities, value objects) → infrastructure (repositories, SQLAlchemy)
```
- **Domain layer must have zero dependencies** on API or infrastructure
- Repositories defined as Protocol/ABC interfaces in the application layer, implemented in infrastructure (Dependency Inversion)
- `src/` layout with domain modules; `pyproject.toml` per package

### Repository + Unit of Work Pattern
- Repositories receive a request-scoped `AsyncSession`
- UnitOfWork coordinates commit/rollback across repositories
- Production SQLAlchemy pool tuning: pool size 20, max overflow 30, `pool_pre_ping=True`

### Dependency Injection
- **FastAPI `Depends`** for request-scoped wiring (DB sessions, current user)
- **`dependency-injector`** (Container, providers.Factory/Resource, `@inject`, WiringConfiguration) for larger apps
- **`lagom`** as a lighter alternative
- Manual DI (constructor injection wired in a composition root) is preferable for smaller services

### Application Factory + Lifespan
- `create_app()` builds the FastAPI app, wires the DI container, adds middleware/CORS, includes routers
- `lifespan` manages startup/shutdown (DB pools, caches)
- `app.include_router()` composition has negligible startup cost

### Background Tasks

| Library | Use When |
|---|---|
| **RQ** | Simplest setup; most Django/Flask apps |
| **Celery** | Periodic tasks, complex workflows, existing ecosystem. Caveat: switch to `acks_late` — default `ACKS_EARLY=True` loses payloads on worker crash |
| **Dramatiq** | Message reliability is paramount (financial/compliance); tasks acked only after completion |
| **ARQ** | Async-native (asyncio), Redis-based; pair with supervisord for multi-worker |

### Python Monorepo: uv Workspaces
- Single root `pyproject.toml` with `[tool.uv.workspace] members = [...]`
- One shared `uv.lock`, one `.venv`, cross-package deps via `[tool.uv.sources] pkg = { workspace = true }` (editable by default)
- Limits: single `requires-python` (intersection of all members); no conflicting dependency versions across members

### Testing Pyramid
- Many unit → fewer integration → fewest E2E
- Integration tests against real dependencies using **testcontainers** (real Postgres/Redis in Docker)
- Mock at architectural boundaries (repository interfaces), not deep internals

---

## Next.js / TypeScript Frontend Architecture

### Folder Structure: Feature-Sliced Design (FSD)
- Feature-based / FSD is the consensus for large apps
- App Router colocation: route owns `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, plus local `_components`/`_lib`
- FSD layers (shared → entities → features → app) enforce unidirectional dependencies
- Atomic Design is good for the design system but doesn't answer where user scenarios live

### Server / Client Component Boundary (Most Critical Decision)
- Server Components are the **default** — data reads, composition, less JS shipped
- Push `'use client'` **down to interactive leaves** — a `'use client'` at the top of `page.tsx` forfeits most of the benefit
- Shifting to RSCs cuts client JS bundles meaningfully and reduces backend load

### State Management Decision Rules

| State Type | Tool |
|---|---|
| Server data (caching, revalidation, dedup) | **TanStack Query** |
| Forms | **React Hook Form** |
| URL-representable (filters, pagination, tabs) | **URL state** |
| Component-local | **useState** |
| Shared simple | **Zustand** |
| Shared granular / derived values | **Jotai** |
| Complex / strict patterns / time-travel debugging | **Redux Toolkit** |

**Anti-pattern #1 in 2026:** fetching API data into Zustand/Redux and manually syncing it.

### Authentication (2025–2026)
- **CVE-2025-29927** (CVSS 9.1, March 2025): middleware-only auth is bypassable via spoofed `x-middleware-subrequest` header. Always use the **Data Access Layer pattern** — verify auth at every data-access point, not just middleware.
- Cookie hardening: `HttpOnly`, `Secure`, `SameSite`, `__Host-` prefix
- **Clerk**: fastest B2C time-to-production
- **WorkOS**: enterprise SSO
- **Better Auth**: full data ownership in your own DB; took over Auth.js maintenance Sept 2025
- **Auth.js v5**: mainly for existing apps (now in security-patch mode)
- JWT sessions scale without DB lookups but can't be revoked before expiry. Database sessions enable instant "sign out everywhere" but add latency

### Frontend Monorepo: Turborepo
- Structure: `apps/*` + `packages/*` with shared `ui`, `eslint-config`, `typescript-config`, `shared-types`
- Remote caching (content-addressed, shared across devs + CI via Vercel free tier or self-hosted S3-compatible storage with `TURBO_TOKEN`/`TURBO_TEAM`) can cut CI from ~20 minutes to under a minute
- **Don't extract a package until a second consumer appears**

---

## Azure Cloud Architecture

### Landing Zones
- Use the Cloud Adoption Framework **enterprise-scale landing zone**
- Management-group hierarchy with governance/Policy inheriting down
- Separate **platform** subscriptions (management, connectivity, identity) and **application** landing-zone subscriptions
- Eight design areas: billing/Entra tenant, identity & access, management-group/subscription org, network topology & connectivity, security, management, governance, platform automation/DevOps
- Centralized Log Analytics + Defender for Cloud + Sentinel from day one

### Networking: Hub-and-Spoke
- Central hub VNet hosting Azure Firewall, VPN/ExpressRoute gateways, Bastion, and Private DNS zones
- Spokes peer to the hub — no direct spoke-to-spoke (route through hub via UDRs for centralized inspection)
- **Networking is the hardest thing to change after workloads deploy** — plan IP space up front
- Use Private Endpoints for PaaS
- **Application Gateway** (regional, WAF, integrates with Azure Firewall) vs **Front Door** (global L7, CDN, TLS termination, WAF, fast failover) — Front Door for global HTTP(S); Application Gateway for regional control + double inspection

### Multi-Region Active-Active
- **Front Door**: global choice; active-active or active-passive, automatic rerouting, integrated WAF/CDN
- **Traffic Manager**: DNS-based (simpler, slower failover due to DNS TTL caching) — useful as backup router if Front Door is unavailable
- **Cosmos DB multi-region writes**: `--enable-multiple-write-locations`, Session consistency by default, automatic conflict resolution
- Front multi-region APIM Premium by adding each regional gateway endpoint as a Front Door custom origin

### Service Mesh on AKS
- **Linkerd**: pragmatic default — Rust micro-proxy, mTLS on by default, 40–400% less latency overhead vs Istio
- **Istio**: when you need advanced traffic shaping, fine-grained policy, broad Envoy ecosystem, and can staff the complexity. AKS offers a managed Istio-based add-on
- CNCF data shows overall mesh adoption declining (from ~18% peak to ~8% by Q3 2025) — many teams don't need one

### IaC: Bicep vs Terraform
- **Bicep**: Azure-only, native day-0 support for new services, no state file, server-side ARM orchestration, preflight policy validation
- **Terraform**: multi-cloud, explicit state with drift detection, reusable versioned modules, consistent HCL across clouds
- Azure Verified Modules (AVM) increasingly used in ALZ-aligned deployments for both
- **Avoid mixing the two on the same resources** (state/drift conflicts)

### Identity and Data
- **Managed identities** (not connection strings/secrets) for service-to-service auth
- **Microsoft Entra External ID**: successor to Azure AD B2C for customer identity
- CQRS read models in Cosmos DB; event sourcing via Event Hubs; Synapse for analytics
- Key Vault with Private Endpoints for secrets/certs

---

## CQRS and Event Sourcing

**Use incrementally and surgically — not as a default.**

When CQRS/event sourcing hurts:
- Query-heavy with many low-latency read shapes — forces projections, adds operational burden
- Team can't commit to event-schema governance — brittle replays and broken consumers
- Adopted too early, before understanding the domain — painful refactoring later ("day-two problem")

**Recommended sequence:**
1. Strengthen the domain model in current persistence first
2. Introduce CQRS only for read models that actually hurt
3. Add an outbox if you publish messages from the write DB
4. Adopt event sourcing for one aggregate where history is genuinely the product (finance, entitlements, audit-heavy workflows)

**Apply Postel's Law:** conservative in what you emit, liberal in what you accept (event schema evolution).

---

## Observability

### OpenTelemetry (Standard)
- **Python/FastAPI**: `FastAPIInstrumentor.instrument_app(app)`; `azure-monitor-opentelemetry` distro gives one-line `configure_azure_monitor(connection_string=...)` export to Application Insights
- **Critical gotcha**: import the framework module (`import fastapi`) and call `configure_azure_monitor()` **before** instantiating `fastapi.FastAPI()`, or the Requests table won't populate
- Exclude health/readiness endpoints: `OTEL_PYTHON_FASTAPI_EXCLUDED_URLS="health,ping"`
- Use **structlog** for structured logging in Python
- Propagate W3C trace context across Python ↔ Next.js ↔ Azure for end-to-end correlation
- Query Application Insights with KQL: `requests | summarize avg(duration) by name`
- Run only one exporter/processor per signal to avoid duplicate telemetry

### Security
- Zero-trust: verify every request, least privilege, managed identities, Private Endpoints
- Secrets in Key Vault — never in code
- WAF on Front Door/App Gateway; GraphQL query-complexity limits; parameterized queries via ORM; input validation with Pydantic/Zod at boundaries

---

## Zero-Downtime Database Migrations (Expand-Contract)

**Core technique for rolling deployments (multiple pods run old + new code simultaneously):**

1. **Phase 1 EXPAND**: Add new column as nullable; deploy code that reads both old and new (backward-compatible)
2. **Phase 2 MIGRATE**: Backfill new column; verify 100%
3. **Phase 3 CONTRACT**: Add NOT NULL, drop old column; deploy code using only new column

**Never rename/drop a column while old code still runs.**

**Alembic on Postgres operational must-dos:**
- Set `transaction_per_migration=True`
- Set short `lock_timeout` (~4s) — migration fails fast rather than queuing every query behind `AccessExclusiveLock`
- Set `statement_timeout` as safety net
- Create indexes with `CONCURRENTLY`
- Add constraints with `NOT VALID` then `VALIDATE`
- Use `alembic check` in CI to block PRs that change models without a migration
- **Never let multiple pods race `alembic upgrade head`** — run migrations as a dedicated step/init-container before new code starts

---

## CI/CD
- GitHub Actions with environment promotion (dev → staging → prod)
- Turborepo remote cache for frontend; uv for fast Python installs
- **Feature flags** for decoupling deploy from release
- Run DB migrations as a dedicated step before new code starts

---

## Process and People

### Conway's Law
"The modular decomposition of a system and the decomposition of the development organization must be done together, continuously" — Martin Fowler. Use DDD strategic design (event storming + context mapping) to find bounded contexts, then assign one team per bounded context. The **Inverse Conway Maneuver**: deliberately shape teams to mirror the architecture you want.

### Architecture Decision Records (ADRs)
- Coined by Michael Nygard (Nov 15, 2011)
- Standard sections (Nygard's order): **Title, Context, Decision, Status, Consequences**
- Store in-repo as numbered markdown (`doc/adr/NNN-*.md`) — synced with code, gets PR review
- ADR numbers are never reused; treat as immutable — if reversed, keep old ADR marked "superseded" with link to replacement
- ThoughtWorks Technology Radar: "Adopt" — store in source control, not a wiki
- **Failure pattern**: ADRs in Confluence/Notion separated from code don't get read at decision time
- Tooling: `adr-tools` (Nat Pryce), Log4brains (publishes static site), MADR template

### Vertical Slice Architecture (Jimmy Bogard, April 19, 2018)
- Code organized around distinct requests, front-end to back
- **Minimize coupling between slices, maximize coupling within a slice**
- Wins when features are relatively independent and teams own different features
- Tradeoff: without disciplined refactoring, slices devolve into sprawling duplicated logic
- Sharing code between slices is allowed — "minimise isn't zero"

---

## Sequencing Decisions

### New Large Project
1. Domain & teams first (event storming, context map, inverse Conway)
2. Repository & build topology (uv workspace monorepo for Python; Turborepo for frontend)
3. Architecture style: **modular monolith** with enforced module boundaries
4. API contracts (tRPC internally; REST/GraphQL at public boundaries; gRPC for high-throughput internal)
5. Backend skeleton: FastAPI app factory + lifespan; layered architecture; repository + UoW; DI; Alembic with expand-contract from day one
6. Frontend skeleton: App Router + FSD; Server Components default; TanStack Query + Zustand/Jotai + React Hook Form + Zod; Auth
7. Azure foundation: enterprise-scale landing zone; hub-and-spoke; Bicep with AVM; managed identities + Key Vault + Private Endpoints; Log Analytics/Defender/Sentinel
8. Cross-cutting from the start: OpenTelemetry → Azure Monitor; structlog; GitHub Actions with env promotion + feature flags; ADRs in-repo

### Evolving an Existing System
1. **Instrument and observe first** — wire OpenTelemetry; find the painful read models, hot paths, deploy-coupling bottlenecks
2. **Introduce module boundaries inside the monolith** before any extraction; add architecture tests
3. **Strangler fig the first slice** — easiest business-bounded slice; façade; ACL; route a percentage; compare behavior before cutover
4. **Extract a service only on a concrete signal** (independent scaling, team friction, fault isolation)
5. **Adopt CQRS/event sourcing surgically** — only where it pays rent
6. **Migrate data with expand-contract** — always backward-compatible

---

## Staged Rollout Thresholds

| Stage | Description | Advance When |
|---|---|---|
| Stage 0 (weeks 1–4) | Enterprise-scale landing zone; monorepos; CI/CD; OpenTelemetry; ADRs | Request traces end-to-end in Application Insights |
| Stage 1 (months 1–6) | FastAPI + Next.js modular monolith with enforced boundaries; expand-contract Alembic | Module boundaries hold in CI; high deploy frequency, clean rollbacks |
| Stage 2 | Extract services on concrete signals only; strangler fig + ACL; Linkerd only if ≥ a handful of services needing mTLS | Can name the concrete scaling/coupling/regulatory driver |
| Stage 3 | Multi-region active-active (Front Door + Cosmos DB multi-region writes + multi-region APIM) | Business SLA/geographic requirement justifies ~3–6x cost |

**Benchmark triggers:**
- Team crossing ~10 engineers → consider modules
- Team crossing ~30–40 engineers → consider first extraction
- Team crossing ~100 engineers → microservices likely justified
- One module needing ~10x the scale of others → extract it
- CI exceeding ~10–20 min → adopt Turborepo remote cache
- Query latency / read-shape pain → introduce CQRS read models
- Audit/history becoming a business requirement → event-source that one aggregate

---

## Common Mistakes to Avoid
- Premature microservices ("distributed monolith")
- Physical splits without logical splits first
- Copying server data into client stores (fetching into Zustand/Redux)
- `'use client'` at the top of the component tree
- Over-extracting shared packages too early (before a second consumer exists)
- CQRS/event sourcing before understanding the domain
- Renaming/dropping DB columns during rolling deploys
- Relying on Next.js middleware alone for auth (CVE-2025-29927)
- Spoke-to-spoke VNet meshes (bypass hub inspection)
- Mixing Bicep and Terraform on the same resources
- ADRs stored away from code
