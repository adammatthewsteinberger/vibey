---
name: mobile-ux-and-patterns
description: Use for mobile UI/UX standards, accessibility compliance, mobile architecture/design patterns, and offline-first data persistence. Triggers on Apple HIG, Material Design 3 / M3 Expressive, touch-target sizing, dark mode, design tokens, WCAG 2.2 AA and the EU Accessibility Act (EAA/BFSG), Clean Architecture / MVVM / MVI, Repository pattern, offline-first sync & conflict resolution (LWW/CRDT), feature flags / remote config, push architecture (APNs/FCM/Azure Notification Hubs), and persistence libraries MMKV, WatermelonDB, Realm (EOL), and SQLCipher / op-sqlite / expo-sqlite.
---

# Mobile UI/UX Gold Standards & Design Patterns

## UI/UX standards

- **Apple HIG** (iOS): 44pt minimum hit target, Dynamic Type.
- **Material Design 3 / M3 Expressive** (Android): 48×48dp touch target, spring motion, dynamic color.
- **Cross-platform RN:** pick one primary design language; adapt navigation/gesture/typography for
  the other.
- Support **dark mode** (system-driven; never hardcode colors/fonts), design tokens/theming,
  skeleton/loading and **optimistic-UI** states, offline-first error states, and biometric auth UX.

## Accessibility is now a legal requirement, not optional

- Baseline: **WCAG 2.2 Level AA**, including **2.5.8 Target Size (Minimum) = 24×24 CSS px** (new in
  WCAG 2.2, Oct 2023; 24px-spacing exception). AAA 2.5.5 = 44×44. **2.5.1** (pointer gestures)
  requires single-pointer alternatives to swipes/pinches.
- **The EU Accessibility Act (Directive (EU) 2019/882) has been enforced since June 28, 2025.**
  Penalties are material: Germany's **BFSG** (Bundesnetzagentur) up to **€100,000/violation**;
  Spain up to **€1,000,000** for very serious infractions plus business suspension up to 3 years;
  **Ireland uniquely carries criminal liability** (up to €60,000 and/or 18 months imprisonment).

## Mobile design patterns

- **Clean Architecture** layering: UI → Domain → Data.
- **MVVM/MVI** unidirectional flow.
- **Repository pattern** abstracting remote + local sources.
- **Offline-first** with sync + conflict resolution: last-write-wins vs operational/field-merge CRDT.
- **DI** via Hilt (Android) / TCA `@Dependency` or factory injection (iOS) — avoid the
  service-locator anti-pattern.
- **Feature flags / remote config** via Azure App Configuration or Firebase Remote Config.
- **Push architecture:** APNs + FCM unified behind **Azure Notification Hubs** (tags, templates,
  per-message telemetry). Note: FCM legacy API retired June 2024 — use **FCM v1**; APNs token auth
  required.
- **Background processing:** BGTaskScheduler (iOS) / WorkManager (Android) / `expo-background-task`.
- Result/sealed-class error types; REST vs GraphQL (persisted queries, N+1 mitigation); cursor-based
  pagination / infinite scroll.

## Offline-first persistence libraries

- **MMKV** (Tencent, C++; `react-native-mmkv` V4 is a Nitro Module requiring RN 0.76+):
  synchronous key-value, "~30x faster than AsyncStorage" per the official README, built-in encryption
  (default AES-128, switchable to AES-256 via `encryptionKey`) — **store the key in
  Keychain/Keystore**. Best for small/medium data, not large datasets.
- **WatermelonDB** (Nozbe, MIT): SQLite-backed, lazy-loaded, observable; queries run on a separate
  native thread; two-phase sync via `pullChanges`/`pushChanges` with a `lastPulledAt` timestamp;
  per-column client-wins conflict resolution; scales to tens of thousands+ records; needs a dev build
  (no Expo Go). (Large-scale "sync success" figures are unverified vendor claims.)
- **Realm / Atlas Device SDK: DEPRECATED.** MongoDB announced deprecation Sept 9, 2024; **Atlas
  Device Sync reached EOL Sept 30, 2025.** Local Realm DB remains open source (v20+ without sync) but
  is maintenance-only. **Do not start new projects on Realm Sync** — if it was in scope, replan now.
- **SQLCipher** (Zetetic): transparent 256-bit AES SQLite encryption (`PRAGMA key`). The official
  Zetetic RN package is Enterprise-only; free paths are **op-sqlite** (`"sqlcipher": true`) and
  **expo-sqlite** (`{"useSQLCipher": true}` config plugin + prebuild, not in Expo Go).

See `mobile-security` for hardware-backed key storage that protects the MMKV/SQLCipher keys.
