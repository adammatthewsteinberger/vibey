---
name: itgov-reference
description: "Use when checking an IT governance anti-pattern, checking what moved (phishing-resistant authentication becoming mandatory on a timeline, and non-human identities now outnumbering human ones, verified August 2026), correcting a misconception, looking up a ratio or benchmark, finding the canon, or needing a picker and an access governance health check. Companion to the other it-infrastructure-governance skills."
---

# IT Infrastructure and Governance: Anti-Patterns, What Moved, Misconceptions, and Canon

> **Part 5 of 5** of the *IT Infrastructure and Governance* reference (plugin `it-infrastructure-governance`), covering §20–§26. Sibling skills: `itgov-infrastructure-layers-compute-storage-and-networking` (§0–§4), `itgov-directory-authentication-authorization-and-privileged-access` (§5–§8), `itgov-identity-lifecycle-access-review-and-segregation-of-duties` (§9–§11), `itgov-endpoints-continuity-itsm-and-vendor-risk` (§12–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** RBAC theory, directory concepts, backup strategy and ITIL process are stable. Two areas moved. See §21 below for the phishing-resistant authentication mandate timeline and non-human identity governance.

> **⚠️ Scope.** The enterprise on-prem and hybrid layer. **Complements a Linux server
> administration reference (host-level operations), a cloud reference (cloud-native
> patterns), and a security reference (threat modelling and defensive controls).**
> ⚠️ **The through-line here is access: who and what can do what, how you know, and how
> you prove it.**
>
> **⚠️ GOTCHA** boxes mark the things that cause audit findings and breaches.
>
> **The three ideas that organize this:**
> 1. **⚠️ Identity is the perimeter.** The network boundary stopped being the control
>    point years ago. **Every meaningful access decision now happens at authentication and
>    authorization time** (§5 → `itgov-directory-authentication-authorization-and-privileged-access`, §6 → `itgov-directory-authentication-authorization-and-privileged-access`).
> 2. **⚠️ Access accumulates and never sheds by itself.** People change roles and keep old
>    permissions; service accounts outlive their systems. **Privilege creep is the default
>    state of any system without deliberate revocation** (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, §10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`).
> 3. **⚠️ Governance is the ability to answer "who has access to what, why, and who
>    approved it" — with evidence.** If you cannot answer it, you do not have governance,
>    you have configuration (§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, §17 → `itgov-endpoints-continuity-itsm-and-vendor-risk`).

---

## §20. Anti-Patterns

```
⚠️ Domain Admin used for daily work — Tier 0 credentials on Tier 2 machines (§5)
⚠️ Shared administrator accounts — no attribution, no accountability
⚠️ Service accounts with permanent passwords and excessive rights (§8)
⚠️ Nested groups nobody can resolve (§7)
⚠️ Roles named after people
⚠️ Access granted "temporarily" with no expiry
⚠️ Recertification as a rubber stamp (§10)
⚠️ Backups never restore-tested (§13)
⚠️ Snapshots or RAID treated as backup (§3, §13)
⚠️ Flat network with no segmentation (§4)
⚠️ Change process so heavy people route around it (§15)
⚠️ CMDB nobody trusts (§16)
⚠️ Break-glass accounts never tested (§6)
⚠️ Logs stored only on the host that generated them (§14)
⚠️ Legacy authentication left enabled "for one app" (§5, §21.1)
⚠️ Policy documents written for audit and never implemented (§17)
```

---

## §21. What Moved — verified August 2026

### 21.1 ⚠️ Phishing-resistant authentication is becoming mandatory, on a timeline
**⚠️ The direction was already clear; what's new is enforcement dates and the retirement
of weak methods.**

**In the Microsoft ecosystem specifically** — **which matters because it's the dominant
enterprise identity platform:**
- **⚠️ Entra ID supports five phishing-resistant methods**: **Microsoft Authenticator
  phone sign-in, Windows Hello for Business (TPM-bound), FIDO2 security keys,
  certificate-based authentication (smart card / PIV), and passkeys** — **all of which
  satisfy phishing-resistant MFA when enforced through Conditional Access authentication
  strength.**
- **⚠️ Authentication Strengths is the mechanism.** **Three built-in strengths: MFA,
  Passwordless MFA, and Phishing-resistant MFA**, and ⚠️ **Microsoft publishes a
  Conditional Access template for requiring phishing-resistant MFA on admin roles**,
  which is the highest-value single policy in most tenants.
- **⚠️ SMS and voice authentication are being retired, reported as starting September
  2026.** **If an organization still depends on SMS, that is now a dated dependency with a
  deadline.**
- **⚠️ Several enforcement dates landed or land through 2026**: **from 6 July 2026,
  Conditional Access policies assigned to the "Register security information" action apply
  during Windows Hello for Business and macOS Platform SSO registration**; **enforcement
  reported as completing 13 July 2026**; **and from 7 September 2026 Self-Service Password
  Reset will accept only methods a user has actually registered.**

> **⚠️ GOTCHA — the deployment problem is bootstrapping, not technology, and it's where
> these projects stall.** ⚠️ **Registering a phishing-resistant credential requires
> authenticating with something, and a user who has nothing phishing-resistant yet must
> register using a weaker method** — **which is precisely the window an attacker wants.**
> **The pattern that addresses it: Temporary Access Pass or equivalent, issued through a
> verified channel, plus Conditional Access on the registration action itself** (which is
> what the July 2026 change enables). ⚠️ **And sequence the rollout by role — privileged
> accounts first, with hardware keys — rather than by convenience.**

**⚠️ Caveat on scope**: **the enforcement dates above are Microsoft-specific and drawn from
its own release notes and community reporting.** **Other IdPs are moving the same
direction on their own timelines**, and ⚠️ **the underlying driver is general: relay
phishing kits made non-phishing-resistant MFA insufficient, and insurers and regulators
have noticed.**

### 21.2 ⚠️ Non-human identities are now the majority of the identity estate
**⚠️ This is the biggest structural change to access governance, and it breaks assumptions
built into §9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties` and §10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`.**

**⚠️ The numbers vary widely and I am going to be explicit about why.** **Reported
non-human-to-human identity ratios range from about 25:1 to 144:1 depending on source and
methodology:**
```
~45:1    commonly cited average enterprise figure (Rubrik Zero Labs)
~80:1    KPMG Cybersecurity Considerations 2026
~100:1   several vendor and survey sources
~144:1   cloud-native / DevOps environments (Entro Labs H1 2025),
         ⚠️ reported as up from 92:1 in H1 2024
```
> **⚠️ GOTCHA — treat every one of these figures with caution.** ⚠️ **Almost all of them
> originate from vendors selling non-human identity management products, and the
> methodologies are not comparable — what counts as an "identity" differs between
> studies.** **KPMG is the most independent source in that list.**
> ⚠️ **What is well-attested is the DIRECTION and the ORDER OF MAGNITUDE: NHIs are now the
> largest identity population in the enterprise by a wide margin, and the ratio is
> growing.** **Do not quote a specific multiple as fact; do act on the direction.**

**⚠️ Why NHIs break conventional IAM, which is the part that actually matters:**
- **⚠️ They cannot use MFA.** **The entire §6 → `itgov-directory-authentication-authorization-and-privileged-access` control stack assumes a human who can be
  challenged.**
- **⚠️ They never log out and are rarely retired.** **A credential issued for a 2019
  integration is still valid.** **One report found a majority of secrets confirmed exposed
  in 2022 were still valid four years later.**
- **⚠️ They frequently have no owner**, which means **§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`'s lifecycle and §10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`'s
  certification have nobody to route to.**
- **⚠️ They are massively over-privileged** — **identities reportedly use a very small
  fraction of granted permissions on average.**
- **⚠️ Exposure is exploited fast**: **exposed cloud credentials have been reported
  exploited within an average of around 17 minutes, while a substantial share of
  organizations take over 24 hours to rotate them.**

**⚠️ Agentic AI is accelerating this rather than creating it.** **The service account
problem is decades old** (§8 → `itgov-directory-authentication-authorization-and-privileged-access`); **what agents add is volume, autonomy, and access breadth —
an agent that reads, decides and acts needs entitlements a conventional service account
wouldn't.** ⚠️ **Reported survey findings — that around 92% of organizations say current
IAM tooling cannot manage AI agent identities, while a much smaller share have implemented
any governing policy — are vendor-survey figures and should be read as indicative rather
than precise.** **The gap they describe is real.**

**⚠️ Concrete findings worth taking seriously**: **the Salesloft-Drift breach of August
2025 is the reference case for third-party integration token compromise** (§19 → `itgov-endpoints-continuity-itsm-and-vendor-risk`), and
⚠️ **one study of nearly 8,000 live Model Context Protocol servers reportedly found 40%
with no authentication at all** — **which, if approximately right, is a straightforward
consequence of new infrastructure being deployed faster than its security patterns
mature.**

**⚠️ What actually works, and it's an extension of §8 → `itgov-directory-authentication-authorization-and-privileged-access` rather than something new:**
```
1. ⚠️ INVENTORY first — you cannot govern what you can't enumerate. Scan for
   secrets, tokens, service accounts and integration grants across environments
2. ⚠️ ASSIGN A HUMAN OWNER to every non-human identity. This is the single
   highest-value control, because it makes §9 and §10 applicable
3. ⚠️ REPLACE long-lived static secrets with short-lived cryptographic identity —
   workload identity federation, SPIFFE/SPIRE, OIDC-based federation
4. RIGHTSIZE against actual usage; remove unused entitlements aggressively
5. ⚠️ DRIVE lifecycle from authoritative sources, same as humans (§9)
6. Monitor behaviour at runtime — NHIs have far more predictable patterns than
   humans, ⚠️ which makes anomaly detection MORE tractable, not less
```
⚠️ **Point 3 is the structural fix.** **Vaulting and rotating a static secret manages a
problem; eliminating the static secret removes it.**

---

## §22. Misconceptions

| Misconception | Correction |
|---|---|
| The network perimeter is the security boundary | ⚠️ **Identity is. Every access decision happens there** (§0 → `itgov-infrastructure-layers-compute-storage-and-networking`, §6 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| The domain is the AD security boundary | ⚠️ **The FOREST is** (§5 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| All MFA is roughly equivalent | ⚠️ **Only phishing-resistant methods survive relay attacks** (§6 → `itgov-directory-authentication-authorization-and-privileged-access`, §21.1) |
| SMS MFA is adequate | ⚠️ **Weakest in use, and being retired** (§6 → `itgov-directory-authentication-authorization-and-privileged-access`, §21.1) |
| RAID protects your data | ⚠️ **Against drive failure only. Not deletion or ransomware** (§3 → `itgov-infrastructure-layers-compute-storage-and-networking`) |
| Snapshots are backups | ⚠️ **Same storage, same fate** (§3 → `itgov-infrastructure-layers-compute-storage-and-networking`, §13 → `itgov-endpoints-continuity-itsm-and-vendor-risk`) |
| The backup job says success | ⚠️ **Only a restore test proves it** (§13 → `itgov-endpoints-continuity-itsm-and-vendor-risk`) |
| RBAC solves access governance | ⚠️ **Role explosion is the default outcome without design** (§7 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| ABAC is the more modern answer | ⚠️ **Trades role explosion for less-visible policy explosion** (§7 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| Effective permissions can be read off the ACL | ⚠️ **Not with nested groups. Use tooling** (§7 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| Recertification means access is controlled | ⚠️ **Rubber-stamping produces perfect evidence of nothing** (§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`) |
| Deprovisioning is handled by disabling the AD account | ⚠️ **Non-SSO apps, API keys and shared secrets persist** (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`) |
| Role changes are a provisioning event | ⚠️ **They must trigger REVOCATION review — this is where creep comes from** (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`) |
| SoD can be checked per permission | ⚠️ **It's combinatorial, over effective access** (§11 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`) |
| Zero-days are the main exploitation route | ⚠️ **Known, patchable vulnerabilities dominate** (§12 → `itgov-endpoints-continuity-itsm-and-vendor-risk`) |
| Compliance means secure | ⚠️ **It's a negotiated floor** (§17 → `itgov-endpoints-continuity-itsm-and-vendor-risk`) |
| Service accounts are a minor cleanup task | ⚠️ **They're the classical form of §21.2's problem** (§8 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| AI agents created the machine identity problem | ⚠️ **They accelerated a decades-old one** (§21.2) |
| NHI ratios are established facts | ⚠️ **Mostly vendor-sourced, 25:1 to 144:1. Trust the direction** (§21.2) |
| Vaulting secrets solves NHI risk | ⚠️ **Eliminating static secrets does. Vaulting manages** (§21.2) |

---

## §23. Numbers

```
IDENTITY ⚠️
Phishing-resistant methods: FIDO2, passkeys, Windows Hello for Business,
  certificate-based, Authenticator phone sign-in
⚠️ SMS/voice MFA retirement reported from September 2026 (Microsoft)
⚠️ Entra enforcement dates: 6 July 2026 (CA on registration action),
  13 July 2026 (completion), 7 September 2026 (SSPR registered methods only)

NON-HUMAN IDENTITY ⚠️ (vendor-sourced — direction reliable, figures are not)
~45:1 average enterprise · ~80:1 KPMG 2026 · ~144:1 cloud-native
⚠️ Exposed cloud credentials exploited in ~17 minutes average
⚠️ Machine identity count reported ~50,000 (2021) → ~250,000 (2025) typical org

BACKUP
3-2-1-1-0: ⚠️ 3 copies, 2 media, 1 offsite, 1 immutable/air-gapped, 0 verify errors
RPO drives frequency · RTO drives architecture

AD TIERS
Tier 0 identity infra · Tier 1 servers · Tier 2 workstations
⚠️ Credentials NEVER flow downward
```

---

## §24. Books

| Author | Work | Why |
|---|---|---|
| **Limoncelli, Hogan & Chalup** | ***The Practice of System and Network Administration*** | ⚠️ **The standard. Still the best single operations book** |
| **Limoncelli et al.** | *The Practice of Cloud System Administration* | The hybrid companion |
| **Beyer et al.** | ***Site Reliability Engineering*** | ⚠️ **Free online. §13–§15 → `itgov-endpoints-continuity-itsm-and-vendor-risk` from the other direction** |
| **Allspaw & Robbins** | *Web Operations* | Operational culture |
| **NIST** | ***SP 800-53, 800-63, CSF 2.0*** | ⚠️ **Free, authoritative. 800-63 is THE authentication reference** |
| **CIS** | ***CIS Controls v8 / Benchmarks*** | ⚠️ **Free, prioritized, immediately actionable** |
| **Microsoft** | *Securing Privileged Access* documentation | ⚠️ **§5 → `itgov-directory-authentication-authorization-and-privileged-access`'s tiering model, from the source** |
| **Hu et al. (NIST)** | *Guide to Attribute Based Access Control* (SP 800-162) | §7 → `itgov-directory-authentication-authorization-and-privileged-access` rigorously |
| **Ferraiolo, Kuhn & Chandramouli** | *Role-Based Access Control* | ⚠️ **The foundational RBAC text** |
| **AXELOS** | *ITIL 4 Foundation* | §15 → `itgov-endpoints-continuity-itsm-and-vendor-risk` — ⚠️ take as vocabulary, not scripture |
| **Kim, Behr & Spafford** | *The Phoenix Project* | ⚠️ **Change management and constraints, as a novel** |

---

## §25. Quick Reference

### 25.1 Picker
| Question | Where |
|---|---|
| Where should access decisions be enforced? | ⚠️ **Identity layer, not network** (§6 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| Is our MFA good enough? | ⚠️ **Is it phishing-resistant? If not, no** (§6 → `itgov-directory-authentication-authorization-and-privileged-access`, §21.1) |
| Why do we have 900 roles? | ⚠️ **Role explosion — split business roles from entitlements** (§7 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| How do we cut standing privilege? | ⚠️ **JIT elevation + PAM vaulting** (§8 → `itgov-directory-authentication-authorization-and-privileged-access`) |
| Where does privilege creep come from? | ⚠️ **The mover case** (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`) |
| Our access reviews are meaningless | ⚠️ **Risk-scope, owner-review, plain language** (§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`) |
| Is this backup adequate? | ⚠️ **3-2-1-1-0, and restore-test it** (§13 → `itgov-endpoints-continuity-itsm-and-vendor-risk`) |
| Who owns this service account? | ⚠️ **If nobody, that's the finding** (§8 → `itgov-directory-authentication-authorization-and-privileged-access`, §21.2) |
| How many machine identities do we have? | ⚠️ **Inventory first — most orgs cannot answer** (§21.2) |
| Which framework should we adopt? | ⚠️ **CIS Controls IG1 to start** (§17 → `itgov-endpoints-continuity-itsm-and-vendor-risk`) |
| Small team, can't separate duties | ⚠️ **Compensating detective controls, honestly documented** (§11 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`) |

### 25.2 Access governance health check
- [ ] Can you enumerate every account, human and non-human? (§16 → `itgov-endpoints-continuity-itsm-and-vendor-risk`, §21.2)
- [ ] ⚠️ **Does every privileged account have a named human owner?** (§8 → `itgov-directory-authentication-authorization-and-privileged-access`, §21.2)
- [ ] Is standing privileged access eliminated or minimized? (§8 → `itgov-directory-authentication-authorization-and-privileged-access`)
- [ ] ⚠️ **Do role changes trigger revocation review, not just grants?** (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`)
- [ ] Are leavers deprovisioned from non-SSO systems too? (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`)
- [ ] Do contractor accounts have expiry dates set at creation? (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`)
- [ ] Are reviews risk-scoped and in plain language? (§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`)
- [ ] ⚠️ **Are privileged accounts on phishing-resistant MFA?** (§6 → `itgov-directory-authentication-authorization-and-privileged-access`, §21.1)
- [ ] Is legacy authentication disabled? (§5 → `itgov-directory-authentication-authorization-and-privileged-access`)
- [ ] Are break-glass accounts tested and monitored? (§6 → `itgov-directory-authentication-authorization-and-privileged-access`)
- [ ] ⚠️ **Have you restore-tested a full system this year?** (§13 → `itgov-endpoints-continuity-itsm-and-vendor-risk`)
- [ ] Are logs forwarded off-host and tamper-resistant? (§14 → `itgov-endpoints-continuity-itsm-and-vendor-risk`)
- [ ] Are third-party OAuth grants and API tokens reviewed? (§19 → `itgov-endpoints-continuity-itsm-and-vendor-risk`, §21.2)

---

## §26. Method

**§1–§20 → `itgov-infrastructure-layers-compute-storage-and-networking`, `itgov-directory-authentication-authorization-and-privileged-access`, `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, `itgov-endpoints-continuity-itsm-and-vendor-risk` rest on stable material** — **RBAC theory (Ferraiolo, Kuhn & Chandramouli;
NIST SP 800-162), directory and Kerberos fundamentals, Microsoft's tiered administration
model, backup and DR practice, and ITIL/COBIT/NIST CSF process** — sourced from §24.
⚠️ **The joiner-mover-leaver problem, role explosion and rubber-stamped recertification
have been the same three failures for twenty years.**

**Two searches were run in August 2026**, both on identity, **because that is where this
domain actually moved.**

**Confidence.** **High** in §1–§20 → `itgov-infrastructure-layers-compute-storage-and-networking`, `itgov-directory-authentication-authorization-and-privileged-access`, `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, `itgov-endpoints-continuity-itsm-and-vendor-risk`.
**High in §21.1's mechanism and method list** — **the five Entra phishing-resistant
methods, Authentication Strengths, and the Conditional Access enforcement pattern are
consistent across Microsoft Learn documentation and multiple independent practitioners.**
⚠️ **The specific enforcement dates (6 July, 13 July, 7 September 2026) and the September
2026 SMS/voice retirement come from Microsoft release notes as relayed by security press
and community blogs — I'd verify them against current Microsoft documentation before
building a project plan around them, since Microsoft timelines move.**

⚠️ **§21.2 needs the most caution and I've built that into the section rather than
appending it.** **Every commonly cited NHI-to-human ratio — 45:1, 80:1, 100:1, 144:1 —
traces to a vendor selling non-human identity tooling, with the partial exception of
KPMG's Cybersecurity Considerations 2026.** **The methodologies are not comparable and
"identity" is not consistently defined between them.** ⚠️ **I have therefore reported the
range with attribution rather than picking a figure, and stated plainly that the direction
and order of magnitude are what's reliable.** **The same applies to the survey statistics
(92% saying tooling can't manage agent identities), the 17-minute credential exploitation
figure, and the MCP server finding — all indicative, none verified independently, and I've
hedged each in place.**

⚠️ **The mechanism claims in §21.2 I'm confident about on first principles rather than on
the surveys**: **NHIs genuinely cannot do MFA, genuinely don't log out, and genuinely tend
to lack owners.** **Those are structural properties, not survey findings** — **and they're
why the §8 → `itgov-directory-authentication-authorization-and-privileged-access` service-account problem and the agentic-AI problem are the same problem at
different scales.** ⚠️ **The recommendation to eliminate static secrets rather than vault
them is the one I'd stand behind most firmly, because it removes the failure mode instead
of managing it.**
