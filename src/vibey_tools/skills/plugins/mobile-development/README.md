# Mobile Development Plugin

A production reference for **enterprise mobile application development on Azure** (state: mid-2026).
The gold-standard stack is **React Native (New Architecture)** with an Azure-native backend
(APIM → Container Apps/AKS → Cosmos DB), secured with MSAL + Entra ID, OAuth 2.0 Authorization Code
+ PKCE, and Intune App Protection Policies — with native Swift/SwiftUI and Kotlin/Compose where deep
platform integration or the Intune App SDK is required. Two facts shape every decision: **Visual
Studio App Center was retired March 31, 2025**, and security must target **OWASP MASVS v2.1.0** and
the **Mobile Top 10 2024**.

- **mobile-react-native**: React Native New Architecture (JSI/TurboModules/Fabric/Codegen, Hermes),
  project structure and state (TanStack Query + Zustand/Redux/Jotai), React Navigation/Expo Router,
  FlashList/Reanimated performance, Jest + Maestro vs Detox testing, Expo/EAS, `react-native-msal`
  auth, Sentry/App Insights observability, and re-platforming off App Center.
- **mobile-native-platforms**: Native iOS (Swift 6 concurrency, SwiftUI, TCA/MVVM, SPM, App Attest)
  and native Android (Coroutines/Flow, Compose UDF/MVI, side-effect APIs, Hilt, Room/DataStore/
  WorkManager, Keystore/StrongBox) — and when to choose native over React Native.
- **mobile-ux-and-patterns**: Apple HIG and Material Design 3, WCAG 2.2 AA and the EU Accessibility
  Act, Clean Architecture/MVVM/MVI, Repository and offline-first sync patterns, push via Azure
  Notification Hubs, and persistence libraries (MMKV, WatermelonDB, Realm EOL, SQLCipher).
- **mobile-azure-deployment**: Intune MDM/MAM and MAM-WE with Conditional Access, APIM → Container
  Apps/AKS → Cosmos DB (change feed, conflict resolution), Azure Static Web Apps, and post–App Center
  CI/CD with Azure DevOps/GitHub Actions/Fastlane, Key Vault signing, and OTA.
- **mobile-security**: OWASP MASVS/MASTG and Mobile Top 10 2024, hardware-backed key storage, SPKI
  certificate pinning, TLS 1.3 + OAuth/PKCE, App Attest/Play Integrity, binary/runtime protection,
  MobSF in CI, privacy regimes, and FIDO2/passkeys + Entra ID MFA / MSAL broker SSO.

