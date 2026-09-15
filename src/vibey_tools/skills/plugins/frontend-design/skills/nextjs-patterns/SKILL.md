---
name: nextjs-patterns
description: "Production-grade Next.js App Router patterns covering rendering strategy (RSC, PPR, Cache Components), data fetching (parallelization, Suspense, React cache), mutations (Server Actions, next-safe-action, Zod), authentication (Auth.js v5, DAL, JWT/session tradeoffs), state management (URL state, Zustand, Jotai), performance (images, fonts, bundle analysis, Turbopack), security (CVE-2025-29927, rate limiting, input validation), TypeScript patterns, testing (Vitest, Playwright), styling (Tailwind, CSS Modules), and deployment (Vercel vs self-hosting, Docker). Use for any Next.js App Router architecture, debugging, or implementation question."
---

# Next.js App Router: Production-Grade Field Guide

## Core Principle

**Default to the server, opt into the client at the leaves.** Keep Server Components as the default; push `'use client'` to the smallest interactive leaf; fetch data on the server (parallelized with `Promise.all`); stream with Suspense; treat every Server Action and Route Handler as a public, unauthenticated endpoint that must independently validate input (Zod) and re-check authorization.

## Version Reality (as of June 2026)

| Version | Released         | Key change                                                        |
|---------|------------------|-------------------------------------------------------------------|
| v14     | —                | `fetch` cached by default; experimental PPR                       |
| v15     | Oct 21, 2024     | `fetch` **uncached by default**; cache opt-in required            |
| v16     | Oct 21, 2025     | Cache Components stable (`cacheComponents: true`, `use cache`); PPR is now default behavior when enabled; React Compiler 1.0 stable but **opt-in**; `middleware.ts` renamed to `proxy.ts` (Node.js runtime) |

**This is the #1 source of cache bugs.** Before debugging caching issues, always identify which major version the codebase is on.

---

## Architecture and Project Structure

### Key Rule: `app/` is for Routing Only

Keep `page.tsx`/`layout.tsx` thin. Move logic into a feature/domain structure:

```
src/
  app/              # routing only — thin page/layout files
  features/         # domain logic: auth/, products/, checkout/
  server/           # DAL, DB queries, service functions
  lib/              # shared pure utilities
  components/       # genuinely shared UI
```

**Why not layer-based buckets (`components/`, `hooks/`, `utils/`)?** They read well early but degrade into high-fan-in dependency magnets at scale. Feature-based structure keeps a feature's code together and makes it testable and deletable.

### Colocation

Folders in `app/` are not routable until a `page`/`route` file exists. Safely colocate components, tests, and utilities inside route segments.

- `_folderName` — private folder excluded from routing
- `(groupName)` — route group: organizes without affecting URL; enables multiple root layouts

### Data Access Layer (DAL)

Establish a DAL from day one — a service/repository layer that:
- Is the only place that touches the database
- Re-verifies auth/authorization before every read or mutation
- Is independently testable (pure functions, no Next.js coupling)
- Is reusable across Server Actions, Route Handlers, webhooks, and cron jobs

Putting business logic directly in Server Actions makes it untestable; extract pure service functions.

### Monorepo (Turborepo)

Turborepo is the default (maintained by Vercel). Critical configuration:
- Set `outputs` in `turbo.json` or every task rebuilds from scratch
- Build shared packages before dependent apps
- Use `transpilePackages` for internal packages
- Use `output: 'standalone'` + correct `outputFileTracingRoot` for deploying a single app

**Barrel exports:** Large `index.ts` barrels hurt dev compile time and tree-shaking. `experimental.optimizePackageImports` auto-rewrites named imports for known libraries (lucide-react, @mui/material) — but does NOT reliably work for internal workspace packages with Turbopack/symlinks (pnpm). For your own barrel files, refactor to direct imports.

---

## App Router Rendering Patterns

### Server vs. Client Decision Framework

**Use Server Components (default) for:**
- Data fetching
- Heavy/secret-bearing dependencies (DB, SDKs, API keys)
- Large lists, markdown/MDX
- Composition without interactivity

**Use Client Components (`'use client'`) only for:**
- Interactivity (`onClick`, `useState`, `useEffect`)
- Browser APIs (`window`, `localStorage`, `navigator`)
- Animations, focus management

