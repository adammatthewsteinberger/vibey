---
name: cybersecurity-principles
description: Use when explaining cybersecurity foundations, the Saltzer-Schroeder design principles, CIA triad, Zero Trust architecture, defense in depth, AAA model, threat intelligence, NIST CSF 2.0, CIS Controls, ISO 27001, modern IAM (FIDO2/passkeys/PAM), SASE, incident response, or building a security mental model. Use for any conceptual cybersecurity question, when grounding security decisions in first principles, when explaining why a security control exists, when evaluating security trade-offs, or when mapping principles to AI-era security challenges. Triggers on least privilege, fail-safe defaults, defense in depth, zero trust, CIA triad, authentication vs authorization, phishing-resistant MFA, NIST CSF, or "why do we need X security control" questions.
---

# Cybersecurity Principles: The Enduring Mental Model

## The insight that matters most

**Every major breach in history traces back to the violation of a small number of foundational principles — most of them articulated before the internet existed.**

Jerome Saltzer and Michael Schroeder published "The Protection of Information in Computer Systems" in the *Proceedings of the IEEE* in 1975. Adam Shostack has called it "one of the most cited, least read works in computer security history." Their eight principles were not technology-specific — they described how any system should behave when protecting information. NIST SP 800-160 Rev 1 (2022) expanded them into 33 security engineering principles. CISA's Secure by Design initiative (2023-24), signed by over 200 organizations, traces directly back to them.

The principles have not merely survived — they have become more relevant as systems grew more complex.

## The Saltzer-Schroeder eight principles

### 1. Least Privilege
Every user, program, and system component should operate with the minimum permissions necessary to accomplish its task.

**Why it exists**: excessive permissions mean any compromise of that account or component immediately grants the attacker excessive power.

**Real-world violations**:
- **Target 2013**: An HVAC vendor's billing credentials provided a path to point-of-sale systems at 1,797 stores because the vendor portal sat on the same network. Access far exceeded what HVAC maintenance required. Estimated cost: $162 million.
- **SolarWinds 2020**: The Orion platform required unrestricted global administrator access to function, creating the perfect vector for distributing SUNBURST malware to 18,000 customers including the Pentagon and FBI.

**The data**: Forrester estimates 80% of security breaches involve privileged credentials. Non-human identities (service accounts, API tokens) now outnumber human identities 80:1, expanding the privileged attack surface dramatically.

**Practical implementation**: just-in-time access (elevate only for specific tasks, auto-revoke after), zero standing privileges for humans, credential vaulting, session monitoring.

### 2. Fail-Safe Defaults
Access should be denied unless explicitly granted. Systems should default to a safe state when they fail.

**Why it exists**: it is far easier to enumerate what should be permitted than to enumerate all possible harmful actions.

**The physical tension**: Fail-safe locks (fail-open) unlock during power loss — safe for people exiting, dangerous for the space. Fail-secure locks (fail-closed) stay locked during power loss — safe for the space, potentially dangerous for trapped occupants. In digital systems, a firewall that fails open exposes the entire network; one that fails closed blocks all legitimate traffic. The correct choice depends on which failure mode is more catastrophic for the specific context.

**Implementation**: default-deny firewall rules, default-deny Kubernetes NetworkPolicy, deny-all IAM policies with explicit allow statements.

### 3. Open Design (Kerckhoffs's Principle)
Security must not depend on attacker ignorance of the design. The only secret element should be the key.

**History**: Auguste Kerckhoffs articulated this in 1883: a cryptosystem should be secure even if everything about the system except the key is public knowledge. Claude Shannon restated it as "the enemy knows the system."

**Why it matters**: source code leaks, hardware gets reverse-engineered, decompilers expose implementation details, employees leave, and disgruntled insiders exist. Security through obscurity fails the moment the secret is exposed — and eventually all secrets are exposed.

**Violations**: proprietary algorithms, relying on internal network architecture remaining hidden, trusting that attackers do not know your system architecture.

### 4. Separation of Privilege
No single entity should hold all-powerful access. Critical operations should require multiple conditions or actors.

**Why it exists**: compromise of any single entity should not grant total control.

