---
name: mobile-security
description: Use for mobile app security, threat compliance, secure auth, and MFA on iOS/Android/React Native. Triggers on OWASP MASVS v2.1.0 / MASTG / MAS Testing Profiles, OWASP Mobile Top 10 2024 (M1 Improper Credential Usage), hardware-backed key storage (iOS Keychain / Secure Enclave, Android Keystore / StrongBox / key attestation), biometric-bound keys, certificate/public-key (SPKI) pinning, TLS 1.3, OAuth 2.0 Authorization Code + PKCE (RFC 7636/8252), JWT refresh-token rotation, root/jailbreak detection, App Attest / Play Integrity, binary protection (R8/ProGuard, RASP, FLAG_SECURE), MobSF in CI, privacy (GDPR/CCPA/ATT), and FIDO2/passkeys / TOTP / Entra ID MFA / Conditional Access / MSAL broker SSO.
---

# Mobile Security & MFA

Design to **OWASP MASVS v2.1.0 / MASTG** and the **OWASP Mobile Top 10 2024**.

## Standards & compliance

- **MASVS v2.1.0** (released Jan 18, 2024) adds **MASVS-PRIVACY**; eight control groups (24
  requirements): **STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE, RESILIENCE, PRIVACY**, verified via
  **MASTG**. From v2.0.0 the standard "does not contain verification levels … replaced by **MAS Testing
  Profiles**" — so RFP language asking for "MASVS Level 2" is stale framing.
- **Mobile Top 10 2024** (first major revision since 2016): **M1 Improper Credential Usage** (now #1 —
  hardcoded API keys/secrets in APKs/IPAs), M2 Inadequate Supply Chain Security, M3 Insecure
  Authentication/Authorization, M4 Insufficient Input/Output Validation, M5 Insecure Communication,
  M6 Inadequate Privacy Controls, M7 Insufficient Binary Protections, M8 Security Misconfiguration,
  M9 Insecure Data Storage, M10 Insufficient Cryptography.

## Secure storage (hardware-backed everywhere)

- **iOS:** Keychain accessibility — use `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` for
  non-syncable secrets; `.biometryCurrentSet` invalidates keys on biometric-enrollment change;
  **Secure Enclave** for non-exportable private keys; `NSFileProtection` for files.
- **Android:** Keystore **TEE** vs **StrongBox** (API 28+, dedicated SE) with **key attestation**;
  verify `isInsideSecureHardware()`.
- **Both:** SQLCipher; biometric-bound keys via `LAContext` (iOS) / `BiometricPrompt.CryptoObject`
  (Android).
- **Root/jailbreak detection + attestation:** **Play Integrity API** (replaced SafetyNet) on Android;
  **App Attest / DeviceCheck** on iOS.

## Secure communications

- Enforce **TLS 1.3**.
- **OAuth 2.0 Authorization Code + PKCE** (RFC 7636) per **RFC 8252**: external browser/AppAuth
  (no embedded WebView), PKCE mandatory, **implicit flow prohibited**. **mTLS** for high-assurance
  calls. **JWT refresh-token rotation with reuse detection.**
- **Certificate pinning — pin public keys (SPKI SHA-256), not certificates, and always keep a backup
  pin:**
  - Android: OkHttp `CertificatePinner` (custom `OkHttpClientFactory` on `OkHttpClientProvider`) or
    TrustKit; plus Network Security Configuration.
  - iOS: TrustKit (`kTSKPublicKeyHashes`, requires primary + backup pin); plus ATS.
  - RN: `react-native-ssl-public-key-pinning` wraps both.

## Binary / runtime protection

Android **R8/ProGuard** (or commercial DexGuard) obfuscation; iOS strip debug symbols + compiler
hardening; signature/integrity checks; **Frida/debugger detection (RASP)**; **`FLAG_SECURE`**
(Android) and screen-capture detection (iOS) to block screenshots; clipboard restrictions.

## Security testing in CI

Wire **MobSF** (static/dynamic) into CI to **fail builds on MASVS-CRYPTO/STORAGE violations**;
Drozer, objection/Frida for deeper testing.

## Privacy

GDPR (consent, data minimization, right to deletion), CCPA, **Apple Privacy Nutrition Labels**,
Android Privacy Dashboard (12+), **App Tracking Transparency** (iOS 14.5+), Microsoft Purview for
enterprise data classification.

## MFA on mobile

- **FIDO2/WebAuthn platform authenticators & passkeys** (phishing-resistant, bound to the RP ID;
  private key never leaves the device):
  - iOS: `AuthenticationServices` + AASA associated domains + iCloud Keychain sync.
  - Android: **Credential Manager API** (unified passkeys/passwords/federated; third-party providers
    on Android 14+) + Digital Asset Links.
- **TOTP** (RFC 6238); push MFA via **Microsoft Authenticator with number matching**; **SMS OTP is
  discouraged** (SIM-swap/SS7; NIST SP 800-63B restricts it).
- **Entra ID MFA** via MSAL + **Conditional Access**; **Entra External ID (B2C)** flows for RN;
  **step-up auth** for high-risk operations (MASVS-AUTH "additional authentication"); OAuth **Device
  Authorization Grant** (RFC 8628) for constrained devices.
- **Silent SSO via the MSAL broker** — Authenticator holds the **PRT** in Secure Enclave /
  hardware-backed Keystore (iOS uses URL-scheme IPC; Android uses the broker within the Work Profile).
  Multi-account support via Intune multi-identity.