**Common mistakes:**
- Putting `'use client'` high in the tree — promotes whole subtree, ships unnecessary JS, kills streaming/SEO
- Reading `cookies()`/`headers()` in layouts — forces the whole route dynamic, disables static/PPR
- Fetching with `useEffect` instead of server fetch — delays render, hurts LCP/SEO, creates waterfalls

### Passing Server Components into Client Components

To avoid promoting whole subtrees to the client, pass Server Components as `children`:

```tsx
// DO: server component renders and passes as children prop
<ClientWrapper>{/* server component here */}</ClientWrapper>

// DON'T: importing a server component inside a client component
// (silently promotes it to client)
```

### Layouts, Parallel Routes, and Intercepting Routes

**Layouts:** Cannot pass data to children via props. Each segment that needs data fetches it independently — fetch memoization makes this cheap.

**Parallel routes (`@slot`):** Render multiple independent segments in one layout. Real uses:
- Dashboards with independent streaming/error/loading per pane
- Role-based conditional rendering (the admin slot is never sent to non-admin browsers)
- Every slot needs a `default.tsx` for hard navigations or the app errors

**Intercepting routes (`(.)`, `(..)`, `(...)`):** Combined with parallel routes, the canonical use is modals with shareable URLs — Instagram-style photo overlays, login modals with a standalone `/login` page. Known gotchas:
- `(..)` counts route *segments*, not filesystem levels (`@slot` folders are skipped)
- Multiple parallel slots can show multiple modals
- Modals can persist on parent navigation without a catch-all/conditional

### Loading UI and Error Boundaries

- `loading.tsx` auto-wraps a route in Suspense with the file's content as fallback
- Place Suspense boundaries around distinct data-loading subtrees with **dimension-matched skeleton fallbacks** (avoids CLS)
- Too-coarse boundaries reintroduce waterfalls; too-fine add overhead

**`error.tsx` must be a Client Component:**
```tsx
'use client'
export default function Error({ error, reset }: { error: Error; reset: () => void }) { ... }
```

`global-error.tsx` is the root fallback — must render its own `<html>` and `<body>`, and cannot use providers above it.

---

## Data Fetching Patterns

### Caching and Revalidation

In **v15+**, `fetch` is uncached by default. To cache:
- `fetch(url, { cache: 'force-cache' })` — permanent until revalidated
- `fetch(url, { next: { revalidate: 60 } })` — time-based ISR
- `export const revalidate = 60` — segment-level time-based

Invalidation strategies:
- `revalidatePath('/path')` — invalidate all data behind a URL (start here, easier to reason about)
- `revalidateTag('tag')` — fine-grained, invalidates data behind multiple URLs sharing a tag

In **v16 Cache Components** (`use cache`):
- `use cache` directive + `cacheLife()` + `cacheTag()` extends tagging beyond `fetch` to any async work (DB queries, filesystem reads)
- `updateTag()` is Server-Action-only for read-your-own-writes

### Parallelizing Fetches (Avoiding Waterfalls)

```tsx
// BAD: sequential — each waits for the previous
const user = await getUser(id)
const posts = await getPosts(id)

// GOOD: parallel — both fire at once
const [user, posts] = await Promise.all([getUser(id), getPosts(id)])
// Use Promise.allSettled for partial-failure tolerance
```

**Preload pattern** — start a fetch early before a blocking call:
```tsx
void preloadItem(id)  // fire-and-forget, starts fetching immediately
const critical = await getCriticalData()
```

### React cache() for Deduplication

```tsx
import { cache } from 'react'

export const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } })
})
// Called anywhere in the render tree — executes only once per request
```

Use the `server-only` package to prevent accidental client import of DB-touching functions.

### React Query / SWR with App Router

Still valuable for: client-side caching, optimistic updates, polling/real-time, and direct cache manipulation. Pattern: fetch initial data on the server, hydrate, then use TanStack Query client-side for live updates.

---

## Mutations: Server Actions

Server Actions compile to **public POST endpoints**. Built-in protections: Origin/Host comparison, POST-only, encrypted non-deterministic action IDs, dead-code elimination.

You **still must:**
1. Validate every input with Zod (`safeParse`, never `parse`)
2. Re-check auth and authorization (IDOR/ownership — don't trust the user's claimed ID)
3. Rate-limit expensive/auth endpoints
4. Avoid leaking secrets through closures (move actions to separate files)