**Shostack's observation**: "the most ignored principle" — over thirty years after its articulation, every major operating system still ships with an all-powerful root account.

**Implementation**: multi-person authorization for production deployments, split knowledge for cryptographic keys, separation of duties between developers and production access, break-glass accounts with multi-party authorization.

### 5. Complete Mediation
Check every access to every object every time. Do not cache permission checks.

**Why it exists**: caching permissions creates TOCTOU (Time-of-Check to Time-of-Use) vulnerabilities. Permission state can change between when it was checked and when it is used.

**Practical failure mode**: a system checks that a user is authorized when they log in, but that user's permissions are later revoked. If the system cached the initial check, the revoked user retains access until cache expiration.

**Implementation**: re-check authorization on every sensitive request, use short-lived tokens rather than long-lived sessions, revocation must propagate immediately.

### 6. Economy of Mechanism
Keep security mechanisms simple. Complex systems hide flaws.

**Why it exists**: security flaws in complex code go unnoticed because normal use does not exercise improper access paths. Complexity is the enemy of security.

**Practical implication**: prefer simple, well-audited libraries over complex in-house implementations. "Don't roll your own crypto" is a direct application of this principle — and of Kerckhoffs's.

**Schneier's Law**: "Anyone can create an algorithm that he himself can't break. What is hard is creating an algorithm that no one else can break, even after years of analysis."

### 7. Least Common Mechanism
Minimize shared mechanisms between users. Shared mechanisms are potential channels for information flow between users.

**Why it exists**: shared state is a side-channel. If two users share a caching mechanism, cache timing can leak information from one user's activity to another's.

**Modern relevance**: side-channel attacks (Spectre, Meltdown) exploit shared CPU caches and speculative execution. Container security (containers share the host kernel) applies this principle — shared kernel means container escapes are a critical threat class.

### 8. Psychological Acceptability
Security mechanisms people cannot use, they will circumvent. Usability is a security property, not a concession.

**Why it exists**: an unusable security control achieves nothing. Users route around it.

**Classic failure**: complex password requirements produce sticky notes on monitors and incremental predictable patterns (Password1! → Password2!). NIST SP 800-63B revised guidance to reflect this: focus on length over complexity, do not mandate rotation unless compromise suspected.

**The FireEye/Target case**: FireEye alerts about the malware were never investigated. The alert mechanism was technically functional but psychologically overwhelming — alert fatigue caused the SOC team to ignore real alerts. A technically correct control failed due to psychological acceptability failure.

## The CIA Triad: what security protects

**Confidentiality, Integrity, Availability** — the three pillars emerged separately. Confidentiality from a 1976 U.S. Air Force study. Integrity from Clark and Wilson's 1987 commercial security paper. Availability as a named concept around 1988. They unified into a triad by the late 1990s.

NIST CSF 2.0 extended this to include data *in use* — the driver behind confidential computing adoption (see Modern Framework Updates section).

### The critical insight: the pillars are in tension

Every security architecture is an act of balancing these tensions, not maximizing any single pillar.

| Tension | Example |
|---------|---------|
| Confidentiality vs. Availability | HIPAA authentication requirements slow access to patient records in emergencies. A doctor trying to access a patient record in a code situation faces this tension daily. |
| Integrity vs. Performance | Running integrity checks on every transaction adds latency that real-time financial systems cannot afford. |
| Confidentiality vs. Availability | Encrypting data at rest protects confidentiality, but if encryption keys are lost, availability is permanently destroyed. |

There is no universally correct balance point. The right trade-off depends on the specific context and which failure mode is more catastrophic.

## AAA: Authentication, Authorization, and Accounting

The lifecycle of any access decision. The three are inseparable.

**Authentication**: establishes identity — "who are you?" Knowledge (password), possession (hardware token), inherence (biometric). Multi-factor combines categories so compromising any single factor is insufficient.

**Authorization**: determines permissions — "what can you do?" Requires authentication first — authorization without authentication is unverifiable.

**Accounting**: creates an audit trail — "what did you do?" Without accounting, you cannot detect or prove abuse. Authentication without accounting leaves you unable to reconstruct what happened after an incident.

