---
name: itgov-directory-authentication-authorization-and-privileged-access
description: "Use when working on who can do what: directory services and hybrid identity including the synchronization models and their failure modes, authentication covering factors, MFA, single sign-on and the federation protocols, authorization with RBAC and the models that extend it, and privileged access management including just-in-time elevation, break-glass accounts and session recording."
---

# IT Infrastructure and Governance: Directory Services, Authentication, Authorization, and Privileged Access

> **Part 2 of 5** of the *IT Infrastructure and Governance* reference (plugin `it-infrastructure-governance`), covering §5–§8. Sibling skills: `itgov-infrastructure-layers-compute-storage-and-networking` (§0–§4), `itgov-identity-lifecycle-access-review-and-segregation-of-duties` (§9–§11), `itgov-endpoints-continuity-itsm-and-vendor-risk` (§12–§19), `itgov-reference` (§20–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    authorization time** (§5, §6).
> 2. **⚠️ Access accumulates and never sheds by itself.** People change roles and keep old
>    permissions; service accounts outlive their systems. **Privilege creep is the default
>    state of any system without deliberate revocation** (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, §10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`).
> 3. **⚠️ Governance is the ability to answer "who has access to what, why, and who
>    approved it" — with evidence.** If you cannot answer it, you do not have governance,
>    you have configuration (§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, §17 → `itgov-endpoints-continuity-itsm-and-vendor-risk`).

---

## §5. Directory Services and Hybrid Identity

**⚠️ Active Directory remains the backbone of enterprise identity in most organizations**,
and it is not going away quickly.
```
FOREST / DOMAIN / OU     ⚠️ the FOREST is the security boundary, not the domain —
                         a common and consequential misunderstanding
GROUP POLICY (GPO)       configuration management for domain-joined machines
KERBEROS                 ⚠️ ticket-based; needs time sync and correct SPNs
LDAP                     directory queries
SITES AND SERVICES       replication topology
FSMO ROLES               ⚠️ single-master operations; know where they live
```
**⚠️ Tiered administration is the single most important AD security model**: **Tier 0
(identity infrastructure — domain controllers, AD, PKI), Tier 1 (servers and
applications), Tier 2 (workstations).** ⚠️ **Credentials must never flow downward: a
Domain Admin logging into a workstation exposes Tier 0 credentials to a Tier 2 machine,
and that single practice is how most domain compromises escalate.**

**Hybrid**: **directory synchronization to a cloud IdP**, **federation vs password hash
sync vs pass-through**, ⚠️ **and the cloud tenant and the on-prem forest are separate trust
domains that happen to share user objects.**
> **⚠️ GOTCHA — hybrid means your attack surface is the union, not the intersection.**
> ⚠️ **Compromise of on-prem AD frequently means compromise of the synced cloud identities,
> and sync accounts are themselves Tier 0 assets that are routinely under-protected.**
> **Legacy authentication protocols that bypass modern policy are the other standing
> hybrid gap** (§6, §21.1 → `itgov-reference`).

---

## §6. Authentication

```
SOMETHING YOU KNOW    password  ⚠️ the weakest factor
SOMETHING YOU HAVE    token, key, device
SOMETHING YOU ARE     biometric
```
**⚠️ Not all MFA is equal, and this is the practical point:**
```
SMS / VOICE      ⚠️ WEAKEST — SIM swap, and real-time phishing relay
TOTP / OATH      ⚠️ better, but still phishable — a user can be tricked into
                 entering the code on a fake login page
PUSH             ⚠️ MFA fatigue attacks; number matching mitigates
PHISHING-RESISTANT  ⚠️ FIDO2/WebAuthn, passkeys, platform authenticators,
                 certificate-based — the credential is CRYPTOGRAPHICALLY BOUND to
                 the origin, so a relay attack cannot work
```
**⚠️ The mechanism is what matters**: **phishing-resistant methods bind the credential to
the legitimate site's origin, so an attacker-in-the-middle proxy gets nothing usable.**
**Every other method can be relayed in real time by a phishing kit, and modern kits do
exactly this routinely.**

**SSO** (SAML, OIDC/OAuth 2.0), **conditional/risk-based access** (⚠️ **evaluating device
compliance, location, sign-in risk and application sensitivity at each authentication —
this is the policy engine that makes identity a real perimeter**), **session management
and token lifetime**, **break-glass accounts** (⚠️ **excluded from policy, hardware-key
protected, monitored, and tested — an untested break-glass account is a bet you haven't
verified**).
**⚠️ Certificates and PKI**: **CA hierarchy, expiry (⚠️ a leading cause of self-inflicted
outages), revocation, and internal CA protection as a Tier 0 asset.**

---

## §7. Authorization: RBAC and Beyond

```
DAC   discretionary — the owner grants. ⚠️ How file shares become ungovernable
MAC   mandatory — system-enforced labels; military and SELinux
RBAC  ⚠️ permissions attach to ROLES, users get roles. The enterprise standard
ABAC  attribute-based — ⚠️ policy evaluated over user, resource, action, environment
ReBAC relationship-based — ⚠️ "can edit documents in projects they own" (Zanzibar-style)
PBAC  policy-based, often externalized to a decision engine
```
**⚠️ Core RBAC concepts**: **role hierarchies (inheritance), role assignment vs
activation, constraints, and permission aggregation.**
**⚠️ Least privilege** — grant the minimum required. **Need to know.** **Deny by default.**

> **⚠️ GOTCHA — role explosion is the standard failure of RBAC, and it is close to
> inevitable without design discipline.** ⚠️ **Every genuine exception becomes a new role;
> you end up with more roles than users, and nobody can say what any of them mean.**
> **The symptoms: roles named after individuals, roles nobody can define, and roles that
> exist only because one person needed one extra permission in 2019.**
>
> ⚠️ **The mitigations that work**: **separate BUSINESS roles (what a job does — these
> map to people) from TECHNICAL entitlements (what a system permits)**, so ⚠️ **one
> business role composes many entitlements and stays comprehensible.** **Add attributes
> for the dimensions that would otherwise multiply roles** — **department, location,
> clearance — rather than encoding them into role names.** **Run role mining against
> actual usage.** **And ⚠️ set an explicit retirement process, because roles are never
> removed unless someone owns removing them.**

**⚠️ RBAC vs ABAC in practice**: **RBAC is comprehensible, auditable, and coarse; ABAC is
expressive, fine-grained, and much harder to reason about or audit.** ⚠️ **The common
enterprise answer is hybrid — RBAC for the coarse grant, attributes for the conditions —
and a pure-ABAC deployment often trades role explosion for policy explosion, which is
worse because it's less visible.**
**⚠️ Group nesting** is where RBAC decays in Windows environments: **nested groups produce
effective permissions nobody can compute by inspection**, and ⚠️ **the only reliable
answer is tooling that resolves effective access rather than reading the ACL.**

---

## §8. Privileged Access

**⚠️ Privileged accounts are the primary target in essentially every significant breach,
because they are the shortest path from foothold to objective.**
```
PAM VAULTING        ⚠️ credentials checked out, rotated after use, never known to humans
JUST-IN-TIME (JIT)  ⚠️ elevate for a window, then automatically revoke —
                    this eliminates STANDING privilege, which is the goal
SESSION RECORDING   privileged sessions recorded and reviewable
JEA / scoped admin  ⚠️ grant the specific task, not the admin role
TIERED ADMIN        §5
BREAK-GLASS         §6
```
**⚠️ Standing privilege is the thing to eliminate.** **A permanent Domain Admin is a
permanent target; a JIT-elevated one is a target for thirty minutes with an audit
trail.**
**⚠️ Service accounts are the perennial gap** — **shared, non-expiring passwords, excessive
privilege, no MFA possible, no owner, and nobody dares rotate them because nothing
documents what would break.** ⚠️ **This is §21.2 → `itgov-reference`'s problem in its classical form, and it
predates AI agents by decades.** **Managed service accounts, workload identities and
short-lived credentials are the structural fix.**
