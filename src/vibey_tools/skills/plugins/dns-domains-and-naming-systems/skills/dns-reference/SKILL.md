---
name: dns-reference
description: "Use when correcting a DNS or domain misconception, looking up a record type, TTL, timing, fee or registration figure, finding the sources, or needing a quick-reference picker — plus the current state of ICANN's new gTLD round and the retreat of blockchain naming. Companion to the other DNS and domain names skills."
---

# DNS and Domain Names: What's Live, Misconceptions, Numbers and Dates, and Sources

> **Part 6 of 6** of the *DNS, Domain Names and Naming Systems* reference (plugin `dns-domains-and-naming-systems`), covering §26–§31. Sibling skills: `dns-namespace-resolution-records-and-zones` (§0–§5), `dns-attacks-dnssec-encrypted-dns-and-operations` (§6–§12), `dns-icann-tlds-registries-and-registration` (§13–§16), `dns-whois-disputes-domain-security-and-aftermarket` (§17–§20), `dns-blockchain-naming-alternatives-assessed` (§21–§25). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** DNS itself is stable. Two things moved. See §26 for ICANN's first new gTLD round since 2012, and the retreat of blockchain naming.

> **⚠️ The layer that turns names humans can remember into addresses machines can route —
> and the most successful distributed database ever built, running on a design from 1983.**
>
> **Complements a communications reference (email depends on MX and §5 → `dns-namespace-resolution-records-and-zones`'s DNS records), a
> cryptography reference (DNSSEC signing, certificate issuance), and a computer-hardware
> reference (networking).**
>
> **⚠️ GOTCHA** boxes mark where the mental model people carry is wrong in ways that cause
> outages.
>
> **The three ideas that organize this document:**
> 1. **⚠️ DNS IS A DELEGATION HIERARCHY, NOT A DIRECTORY** (§2 → `dns-namespace-resolution-records-and-zones`, §5 → `dns-namespace-resolution-records-and-zones`). **Nobody holds a list
>    of all domains. Each level delegates authority downward, and every resolution walks
>    that chain. Understanding delegation explains caching, propagation, DNSSEC and most
>    outages at once.**
> 2. **⚠️ CACHING IS WHY IT SCALES AND WHY IT SURPRISES YOU** (§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`). **"DNS propagation" is
>    not a thing that happens. Old answers expire. The distinction determines what you can
>    and cannot fix quickly, and it is the single most common misunderstanding in
>    operations.**
> 3. **⚠️ A NAMESPACE NEEDS A SINGLE ROOT TO BE UNAMBIGUOUS** (§21 → `dns-blockchain-naming-alternatives-assessed`, §26.2). **Every
>    alternative naming system faces the same problem: without one authoritative root, the
>    same name can mean different things to different software. This is not a political
>    objection to decentralization — it is what a name is for.**

---

## §26. What's Live — checked August 2026

### 26.1 ⚠️ ICANN's first new gTLD round since 2012 has closed — 1,600+ applications
**⚠️ §14 → `dns-icann-tlds-registries-and-registration`'s namespace expanding for the second time — and the application window has now
closed.**

- **⚠️ THE DATES.** ⚠️ **ICANN's New gTLD Program: 2026 Round application window opened on
  30 April 2026 and closed on 12 August 2026, with ICANN's own announcement reporting more
  than 1,600 primary applications received, over 1,100 of which also requested a replacement
  string.** ⚠️ **ICANN expects to publish the list of applications that passed the
  Administrative Check ("Reveal Day") roughly nine weeks after close, with the specific
  timeline due in mid-September 2026.** ⚠️ **ICANN's framing is that for the first time in
  over a decade, organizations can apply to operate their own top-level domain.**
- **⚠️ THE PRECEDENT.** ⚠️ **The 2012 round drew nearly 2,000 applications and resulted in
  more than 1,200 new gTLDs — brands like .microsoft and .sky, places like .africa and
  .berlin, and generic terms like .bank and .eco.**
- **⚠️ THE COSTS AND TIMELINE ARE THE PART PEOPLE UNDERESTIMATE.** ⚠️ **Reporting puts the
  evaluation fee at US$227,000 per application, and applicants must partner with a
  pre-approved Registry Service Provider from ICANN's evaluated list — a requirement that is
  new relative to 2012.** ⚠️ **One registrar's analysis expects a minimum of two years before
  the first TLDs launch, taking it to roughly Q2 2028, with the full programme running
  through 2030 depending on application volume.**
- **⚠️ A NOTABLE POLICY CHANGE**: ⚠️ **the ICANN Board decided in January 2024 that CLOSED
  GENERICS — a single registrant holding a generic term like .book exclusively — will not be
  permitted in this round unless a framework is developed to assess their public-interest
  compatibility.**

> **⚠️ GOTCHA — for anyone who is not applying, the relevant consequence is defensive.**
> ⚠️ **Legal commentary notes the round presents an opportunity for brand owners and a risk
> if third parties apply for strings implicating existing trademark rights — and that
> expanding the namespace opens new space for infringement and abuse.**
> ⚠️ **The rights-protection mechanisms of §18 → `dns-whois-disputes-domain-security-and-aftermarket` — Trademark Clearinghouse, Sunrise, Claims —
> are the practical response, and they require you to have registered marks in the
> Clearinghouse BEFORE the new TLDs launch.**
> **⚠️ Note also ICANN's own status reporting was candid: the programme was in "yellow"
> status in February 2026 due to risk around systems and security testing and a
> behind-schedule operating model — which is the sort of self-assessment worth taking
> seriously.**

**⚠️ Sourcing note: the dates, fee structure and policy positions come from ICANN's own
announcement, Applicant Guidebook and status documents, plus law-firm client alerts —
which agree.**

### 26.2 ⚠️ Blockchain naming retreated, and the challenger applied to join
**⚠️ §24 → `dns-blockchain-naming-alternatives-assessed`'s assessment resolving — and the specific form the resolution took is genuinely
striking.**

- **⚠️ THE ADMISSION.** ⚠️ **In March 2026 Unstoppable Domains' CEO publicly characterized
  blockchain names as part of the 2021 "crypto craze" that "did not cross the chasm into
  mainstream usage."** ⚠️ **Reporting states that traditional DNS then accounted for more
  than 90% of Unstoppable's business — from a company that had raised roughly $70 million
  and sold over four million blockchain names.**
- **⚠️ HANDSHAKE.** ⚠️ **Namecheap exited Handshake TLD support; the Namebase exchange
  closed after a migration; reporting puts the HNS token down 99% and describes the project
  as in decline since 2022.**
- **⚠️ THE DIAGNOSED CAUSE IS EXACTLY §24 → `dns-blockchain-naming-alternatives-assessed`'s.** ⚠️ **One analysis states it plainly:
  mainstream browsers never added native blockchain domain resolution, so typing a name into
  Chrome, Safari, Firefox or Edge requires an extension.** ⚠️ **Another puts it as the
  chicken-and-egg of every alt-root: if people cannot visit your site you will not build on
  it, and if nobody builds on it browsers will not resolve it.**
- **⚠️ AND HERE IS THE REMARKABLE PART: ENS APPLIED FOR `.ens` THROUGH ICANN'S 2026 ROUND**
  (§26.1). ⚠️ **The system built to route around ICANN applied to ICANN.** ⚠️ **Reporting
  also indicates Brave and Unstoppable intend a joint application to make `.brave` an
  official brand gTLD.**
- **⚠️ ENS ALSO SIMPLIFIED ARCHITECTURALLY**: ⚠️ **in February 2026 it reportedly cancelled
  its planned Namechain Layer 2 and committed to deploying ENSv2 on Ethereum mainnet,
  because Ethereum gas limit increases had cut registration costs by roughly 99% and removed
  the justification for a dedicated rollup.**

> **⚠️ GOTCHA — ENS's own argument against rival namespaces is §21 → `dns-blockchain-naming-alternatives-assessed`'s collision problem,
> stated by an interested party but correct on the merits.** ⚠️ **ENS's blog notes that
> issuing a top-level extension not anchored to the global DNS root creates collision risk:
> if a blockchain service issues `.wallet` and ICANN later delegates `.wallet`, two
> authorities claim the same string — and in a browser, DNS resolves according to the ICANN
> root.**
> ⚠️ **With more than 1,600 applications now filed in the 2026 round, that is not hypothetical —
> and it is why ENS's DNSSEC-import path (§22 → `dns-blockchain-naming-alternatives-assessed`), which uses a name you already own rather
> than inventing an extension, is the architecturally sound answer.**

**⚠️ What survives, and it is real**: ⚠️ **the wallet-address use case.** ⚠️ **Analysis
consistently identifies replacing hex addresses with readable names as the highest-adoption
and genuinely valuable function, with one 2026 assessment recommending traditional DNS for
any public website because "Web3 resolution barriers are too high," and ENS for crypto
identity — describing that as the single best use case.**
**⚠️ Sourcing caution: much of this comes from domain-industry press and crypto media, both
with positions.** ⚠️ **But the direction is corroborated by the strongest possible evidence —
the participants' own actions and admissions: a CEO conceding the category did not cross
over, a major registrar exiting, and the flagship project applying to the incumbent
authority it was built to bypass.**

---

## §27. Misconceptions

| Misconception | Correction |
|---|---|
| DNS propagation takes 48 hours | ⚠️ **Nothing propagates. Old cached answers expire** (§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| Lowering TTL now speeds up my change | ⚠️ **The OLD TTL governs. Lower it first, then wait** (§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| There are 13 root servers | ⚠️ **13 named addresses, anycast to hundreds of instances** (§3 → `dns-namespace-resolution-records-and-zones`, §11 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| The root knows where domains are | ⚠️ **It only knows TLD delegations. Referral, not lookup** (§3 → `dns-namespace-resolution-records-and-zones`) |
| You can CNAME the apex | ⚠️ **No — SOA and NS live there. Hence ALIAS hacks** (§4 → `dns-namespace-resolution-records-and-zones`, §10 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| DNSSEC encrypts DNS | ⚠️ **Integrity only. Everything stays visible** (§8 → `dns-attacks-dnssec-encrypted-dns-and-operations`, §9 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| DNSSEC is strictly safer | ⚠️ **Misconfiguration takes you fully offline** (§8 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| DoH is straightforwardly a privacy win | ⚠️ **It moves trust to a few large providers** (§9 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| Encrypted DNS hides the site you visit | ⚠️ **Not without ECH — SNI leaks it** (§9 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| DNS failover works quickly | ⚠️ **TTLs are advisory; clients cache hard** (§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`, §12 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| One good DNS provider is enough | ⚠️ **Single-provider outage = domain gone. See Dyn 2016** (§11 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| You own your domain | ⚠️ **You hold a renewable registration** (§15 → `dns-icann-tlds-registries-and-registration`) |
| The registrar is the registry | ⚠️ **Three distinct parties. Know which to escalate to** (§15 → `dns-icann-tlds-registries-and-registration`) |
| An expired domain is gone | ⚠️ **Grace, then redemption, then pending delete** (§16 → `dns-icann-tlds-registries-and-registration`) |
| .io and .ai are generic | ⚠️ **They're country codes with sovereign risk** (§14 → `dns-icann-tlds-registries-and-registration`) |
| WHOIS redaction was ICANN policy | ⚠️ **It was GDPR. RDAP is the structured answer** (§17 → `dns-whois-disputes-domain-security-and-aftermarket`) |
| UDRP means trademarks always win | ⚠️ **Three elements including bad faith. RDNH is findable** (§18 → `dns-whois-disputes-domain-security-and-aftermarket`) |
| Domain security is about DNSSEC | ⚠️ **Mostly account security, expiry and registry lock** (§19 → `dns-whois-disputes-domain-security-and-aftermarket`) |
| Subdomain takeover is exotic | ⚠️ **Dangling CNAMEs are extremely common** (§19 → `dns-whois-disputes-domain-security-and-aftermarket`) |
| Blockchain domains replace DNS | ⚠️ **No browser resolves them natively. That was fatal** (§24 → `dns-blockchain-naming-alternatives-assessed`, §26.2) |
| Web3 names are censorship-proof | ⚠️ **The name maybe; hosting, gateways and exchanges aren't** (§24 → `dns-blockchain-naming-alternatives-assessed`) |
| "Own it forever, no renewals" | ⚠️ **True of the token, contingent on the infrastructure** (§24 → `dns-blockchain-naming-alternatives-assessed`) |
| Decentralized naming is strictly better | ⚠️ **Multiple roots means the same name resolves differently** (§21 → `dns-blockchain-naming-alternatives-assessed`) |
| ENS is fighting ICANN | ⚠️ **It applied for .ens in ICANN's 2026 round** (§26.2) |
| Web3 naming failed on technology | ⚠️ **It failed on distribution — the classic alt-root problem** (§24 → `dns-blockchain-naming-alternatives-assessed`, §26.2) |

---

## §28. Numbers and Dates

```
⚠️ DNS  ⚠️ RFC 1034/1035 (1987) · UDP 53 · 512-byte classic limit
⚠️ Labels  ⚠️ 63 octets max · full name 255
⚠️ Root  ⚠️ 13 NAMED addresses, anycast to hundreds of instances
⚠️ Kaminsky cache poisoning  ⚠️ 2008
⚠️ Root KSK rollover  ⚠️ first in 2018
⚠️ DoT port 853 · ⚠️ DoH port 443 (indistinguishable, deliberately)
⚠️ Domain lifecycle  ⚠️ auto-renew grace ~45d → redemption ~30d →
   pending delete 5d
⚠️ Transfer lock  ⚠️ 60 days after registration or transfer
⚠️ 2012 gTLD round  ⚠️ ~2,000 applications → 1,200+ delegated
⚠️ ⚠️ 2026 ROUND  ⚠️ opened 30 April 2026 · closed 12 August 2026 ·
   1,600+ applications received
⚠️ 2026 evaluation fee  ⚠️ US$227,000 per application (reported)
⚠️ First new TLDs expected  ⚠️ ~Q2 2028; programme through 2030
⚠️ Closed generics  ⚠️ not permitted in the 2026 round
⚠️ ⚠️ Unstoppable  ⚠️ ~$70m raised, 4m+ names, ⚠️ >90% of business
   now traditional DNS (reported, March 2026)
⚠️ ⚠️ Handshake  ⚠️ HNS token down 99%; Namecheap exited (reported)
⚠️ ⚠️ ENS  ⚠️ applied for .ens via ICANN 2026 round ·
   Namechain L2 cancelled Feb 2026, ENSv2 on mainnet
```

---

## §29. Sources

| Source | Why |
|---|---|
| **RFC 1034 / 1035, and the DNSSEC RFCs (4033-4035)** | ⚠️ **Primary, free, still readable** |
| **Liu & Albitz, *DNS and BIND*** | ⚠️ **The standard practical reference** |
| **ICANN Applicant Guidebook and announcements** | ⚠️ **§13 → `dns-icann-tlds-registries-and-registration`, §26.1 — primary** |
| **IANA root zone database** | ⚠️ **What is actually delegated** |
| **SSAC advisories** | ⚠️ **§19 → `dns-whois-disputes-domain-security-and-aftermarket` — the security committee's output is excellent** |
| **DNS-OARC and RIPE Labs measurement work** | ⚠️ **Real deployment data, not vendor claims** |
| **Cloudflare Learning Center on DNS** | ⚠️ **Accessible, accurate, and free** |
| **Domain Name Wire, DomainIncite** | ⚠️ **§14–§20 → `dns-icann-tlds-registries-and-registration`, `dns-whois-disputes-domain-security-and-aftermarket`, §26 — industry press with long memory** |
| **ENS documentation and blog** | ⚠️ **§22 → `dns-blockchain-naming-alternatives-assessed` — technically good, and an interested party** |
| **Zooko's triangle / petname literature** | ⚠️ **§25 → `dns-blockchain-naming-alternatives-assessed`, the conceptual framing** |

---

## §30. Quick Reference

### 30.1 Picker
| Question | Where |
|---|---|
| Why hasn't my DNS change taken effect? | ⚠️ **The old TTL. Nothing propagates** (§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| How do I migrate without downtime? | ⚠️ **Lower TTL, wait the OLD TTL, then change** (§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| Domain works for some people only | ⚠️ **Delegation mismatch or missing glue** (§5 → `dns-namespace-resolution-records-and-zones`) |
| Can I CNAME my apex? | ⚠️ **No. Use ALIAS/HTTPS records — provider-specific** (§4 → `dns-namespace-resolution-records-and-zones`, §10 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| Should I enable DNSSEC? | ⚠️ **Yes with monitoring; expiry will take you down** (§8 → `dns-attacks-dnssec-encrypted-dns-and-operations`, §11 → `dns-attacks-dnssec-encrypted-dns-and-operations`) |
| Is my domain secure? | ⚠️ **Registry lock, MFA, CAA, expiry monitoring** (§19 → `dns-whois-disputes-domain-security-and-aftermarket`) |
| Someone took over my subdomain | ⚠️ **Dangling CNAME to a reclaimed cloud resource** (§19 → `dns-whois-disputes-domain-security-and-aftermarket`) |
| I let a domain expire | ⚠️ **Check where it is in the lifecycle. Act fast** (§16 → `dns-icann-tlds-registries-and-registration`) |
| Is .io safe for my brand? | ⚠️ **It's a ccTLD. Sovereign risk is real** (§14 → `dns-icann-tlds-registries-and-registration`) |
| Should I buy a .eth domain? | ⚠️ **For crypto identity yes; as a web address no** (§24 → `dns-blockchain-naming-alternatives-assessed`) |
| Should I apply for a gTLD? | ⚠️ **$227k, an RSP, and years. 2026 window closed 12 Aug (1,600+ applied)** (§26.1) |
| Do I need to defend my trademark? | ⚠️ **Get marks into the Clearinghouse before launches** (§18 → `dns-whois-disputes-domain-security-and-aftermarket`, §26.1) |

### 30.2 Domain hygiene checklist
- [ ] ⚠️ **Registry lock on anything significant** (§19 → `dns-whois-disputes-domain-security-and-aftermarket`)
- [ ] ⚠️ **MFA on the registrar account, monitored contact address** (§19 → `dns-whois-disputes-domain-security-and-aftermarket`)
- [ ] ⚠️ **Auto-renew on, with a payment card that will not expire first** (§16 → `dns-icann-tlds-registries-and-registration`, §19 → `dns-whois-disputes-domain-security-and-aftermarket`)
- [ ] Expiry monitored INDEPENDENTLY of the registrar (§19 → `dns-whois-disputes-domain-security-and-aftermarket`)
- [ ] ⚠️ **CAA records restricting certificate issuance** (§4 → `dns-namespace-resolution-records-and-zones`, §19 → `dns-whois-disputes-domain-security-and-aftermarket`)
- [ ] Certificate Transparency monitoring for your names (§19 → `dns-whois-disputes-domain-security-and-aftermarket`)
- [ ] ⚠️ **Nameservers on diverse networks, ideally diverse providers** (§11 → `dns-attacks-dnssec-encrypted-dns-and-operations`)
- [ ] ⚠️ **Parent and child NS records agree; glue correct** (§5 → `dns-namespace-resolution-records-and-zones`)
- [ ] DNSSEC signed, with signature-expiry alerting (§8 → `dns-attacks-dnssec-encrypted-dns-and-operations`, §11 → `dns-attacks-dnssec-encrypted-dns-and-operations`)
- [ ] ⚠️ **Dangling CNAME/NS records audited regularly** (§19 → `dns-whois-disputes-domain-security-and-aftermarket`)
- [ ] AXFR restricted (§5 → `dns-namespace-resolution-records-and-zones`)
- [ ] ⚠️ **TTLs deliberate — short before a migration, long otherwise** (§6 → `dns-attacks-dnssec-encrypted-dns-and-operations`)

---

## §31. Method

**§1–§25 → `dns-namespace-resolution-records-and-zones`, `dns-attacks-dnssec-encrypted-dns-and-operations`, `dns-icann-tlds-registries-and-registration`, `dns-whois-disputes-domain-security-and-aftermarket`, `dns-blockchain-naming-alternatives-assessed` rests on long-settled protocol and institutional description** — **the resolution
model, record semantics, delegation and glue, DNSSEC's chain of trust, the
registry/registrar/registrant structure, UDRP, and the alt-root history.** ⚠️ **None needed
verification; RFC 1034 is from 1987 and the delegation model has not changed.**

**Two searches were run in August 2026**, on **ICANN's new gTLD round** and **blockchain
naming** — ⚠️ **the first because §14 → `dns-icann-tlds-registries-and-registration`'s namespace is expanding for only the second time and
the application window has just closed, the second because §24 → `dns-blockchain-naming-alternatives-assessed`'s assessment reached a
resolution during 2026 that is clearer than anything I could have argued.**

**Confidence.** **High** in §6 → `dns-attacks-dnssec-encrypted-dns-and-operations` and §19 → `dns-whois-disputes-domain-security-and-aftermarket`, which are the sections I'd most want read.
⚠️ **"DNS propagation is not a thing — old answers expire" is the correction that changes
how people plan migrations, and the procedure that follows from it (lower the TTL, wait the
OLD TTL, then change) is the single most useful operational detail here.**
⚠️ **§19 → `dns-whois-disputes-domain-security-and-aftermarket` matters because the domain is the root of online identity — whoever controls it can
obtain certificates for it, receive its mail and pass its password resets — and the
defences are cheap and widely skipped. Registry lock in particular is the strongest
available control and most people have never heard of it.**
**⚠️ §5 → `dns-namespace-resolution-records-and-zones`'s glue explanation is the one that resolves the most confusing debugging sessions.**

**High** on §26.1, which comes from ICANN's own announcement and Applicant Guidebook:
⚠️ **the window opened 30 April 2026 and closed 12 August 2026 with more than 1,600
applications received, the 2012 round produced over 1,200 gTLDs from nearly 2,000
applications, and closed generics are excluded this round.**
⚠️ **The fee and timeline figures are from law-firm and registrar analyses and I have marked
them reported.** **⚠️ ICANN's own "yellow" status assessment is worth noting precisely
because organizations rarely publish that about their own flagship programme.**

**Moderate-to-high** on §26.2, and the evidence type is what makes it strong. ⚠️ **Much of
the coverage is domain-industry press and crypto media, both with positions — but the
direction is corroborated by PARTICIPANT ACTIONS AND ADMISSIONS rather than by commentary:
a CEO conceding the category did not cross into mainstream use, a major registrar exiting
Handshake, and ENS applying for a gTLD through the very body it was built to route
around.**
⚠️ **That last fact is the strongest available evidence for §24 → `dns-blockchain-naming-alternatives-assessed`'s structural verdict — this
was a distribution problem, not a technology problem, and the participants have now acted
on that conclusion themselves.** **⚠️ The specific figures (99% token decline, 90% of
business, $70m raised) are reported and I would not rely on any one of them individually.**