**Non-repudiation**: a property enabled by accounting — the signer cannot deny having signed, the actor cannot deny having acted. Digital signatures provide non-repudiation. Under the EU's eIDAS Regulation, Qualified Electronic Signatures have legal equivalence to handwritten signatures.

## Zero Trust: philosophy, history, and what it is not

### Intellectual history

**Jericho Forum** (2003): argued that network perimeters were dissolving. The concept of "de-perimeterization" — systems must be able to stand alone because the perimeter cannot be trusted.

**Operation Aurora** (2009): Chinese APT attack on Google, Adobe, and others. Google's response was to launch **BeyondCorp** — the first major enterprise implementation of perimeter-less security. Three principles: connecting from a particular network must not determine accessible services; access is granted based on user and device context; all access must be authenticated, authorized, and encrypted.

**John Kindervag at Forrester** (2010): published "No More Chewy Centers: Introducing the Zero Trust Model." Three original concepts: access all resources securely regardless of location; adopt least-privilege with strict enforcement; inspect and log all traffic.

**NIST SP 800-207** (August 2020): catalyzed by the 2015 OPM breach exposing 22.1 million records. Formalized seven tenets (summarized):
1. All resources require authenticated access
2. All communication is secured regardless of location
3. Access is per-session, dynamically determined
4. The enterprise monitors all assets
5. Authentication and authorization are dynamic and strictly enforced
6. Maximum information collected about asset state

**Biden Executive Order on Cybersecurity** (2021) and **OMB Mandate M-22-09** (2022): required federal agencies to adopt Zero Trust by 2024.

### What Zero Trust is not

Zero Trust is an architecture and philosophy — never trust, always verify, assume breach — not a product to purchase. No single vendor delivers Zero Trust. It is the simultaneous application of several Saltzer-Schroeder principles: least privilege (minimum necessary access), complete mediation (verify every request), fail-safe defaults (deny unless explicitly permitted), open design (cryptographic identity, not network location).

## Defense in depth

The insight that no single control is perfect. Borrowed from military castle design — moats, walls, towers, gates — the NSA adapted it for digital systems.

**The fundamental logic**: each layer absorbs failures that breach the previous layer. An attacker who bypasses the perimeter firewall encounters network segmentation. An attacker who compromises one workload encounters microsegmentation. An attacker who escalates privileges is detected by behavioral monitoring. An attacker who exfiltrates data encounters DLP controls.

**Case study — 2024 xz utils backdoor (CVE-2024-3094)**: Organizations with layered defenses detected and contained the supply-chain compromise. Those relying on perimeter security alone were exposed. The attacker executed a sophisticated, patient social engineering campaign targeting a sole burned-out open source maintainer over months to gain commit access. Defense in depth means any single layer failure is recoverable.

## Modern Framework Updates (2024–2026)

### NIST Cybersecurity Framework (CSF) 2.0 — February 2024

The first major revision since 2014. Headline change: a **sixth core function, Govern (GV)**, joining Identify, Protect, Detect, Respond, Recover.

- **Structure**: 6 functions, 22 categories, 106 subcategories
- **Govern contains 31 of the 106 subcategories (≈29%)** — six categories covering organizational context, risk strategy, roles, policy, oversight, and supply-chain risk management
- **CSF 2.0 doubled the supply-chain subcategories (GV.SC)** from five to ten (≈9.4% of all subcategories)
- **Scope expanded** from critical infrastructure to *all* organizations

**Why it matters**: governance and supply-chain risk are now first-class, board-level concerns. CSF 2.0 is the **lingua franca** that maps to ISO 27001, CIS Controls, and NIST SP 800-53. If someone asks what framework to use for board-level communication, the answer is CSF 2.0.

### CIS Controls v8.1 — June 2024

An iterative update to v8 that realigned to NIST CSF 2.0 by adding a **Governance** security function and a new **Documentation** asset class.

- **18 Controls, 153 Safeguards** across three Implementation Groups (IG1/IG2/IG3)
- Full implementation defends against **~86% of MITRE ATT&CK (sub-)techniques** per the CIS Community Defense Model
- **Best operational starting point** for hardening — more prescriptive than CSF 2.0

### ISO/IEC 27001:2022

