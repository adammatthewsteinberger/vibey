---
name: mobile-azure-deployment
description: Use when hosting, deploying, distributing, or running CI/CD for enterprise mobile apps on Azure. Triggers on Intune / MDM vs MAM / App Protection Policies / MAM-WE / Conditional Access, Intune App SDK, Apple Business Manager / Android Enterprise, line-of-business app distribution; Azure API Management as mobile gateway, AKS / Azure Container Apps / Dapr / Easy Auth, Azure Static Web Apps, Cosmos DB change feed & conflict resolution, Azure SignalR / CDN / Functions / Private Endpoints; and post–App Center CI/CD with Azure DevOps / GitHub Actions / Fastlane, Key Vault signing, TestFlight / Play Internal Testing, and OTA (EAS Update / CodePush).
---

# Azure Enterprise Mobile Hosting, Distribution & CI/CD

## Intune / MDM & MAM

- **MDM** = full device management; **MAM** = app-level management.
- **MAM-WE (without enrollment)** protects corporate data on unmanaged **BYOD** via App Protection
  Policies (PIN, encryption, copy/paste/save-as restrictions, **selective wipe checked every 30 min**).
  Must be paired with **Conditional Access requiring an app-protection policy**.
- App Config Policies push settings; on enrolled iOS, `IntuneMAMUPN`/`IntuneMAMOID`/`IntuneMAMDeviceID`
  auto-flow to managed apps. Data-protection framework has three levels (Enterprise basic/L1 → high).
- Apps become managed via the **Intune App SDK** or App Wrapping Tool — the SDK team officially
  supports **native Android/iOS/.NET/MAUI, NOT React Native** (RN integration is unsupported,
  at-your-own-risk; validate with Microsoft).
- Enrollment: **Apple Business Manager (ABM)**, **Android Enterprise** (Work Profile/COPE/COBO).
  Defender for Endpoint and Play Integrity / hardware attestation feed compliance → Entra ID →
  Conditional Access. Distribute LOB `.ipa`/`.apk`/`.aab` as line-of-business apps.

## Backend & data tier

- **Azure API Management** as the mobile gateway (throttling, policies, **JWT validation**,
  developer portal).
- Hosting on **AKS** (ingress, TLS termination) or **Azure Container Apps** (serverless
  scale-to-zero, built-in **Dapr** `1.13.x-msft`, **Easy Auth** built-in).
- **Azure Static Web Apps** (Standard) serves PWA/hybrid content and links a backend under `/api`
  (no CORS; pass-through `X-MS-CLIENT-PRINCIPAL` auth).
- **Cosmos DB** for data: partition strategy; **change feed** (always returns the full document —
  foundational for offline sync); multi-region conflict resolution (**LWW** default on `_ts`, or a
  **Custom merge stored procedure** — NoSQL API only; patch resolves at path level).
- **Azure SignalR** for realtime; **Azure CDN** for assets; **Functions** for event-driven
  endpoints; **Private Endpoints / NSGs / Azure Firewall** for network isolation.

## CI/CD after App Center (retired March 31, 2025)

App Center was retired except for Analytics & Diagnostics (support extended, initially to
June 30, 2026, then to end of March 2027 pending the Azure Monitor mobile migration — **confirm the
live date**). Replacements:

- **Builds:** Azure DevOps Pipelines (macOS agents for iOS, signing certs in **Azure Key Vault**)
  and/or GitHub Actions + **Fastlane** (`match` signing, `gym` build, `deliver`/`supply` store
  uploads, `snapshot`/`screengrab` screenshots). Bitrise/Codemagic are mobile-first alternatives.
- **OTA:** **EAS Build/Update** for Expo; **CodePush** continues standalone — both with version /
  mandatory-update enforcement.
- **Distribution:** TestFlight + App Store Connect API; Google Play Internal Testing; Intune LOB;
  Firebase App Distribution.
- **Bundle optimization:** Hermes bytecode, R8/ProGuard, **AAB over APK**. Semantic versioning + build
  numbering. Manage iOS distribution/enterprise certs and Android keystores in Key Vault.

## Observability tie-in

Crash via Sentry / Crashlytics; performance via New Relic Mobile / Dynatrace / Firebase Performance;
**OpenTelemetry → Azure Monitor Application Insights** (`@azure/monitor-opentelemetry-exporter`).
Hermes lacks OTel auto-instrumentation, so create spans manually and correlate to backend traces via
**W3C Trace Context**. (See `mobile-react-native` for RN-side wiring.)

## Recommended staging

1. **Foundation (wk 0–4):** RN New Architecture (or native), Entra ID + MSAL broker auth, decommission
   App Center, move CI/CD to Azure DevOps/GitHub Actions + Fastlane (certs in Key Vault).
2. **Secure backend & data (wk 4–10):** APIM → Container Apps/AKS → Cosmos DB with Private Endpoints;
   Easy Auth + JWT validation at APIM; offline-first persistence with change-feed sync + explicit
   conflict strategy; public-key cert pinning with a backup pin.
3. **Hardening & distribution (wk 10–16):** Intune App Protection Policies + Conditional Access
   (MAM-WE for BYOD); Play Integrity / App Attest; passkeys/FIDO2 + step-up auth; Sentry + App Insights;
   distribute via Intune LOB / TestFlight / Play Internal Testing.
