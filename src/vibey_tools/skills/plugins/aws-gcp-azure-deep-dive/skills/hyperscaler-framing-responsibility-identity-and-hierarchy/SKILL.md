---
name: hyperscaler-framing-responsibility-identity-and-hierarchy
description: "Use when starting on a provider comparison or designing an account structure: the honest framing of what genuinely differs between AWS, GCP and Azure versus what is naming, the shared responsibility model, identity and access where the three actually diverge — IAM policies and roles, Entra ID and RBAC, and GCP's resource-oriented model — with the comparison that matters, and resource hierarchy and organization design. Includes the router for the whole aws-gcp-azure-deep-dive reference."
---

# AWS, GCP and Azure: The Honest Framing, Shared Responsibility, Identity and Access, and Resource Hierarchy

> **Part 1 of 5** of the *AWS, GCP and Azure Deep Dive* reference (plugin `aws-gcp-azure-deep-dive`), covering §0–§4. Sibling skills: `hyperscaler-networking-compute-containers-and-serverless` (§5–§8), `hyperscaler-storage-databases-analytics-and-observability` (§9–§13), `hyperscaler-cost-reliability-iac-lock-in-and-migration` (§14–§18), `hyperscaler-reference` (§19–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Architecture and IAM models are stable. Two areas moved. See §21 → `hyperscaler-reference` for egress pricing under the EU Data Act switching regime, and the AI-driven shift in market position.

> **⚠️ Scope.** Assumes you know what cloud computing *is*. This is **the comparative
> layer**: where the three genuinely differ, and where the differences bite.
> Complements a cloud-computing reference (general concepts), a Linux server admin
> reference (what runs on the instances), and an IT infrastructure/governance reference
> (identity governance, RBAC theory, on-prem).
>
> **⚠️ GOTCHA** boxes mark things that cause outages or surprise bills.
>
> **The three ideas that organize everything below:**
> 1. **⚠️ The three clouds are not interchangeable, and the service feature lists are the
>    least important difference.** **What actually differs is the identity model, the
>    resource hierarchy, and the network model** — **§3–§5 → `hyperscaler-networking-compute-containers-and-serverless`.** ⚠️ **Everything above those
>    three is broadly comparable; everything about migration difficulty is determined by
>    them.**
> 2. **⚠️ Data gravity is the real lock-in, not APIs.** **Moving compute is a project.
>    Moving petabytes is an economic decision** — and §21.1 → `hyperscaler-reference` explains why that decision
>    just changed.
> 3. **⚠️ Cloud cost surprises are almost never compute.** **They're data transfer, idle
>    provisioned resources, and per-request charges on managed services** — **§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| The honest framing | §1 |
| Shared responsibility | §2 |
| **⚠️ Identity and access — the deepest difference** | **§3** |
| **Resource hierarchy and org structure** | **§4** |
| Networking | §5 → `hyperscaler-networking-compute-containers-and-serverless` |
| Compute | §6 → `hyperscaler-networking-compute-containers-and-serverless` |
| Kubernetes and containers | §7 → `hyperscaler-networking-compute-containers-and-serverless` |
| Serverless | §8 → `hyperscaler-networking-compute-containers-and-serverless` |
| Storage | §9 → `hyperscaler-storage-databases-analytics-and-observability` |
| Databases | §10 → `hyperscaler-storage-databases-analytics-and-observability` |
| Analytics | §11 → `hyperscaler-storage-databases-analytics-and-observability` |
| AI/ML services | §12 → `hyperscaler-storage-databases-analytics-and-observability` |
| Observability | §13 → `hyperscaler-storage-databases-analytics-and-observability` |
| **⚠️ Cost mechanics** | **§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`** |
| Reliability, regions, SLAs | §15 → `hyperscaler-cost-reliability-iac-lock-in-and-migration` |
| IaC | §16 → `hyperscaler-cost-reliability-iac-lock-in-and-migration` |
| **⚠️ Lock-in and multi-cloud, honestly** | **§17 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`** |
| Migration | §18 → `hyperscaler-cost-reliability-iac-lock-in-and-migration` |
| Anti-patterns | §19 → `hyperscaler-reference` |
| **Service equivalence table** | **§20 → `hyperscaler-reference`** |
| **What moved** | **§21 → `hyperscaler-reference`** |
| Misconceptions | §22 → `hyperscaler-reference` |
| Numbers | §23 → `hyperscaler-reference` |
| Resources | §24 → `hyperscaler-reference` |
| Quick reference | §25 → `hyperscaler-reference` |

---

## §1. The Honest Framing

**⚠️ Each cloud has a shape that reflects its origin, and knowing the shape predicts the
service quality better than any comparison matrix.**

```
AWS    ⚠️ Built outward from primitives. The broadest catalogue, the most mature,
       and the most SHARP EDGES. Services are composable and you assemble them.
       ⚠️ Best-in-class breadth; worst-in-class coherence — many services overlap
       and several are effectively legacy but never removed
AZURE  ⚠️ Built inward from enterprise. Deepest integration with Windows, AD,
       Office, and existing enterprise licensing. Strongest hybrid story (Arc,
       Stack). ⚠️ Enterprise agreements and licence portability are often the
       real reason organizations choose it, and that is a legitimate reason
GCP    ⚠️ Built from Google's internal infrastructure. FEWER services, BETTER
       ones in specific areas — BigQuery, GKE, and the network. ⚠️ Historically
       weakest on enterprise sales, support and long-term service commitment,
       which is a real and frequently-cited concern
```
> **⚠️ GOTCHA — the honest selection criteria are rarely technical.** ⚠️ **Existing
> enterprise agreements, what your team already knows, compliance and data residency,
> and which vendor gives you credits usually dominate.** **That is not irrational. The
> technical differences between the three for a typical workload are smaller than the
> difference made by a team that knows the platform.**
> **⚠️ The exceptions where the platform genuinely determines the outcome**: **large-scale
> analytics (BigQuery), Kubernetes at scale (GKE), and Windows/AD-centric estates
> (Azure).**

---

## §2. Shared Responsibility

**⚠️ The provider secures the cloud; you secure what you put in it.** **The line moves by
service model**, and ⚠️ **misunderstanding where it sits is the root cause of most cloud
breaches** — **which are overwhelmingly customer-side misconfiguration, not provider
compromise.**
```
IaaS   ⚠️ You: OS, patching, network config, IAM, data, application
PaaS   ⚠️ You: IAM, data, application config
SaaS   ⚠️ You: IAM, data, and usage
ALWAYS YOURS, on every model: ⚠️ identity, access policy, data classification,
       and the correctness of your configuration
```
**⚠️ The canonical failure is a publicly-readable object store bucket.** **All three
providers now default to private and warn loudly, and it still happens** — because
⚠️ **someone made it public deliberately to solve a problem and never reverted it.**

---

## §3. ⚠️ Identity and Access — Where They Genuinely Differ

**⚠️ This is the section that matters most, and it's the one most comparisons skip.**
**IAM is where the three clouds are least alike, hardest to translate between, and where
mistakes are most consequential.**

### 3.1 AWS
```
Principals   users, roles, and ⚠️ ROLES ARE THE IMPORTANT ONE — an identity that
             is ASSUMED temporarily via STS, producing short-lived credentials
Policies     ⚠️ JSON documents. Identity-based (attached to principal) and
             RESOURCE-based (attached to the resource — S3 bucket policies, KMS
             key policies). ⚠️ BOTH must allow; either can deny
Boundaries   permissions boundaries, SCPs (Service Control Policies) at org level,
             session policies — ⚠️ these INTERSECT, they don't add
Evaluation   ⚠️ explicit DENY always wins → then explicit ALLOW → else implicit deny
```
> **⚠️ GOTCHA — AWS policy evaluation is genuinely hard to reason about, and this is not
> a skill issue.** ⚠️ **An effective permission is the INTERSECTION of the identity
> policy, any resource policy, the permissions boundary, the SCP, and the session policy
> — and any single explicit Deny anywhere overrides every Allow.** **People routinely
> grant a permission and find it doesn't work, or believe they've revoked one and find it
> still does.**
> **⚠️ Use the IAM policy simulator and Access Analyzer rather than reasoning by hand.**

### 3.2 Azure
```
Identity     ⚠️ Microsoft Entra ID (formerly Azure AD) — SEPARATE from the Azure
             resource plane, and this separation is the thing to internalize
Two systems  ⚠️ Entra ROLES govern the directory (users, groups, apps).
             AZURE RBAC governs resources (subscriptions, RGs, resources).
             ⚠️ They are DIFFERENT SYSTEMS with different role definitions
RBAC model   role definitions + scope + principal = role assignment.
             ⚠️ Scopes INHERIT downward: mgmt group → subscription → RG → resource
Deny         ⚠️ Azure RBAC is ADDITIVE — assignments accumulate. Deny assignments
             exist but are limited. Azure Policy is the usual guardrail
Managed identities  ⚠️ system-assigned vs user-assigned. The right way to avoid secrets
```
> **⚠️ GOTCHA — the Entra-vs-Azure-RBAC split confuses almost everyone at first.**
> ⚠️ **Being Global Administrator in Entra does NOT by itself give you access to Azure
> resources**, and **an Azure Owner is not necessarily able to manage the directory.**
> **There is an elevation path, deliberately.** **Treat them as two separate authorization
> systems that happen to share a principal store.**

### 3.3 GCP
```
Hierarchy    ⚠️ Organization → Folders → Projects → Resources. Policy INHERITS
             downward and the PROJECT is the primary unit of isolation
Members      users, groups, service accounts, ⚠️ and service accounts are BOTH an
             identity AND a resource you grant access TO — which is unusual and
             a common source of confusion
Roles        basic (⚠️ Owner/Editor/Viewer — too broad, avoid), predefined, custom
Binding      policy = set of bindings (role → members) attached at a hierarchy node
Deny         ⚠️ IAM Deny policies exist and are relatively recent; the model is
             otherwise additive-with-inheritance
```
> **⚠️ GOTCHA — GCP inheritance is additive and cannot be reduced by a lower level in the
> base model.** ⚠️ **Granting a role at the organization or folder level grants it on
> everything beneath, and a project-level policy cannot take it away.** **Which is why
> broad grants high in the hierarchy are the classic GCP privilege mistake.**

### 3.4 ⚠️ The comparison that matters
| | AWS | Azure | GCP |
|---|---|---|---|
| Primary isolation unit | ⚠️ **Account** | ⚠️ **Subscription** | ⚠️ **Project** |
| Policy language | JSON policies | Role definitions | Role bindings |
| Inheritance | ⚠️ Via SCPs, intersecting | ⚠️ Scope hierarchy, additive | ⚠️ Hierarchy, additive |
| Resource-attached policy | ⚠️ **Yes — significant** | Limited | Limited |
| Temporary credentials | ⚠️ **STS/AssumeRole, central** | Managed identities | Service account impersonation |
| Deny semantics | ⚠️ **Explicit deny always wins** | Mostly additive | Mostly additive |

**⚠️ Universal principles regardless of platform** (see an IT governance reference §7–§9):
**no long-lived static credentials — use workload identity federation, roles, or managed
identities**; **least privilege, granted at the narrowest scope**; **separate accounts /
subscriptions / projects per environment**; ⚠️ **MFA and phishing-resistant methods on
every human with production access**; **and periodic access review, because the grants
accumulate and never expire on their own.**

---

## §4. Resource Hierarchy and Organization

```
AWS     Organization → OUs → ⚠️ ACCOUNTS → resources (with tags)
        ⚠️ The account is the blast radius. Multi-account is the standard pattern
        (Control Tower, Landing Zone). Per-env, per-team, per-workload accounts
AZURE   Mgmt Groups → ⚠️ SUBSCRIPTIONS → Resource Groups → resources
        ⚠️ The RESOURCE GROUP is a genuinely useful lifecycle unit AWS lacks —
        things created together, deleted together
GCP     Organization → Folders → ⚠️ PROJECTS → resources
        ⚠️ The project is both a billing boundary and an isolation boundary,
        which makes the model cleanly simple
```
**⚠️ The universal principle**: **environment separation should be at the strongest
isolation boundary available — separate accounts/subscriptions/projects for prod and
non-prod, not just separate tags or namespaces.** ⚠️ **Tag-based separation is a
convention, not a control.**
**Tagging/labelling** — ⚠️ **enforce it from day one via policy (SCP, Azure Policy, Org
Policy), because retrofitting tags across an existing estate is one of those projects
that never finishes** and **untagged spend is unattributable spend** (§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`).