The 2022 revision restructured Annex A into **4 themes** (Organizational, People, Physical, Technological) and **93 controls**, adding **11 new controls** including threat intelligence, cloud security, data leakage prevention, and secure coding. Organizations had a transition deadline — certifications against the 2013 version expired during the transition window ending in 2025. If someone is operating under ISO 27001, they should be on the 2022 version.

### Modern IAM gold standards

**Phishing-resistant MFA** is now the non-negotiable baseline:
- **FIDO2/WebAuthn** and **PKI (PIV/CAC)**: CISA's explicit "gold standard." The mechanism that matters is *origin binding* — the authenticator cryptographically refuses to respond to a spoofed domain.
- **Prompt bombing** appeared in **14% of incidents per Verizon 2025 DBIR** and over 20% of social-engineering breaches involving MFA bypass. SMS, OTP, and push notifications are all phishable.
- **NIST SP 800-63-4 (2025)** makes phishing-resistant authentication mandatory at AAL3 (hardware-bound, non-exportable keys). Syncable passkeys are not permitted at AAL3.
- **Passkeys** (device-bound for privileged/admin; synced for general workforce) are now natively supported across Apple/Google/Microsoft platforms.

**PAM (Privileged Access Management)**:
- Move to **zero standing privileges** with just-in-time, time-boxed elevation. Gold-standard vendor: CyberArk.
- Use **OAuth 2.0/PKCE** (authorization code flow); avoid implicit flow; short-lived scoped tokens.

### SASE (Secure Access Service Edge)

Convergence of SD-WAN + SWG + CASB + ZTNA + FWaaS. Per **Gartner's 2025 Magic Quadrant for SASE Platforms**, recognized leaders include:
- **Palo Alto Networks (Prisma SASE)**
- **Zscaler (Zero Trust Exchange)**
- **Netskope, Cato Networks, Cloudflare, Fortinet**

SASE is how Zero Trust architecture is operationally delivered for distributed workforces and hybrid environments.

### Incident response: NIST SP 800-61 Rev 3 (2025)

**Rev 3** reframes incident response around the CSF 2.0 functions (rather than the older standalone model).

**PICERL lifecycle** (SANS): Preparation, Identification, Containment, Eradication, Recovery, Lessons learned.

**3-2-1-1-0 backup rule for ransomware resilience**: 3 copies of data, 2 different media types, 1 offsite copy, 1 offline/immutable/air-gapped copy, 0 errors after verification.

## Financial context: why principles violations are expensive

**IBM 2024 Data Breach Report**:
- Average breach cost: **$4.88 million**
- Breaches taking over 200 days to contain cost significantly more
- Organizations using AI and automation detect and contain breaches **98 days faster** and save **$2.2 million per incident**

**Mandiant M-Trends 2025**: global median dwell time is 11 days — dramatically improved from 78 days in 2018 but still revealing. 57% of compromises are first identified by external sources, not the victim organization.

**IBM 2024**: credential-based breaches take **292 days** to identify and contain — the longest of any vector.

**Specific breach costs**:
- Target 2013: ~$162 million total
- OPM 2015: ~22.1 million records exposed, triggered NIST SP 800-207
- SolarWinds 2020: 18,000 affected customers, total cost still accruing

## Building the mental model: the threat landscape

### The structural asymmetries

**Cost asymmetry**: a DDoS attack costs approximately $38/hour to launch but $40,000/hour for victims to defend — a 1,000× cost asymmetry. Attackers win economically.

**Prosecution risk**: estimated 0.05% in the US (WEF 2020). The economic incentives heavily favor attackers.

**Attacker's advantage**: defenders must protect everything; attackers need only one weakness. This asymmetry is irreducible and should inform defensive strategy — assume breach and invest heavily in detection and response, not just prevention.

### How most breaches actually happen

**Verizon 2024 DBIR**: 68% of breaches involve a non-malicious human element. Social engineering exploits authority, urgency, social proof, and reciprocity — bypassing technical controls entirely.

**Verizon 2025 DBIR**: third-party involvement in breaches doubled to 30% year-over-year. You cannot outsource accountability — when a vendor is breached, you bear the consequences.

