---
name: pci-dss-v4
description: Use whenever working on PCI DSS v4.0.1 compliance, SAQ selection, cardholder data environment scoping, or payment security assessments. Covers SAQ-A, SAQ-A-EP, SAQ-B-IP selection and requirements mapping, new v4.0 customized approach, and key technical controls. Trigger on any mention of PCI, cardholder data, CDE, payment card, SAQ, QSA, or merchant compliance.
---

# PCI DSS v4.0.1 — Payment Card Industry Data Security Standard

## What This Skill Does

This skill guides you through PCI DSS v4.0.1: scoping your cardholder data environment, selecting the right SAQ, assessing compliance gaps, and implementing the 12 requirements. It covers the major changes from v3.2.1 to v4.0, the new customized approach, and practical remediation for common gaps.

---

## Framework Overview

PCI DSS is administered by the PCI Security Standards Council (PCI SSC). Version 4.0 was released March 2022; version 4.0.1 (minor clarifications) was released June 2024. All v3.2.1 assessments retired December 31, 2024 — v4.0.1 is now the only active version.

**Who must comply:**
- Any entity that stores, processes, or transmits cardholder data (CHD) or sensitive authentication data (SAD)
- Merchants of all levels; service providers; acquirers; issuers

**Compliance validation:**
- **Level 1 merchants** (>6M transactions/year): Annual QSA assessment (ROC) + quarterly scans
- **Level 2-4 merchants**: SAQ + quarterly ASV scans (Level 2 may require QSA)
- **Service providers**: Level 1 = ROC by QSA; Level 2 = annual SAQ or QSA

---

## The 12 Requirements — 6 Goals

### Goal 1: Build and Maintain a Secure Network and Systems
- **Req 1:** Install and maintain network security controls (firewalls, ACLs, segmentation)
- **Req 2:** Apply secure configurations to all system components (no vendor defaults, CIS Benchmarks)

### Goal 2: Protect Account Data
- **Req 3:** Protect stored account data (minimize storage, mask PAN, encrypt SAD)
- **Req 4:** Protect cardholder data with strong cryptography during transmission (TLS 1.2+)

### Goal 3: Maintain a Vulnerability Management Program
- **Req 5:** Protect all systems against malware (EDR, AV, anti-phishing)
- **Req 6:** Develop and maintain secure systems and software (patch management, SDLC)

### Goal 4: Implement Strong Access Control Measures
- **Req 7:** Restrict access to system components by business need to know
- **Req 8:** Identify users and authenticate access (MFA, password policy, no shared credentials)
- **Req 9:** Restrict physical access to cardholder data


### Goal 5: Regularly Monitor and Test Networks
- **Req 10:** Log and monitor all access to system components and cardholder data (SIEM, audit trails)
- **Req 11:** Test security of systems and networks regularly (pen testing, ASV scans, IDS/IPS, FIM)

### Goal 6: Maintain an Information Security Policy
- **Req 12:** Support information security with organizational policies and programs (risk assessments, security awareness, vendor management)

---

## SAQ Selection Logic

The Self-Assessment Questionnaire type depends on how your system handles card data.

### SAQ A — Fully Outsourced Card Acceptance
**Who qualifies:**
- Card-not-present (e-commerce or mail/telephone order) merchants
- ALL cardholder data functions are outsourced to a PCI DSS compliant third party
- Merchant website does not receive, transmit, or store any cardholder data
- Payment page is a redirect or iframe hosted entirely by the third party
- Merchant has no electronic storage of CHD

**Examples:** Using Stripe Checkout hosted page, PayPal redirect, Square hosted payment page

**Requirements covered:** ~22 requirements (subset of all 12)

**Key controls for SAQ-A:**
- Maintain an information security policy (Req 12)
- Security awareness training (Req 12.6)
- Incident response plan (Req 12.10)
- Confirm service providers are PCI compliant (Req 12.8)
- Protect against phishing on merchant systems (Req 5.4)