### next-safe-action (recommended)

```tsx
import { createSafeActionClient } from 'next-safe-action'
import { z } from 'zod'

const action = createSafeActionClient()
  .inputSchema(z.object({ id: z.string().cuid() }))
  .action(async ({ parsedInput, ctx }) => {
    // input is already validated; ctx has auth from .use() middleware
    return await updateItem(parsedInput.id)
  })
```

`next-safe-action` provides: composable `.use()` middleware (auth, rate-limit), `useAction`/`useOptimisticAction` hooks, Standard Schema support (Zod, Valibot, ArkType). `zsa` is an alternative.

### Form Hooks (React 19)

- `useActionState` — wraps a Server Action with state (pending, error, data)
- `useFormStatus` — gives `pending` state to submit buttons inside a form
- `useOptimistic` — instant UI feedback while action confirms

---

## State Management

### Decision Framework

| State type              | Best tool                                      |
|-------------------------|------------------------------------------------|
| URL/shareable (filters, pagination, search) | nuqs (`parseAsInteger`, `parseAsArrayOf`) |
| Server state            | Keep on server; React `cache()` + Server Components |
| Global client UI state  | Zustand (single store) or Jotai (atomic/derived) |
| Form state              | `react-hook-form` + `zodResolver`              |
| Context (theme, locale) | React Context in a Client Component provider  |

**Critical App Router rule:** Never create a global store at module level on the server — it leaks state across requests. Create per-request stores via provider patterns.

### nuqs Caveats

- Not for large/private objects
- Frequent URL updates can cause perf issues — use debouncing/`limitUrlUpdates`
- Does not replace a global client store

### Context Pitfalls

Context providers must be Client Components, don't cross the server/client boundary, and re-render all consumers (performance trap). Use for low-frequency values only.

---

## Authentication

### Auth.js v5

Single `auth.ts` config exports `{ auth, handlers, signIn, signOut }`. Universal `auth()` works in Server Components, Route Handlers, and middleware.

**Split config for edge compatibility:**
- `auth.config.ts` — edge-safe, no DB adapter; used in middleware for JWT verification
- `auth.ts` — Node.js runtime, with DB adapter for session storage

### Sessions: JWT vs. Database

| Strategy       | Pros                                | Cons                              |
|----------------|-------------------------------------|-----------------------------------|
| JWT            | Stateless, edge-verifiable, fast   | Hard to revoke                    |
| Database       | Revocable, single source of truth  | DB call per request; edge can't reach most DBs |

Common middle ground: short-lived JWT (~15 min) + refresh token in DB.

**Always store session tokens in `httpOnly`, `secure`, `sameSite` cookies — never localStorage (XSS).**

### Defense in Depth: Three Layers

1. **Middleware/proxy** — optimistic route filtering (fast, edge); NOT a security boundary (CVE-2025-29927)
2. **Server Components / Route Handlers** — verify for data access
3. **Server Actions** — verify before every mutation

UI role checks are UX, not security. Include API routes in the middleware matcher (common bug: protecting `/dashboard` but leaving `/api/dashboard/*` open).

---

## TypeScript Patterns

### Zod: Runtime Validation Backbone

TypeScript types are erased at runtime. `userId: string` does not stop `{"userId": {"$ne": null}}`.

```tsx
const schema = z.object({ userId: z.string().cuid() })
const result = schema.safeParse(input)
if (!result.success) return { error: result.error.flatten().fieldErrors }
const { userId } = result.data
```

Validate every Server Action and Route Handler input. Infer types with `z.infer<typeof schema>`.

### Typed Routes

Enable `typedRoutes` in `next.config.ts` to catch invalid `<Link href>` at compile time.

### tRPC

Choose tRPC (T3 stack) when you want end-to-end typed RPC across a separate client. tRPC v11 (2025) integrates with RSC — call procedures directly in Server Components. `create-t3-app` scaffolds App Router by default.

---

## Testing Patterns

| Layer                          | Tool                              | Notes                                              |
|--------------------------------|-----------------------------------|----------------------------------------------------|
| Unit (sync Server/Client Components, Server Actions as plain functions, Zod schemas) | Vitest + React Testing Library | Vitest **cannot render async Server Components** — push those to E2E |
| E2E (async RSC, auth flows, checkout, cookies/middleware) | Playwright | Configure `webServer`; preferred over Cypress     |
| Mocking                        | Vitest mocks for `next/navigation`, `next/headers` | Mocky Balboa for server-side network mocking in Playwright |