**Credential abuse** is the most common initial access vector: 22% of all breaches, 88% of basic web application attacks.

### Memory safety: the dominant vulnerability class

Microsoft revealed ~70% of all CVEs from 2006-2018 were memory safety issues. Google Chromium reports the same figure. Google Project Zero found 67% of zero-day exploits in 2021 targeted memory safety bugs. NSA and CISA jointly recommended transitioning to memory-safe languages (Rust, Go, Java, C#, Swift) in 2023.

## AI-Era Relevance

**The single highest-leverage traditional principle for the AI era is Least Privilege applied to non-human identities.** Most agentic breaches are privilege-and-blast-radius failures, not novel ML attacks. Non-human identities (agents, service accounts, API tokens) already outnumber human identities 80:1 — and agentic AI is adding to that count rapidly.

**Saltzer-Schroeder mapped to AI-era problems**:

| Principle | Traditional application | AI-era application |
|-----------|------------------------|-------------------|
| Complete Mediation | Check authorization on every request | Validate every tool call against policy in a deterministic layer outside the LLM |
| Psychological Acceptability | Don't force developers to hard-code tokens to avoid MFA friction | Human-in-the-loop UX that isn't defeated by alert fatigue; don't require re-approval on every low-risk agent action |
| Least Privilege | Service accounts shouldn't have admin access | Each AI agent is a non-human identity with scoped, just-in-time credentials and a required human sponsor |
| Fail-Safe Defaults | Default-deny firewall rules | Treat system prompts as NOT a security control; enforce security deterministically outside the model |
| Complete Mediation | Re-check auth on every sensitive request | Allowlist tools and egress domains; require re-approval on tool definition changes |
| Economy of Mechanism | Don't roll your own crypto | Prefer small, focused agents over monolithic agents with broad access |

**Why traditional controls remain necessary but insufficient**: prompt injection (OWASP LLM01) exploits a fundamentally new problem — the data/instruction boundary collapses when an LLM processes both in the same channel. No amount of least-privilege configuration prevents a model from following malicious instructions embedded in a document it was told to summarize. This requires new controls (input validation, output filtering, guardrails) layered on top of traditional ones.

## The three structural realities of all security work

1. **Complexity is the enemy of security**: Saltzer and Schroeder's economy of mechanism remains violated at massive scale. The proliferation of cloud services, APIs, containers, and non-human identities continuously expands the attack surface.

2. **The attacker's asymmetric advantage is economic, not technological**: defenders must find every vulnerability; attackers need only one. Prosecution risk is negligible.

3. **Algorithms are rarely the weakest link**: implementation errors, key management failures, misconfigurations, and human mistakes dominate real-world breaches. The algorithms are usually sound; the deployment is usually not.

The organizations that survive are not those with the most sophisticated technology but those that embed these principles into culture, process, and architecture so deeply that they function even when — especially when — individual components fail.

## Quick-reference: principles to scenarios

| Scenario | Which principle applies |
|----------|------------------------|
| Service account has admin access "just in case" | Least Privilege violation |
| Firewall allows all traffic by default | Fail-Safe Defaults violation |
| Internal CA used to sign certificates with no public scrutiny | Open Design / Kerckhoffs violation |
| Single person can approve and deploy production changes | Separation of Privilege violation |
| Authorization checked only at login, not per-request | Complete Mediation violation |
| 400-line custom auth library written in-house | Economy of Mechanism violation |
| All tenants share the same Redis cache instance | Least Common Mechanism concern |
| MFA required for every API call, causing developers to hard-code tokens | Psychological Acceptability failure |
| Flat network: once inside, move anywhere | Defense in Depth missing |
| Network location determines trust level | Zero Trust violation |
| AI agent uses admin credentials "for convenience" | Least Privilege violation (non-human identity) |
| Board asks for security framework language | NIST CSF 2.0 (Govern function) |
| Team needs operational hardening guidance | CIS Controls v8.1 (IG1 → IG2 → IG3) |
| Using SMS push for MFA on admin accounts | Phishing-resistant MFA violation (use FIDO2/passkeys) |
| MFA prompt bombing succeeds | Psychological Acceptability + phishing-resistant MFA violation |
