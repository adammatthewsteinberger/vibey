---
name: itgov-identity-lifecycle-access-review-and-segregation-of-duties
description: "Use when access accumulates faster than it is removed: the identity lifecycle from joiner through mover to leaver and why the mover case causes most privilege creep, access review and certification including how to run one that is not rubber-stamped, and segregation of duties covering the conflict matrix and compensating controls."
---

# IT Infrastructure and Governance: The Identity Lifecycle, Access Review, and Segregation of Duties

> **Part 3 of 5** of the *IT Infrastructure and Governance* reference (plugin `it-infrastructure-governance`), covering §9–§11. Sibling skills: `itgov-infrastructure-layers-compute-storage-and-networking` (§0–§4), `itgov-directory-authentication-authorization-and-privileged-access` (§5–§8), `itgov-endpoints-continuity-itsm-and-vendor-risk` (§12–§19), `itgov-reference` (§20–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** RBAC theory, directory concepts, backup strategy and ITIL process are stable. Two areas moved. See §21 → `itgov-reference` for the phishing-resistant authentication mandate timeline and non-human identity governance.

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
>    state of any system without deliberate revocation** (§9, §10).
> 3. **⚠️ Governance is the ability to answer "who has access to what, why, and who
>    approved it" — with evidence.** If you cannot answer it, you do not have governance,
>    you have configuration (§10, §17 → `itgov-endpoints-continuity-itsm-and-vendor-risk`).

---

## §9. Identity Lifecycle (Joiner-Mover-Leaver)

```
JOINER  ⚠️ provisioning driven from an authoritative source (HR system), not tickets
MOVER   ⚠️ THE HARD ONE — see below
LEAVER  ⚠️ deprovision everything, promptly, including non-SSO apps
```
> **⚠️ GOTCHA — the "mover" case is where privilege creep comes from, and almost every
> organization handles it badly.** ⚠️ **When someone changes role, new access is granted
> promptly because they need it to work — and old access is rarely removed, because
> removing it has no urgency and some risk of breaking something.** **Over a career, a
> long-tenured employee accumulates the union of every role they've held.**
> **⚠️ The fix is that role change must trigger revocation review, not just grant** — and
> ⚠️ **defaulting to revoke-and-re-request is more effective than review-and-remove, because
> the default is what determines the outcome.**

**⚠️ Leaver risk is concentrated in what SSO doesn't cover**: **the account disabled in the
directory is the easy part.** ⚠️ **Locally-provisioned SaaS, shared credentials, personal
API keys, VPN certificates, physical access, and anything the person set up themselves are
what actually persist.** **Immediate disable beats delete** (preserves data and audit
trail), **transfer ownership of data and service accounts**, and **rotate any shared
secret they knew.**
**⚠️ Contractors and third parties need an expiry date at creation** — ⚠️ **time-bounded by
default, because nobody will remember to remove them.**

---

## §10. Access Review and Certification

**⚠️ Periodic recertification: managers or resource owners attest that access is still
needed.** ⚠️ **It is the standard control and it is widely performed badly.**

> **⚠️ GOTCHA — rubber-stamping makes the control worthless while producing perfect
> evidence that it was performed.** ⚠️ **A manager presented with 400 entitlements named
> `APP_PRD_RW_GRP_04` will approve all of them, and the audit artefact will look
> immaculate.**
> **⚠️ What actually improves it**: **review by resource owner rather than line manager
> where the owner understands what the access does**; **plain-language entitlement
> descriptions**; **risk-based scoping — certify high-risk entitlements often and
> low-risk ones rarely, rather than everything annually**; **highlighting anomalies and
> outliers rather than presenting flat lists**; ⚠️ **and micro-certifications triggered by
> events (role change, unusual usage) rather than a calendar.**

**⚠️ Metrics worth tracking**: **orphaned accounts (no owner), dormant accounts (no
sign-in in N days), entitlements never used** (⚠️ **research suggests identities commonly
use a very small fraction of what they're granted, which is the argument for
usage-informed rightsizing**), **exception count and age**, **time-to-deprovision.**

---

## §11. Segregation of Duties

**⚠️ No single person should control an entire sensitive transaction end to end.**
**Classic pairs: create a vendor and approve payment to it; write code and deploy it to
production unreviewed; request access and approve it; administer a system and audit its
logs.**
**⚠️ SoD is a combinatorial problem, not a per-permission one** — **each permission is
fine; the combination is the violation**, ⚠️ **which is why it must be evaluated as a rule
set across effective access, and why it interacts badly with nested groups** (§7 → `itgov-directory-authentication-authorization-and-privileged-access`).
**⚠️ Compensating controls** where SoD is impossible — **and in small teams it frequently
is.** **Detective controls, mandatory review, and logging with independent oversight are
the honest answer for a five-person IT department, rather than pretending the separation
exists.**
