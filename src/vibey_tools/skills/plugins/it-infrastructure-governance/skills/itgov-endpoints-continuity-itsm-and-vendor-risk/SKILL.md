---
name: itgov-endpoints-continuity-itsm-and-vendor-risk
description: "Use when running or governing operations: endpoint management and patching cadence, backup, disaster recovery and continuity including RPO and RTO and testing restores rather than assuming them, monitoring and logging, ITSM and change management, asset and configuration management, the governance frameworks (ITIL, COBIT and the control mappings), capacity and lifecycle planning, and vendor and third-party risk."
---

# IT Infrastructure and Governance: Endpoints and Patching, Continuity, Monitoring, ITSM, Governance Frameworks, and Vendor Risk

> **Part 4 of 5** of the *IT Infrastructure and Governance* reference (plugin `it-infrastructure-governance`), covering §12–§19. Sibling skills: `itgov-infrastructure-layers-compute-storage-and-networking` (§0–§4), `itgov-directory-authentication-authorization-and-privileged-access` (§5–§8), `itgov-identity-lifecycle-access-review-and-segregation-of-duties` (§9–§11), `itgov-reference` (§20–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    state of any system without deliberate revocation** (§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, §10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`).
> 3. **⚠️ Governance is the ability to answer "who has access to what, why, and who
>    approved it" — with evidence.** If you cannot answer it, you do not have governance,
>    you have configuration (§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, §17).

---

## §12. Endpoint Management and Patching

**Imaging and provisioning**, **MDM/UEM**, **configuration baselines** (⚠️ **CIS
Benchmarks, DISA STIGs — and applying a benchmark wholesale without testing breaks
things, so baseline then exception with justification**), **application allowlisting**,
**disk encryption with escrowed recovery keys**, **EDR.**
**⚠️ Patching is where most exploited vulnerabilities actually live** — **not zero-days,
but known vulnerabilities with available patches.** ⚠️ **The constraint is rarely knowing
about them; it's testing, change windows, and legacy dependencies.**
```
Inventory → risk-rank (⚠️ exploitability and exposure, not CVSS alone)
→ test ring → phased deployment → verify → report exceptions
```
**⚠️ Emergency patching needs a pre-agreed process**, because deciding how to bypass change
control during an active exploit is too late.

---

## §13. Backup, DR and Continuity

```
RPO   ⚠️ how much data you can afford to lose  (drives backup FREQUENCY)
RTO   ⚠️ how long you can afford to be down    (drives RECOVERY ARCHITECTURE)
```
**⚠️ The 3-2-1 rule, extended for ransomware**: **3 copies, 2 media types, 1 offsite** —
and ⚠️ **1 immutable or air-gapped, and 0 errors on verification.** **Immutability is the
addition that matters now, because modern ransomware deliberately targets backups first
and encrypts or deletes them before the production data.**

> **⚠️ GOTCHA — an untested backup is not a backup, and this is the most reliably
> expensive lesson in IT operations.** ⚠️ **Restore testing is the only thing that proves
> backup works, and it routinely reveals: missing dependencies, undocumented restore
> order, credentials stored only in the system being restored, RTOs that are wildly
> optimistic, and backup jobs that reported success while capturing nothing.**
> **⚠️ Test restores on a schedule, and test a full-system restore, not just a file.**

**DR**: **hot/warm/cold sites**, **failover and failback** (⚠️ **failback is usually harder
than failover and is almost never rehearsed**), **runbooks**, ⚠️ **and dependency mapping —
because systems restore in an order, and discovering that order during an incident is
the worst time.**
**BCP** is broader than IT: people, facilities, suppliers, communications. ⚠️ **Note that
your incident communication plan probably depends on the systems that are down.**

---

## §14. Monitoring and Logging

**Infrastructure monitoring, APM, log aggregation, SIEM.**
**⚠️ Log what matters for both operations and investigation**: **authentication successes
and failures, privilege use and elevation, configuration and policy changes, data access
for sensitive stores, and administrative actions.**
**⚠️ Retention is a compliance decision and a cost decision, and it is usually decided by
neither** — **set it deliberately.**
**⚠️ Log integrity matters for it to be evidence**: **an attacker who can edit logs has
erased the investigation**, so **forward logs off-host promptly and write-protect them.**
**Alert design** — ⚠️ **see a reporting reference §11: every alert names an action, and
alerts that are routinely ignored should be deleted rather than tolerated.**

---

## §15. ITSM and Change Management

**ITIL practices**: **incident** (⚠️ **restore service — root cause is a separate
activity**), **problem** (⚠️ **eliminate recurrence — and this is the practice most
organizations skip, which is why the same incident happens quarterly**), **change**,
**request fulfilment**, **service level management.**
**Change types**: **standard (pre-approved, low risk), normal (assessed and approved),
emergency (expedited with retrospective review).**
**⚠️ Change management fails in two opposite directions and both are common**: ⚠️ **too
heavy, so people route around it and you lose visibility of the changes actually
happening; or too light, so unassessed changes cause outages.** **The calibration is
risk-based — a standard change catalogue for routine work frees the process to actually
scrutinize the risky changes.**
**⚠️ Post-incident review should be blameless**, because **the alternative reliably
produces concealment, and concealed incidents are how small problems become large ones.**

---

## §16. Asset and Configuration Management

**⚠️ You cannot secure, patch, licence or decommission what you don't know exists**, and
**asset inventory is the control that everything else depends on.**
**CMDB and CI relationships** — ⚠️ **and the standing failure is a CMDB that drifts from
reality until nobody trusts it.** **Automated discovery reconciled against the CMDB beats
manual maintenance, always.**
**⚠️ Shadow IT is an inventory problem before it is a security problem**, and **the
practical response is making the sanctioned path easier rather than prohibition, which
does not work.**
**Software asset management and licence compliance** — ⚠️ **a genuine financial risk;
vendor audits are real and expensive** (§2 → `itgov-infrastructure-layers-compute-storage-and-networking`).

---

## §17. Governance Frameworks

```
ITIL 4        ⚠️ service management practices. Process-focused
COBIT         ⚠️ IT GOVERNANCE — aligning IT to business objectives, control objectives
NIST CSF 2.0  ⚠️ Govern, Identify, Protect, Detect, Respond, Recover.
              The GOVERN function was added in 2.0 and is the notable change
ISO/IEC 27001 ⚠️ certifiable ISMS — the certification is of the management SYSTEM
CIS CONTROLS  ⚠️ prioritized, prescriptive, and the most immediately actionable
SOC 2         ⚠️ an attestation report, not a certification (see a business reference §16)
```
**⚠️ Pick a framework as a checklist, not a religion.** **CIS Controls Implementation
Group 1 is the highest-value starting point for most organizations** because it's
prescriptive and ordered by impact.
**⚠️ The governance question that matters underneath all of them**: **who decides, who
approves, who is accountable, and what evidence exists.** ⚠️ **A policy nobody follows and
a control nobody tests are both worse than nothing, because they create documented
assurance that doesn't exist** (§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`).
**⚠️ Compliance is not security** — **it is a floor, negotiated for a general population,
and a well-run organization exceeds it in the areas that matter to its actual risk.**

---

## §18. Capacity and Lifecycle

**Capacity planning**: **trend, model, plan** — ⚠️ **and remember the queueing result from
§3 → `itgov-infrastructure-layers-compute-storage-and-networking` of an operations context: high utilization means long waits, so planning to 100%
utilization guarantees poor performance.**
**Hardware lifecycle**: **refresh cycles, warranty, end-of-support** (⚠️ **which is a
security deadline, not a suggestion — unsupported systems stop receiving patches**).
**⚠️ Technical debt in infrastructure compounds quietly**: **the unsupported OS running the
one critical application nobody will fund replacing is the standard shape of it**, and
⚠️ **it should be on the risk register with a named owner, not tolerated silently.**

---

## §19. Vendor and Third-Party Risk

**⚠️ Your security posture includes your vendors', and supply-chain compromise is now a
primary attack path.**
**Due diligence, security questionnaires** (⚠️ **low signal, but the absence of answers is
itself signal**), **SOC 2 reports** (⚠️ **read the exceptions section and the scope, which
is where the information is**), **contractual security requirements, right to audit,
breach notification obligations** (see a business reference §16).
**⚠️ Fourth-party risk** — your vendor's vendors.
**⚠️ Integration access is the concrete exposure**: **every SaaS integration holds a
credential into your environment**, and ⚠️ **OAuth grants and API tokens issued to
third-party applications are frequently over-scoped, never reviewed, and outlive the
business relationship** (§21.2 → `itgov-reference`).