---

## Styling

### Compatibility Matrix

| Approach                    | RSC-compatible | Runtime cost | Notes                              |
|-----------------------------|----------------|--------------|------------------------------------|
| Tailwind CSS                | Yes            | Zero         | Default for new App Router projects; foundation for shadcn/ui |
| CSS Modules                 | Yes            | Zero         | Built-in, scoped, zero-config      |
| vanilla-extract / Panda CSS / StyleX | Yes   | Zero         | Zero-runtime CSS-in-JS             |
| styled-components / Emotion | No (requires `'use client'` boundary and registry) | Runtime | Inherent perf trade-offs in App Router |

**Migration advice:** Don't rip out a working styled-components codebase wholesale. Adopt Tailwind for new components, or move to zero-runtime. Dark mode: `next-themes` with class-based Tailwind `dark:`.

---

## Performance Optimization

### Core Primitives

| Tool            | What it does                                                  | Critical detail                                 |
|-----------------|---------------------------------------------------------------|-------------------------------------------------|
| `next/image`    | Automatic WebP/AVIF, lazy loading, responsive srcset         | Set `priority` on LCP image; always provide `width`/`height` |
| `next/font`     | Self-hosts fonts at build time; zero runtime network request | Eliminates layout shift + external DNS; `display: 'swap'` built-in |
| `next/script`   | Controls third-party script loading strategy                  | `afterInteractive`, `lazyOnload`, experimental `worker` |
| `next/dynamic`  | Code splitting for heavy components                           | `ssr: false` for client-only libs               |
| `@next/bundle-analyzer` | Visualize bundle composition                          | Run with `ANALYZE=true`; set CI size budgets    |

Common bundle culprits: moment.js (→ date-fns/dayjs), full lodash (→ lodash-es or per-method), full icon libraries (→ `optimizePackageImports`).

### PPR / Cache Components

Mental model: *everything outside `<Suspense>` is static, everything inside is dynamic.* The static shell is served from the edge (TTFB ~40–90ms), dynamic holes stream in one HTTP response.

**Best for:** Pages with a stable shell and small dynamic regions (product pages, pricing, marketing surfaces with ~80% cacheable layout, ~20% per-user data).

**Skip PPR for:** 100%-personalized pages (account settings, live dashboards), fully authenticated apps (generic shell has little CDN value).

Debugging: a single `cookies()`/`headers()`/`connection()` call **outside** Suspense makes the route fully dynamic. Use `NEXT_LOG_LEVEL=debug next build` to print why a route is dynamic.

### Turbopack (Default in v16)

- Dev: dramatically faster HMR vs Webpack
- Production: one controlled test (Cal.com) showed ~19% faster median cold build but **~211KB larger shared chunk, +279KB median First Load JS per route** — Turbopack tree-shaking is still maturing
- Measure First Load JS before switching production builds
- Hybrid (Turbopack dev, Webpack prod) is a valid fallback
- Some custom Webpack plugins and Sass custom functions aren't supported

---

## Security

### CVE-2025-29927 (CVSS 9.1) — Middleware Auth Bypass

The `x-middleware-subrequest` header could bypass all middleware-based authorization. Published March 21, 2025; reported by Rachid Allam.

- **Patched in:** 12.3.5, 13.5.9, 14.2.25, 15.2.3
- **Not affected:** Vercel-hosted deployments
- **At risk:** Self-hosted (`next start`)
- **Architectural lesson:** Middleware is not a security boundary — auth must live in the DAL

### May 2026 Security Release (13 advisories)

Published May 6–7, 2026 — covering auth bypass, SSRF, cache poisoning, XSS, RSC denial-of-service (CVE-2026-23870).

- Original patches (15.5.16 / 16.2.5) were superseded after an incomplete fix
- **Pin to:** 15.5.18 / 16.2.6 for Turbopack users
- SSRF advisory (GHSA-c4j6-fc7j-m34r) affects only self-hosted deployments

### Rate Limiting

`@upstash/ratelimit` + Upstash Redis (sliding window) is the dominant pattern.