**SAQ-A does NOT require:** Network security controls assessment, full vulnerability scanning, penetration testing, internal system hardening reviews

### SAQ A-EP — E-commerce, Partial Outsource (Script on Merchant Page)
**Who qualifies:**
- E-commerce merchants only
- Payment page is hosted on merchant's systems but all payment processing is outsourced
- Merchant's website receives payment data but immediately passes to payment processor
- OR merchant's website has scripts that affect payment data capture (e.g., JavaScript payment form elements not fully hosted by processor)

**Examples:** Custom checkout form that posts to payment processor; JavaScript SDK embedded in merchant page that collects card fields

**Key distinction from SAQ-A:** The merchant controls the web page/server where payment data is initially captured, even if processing happens elsewhere.

**Requirements covered:** ~191 requirements — significantly more than SAQ-A

**Key additional controls vs SAQ-A:**
- Network security controls (Req 1): Firewall protecting the web server
- System hardening (Req 2): Secure configuration of web servers
- Vulnerability scanning: Quarterly ASV scans required
- Penetration testing: Annual internal and external pen test
- Web application firewall (WAF): Required (Req 6.4.2)
- Payment page script integrity (Req 6.4.3, 11.6.1) — see v4.0 new requirements


### SAQ B-IP — IP-Connected Payment Terminals
**Who qualifies:**
- Merchants using standalone IP-connected POI terminals (not e-commerce)
- Terminals are PTS-approved and do not store electronic cardholder data
- Terminal connects to payment processor via IP network (not dial-up)
- No card data captured by other merchant systems

**Examples:** Retail counter terminals, restaurants using wireless IP terminals (Verifone, Ingenico, PAX) connected via WiFi or Ethernet directly to payment network

**Key requirements vs SAQ-A:**
- Network security controls protecting terminal network segment
- Terminal inventory management
- Physical security of terminals (tamper protection, anti-skimming)
- Quarterly ASV scans of IP-connected terminal environment

**SAQ B-IP does NOT require:** Full e-commerce controls, WAF, payment page script controls

### SAQ Decision Tree

```
Does the merchant store, process, or transmit cardholder data electronically?
  └── No → likely out of scope (confirm with acquiring bank)
  └── Yes →
       Is all card acceptance fully outsourced (redirect/iframe, no merchant code touches CHD)?
         └── Yes, e-commerce only → SAQ-A
         └── Yes, but merchant controls page with embedded payment scripts → SAQ-A-EP
         └── No, merchant uses IP-connected standalone terminals (not e-commerce) → SAQ-B-IP
         └── No, merchant processes cards in a more complex environment → SAQ-C, SAQ-D, or ROC
```

---

## Key New Requirements in PCI DSS v4.0

### Customized Approach (New in v4.0)
Merchants may implement security controls differently from the defined requirements, provided they can demonstrate the objective is met. This is for mature organizations with strong risk management.

- Must document the customized implementation and perform a targeted risk analysis
- Must have controls reviewed by a QSA (not available for SAQ self-assessors)
- The defined approach (standard requirements) remains the default

### Targeted Risk Analysis (Multiple Requirements)
v4.0 introduces explicit requirements to perform a **Targeted Risk Analysis (TRA)** to justify the frequency of certain recurring activities (e.g., log review frequency, scan frequency, security control testing frequency). Organizations must document the analysis supporting their chosen intervals.

### 6.4.3 — Payment Page Script Integrity (Became mandatory April 2025)
For all payment pages that load scripts in the consumer's browser:
- Maintain an inventory of all scripts
- Have a method to confirm each script is authorized
- Have a method to confirm script integrity (e.g., Subresource Integrity hash, Content Security Policy)

**Who this affects most:** SAQ-A-EP merchants and any merchant with custom payment pages. This is a major new control targeting Magecart/formjacking attacks.

**Implementation approaches:**
- Subresource Integrity (SRI) tags on `<script>` elements
- Content Security Policy (CSP) header restricting script sources
- Runtime Application Self-Protection (RASP)
- Third-party script management tools

