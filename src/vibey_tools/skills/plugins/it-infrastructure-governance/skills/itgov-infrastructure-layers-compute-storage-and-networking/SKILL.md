---
name: itgov-infrastructure-layers-compute-storage-and-networking
description: "Use when orienting in an enterprise estate or making a platform decision: the infrastructure layers and where responsibility sits at each, compute and virtualization including hypervisors, consolidation and the on-premises versus cloud decision, storage tiers and protocols, and enterprise networking including segmentation, the edge and remote access. Includes the router for the whole it-infrastructure-governance reference."
---

# IT Infrastructure and Governance: The Layers, Compute and Virtualization, Storage, and Networking

> **Part 1 of 5** of the *IT Infrastructure and Governance* reference (plugin `it-infrastructure-governance`), covering §0–§4. Sibling skills: `itgov-directory-authentication-authorization-and-privileged-access` (§5–§8), `itgov-identity-lifecycle-access-review-and-segregation-of-duties` (§9–§11), `itgov-endpoints-continuity-itsm-and-vendor-risk` (§12–§19), `itgov-reference` (§20–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    you have configuration (§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`, §17 → `itgov-endpoints-continuity-itsm-and-vendor-risk`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| Infrastructure layers | §1 |
| Compute and virtualization | §2 |
| Storage | §3 |
| Networking | §4 |
| **Directory services and hybrid identity** | **§5 → `itgov-directory-authentication-authorization-and-privileged-access`** |
| **Authentication** | **§6 → `itgov-directory-authentication-authorization-and-privileged-access`** |
| **Authorization: RBAC, ABAC and role explosion** | **§7 → `itgov-directory-authentication-authorization-and-privileged-access`** |
| **Privileged access** | **§8 → `itgov-directory-authentication-authorization-and-privileged-access`** |
| **Identity lifecycle (JML)** | **§9 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`** |
| **Access review and certification** | **§10 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties`** |
| Segregation of duties | §11 → `itgov-identity-lifecycle-access-review-and-segregation-of-duties` |
| Endpoint management and patching | §12 → `itgov-endpoints-continuity-itsm-and-vendor-risk` |
| **Backup, DR and continuity** | **§13 → `itgov-endpoints-continuity-itsm-and-vendor-risk`** |
| Monitoring and logging | §14 → `itgov-endpoints-continuity-itsm-and-vendor-risk` |
| ITSM and change management | §15 → `itgov-endpoints-continuity-itsm-and-vendor-risk` |
| Asset and configuration management | §16 → `itgov-endpoints-continuity-itsm-and-vendor-risk` |
| **Governance frameworks** | **§17 → `itgov-endpoints-continuity-itsm-and-vendor-risk`** |
| Capacity and lifecycle planning | §18 → `itgov-endpoints-continuity-itsm-and-vendor-risk` |
| Vendor and third-party risk | §19 → `itgov-endpoints-continuity-itsm-and-vendor-risk` |
| Anti-patterns | §20 → `itgov-reference` |
| **What moved** | **§21 → `itgov-reference`** |
| Misconceptions | §22 → `itgov-reference` |
| Numbers | §23 → `itgov-reference` |
| Books | §24 → `itgov-reference` |
| Quick reference | §25 → `itgov-reference` |

---

## §1. The Layers

```
FACILITY      power, cooling, physical security  (see a power engineering reference §12)
COMPUTE       servers, hypervisors, containers
STORAGE       block, file, object; SAN/NAS
NETWORK       switching, routing, firewalls, load balancing, WAN
PLATFORM      OS, middleware, databases
IDENTITY      ⚠️ directory, authentication, authorization — the control plane
APPLICATION   the things people actually use
⚠️ GOVERNANCE  policy, process, evidence — wraps all of it
```
**⚠️ The hybrid reality is the normal case and worth stating plainly**: **very few
organizations are all-cloud or all-on-prem.** ⚠️ **Most run on-prem Active Directory
synchronized to a cloud identity provider, some workloads in a datacentre and some in
cloud, and the seams between them are where both the operational pain and the security
gaps live.**

---

## §2. Compute and Virtualization

**Bare metal** — ⚠️ **still correct for latency-sensitive, licence-bound, or
hardware-dependent workloads.**
**Hypervisors**: **Type 1 (bare metal — ESXi, Hyper-V, KVM, Xen)** vs **Type 2 (hosted)**.
**⚠️ Consolidation ratios, overcommit (memory and CPU), and the failure mode of
overcommitting: noisy neighbours and unpredictable latency.**
**Clustering and HA**: **live migration, failover, anti-affinity rules** (⚠️ **so your two
redundant VMs don't land on the same physical host — a classic and embarrassing outage
cause**).
**Containers** vs VMs — ⚠️ **different isolation boundaries; a container escape is a
different risk class from a VM escape.**
**⚠️ Licensing is a genuine architectural constraint in enterprise virtualization** —
**per-core, per-socket and per-VM models change the economics of consolidation
substantially, and licence audits are a real financial exposure.**

---

## §3. Storage

```
BLOCK    SAN, iSCSI, FC — ⚠️ raw volumes; databases and VMs
FILE     NAS, SMB/CIFS, NFS — shared filesystems, permissions
OBJECT   S3-compatible — ⚠️ flat namespace, HTTP, massive scale, no POSIX semantics
```
**RAID levels and their real trade-offs** — ⚠️ **RAID is not backup; it protects against
drive failure, not deletion, corruption or ransomware.**
**Tiering, thin provisioning** (⚠️ **and the failure mode: over-provisioning until the
pool fills and everything stops at once**), **snapshots** (⚠️ **which are not backups
either — they usually share the same storage and the same fate**), **replication
(sync vs async)**, **deduplication and compression.**
**⚠️ Storage permissions are where file-level access governance actually lives**, and
**NTFS/share permission interaction, inheritance, and the accumulated mess of nested
groups is a perennial audit finding** (§7 → `itgov-directory-authentication-authorization-and-privileged-access`).

---

## §4. Networking

**Layers and segmentation**: **VLANs**, **subnets**, **routing**, ⚠️ **microsegmentation
— and the point of segmentation is blast radius: it limits lateral movement after an
initial compromise, which is the assumption you should be designing to.**
**Firewalls** (stateful, NGFW), **load balancers**, **proxies**, **NAT**, **VPN**
(⚠️ **site-to-site and remote access, and remote-access VPN is progressively being
displaced by zero-trust network access, which authenticates per-application rather than
granting network presence**).
**⚠️ DNS and DHCP are load-bearing and under-appreciated** — ⚠️ **a large share of "the
network is down" incidents are DNS**, and **in a Windows environment AD depends on DNS
absolutely** (§5 → `itgov-directory-authentication-authorization-and-privileged-access`).
**WAN**: MPLS, SD-WAN, internet breakout. **NTP** — ⚠️ **time skew breaks Kerberos, logging
correlation, and certificate validation, and it is the cause of a surprising number of
authentication failures** (§6 → `itgov-directory-authentication-authorization-and-privileged-access`).