Key rules:
- A global 100 req/min cap is not endpoint security — set low, specific thresholds on the right assets
- In-memory Maps don't survive edge instances/redeploys; use external Redis
- Apply to: login, OTP, password reset, expensive/AI endpoints

### Input Validation and SSRF Prevention

- Validate all inputs server-side with Zod
- For SSRF: restrict/allowlist server-side fetch targets
- Validate `returnTo`/redirect params to relative URLs only (open-redirect/phishing prevention)

### Secrets

- Never expose via `NEXT_PUBLIC_` env vars (these are baked into the client bundle at build time)
- Use the `server-only` package to prevent accidental client import
- Use React taint APIs (`taintObjectReference`, `taintUniqueValue`) to prevent passing sensitive objects to Client Components
- Set `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` for consistent keys across instances

---

## Deployment

### Vercel vs. Self-Hosting

| Factor                  | Vercel                                    | Self-hosted (Docker/K8s)                  |
|-------------------------|-------------------------------------------|-------------------------------------------|
| Setup                   | Zero-config                               | You own CI/CD, cache warming, health probes |
| ISR                     | Distributed automatically                 | Cache lives in `.next/cache`, not durable without custom cache handler |
| Image optimization      | Automatic                                 | Requires `sharp` installed                |
| Version skew protection | Built-in                                  | Manual                                    |
| Cost                    | Significant above ~10M requests/month     | Predictable                               |

### Self-Hosting Configuration

```dockerfile
# output: 'standalone' traces exact deps into a minimal Node server
# Copy public/ and .next/static separately
```

Critical self-hosting checklist:
- Disable reverse-proxy buffering for streaming: `proxy_buffering off`, `X-Accel-Buffering no`, HTTP/1.1
- `NEXT_PUBLIC_` vars are build-time — need rebuild or separate images per environment
- Set `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` for multi-instance consistency
- Separate liveness/readiness probes (DB failures → affect readiness, not liveness)

### Output Modes

- `output: 'standalone'` — minimal Node server (~200MB image vs 1GB+); required for clean Docker/K8s
- `output: 'export'` — fully static (replaces old `next export`)

---

## Anti-Patterns

| Anti-pattern                                        | Why it's wrong                                             |
|-----------------------------------------------------|------------------------------------------------------------|
| Over-using `'use client'`                           | Promotes subtrees, bloats bundles, breaks streaming/SEO    |
| `useEffect` for data that could be server-fetched   | Delays render, hurts LCP/SEO, creates waterfalls           |
| Reading `cookies()`/`headers()` in layouts          | Forces entire route dynamic, disables static/PPR           |
| N+1 queries                                         | Fetch in a loop; batch with `Promise.all`/DataLoader       |
| Trusting page-level auth for Server Actions         | Actions are separate public endpoints; re-verify each time  |
| Trusting TypeScript types at runtime                | Always validate with Zod                                   |
| Module-level global stores on the server            | Leaks state across requests                                |
| Fine-grained `revalidatePath` on everything         | Over-invalidation busts unrelated caches; use tags         |
| Assuming v14 caching in a v15/v16 codebase          | `fetch` is no longer cached by default                     |

---

## Staged Setup Recommendations

**Stage 1 — Foundation (any new project):**
`create-next-app` (or `create-t3-app` for typed RPC + Prisma/Drizzle + Auth.js) on App Router, `src/` directory, TypeScript strict, Tailwind, ESLint. Feature-based structure from day one; establish a DAL.

**Stage 2 — Data and mutations:**
Server Actions with `next-safe-action` + Zod; `react-hook-form` + `zodResolver` on client; `useActionState`/`useOptimistic` for UX. Decide caching explicitly.

**Stage 3 — Auth and security hardening (before launch):**
Auth.js v5 with split edge/Node config; JWT + DB refresh token. Verify auth in middleware AND DAL AND every Server Action. Add `@upstash/ratelimit` to auth and expensive endpoints. Pin Next.js to a patched version.

**Stage 4 — Performance and scale:**
`next/image`, `next/font`, `next/script`, `next/dynamic`; bundle analysis with CI budgets; PPR/Cache Components for mixed static+dynamic pages. Target: LCP <2.5s, INP <200ms, CLS <0.1.

**Stage 5 — Deployment decision:**
Default Vercel for time-to-market. Re-evaluate self-hosting at ~10M+ requests/month, compliance/data-residency needs, or existing K8s platform.