### 11.6.1 — Change and Tamper Detection for Payment Pages (Became mandatory April 2025)
- Deploy a mechanism to detect unauthorized modification of HTTP headers and payment page content
- Alert on changes to payment page scripts, forms, or redirects
- Review alerts at least weekly

**Implementation:** Tools like Reflectiz, Jscrambler, PerimeterX, or custom CSP violation reporting + monitoring.


### MFA Now Required for All CDE Access (Req 8.4.2)
v4.0 expanded MFA to require it for all access to the CDE — not just remote access. This includes:
- All non-console administrative access
- All access to the CDE from within a trusted network

### Password Requirements Updated (Req 8.3.6)
- Minimum password length increased from 7 to 12 characters
- Password change required if there is any suspicion of compromise

---

## Scoping: CDE, Connected Systems, Out-of-Scope

### Cardholder Data Environment (CDE)
All system components that store, process, or transmit cardholder data (CHD) or sensitive authentication data (SAD), plus the security controls that protect those systems.

**CHD includes:** Primary Account Number (PAN), cardholder name, expiration date, service code
**SAD includes:** Full magnetic stripe data, CVV/CVC, PIN blocks — SAD must NEVER be stored post-authorization

### Connected-to or Supporting
Systems that are not in the CDE but that:
- Connect to CDE systems
- Could impact the security of the CDE (e.g., AD domain controllers, patch management servers, monitoring systems, DNS)
These are IN SCOPE and must meet applicable requirements.

### Out-of-Scope Systems
Systems with no connectivity to the CDE and no ability to impact CDE security. Requires:
- Network segmentation (firewall/VLAN isolation from CDE)
- Validation that segmentation is effective (penetration testing at least annually)

### Scope Reduction Strategies

**Tokenization:**
- Replace PAN with a token after initial authorization
- Token has no exploitable value; only the tokenization system (vault) stores PAN
- Systems receiving only tokens are out of scope
- Providers: Braintree, Stripe, Bluesnap, First Data/Fiserv

**Point-to-Point Encryption (P2PE):**
- PCI-validated P2PE solution encrypts CHD at point of interaction (swipe/dip/tap)
- Encrypted data passes through merchant systems but cannot be decrypted there
- Dramatically reduces scope for card-present environments
- Merchant must use a PCI SSC-listed P2PE solution to claim scope reduction

---

## Key Technical Requirements

### TLS Minimum Version (Req 4.2.1)
- TLS 1.2 is the minimum; TLS 1.3 preferred
- SSL and TLS 1.0 are prohibited
- TLS 1.1 was deprecated — confirm removal
- Test with: `nmap --script ssl-enum-ciphers -p 443 <host>` or SSL Labs

### Multi-Factor Authentication (Req 8.4)
- Required for all non-console admin access into CDE
- Required for all remote access to CDE
- Required for all access into CDE from untrusted networks
- Acceptable methods: TOTP, hardware tokens, push-based (Duo), biometric

### WAF Requirement (Req 6.4.2)
- Web Application Firewall required for all public-facing web applications
- Must be active (blocking mode) or under active monitoring
- Must be updated to address new threats
- Options: AWS WAF, Cloudflare WAF, Imperva, Akamai Kona, F5 AWAF

### Logging and Monitoring (Req 10)
- Audit trails required for all CDE systems
- Must capture: user ID, event type, date/time, success/failure, origination, affected component
- Logs must be protected from modification (write-once storage or SIEM)
- Daily log review required (can be automated)
- Retain logs minimum 12 months; 3 months immediately available

### Vulnerability Scanning (Req 11.3)
- Quarterly internal vulnerability scans
- Quarterly external scans by an ASV (Approved Scanning Vendor)
- After significant changes, rescan
- High/critical vulnerabilities must be remediated; rescan to confirm

