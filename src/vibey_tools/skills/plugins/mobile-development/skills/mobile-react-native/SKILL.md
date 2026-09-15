---
name: mobile-react-native
description: Use when building, migrating, or reviewing a React Native (or Expo) mobile app — especially enterprise apps on Azure. Triggers on React Native, Expo, EAS, New Architecture, Fabric, TurboModules, JSI, Codegen, Hermes, Metro, FlashList, Reanimated, React Navigation / Expo Router, TanStack/React Query, Zustand, Redux Toolkit, Jotai, Detox vs Maestro E2E testing, CodePush / EAS Update OTA, react-native-msal / Entra ID auth, and Sentry/App Insights crash & observability. Also triggers on App Center retirement and re-platforming RN CI/CD.
---

# React Native (Primary Enterprise Mobile Platform)

Reference state: mid-2026. Fast-moving version/EOL claims (RN 0.82, Expo SDK 55) should be
reverified at implementation time.

## Adopt the New Architecture now — the legacy Bridge is end-of-life

The New Architecture replaces the asynchronous, JSON-serializing Bridge with four pillars:

- **JSI** — synchronous C++ JS↔native interface (no serialization round-trip).
- **TurboModules** — lazily loaded native modules.
- **Fabric** — the new concurrent renderer.
- **Codegen** — generates type-safe native interfaces from JS specs.

Timeline:
- **RN 0.76 (Oct 23, 2024)** made the New Architecture the **default**; shipped React Native
  DevTools (zero-config, replaces Flipper), a **~15× faster** Metro resolver and ~4× faster
  warm builds, and New-Architecture-only style props `boxShadow` and `filter`. Meta coordinated
  compatibility "with over 850 library maintainers."
- **RN 0.80 (June 12, 2025)** brought React 19.1, **froze** the legacy architecture, and
  deprecated JavaScriptCore in favor of **Hermes** (Hermes is required).
- **RN 0.82** drops the legacy architecture entirely.
- **Expo SDK 53+** defaults to the New Architecture; **SDK 55 (RN 0.83) cannot disable it**.

Migration reality: audit **every third-party native module** for New Architecture
compatibility. Run `npx expo-doctor` to validate against the React Native Directory. Reported
gains (faster cold start, lower memory) are directional vendor/community figures, not controlled
Meta benchmarks.

## Project structure & state management

- **Structure:** feature-first / domain-driven modularization.
- **Split server state from client state:**
  - **Server state** → TanStack Query / React Query v5 (caching, background refetch,
    `useInfiniteQuery` for pagination).
  - **Client state** → **Zustand** (lightweight global state, selective subscriptions);
    **Redux Toolkit + RTK Query** for large apps needing middleware/devtools/time-travel and
    offline-first optimistic-write pipelines; **Jotai** for atomic/scoped state.
- **Type safety:** TypeScript **strict mode** + **Zod** for runtime schema validation at API
  boundaries.

## Navigation

- **React Navigation v7** (stack, native-stack, bottom-tabs, drawer) with typed routes,
  deep-linking config, and conditional navigators keyed on auth state for auth flows.
- **Expo Router** (file-based; v5 on SDK 53, v7 on SDK 55) — higher-level alternative with
  guarded route groups and prefetching.

## Performance

- Replace `FlatList` with Shopify's **FlashList** for large lists.
- `useMemo` / `useCallback` / `React.memo` to control re-renders.
- **Reanimated 3** (UI-thread animations) + **Gesture Handler 2** for 60fps interactions.

## Testing

- **Unit/component (~70% of pyramid):** Jest + React Native Testing Library.
- **E2E:** **Maestro** (YAML, black-box via the accessibility layer, no native build changes,
  sub-1% flakiness) is now generally preferred over **Detox** (gray-box, synchronizes with the
  JS thread, sub-2% flakiness, deeper RN integration but heavy native setup). Jupiter's fintech
  case study found Detox succeeded "only 2 out of 10 times on physical devices" and switched to
  Maestro, slashing MPIN entry from 18s to under 1s via `runScript`.

## Expo / EAS

- **EAS Build** (cloud iOS/Android builds), **EAS Submit** (store submission), **EAS Update**
  (OTA; Hermes-bytecode diffing makes updates substantially smaller in SDK 55).
- **Continuous Native Generation** (`prebuild`) gives managed-to-bare flexibility.

## Azure integration (auth)

- **`react-native-msal`** wraps MSAL for iOS/Android; supports Entra ID and Azure AD B2C /
  External ID.
- iOS config: `CFBundleURLSchemes` = `msauth.$(PRODUCT_BUNDLE_IDENTIFIER)`;
  `LSApplicationQueriesSchemes` = `msauthv2`, `msauthv3`. MSAL uses `ASWebAuthenticationSession`.
- Android config: `BrowserTabActivity` intent filter.
- Use **OAuth 2.0 Authorization Code + PKCE** via the system browser (AppAuth pattern) —
  implicit flow is prohibited; refresh tokens must rotate. **Validate RS256 JWTs server-side**
  against the tenant JWKS endpoint. (See `mobile-security` for full auth/MFA detail.)

## Crash / observability

- **Sentry React Native SDK** (App Start, slow/frozen frames, Hermes profiling, session replay)
  is the leading App Center crash replacement; Firebase Crashlytics and Bugsnag are alternatives.
- Sentry propagates **W3C Trace Context** for end-to-end traces to the backend.
- **OpenTelemetry → Azure Monitor Application Insights** via `@azure/monitor-opentelemetry-exporter`.
  Caveat: **OTel auto-instrumentation does NOT work on Hermes/JSC** — create spans manually and
  correlate to backend traces via W3C Trace Context.

## Re-platform off App Center (retired March 31, 2025)

Visual Studio App Center was retired except for Analytics & Diagnostics (extended runway,
~June 2026 → end of March 2027 — confirm the live date). Replace its pillars:

| App Center function | Replacement |
|---|---|
| CI/CD builds | Azure DevOps Pipelines or GitHub Actions + Fastlane (certs in Azure Key Vault) |
| OTA | CodePush (standalone) or EAS Update with mandatory-update enforcement |
| Crash/perf | Sentry (or Crashlytics) |
| Analytics | Azure Monitor |

## Cross-cutting

a11y via `accessibilityLabel`/`accessibilityRole`/screen-reader props; Universal Links (iOS) /
App Links (Android) via AASA / Digital Asset Links; **Turborepo or Nx** for monorepos; i18n via
**i18next + react-native-localize**. Note: Microsoft does **not** officially support the Intune
App SDK on React Native (see `mobile-azure-deployment`).