### Penetration Testing (Req 11.4)
- Annual external penetration test of CDE
- Annual internal penetration test of CDE
- After significant changes or infrastructure upgrades
- Must follow industry-accepted methodology (PTES, OWASP, NIST)
- Segmentation controls must be tested at least every 6 months


---

## Assessment Types: QSA vs ISA vs Self-Assessment

### Qualified Security Assessor (QSA)
- PCI SSC-certified company (not individual) that performs assessments
- Required for Level 1 merchants and Level 1 service providers
- Produces a Report on Compliance (ROC)
- Also required for customized approach validation

### Internal Security Assessor (ISA)
- Individual certified by PCI SSC through a sponsoring organization
- Can perform SAQ validation internally
- Cannot produce ROCs (that requires QSA company)
- Good for Level 2/3/4 merchants managing compliance internally

### Self-Assessment
- Merchant completes applicable SAQ independently
- Signed by executive officer
- Submitted to acquiring bank
- Valid for Level 2, 3, 4 merchants depending on card brand and acquirer requirements

---

## Compensating Controls

When a requirement cannot be met due to a technical or business constraint:
1. Document the legitimate technical/business constraint
2. Identify the existing controls that compensate
3. Demonstrate the compensating controls meet the intent and rigor of the original requirement
4. Additional risk must be addressed over and above the original requirement

**Example:** If TLS 1.2 cannot be deployed on a legacy POS system, compensating controls might include: network isolation of the terminal, enhanced monitoring, additional authentication layer, and a documented timeline for replacement.

Compensating controls must be reviewed annually and documented in the ROC/SAQ.

---

## Common PCI DSS Gaps and Remediation

### Default Credentials Not Changed (Req 2.1)
**Problem:** Network devices, databases, or applications using vendor default passwords.
**Remediation:** Inventory all systems; change all defaults before deployment; use a configuration standard (CIS Benchmarks).

### PAN Stored Unnecessarily (Req 3.2)
**Problem:** Full PAN found in log files, error messages, databases beyond authorization.
**Remediation:** Data discovery scan (Spirion, Ground Labs); implement tokenization; add logging filters to mask PAN; delete unnecessary stored data.

### No Key Management Procedures (Req 3.7)
**Problem:** Encryption keys not formally managed; no rotation schedule; no split knowledge.
**Remediation:** Document key management procedures; implement key rotation (at least annually); use hardware security modules (HSMs) for key storage; enforce split knowledge and dual control.

### Missing Security Awareness Training (Req 12.6)
**Problem:** No annual security training for personnel with CDE access.
**Remediation:** Deploy KnowBe4, Proofpoint Security Awareness, or equivalent; track completion; test with phishing simulations.

### No Vendor Management Program (Req 12.8)
**Problem:** No list of service providers; no confirmation of their PCI compliance.
**Remediation:** Maintain vendor inventory; obtain AOC (Attestation of Compliance) from each service provider annually; include PCI obligations in contracts.

### Payment Page Scripts Not Inventoried (Req 6.4.3) — v4.0 NEW
**Problem:** Unknown third-party scripts load on payment pages (analytics, chat, A/B testing tools).
**Remediation:** Audit all scripts on payment pages; implement CSP headers; add SRI hashes to known scripts; remove unnecessary scripts.

---

## Conversation Starters for PCI Assessments

When a user needs PCI help, ask:

1. **"Are you a merchant or service provider, and what is your annual card transaction volume?"**
   - Determines merchant level and validation requirements

2. **"How do you accept card payments — e-commerce, in-person terminals, phone/mail order?"**
   - Critical for SAQ selection

3. **"Do your web servers or payment pages host any of the payment form code, or is the entire payment UI hosted by your processor?"**
   - SAQ-A vs SAQ-A-EP determination

4. **"Have you identified your complete cardholder data environment and confirmed network segmentation?"**
   - Scope definition is the foundation of any assessment

5. **"Are there any payment page scripts (analytics, chat, tracking) that load in the browser on your payment page?"**
   - Triggers Req 6.4.3 / 11.6.1 conversation for v4.0 compliance

